# -*- coding: utf-8 -*-
"""逐玉记 · 巨怪讨伐战（battle_system.py）
================================================
用户方案：指令面板(下命令) + 场景里武士真实跑动攻击，两者结合。
战场：外环稻田 (0,-34) 附近；3 名现有 warrior23 武士。

以 BattleMixin 混入 Demo：
  · init_battle()        — 加载巨怪、注册交互点、建指令UI、建血条
  · interact 拦截 golem  — 按 E 开战
  · update_battle(dt)    — 每帧驱动武士跑动/攻击、巨怪受击、动画状态机

玩法：
  回合制。玩家是「王」，每回合对 3 武士下令：
    冲锋(高伤/反击高) / 坚守(低伤/反击低) / 蓄势(回血/不攻击) / 撤退(退出)
  下令后播放跑动+攻击动画→结算→巨怪反击→下一回合。
  胜：巨怪血尽 → 奖励材料+玉器；败：武士全灭 → 损失材料。
"""
import os, math
from panda3d.core import (
    Filename, Vec3, TextNode, CardMaker, TransparencyAttrib,
    Point3, NodePath,
)
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectButton

GOLEM_POS = (-98, 42)         # 战场中心（西外环右后方野花草丛：翻正后立于草地，远离土路与水边）
GOLEM_HP = 120
GOLEM_SCALE = 4.2              # 目标高度(米)，模型原始高~1.0
SAMURAI_HP = 40

PANEL_BG = (0.16, 0.13, 0.09, 0.92)
CARD_BG  = (0.34, 0.28, 0.17, 0.90)
GOLD     = (0.95, 0.82, 0.58)
JADE     = (0.66, 0.80, 0.74)
RED      = (0.78, 0.30, 0.24)
SHADOW   = (0.04, 0.03, 0.02, 1)


class BattleMixin:

    # =============================================================
    # 初始化
    # =============================================================
    def init_battle(self):
        self._bt_active = False
        self._bt_phase = 'idle'        # idle/charge/strike/counter/settle
        self._bt_t = 0.0
        self._bt_round = 0
        self._bt_golem_hp = GOLEM_HP
        self._bt_golem_max = GOLEM_HP
        self._bt_samurai = []          # [{node,home,hp,max,offset}]
        self._bt_log = []
        self._bt_hit_fx = []           # 打击特效活跃列表
        self._bt_fx_root = self.render.attachNewNode('bt_hit_fx')

        # 1) 加载巨怪模型
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'assets_new', 'rock_golem', 'golem.fbx')
            model = self.loader.loadModel(Filename.fromOsSpecific(path))
            self._bt_golem = self.render.attachNewNode('rock_golem')
            model.reparentTo(self._bt_golem)
            # 模型是 Y-up 长轴(raw size 0.59 x 1.0 x 0.95)，横躺；
            # 绕 X 轴 pitch +90° 让长轴(Y)转到 Z 且头朝上（上一版 -90 是倒立）
            model.setP(90)
            # 再按旋转后的 Z 高度归一化到 GOLEM_SCALE
            lo, hi = model.getTightBounds(self._bt_golem)
            h = max(0.01, hi.z - lo.z)
            model.setScale(GOLEM_SCALE / h)
            # 贴地（用旋转缩放后的真实底边）
            lo, hi = model.getTightBounds(self._bt_golem)
            self._bt_golem.setPos(GOLEM_POS[0], GOLEM_POS[1],
                                  self.height(*GOLEM_POS) - lo.z)
            self._bt_golem.setH(180)
            self._bt_golem.setColor(1, 1, 1, 1)
            self._bt_golem_base_color = (1, 1, 1, 1)
            # 强制贴上 basecolor（FBX 材质的贴图引用常失效导致模型全白）
            tex_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'assets_new', 'rock_golem', 'golem_basecolor.jpg')
            try:
                tex = self.loader.loadTexture(Filename.fromOsSpecific(tex_path))
                for gn in model.findAllMatches('**/+GeomNode'):
                    gn.setTexture(tex)
            except Exception:
                pass
        except Exception as e:
            print('[battle] golem load failed:', repr(e))
            self._bt_golem = None

        # 2) 3 名现有武士
        for role, node in getattr(self, 'people23', []):
            if 'warrior' in role and len(self._bt_samurai) < 3:
                self._bt_samurai.append(dict(
                    node=node,
                    home=node.getPos(),
                    hp=SAMURAI_HP, max=SAMURAI_HP,
                    offset=Vec3((len(self._bt_samurai)-1)*2.2 - 2.2, -3.2, 0)))

        # 3) 注册巨怪交互点
        try:
            self.add_target('golem', (GOLEM_POS[0], GOLEM_POS[1], self.height(*GOLEM_POS)),
                            '岩石巨怪', '讨伐岩石巨怪')
        except Exception:
            pass

        # 4) 血条（3D billboard，战斗时显示）
        self._build_healthbars()
        # 5) 指令面板
        self._build_battle_panel()

    def _bar(self, parent, w, h, color, name):
        cm = CardMaker('bt_' + name); cm.setFrame(0, w, -h/2, h/2)
        n = parent.attachNewNode(cm.generate())
        n.setColor(*color); n.setBin('fixed', 130); n.setDepthWrite(False)
        return n

    # ---------------------------------------------------------
    # 打击特效：星芒 + 扩散光环 + 闪光球（billboard，0.55秒淡出）
    # ---------------------------------------------------------
    def _spawn_hit_fx(self, pos, color=(1.0, .84, .45), scale=1.0):
        """在 3D 世界坐标 pos 生成一次打击特效。"""
        try:
            root = self._bt_fx_root.attachNewNode('hitfx')
            root.setPos(pos)
            root.setBillboardPointEye()
            root.setBin('fixed', 132)
            root.setDepthWrite(False)
            # 中心闪光球（一个方片，绕45°成菱形）
            cm = CardMaker('fx_core')
            cm.setFrame(-.28, .28, -.28, .28)
            core = root.attachNewNode(cm.generate())
            core.setColor(color[0], color[1], color[2], 1)
            core.setR(45)
            # 四条星芒
            for ang in (0, 90, 45, 135):
                cm2 = CardMaker('fx_ray')
                cm2.setFrame(0, .85, -.035, .035)
                ray = root.attachNewNode(cm2.generate())
                ray.setColor(color[0], color[1], color[2], .9)
                ray.setR(ang)
            # 扩散光环（LineSegs 圆环）
            from panda3d.core import LineSegs
            ls = LineSegs(); ls.setThickness(3)
            ls.setColor(color[0], color[1], color[2], 1)
            segs = 24
            for i in range(segs + 1):
                a0 = math.radians(360.0 * i / segs)
                px, py = .7 * math.cos(a0), .7 * math.sin(a0)
                if i == 0: ls.moveTo(px, py, 0)
                else: ls.drawTo(px, py, 0)
            ring = root.attachNewNode(ls.create())
            root.setScale(scale)
            root.setTransparency(TransparencyAttrib.MAlpha)
            self._bt_hit_fx.append(dict(root=root, t=0.0, life=.55, base=scale))
        except Exception:
            pass

    def _update_hit_fx(self, dt):
        """每帧推进特效：放大 + 淡出，到期移除。"""
        for fx in list(self._bt_hit_fx):
            fx['t'] += dt
            k = fx['t'] / fx['life']
            if k >= 1.0:
                try: fx['root'].removeNode()
                except Exception: pass
                self._bt_hit_fx.remove(fx)
                continue
            try:
                s = fx['base'] * (0.4 + 2.2 * k)
                fx['root'].setScale(s)
                fx['root'].setColorScale(1, 1, 1, 1 - k)   # 整体淡出
            except Exception:
                pass

    def _build_healthbars(self):
        self._hp_bars = self.render.attachNewNode('bt_hpbars')
        # 巨怪血条
        self._golem_bar_root = self._hp_bars.attachNewNode('golem_bar')
        self._golem_bar_root.setPos(GOLEM_POS[0], GOLEM_POS[1],
                                    self.height(*GOLEM_POS) + GOLEM_SCALE + 1.2)
        self._golem_bar_root.setBillboardPointEye()
        self._bar(self._golem_bar_root, 2.4, .16, (0.1, 0.08, 0.06, .85), 'gb_bg')
        self._golem_bar_fill = self._bar(self._golem_bar_root, 2.35, .12, RED, 'gb_fill')
        self._golem_bar_fill.setPos(0.025, 0, 0)
        self._golem_bar_label = OnscreenText(parent=self._golem_bar_root, text='岩石巨怪',
            font=getattr(self, 'font', None), pos=(0, .22), align=TextNode.ACenter,
            scale=.32, fg=(GOLD[0], GOLD[1], GOLD[2], 1))
        self._golem_bar_label.setBin('fixed', 132)
        self._hp_bars.hide()

    def _build_battle_panel(self):
        """扁平底部 HUD：不遮挡中间战斗画面。顶部一行状态、底部一排指令、日志在底部上方。"""
        root = self.aspect2d.attachNewNode('battle_panel')

        # 顶部：一行细窄半透明状态条（贴屏幕顶，不挡视野）
        cm = CardMaker('battle_top')
        cm.setFrame(-1.5, 1.5, -.055, .055)
        topbg = root.attachNewNode(cm.generate())
        topbg.setColor(.10, .08, .05, .55); topbg.setBin('fixed', 140)
        topbg.setPos(0, 0, .93); topbg.setDepthWrite(False)
        self._bt_status = self._txtb(root, '', 0, .93, .030, JADE, 1, 'battle_status')

        # 底部：一排扁平指令按钮（贴屏幕底）
        cmds = [('冲 锋', self._cmd_charge, -1.02),
                ('坚 守', self._cmd_guard, -.34),
                ('蓄 势', self._cmd_rest, .34),
                ('撤 退', self._cmd_retreat, 1.02)]
        self._bt_buttons = []
        for label, fn, x in cmds:
            bc = CardMaker('bcmd'); bc.setFrame(-.28, .28, -.045, .045)
            bnode = root.attachNewNode(bc.generate())
            bnode.setColor(.30, .25, .16, .78); bnode.setBin('fixed', 142)
            bnode.setPos(x, 0, -.90); bnode.setDepthWrite(False)
            self._txtb(bnode, label, 0, 0, .034, GOLD, 1, 'bcmd_lbl')
            DirectButton(parent=bnode, text='', scale=(.28, 1, .045),
                         frameSize=(-1, 1, -1, 1), pos=(0, 0, 0),
                         frameColor=(0, 0, 0, 0), relief=1,
                         command=fn, sortOrder=143)
            self._bt_buttons.append(bnode)

        # 日志：按钮上方一行小字（贴底，短日志，不挡中间）
        self._bt_log_text = self._txtb(root, '', 0, -.80, .022, GOLD, 1, 'battle_log')
        root.hide()
        self._bt_panel = root

    def _txtb(self, parent, text, x, z, scale, color, align, name):
        t = OnscreenText(parent=parent, text=str(text), font=getattr(self, 'font', None),
                         pos=(x, z), align=align, scale=scale,
                         fg=(color[0], color[1], color[2], 1), mayChange=True)
        t.setBin('fixed', 145)
        t.setShadow(SHADOW)
        return t

    # =============================================================
    # 交互：开战
    # =============================================================
    def try_battle_interact(self):
        if getattr(self, 'near', None) != 'golem':
            return False
        if self._bt_active:
            return True
        self.start_battle()
        return True

    def start_battle(self):
        self._bt_active = True
        self._bt_phase = 'idle'
        self._bt_round = 1
        self._bt_golem_hp = GOLEM_HP
        for s in self._bt_samurai:
            s['hp'] = s['max']
            s['node'].setPos(s['home'])
        self._bt_log = ['岩石巨怪拦住去路！', '王啊，请下令。']
        self.dialog = True
        self.keys.clear()
        # 战斗期间隐藏常规 HUD，避免与战斗 HUD 重叠、让画面更干净
        self._battle_hidden_hud = []
        for nm in ('top', 'title', 'stats', 'goal', 'economy',
                   'controls_text', 'prompt', 'message'):
            obj = getattr(self, nm, None)
            if obj is not None and not obj.isHidden():
                try:
                    obj.hide(); self._battle_hidden_hud.append(obj)
                except Exception:
                    pass
        decor = getattr(self, '_hp_decor', None)
        if decor is not None and not decor.isHidden():
            try:
                decor.hide(); self._battle_hidden_hud.append(decor)
            except Exception:
                pass
        self._bt_panel.show()
        self._hp_bars.show()
        self._refresh_battle_ui()
        try: self.cue('portal', '战鼓')
        except Exception: pass

    # =============================================================
    # 指令
    # =============================================================
    def _log(self, msg):
        self._bt_log.append(msg)
        self._bt_log = self._bt_log[-4:]

    def _cmd_charge(self):
        if self._bt_phase != 'idle': return
        self._bt_phase = 'charge'; self._bt_t = 0.0
        self._bt_pending = dict(dmg=(14, 22), counter=(5, 9))
        self._log('第 %d 回合：全军冲锋！' % self._bt_round)

    def _cmd_guard(self):
        if self._bt_phase != 'idle': return
        self._bt_phase = 'charge'; self._bt_t = 0.0
        self._bt_pending = dict(dmg=(5, 9), counter=(1, 3))
        self._log('第 %d 回合：结阵坚守。' % self._bt_round)

    def _cmd_rest(self):
        if self._bt_phase != 'idle': return
        self._bt_phase = 'rest'; self._bt_t = 0.0
        self._bt_pending = dict(dmg=(0, 0), counter=(2, 4))
        self._log('第 %d 回合：蓄势休整。' % self._bt_round)

    def _cmd_retreat(self):
        if not self._bt_active: return
        self.end_battle('retreat')

    # =============================================================
    # 每帧动画状态机
    # =============================================================
    def update_battle(self, dt):
        # 打击特效始终推进（战斗结束后残留特效也要淡出）
        self._update_hit_fx(dt)
        if not self._bt_active: return
        self._bt_t += dt
        t = self._bt_t

        if self._bt_phase in ('charge', 'rest'):
            # 阶段1(0~1.2s)：武士跑向巨怪；阶段2(1.2~1.8s)：攻击/蓄势；阶段3(1.8~2.4s)：巨怪反击
            target = Vec3(GOLEM_POS[0], GOLEM_POS[1], 0)
            run = min(1.0, t / 1.2)
            for s in self._bt_samurai:
                if s['hp'] <= 0: continue
                dest = target + s['offset']
                dest.z = self.height(dest.x, dest.y)
                home = s['home']
                pos = home + (dest - home) * run
                if t > 1.8:   # 反击后退回
                    back = min(1.0, (t - 1.8) / 1.0)
                    pos = dest + (home - dest) * back
                s['node'].setPos(pos)
                # 攻击前冲/摇晃表现
                if 1.2 <= t < 1.5 and self._bt_phase == 'charge':
                    s['node'].setY(pos.y - math.sin((t-1.2)/.3*math.pi) * 1.2)
            if t >= 1.3 and not self._bt_pending.get('applied'):
                self._apply_player_action()
                self._bt_pending['applied'] = True
            if t >= 2.0 and not self._bt_pending.get('countered'):
                self._apply_golem_counter()
                self._bt_pending['countered'] = True
            if t >= 2.8:
                self._end_round()
            # 巨怪受击闪红
            if 1.3 <= t < 1.7 and self._bt_golem is not None:
                self._bt_golem.setColor(1, .45, .35, 1)
            elif self._bt_golem is not None:
                self._bt_golem.setColor(1, 1, 1, 1)
        self._refresh_battle_ui()

    def _apply_player_action(self):
        p = self._bt_pending
        alive = [s for s in self._bt_samurai if s['hp'] > 0]
        if self._bt_phase == 'rest':
            for s in alive:
                s['hp'] = min(s['max'], s['hp'] + 10)
            self._log('武士蓄势，恢复 10 点生命。')
            return
        import random
        total = 0
        for s in alive:
            dmg = random.randint(*p['dmg'])
            total += dmg
        self._bt_golem_hp = max(0, self._bt_golem_hp - total)
        # 打击特效：巨怪胸前金色爆闪
        if alive and self._bt_golem is not None:
            try:
                gp = self._bt_golem.getPos()
                self._spawn_hit_fx(Vec3(gp.x, gp.y, gp.z + GOLEM_SCALE * .55),
                                   color=(1.0, .84, .42), scale=1.1)
            except Exception:
                pass
        self._log('%d 名武士命中，造成 %d 点伤害。' % (len(alive), total))
        if self._bt_golem_hp <= 0:
            self.end_battle('win')

    def _apply_golem_counter(self):
        if self._bt_golem_hp <= 0: return
        import random
        p = self._bt_pending
        alive = [s for s in self._bt_samurai if s['hp'] > 0]
        if not alive: return
        victim = random.choice(alive)
        dmg = random.randint(*p['counter'])
        victim['hp'] = max(0, victim['hp'] - dmg)
        # 打击特效：被击武士身上红色爆闪
        try:
            vp = victim['node'].getPos()
            self._spawn_hit_fx(Vec3(vp.x, vp.y, vp.z + 1.2),
                               color=(1.0, .38, .30), scale=.7)
        except Exception:
            pass
        self._log('巨怪反击，%s 受到 %d 点伤害。' % ('武士', dmg))
        if all(s['hp'] <= 0 for s in self._bt_samurai):
            self.end_battle('lose')

    def _end_round(self):
        self._bt_round += 1
        self._bt_phase = 'idle'
        self._bt_t = 0.0
        self._bt_pending = {}
        for s in self._bt_samurai:
            s['node'].setPos(s['home'])

    def _refresh_battle_ui(self):
        try:
            g = self._bt_golem_hp
            self._golem_bar_fill.setScale(max(.001, g / self._bt_golem_max), 1, 1)
            alive = sum(1 for s in self._bt_samurai if s['hp'] > 0)
            hps = ' / '.join(str(s['hp']) for s in self._bt_samurai)
            self._bt_status.setText('巨怪  %d / %d     武士生命  [%s]     回合 %d' % (
                g, self._bt_golem_max, hps, self._bt_round))
            # 只显示最近 1 条日志，保持底部一行、不遮挡画面
            self._bt_log_text.setText(self._bt_log[-1] if self._bt_log else '')
        except Exception:
            pass

    def end_battle(self, result):
        self._bt_active = False
        self._bt_phase = 'idle'
        self._bt_panel.hide()
        self._hp_bars.hide()
        self.dialog = False
        # 恢复战斗前隐藏的常规 HUD
        for obj in getattr(self, '_battle_hidden_hud', []):
            try: obj.show()
            except Exception: pass
        self._battle_hidden_hud = []
        if self._bt_golem is not None:
            self._bt_golem.setColor(1, 1, 1, 1)
        for s in self._bt_samurai:
            s['node'].setPos(s['home'])
        if result == 'win':
            self.state.material += 20
            self.state.jade = True
            self.toast = '巨怪崩解！获得材料 +20，玉石已入手。'; self.toasting = 8
            self._log('胜利！巨怪崩解。')
            # 收起巨怪模型
            if self._bt_golem is not None:
                self._bt_golem.hide()
            try: self.refresh(); self.sync_ui()
            except Exception: pass
        elif result == 'lose':
            lost = min(self.state.population, 2)
            self.state.population -= lost
            self.toast = '武士败退，损失 %d 名族人来年再战。' % lost; self.toasting = 8
            try: self.refresh(); self.sync_ui()
            except Exception: pass
        else:
            self.toast = '已撤退，武士各归其位。'; self.toasting = 5
