# -*- coding: utf-8 -*-
"""逐玉记 JadeHunt · 主菜单 + 图形化 HUD + 拍照模式
================================================
参考两图：
  图2 主菜单：左上美术字标题「逐玉记 · JadeHunt」、左侧竖排磨砂青圆角按钮
    （继续游戏 / 开始新游戏 / 设置 / 制作人员 / 退出），按钮左侧玉璧小图标。
    游戏启动先进入此界面；菜单期间相机俯瞰王城缓慢环绕；
    点击「继续游戏 / 开始新游戏」镜头平滑降落回第三人称。
  图1 HUD：左上圆形小地图 + 日期徽章；右上功能按钮组(带键位角标)；
    底部中央图形交互按钮组（拍照Q / 互动E / 玉光F）；提示用圆润幼圆字体。
  拍照模式：Q 进入，隐藏 HUD，四角取景框 + 快门，拍照白闪反馈。

以 MenuMixin 混入 Demo；init_menu() 初始化。
"""
import math, os
from panda3d.core import (
    TextNode, LineSegs, NodePath, Vec3, Filename, TransparencyAttrib,
)
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame, DirectButton

import ui_theme as T

def _otext(**kw):
    """OnscreenText 包装：放进 fixed bin（priority 120），保证盖在卡片(100)之上。"""
    sort = kw.pop('sortOrder', 120)
    t = OnscreenText(**kw)
    try:
        t.setBin('fixed', sort)
    except Exception:
        pass
    return t


ROUND_FONT = 'C:/Windows/Fonts/SIMYOU.TTF'   # 幼圆：圆润提示字体


class MenuMixin:

    # =============================================================
    # 初始化
    # =============================================================
    def init_menu(self):
        self._menu_open = False
        self._landing = False
        self._photo = False
        self._round_font = self._load_round()
        jade = T._get('jade', lambda: T.make_jade_panel('ui_jade_overlay', 512, 384))
        btn = T._get('btn', lambda: T.make_jade_button('ui_jade_btn', 128, 64, hover=False))
        self._m_tex = dict(jade=jade, btn=btn)

        self._build_minimap()
        self._build_date_badge()
        self._build_corner_buttons()
        self._build_bottom_buttons()
        self._build_menu()
        self._build_photo()
        self._build_subpanels()

        # 快捷键
        self.accept('q', self.toggle_photo)   # 拍照模式（事件弹窗已改 Y 键）

        # 提示类文字换圆润幼圆字体（用户要求更圆润）
        for name in ('prompt', 'message', 'controls_text'):
            obj = getattr(self, name, None)
            if obj is not None:
                try: obj.setFont(self._round_font)
                except Exception: pass

        # 启动即进入主菜单
        self.open_menu()

    def _load_round(self):
        try:
            f = self.loader.loadFont(Filename.fromOsSpecific(ROUND_FONT).getFullpath())
            f.setPixelsPerUnit(48)
            return f
        except Exception:
            return getattr(self, 'font', None)

    # =============================================================
    # 通用：图形按钮（玉牌贴图底 + 符号 + 右下角键位角标）
    # =============================================================
    def _gbtn(self, container, glyph, key_label, pos, size=.16, command=None,
              name='gb', glyph_scale=.062):
        """图1式圆角图标按钮：玉牌贴图卡片 + 居中大符号 + 右下角键位小字。"""
        root = container.attachNewNode('gbtn_' + name)
        root.setPos(*pos)
        card = root.attachNewNode('card_' + name)
        cm = card.node()
        # 用 CardMaker 铺方形玉牌底
        from panda3d.core import CardMaker
        mk = CardMaker('cm_' + name)
        mk.setFrame(-size / 2, size / 2, -size / 2, size / 2)
        card = root.attachNewNode(mk.generate())
        card.setTexture(self._m_tex['btn'])
        card.setTransparency(TransparencyAttrib.MAlpha)
        card.setBin('fixed', 100)
        g = _otext(parent=root, text=glyph, font=self._round_font,
                         pos=(0, .012), align=TextNode.ACenter, scale=glyph_scale,
                         fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2], 1),
                         mayChange=True, sortOrder=120)
        if key_label:
            _otext(parent=root, text=key_label, font=self._round_font,
                         pos=(size / 2 - .045, -size / 2 + .028),
                         align=TextNode.ACenter, scale=.030,
                         fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2], .95),
                         sortOrder=120)
        # 透明 DirectButton 提供点击区
        if command:
            DirectButton(parent=root, text='', scale=size,
                         frameSize=(-.5, .5, -.5, .5),
                         pos=(0, 0, 0), frameColor=(0, 0, 0, 0), relief=1,
                         command=command, sortOrder=121)
        return root

    def _menu_btn(self, container, text, pos, command, enabled=True, wide=1.02):
        """图2式磨砂青圆角条按钮：贴图卡 + 左侧玉璧符号 + 文字。"""
        root = container.attachNewNode('mbtn')
        root.setPos(*pos)
        from panda3d.core import CardMaker
        mk = CardMaker('cm')
        mk.setFrame(-wide / 2, wide / 2, -.115, .115)
        card = root.attachNewNode(mk.generate())
        card.setTexture(self._m_tex['jade'])
        card.setTransparency(TransparencyAttrib.MAlpha)
        card.setBin('fixed', 100)
        if not enabled:
            card.setColorScale(.62, .62, .62, .8)
        _otext(parent=root, text='◎', font=self._round_font,
                     pos=(-wide / 2 + .10, 0), align=TextNode.ACenter, scale=.040,
                     fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2], .9),
                     sortOrder=120)
        _otext(parent=root, text=text, font=self._round_font,
                     pos=(.06, 0), align=TextNode.ACenter, scale=.040,
                     fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2],
                         1 if enabled else .55),
                     sortOrder=120)
        if enabled and command:
            DirectButton(parent=root, text='', scale=(wide / 2, 1, .17),
                         frameSize=(-1, 1, -1, 1),
                         pos=(0, 0, 0), frameColor=(0, 0, 0, 0), relief=1,
                         command=command, sortOrder=121)
        return root

    # =============================================================
    # 图1：左上圆形小地图 + 日期徽章
    # =============================================================
    def _build_minimap(self):
        tex = self._make_minimap_tex()
        self._mm_root = self.aspect2d.attachNewNode('minimap')
        self._mm_root.setPos(-1.56, 0, .74)
        from panda3d.core import CardMaker
        mk = CardMaker('mm'); mk.setFrame(-.19, .19, -.19, .19)
        c = self._mm_root.attachNewNode(mk.generate())
        c.setTexture(tex); c.setTransparency(TransparencyAttrib.MAlpha)
        c.setBin('fixed', 100)
        # 指北箭头（随 yaw 旋转）
        self._mm_arrow = _otext(parent=self._mm_root, text='▲',
                                      font=self._round_font, pos=(0, -.012),
                                      align=TextNode.ACenter, scale=.085,
                                      fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2], .95),
                                      sortOrder=120)

    def _make_minimap_tex(self):
        from panda3d.core import PNMImage, Texture
        img = PNMImage(256, 256, 4)
        cx = cy = 128
        # 外圈玉环 + 内盘（低饱和淡青）
        for y in range(256):
            for x in range(256):
                d = math.hypot(x - cx, y - cy)
                if d <= 120:
                    a = .82 if d <= 104 else .95
                    v = .74 + .10 * (1 - d / 120)
                    img.setXelA(x, y, .58 * v, .78 * v, .73 * v, a)
                elif d <= 128:
                    img.setXelA(x, y, .30, .42, .40, .9)   # 边环
        # 同心刻度环
        for r in (36, 66, 96):
            for i in range(360):
                ang = math.radians(i)
                for k in (0, 1):
                    px = int(cx + math.cos(ang) * (r + k))
                    py = int(cy + math.sin(ang) * (r + k))
                    if 0 <= px < 256 and 0 <= py < 256:
                        rr, gg, bb, aa = img.getXelA(px, py)
                        img.setXelA(px, py, rr * .82, gg * .82, bb * .82, min(1, aa + .12))
        # 北向标记 N
        for dx in range(-3, 4):
            for dy in range(6):
                px, py = cx + dx, cy - 112 + dy
                if 0 <= px < 256 and 0 <= py < 256:
                    img.setXelA(px, py, .10, .17, .16, .95)
        tex = Texture('minimap'); tex.load(img)
        return tex

    def _build_date_badge(self):
        """日期徽章：小地图右侧圆角胶囊「第 N 日 · DAY N」"""
        self._date_root = self.aspect2d.attachNewNode('date_badge')
        self._date_root.setPos(-1.22, 0, .74)
        from panda3d.core import CardMaker
        mk = CardMaker('db'); mk.setFrame(0, .56, -.115, .115)
        c = self._date_root.attachNewNode(mk.generate())
        c.setTexture(self._m_tex['jade']); c.setTransparency(TransparencyAttrib.MAlpha)
        c.setBin('fixed', 100)
        self._date_text = _otext(parent=self._date_root, text='第 0 日',
                                       font=self._round_font, pos=(.28, 0),
                                       align=TextNode.ACenter, scale=.046,
                                       fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2], 1),
                                       mayChange=True, sortOrder=120)

    def update_minimap(self):
        """每帧由 update 调用：箭头随朝向旋转、日期刷新。"""
        try:
            if not self._mm_root.isHidden():
                self._mm_arrow.setR(-self.yaw)
        except Exception:
            pass
        try:
            self._date_text.setText('第 %d 日' % self.state.day)
        except Exception:
            pass

    # =============================================================
    # 图1：右上功能按钮组 + 底部交互按钮组
    # =============================================================
    def _build_corner_buttons(self):
        c = self._hud_extra = self.aspect2d.attachNewNode('hud_corner')
        for i, (glyph, key, cmd) in enumerate([
                ('◎', 'P', lambda: self.toggle_screen('hero')),
                ('书', 'H', lambda: self.toggle_screen('journal')),
                ('≡', 'O', lambda: self.toggle_settings()),
                ('？', 'F1', lambda: self.toggle_screen('home'))]):
            self._gbtn(c, glyph, key, (1.22 + i * .21, 0, .70), .17, cmd,
                       name='c%d' % i, glyph_scale=.055)

    def _build_bottom_buttons(self):
        c = self._hud_bottom = self.aspect2d.attachNewNode('hud_bottom')
        self._gbtn(c, '拍', 'Q', (-.55, 0, -.84), .19, self.toggle_photo,
                   name='cam', glyph_scale=.075)
        self._gbtn(c, 'E', '', (0, 0, -.84), .19,
                   lambda: self.interact() if not self.dialog else None,
                   name='use', glyph_scale=.070)
        self._gbtn(c, '◆', 'F', (.55, 0, -.84), .19, self.demo_all_jade_fx,
                   name='fx', glyph_scale=.065)

    # =============================================================
    # 图2：主菜单
    # =============================================================
    def _build_menu(self):
        c = self._menu_root = self.aspect2d.attachNewNode('main_menu')
        # 左上标题
        _otext(parent=c, text='逐玉记', font=T.load_font(self) or self.font,
                     pos=(-1.52, .82), align=TextNode.ALeft, scale=.13,
                     fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2], 1), sortOrder=115)
        _otext(parent=c, text='· JadeHunt', font=self._round_font,
                     pos=(-1.02, .68), align=TextNode.ALeft, scale=.048,
                     fg=(T.EARTH_DARK[0], T.EARTH_DARK[1], T.EARTH_DARK[2], 1), sortOrder=115)
        _otext(parent=c, text='◎ 追寻良渚古玉 · 玉为通神信物',
                     font=self._round_font, pos=(-1.50, .60), align=TextNode.ALeft,
                     scale=.032, fg=(T.EARTH_DARK[0], T.EARTH_DARK[1], T.EARTH_DARK[2], .95),
                     sortOrder=115)
        # 左侧按钮列
        try:
            import main as _main
            has_save = (_main.SAVE / 'save.json').exists()
        except Exception:
            has_save = False
        self._menu_btn(c, '继续游戏', (-1.18, 0, .42),
                       lambda: self._menu_start(new=False), enabled=has_save)
        self._menu_btn(c, '开始新游戏', (-1.18, 0, .21),
                       lambda: self._menu_start(new=True))
        self._menu_btn(c, '设置', (-1.18, 0, 0.0),
                       lambda: self.toggle_settings())
        self._menu_btn(c, '制作人员', (-1.18, 0, -.21),
                       lambda: self.toggle_credits())
        self._menu_btn(c, '退出', (-1.18, 0, -.38),
                       lambda: self.userExit())
        _otext(parent=c, text='V1.0 · 静谧克制 · 玉为通神', font=self._round_font,
                     pos=(-1.52, -.86), align=TextNode.ALeft, scale=.026,
                     fg=(T.EARTH_DARK[0], T.EARTH_DARK[1], T.EARTH_DARK[2], .8),
                     sortOrder=115)
        c.hide()

    def open_menu(self):
        self._menu_open = True
        self._menu_root.show()
        self._set_hud(False)
        self._hud_extra.hide(); self._hud_bottom.hide()
        self._mm_root.hide(); self._date_root.hide()
        for n in getattr(self, 'markers', {}).values():
            try: n.hide()
            except Exception: pass

    def _menu_start(self, new):
        """点击 继续/新游戏：关菜单 → 镜头平滑降落到角色。"""
        self._menu_open = False
        self._menu_root.hide()
        self._close_subs()
        self._set_hud(True)
        self._hud_extra.show(); self._hud_bottom.show()
        self._mm_root.show(); self._date_root.show()
        if new:
            self.reset()
        else:
            try: self.load()
            except Exception: pass
        # 计算降落数值（main.py 相机公式）
        pos = self.player.getPos()
        angle = math.radians(self.yaw); elev = math.radians(self.pitch)
        target = pos + Vec3(0, 0, 1.35)
        offset = Vec3(math.sin(angle) * self.distance * math.cos(elev),
                      -math.cos(angle) * self.distance * math.cos(elev),
                      math.sin(elev) * self.distance)
        self._land_from = self.camera.getPos()
        self._land_to = target + offset
        self._land_look = target
        self._landing = True
        self._land_t0 = self.t
        self.toast = '沿石径走向营火，与长者交谈。'; self.toasting = 8

    # -------------------------------------------------------------
    # 子面板：设置 / 制作人员
    # -------------------------------------------------------------
    def _build_subpanels(self):
        self._sub_root = self.aspect2d.attachNewNode('menu_subs')
        self._sub_root.setBin('fixed', 130)
        # 设置面板
        s = self._sub_root.attachNewNode('settings')
        self._card_at(s, 2.0, 1.1, (0, 0, 0))
        _otext(parent=s, text='设 置', font=self._round_font, pos=(0, .34),
                     align=TextNode.ACenter, scale=.055,
                     fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2], 1), sortOrder=132)
        self._set_hint = _otext(parent=s, text='沉浸模式：关   （F10 可随时切换）',
                                      font=self._round_font, pos=(0, .08),
                                      align=TextNode.ACenter, scale=.034,
                                      fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2], 1),
                                      mayChange=True, sortOrder=132)
        self._menu_btn(s, '视野  近 ◀ ▶ 远', (0, 0, -.12), lambda: self._cycle_dist())
        self._menu_btn(s, '返 回', (0, 0, -.34), lambda: self._close_subs())
        s.hide()
        # 制作人员
        cr = self._sub_root.attachNewNode('credits')
        self._card_at(cr, 2.0, 1.1, (0, 0, 0))
        _otext(parent=cr, text='制作人员', font=self._round_font, pos=(0, .34),
                     align=TextNode.ACenter, scale=.055,
                     fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2], 1), sortOrder=132)
        _otext(parent=cr, text='逐玉记 JadeHunt · 良渚圈层王城生存运营 Demo\n'
                                     '世界与玩法 · 良渚神王与你\n'
                                     '美术 · 三渲二 大块几何手绘\n'
                                     '音乐氛围 · 静谧克制，致敬《光遇》',
                     font=self._round_font, pos=(0, .04), align=TextNode.ACenter,
                     scale=.030, wordwrap=44,
                     fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2], 1), sortOrder=132)
        self._menu_btn(cr, '返 回', (0, 0, -.34), lambda: self._close_subs())
        cr.hide()
        self._subs = {'settings': s, 'credits': cr}
        self.accept('o', self.toggle_settings)
        self.accept('escape', self._esc_handler)

    def _card_at(self, parent, w, h, pos):
        from panda3d.core import CardMaker
        mk = CardMaker('cm'); mk.setFrame(-w / 2, w / 2, -h / 2, h / 2)
        c = parent.attachNewNode(mk.generate())
        c.setTexture(self._m_tex['jade'])
        c.setTransparency(TransparencyAttrib.MAlpha)
        c.setPos(*pos)
        c.setBin('fixed', 100)
        return c

    def toggle_settings(self):
        if self._menu_open:
            cr = self._subs['credits']
            s = self._subs['settings']
            cr.hide()
            s.show() if s.isHidden() else s.hide()

    def toggle_credits(self):
        if self._menu_open:
            s = self._subs['settings']
            cr = self._subs['credits']
            s.hide()
            cr.show() if cr.isHidden() else cr.hide()

    def _close_subs(self):
        for s in self._subs.values():
            s.hide()

    def _esc_handler(self):
        if self._menu_open:
            self._close_subs()
        else:
            self.pause()

    def _cycle_dist(self):
        self.distance = 4.5 if self.distance > 6 else (7.5 if self.distance < 6 else 10)

    # =============================================================
    # 拍照模式
    # =============================================================
    def _build_photo(self):
        c = self._photo_root = self.aspect2d.attachNewNode('photo_mode')
        # 四角取景框（LineSegs，留白 8%）
        ls = LineSegs(); ls.setThickness(6)
        col = (0.92, 0.98, 0.96, 1.0)
        ls.setColor(col[0], col[1], col[2], col[3])
        m, L = .12, .13
        for sx in (-1, 1):
            for sy in (-1, 1):
                x = sx * (1.78 - m); z = sy * (1.0 - m)
                ls.moveTo(x - sx * L, 0, z); ls.drawTo(x, 0, z)
                ls.moveTo(x, 0, z); ls.drawTo(x, 0, z - sy * L)
        lsnode = c.attachNewNode(ls.create()); lsnode.setBin('fixed', 128)
        _otext(parent=c, text='拍照模式 · Q 退出 · 快门保存', font=self._round_font,
                     pos=(0, .90), align=TextNode.ACenter, scale=.034,
                     fg=(T.JADE_PALE[0], T.JADE_PALE[1], T.JADE_PALE[2], 1), sortOrder=130)
        # 快门按钮
        self._gbtn(c, '○', '', (0, 0, -.82), .17, self._shutter, name='shutter',
                   glyph_scale=.085)
        # 白闪反馈层
        from panda3d.core import CardMaker
        mk = CardMaker('flash'); mk.setFrame(-1.8, 1.8, -1.05, 1.05)
        self._flash = c.attachNewNode(mk.generate())
        self._flash.setColor(1, 1, 1, 0)
        self._flash.setTransparency(TransparencyAttrib.MAlpha)
        self._flash.setBin('fixed', 200)
        c.hide()

    def toggle_photo(self):
        if self._menu_open or getattr(self, 'state', None) is None:
            return
        if getattr(self, 'in_conversation', False):
            try: self.end_dialogue()
            except Exception: pass
        self._photo = not self._photo
        if self._photo:
            self._set_hud(False)
            self._hud_extra.hide(); self._hud_bottom.hide()
            self._mm_root.hide(); self._date_root.hide()
            for n in getattr(self, 'markers', {}).values():
                try: n.hide()
                except Exception: pass
            self._photo_root.show()
        else:
            self._photo_root.hide()
            self._set_hud(not getattr(self, '_ui_immersive', False))
            self._hud_extra.show(); self._hud_bottom.show()
            self._mm_root.show(); self._date_root.show()

    def _shutter(self):
        """拍照：保存截图 + 白闪反馈。"""
        try:
            self.screenshot()
        except Exception:
            pass
        self._flash.setColor(1, 1, 1, .85)
        def fade(task):
            a = self._flash.getColor()[3] - task.getDt() * 1.8
            if a <= 0:
                self._flash.setColor(1, 1, 1, 0)
                return task.done
            self._flash.setColor(1, 1, 1, a)
            return task.cont
        self.taskMgr.add(fade, 'photo_flash')

    # =============================================================
    # HUD 显隐
    # =============================================================
    def _set_hud(self, visible):
        for name in ('top', 'title', 'stats', 'goal', 'economy',
                     'controls_text', 'message', 'prompt', '_ui_top_card'):
            obj = getattr(self, name, None)
            if obj is None: continue
            try: obj.show() if visible else obj.hide()
            except Exception: pass

    # =============================================================
    # 相机：菜单俯瞰环绕 / 降落插值（在 update 最前被调用）
    # =============================================================
    def menu_camera(self):
        """返回 True 表示本帧相机由菜单/降落接管（update 提前 return）。"""
        if self._menu_open:
            ang = self.t * .12
            self.camera.setPos(26 * math.cos(ang), 30 + 22 * math.sin(ang), 54)
            self.camera.lookAt(0, 36, 0)
            return True
        if self._landing:
            t01 = min(1.0, (self.t - self._land_t0) / 1.6)
            ease = t01 * t01 * (3 - 2 * t01)
            pos = self._land_from + (self._land_to - self._land_from) * ease
            self.camera.setPos(pos)
            self.camera.lookAt(self._land_look)
            if t01 >= 1.0:
                self._landing = False
            return True
        return False
