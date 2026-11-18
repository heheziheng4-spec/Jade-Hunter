# -*- coding: utf-8 -*-
"""沙光良渚 v0.23 扩展版 —— 对话系统 / 石环落地 / 新模型 / 玉石特效

基于 v0.23(PeopleDemo) 叠加，不改动原 demo_v23.py：
1. 圆形石环调转 180° 并按包围盒落地，绿色圆盘贴地、清理石环自带绿色薄片
2. 墙体逐段复核：pitch/roll 归零、垂直直立贴地
3. 接入 5 个新模型：图腾小怪物群 / 神鹿 / 发光玉石 / 玉琮 / 玉石旋环
4. 玉石交互特效：青绿旋转光弧 + 发光核心 + 漂浮碎屑
5. 数据驱动的多轮对话系统 + 好感度反馈
"""
import math, random, os
from panda3d.core import (
    loadPrcFileData, Filename, Texture, Vec3,
    TransparencyAttrib, ColorBlendAttrib, CardMaker, PNMImage,
)
from panda3d.core import Shader
from direct.gui.OnscreenText import OnscreenText
from demo_v23 import PeopleDemo
from dialogue_ui import DialogueUIMixin
from menu_image import ImageMenuMixin
from render_polish import RenderPolishMixin
from jade_ui import JadeUIMixin
from hud_polish import HudPolishMixin
from battle_system import BattleMixin
import dialogue as DLG

ASSETS_NEW = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets_new')


class Sandlight23Ext(BattleMixin, HudPolishMixin, JadeUIMixin, RenderPolishMixin, ImageMenuMixin, DialogueUIMixin, PeopleDemo):
    """v0.23 基线 + 对话/石环/新模型/特效扩展。"""

    # 交互点 key -> 角色 key（interact 中 near 命中即进入对话）
    # 注意：elder 不在此列——原「长者」交互点走 rules 主线（greeted），避免被对话挡住
    CHAR_TARGETS = {
        'talk_farmer': 'farmer', 'talk_artisan': 'artisan',
        'talk_priest': 'priest', 'talk_warrior': 'warrior',
        'talk_totem': 'totem', 'talk_deer': 'deer', 'talk_noble': 'noble',
    }
    JADE_TARGETS = {'jade_glow_pick', 'jade_cong_pick', 'jade_ring_pick'}

    # ---------------------------------------------------------------
    # 状态初始化：world() 在父类构造期被调用，不能依赖 __init__
    # ---------------------------------------------------------------
    def _ensure_state(self):
        if not hasattr(self, 'ext_new_nodes'):  self.ext_new_nodes = []      # 新模型节点
        if not hasattr(self, 'ext_jade_fx'):    self.ext_jade_fx = []         # 玉石特效
        if not hasattr(self, 'ext_jade_pick'):  self.ext_jade_pick = {}       # key -> 节点
        if not hasattr(self, 'ext_discs'):      self.ext_discs = []           # 贴地圆盘
        if not hasattr(self, 'night_factor'):   self.night_factor = 0.0       # 夜色浓度 0..1
        if not hasattr(self, 'star_show_until'):self.star_show_until = 0.0    # 观星结束时刻
        if not hasattr(self, 'big_dipper'):     self.big_dipper = []          # 北斗七星节点
        if not hasattr(self, 'rebuilt_walls'):  self.rebuilt_walls = []       # 重建的方正墙段
        if not hasattr(self, 'soft_fire'):      self.soft_fire = []            # 柔和火焰层
        if not hasattr(self, 'fire_sparks'):    self.fire_sparks = []          # 火星粒子
        if not hasattr(self, '_ui_screen_active'): self._ui_screen_active = False
        if not hasattr(self, '_event_beach_done'): self._event_beach_done = False

    def remove_sky_treehouses(self):
        """移除云岸浮岛(baseZ>30)上悬在空中的巨型树屋，其它地面上的保留。"""
        try:
            n = 0
            for node in list(self.render.findAllMatches('**/frontier_tree18')):
                if node.getZ() > 30:      # 只有云岸浮岛(高35m)上那两棵是"天上的"
                    node.hide(); n += 1
            print('[treehouse] hidden %d sky treehouses' % n)
        except Exception:
            pass

    def __init__(self):
        super().__init__()
        self._ensure_state()
        self.remove_sky_treehouses()
        # 对话 UI：font 此时已就绪
        self.init_dialogue_ui()
        self.bind_dialogue_keys()
        self.accept('f', self.demo_all_jade_fx)
        self.accept('n', self.start_stargaze)   # N 键也可观星（方便测试）
        self.accept('b', self.trigger_altar_blue_fx)  # B 键触发祭坛蓝色方圆特效
        # 主菜单：直接用设计图做全屏背景（启行新局/读取玉契/...），点击进入游戏
        try:
            self.init_image_menu()
        except Exception as e:
            print('[menu_image] init failed:', repr(e))
        # 风格化写实渲染润色（暖金主光/冷青补光/薄雾/Bloom/玉石微光）
        try:
            self.init_render_polish()
        except Exception as e:
            print('[render_polish] init failed:', repr(e))
        # 逐玉记设计稿 UI：M 王城圈层地图 / K 礼器·技艺面板
        try:
            self.init_jade_ui()
        except Exception as e:
            print('[jade_ui] init failed:', repr(e))
        # HUD 隶书化 + 玉石图标 + 资源栏可点击（看物资）
        try:
            self.init_hud_polish()
        except Exception as e:
            print('[hud_polish] init failed:', repr(e))
        # 巨怪讨伐战：加载岩石巨怪 + 3武士战斗系统
        try:
            self.init_battle()
        except Exception as e:
            print('[battle] init failed:', repr(e))

    # ---------------------------------------------------------------
    # 世界构建
    # ---------------------------------------------------------------
    def world(self):
        self._ensure_state()
        super().world()
        self.fix_ring_and_walls()
        self.adjust_entry_pillars_and_gather()
        self.place_new_models()
        self.adjust_houses_and_creatures()   # 需在 place_new_models 后(小怪物已生成)
        self.ground_floating_trees()
        self.adjust_waterside_pillars()
        self.build_jade_effects()
        self.build_big_dipper()
        self.build_soft_fire()
        self.build_altar_scene()

    # ---------------------------------------------------------------
    # 石环调转 180° + 落地；绿色圆盘贴地、清理绿色薄片；墙直立落地
    # ---------------------------------------------------------------
    def fix_ring_and_walls(self):
        for node in list(self.builder.instances.getChildren()):
            name = node.getName()
            p = node.getPos(self.render)
            ground = self.height(p.x, p.y)
            # 圆形石环：调转 180°，按包围盒落地
            if 'ring19' in name or 'ring18' in name:
                node.setH(node.getH() + 180)
                lo, hi = node.getTightBounds(self.render)
                node.setZ(node.getZ() + ground - lo.z - .05)
            # 玉旋环落地
            if 'orbit21' in name:
                lo, hi = node.getTightBounds(self.render)
                node.setZ(node.getZ() + ground - lo.z - .06)
            # 墙体：保持 v0.22 原生 wall20 模型与其落地/朝向处理，
            # 位置和形态本就正确（见截图），不再隐藏或重建。

        # 清理石环自带"绿色薄片"：石环附近的 billboard disc 全部隐藏
        for n in list(self.render.findAllMatches('**/+GeomNode')):
            lname = n.getName().lower()
            if 'disc' in lname or 'halo' in lname:
                # 只隐藏玉区/石环区的（x 接近 ±76~100 或 y 在 -50 附近）
                try:
                    p = n.getPos(self.render)
                    if abs(abs(p.x) - 76) < 30 or abs(p.y + 43) < 20:
                        n.hide()
                except Exception:
                    pass

        # 新建贴地绿色圆盘：平铺在石环脚下（setP 不朝相机）
        disc = self.make_ground_disc(3.4, (.18, .78, .52, .5))
        disc.setPos(76, 0, self.height(76, 0) + .04)
        self.ext_discs.append(disc)

    def adjust_entry_pillars_and_gather(self):
        """①入口柱子拉宽拉长拉粗；②石环后侧放『石料+日志』交互(与前面观星分开)。"""
        # ① 入口/门区柱子拉宽拉长拉粗（做成粗壮的巨型门柱构筑物）
        for n in self.builder.instances.getChildren():
            name = n.getName(); low = name.lower()
            p = n.getPos(self.render)
            if 'entry19' in low:
                lo, hi = n.getTightBounds(self.render)
                h = hi.z - lo.z
                cur_w = max(hi.x - lo.x, hi.y - lo.y)
                # 目标宽高比：巨型门柱约 0.6（原来 0.28 太细）
                # 只加宽(X/Y)，高度保持；对每根按比例放大
                target_w = h * 0.62
                if cur_w < target_w:
                    factor = target_w / cur_w
                    sx, sy, sz = n.getScale()
                    n.setScale(sx * factor, sy * factor, sz)
                    lo2, hi2 = n.getTightBounds(self.render)
                    n.setZ(n.getZ() + self.height(p.x, p.y) - lo2.z - .05)  # 保持贴地
            elif 'jadepost' in low and (abs(p.y - 55) < 2):
                if abs(abs(p.x) - 8) < 1.5:
                    n.setScale(8.1, 8.1, 7.8)
                    lo, hi = n.getTightBounds(self.render)
                    n.setZ(n.getZ() + self.height(p.x, p.y) - lo.z - .05)
        # ② 石环双交互：前面(y=-3)观星 star_ring 保留；
        #    把『东南观星祭岛』收集(石料+6/石徽日志)从重合点移到环后面 (76,+4)
        if 'island1' in self.targets:
            pos, label, verb = self.targets['island1']
            newpos = (76.0, 4.0, self.height(76.0, 4.0))
            self.targets['island1'] = (newpos, '观星石环 · 后', '调查石徽 · 石料 +6')
            if 'island1' in self.markers:
                self.markers['island1'].setPos(newpos[0], newpos[1], newpos[2] + 2.6)

    def adjust_houses_and_creatures(self):
        """①东北聚落小屋放大(人可进入感)；②删除棕色木架货摊(stall)；③图腾小怪物缩小。"""
        # ① 房屋放大：所有 hut 放大 1.5 倍（原来 2.9 米高，人进不去）
        for n in self.builder.instances.getChildren():
            name = n.getName(); low = name.lower()
            p = n.getPos(self.render)
            if 'hut' in low:
                sx, sy, sz = n.getScale()
                n.setScale(sx * 1.55, sy * 1.55, sz * 1.55)
                lo, hi = n.getTightBounds(self.render)
                n.setZ(n.getZ() + self.height(p.x, p.y) - lo.z - .05)  # 贴地
            # ② 删除棕色木架货摊 stall（图2突兀的木质几何）
            elif 'stall' in low:
                n.removeNode()
        # ③ 图腾小怪物缩小到 0.5（图3前景大头绿脸小怪物）
        for n in getattr(self, 'ext_new_nodes', []):
            if 'totem_monster' in n.getName():
                n.setScale(0.5)

    def ground_floating_trees(self):
        """把悬浮在空中的古树(frontier_ancient)落地：底面对齐各自地面高度。
        这些是 v21/v22 放的远景古树，原始 z 高达 30~55，浮在天上。"""
        fixed = 0
        for n in self.builder.instances.getChildren():
            low = n.getName().lower()
            if 'ancient' in low:
                p = n.getPos(self.render)
                lo, hi = n.getTightBounds(self.render)
                ground = self.height(p.x, p.y)
                gap = lo.z - ground
                if gap > 1.0:   # 明显悬空才修正（>1米）
                    n.setZ(n.getZ() - gap - .04)
                    fixed += 1
        self.floating_trees_fixed = fixed

    def adjust_waterside_pillars(self):
        """① 水边 3 根玉柱(jadepost -37,29 / -9,40 / 39,30)加宽加大并立于水中；
        ② 把紧邻水渠、视觉上像浮空的大树 arbor(-39,36) 移到旁边空地并贴地。"""
        # ① 水边玉柱：加宽加大 ×1.6，底部沉到水面(z≈0)让她像从水中升起
        for n in self.builder.instances.getChildren():
            if 'jadepost' not in n.getName().lower():
                continue
            p = n.getPos(self.render)
            # 只处理水边那 3 根（排除入口 (±8,55) 已加粗的）
            if abs(abs(p.x) - 8) < 2 and abs(p.y - 55) < 3:
                continue
            n.setScale(5.5, 5.5, 8.0)          # 原 3.43 → 宽×1.6、高×1.6
            lo, hi = n.getTightBounds(self.render)
            n.setZ(n.getZ() + 0.1 - lo.z)       # 底部落到水面 z=0.1（立于水中）
        # ② 大树 arbor(-39,36)：树冠太宽伸到水面上方像浮空，移到旁边空地
        for n in self.builder.instances.getChildren():
            if n.getName().lower() != 'arbor':
                continue
            p = n.getPos(self.render)
            if abs(p.x + 39) < 2 and abs(p.y - 36) < 2:
                nx, ny = -36, 41                 # 移回神树之门/神木交互点旁(贴地立正,不再浮空)
                ground = self.height(nx, ny)
                lo, hi = n.getTightBounds(self.render)
                # 平移：先算当前底部世界 z，再对齐到新位置地面
                n.setPos(nx, ny, n.getZ() + ground - lo.z)
                lo2, hi2 = n.getTightBounds(self.render)
                n.setZ(n.getZ() + ground - lo2.z - .05)
                if not hasattr(self, 'moved_trees'):
                    self.moved_trees = []
                self.moved_trees.append(n.getName())

    def rebuild_walls(self, specs):
        """方正直立石墙：标准长方体几何 + 整齐砖墙贴图，横向一排排、加厚、浅色。

        说明：tripo『石质外墙』模型贴图本身是乱石堆，即使几何掰直，视觉上仍是斜石块，
        无法得到方正方正的长方体墙。故改用程序生成砖墙贴图 + 带UV立方体，几何严格方正。
        """
        # 用你提供的『石质外墙』模型：几何已在 Blender 重塑成规整单位盒子(1×1×1,
        # 底部z=0)，保留模型自带 UV 与贴图。这样既是这个模型、几何又绝对方正直立。
        path = Filename.fromOsSpecific(os.path.join(ASSETS_NEW, 'stone_wall_cube.bam'))
        self.stone_wall_model = self.loader.loadModel(path)
        # 浅色版贴图：对模型原 basecolor 提亮+去饱和，弱化深色石块感
        self.wall_light_tex = self.loader.loadTexture(
            Filename.fromOsSpecific(os.path.join(ASSETS_NEW, 'wall_light.png')))
        rng = random.Random(2001)
        THICK = 1.7          # 墙加厚
        SEAM = 1.14          # 段长放大系数：让相邻段明确重叠，消除可见接缝
        for idx, (x, y, ground, sx, sy, height) in enumerate(specs):
            along_x = sx >= sy
            length = max(sx, sy) * SEAM            # 加长以无缝拼接
            if length < .5:
                continue
            h = height if height > .3 else 2.3
            node = self.effects.attachNewNode('stone_wall_%d' % idx)
            node.setPos(x, y, ground)              # 模型底部 z=0，直直垂直落地
            if along_x:
                node.setH(90)                      # 长边沿 X（横向一排）
            # 模型本地为 0..1 盒子：X=厚 Y=长 Z=高；hpr 保持(0/90,0,0) 完全垂直
            node.setScale(THICK, length, h)
            self.stone_wall_model.instanceTo(node)
            node.setTexture(self.wall_light_tex)    # 覆盖为极淡贴图
            node.setColorScale(1, 1, 1, 1)          # 贴图已极淡，不再提亮
            self.rebuilt_walls.append(node)

    def make_ground_disc(self, radius, color):
        from panda3d.core import (Geom, GeomNode, GeomVertexData,
                                  GeomVertexFormat, GeomVertexWriter, GeomTriangles)
        fmt = GeomVertexFormat.getV3c4()
        data = GeomVertexData('ground disc', fmt, Geom.UHStatic)
        v = GeomVertexWriter(data, 'vertex'); c = GeomVertexWriter(data, 'color')
        tris = GeomTriangles(Geom.UHStatic)
        v.addData3(0, 0, 0); c.addData4(*color)
        seg = 24
        for i in range(seg + 1):
            a = i * math.tau / seg
            v.addData3(radius * math.cos(a), radius * math.sin(a), 0)
            c.addData4(color[0], color[1], color[2], 0.0)
        for i in range(seg):
            tris.addVertices(0, i + 1, i + 2)
        geom = Geom(data); geom.addPrimitive(tris)
        gn = GeomNode('jade ground disc'); gn.addGeom(geom)
        node = self.effects.attachNewNode(gn)
        node.setTransparency(TransparencyAttrib.MAlpha)
        node.setDepthWrite(False)
        return node

    # ---------------------------------------------------------------
    # 新模型加载与摆放
    # ---------------------------------------------------------------
    def load_new_model(self, name, x, y, z, scale=1.0, heading=0.0):
        path = Filename.fromOsSpecific(os.path.join(ASSETS_NEW, name + '.bam'))
        model = self.loader.loadModel(path)
        node = self.effects.attachNewNode('ext_' + name)
        node.setPos(x, y, z); node.setScale(scale); node.setH(heading)
        model.reparentTo(node)
        lo, hi = node.getTightBounds(self.render)
        node.setZ(node.getZ() + z - lo.z)
        self.ext_new_nodes.append(node)
        return node

    def place_new_models(self):
        rng = random.Random(2301)
        # --- 图腾小怪物群：围绕玉雕与神树图腾竖立守护 ---
        # 中心点 = 场景里已有的三处玉雕/图腾（图二那种青绿玉石雕塑+大树）
        #   西玉雕 jade21(-95,-43) / 东玉旋环 orbit21(95,-43) / 神树图腾 totem23(100,91)
        guard_centers = [(-95, -43), (95, -43), (100, 91)]
        for ci, (cx, cy) in enumerate(guard_centers):
            for j in range(4):
                ang = j * math.tau / 4 + ci * .4
                px = cx + 4.5 * math.cos(ang)
                py = cy + 4.5 * math.sin(ang)
                # 朝向中心玉雕站立：heading 指向圆心（模型已修正为站立，不再躺倒）
                face = math.degrees(math.atan2(cy - py, cx - px))
                self.load_new_model('totem_monster', px, py, self.height(px, py),
                                    1.0, face)
        # 对话点放在西玉雕旁（玩家最容易接近的一处）
        self.add_target('talk_totem', (-91, -43, self.height(-91, -43) + .6),
                        '图腾小怪物 · 玉灵', 'E 与玉灵交谈')
        # --- 神鹿：林间引路灵兽 ---
        dz = self.height(60, 60)
        self.load_new_model('deer_god', 60, 60, dz, 1.0, -90)
        self.add_target('talk_deer', (60, 60, dz + .6), '神鹿 · 白蹄', 'E 与神鹿交流')

        # --- 发光玉石 / 玉琮 / 玉石旋环：边缘拾取域 ---
        jade_spots = [
            ('glow_jade', -100, -48, 'jade_glow_pick', '发光玉石'),
            ('jade_cong', -88, -52, 'jade_cong_pick', '玉琮'),
            ('jade_ring', -96, -56, 'jade_ring_pick', '玉石旋环'),
            ('glow_jade', 100, -48, 'jade_glow_pick_e', '发光玉石·东'),
        ]
        for name, x, y, key, label in jade_spots:
            z = self.height(x, y)
            node = self.load_new_model(name, x, y, z, 1.0, 0)
            self.ext_jade_pick[key] = node
            self.add_target(key, (x, y, z + .5), label, 'E 感应 / 拾取玉')
        # --- 其余角色对话点：给 v23 已有的 NPC 旁加对话交互 ---
        # （长者不建新交互点：原 targets['elder'] 已有「长者」标签，避免文字重叠）
        npc_talk = [
            ('talk_farmer', 18, -32, '农夫 · 阿禾'),
            ('talk_artisan', -20, 34, '工匠 · 石乙'),
            ('talk_priest', -4, 83, '巫祝 · 云巫'),
            ('talk_warrior', 6, -24, '武士 · 戈'),
            ('talk_noble', 23, 83, '玉君'),
        ]
        for key, x, y, label in npc_talk:
            self.add_target(key, (x, y, self.height(x, y) + .4), label, 'E 交谈')

    # ---------------------------------------------------------------
    # 玉石交互特效（参考图3）：青绿旋转弧 + 发光核心 + 漂浮碎屑
    # ---------------------------------------------------------------
    def build_jade_effects(self):
        self._jade_glow_tex = None
        for key, node in self.ext_jade_pick.items():
            p = node.getPos(self.render)
            cx, cy, cz = p.x, p.y, p.z + 1.0
            arcs = []
            for k in range(3):
                arc = self.make_arc(1.3 + k * .35, (.15, 1.0, .72, .9))
                arc.setPos(cx, cy, cz); arc.hide(); arcs.append(arc)
            core = self.make_glow_card(1.6, (.35, 1.0, .72, .85)); core.setPos(cx, cy, cz); core.hide()
            rng = random.Random(sum(ord(ch) for ch in key))
            sparks = []
            for i in range(12):
                s = self.make_glow_card(.18, (.6, 1.0, .5, .9))
                s.hide(); sparks.append((s, rng.random() * math.tau, rng.uniform(.4, 1.6)))
            self.ext_jade_fx.append({'key': key, 'center': (cx, cy, cz), 'arcs': arcs,
                                     'core': core, 'sparks': sparks, 'active_until': 0.0})

    def make_arc(self, radius, color):
        from panda3d.core import LineSegs
        segs = LineSegs('jade arc'); segs.setThickness(3)
        segs.setColor(color[0], color[1], color[2], color[3])
        span = math.pi * 1.25
        for i in range(25):
            a = span * i / 24
            segs.drawTo(radius * math.cos(a), radius * math.sin(a), 0)
        node = self.effects.attachNewNode(segs.create()); node.setLightOff()
        return node

    def make_glow_card(self, size, color):
        if self._jade_glow_tex is None:
            img = PNMImage(64, 64, 4)
            for yy in range(64):
                for xx in range(64):
                    r = ((xx - 31.5) / 32) ** 2 + ((yy - 31.5) / 32) ** 2
                    img.setXelA(xx, yy, color[0], color[1], color[2], max(0, 1 - r) ** 3)
            tex = Texture('jade glow'); tex.load(img)
            self._jade_glow_tex = tex
        card = CardMaker('jade glow card'); card.setFrame(-1, 1, -1, 1)
        node = self.effects.attachNewNode(card.generate())
        node.setTexture(self._jade_glow_tex)
        node.setBillboardPointEye(); node.setLightOff(); node.setShaderOff()
        node.setDepthWrite(False); node.setTransparency(TransparencyAttrib.MAlpha)
        node.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                       ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne))
        node.setScale(size)
        return node

    # ---------------------------------------------------------------
    # 观星：北斗七星 + 天色转暗（靠近观星石环按 E 触发）
    # ---------------------------------------------------------------
    def build_big_dipper(self):
        """在石环上方天空搭北斗七星（勺形）：7 颗星 + 连线，初始隐藏。"""
        # 勺形相对坐标（x 向右, z 向上），天枢→天璇→天玑→天权为斗，玉衡→开阳→摇光为柄
        pattern = [
            (-4.5, 3.2),   # 天枢 Dubhe
            (-4.0, 1.6),   # 天璇 Merak
            (-2.2, 1.3),   # 天玑 Phecda
            (-1.8, 2.9),   # 天权 Megrez
            ( 0.0, 3.0),   # 玉衡 Alioth
            ( 1.9, 2.4),   # 开阳 Mizar
            ( 3.7, 1.4),   # 摇光 Alkaid
        ]
        edges = [(0, 1), (1, 2), (2, 3), (3, 0), (3, 4), (4, 5), (5, 6)]
        cx, cy, cz = 76, 34, 52          # 石环上方偏后高空
        self.star_center = (cx, cy, cz)
        # 星点：白色/淡青发光卡片
        if not hasattr(self, '_star_tex'):
            img = PNMImage(64, 64, 4)
            for yy in range(64):
                for xx in range(64):
                    r = ((xx - 31.5) / 32) ** 2 + ((yy - 31.5) / 32) ** 2
                    core = max(0, 1 - r) ** 4
                    spike = max(0, 1 - abs(xx - 31.5) / 32) ** 12 * max(0, 1 - abs(yy - 31.5) / 12) if abs(yy - 31.5) < 12 else 0
                    spike2 = max(0, 1 - abs(yy - 31.5) / 32) ** 12 * max(0, 1 - abs(xx - 31.5) / 12) if abs(xx - 31.5) < 12 else 0
                    a = min(1, core + .5 * spike + .5 * spike2)
                    img.setXelA(xx, yy, .92, .98, 1.0, a)
            tex = Texture('star glow'); tex.load(img)
            self._star_tex = tex
        self.big_dipper = []
        for i, (sx, sz) in enumerate(pattern):
            card = CardMaker('star%d' % i); card.setFrame(-1, 1, -1, 1)
            node = self.effects.attachNewNode(card.generate())
            node.setTexture(self._star_tex)
            node.setBillboardPointEye(); node.setLightOff(); node.setShaderOff()
            node.setDepthWrite(False); node.setDepthTest(False)
            node.setTransparency(TransparencyAttrib.MAlpha)
            node.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                           ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne))
            node.setPos(cx + sx, cy, cz + sz)
            node.setScale(1.5 if i in (0, 6) else 1.1)
            node.setColorScale(.75, .88, 1, 1)
            node.hide()
            self.big_dipper.append(node)
        # 连线（暗青色细线，连接斗形）
        from panda3d.core import LineSegs
        segs = LineSegs('dipper lines'); segs.setThickness(1.5)
        segs.setColor(.45, .75, .95, 1)
        for a, b in edges:
            ax, az = pattern[a]; bx, bz = pattern[b]
            segs.moveTo(cx + ax, cy, cz + az); segs.drawTo(cx + bx, cy, cz + bz)
        self.dipper_lines = self.effects.attachNewNode(segs.create())
        self.dipper_lines.setLightOff(); self.dipper_lines.setDepthTest(False)
        self.dipper_lines.hide()

    # ---------------------------------------------------------------
    # 柔和火焰：多层软边光晕 billboard + 摇曳呼吸 + 火星（替换尖锐锥体）
    # ---------------------------------------------------------------
    def build_soft_fire(self):
        # 隐藏旧的锥体火舌（v16 living_flames）与旧 flame
        for n in getattr(self, 'living_flames', []):
            n.hide()
        if hasattr(self, 'flame'):
            self.flame.hide()
        # 营火柴堆放大（logs 在 v16 加载，找 effects/render 下名为 logs 的实例化）
        for n in self.render.findAllMatches('**/logs'):
            if abs(n.getPos(self.render).x) < 3 and abs(n.getPos(self.render).y) < 3:
                n.setScale(2.9, 2.9, 2.9)   # 原 2.15 -> 2.9，篝火更大

        # 软边渐变贴图：中心亮黄 -> 橙 -> 暗红 -> 透明
        img = PNMImage(128, 128, 4)
        for yy in range(128):
            for xx in range(128):
                nx = (xx - 63.5) / 64.0; ny = (yy - 63.5) / 64.0
                r = math.sqrt(nx * nx + ny * ny)
                a = max(0.0, 1.0 - r) ** 2.2
                # 内白黄，外橙红
                if r < .35:
                    cr, cg, cb = 1.0, .92, .55
                elif r < .7:
                    cr, cg, cb = 1.0, .48, .10
                else:
                    cr, cg, cb = .85, .20, .04
                img.setXelA(xx, yy, cr, cg, cb, a)
        tex = Texture('soft fire'); tex.load(img)
        self._fire_tex = tex
        card = CardMaker('fire glow'); card.setFrame(-1, 1, -1, 1)

        # 多层光晕：从底到顶，尺度/颜色/相位不同，叠加成灵动火焰
        layers = [
            # (相对高度, 基础宽, 基础高, 颜色, 相位)
            (0.45, 1.5, 1.4, (1.00, .55, .15, 1), 0.0),   # 底部宽橙光
            (0.85, 1.1, 1.7, (1.00, .70, .25, 1), 1.1),   # 中段亮黄
            (1.25, .75, 1.6, (1.00, .82, .40, 1), 2.3),   # 上段淡黄
            (1.65, .45, 1.2, (1.00, .60, .20, 1), 3.5),   # 顶部摇曳
        ]
        self.soft_fire = []
        for i, (z, w, hgt, color, ph) in enumerate(layers):
            node = self.effects.attachNewNode(card.generate())
            node.setTexture(tex)
            node.setBillboardPointEye(); node.setLightOff(); node.setShaderOff()
            node.setDepthWrite(False); node.setTransparency(TransparencyAttrib.MAlpha)
            node.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                           ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne))
            node.setPos(0, 0, z)
            node.setScale(w, 1, hgt)
            node.setColorScale(*color)
            self.soft_fire.append((node, z, w, hgt, color, ph))

        # 火星：小亮点上升飘散（用火焰贴图，暖橙色，不复用玉绿贴图）
        self.fire_sparks = []
        rng = random.Random(99)
        for i in range(14):
            s = self.effects.attachNewNode(card.generate())
            s.setTexture(tex)
            s.setBillboardPointEye(); s.setLightOff(); s.setShaderOff()
            s.setDepthWrite(False); s.setTransparency(TransparencyAttrib.MAlpha)
            s.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd,
                        ColorBlendAttrib.OIncomingAlpha, ColorBlendAttrib.OOne))
            s.setScale(.10); s.setColorScale(1.0, .72, .30, 1)
            self.fire_sparks.append((s, rng.random() * math.tau,
                                     rng.uniform(.5, 1.5), rng.uniform(0, 6)))

    def update_soft_fire(self):
        for node, z, w, hgt, color, ph in self.soft_fire:
            # 火光呼吸 + 摇曳：宽窄与高度随时间起伏，横向轻微摆动
            breathe = .82 + .18 * math.sin(self.t * 5.5 + ph)
            sway = .16 * math.sin(self.t * 3.3 + ph * 1.7)
            node.setPos(sway, .06 * math.cos(self.t * 4.1 + ph), z + .05 * math.sin(self.t * 6 + ph))
            node.setScale(w * breathe, 1, hgt * (.9 + .15 * math.sin(self.t * 7 + ph)))
            # 颜色在橙-黄间流动
            flick = .9 + .1 * math.sin(self.t * 9 + ph * 2)
            node.setColorScale(color[0], color[1] * flick, color[2] * flick, 1)
        for s, phase, speed, offset in self.fire_sparks:
            life = (self.t * speed + offset) % 2.4
            rise = life / 2.4
            a = phase + self.t * .9
            s.setPos(.55 * math.cos(a) * rise, .55 * math.sin(a) * rise, .4 + rise * 2.2)
            s.setScale(.10 * (1 - rise * .7))
            s.setAlphaScale(max(0, 1 - rise))
            s.show()

    # ---------------------------------------------------------------
    # 祭坛玉琮 + 蓝色方圆特效 + 高台空地丰富
    # ---------------------------------------------------------------
    def build_altar_scene(self):
        import altar_scene
        self._altar_scene = altar_scene
        altar_scene.place_jade_cong(self)
        altar_scene.build_altar_fx(self)
        altar_scene.enrich_highland(self)
        altar_scene.restore_market_stall(self)
        altar_scene.place_plaza_models(self)

    def trigger_altar_blue_fx(self):
        self._altar_scene.trigger_altar_fx(self, duration=8)
        self.toast = '玉琮共鸣，方与圆的蓝光在祭坛上苏醒。'
        self.toasting = 6

    def start_stargaze(self):
        """触发观星：天色转暗 + 北斗七星显现，持续约 12 秒。"""
        self.star_show_until = self.t + 12
        self.toast = '石环指向天心。夜色降临，北斗七星在环上苏醒。'
        self.toasting = 7
        if hasattr(self, 'cue'):
            self.cue('portal', '观星共鸣')

    def trigger_jade_fx(self, key):
        for fx in self.ext_jade_fx:
            if fx['key'] == key:
                fx['active_until'] = self.t + 6

    def demo_all_jade_fx(self):
        for fx in self.ext_jade_fx:
            fx['active_until'] = self.t + 6

    # ---------------------------------------------------------------
    # 交互：对话优先，其次玉石拾取，最后交回父类
    # ---------------------------------------------------------------
    def interact(self):
        near = getattr(self, 'near', None)
        # 岩石巨怪：按 E 进入讨伐战（战斗中不再触发）
        if near == 'golem' and not getattr(self, '_bt_active', False):
            if self.try_battle_interact():
                return
        if getattr(self, '_bt_active', False):
            return   # 战斗中屏蔽其它交互
        if near in self.CHAR_TARGETS and not self.in_conversation:
            self.start_dialogue(self.CHAR_TARGETS[near])
            return
        if near == 'star_ring' and not self.dialog:
            self.start_stargaze()
            return
        if near == 'altar' and not self.dialog:
            self.trigger_altar_blue_fx()      # 祭祀交互触发蓝色方圆特效
            return super().interact()          # 同时保留原祭祀结算
        if near in self.JADE_TARGETS and not self.dialog:
            self.trigger_jade_fx(near)
            self.toast = self.dlg_engine.small_talk('noble', 'explore') + '  【玉光响应】'
            self.toasting = 6
            self.cue('portal', '玉石共鸣')
            return
        return super().interact()

    # ---------------------------------------------------------------
    # 每帧：特效动画
    # ---------------------------------------------------------------
    def update(self, task):
        # 主菜单：背景是设计图，菜单期间跳过漫游逻辑
        # 先确保菜单期间不出现任何游戏 HUD 装饰/按钮
        try:
            if getattr(self, '_im_open', False):
                self._hp_decor.hide()
                if getattr(self, '_roam_btn', None) is not None:
                    self._roam_btn.hide()
        except Exception:
            pass
        try:
            if self.image_menu_camera():
                return task.cont
        except Exception:
            pass
        result = super().update(task)
        # 巨怪讨伐战：驱动武士跑动/攻击/巨怪反击动画
        try:
            self.update_battle(task.dt if hasattr(task, 'dt') else 0.016)
        except Exception:
            pass
        # 纯漫游模式：压制 main.py 每帧重新显示的标记/文字
        try:
            self.enforce_roam_only()
        except Exception:
            pass
        # 风格化写实 grade：压住 v02 天气覆盖，暖金主光+冷青补光+薄雾
        try:
            self.apply_render_grade()
        except Exception:
            pass
        # 柔和火焰：v16 的 update 会每帧重设 living_flames，这里再压一次隐藏+驱动新火焰
        for n in getattr(self, 'living_flames', []):
            n.hide()
        if hasattr(self, 'flame'): self.flame.hide()
        self.update_soft_fire()
        # 祭坛蓝色方圆特效
        if hasattr(self, '_altar_scene'):
            self._altar_scene.update_altar_fx(self)
        # 观星石环交互放宽：石环直径9米，底层 near 判定只有2.6米太近。
        # 只在玩家位于石环【南侧前门】(y<-1)时放宽到6.5米触发观星；
        # 环【北侧后门】(y>1)留给 island1 的『石料+日志』交互，两者互不抢占。
        if not self.dialog and not self.in_conversation:
            sp = self.targets.get('star_ring')
            if sp:
                from panda3d.core import Vec3
                pp = self.player.getPos()
                d = (pp - Vec3(*sp[0])).length()
                if pp.y < -1 and d < 6.5 and (not self.near or self.near == 'star_ring' or d < 2.6):
                    self.near = 'star_ring'
                    if hasattr(self, 'prompt'):
                        self.prompt.setText('[ E ]  观星 · 北斗夜色')
                    if hasattr(self, 'markers') and 'star_ring' in self.markers:
                        self.markers['star_ring'].show()
        for fx in self.ext_jade_fx:
            active = self.t < fx['active_until']
            cx, cy, cz = fx['center']
            for k, a in enumerate(fx['arcs']):
                if active:
                    a.show()
                    a.setH(self.t * (90 + k * 40) * (1 if k % 2 else -1))
                    a.setScale(1 + .12 * math.sin(self.t * 3 + k))
                else:
                    a.hide()
            if active:
                fx['core'].show()
                fx['core'].setScale(1.6 + .3 * math.sin(self.t * 4))
            else:
                fx['core'].hide()
            for s, phase, height in fx['sparks']:
                if not active:
                    s.hide(); continue
                s.show()
                a = phase + self.t * .8
                life = (self.t * height) % 2.2
                s.setPos(cx + 1.5 * math.cos(a), cy + 1.5 * math.sin(a),
                         cz + life - .6)
                s.setScale(.18 * (1 - .3 * life / 2.2))

        # ---- 观星夜色：在父类天气循环之后覆盖天色，压住白昼配色 ----
        stargazing = self.t < self.star_show_until
        target_night = 1.0 if stargazing else 0.0
        rate = .03 if stargazing else .015          # 淡入快、淡出慢
        self.night_factor += (target_night - self.night_factor) * min(1.0, rate * 60 * 0.016)
        nf = self.night_factor
        if nf > .001:
            # 白天基准色（v02 天气系统算出的当前值）
            base_sky = getattr(self, 'sky_now', [.77, .73, .54])
            base_sun = getattr(self, 'sun_now', [1.03, .91, .65])
            base_amb = getattr(self, 'ambient_now', [.45, .45, .35])
            night_sky = (.025, .04, .10)
            night_sun = (.12, .16, .34)
            night_amb = (.10, .13, .28)
            mix = lambda a, b: tuple(x + (y - x) * nf for x, y in zip(a, b))
            sky = mix(base_sky, night_sky)
            sun = mix(base_sun, night_sun)
            amb = mix(base_amb, night_amb)
            self.setBackgroundColor(*sky, 1)
            if hasattr(self, 'fog'):
                self.fog.setColor(*sky)
                self.fog.setExpDensity(.006 + .004 * nf)
            if hasattr(self, 'sun'):  self.sun.setColor((*sun, 1))
            if hasattr(self, 'ambient'): self.ambient.setColor((*amb, 1))
            # 星空显现 + 闪烁
            twinkle = .78 + .22 * math.sin(self.t * 2.2)
            for i, node in enumerate(self.big_dipper):
                node.show()
                node.setColorScale(.75 * twinkle, .88 * twinkle, 1.0, nf)
            self.dipper_lines.setColorScale(.45, .75, .95, nf * .8)
            self.dipper_lines.show()
        else:
            for node in self.big_dipper: node.hide()
            self.dipper_lines.hide()
        return result

    def sync_ui(self):
        super().sync_ui()
        if hasattr(self, 'goal') and hasattr(self, 'dlg_engine'):
            top = sorted(self.dlg_engine.affinity.items(), key=lambda kv: -kv[1])[:2]
            if top and top[0][1] > 0:
                txt = '  |  ' + '  '.join(
                    f'{DLG.CHARACTERS[k].name.split(" · ")[-1]} {v}' for k, v in top)
                self.goal.setText(self.goal.getText() + txt)


if __name__ == '__main__':
    loadPrcFileData('', 'window-title Sandlight 0.23+ | Jade & Dialogue')
    Sandlight23Ext().run()
