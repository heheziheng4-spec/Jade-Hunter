# -*- coding: utf-8 -*-
"""沙光良渚 · 角色对话与剧情系统（数据驱动，引擎无关）

设计目标：
- 每个角色有独特说话风格 / 口头禅 / 性格，与其身份背景一致。
- 多轮对话树：节点根据玩家选择、当前剧情状态、好感度分流。
- 情境化闲聊 + 战斗/探索/日常差异化台词。
- 对话选择影响好感度与剧情旗标，并给出即时反馈。
- 结构化数据，便于按角色 / 场景 / 剧情模块扩展。

接入方式见 dialogue_ui.py；状态源为 rules.Village（游戏主状态）。
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# =====================================================================
# 一、剧情设定 · 世界观与角色关系
# =====================================================================
STORY = {
    "title": "沙光良渚 · 玉光归来",
    "premise": (
        "良渚水城连年旱涝，古礼失传。长者守着将熄的营火，"
        "祭坛刻纹黯淡。玩家作为『寻玉者』，需疏通水渠、安顿人口、"
        "修复堤坝，在第四个雨日赴河滩拾玉，最终以玉与粮重启祭祀。"
    ),
    "main_act": [
        "第一幕 · 火种：与长者交谈，接过疏通水渠之托。",
        "第二幕 · 水与田：疏通水渠、分配农民与手工者、收集材料修堤。",
        "第三幕 · 洪日：第四日洪水考验，检验准备是否充分。",
        "第四幕 · 寻玉：雨后在河滩拾取被冲出的玉器。",
        "第五幕 · 礼成：整修祭坛，献玉献粮，重燃玉光。",
    ],
    "branches": [
        ("仁政线", "多与村民闲聊、优先救济与分粮，提升民心，祭祀时获得额外粮食返还。"),
        ("务实线", "专注水利与材料，快速修堤，洪水损失最小，长者评价更看重效率。"),
        ("礼祀线", "早修祭坛、多问长者礼制细节，解锁隐藏的『古礼问答』对话。"),
    ],
    "relationships": [
        ("长者 ↔ 寻玉者", "师长与传承者。长者知晓祭坛与玉的旧事，好感度高会透露隐藏线索。"),
        ("农夫阿禾 ↔ 长者", "祖孙。阿禾继承了父亲的耕作技艺，长者常念叨他。"),
        ("工匠石乙 ↔ 巫祝", "旧识。曾一同修祭坛，对礼制有分歧，闲聊会流露旧怨。"),
        ("神鹿 ↔ 图腾小怪物", "守护搭档。神鹿引领迷路者，小怪物驱逐觊觎玉石的外人。"),
    ],
}


# =====================================================================
# 二、角色档案：说话风格 / 口头禅 / 性格 / 目标动机
# =====================================================================
@dataclass
class Character:
    key: str
    name: str
    role: str
    personality: str
    speech_style: str
    catchphrases: List[str]
    voice_quirk: str
    motive: str
    affinity: int = 0
    flags: Dict[str, bool] = field(default_factory=dict)


CHARACTERS: Dict[str, Character] = {
    "elder": Character(
        "elder", "长者 · 耄", "聚落长者 / 礼制守护者",
        "沉稳慈悯、话里有话，习惯用古喻今，不轻易表露情绪。",
        "短句、多用比喻，常以『老朽』自称，语气平缓而权威。",
        ["水记得每一道渠。", "玉不自鸣，待人而光。", "慢些，孩子。"],
        "句末常带『……』停顿，爱用『你且看』起头。",
        "在有生之年让玉光重燃，把礼制与治水之道传给下一个寻玉者。",
    ),
    "farmer": Character(
        "farmer", "农夫 · 阿禾", "稻田农人",
        "憨厚乐天、踏实肯干，爱讲庄稼和天气，对社会大事不甚了了。",
        "口语化、句子短，喜欢用农事打比方，语气热情。",
        ["嘿，这苗长得精神！", "要看天色嘞。", "管够，管够！"],
        "句首常带『嘿』『哎呀』，爱重复词『慢慢来慢慢来』。",
        "把稻田种好，让家家有余粮；暗暗仰慕长者，想被认可。",
    ),
    "artisan": Character(
        "artisan", "工匠 · 石乙", "手工者 / 石匠",
        "耿直急躁、认死理，对手艺极自尊，嘴上不饶人但心软。",
        "短促有力，多用祈使句，爱用『哼』『啧』。",
        ["哼，这活儿得这么干！", "石头不会骗人。", "少废话，材料拿来。"],
        "句末常带『！』，几乎不用问句，不耐烦时声音更短。",
        "修好祭坛石构，证明匠人之功不亚于礼制；与巫祝有旧日心结。",
    ),
    "priest": Character(
        "priest", "巫祝 · 云巫", "祭坛巫祝",
        "神秘温柔、言语缥缈，常沉浸在自己的感应里，说话半诗半谜。",
        "长句、意象丰富，多用『听』『感应』『回响』等词。",
        ["听，玉在呼吸。", "风会带来答案。", "刻纹记得所有名字。"],
        "语速缓慢，句中多停顿，喜欢用叠词『远远地』『轻轻地』。",
        "唤醒祭坛刻纹，与玉共鸣；认为礼制重在心意而非器物。",
    ),
    "warrior": Character(
        "warrior", "武士 · 戈", "边防武士",
        "寡言刚毅、警觉，动作先于言语，对陌生人保持戒备。",
        "极简、命令式，常用单词回答，不寒暄。",
        ["站住。", "盯着点。", "有我在。"],
        "句子常只有三五字，几乎不用形容词，情绪藏在停顿里。",
        "守住北境安宁，防止外人觊觎玉石；好感度高才透露防务部署。",
    ),
    "totem": Character(
        "totem", "图腾小怪物 · 玉灵", "神树守护灵 / 群居小怪物",
        "机灵护短、好奇又胆小，成群行动，对玉石有强烈守护本能。",
        "短促尖锐的吱吱声夹杂简单词句，情绪外露，爱重复使用『玉！』。",
        ["玉！我们的！", "吱吱——不准碰！", "朋友？真的是朋友？"],
        "句末爱带『！？』，慌张时叠字『快快快』，高兴时连喊『玉玉玉』。",
        "世代守护神树旁的玉石，驱赶一切觊觎者；认定玩家是朋友后会带路。",
    ),
    "deer": Character(
        "deer", "神鹿 · 白蹄", "林间灵兽 / 引路者",
        "温顺聪慧、通人性，不轻易接近，认定后可作向导。",
        "几乎不说话，以动作与眼神示意；开口时温柔简短。",
        ["……（轻轻点头）", "跟着我。", "（鹿角微光一闪）"],
        "台词多为动作描写括号，话语极轻。",
        "为迷路者引路，守护林中净土；感应玩家心意决定是否同行。",
    ),
    "noble": Character(
        "noble", "贵族 · 玉君", "玉之王（拟人）",
        "雍容自信、略带威严，视玉为权力与秩序的象征，处事从容。",
        "文雅整饬、用词典雅，句子完整，带王者口吻。",
        ["玉者，国之重器。", "你来得正好。", "且看这环如何运转。"],
        "自称『本君』，句末多用『。』，语气平稳不容置疑。",
        "维系玉的秩序与礼法，考验玩家是否配得上执玉之人。",
    ),
}

# 情境台词库：战斗 / 探索 / 日常
CONTEXT_LINES: Dict[str, Dict[str, List[str]]] = {
    "elder": {
        "daily": ["火要添柴，人要添话。你今日可还顺遂？", "老朽在这火边坐了大半辈子，见过三次洪水。"],
        "explore": ["往北是高台，往上走，风会变大。", "河滩的玉，只在雨后现身。切莫空手而归。"],
        "battle": ["退后！让武士先上。", "守住材料，便是守住希望。"],
    },
    "farmer": {
        "daily": ["嘿嘿，今儿个太阳好，苗儿准高兴！", "你要是缺粮，跟我说，我给你留点。"],
        "explore": ["那边石头堆里好像有东西，你去瞧瞧？", "水渠那头我常去，通畅着呢！"],
        "battle": ["哎呀呀！躲、躲到田埂后头去！"],
    },
    "artisan": {
        "daily": ["哼，又来催活？材料够了我自然动手。", "这石头的纹路，我闭着眼都摸得清。"],
        "explore": ["祭坛那块缺了角，你去寻块好石料来。", "别碰我工具！……哦，是你啊。"],
        "battle": ["让开！看我一锤子招呼他！"],
    },
    "priest": {
        "daily": ["听……风里有旧人在低语。", "你身上，有玉的气息，很淡，很远。"],
        "explore": ["石环的方向错了，它会记得天空的。", "玉琮在地底沉睡了千年，轻些唤醒它。"],
        "battle": ["别怕，刻纹会护着你……若你诚心。"],
    },
    "warrior": {
        "daily": ["……没事就退下吧。", "（默默擦拭石矛）"],
        "explore": ["北边安静得反常。跟紧我。", "神树那边有动静，小怪物们躁动。"],
        "battle": ["退后。", "有我在。", "别分心！"],
    },
    "totem": {
        "daily": ["玉玉玉！亮晶晶的！", "吱——你又来啦？这次带吃的没？"],
        "explore": ["神树在那边！小心脚下！", "别、别碰那块玉！它会咬人！（其实不会）"],
        "battle": ["吱吱吱！谁来抢玉！打他打他！"],
    },
    "deer": {
        "daily": ["……（轻轻蹭了蹭你的手）", "（低头，鹿角映出微光）"],
        "explore": ["跟着我。", "（停下脚步，回头望你）"],
        "battle": ["（昂首，鹿角亮起）别怕。"],
    },
    "noble": {
        "daily": ["你来了。本君正想与你说说这玉的来历。", "环有环的规矩，正如城有城的秩序。"],
        "explore": ["玉旋环指向天心，你可知为何？", "去吧，试玉之人。"],
        "battle": ["玉光护体，何惧之有。"],
    },
}


# =====================================================================
# 三、对话树
# =====================================================================
@dataclass
class Option:
    text: str
    next: Optional[str] = None
    affinity: int = 0
    flag: Optional[str] = None
    require: Optional[str] = None
    require_affinity: Optional[int] = None
    reply: Optional[str] = None


@dataclass
class Node:
    speaker: str
    text: str
    options: List[Option]


DIALOGUES: Dict[str, Node] = {}
def _add(nid, speaker, text, options): DIALOGUES[nid] = Node(speaker, text, options)

# ---- 长者：多轮 + 隐藏古礼问答 ----
_add("elder_root", "elder", "你且看这营火，将熄未熄。孩子，你为何而来？", [
    Option("我为治水与礼制而来，愿听您指点。", "elder_wise", affinity=8, flag="learned_purpose",
           reply="长者缓缓点头：『水路即礼路。你懂这个，便已入门。』"),
    Option("我只是想帮聚落渡过洪水。", "elder_kind", affinity=5, flag="kind_heart",
           reply="长者：『心存聚落，便已是寻玉之人。』"),
    Option("玉到底有什么用？能换粮吗？", "elder_blunt", affinity=-3,
           reply="长者眉头微皱：『玉不换粮。玉，换的是人心。』"),
    Option("（沉默，递上一份材料）", "elder_gift", affinity=12, flag="elder_gifted",
           reply="长者接过材料，眼中闪过一丝暖意：『……有心了。』"),
])
_add("elder_wise", "elder", "水记得每一道渠。你若疏通了它，田便会活。祭坛那边……你且先别急。", [
    Option("祭坛的刻纹，藏着什么？", "elder_lore", require_affinity=8,
           reply="长者压低声音：『刻纹记着每一位执玉者的名字。』"),
    Option("我明白了，这就去疏通水渠。", None, affinity=3, reply="长者：『去吧，我守着火。』"),
])
_add("elder_kind", "elder", "慢些，孩子。先与阿禾他们聊聊，聚落不只是一个人的事。", [
    Option("好，我先去认识大家。", None, affinity=4, reply="长者：『嗯，得民心者，方得玉光。』"),
])
_add("elder_blunt", "elder", "哼……也罢。你自会明白。先去水渠看看吧。", [
    Option("（告辞）", None, reply="长者不再言语，只望着营火。"),
])
_add("elder_gift", "elder", "玉不自鸣，待人而光。你这份心意，老朽记下了。", [
    Option("您说的『古礼』，能再讲讲吗？", "elder_lore", require="elder_gifted",
           reply="长者：『祭祀之礼，贵在诚，不在多。』"),
    Option("我去干活了。", None, reply="长者：『去吧，火我看着。』"),
])
_add("elder_lore", "elder", "古礼有三：治水以养民，筑台以通天，献玉以明志。三者缺一，玉光不醒。", [
    Option("我记住了：治水、筑台、献玉。", None, affinity=6, flag="knows_rite",
           reply="长者：『记住便好。礼，终究要有人传承。』"),
])

# ---- 农夫阿禾 ----
_add("farmer_root", "farmer", "嘿！你就是长者说的新来的寻玉者？", [
    Option("是的，我来帮大家。", "farmer_friend", affinity=6, reply="阿禾：『太好了！多个人多份力！』"),
    Option("稻田现在怎么样？", "farmer_field", reply="阿禾：『水渠一通，我这苗儿就能喝饱咯！』"),
    Option("（不理他，转身走开）", None, affinity=-5, reply="阿禾嘟囔：『哼，傲气……』"),
])
_add("farmer_friend", "farmer", "管够，管够！等我稻子收了，第一个给你送粮去！", [
    Option("多谢，你先忙。", None, affinity=3, reply="阿禾：『好嘞！要看天色嘞！』"),
])
_add("farmer_field", "farmer", "你看这苗，绿油油的。可水渠堵了，再这么下去……哎呀呀。", [
    Option("我去疏通水渠。", None, affinity=4, flag="promised_canal",
           reply="阿禾：『真的？嘿，这可太好了！』"),
])

# ---- 工匠石乙 ----
_add("artisan_root", "artisan", "哼，站那么远做什么？又不是老虎。", [
    Option("听说你手艺最好，祭坛就靠你了。", "artisan_pride", affinity=7, reply="石乙：『算你有眼力！』"),
    Option("我需要材料，你能帮吗？", "artisan_mat", reply="石乙：『材料拿来，活儿我包了。』"),
    Option("你脾气可真冲。", None, affinity=-4, reply="石乙：『啧，爱要不要！』"),
])
_add("artisan_pride", "artisan", "那祭坛的石构，我盯了三年了。缺的那块角，我迟早补上。", [
    Option("需要我找石料吗？", None, affinity=5, flag="artisan_helped",
           reply="石乙：『哼……算你识相。北边采石场有好料。』"),
])
_add("artisan_mat", "artisan", "休整的时候，我就能把材料打成器物。你多攒点料来。", [
    Option("明白，我去收集。", None, affinity=2, reply="石乙：『嗯，快去。』"),
])

# ---- 巫祝云巫 ----
_add("priest_root", "priest", "听……风里有旧人在低语。你，也听见了吗？", [
    Option("我听见了，它们在说玉。", "priest_resonance", affinity=9, flag="priest_bond",
           reply="云巫眼中一亮：『你果然……听得见。』"),
    Option("没有，我只听见风。", "priest_calm", affinity=2, reply="云巫：『无妨。听不见的人，也能感应。』"),
])
_add("priest_resonance", "priest", "玉在呼吸。河滩的玉，石环的方向，玉琮的低鸣——它们本是一体。", [
    Option("我要如何感应它们？", "priest_hint", require="priest_bond",
           reply="云巫：『靠近时，静心。光会告诉你答案。』"),
])
_add("priest_calm", "priest", "那就静下心。玉不自鸣，待人而光。", [
    Option("我会试试。", None, affinity=2, reply="云巫：『……嗯，风会带你来。』"),
])
_add("priest_hint", "priest", "石环要朝天，玉琮要归位，旋环要转动。三者各安其位，玉光方能圆满。", [
    Option("我记下了，多谢。", None, affinity=5, flag="knows_jade_trio",
           reply="云巫：『去吧，风会护着你。』"),
])

# ---- 武士戈 ----
_add("warrior_root", "warrior", "站住。什么人。", [
    Option("我是寻玉者，来助聚落。", "warrior_check", affinity=4, reply="武士：（点头）『……知道了。』"),
    Option("让开，我有要事。", None, affinity=-6, reply="武士：『……（握紧石矛）』"),
])
_add("warrior_check", "warrior", "北境最近不太平。神树那边的小怪物躁动不安。", [
    Option("我会留意。有你在，我安心。", None, affinity=8, flag="warrior_trust",
           reply="武士：（别过脸）『……有我在。』"),
])

# ---- 图腾小怪物 ----
_add("totem_root", "totem", "吱！玉！我们的玉！你、你是谁？朋友？", [
    Option("我是朋友，来守护玉石的。", "totem_friend", affinity=10, flag="totem_friend",
           reply="小怪物们吱吱叫着围上来：『朋友！真的是朋友！』"),
    Option("我只是路过。", None, affinity=-2, reply="小怪物：『哼！盯、盯着你！』"),
])
_add("totem_friend", "totem", "朋友好！玉玉玉，亮晶晶！谁抢玉，我们就打谁！", [
    Option("你们做得很好，我去看看神树。", None, affinity=5, reply="小怪物：『吱吱——慢走！』"),
])

# ---- 神鹿 ----
_add("deer_root", "deer", "……（白蹄轻轻踏地，鹿角微光一闪，望向神树方向）", [
    Option("你要为我引路吗？", "deer_lead", affinity=8, flag="deer_guide",
           reply="神鹿（点头，缓步向前）：『跟着我。』"),
    Option("（静静陪伴，摸了摸它）", None, affinity=12, reply="神鹿（轻蹭你的手，鹿角泛起柔光）"),
])
_add("deer_lead", "deer", "跟着我。林间的小家伙们，认得玉的光。", [
    Option("好，我跟着你。", None, affinity=4, reply="神鹿（鹿角微亮，缓步引路）"),
])

# ---- 玉之王 ----
_add("noble_root", "noble", "你来了。本君正想问问：你为何执玉？", [
    Option("为守护聚落，重续礼制。", "noble_worthy", affinity=10, flag="noble_test_pass",
           reply="玉君（颔首）：『善。玉者，国之重器，非为私藏。』"),
    Option("为了力量。", "noble_power", affinity=-5, reply="玉君（目光一冷）：『……那你不配。』"),
])
_add("noble_worthy", "noble", "环有环的规矩。你看这玉旋环——它总会回到天心。人心亦当如此。", [
    Option("我明白了，守序方能守护。", None, affinity=6, flag="jade_worthy",
           reply="玉君：『去吧，执玉之人。玉光会认得你。』"),
])
_add("noble_power", "noble", "哼。器物若只为私欲，便只是一块石头。", [
    Option("……我会重新想想。", None, affinity=3, reply="玉君：『去吧。想清楚了再来。』"),
])


# =====================================================================
# 四、对话引擎
# =====================================================================
class DialogueEngine:
    def __init__(self, state=None):
        self.state = state
        self.affinity: Dict[str, int] = {k: 0 for k in CHARACTERS}
        self.flags: Dict[str, bool] = {}
        self.current: Optional[str] = None
        self.history: List[dict] = []

    def set_state(self, state): self.state = state

    def context_of(self) -> str:
        if getattr(self.state, "ceremony", 0) or getattr(self.state, "in_battle", False):
            return "battle"
        day = getattr(self.state, "day", 0)
        if day >= 3 or not getattr(self.state, "greeted", False): return "explore"
        return "daily"

    def start(self, char_key: str) -> Node:
        root = char_key + "_root"
        if root not in DIALOGUES:
            lines = CONTEXT_LINES.get(char_key, {}).get(self.context_of(), ["……"])
            self.current = None
            return Node(char_key, lines[0], [Option("（结束对话）", None)])
        self.current = root
        return DIALOGUES[root]

    def visible_options(self, node: Node) -> List[Option]:
        out = []
        for o in node.options:
            if o.require and not self.flags.get(o.require): continue
            if o.require_affinity is not None and self.affinity.get(node.speaker, 0) < o.require_affinity: continue
            out.append(o)
        return out

    def choose(self, option: Option) -> Optional[Node]:
        speaker = DIALOGUES[self.current].speaker if self.current in DIALOGUES else None
        if speaker is None and self.current is None: return None
        if option.affinity:
            self.affinity[speaker] = max(0, min(100, self.affinity.get(speaker, 0) + option.affinity))
            if speaker in CHARACTERS: CHARACTERS[speaker].affinity = self.affinity[speaker]
        if option.flag:
            self.flags[option.flag] = True
            if speaker in CHARACTERS: CHARACTERS[speaker].flags[option.flag] = True
            if self.state is not None and hasattr(self.state, option.flag):
                setattr(self.state, option.flag, True)
        self.history.append({"speaker": speaker, "choice": option.text,
                             "affinity": option.affinity, "reply": option.reply})
        if option.next and option.next in DIALOGUES:
            self.current = option.next
            return DIALOGUES[option.next]
        self.current = None
        return None

    def small_talk(self, char_key: str, context: Optional[str] = None) -> str:
        import random
        ctx = context or self.context_of()
        return random.choice(CONTEXT_LINES.get(char_key, {}).get(ctx, ["……"]))

    def affinity_label(self, char_key: str) -> str:
        v = self.affinity.get(char_key, 0)
        if v >= 80: return "知己"
        if v >= 50: return "信任"
        if v >= 25: return "友好"
        if v >= 10: return "认识"
        return "陌生"


ENGINE = DialogueEngine()
