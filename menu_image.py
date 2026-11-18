# -*- coding: utf-8 -*-
"""逐玉记 · 设计图直用主菜单（menu_image.py）
================================================
直接用用户提供的设计图 menu_bg.jpg 作为全屏菜单背景（1920×1080，
含标题/按钮列/玉琮祭坛画面/更多纪事），不重画、不动 3D 场景。
在图片按钮的像素位置精确叠加透明可点击区：
  启行新局 / 读取玉契 / 设置 / 制作信息 / 归退 / 更多纪事
点击「启行新局/读取玉契」→ 关菜单进入第三人称游戏。

坐标：设计图 1920×1080，aspect2d 16:9 映射：
  ax = (px/1920*2-1)*(1920/1080);  ay = 1-py/1080*2
按钮区像素中心（PIL 拆解得出）：
  启行新局(198,502) 读取玉契(198,596) 设置(198,691)
  制作信息(198,788) 归退(198,887) 更多纪事(1753,1024)
按钮尺寸约 213×80 px → aspect2d 0.394×0.148

以 ImageMenuMixin 混入 Demo；init_image_menu() 初始化。
"""
import os
from panda3d.core import (
    Filename, CardMaker, TransparencyAttrib, TextNode,
)
from direct.gui.DirectGui import DirectButton
from direct.gui.OnscreenText import OnscreenText

BG_IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      'assets_new', 'ui', 'menu_bg.jpg')
W, H = 1920.0, 1080.0
AR = W / H


def a2d(px, py):
    return (px / W * 2 - 1) * AR, (1 - py / H * 2)


class ImageMenuMixin:

    def init_image_menu(self):
        self._im_open = False
        self._im_root = self.aspect2d.attachNewNode('image_menu')
        # 1) 全屏背景（设计图本身）
        cm = CardMaker('im_bg')
        cm.setFrame(-AR, AR, -1, 1)
        bg = self._im_root.attachNewNode(cm.generate())
        tex = self.loader.loadTexture(Filename.fromOsSpecific(BG_IMG))
        bg.setTexture(tex)
        bg.setBin('fixed', 100)
        # 2) 透明点击区（精确对齐图上按钮）
        btns = [
            ('启行新局', 198, 502, lambda: self._im_start(new=True)),
            ('读取玉契', 198, 596, lambda: self._im_start(new=False)),
            ('设置',     198, 691, lambda: self._im_info('设 置', '沉浸模式 F10 隐藏 HUD\nF5 存档 / F9 读档')),
            ('制作信息', 198, 788, lambda: self._im_info('制作信息', '逐玉记 JadeHunt · 良渚王城生存运营 Demo\n美术 三渲二大块几何 / 渲染 风格化写实')),
            ('归退',     198, 887, lambda: self.userExit()),
            ('更多纪事', 1753, 1024, lambda: self._im_info('纪 事', '以玉通神，守此良渚。\n洪水将临，部族需玉，王城中记。')),
        ]
        self._im_btns = []
        for i, (name, px, py, cmd) in enumerate(btns):
            ax, ay = a2d(px, py)
            root = self._im_root.attachNewNode('im_btn_' + str(i))
            root.setPos(ax, 0, ay)
            # 宽高：更多纪事是小按钮
            w, h = (0.26, 0.075) if name == '更多纪事' else (0.394, 0.148)
            DirectButton(parent=root, text='', scale=(w/2, 1, h/2),
                         frameSize=(-1, 1, -1, 1), pos=(0, 0, 0),
                         frameColor=(0, 0, 0, 0), relief=1,
                         command=cmd, sortOrder=121)
            self._im_btns.append(root)
        # 3) 简易信息浮层（设置/制作信息/纪事）
        self._im_info_layer = self._im_root.attachNewNode('im_info')
        cm2 = CardMaker('im_info_bg'); cm2.setFrame(-.75, .75, -.22, .22)
        ib = self._im_info_layer.attachNewNode(cm2.generate())
        ib.setColor(.24, .22, .18, .95); ib.setBin('fixed', 130)
        self._im_info_title = OnscreenText(parent=self._im_info_layer, text='',
            font=self.font, pos=(0, .10), align=TextNode.ACenter, scale=.05,
            fg=(.82, .91, .86, 1), mayChange=True)
        self._im_info_title.setBin('fixed', 131)
        self._im_info_body = OnscreenText(parent=self._im_info_layer, text='',
            font=self.font, pos=(0, -.02), align=TextNode.ACenter, scale=.032,
            fg=(.90, .87, .78, 1), wordwrap=40, mayChange=True)
        self._im_info_body.setBin('fixed', 131)
        b = DirectButton(parent=self._im_info_layer, text='返 回', text_font=self.font,
            scale=.038, pos=(0, 0, -.15), frameColor=(.66, .80, .74, .85),
            text_fg=(.18, .28, .27, 1), command=lambda: self._im_info_layer.hide(),
            sortOrder=132)
        self._im_info_layer.hide()
        self.open_image_menu()

    def open_image_menu(self):
        self._im_open = True
        self._im_root.show()
        self._im_info_layer.hide()
        # 隐藏游戏常驻 HUD（避免文字透出设计图）
        self._im_hidden_hud = []
        for nm in ('top', 'title', 'stats', 'goal', 'economy',
                   'controls_text', 'prompt', 'message', '_ui_top_card',
                   'kiln_label'):
            obj = getattr(self, nm, None)
            if obj is not None:
                try:
                    obj.hide(); self._im_hidden_hud.append(obj)
                except Exception:
                    pass

    def _im_info(self, title, body):
        self._im_info_title.setText(title)
        self._im_info_body.setText(body)
        self._im_info_layer.show()

    def _im_start(self, new):
        """点击 启行新局/读取玉契：关菜单 → 直接进入第三人称游戏。"""
        self._im_open = False
        self._im_root.hide()
        # 结束对话/面板等残留态
        if getattr(self, '_ju_open', None):
            try: self.close_jade_ui()
            except Exception: pass
        if new:
            self.reset()
        else:
            try: self.load()
            except Exception: pass
        # 恢复游戏 HUD
        for obj in getattr(self, '_im_hidden_hud', []):
            try: obj.show()
            except Exception: pass
        self._im_hidden_hud = []
        self.toast = '沿石径走向营火，与长者交谈。'; self.toasting = 8

    def image_menu_camera(self):
        """菜单期间：不需要相机环绕（背景是图片），直接返回 True 跳过漫游。"""
        return self._im_open
