# -*- coding: utf-8 -*-
"""逐玉记 · 程序化玉器图标贴图
用 PNMImage 画几何玉器剪影，供 UI 卡片使用：
  玉琮(方柱横纹) / 玉璧(圆环中孔) / 玉璜(弧片) / 玉玦(缺口环) / 玉钺(斧) / 卷涡纹印章 / 玉璧铆钉
统一低饱和青玉色 + 内柔光 + 浅刻纹，风格对齐设计稿。
"""
import math, os
from panda3d.core import PNMImage, Texture, Filename

_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets_new', 'ui')
os.makedirs(_OUT, exist_ok=True)

JADE = (0.66, 0.80, 0.74)      # 青玉
JADE_HI = (0.82, 0.91, 0.86)   # 玉高光
JADE_DK = (0.45, 0.62, 0.56)   # 玉暗部
INK = (0.30, 0.42, 0.39)       # 刻线深青


def _tex(name):
    t = Texture(name); return t


def _save(img, name):
    path = os.path.join(_OUT, name + '.png')
    img.write(Filename.fromOsSpecific(path))
    t = _tex(name); t.load(img)
    return t, path


def _circle(img, cx, cy, r, col, alpha=1.0, ring=False, width=3):
    w, h = img.getXSize(), img.getYSize()
    for y in range(int(cy-r-2), int(cy+r+3)):
        for x in range(int(cx-r-2), int(cx+r+3)):
            if 0 <= x < w and 0 <= y < h:
                d = math.hypot(x-cx, y-cy)
                if ring:
                    if abs(d-r) <= width/2:
                        img.setXelA(x, y, col[0], col[1], col[2], alpha)
                elif d <= r:
                    img.setXelA(x, y, col[0], col[1], col[2], alpha)


def jade_bi(name='icon_bi', S=128):
    """玉璧：同心圆环 + 中孔，边缘柔光。"""
    img = PNMImage(S, S, 4)
    cx = cy = S/2
    R = S*0.40
    _circle(img, cx, cy, R, JADE)                       # 外盘
    _circle(img, cx, cy, R*0.92, JADE_HI, .5)          # 内高光圈
    _circle(img, cx, cy, R*0.78, JADE_DK, .35)         # 内暗圈(玉质分层)
    _circle(img, cx, cy, R*0.30, (0,0,0), 0)           # 中孔：挖空
    for y in range(S):
        for x in range(S):
            d = math.hypot(x-cx, y-cy)
            if d < R*0.30:
                img.setXelA(x, y, 0, 0, 0, 0)
            elif abs(d-R*0.78) < 2 or abs(d-R*0.92) < 1.5:
                img.setXelA(x, y, INK[0], INK[1], INK[2], .55)
    return _save(img, name)


def jade_cong(name='icon_cong', S=128):
    """玉琮：外方内圆的方柱，带横向分层纹。"""
    img = PNMImage(S, S, 4)
    cx = cy = S/2
    half = S*0.32
    # 方柱体（带轻微圆角）
    for y in range(S):
        for x in range(S):
            dx, dy = abs(x-cx), abs(y-cy)
            if dx <= half and dy <= half*1.05:
                edge = (dx > half-4 or dy > half*1.05-4)
                col = JADE_DK if edge else JADE
                img.setXelA(x, y, col[0], col[1], col[2], 1)
    # 中孔（圆）
    _circle(img, cx, cy, half*0.42, (0,0,0), 0)
    for y in range(S):
        for x in range(S):
            if math.hypot(x-cx, y-cy) < half*0.42:
                img.setXelA(x, y, 0, 0, 0, 0)
    # 横向分层刻线（玉琮典型节纹）
    for f in (0.28, 0.52, 0.76):
        yy = int(cy - half + half*2*f)
        for x in range(int(cx-half)+3, int(cx+half)-2):
            for dy in (-1, 0, 1):
                img.setXelA(x, yy+dy, INK[0], INK[1], INK[2], .6)
    # 四角竖向浅刻线
    for sx in (-1, 1):
        for sy in (-1, 1):
            xx = int(cx + sx*(half-6))
            for y in range(int(cy-half)+5, int(cy+half)-4):
                img.setXelA(xx, y, INK[0], INK[1], INK[2], .35)
    return _save(img, name)


def jade_huang(name='icon_huang', S=128):
    """玉璜：弧形片（圆环下弧段）。"""
    img = PNMImage(S, S, 4)
    cx, cy = S/2, S*0.62
    R = S*0.38
    for y in range(S):
        for x in range(S):
            d = math.hypot(x-cx, y-cy)
            ang = math.atan2(y-cy, x-cx)   # 下弧: ang in (0, pi)
            if R*0.62 <= d <= R and 0.05 < ang < math.pi-0.05:
                img.setXelA(x, y, JADE[0], JADE[1], JADE[2], 1)
                if d > R*0.9 or d < R*0.7:
                    img.setXelA(x, y, INK[0], INK[1], INK[2], .4)
    return _save(img, name)


def jade_jue(name='icon_jue', S=128):
    """玉玦：带缺口的圆环。"""
    img = PNMImage(S, S, 4)
    cx = cy = S/2
    R = S*0.36
    for y in range(S):
        for x in range(S):
            d = math.hypot(x-cx, y-cy)
            ang = math.degrees(math.atan2(y-cy, x-cx))
            if R*0.55 <= d <= R:
                if -20 < ang < 20:   # 缺口
                    continue
                col = JADE_HI if d > R*0.88 else JADE
                img.setXelA(x, y, col[0], col[1], col[2], 1)
    return _save(img, name)


def jade_yue(name='icon_yue', S=128):
    """玉钺：斧形（梯形刃 + 中孔 + 柄）。"""
    img = PNMImage(S, S, 4)
    cx, cy = S/2, S*0.55
    for y in range(int(S*0.20), int(S*0.80)):
        for x in range(S):
            # 梯形：上窄下宽
            t = (y - S*0.20) / (S*0.60)
            half = S*(0.14 + 0.22*t)
            if abs(x-cx) <= half:
                img.setXelA(x, y, JADE[0], JADE[1], JADE[2], 1)
    _circle(img, cx, cy, S*0.07, (0,0,0), 0)
    for y in range(S):
        for x in range(S):
            if math.hypot(x-cx, y-cy) < S*0.07:
                img.setXelA(x, y, 0, 0, 0, 0)
    return _save(img, name)


def vortex_seal(name='icon_vortex', S=128):
    """卷涡纹印章：同心螺旋纹（良渚神徽简化）。"""
    img = PNMImage(S, S, 4)
    cx = cy = S/2
    _circle(img, cx, cy, S*0.44, JADE_DK, .85)
    _circle(img, cx, cy, S*0.40, JADE, 1)
    # 单线螺旋
    steps = 240
    prev = None
    for i in range(steps):
        t = i / (steps-1)
        ang = t * math.tau * 2.5
        rr = (S*0.36) * (1 - t*0.85)
        px, py = cx + math.cos(ang)*rr, cy + math.sin(ang)*rr
        if prev:
            for k in range(5):
                ix = int(prev[0] + (px-prev[0])*k/5)
                iy = int(prev[1] + (py-prev[1])*k/5)
                if 0 <= ix < S and 0 <= iy < S:
                    img.setXelA(ix, iy, INK[0], INK[1], INK[2], .9)
        prev = (px, py)
    return _save(img, name)


def bi_rivet(name='icon_rivet', S=64):
    """玉璧铆钉：小同心环，面板四角装饰。"""
    img = PNMImage(S, S, 4)
    cx = cy = S/2
    _circle(img, cx, cy, S*0.40, JADE_DK, 1)
    _circle(img, cx, cy, S*0.30, JADE_HI, 1)
    _circle(img, cx, cy, S*0.12, INK, 1)
    return _save(img, name)


def make_all():
    """生成全部图标，返回 {名称: Texture}。"""
    return dict(
        bi=jade_bi()[0], cong=jade_cong()[0], huang=jade_huang()[0],
        jue=jade_jue()[0], yue=jade_yue()[0],
        vortex=vortex_seal()[0], rivet=bi_rivet()[0])


if __name__ == '__main__':
    for k, v in make_all().items():
        print('ICON', k, v.getXSize(), v.getYSize())
