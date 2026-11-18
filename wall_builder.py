# -*- coding: utf-8 -*-
"""方正直立石墙生成器：带 UV 的长方体几何 + 程序生成的整齐砖墙贴图。

不依赖外部模型——模型贴图是乱石堆，视觉上仍是斜石块；这里用规整砖纹理 +
标准立方体，得到真正横平竖直、方方正正、颜色浅的石墙。
"""
import math, random
from panda3d.core import (
    Geom, GeomNode, GeomVertexData, GeomVertexFormat,
    GeomVertexWriter, GeomTriangles, Texture, PNMImage, NodePath,
)


def make_brick_texture(name='clean brick', w=256, h=256, seed=7):
    """生成整齐错缝砖墙贴图：浅米灰石砖 + 深色勾缝。"""
    rng = random.Random(seed)
    img = PNMImage(w, h, 3)
    # 底色 = 勾缝色（深灰褐）
    grout = (0.42, 0.38, 0.32)
    img.fill(grout[0], grout[1], grout[2])
    rows = 6
    row_h = h / rows
    brick_w = w / 3.0
    for r in range(rows):
        offset = (brick_w / 2) if r % 2 else 0.0
        y0 = r * row_h; y1 = y0 + row_h
        x = -offset
        while x < w:
            bx0, bx1 = x + 2, x + brick_w - 2      # 勾缝宽度
            by0, by1 = y0 + 2, y1 - 2
            # 浅米色砖，带轻微随机明度与偏绿做旧
            base = rng.uniform(0.74, 0.86)
            tint_g = rng.uniform(0.98, 1.04)
            col = (min(1, base), min(1, base * 0.94 * tint_g), min(1, base * 0.80))
            for yy in range(int(max(0, by0)), int(min(h, by1))):
                for xx in range(int(max(0, bx0)), int(min(w, bx1))):
                    # 砖面内轻微颗粒噪声
                    n = rng.uniform(-0.03, 0.03)
                    img.setXel(xx, yy,
                               max(0, min(1, col[0] + n)),
                               max(0, min(1, col[1] + n)),
                               max(0, min(1, col[2] + n)))
            # 顶部高光边 / 底部阴影边（增强砖块立体感）
            for xx in range(int(max(0, bx0)), int(min(w, bx1))):
                yy = int(by0); img.setXel(xx, yy, *[min(1, c + .06) for c in col])
                yy = int(by1) - 1; img.setXel(xx, yy, *[max(0, c - .05) for c in col])
            x += brick_w
    tex = Texture(name); tex.load(img)
    tex.setWrapU(Texture.WM_repeat); tex.setWrapV(Texture.WM_repeat)
    tex.setMinfilter(Texture.FTLinearMipmapLinear)
    tex.setMagfilter(Texture.FTLinear)
    return tex


def box_with_uv(name='wall box'):
    """单位立方体（-0.5..0.5），带 UV，六面铺满 0..1。"""
    fmt = GeomVertexFormat.getV3n3t2()
    data = GeomVertexData(name, fmt, Geom.UHStatic)
    v = GeomVertexWriter(data, 'vertex')
    n = GeomVertexWriter(data, 'normal')
    uv = GeomVertexWriter(data, 'texcoord')
    tris = GeomTriangles(Geom.UHStatic)
    # 六个面：每面 4 顶点 + UV(0,0)(1,0)(1,1)(0,1)
    faces = [
        ((0,0,1), [(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)]),
        ((0,0,-1),[(.5,-.5,-.5),(-.5,-.5,-.5),(-.5,.5,-.5),(.5,.5,-.5)]),
        ((1,0,0), [(.5,-.5,.5),(.5,-.5,-.5),(.5,.5,-.5),(.5,.5,.5)]),
        ((-1,0,0),[(-.5,-.5,-.5),(-.5,-.5,.5),(-.5,.5,.5),(-.5,.5,-.5)]),
        ((0,1,0), [(-.5,.5,.5),(.5,.5,.5),(.5,.5,-.5),(-.5,.5,-.5)]),
        ((0,-1,0),[(-.5,-.5,-.5),(.5,-.5,-.5),(.5,-.5,.5),(-.5,-.5,.5)]),
    ]
    uvcoords = [(0,0),(1,0),(1,1),(0,1)]
    idx = 0
    for normal, quad in faces:
        for p, tc in zip(quad, uvcoords):
            v.addData3(*p); n.addData3(*normal); uv.addData2(*tc)
        tris.addVertices(idx, idx+1, idx+2)
        tris.addVertices(idx, idx+2, idx+3)
        idx += 4
    geom = Geom(data); geom.addPrimitive(tris)
    gn = GeomNode(name); gn.addGeom(geom)
    return NodePath(gn)
