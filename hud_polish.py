# -*- coding: utf-8 -*-
"""逐玉记 · HUD 静谧低干预优化（hud_polish.py）— 回滚版
================================================
上一稳定版：隶书 + 柔和低饱和字色 + 无方框（靠阴影可读）+ 玉石 icon +
世界标签 + 纯漫游常驻按钮（可返回）。不含参考图贴图顶栏/胶囊那套。

以 HudPolishMixin 混入 Demo，init_hud_polish() 初始化。
主菜单期间不显示任何游戏 HUD（由 enforce_roam_only 的按钮逻辑 + menu_image 隐藏 HUD 保证）。
"""
import os
from panda3d.core import Filename, CardMaker, TransparencyAttrib
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectButton

import jade_icons as ICON

LISU = 'C:/Windows/Fonts/SIMLI.TTF'
LISU2 = 'C:/Windows/Fonts/STLITI.TTF'

# 静谧 · 低干预 · 低饱和：字色柔和、无底板方框，靠阴影保证可读
GOLD     = (0.90, 0.84, 0.70)   # 主字：柔金（降饱和）
JADE_TXT = (0.72, 0.82, 0.76)   # 青玉字：柔青（降饱和）
SHADOW   = (0.04, 0.04, 0.03, 1)


class HudPolishMixin:

    def init_hud_polish(self):
        self._hp_font = self._load_lisu()
        self._icons = getattr(self, '_icons', None) or ICON.make_all()
        self._hp_decor = self.aspect2d.attachNewNode('hud_decor')
        self._roam_only = False
        self._apply_font()
        self._style_world_markers()
        self._decorate()
        self._make_resource_hotzone()
        self._make_roam_button()
        if getattr(self, '_im_open', False) or getattr(self, '_menu_open', False):
            # 主菜单期间：装饰节点和切换按钮都不显示
            try: self._hp_decor.hide()
            except Exception: pass
            try: self._roam_btn.hide()
            except Exception: pass

    # ---------------------------------------------------------
    # 字体 / 文字样式
    # ---------------------------------------------------------
    def _load_lisu(self):
        for path in (LISU, LISU2):
            try:
                f = self.loader.loadFont(Filename.fromOsSpecific(path).getFullpath())
                f.setPixelsPerUnit(48); return f
            except Exception:
                continue
        return getattr(self, 'font', None)

    def _restyle(self, obj, scale=None, color=None, shadow=True):
        if obj is None: return
        try:
            if self._hp_font: obj.setFont(self._hp_font)
            if scale: obj.setScale(scale)
            if color: obj.setFg(color[0], color[1], color[2], 1)
            if shadow: obj.setShadow(SHADOW)
        except Exception:
            pass

    def _apply_font(self):
        self._restyle(getattr(self, 'title', None), .056, GOLD)
        self._restyle(getattr(self, 'stats', None), .038, GOLD)
        self._restyle(getattr(self, 'goal', None), .035, JADE_TXT)
        self._restyle(getattr(self, 'economy', None), .030, GOLD)
        self._restyle(getattr(self, 'prompt', None), .048, GOLD)
        self._restyle(getattr(self, 'message', None), .032, GOLD)
        self._restyle(getattr(self, 'controls_text', None), .026, GOLD)
        self._restyle(getattr(self, 'overlaytext', None), .068, GOLD)
        self._restyle(getattr(self, 'overlaydetail', None), .038, GOLD)

        title = getattr(self, 'title', None)
        if title is not None:
            try: title.setText('逐玉记  ◇  JADE HUNTER')
            except Exception: pass
        ctl = getattr(self, 'controls_text', None)
        if ctl is not None:
            try:
                ctl.setText('WASD 行 ｜ Shift 疾 ｜ 空格 跃 ｜ 右键/方向 环视 ｜ E 互动 ｜ M 圈层 ｜ K 玉契 ｜ H 隐藏界面 ｜ Esc 暂停')
            except Exception: pass
        # 静谧：所有文字去掉底板方框（alpha=0），只留阴影
        for obj in (getattr(self, 'prompt', None), getattr(self, 'controls_text', None),
                    getattr(self, 'goal', None), getattr(self, 'economy', None),
                    getattr(self, 'title', None), getattr(self, 'stats', None),
                    getattr(self, 'message', None)):
            try: obj.node().setCardColor(0, 0, 0, 0)
            except Exception: pass
        # 顶部条保留深褐（参考之前的样子，不额外加贴图）
        top = getattr(self, 'top', None)
        if top is not None:
            try: top['frameColor'] = (.14, .12, .09, .78)
            except Exception: pass

    def _style_world_markers(self):
        """世界标记 → 静谧浮动标签（无方框 + 柔字 + 阴影 + 玉石icon）。"""
        icon_for = {
            'elder': 'cong', 'rest': 'huang', 'canal': 'jue', 'farm': 'bi',
            'workshop': 'yue', 'dam': 'cong', 'jade': 'bi', 'altar': 'cong',
            'cache0': 'yue', 'cache1': 'yue', 'cache2': 'yue',
        }
        markers = getattr(self, 'markers', {}) or {}
        for key, np in markers.items():
            try: tn = np.node()
            except Exception: continue
            steps = [
                lambda: tn.setTextColor(.94, .88, .72, 1),
                lambda: tn.setShadow(SHADOW),
                lambda: tn.setCardColor(0, 0, 0, 0),
                lambda: np.setScale(.30),
            ]
            if self._hp_font:
                steps.insert(0, lambda: tn.setFont(self._hp_font))
            for fn in steps:
                try: fn()
                except Exception: pass
            # 玉石 icon（子节点随 billboard / 父 show-hide）
            ic_key = icon_for.get(key, 'bi')
            tex = self._icons.get(ic_key)
            if tex is None: continue
            try:
                old = np.find('**/hp_marker_icon')
                if not old.isEmpty(): old.removeNode()
                cm = CardMaker('hp_marker_icon')
                s = .34
                cm.setFrame(-s/2, s/2, -.17, .17)
                ic = np.attachNewNode(cm.generate())
                ic.setTexture(tex)
                ic.setTransparency(TransparencyAttrib.MAlpha)
                ic.setY(-0.06); ic.setDepthWrite(False); ic.setBin('fixed', 119)
                name_len = max(1, len(np.node().getText() or '玉'))
                ic.setX(-name_len * .30 - .10); ic.setZ(0)
            except Exception:
                pass
            try:
                np.setDepthWrite(False); np.setBin('fixed', 118)
            except Exception:
                pass

    # ---------------------------------------------------------
    # 装饰图标
    # ---------------------------------------------------------
    def _icon(self, key, x, z, scale=.07, name='ic'):
        tex = self._icons.get(key)
        if tex is None: return None
        cm = CardMaker('hp_' + name)
        cm.setFrame(-scale/2, scale/2, -scale/2, scale/2)
        node = self._hp_decor.attachNewNode(cm.generate())
        node.setTexture(tex)
        node.setTransparency(TransparencyAttrib.MAlpha)
        node.setBin('fixed', 118)
        node.setPos(x, 0, z)
        return node

    def _decorate(self):
        # 标题旁玉璧
        self._icon('bi', -1.745, .90, .050, 'title_bi_l')
        # 资源栏玉石图标一排
        for i, k in enumerate(['jue', 'bi', 'huang', 'cong', 'yue']):
            self._icon(k, .80 + i*.15, .90, .032, 'res_'+k)

    def _make_resource_hotzone(self):
        root = self.aspect2d.attachNewNode('res_hotzone')
        DirectButton(parent=root, text='', scale=(1.60, 1, .12),
                     frameSize=(-1, 1, -1, 1), pos=(0, 0, .87),
                     frameColor=(0, 0, 0, 0), relief=1,
                     command=self._open_supplies, sortOrder=122)

    def _open_supplies(self):
        if self._roam_only: return
        try:
            if getattr(self, '_im_open', False) or getattr(self, '_menu_open', False): return
            if getattr(self, 'in_conversation', False) or getattr(self, '_photo', False): return
            if not getattr(self, '_ju_open', None): self.open_jade_ui('craft')
            self._ju_tab('仓廪'); self._refresh_jade_ui_craft()
        except Exception: pass

    # ---------------------------------------------------------
    # 纯漫游模式（按钮 + H）——按钮永不隐藏，可返回
    # ---------------------------------------------------------
    def _make_roam_button(self):
        """右下角常驻切换按钮：隐藏界面 <-> 显示界面，永远可点。"""
        self._roam_btn = self.aspect2d.attachNewNode('roam_btn')
        self._roam_btn.setPos(1.60, 0, -.94)
        self._roam_lbl = OnscreenText(parent=self._roam_btn, text='◎ 隐藏界面',
                                      font=self._hp_font, pos=(0, 0), align=0,
                                      scale=.030, fg=(.90, .87, .78, 1))
        self._roam_lbl.setShadow(SHADOW)
        self._roam_lbl.setBin('fixed', 123)
        cm = CardMaker('roam_bg'); cm.setFrame(-.19, .19, -.038, .038)
        card = self._roam_btn.attachNewNode(cm.generate())
        card.setColor(.30, .28, .22, .32); card.setBin('fixed', 122)
        card.setDepthWrite(False)
        DirectButton(parent=self._roam_btn, text='', scale=(.19, 1, .038),
                     frameSize=(-1, 1, -1, 1), pos=(0, 0, 0),
                     frameColor=(0, 0, 0, 0), relief=1,
                     command=self.toggle_roam_only, sortOrder=124)
        self.accept('h', self.toggle_roam_only)

    def toggle_roam_only(self):
        if getattr(self, '_im_open', False): return
        self._roam_only = not self._roam_only
        try: self._roam_lbl.setText('◎ 显示界面' if self._roam_only else '◎ 隐藏界面')
        except Exception: pass
        text_objs = [getattr(self, n, None) for n in (
            'top', 'title', 'stats', 'goal', 'economy', 'controls_text',
            'prompt', 'message', '_ui_top_card')]
        for obj in text_objs + [self._hp_decor]:
            if obj is None: continue
            try: obj.hide() if self._roam_only else obj.show()
            except Exception: pass
        for np in (getattr(self, 'markers', {}) or {}).values():
            try: np.hide() if self._roam_only else np.show()
            except Exception: pass
        if not self._roam_only:
            try: self.toast = '已退出纯漫游 · 界面恢复'; self.toasting = 3
            except Exception: pass

    def enforce_roam_only(self):
        """update 末尾：主菜单时隐藏所有游戏HUD(含切换按钮)；纯漫游时压制标记/文字。"""
        in_menu = getattr(self, '_im_open', False) or getattr(self, '_menu_open', False)
        btn = getattr(self, '_roam_btn', None)
        if btn is not None:
            try: btn.hide() if in_menu else btn.show()
            except Exception: pass
        # 主菜单期间隐藏装饰图标；进游戏后恢复（纯漫游除外）
        try:
            if in_menu or self._roam_only:
                self._hp_decor.hide()
            else:
                self._hp_decor.show()
        except Exception: pass
        if not self._roam_only: return
        for np in (getattr(self, 'markers', {}) or {}).values():
            try: np.hide()
            except Exception: pass
        for name in ('title', 'stats', 'goal', 'economy', 'controls_text',
                     'prompt', 'message', 'top'):
            obj = getattr(self, name, None)
            if obj is not None:
                try: obj.hide()
                except Exception: pass
