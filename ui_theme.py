# -*- coding: utf-8 -*-
"""逐玉记 JadeHunt · UI 主题模块
================================================
把游戏现有的 OnscreenText / DirectFrame / DirectButton 统一换皮为：
  · 透青玉面板（祭祀/事件/叙事/玉相关）—— 半透淡青、柔和内漫光、卷涡纹角饰
  · 夯土粗陶面板（资源/建造/日志/帮助）—— 哑光土黄灰褐、风化肌理、玉璧印记

设计红线：无竹、无玻璃拟态、无红色警报、无金色霓虹、无密集进度条。
所有纹样只做几何化局部点缀，不满铺。

关键约束：不删除现有的 OnscreenText 对象（update()/sync_ui() 每帧按名字引用它们），
只修改其字体/颜色/尺寸/位置；背景面板用带贴图的 CardMaker 卡片垫在文字后面。
"""
import math, os
from panda3d.core import (
    PNMImage, Texture, Filename, CardMaker, Vec4,
    TextNode, TransparencyAttrib,
)

# ---------- 色彩系统（规范值，0..1）----------
JADE        = (0.58, 0.78, 0.73)   # #94C8BB 青玉主色
JADE_PALE   = (0.74, 0.86, 0.82)   # 淡青高光
JADE_DEEP   = (0.18, 0.28, 0.27)   # #2E4844 深墨青（正文）
EARTH       = (0.66, 0.55, 0.43)   # #A88C6E 夯土棕
EARTH_DARK  = (0.42, 0.34, 0.26)   # 深夯土
SAND        = (0.85, 0.78, 0.66)   # #D9C8A9 枯草米黄

FONT_PATH = 'C:/Windows/Fonts/Noto Sans SC (TrueType).otf'
FONT_PATH_FB = 'C:/Windows/Fonts/Noto Sans SC (TrueType).otf'
_OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets_new', 'ui')
os.makedirs(_OUT_DIR, exist_ok=True)


def _hex(c):
    return (int(c[0]*255), int(c[1]*255), int(c[2]*255))


def _rrect_alpha(x, y, w, h, r):
    """圆角矩形内部判定（像素坐标，左上原点）。"""
    cx = min(max(x, r), w - r)
    cy = min(max(y, r), h - r)
    dx, dy = x - cx, y - cy
    return (dx*dx + dy*dy) <= r*r


def _spiral(img, cx, cy, rad, col, alpha=0.45):
    """画一个简化良渚卷涡纹（单线螺旋），用于面板角部点缀。"""
    steps = 90
    prev = None
    for i in range(steps):
        t = i / (steps - 1)
        ang = t * math.tau * 1.6
        rr = rad * (1.0 - t * 0.78)
        px = cx + math.cos(ang) * rr
        py = cy + math.sin(ang) * rr
        if prev:
            #  Bresenham-ish 连线：密集插值
            for k in range(6):
                ix = int(prev[0] + (px - prev[0]) * k / 6)
                iy = int(prev[1] + (py - prev[1]) * k / 6)
                if 0 <= ix < img.getXSize() and 0 <= iy < img.getYSize():
                    r, g, b, a = img.getXelA(ix, iy)
                    img.setXelA(ix, iy, col[0], col[1], col[2],
                                min(1.0, a + alpha))
        prev = (px, py)


def _jade_bi(img, cx, cy, rad, col, alpha=0.4):
    """画一枚简化玉璧（同心圆环 + 中心孔），作为项目印记/图标底。"""
    w, h = img.getXSize(), img.getYSize()
    for ang_i in range(360):
        ang = math.radians(ang_i)
        for rr in (rad, rad*0.72, rad*0.30):
            px = int(cx + math.cos(ang) * rr)
            py = int(cy + math.sin(ang) * rr)
            if 0 <= px < w and 0 <= py < h:
                r, g, b, a = img.getXelA(px, py)
                img.setXelA(px, py, col[0], col[1], col[2], min(1.0, a + alpha))


def make_jade_panel(name='ui_jade', w=512, h=256, glow=True):
    """生成透青玉面板贴图：半透淡青、柔和内漫光、圆角、角部卷涡纹。"""
    img = PNMImage(w, h, 4)
    # 新建 PNMImage 默认全透明，无需 fill
    base = _hex(JADE)
    edge = 6
    rad = 26
    for y in range(h):
        for x in range(w):
            if not _rrect_alpha(x, y, w, h, rad):
                continue
            # 柔和内漫光：中心略亮、边缘略暗，低对比
            nx = (x - w/2) / (w/2); ny = (y - h/2) / (h/2)
            d = min(1.0, math.sqrt(nx*nx*0.7 + ny*ny*0.5))
            lift = 0.10 * (1 - d) if glow else 0
            # 边缘一圈稍深，模拟玉料断口
            near_edge = (x < edge or x > w-edge or y < edge or y > h-edge)
            shade = 0.86 if near_edge else 1.0
            rr = min(255, int((base[0] + 22*lift/0.1*0.1) * shade))
            gg = min(255, int((base[1] + 18*lift/0.1*0.1) * shade))
            bb = min(255, int((base[2] + 16*lift/0.1*0.1) * shade))
            # 半透：整体 alpha 0.86，中心略高（保留玉质通透感同时保证文字可读）
            a = 0.82 + 0.10 * (1 - d)
            img.setXelA(x, y, rr/255, gg/255, bb/255, min(0.9, a))
    # 角部卷涡纹（淡墨青，仅两角）
    dark = _hex(JADE_DEEP)
    _spiral(img, 34, 34, 18, [v/255 for v in dark], 0.30)
    _spiral(img, w-34, h-34, 18, [v/255 for v in dark], 0.30)
    path = os.path.join(_OUT_DIR, name + '.png')
    img.write(Filename.fromOsSpecific(path))
    tex = Texture(name)
    tex.load(img)
    return tex, path


def make_earth_panel(name='ui_earth', w=512, h=128, bi_mark=True):
    """生成夯土粗陶面板贴图：土黄灰褐、哑光风化肌理、角落玉璧印记。"""
    import random
    rng = random.Random(20261117)
    img = PNMImage(w, h, 4)
    # 新建 PNMImage 默认全透明，无需 fill
    base = _hex(EARTH)
    rad = 14
    # 预生成少量风化斑点
    spots = [(rng.randrange(w), rng.randrange(h), rng.uniform(.04, .10)) for _ in range(90)]
    for y in range(h):
        for x in range(w):
            if not _rrect_alpha(x, y, w, h, rad):
                continue
            # 粗糙肌理：小块噪声 + 竖向夯土层理
            n = rng.uniform(-0.05, 0.05)
            layer = 0.03 * math.sin(y * 0.35)
            v = 1 + n + layer
            rr = min(255, int(base[0] * v)); gg = min(255, int(base[1] * v)); bb = min(255, int(base[2] * v))
            a = 0.88
            img.setXelA(x, y, rr/255, gg/255, bb/255, a)
    # 风化斑点（浅/深）
    for (sx, sy, sv) in spots:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                x, y = sx+dx, sy+dy
                if 0 <= x < w and 0 <= y < h and _rrect_alpha(x, y, w, h, rad):
                    r, g, b, a = img.getXelA(x, y)
                    f = 1 - sv if (dx+dy) % 2 else 1 + sv*0.5
                    img.setXelA(x, y, min(1,r*f), min(1,g*f), min(1,b*f), a)
    # 角落玉璧印记（淡青，微型）
    if bi_mark:
        _jade_bi(img, 26, h-26, 12, [v/255 for v in _hex(JADE_PALE)], 0.5)
    path = os.path.join(_OUT_DIR, name + '.png')
    img.write(Filename.fromOsSpecific(path))
    tex = Texture(name)
    tex.load(img)
    return tex, path


def make_jade_button(name='ui_jade_btn', w=128, h=64, hover=False):
    """生成小玉牌按钮贴图（常态 / hover 柔光）。"""
    img = PNMImage(w, h, 4)
    base = _hex(JADE_PALE if hover else JADE)
    rad = 16
    for y in range(h):
        for x in range(w):
            if not _rrect_alpha(x, y, w, h, rad):
                continue
            nx = (x-w/2)/(w/2); ny = (y-h/2)/(h/2)
            d = min(1.0, math.sqrt(nx*nx + ny*ny))
            glow = (1-d) * (0.18 if hover else 0.08)
            a = 0.72 + glow + (0.10 if hover else 0)
            img.setXelA(x, y,
                        min(1, base[0]/255+glow), min(1, base[1]/255+glow),
                        min(1, base[2]/255+glow), min(0.95, a))
    path = os.path.join(_OUT_DIR, name + '.png')
    img.write(Filename.fromOsSpecific(path))
    tex = Texture(name); tex.load(img)
    return tex, path


# ---------- 缓存纹理 ----------
_TEX = {}
def _get(key, maker):
    if key not in _TEX:
        _TEX[key] = maker()
    return _TEX[key][0]


# ---------- 字体 ----------
def load_font(game):
    """加载思源黑体（规范指定），失败回退微软雅黑。"""
    import os.path as op
    for p in (FONT_PATH, 'C:/Windows/Fonts/msyh.ttc'):
        if op.exists(p):
            try:
                f = game.loader.loadFont(Filename.fromOsSpecific(p).getFullpath())
                f.setPixelsPerUnit(48)
                return f
            except Exception:
                pass
    return getattr(game, 'font', None)


# ---------- 面板卡片 ----------
def make_card(game, tex, width, height, pos=(0,0,0), parent=None, name='ui_panel'):
    """用带贴图的平面卡片做面板背景（替代默认 DirectFrame 纯色块）。"""
    cm = CardMaker(name)
    cm.setFrame(-width/2, width/2, -height/2, height/2)
    node = (parent or game.aspect2d).attachNewNode(cm.generate())
    node.setTexture(tex)
    node.setTransparency(TransparencyAttrib.MAlpha)
    node.setPos(*pos)
    return node


# ---------- 主换皮入口 ----------
def apply(game):
    """把现有 UI 统一换皮。保留所有 OnscreenText 对象，只改样式并垫背景卡片。"""
    font = load_font(game)
    if font:
        game.font = font

    # 1) 生成/取缓存面板贴图
    earth_tex = _get('earth', lambda: make_earth_panel('ui_earth_bar', 768, 96))
    jade_tex  = _get('jade',  lambda: make_jade_panel('ui_jade_overlay', 512, 384))

    # 2) 顶部资源条：保留 self.top（DirectFrame），改成夯土贴图卡片垫底
    if hasattr(game, 'top'):
        try:
            game.top['frameColor'] = (0,0,0,0)   # 隐藏原纯色块
        except Exception:
            pass
    # 顶部条背景卡片（aspect2d 坐标 -1.6..1.6 宽、0.78..1.0 高）
    if not hasattr(game, '_ui_top_card'):
        game._ui_top_card = make_card(game, earth_tex, 3.2, 0.24,
                                      pos=(0, 0, 0.89), parent=game.aspect2d,
                                      name='ui_top_earth')

    # 3) 统一文字颜色/字体/尺寸（对象保留，引用不断）
    def style(txt, color, scale=None, font_on=True):
        if txt is None: return
        try:
            if font_on and font: txt.setFont(font)
            txt.setFg(color[0], color[1], color[2], 1)
            if scale: txt.setScale(scale)
        except Exception:
            pass

    # 顶条（夯土陶板底）→ 深墨青正文，对比清晰
    style(getattr(game,'title',None),   JADE_DEEP, .050)
    style(getattr(game,'stats',None),   JADE_DEEP, .033)
    style(getattr(game,'goal',None),    JADE_DEEP, .032)
    style(getattr(game,'economy',None), JADE_DEEP, .026)
    # 浮在 3D 场景上的提示 → 浅色（淡青/米黄）保证暗背景可读
    style(getattr(game,'prompt',None),  JADE_PALE, .044)
    style(getattr(game,'message',None), SAND,      .030)
    style(getattr(game,'controls_text',None), SAND, .023)
    # 青玉浮层 → 深墨青
    style(getattr(game,'overlaytext',None),   JADE_DEEP, .060)
    style(getattr(game,'overlaydetail',None), JADE_DEEP, .034)

    # 4) 暂停/结算浮层：青玉面板垫底（叙事仪式感）
    if hasattr(game, 'overlay'):
        try:
            game.overlay['frameColor'] = (0,0,0,0)
        except Exception:
            pass
    if not hasattr(game, '_ui_overlay_card'):
        game._ui_overlay_card = make_card(game, jade_tex, 1.8, 1.16,
                                          pos=(0,0,0), parent=game.overlay,
                                          name='ui_overlay_jade')

    # 5) 按钮：小玉牌样式（frameColor 淡青、文字深墨青）
    for btn in [getattr(game,'resume_button',None)]:
        if btn is None: continue
        try:
            btn['frameColor'] = (JADE[0], JADE[1], JADE[2], .62)
            btn['text_fg'] = (JADE_DEEP[0], JADE_DEEP[1], JADE_DEEP[2], 1)
            btn['text_font'] = font or getattr(game,'font',None)
        except Exception:
            pass
    # 6) 沉浸模式：漫游时隐藏操作说明长条（底部），需要时由 F10 切换
    game._ui_immersive = getattr(game, '_ui_immersive', False)
    game.accept('f10', toggle_immersive)

    try:
        print('[ui_theme] applied: jade/earth panels, Noto Sans SC')
    except Exception:
        pass


def toggle_immersive():
    """F10：第三人称漫游沉浸模式——隐藏常驻 HUD，只保留交互提示。"""
    game = _CUR_GAME.get('g')
    if not game: return
    game._ui_immersive = not game._ui_immersive
    hide = game._ui_immersive
    for name in ('top','title','stats','goal','economy','controls_text','message'):
        obj = getattr(game, name, None)
        if obj is None: continue
        try:
            obj.hide() if hide else obj.show()
        except Exception:
            pass
    for name in ('_ui_top_card',):
        obj = getattr(game, name, None)
        if obj is not None:
            obj.hide() if hide else obj.show()


def apply_dialogue(game):
    """对话界面换皮：青玉面板 + 深墨青文字 + 玉牌选项按钮。保留所有对象引用。"""
    font = load_font(game) or getattr(game, 'font', None)
    # 1) 对话框背景：青玉面板（叙事仪式感最强）
    dlg = getattr(game, 'dlg_frame', None)
    if dlg is None:
        return
    try:
        dlg['frameColor'] = (0, 0, 0, 0)
    except Exception:
        pass
    jade_tex = _get('jade', lambda: make_jade_panel('ui_jade_overlay', 512, 384))
    if not hasattr(game, '_ui_dlg_card'):
        game._ui_dlg_card = make_card(game, jade_tex, 2.35, 1.28,
                                      pos=(0, 0, -.06), parent=game.aspect2d,
                                      name='ui_dlg_jade')
        game._ui_dlg_card.hide()

    # 2) 文字：深墨青为主、好感度用青玉色、反馈淡青
    def st(obj, color, scale=None):
        if obj is None: return
        try:
            if font: obj.setFont(font)
            obj.setFg(color[0], color[1], color[2], 1)
            if scale: obj.setScale(scale)
        except Exception:
            pass
    st(getattr(game,'dlg_speaker',None),  JADE_DEEP, .050)
    st(getattr(game,'dlg_affinity',None), JADE,      .032)
    st(getattr(game,'dlg_text',None),     JADE_DEEP, .036)
    st(getattr(game,'dlg_feedback',None), JADE_DEEP, .030)

    # 3) 选项按钮：小玉牌（淡青底、深墨青字、扁平无立体边框）
    for b in getattr(game, 'dlg_buttons', []):
        try:
            b['frameColor'] = (JADE[0], JADE[1], JADE[2], .88)
            b['text_fg'] = (JADE_DEEP[0], JADE_DEEP[1], JADE_DEEP[2], 1)
            b['relief'] = 1  # FLAT，去除默认立体框，像一枚玉片
            if font: b['text_font'] = font
        except Exception:
            pass
    # 对话框卡片随 dlg_frame 显隐：hook show/hide
    _sync_dlg_card(game)


def _sync_dlg_card(game):
    """让青玉背景卡片跟随对话框显隐（每帧轻量检查）。"""
    if getattr(game, '_ui_dlg_hooked', False):
        return
    game._ui_dlg_hooked = True
    # 用 task 每帧同步可见性
    def sync(task):
        card = getattr(game, '_ui_dlg_card', None)
        frame = getattr(game, 'dlg_frame', None)
        if card is None or frame is None:
            return task.cont
        try:
            if not frame.isHidden():
                card.show()
                # 对话期间持续保持玉牌样式（_dlg_show 设 text 后可能重置）
                for b in getattr(game, 'dlg_buttons', []):
                    try:
                        b['frameColor'] = (JADE[0], JADE[1], JADE[2], .88)
                        b['text_fg'] = (JADE_DEEP[0], JADE_DEEP[1], JADE_DEEP[2], 1)
                    except Exception:
                        pass
            else:
                card.hide()
        except Exception:
            pass
        return task.cont
    game.taskMgr.add(sync, 'ui_dlg_card_sync')


_CUR_GAME = {}
def register(game):
    _CUR_GAME['g'] = game
