# -*- coding: utf-8 -*-
"""把石质外墙的 basecolor 贴图做成浅色版：提亮 + 去饱和 + 拉向浅米灰。
输出 PNG，运行时替换到墙模型上。
"""
import os
from panda3d.core import PNMImage, Filename

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '_model_work', 'stone_wall', '石质外墙3d模型.fbm', '石质外墙3d模型_basecolor.jpg')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'frontier', 'wall_light.png')
# 用 assets_new 目录更稳妥（可写，独立）
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets_new', 'wall_light.png')

img = PNMImage()
if not img.read(Filename.fromOsSpecific(SRC)):
    raise SystemExit("无法读取: " + SRC)
w, h = img.getXSize(), img.getYSize()
print("SRC", w, h)

LIFT = 0.80      # 整体提亮幅度（向浅色混合）——极淡
DESAT = 0.85     # 去饱和强度（0=保留,1=完全灰度）
TARGET = (0.94, 0.92, 0.86)   # 目标：非常淡的浅米白

for y in range(h):
    for x in range(w):
        r, g, b = img.getXel(x, y)
        lum = 0.299*r + 0.587*g + 0.114*b
        # 去饱和
        nr = r + (lum - r) * DESAT
        ng = g + (lum - g) * DESAT
        nb = b + (lum - b) * DESAT
        # 提亮：向目标浅色混合
        nr = nr + (TARGET[0] - nr) * LIFT
        ng = ng + (TARGET[1] - ng) * LIFT
        nb = nb + (TARGET[2] - nb) * LIFT
        img.setXel(x, y, min(1, max(0, nr)), min(1, max(0, ng)), min(1, max(0, nb)))

img.write(Filename.fromOsSpecific(OUT))
print("OUT", OUT, os.path.getsize(OUT), "bytes")
