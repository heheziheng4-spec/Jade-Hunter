# -*- coding: utf-8 -*-
"""逐玉记 · 参考图 HUD 贴图生成器（hud_ref_tex.py）
按用户两张参考图程序化绘制精确 UI 组件：
  · 回纹装饰（标题两侧方折雷纹）
  · 竖线分隔符
  · 暖褐圆角卡片（带浅金描边）—— 顶部信息卡 / 中央交互卡
  · 深褐胶囊长条 + 键帽 —— 底部快捷键
  · 各类线性玉石 icon（斗笠/立方/玉璧六边形/人/水）—— 顶部资源栏
配色采样自参考图：深褐 #2D251B、暖褐 #A98E55、亮金 #F1CE92、浅金 #D2AA68。
"""
import math, os
from panda3d.core import PNMImage, Texture, Filename

_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets_new', 'ui')
os.makedirs(_OUT, exist_ok=True)

DARK  = (0.176, 0.145, 0.106)   # #2D251B
WARM  = (0.663, 0.557, 0.333)   # #A98E55
GOLD  = (0.945, 0.808, 0.573)   # #F1CE92
LGOLD = (0.824, 0.667, 0.408)   # #D2AA68
LINE  = (0.75, 0.62, 0.36)      # 描边浅金


def _save(img, name):
    p = os.path.join(_OUT, name + '.png')
    img.write(Filename.fromOsSpecific(p))
    t = Texture(name); t.load(img)
    return t


def _rounded_rect(img, x0, y0, x1, y1, r, fill, edge=None, ew=2):
    """圆角矩形：逐像素绘制，fill=(r,g,b,a)，edge 描边色。"""
    w, h = img.getXSize(), img.getYSize()
    def inside(px, py):
        cx = min(max(px, x0+r), x1-r); cy = min(max(py, y0+r), y1-r)
        return (px-cx)**2 + (py-cy)**2 <= r*r and x0 <= px <= x1 and y0 <= py <= y1
    for y in range(int(y0)-1, int(y1)+2):
        for x in range(int(x0)-1, int(x1)+2):
            # 判断是否在圆角内（SDF）
            cx = min(max(x, x0+r), x1-r); cy = min(max(y, y0+r), y1-r)
            d2 = (x-cx)**2 + (y-cy)**2
            inr = (x0 <= x <= x1 and y0 <= y <= y1 and d2 <= r*r)
            if not inr: continue
            is_edge = edge is not None and d2 > (r-ew)**2
            c = edge if is_edge else fill
            if 0 <= x < w and 0 <= y < h:
                img.setXelA(x, y, c[0], c[1], c[2], c[3])


def card_tex(name='ref_card', W=720, H=150, r=16):
    """暖褐圆角卡片 + 浅金细描边（顶部信息卡 / 中央交互卡通用）。"""
    img = PNMImage(W, H, 4)
    fill = (WARM[0], WARM[1], WARM[2], .70)
    edge = (LINE[0], LINE[1], LINE[2], .95)
    _rounded_rect(img, 3, 3, W-4, H-4, r, fill, edge, 2)
    return _save(img, name)


def capsule_tex(name='ref_capsule', W=1440, H=64, r=14):
    """深褐圆角长条（底部快捷键底）。"""
    img = PNMImage(W, H, 4)
    fill = (0.20, 0.17, 0.12, .82)
    edge = (LINE[0], LINE[1], LINE[2], .65)
    _rounded_rect(img, 2, 2, W-3, H-3, r, fill, edge, 2)
    return _save(img, name)


def keycap_tex(name='ref_keycap', W=150, H=52, r=8):
    """键帽：暖褐填充 + 浅金描边圆角矩形。"""
    img = PNMImage(W, H, 4)
    fill = (0.42, 0.34, 0.20, .55)
    edge = (GOLD[0], GOLD[1], GOLD[2], .95)
    _rounded_rect(img, 3, 3, W-4, H-4, r, fill, edge, 2)
    return _save(img, name)


def bar_tex(name='ref_topbar', W=2048, H=128):
    """顶部深褐条（带微妙横向纹理）。"""
    img = PNMImage(W, H, 4)
    for y in range(H):
        for x in range(W):
            v = 0.02 * math.sin(y * .5)
            a = .92 - (y/H)*.12
            img.setXelA(x, y, DARK[0]+v, DARK[1]+v, DARK[2]+v, a)
    return _save(img, name)


def huiwen_tex(name='ref_huiwen', W=180, H=56, mirror=False):
    """回纹装饰：方折雷纹（类似 ㄋ┐ + 圆点）。"""
    img = PNMImage(W, H, 4)
    lw = 3
    def line(x0,y0,x1,y1):
        steps = int(max(abs(x1-x0), abs(y1-y0)))+1
        for i in range(steps+1):
            x = int(x0+(x1-x0)*i/steps); y = int(y0+(y1-y0)*i/steps)
            for dy in range(-lw//2, lw//2+1):
                for dx in range(-lw//2, lw//2+1):
                    if 0 <= x+dx < W and 0 <= y+dy < H:
                        img.setXelA(x+dx, y+dy, GOLD[0], GOLD[1], GOLD[2], .95)
    if mirror:
        # 右侧回纹：┐┌ 折线 + 圆点
        line(20,28,40,28); line(40,28,40,14); line(40,14,120,14); line(120,14,120,42); line(120,42,160,42)
    else:
        # 左侧回纹
        line(160,28,140,28); line(140,28,140,14); line(140,14,60,14); line(60,14,60,42); line(60,42,20,42)
    return _save(img, name)


def icon_tex(kind, name=None, S=64):
    """线性玉石 icon：用线条画（sun/person/grain/material/jade）。"""
    img = PNMImage(S, S, 4)
    cx = cy = S/2
    def px(x,y,c=GOLD,a=1):
        if 0<=x<S and 0<=y<S: img.setXelA(int(x),int(y),c[0],c[1],c[2],a)
    def circle(r, lw=3):
        for a_i in range(0, 360):
            a0 = math.radians(a_i)
            for rr in range(r-lw, r+1):
                px(cx+rr*math.cos(a0), cy+rr*math.sin(a0))
    def line(x0,y0,x1,y1,lw=3):
        steps=int(max(abs(x1-x0),abs(y1-y0)))+1
        for i in range(steps+1):
            x=x0+(x1-x0)*i/steps; y=y0+(y1-y0)*i/steps
            for dy in range(-lw//2,lw//2+1):
                for dx in range(-lw//2,lw//2+1): px(x+dx,y+dy)
    if kind == 'day':  # 太阳 ☼
        circle(12,3)
        for ang in range(0,360,45):
            a0=math.radians(ang)
            line(cx+16*math.cos(a0),cy+16*math.sin(a0),cx+24*math.cos(a0),cy+24*math.sin(a0),3)
    elif kind == 'people':  # 人 ♧
        circle(8,3); line(cx,cy+10,cx,cy+24,3); line(cx-12,cy+16,cx+12,cy+16,3); line(cx,cy+24,cx-9,cy+32,2); line(cx,cy+24,cx+9,cy+32,2)
    elif kind == 'grain':  # 粮穗
        line(cx,cy+24,cx,cy-24,3)
        for i in range(4):
            yy=cy-18+i*12
            line(cx,yy,cx-10,yy-6,2); line(cx,yy,cx+10,yy-6,2)
    elif kind == 'material':  # 立方体
        line(cx-18,cy+8,cx,cy+18,3); line(cx,cy+18,cx+18,cy+8,3); line(cx+18,cy+8,cx+18,cy-10,3)
        line(cx+18,cy-10,cx,cy-20,3); line(cx,cy-20,cx-18,cy-10,3); line(cx-18,cy-10,cx-18,cy+8,3)
        line(cx-18,cy-10,cx,cy,2); line(cx,cy,cx+18,cy-10,2); line(cx,cy,cx,cy+18,2)
    elif kind == 'jade':  # 玉璧六边形
        pts=[(cx+20*math.cos(math.radians(a)), cy+20*math.sin(math.radians(a))) for a in range(0,360,60)]
        for i in range(len(pts)):
            x0,y0=pts[i]; x1,y1=pts[(i+1)%len(pts)]
            line(x0,y0,x1,y1,3)
        circle(7,2)
    elif kind == 'info':  # ⓘ
        circle(20,3); px(cx,cy+10,GOLD); line(cx,cy-12,cx,cy+4,3)
    return _save(img, 'ref_icon_'+kind)


def make_all():
    return dict(
        bar=bar_tex(), card=card_tex(), capsule=capsule_tex(), keycap=keycap_tex(),
        huiwen_l=huiwen_tex('ref_huiwen_l', mirror=False),
        huiwen_r=huiwen_tex('ref_huiwen_r', mirror=True),
        day=icon_tex('day'), people=icon_tex('people'), grain=icon_tex('grain'),
        material=icon_tex('material'), jade=icon_tex('jade'), info=icon_tex('info'))


if __name__ == '__main__':
    for k, v in make_all().items():
        print('TEX', k, v.getXSize())
