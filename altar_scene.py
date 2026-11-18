# -*- coding: utf-8 -*-
"""祭坛玉琮替换 + 蓝色方圆交互光影特效 + 礼制高台空地丰富。

由 demo_v23ext 调用，函数都以 game(ShowBase实例) 为第一参数。
"""
import math, random, os
from panda3d.core import (
    Filename, Texture, PNMImage, CardMaker, LineSegs,
    TransparencyAttrib, ColorBlendAttrib,
)

ASSETS_NEW = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets_new')


# =====================================================================
# 一、玉琮替换祭坛方块
# =====================================================================
def place_jade_cong(game):
    """隐藏供台上原有的棕色 drum 圆柱几何 + jade offering 锥体，
    在 (-1.9, 83.5) 放真实的玉琮模型，作为祭祀交互主体。"""
    game.altar_cong_x, game.altar_cong_y = -1.9, 83.5
    base_z = 6.32 + 0.75          # drum 顶面高度

    # 隐藏原几何：找祭坛中心附近的小型锥/圆柱几何（jade offering, drum）
    for n in list(game.render.findAllMatches('**/+GeomNode')):
        par = n.getParent()
        p = par.getPos(game.render)
        # g.effects 下的 jade offering / 供台小几何
        if abs(p.x + 1.9) < 3 and abs(p.y - 83.5) < 3:
            nm = (n.getName() + ' ' + par.getName()).lower()
            if 'jade offering' in nm or 'altarjade' in nm or 'offering' in nm:
                n.hide()
    if hasattr(game, 'altarjade'):
        try: game.altarjade.hide()
        except Exception: pass
    # 隐藏 drum 圆柱本体（sky_temple 生成的 g.offer 是分组，找里面的圆柱 GeomNode）
    for n in list(game.render.findAllMatches('**/+GeomNode')):
        par = n.getParent()
        p = par.getPos(game.render)
        if abs(p.x + 1.9) < 2.5 and abs(p.y - 83.5) < 2.5:
            try:
                lo, hi = n.getTightBounds(game.render)
            except Exception:
                continue
            w, d, h = hi.x - lo.x, hi.y - lo.y, hi.z - lo.z
            # 供台圆柱：直径约1.46、高0.75
            if 1.0 < w < 2.2 and 1.0 < d < 2.2 and .4 < h < 1.3:
                n.hide()

    # 加载玉琮模型
    path = Filename.fromOsSpecific(os.path.join(ASSETS_NEW, 'jade_cong.bam'))
    model = game.loader.loadModel(path)
    node = game.effects.attachNewNode('jade_cong_altar')
    node.setPos(game.altar_cong_x, game.altar_cong_y, base_z)
    node.setScale(1.35)           # 玉琮放大，作为祭坛主体
    model.reparentTo(node)
    game.altar_cong = node
    return node


# =====================================================================
# 二、蓝色方圆交互光影特效
# =====================================================================
def build_altar_fx(game):
    """蓝色光体 + 方形环 + 圆形光带，以『方/圆』为几何元素构成交互特效。"""
    cx, cy = game.altar_cong_x, game.altar_cong_y
    cz = 6.32 + 0.75

    # 蓝色发光贴图（冷青蓝）
    img = PNMImage(64, 64, 4)
    for yy in range(64):
        for xx in range(64):
            r = ((xx - 31.5) / 32) ** 2 + ((yy - 31.5) / 32) ** 2
            img.setXelA(xx, yy, .30, .70, 1.0, max(0, 1 - r) ** 3)
    tex = Texture('blue glow'); tex.load(img)

    # 中心蓝色光体（billboard 加色混合）
    card = CardMaker('blue core'); card.setFrame(-1, 1, -1, 1)
    core = game.effects.attachNewNode(card.generate())
    core.setTexture(tex); core.setBillboardPointEye(); core.setLightOff(); core.setShaderOff()
    core.setDepthWrite(False); core.setTransparency(TransparencyAttrib.MAlpha)
    core.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                   ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne))
    core.setPos(cx, cy, cz + 1.1); core.setScale(1.3); core.hide()

    # 蓝色光柱（4 个细长 billboard）
    pillars = []
    for i in range(4):
        a = i * math.tau / 4
        s = game.effects.attachNewNode(card.generate())
        s.setTexture(tex); s.setBillboardPointEye(); s.setLightOff(); s.setShaderOff()
        s.setDepthWrite(False); s.setTransparency(TransparencyAttrib.MAlpha)
        s.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                    ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne))
        s.setScale(.28, 1, 1.5)
        s.hide(); pillars.append((s, a))

    # 方形环：用 LineSegs 画正方形，多层不同高度
    square_rings = []
    for k, (r, z) in enumerate([(1.7, cz + .3), (2.3, cz + .9), (1.4, cz + 1.6)]):
        segs = LineSegs('square ring'); segs.setThickness(2.5)
        segs.setColor(.30, .72, 1.0, 1)
        corners = [(-r, -r), (r, -r), (r, r), (-r, r), (-r, -r)]
        for j, (sx, sy) in enumerate(corners):
            segs.moveTo(cx + sx, cy + sy, z); segs.drawTo(cx + sx, cy + sy, z) if j == 0 else None
        # 重画为连续线段
        segs2 = LineSegs('sq'); segs2.setThickness(2.5); segs2.setColor(.30, .72, 1.0, 1)
        for j, (sx, sy) in enumerate(corners):
            if j == 0: segs2.moveTo(cx + sx, cy + sy, z)
            else: segs2.drawTo(cx + sx, cy + sy, z)
        n = game.effects.attachNewNode(segs2.create()); n.setLightOff(); n.hide()
        square_rings.append((n, k))

    # 圆形光带：LineSegs 画圆，多层
    circle_rings = []
    for k, (r, z) in enumerate([(2.0, cz + .15), (2.7, cz + 1.2)]):
        segs = LineSegs('circle ring'); segs.setThickness(2.5)
        segs.setColor(.35, .80, 1.0, 1)
        for i in range(49):
            a = i * math.tau / 48
            if i == 0: segs.moveTo(cx + r * math.cos(a), cy + r * math.sin(a), z)
            else: segs.drawTo(cx + r * math.cos(a), cy + r * math.sin(a), z)
        n = game.effects.attachNewNode(segs.create()); n.setLightOff(); n.hide()
        circle_rings.append((n, k))

    # 漂浮蓝色光点
    motes = []
    rng = random.Random(77)
    for i in range(16):
        s = game.effects.attachNewNode(card.generate())
        s.setTexture(tex); s.setBillboardPointEye(); s.setLightOff(); s.setShaderOff()
        s.setDepthWrite(False); s.setTransparency(TransparencyAttrib.MAlpha)
        s.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                    ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne))
        s.setScale(.16); s.hide()
        motes.append((s, rng.random() * math.tau, rng.uniform(.6, 1.6)))

    game.altar_fx = dict(core=core, pillars=pillars, squares=square_rings,
                         circles=circle_rings, motes=motes, cz=cz,
                         cx=cx, cy=cy, active_until=0.0)


def trigger_altar_fx(game, duration=8):
    if hasattr(game, 'altar_fx'):
        game.altar_fx['active_until'] = game.t + duration


def update_altar_fx(game):
    fx = getattr(game, 'altar_fx', None)
    if not fx: return
    active = game.t < fx['active_until']
    cx, cy, cz = fx['cx'], fx['cy'], fx['cz']
    core = fx['core']
    if active:
        core.show(); core.setScale(1.3 + .25 * math.sin(game.t * 3))
        for s, a in fx['pillars']:
            s.show()
            rr = 1.1
            s.setPos(cx + rr * math.cos(a), cy + rr * math.sin(a), cz + 1.0)
            s.setScale(.28, 1, 1.5 + .3 * math.sin(game.t * 4 + a))
        for n, k in fx['squares']:
            n.show(); n.setH(game.t * (30 + k * 20) * (1 if k % 2 else -1))
        for n, k in fx['circles']:
            n.show(); n.setH(game.t * (20 + k * 15) * (1 if k % 2 else -1))
        for s, ph, sp in fx['motes']:
            s.show()
            a = ph + game.t * .6
            life = (game.t * sp) % 3.0
            s.setPos(cx + 2.4 * math.cos(a), cy + 2.4 * math.sin(a), cz + .3 + life)
            s.setScale(.16 * (1 - life / 3.5))
    else:
        core.hide()
        for s, a in fx['pillars']: s.hide()
        for n, k in fx['squares']: n.hide()
        for n, k in fx['circles']: n.hide()
        for s, ph, sp in fx['motes']: s.hide()


# =====================================================================
# 三、礼制高台空地丰富（动物/人物/草地/建筑/石块）
# =====================================================================
def enrich_highland(game):
    """图2空地：在 (x=-14..14, y=58..78) 的台地加入草地、石块、建筑、人物、动物。
    全部复用 assets/frontier 与 assets/tripo 已有 .bam 模型。"""
    rng = random.Random(8801)
    added = []

    def place(kind, x, y, scale, heading=0):
        z = game.height(x, y)
        try:
            n = game.builder.asset(kind, x, y, z, scale, heading)
            lo, hi = n.getTightBounds(game.render)
            n.setZ(n.getZ() + z - lo.z - .05)
            added.append(n)
            return n
        except Exception:
            return None

    # 用户要求：T台不长草、两边不要小房子/纪念柱、不要人物动物。
    # 只保留少量岩石点缀，其余全部取消。
    rock_spots = [(-12, 62), (-9, 72), (11, 60), (12, 74), (-13, 68),
                  (7, 57), (4, 77), (-4, 58), (9, 68)]
    for i, (x, y) in enumerate(rock_spots):
        place('rock1' if i % 2 else 'rock2', x, y,
              (rng.uniform(1.2, 2.2),) * 3, rng.uniform(0, 360))

    game.highland_added = added
    return added


# =====================================================================
# 四、恢复茅草市场摊位（之前误删，用 tripo 模型重新摆回 pottery_trade 处）
# =====================================================================
def restore_market_stall(game):
    """在 pottery_trade(9,36.5) 茅草市场交互点附近摆回茅草市场摊位模型。
    之前把 stall 全删时误伤了它，现在用 11.10 的 tripo 模型恢复。"""
    path = Filename.fromOsSpecific(os.path.join(ASSETS_NEW, 'market_stall.bam'))
    try:
        model = game.loader.loadModel(path)
    except Exception as e:
        print('[market] load fail', e)
        return []
    placed = []
    # 模型本地为底部贴地、约 3.88 宽 × 3.74 深 × 3.2 高；围绕交互点摆 2 个摊位
    # 注意：(5.5,34.5) 那个压在旗帜(6,35)正下方，用户觉得突兀，已去掉。
    spots = [
        (12.5, 34.0, 200, 1.70),   # 主摊位，交互点东南侧（放大）
        (9.0, 40.5, 20, 1.40),     # 北侧（放大并稍拉开避免重叠）
    ]
    for i, (x, y, h, s) in enumerate(spots):
        node = game.effects.attachNewNode('market_stall_%d' % i)
        z = game.height(x, y)
        node.setPos(x, y, z - .05)
        node.setH(h)
        node.setScale(s)
        model.instanceTo(node)
        placed.append(node)
    game.market_stalls = placed
    return placed


# =====================================================================
# 五、东侧空地：玉石旋环 + 石碑立柱 + 石头
# =====================================================================
def place_plaza_models(game):
    """在东侧空地(x=9~16,y=50~62)摆放两个新模型(玉石旋环/石碑立柱)和若干石头。
    位置避开已有 jadepost(8,55)/lodge(14,49)(16,54)/flag(8,51)/rune(8,61)。"""
    placed = []
    def inst(mdl, name, x, y, scale=1.0, heading=0.0, sink=.05):
        node = game.effects.attachNewNode(name)
        z = game.height(x, y)
        node.setPos(x, y, z - sink)
        node.setH(heading)
        node.setScale(scale)
        mdl.instanceTo(node)
        placed.append(node)
        return node

    ring = game.loader.loadModel(Filename.fromOsSpecific(os.path.join(ASSETS_NEW, 'jade_ring2.bam')))
    stele = game.loader.loadModel(Filename.fromOsSpecific(os.path.join(ASSETS_NEW, 'stele_pillar.bam')))

    # 石碑立柱：立在空地显眼处（模型高 3.6m）
    inst(stele, 'plaza_stele_0', 11.5, 52.0, 1.15, 25)
    inst(stele, 'plaza_stele_1', 15.0, 60.5, 1.0, -40)
    # 玉石旋环：竖立的圆环（模型高 2.2m）
    inst(ring, 'plaza_ring_0', 10.5, 58.0, 1.1, 15)
    inst(ring, 'plaza_ring_1', 14.0, 55.5, 0.95, -25)

    # 石头：用现有 rock1/rock2 散布周围
    rock_specs = [(9.5, 54, 'rock2', 1.0), (13, 51.5, 'rock1', 1.3),
                  (16, 58, 'rock2', 1.1), (11, 61.5, 'rock1', 0.9),
                  (15.5, 52.5, 'rock2', 0.8), (9.8, 60, 'rock1', 1.0),
                  (17, 55, 'rock2', 1.2)]
    for i, (x, y, kind, s) in enumerate(rock_specs):
        try:
            r = game.builder.asset(kind, x, y, game.height(x, y), (s,) * 3, i * 47)
            lo, hi = r.getTightBounds(game.render)
            r.setZ(r.getZ() + game.height(x, y) - lo.z - .05)
            placed.append(r)
        except Exception:
            pass

    game.plaza_new = placed
    return placed
