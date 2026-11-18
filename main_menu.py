# -*- coding: utf-8 -*-
"""逐玉记 · 主菜单（精简版，只含菜单本身）
================================================
按参考图2实现：游戏启动先进入主菜单——
  左上「逐玉记 · JadeHunt」标题 + 左侧竖排磨砂青按钮列：
    继续游戏(有存档才可点) / 开始新游戏 / 设置 / 制作人员 / 退出
  菜单期间相机俯瞰王城缓慢环绕；点击开始后镜头平滑降落到第三人称。

不含任何其他 UI 改动（无小地图/按钮组/拍照/主题换皮）。
以 MenuOnlyMixin 混入 Demo；init_main_menu() 初始化。

技术要点（踩坑经验）：
  · OnscreenText 不支持 sortOrder → 用 setBin('fixed', 120)
  · 半透明贴图卡片 setBin('fixed', 100)，同 bin 按 priority 排序，文字(120)盖住卡片(100)
  · text='' 的透明 DirectButton 必须显式 frameSize，否则点击区域为零
"""
import math, os
from panda3d.core import TextNode, Filename, CardMaker, TransparencyAttrib, Vec3
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectButton

import ui_theme as T

ROUND_FONT = 'C:/Windows/Fonts/SIMYOU.TTF'   # 幼圆（菜单文字圆润）


def _otext(**kw):
    """OnscreenText 包装：fixed bin 120，保证盖在卡片(100)之上。"""
    sort = kw.pop('sortOrder', 120)
    t = OnscreenText(**kw)
    try:
        t.setBin('fixed', sort)
    except Exception:
        pass
    return t


class MenuOnlyMixin:

    # =============================================================
    # 初始化
    # =============================================================
    def init_main_menu(self):
        self._menu_open = False
        self._landing = False
        self._round_font = self._load_round()
        self._m_tex = dict(
            jade=T._get('jade', lambda: T.make_jade_panel('ui_jade_overlay', 512, 384)))
        self._build_menu()
        self._build_subpanels()
        self.accept('escape', self._esc_handler)
        self.open_menu()

    def _load_round(self):
        try:
            f = self.loader.loadFont(Filename.fromOsSpecific(ROUND_FONT).getFullpath())
            f.setPixelsPerUnit(48)
            return f
        except Exception:
            return getattr(self, 'font', None)

    # =============================================================
    # 图2 磨砂青按钮条：贴图卡 + 玉璧图标 + 文字 + 透明点击层
    # =============================================================
    def _menu_btn(self, container, text, pos, command, enabled=True, wide=1.02):
        root = container.attachNewNode('mbtn')
        root.setPos(*pos)
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
               fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2], .9))
        _otext(parent=root, text=text, font=self._round_font,
               pos=(.06, 0), align=TextNode.ACenter, scale=.040,
               fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2],
                   1 if enabled else .55))
        if enabled and command:
            DirectButton(parent=root, text='', scale=(wide / 2, 1, .17),
                         frameSize=(-1, 1, -1, 1),
                         pos=(0, 0, 0), frameColor=(0, 0, 0, 0), relief=1,
                         command=command, sortOrder=121)
        return root

    def _card_at(self, parent, w, h, pos=(0, 0, 0)):
        mk = CardMaker('cm'); mk.setFrame(-w / 2, w / 2, -h / 2, h / 2)
        c = parent.attachNewNode(mk.generate())
        c.setTexture(self._m_tex['jade'])
        c.setTransparency(TransparencyAttrib.MAlpha)
        c.setPos(*pos)
        c.setBin('fixed', 100)
        return c

    # =============================================================
    # 主菜单
    # =============================================================
    def _build_menu(self):
        c = self._menu_root = self.aspect2d.attachNewNode('main_menu')
        font = T.load_font(self) or self.font
        _otext(parent=c, text='逐玉记', font=font,
               pos=(-1.52, .82), align=TextNode.ALeft, scale=.13,
               fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2], 1), sortOrder=115)
        _otext(parent=c, text='· JadeHunt', font=self._round_font,
               pos=(-1.02, .68), align=TextNode.ALeft, scale=.048,
               fg=(T.EARTH_DARK[0], T.EARTH_DARK[1], T.EARTH_DARK[2], 1), sortOrder=115)
        _otext(parent=c, text='◎ 追寻良渚古玉 · 玉为通神信物',
               font=self._round_font, pos=(-1.50, .60), align=TextNode.ALeft,
               scale=.032, fg=(T.EARTH_DARK[0], T.EARTH_DARK[1], T.EARTH_DARK[2], .95),
               sortOrder=115)
        # 继续游戏：只有存在存档才可点
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
        self._menu_btn(c, '退出', (-1.18, 0, -.42),
                       lambda: self.userExit())
        _otext(parent=c, text='V1.0 · 追寻古玉，守此良渚', font=self._round_font,
               pos=(-1.52, -.86), align=TextNode.ALeft, scale=.026,
               fg=(T.EARTH_DARK[0], T.EARTH_DARK[1], T.EARTH_DARK[2], .8),
               sortOrder=115)
        c.hide()

    def open_menu(self):
        self._menu_open = True
        self._menu_root.show()
        for n in getattr(self, 'markers', {}).values():
            try: n.hide()
            except Exception: pass

    def _menu_start(self, new):
        """点击 继续/新游戏：关菜单 → 直接进入第三人称游戏（无过渡动画）。"""
        self._menu_open = False
        self._menu_root.hide()
        self._close_subs()
        if new:
            self.reset()
        else:
            try: self.load()
            except Exception: pass
        self.toast = '沿石径走向营火，与长者交谈。'; self.toasting = 8

    # -------------------------------------------------------------
    # 子面板：设置 / 制作人员
    # -------------------------------------------------------------
    def _build_subpanels(self):
        self._sub_root = self.aspect2d.attachNewNode('menu_subs')
        s = self._sub_root.attachNewNode('settings')
        self._card_at(s, 2.0, 1.1)
        _otext(parent=s, text='设 置', font=self._round_font, pos=(0, .34),
               align=TextNode.ACenter, scale=.055,
               fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2], 1))
        _otext(parent=s, text='沉浸模式：F10 可随时切换隐藏 HUD',
               font=self._round_font, pos=(0, .08), align=TextNode.ACenter, scale=.034,
               fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2], 1))
        self._menu_btn(s, '视野  近 < > 远', (0, 0, -.12), lambda: self._cycle_dist())
        self._menu_btn(s, '返 回', (0, 0, -.34), lambda: self._close_subs())
        s.hide()
        cr = self._sub_root.attachNewNode('credits')
        self._card_at(cr, 2.0, 1.1)
        _otext(parent=cr, text='制作人员', font=self._round_font, pos=(0, .34),
               align=TextNode.ACenter, scale=.055,
               fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2], 1))
        _otext(parent=cr, text='逐玉记 JadeHunt · 良渚圈层王城生存运营 Demo\n'
                               '世界与玩法 · 良渚神王与你\n'
                               '美术 · 三渲二 大块几何手绘\n'
                               '氛围 · 静谧克制，致敬《光遇》',
               font=self._round_font, pos=(0, .04), align=TextNode.ACenter,
               scale=.030, wordwrap=44,
               fg=(T.JADE_DEEP[0], T.JADE_DEEP[1], T.JADE_DEEP[2], 1))
        self._menu_btn(cr, '返 回', (0, 0, -.34), lambda: self._close_subs())
        cr.hide()
        self._subs = {'settings': s, 'credits': cr}

    def toggle_settings(self):
        if self._menu_open:
            self._subs['credits'].hide()
            s = self._subs['settings']
            s.show() if s.isHidden() else s.hide()

    def toggle_credits(self):
        if self._menu_open:
            self._subs['settings'].hide()
            cr = self._subs['credits']
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
    # 相机：菜单期间俯瞰环绕（update 最前调用）
    # =============================================================
    def menu_camera(self):
        """返回 True 表示本帧相机由菜单接管（update 提前 return）。"""
        if self._menu_open:
            ang = self.t * .12
            self.camera.setPos(26 * math.cos(ang), 30 + 22 * math.sin(ang), 54)
            self.camera.lookAt(0, 36, 0)
            return True
        return False
