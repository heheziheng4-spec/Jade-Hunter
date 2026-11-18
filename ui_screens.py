# -*- coding: utf-8 -*-
"""逐玉记 JadeHunt · 全套界面系统
================================================
按《逐玉记 UI 设计规范 V1.0》实现的 8 个独立界面：
  1. 启动首页      2. 王城俯视总览   3. 营建建造面板   4. 事件弹窗
  5. 祭坛祭祀界面  6. 角色面板       7. 纪事说明       8. 结算结局

统一遵守：
  · 青玉面板用于祭祀/事件/叙事；夯土陶板用于资源/建造/日志/帮助/角色
  · 思源黑体、深墨青正文、无红色警报、无金无霓虹、无竹、无玻璃拟态
  · 弹窗不全屏遮挡，保留底层 3D 场景，低透明度
  · 慢淡入淡出、无弹跳抖动

以 UIScreensMixin 混入 Demo；调用 init_ui_screens() 初始化。
所有界面读真实 Village 状态，选项按钮对资源/剧情产生真实影响。
"""
import math
from panda3d.core import TextNode, Vec4
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame, DirectButton

import ui_theme as T


# 界面快捷键（避开漫游/对话已占用键）
KEYS = {
    'home':     'f1',    # 启动首页
    'overview': 'tab',   # 王城俯视总览
    'build':    'c',     # 营建面板
    'event':    'y',     # 事件弹窗
    'ritual':   't',     # 祭坛祭祀
    'hero':     'p',     # 角色面板
    'journal':  'h',     # 纪事说明
    'ending':   'f2',    # 结算结局预览
}


class UIScreensMixin:
    """全套独立界面。init_ui_screens() 后可用快捷键呼出。"""

    # -------------------------------------------------------------
    # 初始化
    # -------------------------------------------------------------
    def init_ui_screens(self):
        self._screens = {}
        self._screen_now = None
        self._ui_fade_task = None
        font = T.load_font(self) or getattr(self, 'font', None)
        self._ui_font = font

        # 青玉 / 夯土 / 玉牌按钮贴图（复用缓存）
        jade = T._get('jade', lambda: T.make_jade_panel('ui_jade_overlay', 512, 384))
        earth = T._get('earth', lambda: T.make_earth_panel('ui_earth_bar', 768, 96))
        btn_tex = T._get('btn', lambda: T.make_jade_button('ui_jade_btn', 128, 64, hover=False))
        self._ui_tex = dict(jade=jade, earth=earth, btn=btn_tex)

        # 构建 8 个界面（默认隐藏）
        self._build_home()
        self._build_overview()
        self._build_build()
        self._build_event()
        self._build_ritual()
        self._build_hero()
        self._build_journal()
        self._build_ending()

        # 绑定快捷键
        for name, key in KEYS.items():
            self.accept(key, self.toggle_screen, [name])

    # -------------------------------------------------------------
    # 通用构件
    # -------------------------------------------------------------
    def _scr_container(self, name, pos=(0, 0, 0)):
        c = self.aspect2d.attachNewNode('scr_' + name)
        c.setPos(*pos)
        c.hide()
        return c

    def _scr_card(self, container, kind='jade', w=2.5, h=1.4, pos=(0, 0, 0), name='card'):
        tex = self._ui_tex['jade' if kind == 'jade' else 'earth']
        return T.make_card(self, tex, w, h, pos=pos, parent=container, name=name)

    def _scr_text(self, container, text, pos, scale=.04, color=None,
                  align=TextNode.ALeft, wrap=None, name='t'):
        color = color or T.JADE_DEEP
        kw = dict(parent=container, text=text, font=self._ui_font,
                  pos=pos, align=align, scale=scale,
                  fg=(color[0], color[1], color[2], 1), mayChange=True)
        if wrap:
            kw['wordwrap'] = wrap
        return OnscreenText(**kw)

    def _scr_button(self, container, text, pos, scale=.042, command=None, name='b'):
        b = DirectButton(
            parent=container, text=text, text_font=self._ui_font,
            scale=scale, pos=pos,
            frameColor=(T.JADE[0], T.JADE[1], T.JADE[2], .85),
            text_fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2], 1),
            relief=1, command=command or (lambda: None),
            sortOrder=110)
        return b

    def _scr_icon(self, container, glyph, pos, scale=.05, name='icon'):
        """几何图标：用几何符号字符近似剪影（玉璧◎/陶釜▽/人形☻/夯土■/水纹≈/玉凿◆）。"""
        return self._scr_text(container, glyph, pos, scale=scale,
                              color=T.JADE, align=TextNode.ACenter, name=name)

    def _n(self):
        """当前资源摘要文本。"""
        s = self.state
        return (f'玉料 {int(s.jade)}    粮食 {s.food}    人口 {s.population}    '
                f'夯土 {s.material}    水源 {"通" if s.canal else "塞"}')

    # -------------------------------------------------------------
    # 界面 1：启动首页（左上标题 + 左侧玉牌按钮 + 底部小字）
    # -------------------------------------------------------------
    def _build_home(self):
        c = self._scr_container('home')
        self._scr_text(c, '逐玉记', (-1.55, .72), scale=.105, color=T.JADE_DEEP)
        self._scr_text(c, 'JadeHunt', (-1.55, .58), scale=.055, color=T.EARTH_DARK)
        self._scr_text(c, '追寻良渚古玉 · 玉为通神信物', (-1.55, .49),
                       scale=.030, color=T.EARTH_DARK)
        self._scr_button(c, '启 行', (-1.25, 0, .28), .055,
                         lambda: self.close_screen())
        self._scr_button(c, '纪 事', (-1.25, 0, .14), .055,
                         lambda: self.show_screen('journal'))
        self._scr_text(c, '追寻古玉，守此良渚', (-1.55, -.80),
                       scale=.026, color=T.EARTH_DARK)
        self._screens['home'] = c

    # -------------------------------------------------------------
    # 界面 2：王城俯视总览（资源栏 + 圈层导航 + 功能按钮）
    # -------------------------------------------------------------
    def _build_overview(self):
        c = self._scr_container('overview')
        # 顶部夯土资源栏
        self._scr_card(c, 'earth', 3.0, .22, (0, 0, .80), 'resbar')
        self._res_text = self._scr_text(c, self._n(), (0, .80), scale=.032,
                                        align=TextNode.ACenter, name='res')
        # 中部标题
        self._scr_text(c, '王城 · 同心圈层', (0, .40), scale=.052,
                       align=TextNode.ACenter, color=T.JADE_DEEP)
        # 右侧圈层导航（青玉小牌）
        rings = ['中心祭坛', '内圈聚落', '中圈田坊', '河滩采玉', '荒野探索']
        self._ring_desc = {
            '中心祭坛': '献玉启祀，铭刻玉契。走到祭坛高台按 E。',
            '内圈聚落': '村民主活。营火休整推进日程。',
            '中圈田坊': '农田与工坊。疏通水渠可增产。',
            '河滩采玉': '雨后河滩拾取通神古玉。',
            '荒野探索': '守护玉石的图腾小怪物与神鹿栖息之地。',
        }
        self._ring_text = self._scr_text(c, self._ring_desc['中心祭坛'],
                                         (0, .16), scale=.032, wrap=44,
                                         align=TextNode.ACenter)
        for i, r in enumerate(rings):
            self._scr_button(c, r, (1.05, 0, .28 - i * .13), .034,
                             lambda r=r: self._ring_text.setText(self._ring_desc[r]))
        # 底部功能按钮
        self._scr_button(c, '营 建', (-.9, 0, -.62), .040,
                         lambda: self.show_screen('build'))
        self._scr_button(c, '玉契日志', (-.35, 0, -.62), .040,
                         lambda: self.show_screen('journal'))
        self._scr_button(c, '返回漫游', (1.02, 0, -.62), .040,
                         lambda: self.close_screen())
        self._screens['overview'] = c

    # -------------------------------------------------------------
    # 界面 3：营建建造面板（夯土陶板 + 建筑卡片）
    # -------------------------------------------------------------
    def _build_build(self):
        c = self._scr_container('build')
        self._scr_card(c, 'earth', 2.7, 1.5, (0, 0, 0), 'panel')
        self._scr_text(c, '营 建', (0, .58), scale=.055,
                       align=TextNode.ACenter, color=T.JADE_DEEP)
        self._build_feedback = self._scr_text(c, '', (0, .46), scale=.028,
                                              align=TextNode.ACenter)
        builds = [
            ('民居', '▣', '安置族人，扩充人口', lambda: self._build_action('民居')),
            ('粮仓', '▽', '储粮备荒，安稳越冬', lambda: self._build_action('粮仓')),
            ('引水渠', '≈', '引水灌田，提升产量', lambda: self._build_action('引水渠')),
            ('玉工坊', '◎', '雕琢玉料，制备礼器', lambda: self._build_action('玉工坊')),
            ('夯土堤', '■', '筑堤防洪，护住稻田', lambda: self._build_action('夯土堤')),
            ('小型祭台', '◆', '就近祭玉，凝聚庇佑', lambda: self._build_action('小型祭台')),
        ]
        for i, (nm, glyph, desc, cmd) in enumerate(builds):
            col, row = i % 3, i // 3
            x = -0.82 + col * 0.82
            y = 0.24 - row * 0.44
            self._scr_icon(c, glyph, (x, y + .12), .05)
            self._scr_text(c, nm, (x, y + .04), scale=.032,
                           align=TextNode.ACenter, color=T.JADE_DEEP)
            self._scr_text(c, desc, (x, y - .06), scale=.021,
                           align=TextNode.ACenter, color=T.EARTH_DARK, wrap=12)
            self._scr_button(c, '筑造', (x, 0, y - .18), .030, cmd)
        self._scr_button(c, '收 卷', (0, 0, -.66), .038, lambda: self.close_screen())
        self._screens['build'] = c

    def _build_action(self, name):
        """营建反馈：Demo 里以叙事反馈为主，部分接入真实规则。"""
        s = self.state
        if name == '引水渠' and not s.canal:
            if s.material >= 8:
                s.material -= 8; s.canal = True
                self._build_feedback.setText('水渠已疏通，农田开始产粮。')
            else:
                self._build_feedback.setText('夯土不足，需 8 材料。')
        elif name == '夯土堤' and not s.dam:
            if s.material >= 10:
                s.material -= 10; s.dam = True
                self._build_feedback.setText('堤坝落成，可御第 4 日洪水。')
            else:
                self._build_feedback.setText('夯土不足，需 10 材料。')
        else:
            self._build_feedback.setText(f'{name}：此地已规划，漫游至对应圈层查看详情。')
        self.sync_ui()

    # -------------------------------------------------------------
    # 界面 4：事件弹窗（横向青玉面板 + 2~3 玉牌选项）
    # -------------------------------------------------------------
    def _build_event(self):
        c = self._scr_container('event')
        self._scr_card(c, 'jade', 2.9, 1.5, (0, 0, 0), 'panel')
        self._event_title = self._scr_text(c, '河滩得玉', (0, .55), scale=.058,
                                           align=TextNode.ACenter, color=T.JADE_DEEP)
        self._event_body = self._scr_text(
            c, '雨歇河滩，一道青光嵌于泥沙。\n取之，或留待有缘人。',
            (0, .26), scale=.034, wrap=40, align=TextNode.ACenter, color=T.JADE_DEEP)
        # 3 枚玉牌选项（统一大小、横向均匀）
        self._event_btns = [
            self._scr_button(c, '以玉祈福\n耗玉料·安洪', (-.85, 0, -.34), .032,
                             lambda: self._event_pick(0)),
            self._scr_button(c, '加固堤岸\n耗夯土·防洪', (0, 0, -.34), .032,
                             lambda: self._event_pick(1)),
            self._scr_button(c, '静观其变\n无消耗·担风险', (.85, 0, -.34), .032,
                             lambda: self._event_pick(2)),
        ]
        self._scr_button(c, '暂 缓', (0, 0, -.62), .030, lambda: self.close_screen())
        self._screens['event'] = c

    def _event_pick(self, i):
        s = self.state
        if i == 0 and s.jade:
            s.jade = False; self.toast = '以玉祈福，洪水之虞稍减。'
        elif i == 1 and s.material >= 6:
            s.material -= 6; s.dam = True; self.toast = '堤岸加固，防洪能力提升。'
        elif i == 1:
            self.toast = '夯土不足，无法加固。'
        else:
            self.toast = '静观其变，听天由命。'
        self.toasting = 5
        self.sync_ui()
        self.close_screen()

    # -------------------------------------------------------------
    # 界面 5：祭坛祭祀界面（异形玉琮面板 + 贡品槽 + 启祀）
    # -------------------------------------------------------------
    def _build_ritual(self):
        c = self._scr_container('ritual')
        self._scr_card(c, 'jade', 2.0, 1.5, (0, 0, 0), 'panel')
        self._scr_text(c, '祭祀 · 玉契铭刻', (0, .58), scale=.055,
                       align=TextNode.ACenter, color=T.JADE_DEEP)
        self._scr_text(c, '玉为通神之信，献玉启祀', (0, .42), scale=.028,
                       align=TextNode.ACenter, color=T.EARTH_DARK)
        # 三个贡品槽（单线玉璧轮廓用"◎"近似）
        self._slots = []
        for i, glyph in enumerate(['◎', '▣', '◍']):
            x = -.55 + i * .55
            self._scr_text(c, glyph, (x, .12), scale=.11,
                           align=TextNode.ACenter,
                           color=T.JADE if i == 0 else T.EARTH_DARK, name='slot%d' % i)
            self._scr_text(c, ['玉璧', '玉琮', '玉璜'][i], (x, -.02), scale=.026,
                           align=TextNode.ACenter, color=T.JADE_DEEP)
        self._ritual_hint = self._scr_text(c, '', (0, -.20), scale=.028,
                                           align=TextNode.ACenter)
        self._ritual_btn = self._scr_button(c, '启 祀', (0, 0, -.48), .050,
                                            lambda: self._do_ritual())
        self._scr_button(c, '收 卷', (0, 0, -.66), .030, lambda: self.close_screen())
        self._screens['ritual'] = c

    def _do_ritual(self):
        s = self.state
        if s.jade and s.food >= 10:
            s.food -= 10; s.jade = False; s.won = True
            self.toast = '礼成 · 玉光苏醒，玉契铭刻。'; self.toasting = 8
            self.refresh(); self.sync_ui()
            self.close_screen()
            self.show_screen('ending')
        else:
            need = []
            if not s.jade: need.append('玉器')
            if s.food < 10: need.append('10 粮食')
            self._ritual_hint.setText('祭祀尚需：' + '、'.join(need))

    # -------------------------------------------------------------
    # 界面 6：角色面板（窄夯土陶板 + 几何立绘 + 状态词条）
    # -------------------------------------------------------------
    def _build_hero(self):
        c = self._scr_container('hero')
        self._scr_card(c, 'earth', 2.0, 1.4, (0, 0, 0), 'panel')
        # 几何神王立绘（用几何符号堆叠近似，左列）
        self._scr_text(c, '◎', (-.62, .30), scale=.18,
                       align=TextNode.ACenter, color=T.JADE_DEEP)
        self._scr_text(c, '▽', (-.62, .00), scale=.20,
                       align=TextNode.ACenter, color=T.EARTH_DARK)
        self._scr_text(c, '良渚神王', (-.62, -.26), scale=.038,
                       align=TextNode.ACenter, color=T.JADE_DEEP)
        self._scr_text(c, '部族声望 · 玉之庇佑', (-.62, -.38), scale=.022,
                       align=TextNode.ACenter, color=T.EARTH_DARK)
        # 右侧状态词条（在面板内）
        self._hero_stats = self._scr_text(c, '', (.48, .16), scale=.030,
                                          align=TextNode.ACenter, wrap=22)
        self._scr_button(c, '收 卷', (.48, 0, -.50), .034, lambda: self.close_screen())
        self._screens['hero'] = c

    # -------------------------------------------------------------
    # 界面 7：纪事说明（夯土长陶板 + 简短文字 + 微型示意）
    # -------------------------------------------------------------
    def _build_journal(self):
        c = self._scr_container('journal')
        self._scr_card(c, 'earth', 2.8, 1.5, (0, 0, 0), 'panel')
        self._scr_text(c, '纪 事', (0, .56), scale=.055,
                       align=TextNode.ACenter, color=T.JADE_DEEP)
        self._scr_text(
            c,
            '◎ 玉为通神信物，是你一路追寻之物。\n'
            '▽ 粮食养民，人口与手工者共营王城。\n'
            '■ 夯土筑堤、修渠、建坊。\n'
            '≈ 水源通畅，田坊方能产粮。\n'
            '◎ 献玉于祭坛，铭刻玉契，部族长存。\n\n'
            '同心圈层：中心祭坛 → 内圈聚落 → 中圈田坊 → 河滩采玉 → 荒野',
            (0, .10), scale=.028, wrap=46, align=TextNode.ACenter, color=T.JADE_DEEP)
        self._scr_button(c, '返 回', (0, 0, -.62), .036, lambda: self.close_screen())
        self._screens['journal'] = c

    # -------------------------------------------------------------
    # 界面 8：结算结局（夯土长板 + 玉璧装饰 + 两分支）
    # -------------------------------------------------------------
    def _build_ending(self):
        c = self._scr_container('ending')
        self._scr_card(c, 'jade', 2.7, 1.5, (0, 0, 0), 'panel')
        self._scr_text(c, '◎', (0, .58), scale=.09,
                       align=TextNode.ACenter, color=T.JADE)
        self._ending_title = self._scr_text(c, '玉契永续 · 部族长存', (0, .38),
                                            scale=.052, align=TextNode.ACenter,
                                            color=T.JADE_DEEP)
        self._ending_detail = self._scr_text(c, '', (0, .10), scale=.030,
                                             wrap=44, align=TextNode.ACenter,
                                             color=T.JADE_DEEP)
        self._scr_button(c, '再逐玉', (-.6, 0, -.52), .042,
                         lambda: (self.close_screen(), self.reset()))
        self._scr_button(c, '归主界面', (.6, 0, -.52), .042,
                         lambda: (self.close_screen(), self.show_screen('home')))
        self._screens['ending'] = c

    def _refresh_ending(self):
        s = self.state
        won = s.won
        self._ending_title.setText('玉契永续 · 部族长存' if won else '洪水侵陵 · 玉迹湮没')
        self._ending_detail.setText(
            f'走过 {s.day} 日 · 守护 {s.population} 位族人\n'
            f'礼器铭刻 {"已成" if s.shrine else "未成"} · 玉契 {"永续" if won else "待续"}\n'
            + ('堤坝守住了稻田。' if s.dam else '聚落承受了洪水的考验。'))

    def _refresh_hero(self):
        s = self.state
        buff = '玉之庇佑 · 稳固' if s.dam else '玉之庇佑 · 微弱'
        self._hero_stats.setText(
            f'部族声望  {"兴盛" if s.won else "存续"}\n'
            f'{buff}\n'
            f'族人 {s.population} · 玉料 {int(s.jade)}\n'
            f'良渚守望者')

    # -------------------------------------------------------------
    # 显示 / 隐藏 / 淡入
    # -------------------------------------------------------------
    def show_screen(self, name):
        c = self._screens.get(name)
        if c is None:
            return
        # 关闭正在进行的对话
        if getattr(self, 'in_conversation', False):
            try: self.end_dialogue()
            except Exception: pass
        # 先隐藏当前
        if self._screen_now and self._screen_now != name:
            self._screens[self._screen_now].hide()
        self._screen_now = name

        # 打开前刷新动态内容
        if name == 'overview':
            self._res_text.setText(self._n())
        elif name == 'hero':
            self._refresh_hero()
        elif name == 'ending':
            self._refresh_ending()
        elif name == 'build':
            self._build_feedback.setText('选一项营建，查看反馈。')
        elif name == 'ritual':
            self._ritual_hint.setText('献入玉器后启祀。')

        # 暂停漫游：只在首个界面打开时记录原状态，避免界面间切换嵌套覆盖
        if not hasattr(self, '_ui_screen_active') or not self._ui_screen_active:
            self._prev_dialog = getattr(self, 'dialog', False)
            self._ui_screen_active = True
        self.dialog = True
        self.keys.clear()

        c.show()
        c.setAlphaScale(0.0)
        # 慢淡入（无弹跳）：0.5 秒线性
        if self._ui_fade_task:
            self.taskMgr.remove(self._ui_fade_task)
        state = {'a': 0.0, 'node': c}
        def fade(task):
            dt = min(globalClock.getDt(), .05)
            state['a'] = min(1.0, state['a'] + dt / 0.5)
            state['node'].setAlphaScale(state['a'])
            if state['a'] >= 1.0:
                return task.done
            return task.cont
        self._ui_fade_task = 'ui_screen_fade'
        self.taskMgr.add(fade, self._ui_fade_task)

    def close_screen(self):
        if self._screen_now is None:
            return
        c = self._screens.get(self._screen_now)
        if c is not None:
            c.hide()
        self._screen_now = None
        self._ui_screen_active = False
        self.dialog = getattr(self, '_prev_dialog', False)

    def toggle_screen(self, name):
        if self._screen_now == name:
            self.close_screen()
        else:
            self.show_screen(name)
