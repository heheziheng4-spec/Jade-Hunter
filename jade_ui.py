# -*- coding: utf-8 -*-
"""逐玉记 JadeHunt · 设计稿 UI 系统（jade_ui.py）
================================================
按 6 张设计稿实现游戏内界面，以 JadeUIMixin 混入 Demo。
  · 图3/5 王城圈层地图：同心圆 + 资源栏 + 状态卡 + 花瓣/菱形快捷 + 铭刻弹窗
  · 图2/4 礼器·技艺面板：标签栏 + 玉器卡片 + 双科技树 + 当前玉契/部族要务
  · 图6 叙事页：点击任意键启行 + 玉牌文本框
所有面板读真实 Village 状态，呼出才显示、关闭即回漫游。

视觉：深褐灰底 + 青玉 + 米白字，玉器图标(jade_icons) + 卷涡纹 + 四角玉璧铆钉。
技术要点（踩坑经验）：
  · OnscreenText 无 sortOrder → setBin('fixed', N)
  · 卡片 setBin('fixed', 100)，文字 120，图标 118
  · text='' 的透明 DirectButton 必须显式 frameSize
  · 玉琮/文字层级：面板底 100 < 图标 118 < 文字 120 < 弹窗 130
"""
import math, os
from panda3d.core import (
    TextNode, Filename, CardMaker, TransparencyAttrib, PNMImage, Texture, LineSegs,
)
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectButton

import ui_theme as T
import jade_icons as ICON

# 配色
# 配色依据设计稿 PIL 采样：面板底 #433E34 / 卡片 #666055 / 青玉 #B3C5B9~#CFDED5
BG       = (0.26, 0.24, 0.20, 0.95)   # 深褐灰面板底（#433E34 系）
BG_LITE  = (0.40, 0.38, 0.33, 0.93)   # 卡片底（#666055 系）
JADE     = (0.70, 0.82, 0.75)         # 青玉（#B3C5B9 系）
JADE_HI  = (0.81, 0.87, 0.83)         # 青玉高光（#CFDED5 系）
JADE_DK  = (0.47, 0.62, 0.55)
PAPER    = (0.90, 0.88, 0.81)         # 米白字
INK      = (0.28, 0.40, 0.37)

SONG = 'C:/Windows/Fonts/simsun.ttc'      # 标题衬线
KAI  = 'C:/Windows/Fonts/STKAITI.TTF'     # 古风标题
YUAN = 'C:/Windows/Fonts/SIMYOU.TTF'      # 正文幼圆

# 快捷键
KEYS = {'map': 'm', 'craft': 'k'}


def _otext(**kw):
    sort = kw.pop('sortOrder', 120)
    t = OnscreenText(**kw)
    try: t.setBin('fixed', sort)
    except Exception: pass
    return t


def _load_font(game, path, ppu=48):
    try:
        f = game.loader.loadFont(Filename.fromOsSpecific(path).getFullpath())
        f.setPixelsPerUnit(ppu); return f
    except Exception:
        return getattr(game, 'font', None)


class JadeUIMixin:

    # =============================================================
    # 初始化
    # =============================================================
    def init_jade_ui(self):
        self._ju_open = None            # 当前打开的面板名
        self._fonts = dict(
            song=_load_font(self, SONG, 48),
            kai=_load_font(self, KAI, 48),
            yuan=_load_font(self, YUAN, 48))
        self._icons = ICON.make_all()
        self._build_map()
        self._build_craft()
        self._build_narrative()
        self.accept('m', self.toggle_map)
        self.accept('k', self.toggle_craft)
        self.accept('escape', self._ju_esc)

    # =============================================================
    # 通用组件
    # =============================================================
    def _ju_panel(self, name, w=2.9, h=1.7, pos=(0, 0, 0)):
        c = self.aspect2d.attachNewNode('ju_' + name)
        c.setPos(*pos)
        cm = CardMaker('ju_bg_' + name)
        cm.setFrame(-w/2, w/2, -h/2, h/2)
        card = c.attachNewNode(cm.generate())
        card.setColor(*BG)
        card.setBin('fixed', 100)
        # 四角玉璧铆钉
        for sx in (-1, 1):
            for sy in (-1, 1):
                self._ju_icon(c, 'rivet', (sx*(w/2-.10), sy*(h/2-.10)), .045)
        c.hide()
        return c

    def _ju_icon(self, parent, key, pos, scale=.09, name='icon'):
        tex = self._icons.get(key)
        if tex is None: return None
        cm = CardMaker('ic_' + name)
        cm.setFrame(-scale/2, scale/2, -scale/2, scale/2)
        node = parent.attachNewNode(cm.generate())
        node.setTexture(tex)
        node.setTransparency(TransparencyAttrib.MAlpha)
        node.setBin('fixed', 118)
        node.setPos(pos[0], 0, pos[1])
        return node

    def _ju_text(self, parent, text, pos, scale=.04, color=None,
                 font='yuan', align=TextNode.ALeft, wrap=None, name='t', sort=120):
        color = color or PAPER
        kw = dict(parent=parent, text=str(text), font=self._fonts[font],
                  pos=pos, align=align, scale=scale,
                  fg=(color[0], color[1], color[2], 1), mayChange=True)
        if wrap: kw['wordwrap'] = wrap
        t = _otext(sortOrder=sort, **kw)
        return t

    def _ju_btn(self, parent, text, pos, scale=.038, command=None,
                w=.34, h=.09, enabled=True, name='b'):
        root = parent.attachNewNode('jb_' + name)
        root.setPos(pos[0], 0, pos[1])
        cm = CardMaker('cm')
        cm.setFrame(-w/2, w/2, -h/2, h/2)
        card = root.attachNewNode(cm.generate())
        card.setColor(*(JADE if enabled else BG_LITE))
        card.setBin('fixed', 118)
        self._ju_text(root, text, (0, 0), scale=scale,
                      color=INK if enabled else JADE_DK,
                      align=TextNode.ACenter, name='txt', sort=120)
        if enabled and command:
            DirectButton(parent=root, text='', scale=(w/2, 1, h/2),
                         frameSize=(-1, 1, -1, 1), pos=(0, 0, 0),
                         frameColor=(0, 0, 0, 0), relief=1,
                         command=command, sortOrder=121)
        return root

    def _ju_resbar(self, parent, z=.78):
        """顶部资源栏：玉料/粮食/人口/夯土/水源（真实 state）。"""
        s = self.state
        data = [('bi', '玉料', int(s.jade)), ('bi', '粮食', s.food),
                ('bi', '人口', s.population), ('cong', '夯土', s.material),
                ('jue', '水源', '通' if s.canal else '塞')]
        x0 = -1.35
        for i, (ic, label, val) in enumerate(data):
            x = x0 + i * .52
            self._ju_icon(parent, ic, (x, z), .055)
            self._ju_text(parent, '%s %s' % (label, val), (x+.05, z), .030,
                          color=PAPER, name='res%d' % i, sort=122)

    # =============================================================
    # 图3/5 · 王城圈层地图
    # =============================================================
    def _build_map(self):
        c = self._ju_panel('map', 2.9, 1.72)
        self._ju_resbar(c, .78)
        self._ju_text(c, '王 城 圈 层', (0, .74), .055,
                      color=PAPER, font='kai', align=TextNode.ACenter)
        # 同心圆地图贴图
        tex = self._make_ring_map_tex()
        cm = CardMaker('ringmap'); cm.setFrame(-.72, .72, -.72, .72)
        ring = c.attachNewNode(cm.generate())
        ring.setTexture(tex); ring.setTransparency(TransparencyAttrib.MAlpha)
        ring.setBin('fixed', 105); ring.setPos(-.06, 0, -.05)
        # 圈层标注：沿同心圆上下分布（避开圆心发光与刻度环）
        labels = [('荒野探索', -.06, .66), ('中圈田坊', -.06, .44),
                  ('内心祭坛', -.06, .22), ('河滩采玉', -.06, -.62)]
        for lab, x, z in labels:
            self._ju_text(c, lab, (x, z), .028, color=JADE_HI,
                          align=TextNode.ACenter, name='ring_'+lab)
        # 右上状态卡
        self._ju_text(c, '部族声望 / 玉之庇佑 / 存续', (1.18, .60), .028,
                      color=JADE_HI, align=TextNode.ACenter, name='stat_lbl')
        self._map_stats = self._ju_text(c, '', (1.18, .48), .026,
                                        color=PAPER, align=TextNode.ACenter, name='stats')
        # 花瓣侧栏（左右快捷）
        for i, lab in enumerate(['营建', '玉凿', '祭台']):
            self._ju_btn(c, lab, (-1.20, .30-i*.16), .026, w=.20, h=.075,
                         command=lambda l=lab: self._ju_toast(l), name='ml%d' % i)
        for i, lab in enumerate(['玉琮', '玉璧', '祭品']):
            self._ju_btn(c, lab, (1.20, .30-i*.16), .026, w=.20, h=.075,
                         command=lambda l=lab: self._ju_toast(l), name='mr%d' % i)
        # 底部三按钮
        self._ju_btn(c, '返回漫游', (-.62, -.76), .030, command=self.close_jade_ui, w=.42)
        self._ju_btn(c, '玉契纪事', (0, -.76), .030,
                     command=lambda: self._map_seal.show(), w=.42)
        self._ju_btn(c, '留 影', (.62, -.76), .030, command=lambda: self._ju_toast('留影'), w=.42)
        # 铭刻玉契弹窗（默认隐藏，点"玉契纪事"弹出）
        self._map_seal = c.attachNewNode('seal')
        self._map_seal.setPos(0, 0, -.60)
        self._map_seal.hide()
        cm2 = CardMaker('sealbg'); cm2.setFrame(-.72, .72, -.16, .16)
        sc = self._map_seal.attachNewNode(cm2.generate())
        sc.setColor(*BG_LITE); sc.setBin('fixed', 128)
        self._ju_text(self._map_seal, '铭刻玉契 · 确定保存当前部族进度？',
                      (0, .06), .032, color=PAPER, align=TextNode.ACenter, name='seal_t')
        self._ju_btn(self._map_seal, '铭刻确认', (-.30, -.08), .030,
                     command=self._ju_save, w=.36, h=.08, name='seal_ok')
        self._ju_btn(self._map_seal, '作 罢', (.30, -.08), .030,
                     command=lambda: self._map_seal.hide(), w=.36, h=.08, name='seal_no')
        self._map_root = c

    def _make_ring_map_tex(self, S=512):
        """程序化同心圆地图：玉璧质感 + 多圈刻线 + 中心发光祭坛。"""
        img = PNMImage(S, S, 4)
        cx = cy = S/2
        maxR = S*0.47
        for y in range(S):
            for x in range(S):
                d = math.hypot(x-cx, y-cy)
                if d <= maxR:
                    # 底色：设计稿采样 #5D584B → 外深内浅的玉璧盘
                    v = 1 - d/maxR
                    r = 0.36 + 0.12*v; g = 0.35 + 0.13*v; b = 0.29 + 0.12*v
                    a = .90
                    # 同心刻线：采样线描青 #7A9E91
                    for rr in (0.98, 0.86, 0.72, 0.56, 0.38, 0.20):
                        if abs(d - maxR*rr) < 1.6:
                            r, g, b = 0.48, 0.62, 0.57; a = .95
                    # 细密刻度（外圈）
                    if maxR*0.86 < d < maxR*0.98:
                        ang = math.degrees(math.atan2(y-cy, x-cx))
                        if int(ang) % 6 == 0:
                            r, g, b = 0.44, 0.58, 0.52
                    # 中心祭坛发光：采样 #BFDDCF
                    if d < maxR*0.10:
                        glow = 1 - d/(maxR*0.10)
                        r = 0.55+0.42*glow; g = 0.72+0.26*glow; b = 0.64+0.30*glow; a = 1
                    img.setXelA(x, y, min(1,r), min(1,g), min(1,b), a)
        tex = Texture('ringmap'); tex.load(img)
        return tex

    def _ju_save(self):
        try: self.save()
        except Exception: pass
        self._map_seal.hide()
        self._ju_toast('玉契已铭刻')

    # =============================================================
    # 图2/4 · 礼器·技艺面板（后续方法见 jade_ui_craft.py 内容追加）
    # =============================================================
    # 【craft 面板与叙事页在下方 _build_craft/_build_narrative 实现】

    # =============================================================
    # 面板控制
    # =============================================================
    def _ju_toast(self, msg):
        try:
            self.toast = msg; self.toasting = 4
        except Exception:
            pass

    def open_jade_ui(self, name):
        panel = getattr(self, '_' + name + '_root', None)
        if panel is None: return
        if not self._ju_open:
            # 首次打开：隐藏常驻 HUD（顶部条/标题/目标/操作提示/按钮卡）+ 主菜单节点
            self._ju_hidden = []
            for nm in ('top', 'title', 'stats', 'goal', 'economy',
                       'controls_text', 'prompt', 'message', '_ui_top_card',
                       '_menu_root', '_im_root'):
                obj = getattr(self, nm, None)
                if obj is not None:
                    try:
                        if not obj.isHidden():
                            obj.hide(); self._ju_hidden.append(obj)
                    except Exception:
                        pass
        if self._ju_open and self._ju_open != name:
            getattr(self, '_' + self._ju_open + '_root').hide()
        self._ju_open = name
        self._refresh_jade_ui(name)
        panel.show()
        self.dialog = True
        self.keys.clear()

    def close_jade_ui(self):
        if not self._ju_open: return
        panel = getattr(self, '_' + self._ju_open + '_root', None)
        if panel is not None: panel.hide()
        self._ju_open = None
        self.dialog = False
        # 恢复之前隐藏的 HUD
        for obj in getattr(self, '_ju_hidden', []):
            try: obj.show()
            except Exception: pass
        self._ju_hidden = []

    def toggle_map(self):
        # 主菜单/对话时不响应
        if getattr(self, '_im_open', False) or getattr(self, '_menu_open', False): return
        if getattr(self, 'in_conversation', False): return
        if self._ju_open == 'map': self.close_jade_ui()
        else: self.open_jade_ui('map')

    def toggle_craft(self):
        if getattr(self, '_im_open', False) or getattr(self, '_menu_open', False): return
        if getattr(self, 'in_conversation', False): return
        if self._ju_open == 'craft': self.close_jade_ui()
        else: self.open_jade_ui('craft')

    def _ju_esc(self):
        if getattr(self, '_im_open', False) or getattr(self, '_menu_open', False):
            return   # 主菜单期间 Esc 由菜单/信息层处理
        if self._ju_open:
            self.close_jade_ui()
        else:
            self.pause()

    # =============================================================
    # 图2/4 · 礼器·技艺面板
    # =============================================================
    def _build_craft(self):
        c = self._ju_panel('craft', 2.9, 1.72)
        # 顶部标签栏：5 页全部可点，点击切换内容子容器
        tabs = ['礼器', '仓廪', '技艺', '玉契', '设置']
        self._craft_tab_btns = {}
        self._craft_pages = {}
        for i, tab in enumerate(tabs):
            root = self._ju_btn(c, tab, (-1.10 + i*.55, .74), .034,
                                command=lambda t=tab: self._ju_tab(t),
                                w=.50, h=.10, enabled=True, name='tab'+str(i))
            self._craft_tab_btns[tab] = root
            page = c.attachNewNode('page_' + tab)
            page.setBin('fixed', 102)
            self._craft_pages[tab] = page
        self._craft_cur = '礼器'

        # ---------- 页1：礼器（原内容） ----------
        p = self._craft_pages['礼器']
        # 左侧玉器卡片（主礼器/次礼器/祭祀增益/神佑时长）
        cards = [('cong', '主礼器'), ('bi', '次礼器'),
                 ('huang', '祭祀增益'), ('jue', '神佑时长')]
        for i, (ic, lab) in enumerate(cards):
            x, z = -1.18, .46 - i*.28
            cm = CardMaker('card'); cm.setFrame(-.26, .26, -.115, .115)
            cd = p.attachNewNode(cm.generate())
            cd.setColor(*BG_LITE); cd.setBin('fixed', 104); cd.setPos(x, 0, z)
            self._ju_icon(p, ic, (x-.13, z), .10, name='card'+ic)
            self._ju_text(p, lab, (x+.09, z), .028, color=PAPER, name='cl'+str(i))
        # 中部大玉琮 + 标题 + 卷涡纹印章
        self._ju_icon(p, 'cong', (-.30, .18), .42, name='big_cong')
        self._ju_text(p, '礼器祀神', (-.30, .46), .048, color=PAPER,
                      font='kai', align=TextNode.ACenter, name='ctitle')
        self._ju_text(p, '以玉通神，消耗玉器获得文明增益', (-.30, -.22), .026,
                      color=JADE_HI, align=TextNode.ACenter, name='cdesc')
        self._ju_icon(p, 'vortex', (.02, -.30), .15, name='cseal')
        # 右侧双科技树
        self._build_tree(p, '营建', [('农田增产', 'canal'), ('筑堤防洪', 'dam'),
                                     ('工坊提速', None), ('仓储扩容', None)], .72)
        self._build_tree(p, '祭祀', [('玉质提升', None), ('祭礼增效', None),
                                     ('神佑时长', None), ('灾害减免', None)], .10)
        # 底部：当前玉契 + 部族要务
        self._ju_text(p, '当前玉契', (-.78, -.68), .034, color=JADE_HI, font='kai')
        self._craft_jade = self._ju_text(p, '', (-.78, -.76), .026,
                                         color=PAPER, name='cjade')
        self._ju_text(p, '部族要务', (.42, -.68), .034, color=JADE_HI, font='kai')
        self._craft_task = self._ju_text(p, '', (.42, -.76), .026,
                                         color=PAPER, name='ctask')

        # ---------- 页2-5 ----------
        self._build_granary_page(self._craft_pages['仓廪'])
        self._build_skill_page(self._craft_pages['技艺'])
        self._build_covenant_page(self._craft_pages['玉契'])
        self._build_settings_page(self._craft_pages['设置'])

        # 只显示当前页
        for tab, page in self._craft_pages.items():
            page.hide() if tab != '礼器' else page.show()
        # 通用返回按钮（所有页共用）
        self._ju_btn(c, '返回漫游', (0, -.78), .030,
                     command=self.close_jade_ui, w=.5, h=.09, name='craft_back')
        self._craft_root = c

    def _build_tree(self, parent, title, items, x):
        """竖向点线科技树：青玉圆点 + 连线 + 标签。"""
        self._ju_text(parent, title, (x, .46), .038, color=PAPER,
                      font='kai', align=TextNode.ACenter, name='tree_'+title)
        pts = []
        for i, (lab, flag) in enumerate(items):
            z = .30 - i*.17
            tex = self._icons.get('rivet')
            if tex:
                cm = CardMaker('node'); cm.setFrame(-.035, .035, -.035, .035)
                nd = parent.attachNewNode(cm.generate())
                nd.setTexture(tex); nd.setTransparency(TransparencyAttrib.MAlpha)
                nd.setBin('fixed', 119); nd.setPos(x-.18, 0, z)
            # 节点是否点亮（真实 state）
            lit = bool(getattr(self.state, flag)) if flag else False
            self._ju_text(parent, lab, (x+.02, z), .026,
                          color=JADE_HI if lit else JADE_DK, name='tn'+lab)
            pts.append((x-.18, z))
        # 连线
        if len(pts) >= 2:
            ls = LineSegs(); ls.setThickness(2)
            ls.setColor(JADE_DK[0], JADE_DK[1], JADE_DK[2], .8)
            for a, b in zip(pts, pts[1:]):
                ls.moveTo(a[0], 0, a[1]); ls.drawTo(b[0], 0, b[1])
            ln = parent.attachNewNode(ls.create()); ln.setBin('fixed', 110)

    # ---------- 页2：仓廪（资源与人口经营）----------
    def _build_granary_page(self, p):
        self._ju_text(p, '仓 廪', (0, .52), .055, color=PAPER,
                      font='kai', align=TextNode.ACenter)
        self._ju_text(p, '粮仓储备与族人工商分工 · 收支一目了然', (0, .42), .026,
                      color=JADE_HI, align=TextNode.ACenter)
        # 资源大数字
        self._gra_stats = self._ju_text(p, '', (0, .18), .040,
                                        color=PAPER, align=TextNode.ACenter, name='gra_stats')
        # 收支预测
        self._gra_forecast = self._ju_text(p, '', (0, .10), .024,
                                           color=JADE_HI, align=TextNode.ACenter,
                                           name='gra_fc', sort=122)
        # 人口分工操作（真实 act）
        self._ju_btn(p, '+ 农 民', (-.78, -.40), .030,
                     command=lambda: self._ju_act('farm'), w=.44, h=.10, name='gra_farm')
        self._ju_btn(p, '+ 手工者', (-.02, -.40), .030,
                     command=lambda: self._ju_act('workshop'), w=.44, h=.10, name='gra_work')
        self._ju_btn(p, '休整一日', (.74, -.40), .030,
                     command=lambda: self._ju_act('rest'), w=.44, h=.10, name='gra_rest')
        self._ju_text(p, '分工影响产粮与材料；休整推进一日并结算收支',
                      (0, -.60), .022, color=JADE_DK, align=TextNode.ACenter)

    # ---------- 页3：技艺（营建图纸）----------
    def _build_skill_page(self, p):
        self._ju_text(p, '技 艺', (0, .52), .055, color=PAPER,
                      font='kai', align=TextNode.ACenter)
        self._ju_text(p, '营建图纸 · 点节点查看解锁条件', (0, .42), .026,
                      color=JADE_HI, align=TextNode.ACenter)
        self._build_tree(p, '营建', [('农田增产', 'canal'), ('筑堤防洪', 'dam'),
                                     ('工坊提速', None), ('仓储扩容', None)], -.55)
        self._build_tree(p, '祭礼', [('玉质提升', None), ('祭礼增效', None),
                                     ('神佑时长', None), ('灾害减免', None)], .55)
        self._skill_hint = self._ju_text(p, '点击节点查看条件', (0, -.52), .028,
                                         color=PAPER, align=TextNode.ACenter, name='sk_hint')
        # 节点点击热区：透明，不遮住点线（营建4 + 祭礼4）
        for col, x in enumerate((-.73, .13)):
            for i in range(4):
                z = .30 - i*.17
                root = p.attachNewNode('skhot_%d_%d' % (col, i))
                root.setPos(x, 0, z)
                DirectButton(parent=root, text='', scale=(.16, 1, .05),
                             frameSize=(-1, 1, -1, 1), pos=(0, 0, 0),
                             frameColor=(0, 0, 0, 0), relief=1,
                             command=lambda c=col, j=i: self._ju_skill_node(c, j),
                             sortOrder=121)

    # ---------- 页4：玉契（目标/纪事/存档）----------
    def _build_covenant_page(self, p):
        self._ju_text(p, '玉 契', (0, .52), .055, color=PAPER,
                      font='kai', align=TextNode.ACenter)
        self._ju_text(p, '当前目标', (-.70, .34), .034, color=JADE_HI, font='kai')
        self._cov_goal = self._ju_text(p, '', (-.70, .22), .028,
                                       color=PAPER, name='cov_goal', wrap=30)
        self._ju_text(p, '玉契纪事', (.42, .34), .034, color=JADE_HI, font='kai')
        self._cov_hist = self._ju_text(p, '', (.42, .22), .026,
                                       color=PAPER, name='cov_hist', wrap=26)
        self._ju_btn(p, '铭刻玉契（存档）', (-.62, -.40), .030,
                     command=lambda: self._ju_act('save'), w=.62, h=.10, name='cov_save')
        self._ju_btn(p, '读取玉契', (.42, -.40), .030,
                     command=lambda: self._ju_act('load'), w=.62, h=.10, name='cov_load')
        self._ju_text(p, '目标随游戏进度实时更新 · 铭刻保存当前部族进度',
                      (0, -.62), .024, color=JADE_DK, align=TextNode.ACenter)

    # ---------- 页5：设置 ----------
    def _build_settings_page(self, p):
        self._ju_text(p, '设 置', (0, .52), .055, color=PAPER,
                      font='kai', align=TextNode.ACenter)
        self._ju_text(p, '视野与体验', (0, .36), .030, color=JADE_HI,
                      font='kai', align=TextNode.ACenter)
        self._set_dist = self._ju_text(p, '', (0, .22), .028,
                                       color=PAPER, align=TextNode.ACenter, name='set_dist')
        self._ju_btn(p, '视野 近 <', (-.62, .02), .030,
                     command=lambda: self._ju_dist(-1), w=.55, h=.10, name='set_near')
        self._ju_btn(p, '视野 远 >', (.42, .02), .030,
                     command=lambda: self._ju_dist(1), w=.55, h=.10, name='set_far')
        self._ju_btn(p, '切换沉浸模式', (0, -.22), .030,
                     command=self._ju_immersive, w=.7, h=.10, name='set_imm')
        self._ju_btn(p, '返回主菜单', (0, -.46), .030,
                     command=self._ju_to_menu, w=.7, h=.10, name='set_menu')

    # ---------- 标签切换 / 真实交互 ----------
    def _ju_tab(self, tab):
        self._craft_cur = tab
        for name, page in self._craft_pages.items():
            page.show() if name == tab else page.hide()
        # 高亮当前标签（青玉）；恢复其他
        for name, root in self._craft_tab_btns.items():
            card = root.find('**/+GeomNode')
            if card is not None:
                col = JADE if name == tab else BG_LITE
                try: card.setColor(*col)
                except Exception: pass

    def _refresh_jade_ui_craft(self):
        s = self.state
        # 仓廪页
        grain, meals, made = s.forecast()
        self._gra_stats.setText(
            '粮食 %d    人口 %d    夯土 %d' % (s.food, s.population, s.material))
        self._gra_forecast.setText(
            '农民 %d · 手工 %d  ｜  下次休整：粮 %+d 料 +%d' % (
                s.farmers, s.population - s.farmers, grain - meals, made))
        # 玉契页
        self._cov_goal.setText(s.objective())
        recs = s.history[-4:]
        self._cov_hist.setText('\n'.join(
            '第 %d 日 · 粮+%d 料+%d' % (r['day'], r['grain'], r['made']) for r in recs)
            if recs else '尚无纪事\n（休整后可查看每日收支）')
        # 设置页
        self._set_dist.setText('当前视角距离：%.1f' % getattr(self, 'distance', 7.3))
        # 礼器页
        self._craft_jade.setText('河滩得玉 %s · 献祭玉料 x%d' % (
            '已得' if s.jade else '未得', int(s.jade)))
        self._craft_task.setText(s.objective())

    def _ju_act(self, key):
        """面板内调用真实游戏规则。"""
        msg = self.state.act(key)
        if key == 'rest':
            self.refresh()
            self.sync_ui()
        if key == 'save':
            try: self.save()
            except Exception: pass
        elif key == 'load':
            try: self.load(); self.refresh(); self.sync_ui()
            except Exception: pass
        try: self._refresh_jade_ui_craft()
        except Exception: pass
        self._ju_toast(msg)

    def _ju_skill_node(self, col, i):
        build = [('农田增产', '疏通水渠后自动生效'), ('筑堤防洪', '需 10 材料 · 去堤坝交互点'),
                 ('工坊提速', '安排手工者后休整产出材料'), ('仓储扩容', '待后续开放')]
        jade = [('玉质提升', '献玉祭祀后可提升'), ('祭礼增效', '整修祭坛后生效'),
                ('神佑时长', '献玉后可延长'), ('灾害减免', '筑堤后生效')]
        name, cond = (build if col == 0 else jade)[i]
        self._skill_hint.setText('%s：%s' % (name, cond))

    def _ju_dist(self, d):
        self.distance = max(3.3, min(11, getattr(self, 'distance', 7.3) + d * 1.5))
        self._set_dist.setText('当前视角距离：%.1f' % self.distance)

    def _ju_immersive(self):
        # 复用 ui_theme 的沉浸模式（若加载），否则简单隐藏提示文字
        try:
            import ui_theme
            ui_theme.toggle_immersive()
            self._ju_toast('已切换沉浸模式')
        except Exception:
            obj = getattr(self, 'controls_text', None)
            if obj is not None:
                obj.hide() if not obj.isHidden() else obj.show()

    def _ju_to_menu(self):
        self.close_jade_ui()
        try: self.open_image_menu()
        except Exception: pass

    # =============================================================
    # 图6 · 叙事页（点击任意键启行）
    # =============================================================
    def _build_narrative(self):
        c = self._ju_panel('narrative', 2.2, 1.3)
        self._ju_text(c, '逐玉记', (0, .40), .10, color=JADE_HI,
                      font='kai', align=TextNode.ACenter)
        self._ju_text(c, 'JADE HUNTER', (0, .24), .045, color=PAPER,
                      align=TextNode.ACenter, name='n_en')
        self._ju_text(c, '以玉通神，守此良渚', (0, .10), .034,
                      color=JADE_HI, align=TextNode.ACenter)
        # 玉牌文本框
        cm = CardMaker('nbox'); cm.setFrame(-.72, .72, -.10, .12)
        box = c.attachNewNode(cm.generate())
        box.setColor(*JADE); box.setBin('fixed', 108); box.setPos(0, 0, -.10)
        self._ju_text(c, '洪水将临，部族需玉，王城中记。', (0, -.035), .034,
                      color=INK, align=TextNode.ACenter, name='nbox_txt', sort=122)
        self._ju_text(c, '点击任意键启行', (0, -.40), .030,
                      color=PAPER, align=TextNode.ACenter, name='n_hint')
        self._narrative_root = c

    def _refresh_jade_ui(self, name):
        s = self.state
        if name == 'map':
            self._map_stats.setText('%s · %s\n%d 日' % (
                '兴盛' if s.won else '存续',
                '稳固' if s.dam else '微弱', s.day))
            self._map_seal.hide()
        elif name == 'craft':
            self._refresh_jade_ui_craft()
