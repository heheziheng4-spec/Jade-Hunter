"""Deterministic gameplay state, independent of rendering and engine."""
from dataclasses import dataclass, field, asdict

@dataclass
class Village:
    day: int = 0
    food: int = 18
    material: int = 4
    population: int = 6
    farmers: int = 4
    canal: bool = False
    greeted: bool = False
    dam: bool = False
    shrine: bool = False
    jade: bool = False
    won: bool = False
    caches: list = field(default_factory=list)
    history: list = field(default_factory=list)

    def forecast(self):
        n = min(self.farmers, self.population)
        grain = n * 2 if self.canal else 0
        if self.day + 1 in (4, 5) and not self.dam:
            grain //= 2
        return grain, self.population, (self.population - n) * 2

    def act(self, key):
        if self.won: return '祭祀已经完成。按 R 重新体验。'
        if self.population <= 0: return '聚落已失去生机。按 R 重新开始。'
        if key == 'elder':
            self.greeted = True
            return '长者：沿青色水渠找到堵塞处，让水重新流入稻田。'
        if key == 'canal':
            if self.canal: return '水渠已经畅通，稻田可以持续产粮。'
            self.canal = True
            return '水渠已疏通。流水进入田地，农人开始耕作。'
        if key == 'farm':
            self.farmers = min(self.population, self.farmers + 1)
            return f'已安排 {self.farmers} 名农民，{self.population-self.farmers} 名手工者。'
        if key == 'workshop':
            self.farmers = max(0, self.farmers - 1)
            return f'已安排 {self.farmers} 名农民，{self.population-self.farmers} 名手工者。'
        if key.startswith('cache'):
            if key in self.caches: return '这里的材料已经收集。工坊仍可在休整时生产材料。'
            self.caches.append(key); self.material += 4
            return '拾取木料与石料：材料 +4。'
        if key == 'dam':
            if self.dam: return '堤坝已修复，聚落将免于本次洪水减产。'
            if self.material < 10: return '修复需要 10 材料。可收集材料堆，或安排手工者后在营火休整。'
            self.material -= 10; self.dam = True
            return '堤坝缺口已封闭。涨水时，水流将被引向外河。'
        if key == 'jade':
            if self.day < 4: return '河滩上的玉石尚未显露。第 4 次休整后再来。'
            if self.jade: return '你已拾取祭祀所需的玉器。'
            self.jade = True
            return '拾得温润玉器。登上高台，将它带到供台。'
        if key == 'altar':
            if not self.shrine:
                if self.material < 12: return '整修祭坛需要 12 材料。'
                self.material -= 12; self.shrine = True
                return '祭坛已整修。洪水过后，携 1 件玉器与 10 粮食再次互动举行祭祀。'
            if self.day < 4: return '雨季尚未到来。先在营火休整，并为洪水做好准备。'
            if not self.jade: return '还缺少玉器。雨后河滩有一道青色微光。'
            if self.food < 10: return '祭祀需要储备 10 粮食。安排农民，在营火休整后再来。'
            self.food -= 10; self.jade = False; self.won = True
            return '玉光苏醒。稻作、水利与礼制，再次连接起这座聚落。'
        if key == 'rest':
            grain, meals, made = self.forecast()
            self.day += 1
            self.food += grain - meals; self.material += made
            lost = 0
            if self.food < 0:
                lost = min(self.population, (-self.food + 1)//2)
                self.food = 0; self.population -= lost; self.farmers = min(self.farmers,self.population)
            record = dict(day=self.day,grain=grain,meals=meals,made=made,food=self.food,population=self.population)
            self.history.append(record)
            msg=f'第 {self.day} 日：收粮 +{grain}，消耗 -{meals}，材料 +{made}。'
            if self.day == 2: msg += ' 河水渐涨：第 4 日洪水来临。'
            if self.day == 4: msg += ' 堤坝挡住了洪水。' if self.dam else ' 洪水漫入稻田，本日与次日产量减半。'
            if lost: msg += f' 缺粮，{lost} 位村民离开聚落。'
            return msg
        raise ValueError(key)

    def objective(self):
        if self.won:return '礼成 · 聚落重获生机'
        if not self.population:return '粮食耗尽 · 按 R 重新开始'
        if not self.greeted:return '与营火旁的长者交谈'
        if not self.canal:return '沿水渠前往稻田 · 疏通堵塞处'
        if self.day < 4 and not self.dam:return '雨季将至 · 收集 10 材料修复堤坝'
        if self.day < 4:return '在营火休整至第 4 日 · 观察粮食收支'
        if not self.jade:return '前往河滩 · 拾取雨水冲出的玉器'
        if not self.shrine:return '登上北侧高台 · 用 12 材料整修祭坛'
        if self.food < 10:return '祭祀尚需 10 粮食 · 恢复生产与储备'
        return '在供台前按 E · 献玉举行祭祀'
