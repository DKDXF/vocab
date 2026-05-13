"""
数据库初始化脚本 —— 建表 + 导入词库数据
运行方式: python init_db.py
"""
from database import get_db, close_db, init_tables

# ==================== 词根词缀数据 ====================
WORD_ROOTS = [
    {"root_text": "spect", "meaning": "看", "description": "表示看、观察，如 inspect(向内看→检查)、respect(回看→尊重)、prospect(向前看→前景)"},
    {"root_text": "dict", "meaning": "说", "description": "表示说、讲，如 predict(预先说→预测)、contradict(反向说→反驳)、dictate(说写→听写)"},
    {"root_text": "duct", "meaning": "引导", "description": "表示引导、带来，如 conduct(共同引导→指挥)、produce(向前引→生产)、reduce(回引→减少)"},
    {"root_text": "gress", "meaning": "走", "description": "表示行走、步，如 progress(向前走→进步)、aggress(走向→侵略)、regress(往回走→倒退)"},
    {"root_text": "ject", "meaning": "投掷", "description": "表示投、掷，如 project(向前投→项目)、reject(回投→拒绝)、inject(向内投→注射)"},
    {"root_text": "port", "meaning": "运送", "description": "表示搬运、运送，如 transport(跨越运→运输)、export(向外运→出口)、import(向内运→进口)"},
    {"root_text": "tract", "meaning": "拉、拖", "description": "表示拉、拖，如 attract(向拉→吸引)、distract(分开拉→分散)、extract(向外拉→提取)"},
    {"root_text": "vene", "meaning": "来", "description": "表示来、到，如 convene(共同来→召集)、intervene(中间来→干预)、prevent(预先来→预防)"},
    {"root_text": "clude", "meaning": "关闭", "description": "表示关闭，如 include(关在内→包含)、exclude(关在外→排除)、conclude(共同关→结论)"},
    {"root_text": "pute", "meaning": "计算、思考", "description": "表示计算、思考，如 compute(共同计算→计算机)、dispute(分散思考→争论)、repute(反复想→名誉)"},
    {"root_text": "scend", "meaning": "攀爬", "description": "表示攀爬，如 ascend(向上爬→上升)、descend(向下爬→下降)、transcend(跨越爬→超越)"},
    {"root_text": "sist", "meaning": "站立", "description": "表示站立，如 assist(站在旁边→帮助)、resist(反站→抵抗)、persist(持续站→坚持)"},
    {"root_text": "tain", "meaning": "保持、握住", "description": "表示保持、握住，如 maintain(保持手→维持)、contain(共同握→包含)、obtain(紧握→获得)"},
    {"root_text": "tribute", "meaning": "给予", "description": "表示给予，如 attribute(给予方向→归因)、contribute(共同给→贡献)、distribute(分散给→分发)"},
    {"root_text": "vert", "meaning": "转", "description": "表示转动，如 convert(共同转→转换)、invert(向内转→倒置)、divert(分开转→转移)"},
    {"root_text": "viv", "meaning": "生命", "description": "表示生命、活，如 survive(超出活→幸存)、revive(再活→复活)、vivid(活的→生动的)"},
    {"root_text": "locut", "meaning": "说话", "description": "表示说话，如 eloquent(说得好→雄辩的)、interlocutor(对话者)"},
    {"root_text": "mit", "meaning": "发送", "description": "表示发送、投递，如 transmit(跨越发送→传输)、submit(下发送→提交)、emit(向外发→发射)"},
    {"root_text": "ced", "meaning": "走、让步", "description": "表示行走、让步，如 precede(预先走→先于)、recede(往回走→后退)、accede(走向→同意)"},
    {"root_text": "flect", "meaning": "弯曲", "description": "表示弯曲，如 reflect(回弯→反射)、flexible(可弯曲→灵活的)、deflect(偏弯→偏转)"},
]

# ==================== 混淆组数据 ====================
# 格式：混淆组ID -> 组描述
CONFUSION_GROUPS = {
    "spect_group": "spect 词根形近词: inspect/expect/respect/aspect/prospect/suspect",
    "dict_group": "dict 词根形近词: predict/contradict/dictate/diction/edict",
    "duct_group": "duct 词根形近词: conduct/product/reduce/deduce/induce",
    "gress_group": "gress 词根形近词: progress/aggress/regress/transgress/digress",
    "sist_group": "sist 词根形近词: assist/resist/persist/insist/consist/exit",
    "tain_group": "tain 词根形近词: maintain/contain/obtain/retain/attain",
    "tribute_group": "tribute 形近词: attribute/contribute/distribute/retribution",
    "vert_group": "vert 形近词: convert/invert/divert/avert/revert",
    "cept_group": "cept 形近词: accept/except/concept/intercept/recept",
    "press_group": "press 形近词: compress/depress/express/impress/oppress/suppress",
    "sume_group": "sume 形近词: assume/consume/presume/resume/subsume",
    "ceive_group": "ceive 形近词: receive/conceive/deceive/perceive/deceit",
    "sure_group": "sure 形近词: assure/ensure/insure/measure/pressure",
    "fect_group": "fect 形近词: affect/effect/infect/perfect/defect",
    "lect_group": "lect 形近词: collect/select/elect/neglect/intellect",
    "port_group": "port 形近词: transport/export/import/support/report",
    "tract_group": "tract 形近词: attract/distract/extract/contract/subtract",
}

# 单词到混淆组的映射
WORD_CONFUSION_MAP = {
    "inspect": "spect_group", "expect": "spect_group", "respect": "spect_group",
    "aspect": "spect_group", "prospect": "spect_group", "suspect": "spect_group",
    "predict": "dict_group", "contradict": "dict_group",
    "conduct": "duct_group", "allocate": "duct_group",
    "progress": "gress_group", "aggressive": "gress_group",
    "assist": "sist_group", "persist": "sist_group", "consist": "sist_group",
    "maintain": "tain_group", "contain": "tain_group", "obtain": "tain_group",
    "attain": "tain_group", "retain": "tain_group",
    "attribute": "tribute_group", "contribute": "tribute_group", "distribute": "tribute_group",
    "convert": "vert_group", "diverse": "vert_group", "alternative": "vert_group",
    "accept": "cept_group", "except": "cept_group", "concept": "cept_group",
    "express": "press_group", "impress": "press_group", "oppress": "press_group",
    "suppress": "press_group", "depress": "press_group", "compress": "press_group",
    "assume": "sume_group", "consume": "sume_group", "presume": "sume_group",
    "resume": "sume_group",
    "receive": "ceive_group", "conceive": "ceive_group", "deceive": "ceive_group",
    "perceive": "ceive_group",
    "assure": "sure_group", "ensure": "sure_group", "insure": "sure_group",
    "assess": "sure_group",
    "affect": "fect_group", "effect": "fect_group", "infect": "fect_group",
    "perfect": "fect_group", "defect": "fect_group",
    "collect": "lect_group", "select": "lect_group", "elect": "lect_group",
    "neglect": "lect_group", "intellect": "lect_group",
    "transport": "port_group", "export": "port_group", "import": "port_group",
    "support": "port_group", "report": "port_group",
    "attract": "tract_group", "distract": "tract_group", "extract": "tract_group",
    "abstract": "tract_group", "contract": "tract_group",
}

# 单词到词根的映射
WORD_ROOT_MAP = {
    "inspect": "spect", "expect": "spect", "respect": "spect",
    "aspect": "spect", "prospect": "spect", "suspect": "spect",
    "predict": "dict", "contradict": "dict",
    "conduct": "duct", "produce": "duct", "reduce": "duct",
    "progress": "gress", "aggressive": "gress",
    "project": "ject", "reject": "ject",
    "transport": "port", "export": "port", "import": "port",
    "support": "port", "report": "port",
    "attract": "tract", "distract": "tract", "extract": "tract",
    "abstract": "tract", "contract": "tract",
    "convene": "vene", "intervene": "vene", "prevent": "vene",
    "include": "clude", "exclude": "clude", "conclude": "clude",
    "ascend": "scend", "transcend": "scend",
    "assist": "sist", "resist": "sist", "persist": "sist", "insist": "sist",
    "maintain": "tain", "contain": "tain", "obtain": "tain",
    "attribute": "tribute", "contribute": "tribute", "distribute": "tribute",
    "convert": "vert", "divert": "vert", "diverse": "vert",
    "survive": "viv", "revive": "viv",
    "transmit": "mit", "submit": "mit", "commit": "mit", "permit": "mit",
    "precede": "ced", "recede": "ced", "accede": "ced",
    "reflect": "flect", "flexible": "flect",
    "articulate": "locut",
    "allocate": "pute", "compute": "pute",
    "discipline": "lect", "collect": "lect", "select": "lect",
    "neglect": "lect",
}

# 常考释义映射
HIGH_FREQ_DEFS = {
    "abandon": "放弃",
    "abstract": "抽象的",
    "academic": "学术的",
    "accomplish": "完成",
    "acknowledge": "承认",
    "acquire": "获得",
    "adequate": "充足的",
    "adjust": "调整",
    "advocate": "提倡",
    "afford": "买得起",
    "aggressive": "侵略的;积极的",
    "allocate": "分配",
    "alter": "改变",
    "alternative": "替代选择",
    "ambiguous": "模糊的",
    "ambitious": "有抱负的",
    "analyze": "分析",
    "annual": "每年的",
    "anticipate": "预期",
    "apparent": "明显的",
    "appreciate": "欣赏;感激",
    "approach": "接近;方法",
    "appropriate": "适当的",
    "approve": "批准",
    "arise": "出现",
    "artificial": "人工的",
    "assess": "评估",
    "assign": "分配",
    "associate": "联系",
    "assume": "假设;承担",
    "assure": "保证",
    "attach": "附加",
    "attempt": "尝试",
    "attribute": "归因于",
    "available": "可用的",
    "abide": "遵守",
    "abolish": "废除",
    "abrupt": "突然的",
    "absurd": "荒谬的",
    "abundance": "丰富",
    "accumulate": "积累",
    "adhere": "坚持",
    "administer": "管理",
    "advent": "出现",
    "adverse": "不利的",
    "affluent": "富裕的",
    "aggravate": "加重",
    "alleviate": "减轻",
    "amplify": "放大",
    "analogy": "类比",
    "anonymous": "匿名的",
    "apparatus": "器械",
    "appeal": "呼吁;上诉",
    "appraise": "评价",
    "articulate": "善于表达的",
    "ascertain": "确定",
    "asset": "资产;优点",
    "assimilate": "同化;吸收",
    "authentic": "真实的",
    "autonomous": "自治的",
    "bias": "偏见",
    "bolster": "支持",
    "bureaucracy": "官僚体制",
    "accommodate": "容纳",
    "adapt": "适应",
    "beneficial": "有益的",
    "budget": "预算",
    "capacity": "容量;能力",
    "certificate": "证书",
    "challenge": "挑战",
    "circumstance": "情况",
    "collaborate": "合作",
    "commence": "开始",
    "compensate": "补偿",
    "confirm": "证实",
    "consequence": "后果",
    "contemporary": "当代的",
    "controversial": "有争议的",
    "convention": "惯例;大会",
    "coordinate": "协调",
    "cornerstone": "基石",
    "cumulative": "累积的",
    "delegate": "委派;代表",
    "deploy": "部署",
    "derive": "源于",
    "devastating": "毁灭性的",
    "diminish": "减少",
    "discipline": "纪律;学科",
    "diverse": "多样的",
    "abate": "减少",
    "abdicate": "退位",
    "acumen": "敏锐",
    "admonish": "告诫",
    "affable": "和蔼的",
    "alacrity": "敏捷",
    "amalgamate": "合并",
    "ameliorate": "改善",
    "anomaly": "异常",
    "apathy": "冷漠",
    "appease": "安抚",
    "arbiter": "仲裁者",
    "arcane": "神秘的",
    "arduous": "艰巨的",
    "ascetic": "苦行的",
    "assiduous": "勤勉的",
    "audacious": "大胆的",
    "auspicious": "吉祥的",
    "avarice": "贪婪",
    "cogent": "令人信服的",
    "contrite": "悔恨的",
}

# ==================== 助记法数据 ====================
WORD_MNEMONICS = {
    "abandon": "a+band+on → 一个乐队在台上演出，但观众都离开了→放弃",
    "abstract": "abs(离开)+tract(拉) → 从具体中拉出来→抽象的",
    "academic": "academ(学院)+ic → 学院的→学术的",
    "accomplish": "ac+compl(完成)+ish → 完成",
    "acknowledge": "ac+knowledge(知识) → 承认知晓→承认",
    "acquire": "ac+quire(寻求) → 不断寻求→获得",
    "adequate": "ad+equ(平等)+ate → 足够平等的→充足的",
    "adjust": "ad+just(正确) → 使正确→调整",
    "advocate": "ad+voc(声音)+ate → 为…发声→提倡",
    "afford": "af+ford(提供) → 能够提供→买得起",
    "aggressive": "ag+gress(走)+ive → 朝前走→侵略的",
    "allocate": "al+loc(地方)+ate → 放到各地方→分配",
    "alter": "alt(其他)+er → 变成其他→改变",
    "alternative": "alter(改变)+native → 可替换的选择",
    "ambiguous": "ambi(两边)+gu(走)+ous → 两边走的→模糊的",
    "ambitious": "ambit(范围)+ious → 想扩大范围→有抱负的",
    "analyze": "ana(分开)+lyze(松开) → 分开解析→分析",
    "annual": "ann(年)+ual → 每年的",
    "anticipate": "anti(前)+cip(抓)+ate → 提前抓住→预期",
    "apparent": "ap+parent(出现) → 出现的→明显的",
    "appreciate": "ap+prec(价格)+iate → 给出价格→欣赏/感激",
    "approach": "ap+proach(靠近) → 接近",
    "appropriate": "ap+propri(适当的)+ate → 适当的",
    "approve": "ap+prove(证明) → 证明可行→批准",
    "arise": "a+rise(升起) → 升起来→出现",
    "artificial": "arti(技巧)+fic(做)+ial → 用技巧做的→人工的",
    "assess": "as+sess(坐) → 坐在旁边评估→评估",
    "assign": "as+sign(标记) → 做标记→分配",
    "associate": "as+soci(同伴)+ate → 与同伴在一起→联系",
    "assume": "as+sume(拿) → 拿到自己这里→假设/承担",
    "assure": "as+sure(确信) → 使确信→保证",
    "attach": "at+tach(钉) → 钉上去→附加",
    "attempt": "at+tempt(尝试) → 尝试",
    "attribute": "at+tribute(给予) → 归因于",
    "available": "a+vail(价值)+able → 有价值的→可用的",
    "abide": "a+bide(等待) → 等待→遵守",
    "abolish": "a+bol(抛)+ish → 抛弃→废除",
    "abrupt": "ab(离开)+rupt(断) → 突然断裂→突然的",
    "absurd": "ab+surd(聋) → 聋了听不见→荒谬的",
    "abundance": "abund(丰富)+ance → 丰富",
    "accumulate": "ac+cumul(堆积)+ate → 堆积→积累",
    "adhere": "ad+her(粘)+e → 粘上去→坚持",
    "administer": "ad+minister(管理) → 管理",
    "advent": "ad+vent(来) → 到来→出现",
    "adverse": "ad+vers(转)+e → 转向不好→不利的",
    "affluent": "af+flu(流)+ent → 钱财流入→富裕的",
    "aggravate": "ag+grav(重)+ate → 加重",
    "alleviate": "al+lev(轻)+iate → 使轻→减轻",
    "amplify": "ampl(大)+ify → 放大",
    "analogy": "ana(按照)+logy(说话) → 按比例说→类比",
    "anonymous": "an+onym(名字)+ous → 没名字的→匿名的",
    "apparatus": "appa(准备)+atus → 准备好的工具→器械",
    "appeal": "ap+peal(呼唤) → 呼唤→呼吁",
    "appraise": "ap+praise(价值) → 评定价值→评价",
    "articulate": "artic(关节)+ulate → 关节灵活→善于表达",
    "ascertain": "as+certain(确定) → 使确定→查明",
    "asset": "as+set(放置) → 放在那有价值的东西→资产",
    "assimilate": "as+simil(相同)+ate → 使相同→同化",
    "authentic": "auth(作者)+entic → 作者亲笔的→真实的",
    "autonomous": "auto(自己)+nom(法律)+ous → 自己立法→自治的",
    "bias": "bi(两)+as → 偏向一边→偏见",
    "bolster": "bolst(支撑)+er → 支撑→支持",
    "bureaucracy": "bureau(局)+cracy(统治) → 局里统治→官僚体制",
    "accommodate": "ac+commod(方便)+ate → 提供方便→容纳",
    "adapt": "ad+apt(适合) → 使适合→适应",
    "beneficial": "bene(好)+fic(做)+ial → 做好事→有益的",
    "budget": "budg(钱包)+et → 钱包的→预算",
    "capacity": "cap(拿)+acity → 能拿多少→容量/能力",
    "certificate": "cert(确定)+ific+ate → 确定身份的纸→证书",
    "challenge": "chall(叫)+enge → 大声叫喊→挑战",
    "circumstance": "circum(周围)+stance(站) → 站在周围的情况→环境",
    "collaborate": "col+labor(劳动)+ate → 共同劳动→合作",
    "commence": "com+mence(开始) → 开始",
    "compensate": "com+pens(衡量)+ate → 衡量补偿→补偿",
    "confirm": "con+firm(坚定) → 使坚定→确认",
    "consequence": "con+sequ(跟随)+ence → 跟随而来的→后果",
    "contemporary": "con+tempor(时间)+ary → 同时代的→当代的",
    "contradict": "contra(反)+dict(说) → 反着说→反驳",
    "controversial": "contro(反)+vers(转)+ial → 反转的→有争议的",
    "convention": "con+vent(来)+ion → 大家都来→大会/惯例",
    "coordinate": "co+ordin(顺序)+ate → 共同排序→协调",
    "cornerstone": "corner(角落)+stone(石头) → 角落的基石→基础",
    "cumulative": "cumul(堆积)+ative → 堆积的→累积的",
    "delegate": "de+leg(送)+ate → 送出去→委派",
    "deploy": "de+ploy(折叠) → 展开部署",
    "derive": "de+riv(河流)+e → 从河流引出→源于",
    "devastating": "de+vast(空旷)+ating → 使成废墟→毁灭性的",
    "diminish": "di+min(小)+ish → 使变小→减少",
    "discipline": "discip(学习)+line(线) → 按线学习→纪律/学科",
    "diverse": "di+vers(转)+e → 转向不同方向→多样的",
    "abate": "a+bate(打) → 打下去→减少",
    "abdicate": "ab+dic(说)+ate → 宣布放弃→退位",
    "acumen": "acu(尖锐)+men → 头脑尖锐→敏锐",
    "admonish": "ad+mon(警告)+ish → 警告→告诫",
    "affable": "af+fabil(说)+le → 好说话的→和蔼的",
    "alacrity": "ala(快)+crity → 快速→敏捷",
    "amalgamate": "a+malgam(融合)+ate → 融合→合并",
    "ameliorate": "a+melior(更好)+ate → 使更好→改善",
    "anomaly": "a+nomaly(规则) → 不规则→异常",
    "apathy": "a+pathy(感情) → 没感情→冷漠",
    "appease": "ap+pease(和平) → 使和平→安抚",
    "arbiter": "arbit(判断)+er → 判断者→仲裁者",
    "arcane": "arc(秘密)+ane → 秘密的→神秘的",
    "arduous": "ard(燃烧)+uous → 像火烧一样→艰巨的",
    "ascetic": "ascet(练习)+ic → 苦练的→苦行的",
    "assiduous": "as+sid(坐)+uous → 一直坐着学→勤勉的",
    "audacious": "aud(大胆)+acious → 大胆的",
    "auspicious": "au+spic(看)+ious → 好兆头→吉祥的",
    "avarice": "avar(贪婪)+ice → 贪婪",
    "cogent": "co+gent(产生) → 能产生说服力的→令人信服的",
    "contrite": "con+trit(摩擦)+e → 内心摩擦→悔恨的",
}

# ==================== 近义词数据 ====================
WORD_SYNONYMS = {
    "abandon": "forsake, desert, relinquish",
    "abstract": "theoretical, conceptual, vague",
    "academic": "scholarly, educational, intellectual",
    "accomplish": "achieve, complete, fulfill",
    "acknowledge": "admit, recognize, confess",
    "acquire": "obtain, gain, attain",
    "adequate": "sufficient, enough, ample",
    "adjust": "adapt, modify, alter",
    "advocate": "support, promote, endorse",
    "afford": "bear, manage, sustain",
    "aggressive": "assertive, forceful, proactive",
    "allocate": "assign, distribute, allot",
    "alter": "change, modify, transform",
    "alternative": "substitute, option, choice",
    "ambiguous": "vague, unclear, equivocal",
    "ambitious": "aspiring, enterprising, driven",
    "analyze": "examine, investigate, study",
    "annual": "yearly, perennial",
    "anticipate": "expect, foresee, predict",
    "apparent": "obvious, evident, clear",
    "appreciate": "value, admire, be grateful",
    "approach": "method, technique, access",
    "appropriate": "suitable, proper, fitting",
    "approve": "endorse, authorize, sanction",
    "arise": "emerge, appear, occur",
    "artificial": "synthetic, man-made, fake",
    "assess": "evaluate, appraise, judge",
    "assign": "allocate, appoint, designate",
    "associate": "connect, link, relate",
    "assume": "presume, suppose, take on",
    "assure": "guarantee, convince, ensure",
    "attach": "fasten, connect, affix",
    "attempt": "try, endeavor, strive",
    "attribute": "ascribe, credit, impute",
    "available": "accessible, obtainable, ready",
    "abolish": "eliminate, eradicate, annul",
    "accumulate": "amass, collect, gather",
    "adhere": "stick, cling, comply",
    "adverse": "unfavorable, harmful, contrary",
    "affluent": "wealthy, prosperous, rich",
    "alleviate": "relieve, ease, mitigate",
    "amplify": "magnify, increase, enhance",
    "appeal": "plead, request, attract",
    "authentic": "genuine, real, legitimate",
    "beneficial": "helpful, advantageous, favorable",
    "collaborate": "cooperate, work together, partner",
    "consequence": "result, outcome, effect",
    "controversial": "debatable, disputed, contentious",
    "coordinate": "harmonize, organize, synchronize",
    "diminish": "decrease, reduce, lessen",
    "diverse": "varied, different, multifaceted",
    "cogent": "convincing, compelling, persuasive",
    "contrite": "remorseful, repentant, penitent",
}

# ==================== 反义词数据 ====================
WORD_ANTONYMS = {
    "abandon": "retain, keep, maintain",
    "abstract": "concrete, specific, definite",
    "adequate": "insufficient, inadequate, deficient",
    "aggressive": "passive, peaceful, mild",
    "ambiguous": "clear, definite, explicit",
    "annual": "irregular, occasional",
    "apparent": "hidden, obscure, unclear",
    "appreciate": "depreciate, undervalue, despise",
    "appropriate": "inappropriate, unsuitable, improper",
    "approve": "reject, disapprove, condemn",
    "artificial": "natural, genuine, authentic",
    "assess": "ignore, neglect, overlook",
    "available": "unavailable, inaccessible",
    "abolish": "establish, create, institute",
    "accumulate": "dissipate, scatter, disperse",
    "adverse": "favorable, beneficial, helpful",
    "affluent": "poor, impoverished, destitute",
    "alleviate": "worsen, aggravate, intensify",
    "amplify": "reduce, diminish, quiet",
    "authentic": "fake, counterfeit, false",
    "beneficial": "harmful, detrimental, adverse",
    "controversial": "uncontroversial, accepted, agreed",
    "diminish": "increase, enlarge, expand",
    "diverse": "uniform, homogeneous, identical",
    "cogent": "weak, unconvincing, implausible",
    "contrite": "unrepentant, unremorseful, defiant",
}

# ==================== 派生词数据 ====================
WORD_DERIVATIVES = {
    "abandon": "abandoned (adj.), abandonment (n.)",
    "abstract": "abstraction (n.), abstractly (adv.)",
    "academic": "academy (n.), academically (adv.)",
    "accomplish": "accomplishment (n.), accomplished (adj.)",
    "acknowledge": "acknowledgment (n.), acknowledged (adj.)",
    "acquire": "acquisition (n.), acquired (adj.)",
    "adequate": "adequately (adv.), adequacy (n.)",
    "adjust": "adjustment (n.), adjustable (adj.)",
    "advocate": "advocacy (n.), advocation (n.)",
    "aggressive": "aggression (n.), aggressively (adv.)",
    "allocate": "allocation (n.), allocator (n.)",
    "alter": "alteration (n.), alternate (adj.)",
    "ambiguous": "ambiguity (n.), ambiguously (adv.)",
    "ambitious": "ambition (n.), ambitiously (adv.)",
    "analyze": "analysis (n.), analytical (adj.)",
    "annual": "annually (adv.), annuity (n.)",
    "apparent": "apparently (adv.), apparency (n.)",
    "appreciate": "appreciation (n.), appreciative (adj.)",
    "approve": "approval (n.), approvingly (adv.)",
    "artificial": "artificiality (n.), artificially (adv.)",
    "assess": "assessment (n.), assessor (n.)",
    "assume": "assumption (n.), assumptive (adj.)",
    "assure": "assurance (n.), assured (adj.)",
    "accumulate": "accumulation (n.), accumulative (adj.)",
    "adverse": "adversity (n.), adversely (adv.)",
    "affluent": "affluence (n.), affluently (adv.)",
    "alleviate": "alleviation (n.), alleviative (adj.)",
    "amplify": "amplification (n.), amplifier (n.)",
    "authentic": "authenticity (n.), authenticate (v.)",
    "beneficial": "benefit (n./v.), beneficiary (n.)",
    "collaborate": "collaboration (n.), collaborator (n.)",
    "controversial": "controversy (n.), controversially (adv.)",
    "diminish": "diminution (n.), diminishing (adj.)",
    "diverse": "diversity (n.), diversify (v.)",
}

# ==================== 词根拆解格式数据 ====================
WORD_NOTES = {
    "abstract": "abs=away\ntract",
    "accomplish": "ac=to\ncompl\nish",
    "acknowledge": "ac=to\nknowledge",
    "acquire": "ac=to\nquire",
    "advocate": "ad=to\nvoc\nate",
    "aggressive": "ag=to\ngress\nive",
    "allocate": "al=to\nloc\nate",
    "anticipate": "anti=before\ncip\nate",
    "appreciate": "ap=to\nprec\niate",
    "approach": "ap=to\nproach",
    "appropriate": "ap=to\npropri\nate",
    "associate": "as=to\nsoci\nate",
    "assume": "as=to\nsume",
    "attribute": "at=to\ntribute",
    "abolish": "ab=away\nol\nish",
    "accumulate": "ac=to\ncumul\nate",
    "adhere": "ad=to\nher\ne",
    "adverse": "ad=to\nvers\ne",
    "affluent": "af=to\nflu\nent",
    "aggravate": "ag=to\ngrav\nate",
    "alleviate": "al=to\nlev\niate",
    "amplify": "ampl\nify",
    "apparatus": "appa\nrat\nus",
    "articulate": "artic\nulate",
    "assimilate": "as=to\nsimil\nate",
    "autonomous": "auto=self\nnom\nous",
    "collaborate": "col=together\nlabor\nate",
    "compensate": "com=together\npens\nate",
    "contradict": "contra=against\ndict",
    "controversial": "contra=against\nvers\nial",
    "convention": "con=together\nvent\nion",
    "coordinate": "co=together\nordin\nate",
    "diminish": "di=apart\nmin\nish",
    "diverse": "di=apart\nvers\ne",
    "inspect": "in=into\nspect",
    "expect": "ex=out\nspect",
    "respect": "re=again\nspect",
    "prospect": "pro=forward\nspect",
    "suspect": "sub=under\nspect",
    "predict": "pre=before\ndict",
    "conduct": "con=together\nduct",
    "produce": "pro=forward\nduct",
    "reduce": "re=back\nduct",
    "progress": "pro=forward\ngress",
    "project": "pro=forward\nject",
    "reject": "re=back\nject",
    "transport": "trans=across\nport",
    "export": "ex=out\nport",
    "import": "im=into\nport",
    "attract": "at=to\ntract",
    "distract": "dis=apart\ntract",
    "extract": "ex=out\ntract",
    "convene": "con=together\nvene",
    "intervene": "inter=between\nvene",
    "prevent": "pre=before\nvent",
    "include": "in=into\nclude",
    "exclude": "ex=out\nclude",
    "conclude": "con=together\nclude",
    "ascend": "a=up\nscend",
    "transcend": "trans=across\nscend",
    "assist": "as=to\nsist",
    "resist": "re=against\nsist",
    "persist": "per=through\nsist",
    "insist": "in=on\nsist",
    "maintain": "main=hand\ntain",
    "contain": "con=together\ntain",
    "obtain": "ob=to\ntain",
    "attribute": "at=to\ntribute",
    "contribute": "con=together\ntribute",
    "distribute": "dis=apart\ntribute",
    "convert": "con=together\nvert",
    "divert": "di=apart\nvert",
    "survive": "sur=beyond\nviv\ne",
    "revive": "re=again\nviv\ne",
    "transmit": "trans=across\nmit",
    "submit": "sub=under\nmit",
    "commit": "com=together\nmit",
    "reflect": "re=back\nflect",
    "precede": "pre=before\ncede",
    "recede": "re=back\ncede",
}

# ==================== 词库数据（从原 vocab-master.html 提取） ====================
WORD_BOOKS = [
    {
        "id": "cet4",
        "name": "CET-4 核心词汇",
        "description": "大学英语四级核心词汇，打好基础",
        "icon": "📘",
        "words": [
            {"word": "abandon", "phonetic": "/əˈbændən/", "pos": "v.", "def": "放弃；抛弃", "ex": "He abandoned his plan to travel abroad.", "exCn": "他放弃了出国旅行的计划。"},
            {"word": "abstract", "phonetic": "/ˈæbstrækt/", "pos": "adj.", "def": "抽象的 n. 摘要", "ex": "The concept is too abstract for children.", "exCn": "这个概念对孩子们来说太抽象了。"},
            {"word": "academic", "phonetic": "/ˌækəˈdemɪk/", "pos": "adj.", "def": "学术的；学院的", "ex": "She has an outstanding academic record.", "exCn": "她有着出色的学术成绩。"},
            {"word": "accomplish", "phonetic": "/əˈkɒmplɪʃ/", "pos": "v.", "def": "完成；实现", "ex": "We accomplished the task ahead of schedule.", "exCn": "我们提前完成了任务。"},
            {"word": "acknowledge", "phonetic": "/əkˈnɒlɪdʒ/", "pos": "v.", "def": "承认；确认", "ex": "He acknowledged his mistake publicly.", "exCn": "他公开承认了自己的错误。"},
            {"word": "acquire", "phonetic": "/əˈkwaɪər/", "pos": "v.", "def": "获得；习得", "ex": "She acquired a taste for classical music.", "exCn": "她培养了对古典音乐的品味。"},
            {"word": "adequate", "phonetic": "/ˈædɪkwət/", "pos": "adj.", "def": "充足的；适当的", "ex": "The food supply is adequate for the winter.", "exCn": "食物供应足够过冬。"},
            {"word": "adjust", "phonetic": "/əˈdʒʌst/", "pos": "v.", "def": "调整；适应", "ex": "You need to adjust to the new environment.", "exCn": "你需要适应新环境。"},
            {"word": "advocate", "phonetic": "/ˈædvəkeɪt/", "pos": "v.", "def": "提倡；主张 n. 提倡者", "ex": "She advocates for equal rights.", "exCn": "她倡导平等权利。"},
            {"word": "afford", "phonetic": "/əˈfɔːrd/", "pos": "v.", "def": "买得起；提供", "ex": "I cannot afford a new car.", "exCn": "我买不起新车。"},
            {"word": "aggressive", "phonetic": "/əˈɡresɪv/", "pos": "adj.", "def": "侵略的；好斗的", "ex": "He took an aggressive approach to sales.", "exCn": "他采取了积极的销售策略。"},
            {"word": "allocate", "phonetic": "/ˈæləkeɪt/", "pos": "v.", "def": "分配；拨出", "ex": "The government allocated funds for education.", "exCn": "政府拨出了教育经费。"},
            {"word": "alter", "phonetic": "/ˈɔːltər/", "pos": "v.", "def": "改变；修改", "ex": "We need to alter our plans.", "exCn": "我们需要修改计划。"},
            {"word": "alternative", "phonetic": "/ɔːlˈtɜːrnətɪv/", "pos": "n.", "def": "替代选择 adj. 替代的", "ex": "Is there an alternative solution?", "exCn": "有没有替代方案？"},
            {"word": "ambiguous", "phonetic": "/æmˈbɪɡjuəs/", "pos": "adj.", "def": "模糊的；含混的", "ex": "His reply was deliberately ambiguous.", "exCn": "他的回答故意含糊其辞。"},
            {"word": "ambitious", "phonetic": "/æmˈbɪʃəs/", "pos": "adj.", "def": "有抱负的；雄心勃勃的", "ex": "She is ambitious and hardworking.", "exCn": "她既有雄心又勤奋。"},
            {"word": "analyze", "phonetic": "/ˈænəlaɪz/", "pos": "v.", "def": "分析；解析", "ex": "We need to analyze the data carefully.", "exCn": "我们需要仔细分析数据。"},
            {"word": "annual", "phonetic": "/ˈænjuəl/", "pos": "adj.", "def": "每年的；年度的", "ex": "The annual report is now available.", "exCn": "年度报告现已发布。"},
            {"word": "anticipate", "phonetic": "/ænˈtɪsɪpeɪt/", "pos": "v.", "def": "预期；期望", "ex": "We anticipate a busy holiday season.", "exCn": "我们预期假期会很忙。"},
            {"word": "apparent", "phonetic": "/əˈpærənt/", "pos": "adj.", "def": "明显的；表面上的", "ex": "It was apparent that she was tired.", "exCn": "很明显她累了。"},
            {"word": "appreciate", "phonetic": "/əˈpriːʃieɪt/", "pos": "v.", "def": "欣赏；感激", "ex": "I really appreciate your help.", "exCn": "我非常感谢你的帮助。"},
            {"word": "approach", "phonetic": "/əˈprəʊtʃ/", "pos": "v.", "def": "接近 n. 方法", "ex": "We need a new approach to this problem.", "exCn": "我们需要用新方法解决这个问题。"},
            {"word": "appropriate", "phonetic": "/əˈprəʊpriət/", "pos": "adj.", "def": "适当的；恰当的", "ex": "This dress is not appropriate for the occasion.", "exCn": "这条裙子不适合这个场合。"},
            {"word": "approve", "phonetic": "/əˈpruːv/", "pos": "v.", "def": "批准；赞成", "ex": "The committee approved the proposal.", "exCn": "委员会批准了这项提案。"},
            {"word": "arise", "phonetic": "/əˈraɪz/", "pos": "v.", "def": "出现；产生", "ex": "New problems may arise during the project.", "exCn": "项目过程中可能出现新问题。"},
            {"word": "artificial", "phonetic": "/ˌɑːrtɪˈfɪʃl/", "pos": "adj.", "def": "人工的；虚假的", "ex": "Artificial intelligence is changing our lives.", "exCn": "人工智能正在改变我们的生活。"},
            {"word": "assess", "phonetic": "/əˈses/", "pos": "v.", "def": "评估；评定", "ex": "We need to assess the risk before investing.", "exCn": "投资前我们需要评估风险。"},
            {"word": "assign", "phonetic": "/əˈsaɪn/", "pos": "v.", "def": "分配；指派", "ex": "The teacher assigned homework to students.", "exCn": "老师给学生布置了作业。"},
            {"word": "associate", "phonetic": "/əˈsəʊʃieɪt/", "pos": "v.", "def": "联系；联想", "ex": "People often associate wealth with happiness.", "exCn": "人们常把财富和幸福联系在一起。"},
            {"word": "assume", "phonetic": "/əˈsjuːm/", "pos": "v.", "def": "假设；承担", "ex": "I assume you have read the report.", "exCn": "我假设你已经读过报告了。"},
            {"word": "assure", "phonetic": "/əˈʃʊər/", "pos": "v.", "def": "保证；使确信", "ex": "I assure you that everything is fine.", "exCn": "我向你保证一切都没问题。"},
            {"word": "attach", "phonetic": "/əˈtætʃ/", "pos": "v.", "def": "附加；连接", "ex": "Please attach your resume to the email.", "exCn": "请将简历附在邮件中。"},
            {"word": "attempt", "phonetic": "/əˈtempt/", "pos": "v.", "def": "尝试；企图", "ex": "He attempted to climb the mountain alone.", "exCn": "他尝试独自攀登那座山。"},
            {"word": "attribute", "phonetic": "/əˈtrɪbjuːt/", "pos": "v.", "def": "归因于 n. 属性", "ex": "She attributes her success to hard work.", "exCn": "她把成功归因于努力工作。"},
            {"word": "available", "phonetic": "/əˈveɪləbl/", "pos": "adj.", "def": "可用的；有空的", "ex": "The room is available next week.", "exCn": "这间房下周可用。"},
        ]
    },
    {
        "id": "cet6",
        "name": "CET-6 核心词汇",
        "description": "大学英语六级核心词汇，进阶提升",
        "icon": "📗",
        "words": [
            {"word": "abide", "phonetic": "/əˈbaɪd/", "pos": "v.", "def": "遵守；忍受", "ex": "You must abide by the rules.", "exCn": "你必须遵守规则。"},
            {"word": "abolish", "phonetic": "/əˈbɒlɪʃ/", "pos": "v.", "def": "废除；废止", "ex": "The government abolished the old tax law.", "exCn": "政府废除了旧税法。"},
            {"word": "abrupt", "phonetic": "/əˈbrʌpt/", "pos": "adj.", "def": "突然的；唐突的", "ex": "The road makes an abrupt turn.", "exCn": "道路突然转弯。"},
            {"word": "absurd", "phonetic": "/əbˈsɜːrd/", "pos": "adj.", "def": "荒谬的；可笑的", "ex": "It would be absurd to blame them.", "exCn": "责怪他们是荒谬的。"},
            {"word": "abundance", "phonetic": "/əˈbʌndəns/", "pos": "n.", "def": "丰富；充裕", "ex": "There is an abundance of natural resources.", "exCn": "这里有丰富的自然资源。"},
            {"word": "accumulate", "phonetic": "/əˈkjuːmjəleɪt/", "pos": "v.", "def": "积累；堆积", "ex": "He accumulated a fortune over the years.", "exCn": "多年来他积累了一笔财富。"},
            {"word": "acquaint", "phonetic": "/əˈkweɪnt/", "pos": "v.", "def": "使熟悉；介绍", "ex": "Let me acquaint you with the new system.", "exCn": "让我给你介绍新系统。"},
            {"word": "adhere", "phonetic": "/ədˈhɪər/", "pos": "v.", "def": "坚持；粘附", "ex": "We must adhere to the original plan.", "exCn": "我们必须坚持原计划。"},
            {"word": "adjacent", "phonetic": "/əˈdʒeɪsnt/", "pos": "adj.", "def": "邻近的；毗连的", "ex": "The hotel is adjacent to the railway station.", "exCn": "酒店紧邻火车站。"},
            {"word": "administer", "phonetic": "/ədˈmɪnɪstər/", "pos": "v.", "def": "管理；执行", "ex": "She administers the project efficiently.", "exCn": "她高效地管理着这个项目。"},
            {"word": "adolescent", "phonetic": "/ˌædəˈlesnt/", "pos": "n.", "def": "青少年 adj. 青春期的", "ex": "Adolescents often face identity issues.", "exCn": "青少年常面临身份认同问题。"},
            {"word": "advent", "phonetic": "/ˈædvent/", "pos": "n.", "def": "出现；到来", "ex": "The advent of the internet changed everything.", "exCn": "互联网的出现改变了一切。"},
            {"word": "adverse", "phonetic": "/ˈædvɜːrs/", "pos": "adj.", "def": "不利的；相反的", "ex": "Adverse weather conditions delayed the flight.", "exCn": "恶劣天气延误了航班。"},
            {"word": "affluent", "phonetic": "/ˈæfluənt/", "pos": "adj.", "def": "富裕的；丰富的", "ex": "They live in an affluent neighborhood.", "exCn": "他们住在富裕的社区。"},
            {"word": "aggravate", "phonetic": "/ˈæɡrəveɪt/", "pos": "v.", "def": "加重；恶化", "ex": "Stress can aggravate the condition.", "exCn": "压力可能加重病情。"},
            {"word": "aggregate", "phonetic": "/ˈæɡrɪɡeɪt/", "pos": "v.", "def": "聚集 adj. 总计的", "ex": "The aggregate cost exceeded the budget.", "exCn": "总费用超过了预算。"},
            {"word": "alienate", "phonetic": "/ˈeɪliəneɪt/", "pos": "v.", "def": "疏远；使疏离", "ex": "His behavior alienated his friends.", "exCn": "他的行为疏远了朋友。"},
            {"word": "alleviate", "phonetic": "/əˈliːvieɪt/", "pos": "v.", "def": "减轻；缓和", "ex": "Medicine can alleviate the pain.", "exCn": "药物可以减轻疼痛。"},
            {"word": "allure", "phonetic": "/əˈlʊər/", "pos": "v.", "def": "引诱 n. 诱惑力", "ex": "The allure of the city attracted many young people.", "exCn": "城市的魅力吸引了许多年轻人。"},
            {"word": "ameliorate", "phonetic": "/əˈmiːliəreɪt/", "pos": "v.", "def": "改善；改进", "ex": "Steps were taken to ameliorate the situation.", "exCn": "采取了措施来改善局势。"},
            {"word": "amplify", "phonetic": "/ˈæmplɪfaɪ/", "pos": "v.", "def": "放大；增强", "ex": "The microphone amplified his voice.", "exCn": "麦克风放大了他的声音。"},
            {"word": "analogy", "phonetic": "/əˈnælədʒi/", "pos": "n.", "def": "类比；类推", "ex": "He drew an analogy between life and a journey.", "exCn": "他把人生比作一段旅程。"},
            {"word": "anonymous", "phonetic": "/əˈnɒnɪməs/", "pos": "adj.", "def": "匿名的；无名的", "ex": "The donor wished to remain anonymous.", "exCn": "捐赠者希望匿名。"},
            {"word": "apparatus", "phonetic": "/ˌæpəˈreɪtəs/", "pos": "n.", "def": "器械；装置", "ex": "The lab is equipped with modern apparatus.", "exCn": "实验室配备了现代化设备。"},
            {"word": "appeal", "phonetic": "/əˈpiːl/", "pos": "v.", "def": "呼吁 n. 上诉", "ex": "The charity appealed for donations.", "exCn": "慈善机构呼吁捐款。"},
            {"word": "appraise", "phonetic": "/əˈpreɪz/", "pos": "v.", "def": "评价；鉴定", "ex": "The manager will appraise your performance.", "exCn": "经理将评估你的表现。"},
            {"word": "articulate", "phonetic": "/ɑːˈtɪkjuleɪt/", "pos": "adj.", "def": "善于表达的 v. 清楚表述", "ex": "She is very articulate in expressing her ideas.", "exCn": "她很善于表达自己的想法。"},
            {"word": "ascertain", "phonetic": "/ˌæsəˈteɪn/", "pos": "v.", "def": "确定；查明", "ex": "We need to ascertain the facts first.", "exCn": "我们需要先查明事实。"},
            {"word": "asset", "phonetic": "/ˈæset/", "pos": "n.", "def": "资产；优点", "ex": "Good health is a great asset.", "exCn": "健康是一笔巨大的财富。"},
            {"word": "assimilate", "phonetic": "/əˈsɪməleɪt/", "pos": "v.", "def": "同化；吸收", "ex": "It takes time to assimilate new information.", "exCn": "吸收新信息需要时间。"},
            {"word": "authentic", "phonetic": "/ɔːˈθentɪk/", "pos": "adj.", "def": "真实的；正宗的", "ex": "This is an authentic Italian restaurant.", "exCn": "这是一家正宗的意大利餐厅。"},
            {"word": "autonomous", "phonetic": "/ɔːˈtɒnəməs/", "pos": "adj.", "def": "自治的；自主的", "ex": "The region is fully autonomous.", "exCn": "该地区完全自治。"},
            {"word": "bias", "phonetic": "/ˈbaɪəs/", "pos": "n.", "def": "偏见；偏心", "ex": "The report showed a clear bias.", "exCn": "报告显示出明显的偏见。"},
            {"word": "bolster", "phonetic": "/ˈbəʊlstər/", "pos": "v.", "def": "支持；增强", "ex": "The evidence bolsters the theory.", "exCn": "这一证据支持了该理论。"},
            {"word": "bureaucracy", "phonetic": "/bjʊˈrɒkrəsi/", "pos": "n.", "def": "官僚体制；官僚主义", "ex": "Excessive bureaucracy slows down progress.", "exCn": "过度的官僚主义阻碍了进步。"},
        ]
    },
    {
        "id": "ielts",
        "name": "雅思核心词汇",
        "description": "IELTS考试高频核心词汇",
        "icon": "📙",
        "words": [
            {"word": "accommodate", "phonetic": "/əˈkɒmədeɪt/", "pos": "v.", "def": "容纳；提供住宿", "ex": "The hotel can accommodate 200 guests.", "exCn": "这家酒店可容纳200位客人。"},
            {"word": "accumulate", "phonetic": "/əˈkjuːmjəleɪt/", "pos": "v.", "def": "积累；积聚", "ex": "Dust tends to accumulate on surfaces.", "exCn": "灰尘容易积聚在表面上。"},
            {"word": "adapt", "phonetic": "/əˈdæpt/", "pos": "v.", "def": "适应；改编", "ex": "Animals adapt to their environment.", "exCn": "动物适应它们的环境。"},
            {"word": "advocate", "phonetic": "/ˈædvəkeɪt/", "pos": "v.", "def": "主张 n. 拥护者", "ex": "Many experts advocate renewable energy.", "exCn": "许多专家主张使用可再生能源。"},
            {"word": "affluent", "phonetic": "/ˈæfluənt/", "pos": "adj.", "def": "富裕的；丰富的", "ex": "Affluent societies face different challenges.", "exCn": "富裕社会面临不同的挑战。"},
            {"word": "alternative", "phonetic": "/ɔːlˈtɜːrnətɪv/", "pos": "n.", "def": "替代方案 adj. 替代的", "ex": "Solar energy is a viable alternative.", "exCn": "太阳能是一种可行的替代方案。"},
            {"word": "anticipate", "phonetic": "/ænˈtɪsɪpeɪt/", "pos": "v.", "def": "预期；预料", "ex": "We anticipate significant changes next year.", "exCn": "我们预计明年会有重大变化。"},
            {"word": "attribute", "phonetic": "/əˈtrɪbjuːt/", "pos": "v.", "def": "归因于 n. 属性", "ex": "He attributes his recovery to exercise.", "exCn": "他把康复归功于锻炼。"},
            {"word": "beneficial", "phonetic": "/ˌbenɪˈfɪʃl/", "pos": "adj.", "def": "有益的；有利的", "ex": "Regular exercise is beneficial to health.", "exCn": "规律的运动对健康有益。"},
            {"word": "budget", "phonetic": "/ˈbʌdʒɪt/", "pos": "n.", "def": "预算 v. 编预算", "ex": "We need to stick to our budget.", "exCn": "我们需要坚持预算。"},
            {"word": "capacity", "phonetic": "/kəˈpæsəti/", "pos": "n.", "def": "容量；能力", "ex": "The stadium has a capacity of 50,000.", "exCn": "体育场可容纳五万人。"},
            {"word": "certificate", "phonetic": "/sərˈtɪfɪkət/", "pos": "n.", "def": "证书；执照", "ex": "You need a medical certificate for this.", "exCn": "你需要一张医疗证明。"},
            {"word": "challenge", "phonetic": "/ˈtʃælɪndʒ/", "pos": "n.", "def": "挑战 v. 质疑", "ex": "Climate change is a global challenge.", "exCn": "气候变化是全球性挑战。"},
            {"word": "circumstance", "phonetic": "/ˈsɜːrkəmstæns/", "pos": "n.", "def": "情况；环境", "ex": "Under no circumstance should you give up.", "exCn": "在任何情况下都不应放弃。"},
            {"word": "collaborate", "phonetic": "/kəˈlæbəreɪt/", "pos": "v.", "def": "合作；协作", "ex": "The two companies decided to collaborate.", "exCn": "两家公司决定合作。"},
            {"word": "commence", "phonetic": "/kəˈmens/", "pos": "v.", "def": "开始；着手", "ex": "The ceremony will commence at noon.", "exCn": "典礼将于中午开始。"},
            {"word": "compensate", "phonetic": "/ˈkɒmpenseɪt/", "pos": "v.", "def": "补偿；赔偿", "ex": "The company will compensate for the loss.", "exCn": "公司将赔偿损失。"},
            {"word": "conceive", "phonetic": "/kənˈsiːv/", "pos": "v.", "def": "构想；想象", "ex": "I cannot conceive of a better solution.", "exCn": "我无法想象更好的解决方案。"},
            {"word": "confirm", "phonetic": "/kənˈfɜːrm/", "pos": "v.", "def": "证实；确认", "ex": "Please confirm your reservation by email.", "exCn": "请通过电子邮件确认预订。"},
            {"word": "consequence", "phonetic": "/ˈkɒnsɪkwəns/", "pos": "n.", "def": "后果；结果", "ex": "Every action has consequences.", "exCn": "每个行为都有后果。"},
            {"word": "contemporary", "phonetic": "/kənˈtemprəri/", "pos": "adj.", "def": "当代的 n. 同代人", "ex": "Contemporary art is often controversial.", "exCn": "当代艺术常常有争议。"},
            {"word": "contradict", "phonetic": "/ˌkɒntrəˈdɪkt/", "pos": "v.", "def": "反驳；矛盾", "ex": "The evidence contradicts his statement.", "exCn": "证据与他的陈述相矛盾。"},
            {"word": "controversial", "phonetic": "/ˌkɒntrəˈvɜːrʃl/", "pos": "adj.", "def": "有争议的", "ex": "The policy remains highly controversial.", "exCn": "这项政策仍然很有争议。"},
            {"word": "convention", "phonetic": "/kənˈvenʃn/", "pos": "n.", "def": "惯例；大会", "ex": "The convention attracted thousands of attendees.", "exCn": "大会吸引了数千名参与者。"},
            {"word": "coordinate", "phonetic": "/kəʊˈɔːdɪneɪt/", "pos": "v.", "def": "协调；配合", "ex": "We need to coordinate our efforts.", "exCn": "我们需要协调行动。"},
            {"word": "cornerstone", "phonetic": "/ˈkɔːrnərstəʊn/", "pos": "n.", "def": "基石；基础", "ex": "Education is the cornerstone of society.", "exCn": "教育是社会的基石。"},
            {"word": "cumulative", "phonetic": "/ˈkjuːmjələtɪv/", "pos": "adj.", "def": "累积的", "ex": "The cumulative effect was significant.", "exCn": "累积效应是显著的。"},
            {"word": "delegate", "phonetic": "/ˈdelɪɡeɪt/", "pos": "v.", "def": "委派 n. 代表", "ex": "A good manager knows how to delegate.", "exCn": "好的管理者知道如何委派任务。"},
            {"word": "demographics", "phonetic": "/ˌdeməˈɡræfɪks/", "pos": "n.", "def": "人口统计资料", "ex": "Demographics influence market trends.", "exCn": "人口统计数据影响市场趋势。"},
            {"word": "deploy", "phonetic": "/dɪˈplɔɪ/", "pos": "v.", "def": "部署；调动", "ex": "The company deployed new technology.", "exCn": "公司部署了新技术。"},
            {"word": "derive", "phonetic": "/dɪˈraɪv/", "pos": "v.", "def": "源于；获得", "ex": "The word derives from Latin.", "exCn": "这个词源于拉丁语。"},
            {"word": "devastating", "phonetic": "/ˈdevəsteɪtɪŋ/", "pos": "adj.", "def": "毁灭性的", "ex": "The earthquake had a devastating impact.", "exCn": "地震造成了毁灭性的影响。"},
            {"word": "diminish", "phonetic": "/dɪˈmɪnɪʃ/", "pos": "v.", "def": "减少；缩小", "ex": "His influence has diminished over time.", "exCn": "他的影响力随时间减弱了。"},
            {"word": "discipline", "phonetic": "/ˈdɪsəplɪn/", "pos": "n.", "def": "纪律；学科", "ex": "Self-discipline is key to success.", "exCn": "自律是成功的关键。"},
            {"word": "diverse", "phonetic": "/daɪˈvɜːrs/", "pos": "adj.", "def": "多样的；不同的", "ex": "The city has a diverse population.", "exCn": "这座城市人口多样化。"},
        ]
    },
    {
        "id": "gre",
        "name": "GRE 核心词汇",
        "description": "GRE考试核心词汇，挑战极限",
        "icon": "📕",
        "words": [
            {"word": "abate", "phonetic": "/əˈbeɪt/", "pos": "v.", "def": "减少；减弱", "ex": "The storm began to abate by evening.", "exCn": "到傍晚暴风雨开始减弱。"},
            {"word": "abdicate", "phonetic": "/ˈæbdɪkeɪt/", "pos": "v.", "def": "退位；放弃", "ex": "The king was forced to abdicate.", "exCn": "国王被迫退位。"},
            {"word": "abjure", "phonetic": "/əbˈdʒʊər/", "pos": "v.", "def": "发誓放弃；郑重拒绝", "ex": "He abjured his former beliefs.", "exCn": "他发誓放弃以前的信仰。"},
            {"word": "abstemious", "phonetic": "/æbˈstiːmiəs/", "pos": "adj.", "def": "有节制的；节俭的", "ex": "He led an abstemious lifestyle.", "exCn": "他过着节制的生活方式。"},
            {"word": "acrimony", "phonetic": "/ˈækrɪməni/", "pos": "n.", "def": "刻毒；激烈", "ex": "The debate ended in acrimony.", "exCn": "辩论以激烈的争吵告终。"},
            {"word": "acumen", "phonetic": "/ˈækjʊmen/", "pos": "n.", "def": "敏锐；精明", "ex": "She showed great business acumen.", "exCn": "她展现了出色的商业敏锐度。"},
            {"word": "admonish", "phonetic": "/ədˈmɒnɪʃ/", "pos": "v.", "def": "告诫；劝告", "ex": "The teacher admonished the student.", "exCn": "老师告诫了这名学生。"},
            {"word": "adulterate", "phonetic": "/əˈdʌltəreɪt/", "pos": "v.", "def": "掺杂；掺假", "ex": "The food was adulterated with chemicals.", "exCn": "食物被掺入了化学物质。"},
            {"word": "affable", "phonetic": "/ˈæfəbl/", "pos": "adj.", "def": "和蔼的；友善的", "ex": "He is an affable and pleasant person.", "exCn": "他是一个和蔼可亲的人。"},
            {"word": "alacrity", "phonetic": "/əˈlækrəti/", "pos": "n.", "def": "敏捷；乐意", "ex": "She accepted the invitation with alacrity.", "exCn": "她欣然接受了邀请。"},
            {"word": "amalgamate", "phonetic": "/əˈmælɡəmeɪt/", "pos": "v.", "def": "合并；融合", "ex": "The two companies amalgamated last year.", "exCn": "两家公司去年合并了。"},
            {"word": "ameliorate", "phonetic": "/əˈmiːliəreɪt/", "pos": "v.", "def": "改善；改进", "ex": "Reforms were introduced to ameliorate conditions.", "exCn": "推行了改革以改善条件。"},
            {"word": "anachronism", "phonetic": "/əˈnækrənɪzəm/", "pos": "n.", "def": "时代错误；过时之物", "ex": "The law is an anachronism in modern society.", "exCn": "这项法律在现代社会已过时。"},
            {"word": "anomaly", "phonetic": "/əˈnɒməli/", "pos": "n.", "def": "异常；反常", "ex": "The data showed several anomalies.", "exCn": "数据显示了几处异常。"},
            {"word": "antipathy", "phonetic": "/ænˈtɪpəθi/", "pos": "n.", "def": "反感；厌恶", "ex": "She felt an antipathy toward dishonesty.", "exCn": "她对不诚实感到厌恶。"},
            {"word": "apathy", "phonetic": "/ˈæpəθi/", "pos": "n.", "def": "冷漠；无动于衷", "ex": "Voter apathy is a serious problem.", "exCn": "选民冷漠是一个严重的问题。"},
            {"word": "appease", "phonetic": "/əˈpiːz/", "pos": "v.", "def": "安抚；平息", "ex": "The government tried to appease the protesters.", "exCn": "政府试图安抚抗议者。"},
            {"word": "approbation", "phonetic": "/ˌæprəˈbeɪʃn/", "pos": "n.", "def": "认可；批准", "ex": "The plan received the committee's approbation.", "exCn": "计划获得了委员会的认可。"},
            {"word": "arbiter", "phonetic": "/ˈɑːrbɪtər/", "pos": "n.", "def": "仲裁者；主宰者", "ex": "Fashion is the arbiter of taste.", "exCn": "时尚是品味的主宰者。"},
            {"word": "arcane", "phonetic": "/ɑːrˈkeɪn/", "pos": "adj.", "def": "神秘的；晦涩的", "ex": "The ritual was shrouded in arcane knowledge.", "exCn": "这个仪式笼罩在神秘的知识中。"},
            {"word": "arduous", "phonetic": "/ˈɑːrdjuəs/", "pos": "adj.", "def": "艰巨的；费力的", "ex": "The journey was long and arduous.", "exCn": "旅途漫长而艰辛。"},
            {"word": "ascetic", "phonetic": "/əˈsetɪk/", "pos": "adj.", "def": "苦行的 n. 苦行者", "ex": "He lived an ascetic life in the mountains.", "exCn": "他在山中过着苦行的生活。"},
            {"word": "assiduous", "phonetic": "/əˈsɪdjuəs/", "pos": "adj.", "def": "勤勉的；刻苦的", "ex": "She was assiduous in her studies.", "exCn": "她在学习上勤勉刻苦。"},
            {"word": "assuage", "phonetic": "/əˈsweɪdʒ/", "pos": "v.", "def": "缓和；减轻", "ex": "Nothing could assuage her grief.", "exCn": "没有什么能减轻她的悲伤。"},
            {"word": "attenuate", "phonetic": "/əˈtenjueɪt/", "pos": "v.", "def": "使变弱；稀释", "ex": "The signal attenuates over distance.", "exCn": "信号随距离而衰减。"},
            {"word": "audacious", "phonetic": "/ɔːˈdeɪʃəs/", "pos": "adj.", "def": "大胆的；鲁莽的", "ex": "The plan was audacious but feasible.", "exCn": "这个计划大胆但可行。"},
            {"word": "auspicious", "phonetic": "/ɔːˈspɪʃəs/", "pos": "adj.", "def": "吉祥的；有前途的", "ex": "It was an auspicious beginning to the year.", "exCn": "这是一年吉祥的开端。"},
            {"word": "avarice", "phonetic": "/ˈævərɪs/", "pos": "n.", "def": "贪婪", "ex": "His avarice led to his downfall.", "exCn": "他的贪婪导致了他的败落。"},
            {"word": "axiom", "phonetic": "/ˈæksiəm/", "pos": "n.", "def": "公理；格言", "ex": "It is an axiom of economics that supply meets demand.", "exCn": "供需相等是经济学的公理。"},
            {"word": "bolster", "phonetic": "/ˈbəʊlstər/", "pos": "v.", "def": "支持；增强", "ex": "New data bolsters the hypothesis.", "exCn": "新数据支持了这一假说。"},
            {"word": "cacophony", "phonetic": "/kəˈkɒfəni/", "pos": "n.", "def": "刺耳的声音；不和谐", "ex": "A cacophony of car horns filled the street.", "exCn": "刺耳的汽车喇叭声充满了街道。"},
            {"word": "caustic", "phonetic": "/ˈkɔːstɪk/", "pos": "adj.", "def": "腐蚀性的；刻薄的", "ex": "His caustic remarks hurt her feelings.", "exCn": "他刻薄的话伤了她的感情。"},
            {"word": "chicanery", "phonetic": "/ʃɪˈkeɪnəri/", "pos": "n.", "def": "诡计；狡辩", "ex": "The politician was known for his chicanery.", "exCn": "这位政客以诡计多端著称。"},
            {"word": "cogent", "phonetic": "/ˈkəʊdʒənt/", "pos": "adj.", "def": "令人信服的", "ex": "She presented a cogent argument.", "exCn": "她提出了令人信服的论点。"},
            {"word": "contrite", "phonetic": "/kənˈtraɪt/", "pos": "adj.", "def": "悔恨的；痛悔的", "ex": "He seemed genuinely contrite about his behavior.", "exCn": "他似乎对自己的行为真心悔过。"},
        ]
    },
]


def seed_data():
    """向数据库中插入词书和单词数据（幂等：已存在则跳过）"""
    conn = get_db()
    try:
        # 1. 插入词根词缀
        root_id_map = {}
        for root in WORD_ROOTS:
            existing = conn.execute(
                "SELECT id FROM word_roots WHERE root_text = ?", (root["root_text"],)
            ).fetchone()
            if existing:
                root_id_map[root["root_text"]] = existing["id"]
            else:
                cursor = conn.execute(
                    "INSERT INTO word_roots (root_text, meaning, description) VALUES (?, ?, ?)",
                    (root["root_text"], root["meaning"], root["description"]),
                )
                root_id_map[root["root_text"]] = cursor.lastrowid
                print(f"  ✅ 插入词根: {root['root_text']} = {root['meaning']}")

        # 2. 插入词书和单词
        for book in WORD_BOOKS:
            existing = conn.execute(
                "SELECT id FROM word_books WHERE id = ?", (book["id"],)
            ).fetchone()
            if existing:
                print(f"  词书 {book['id']} 已存在，跳过")
                # 即使词书已存在，也更新现有单词的 root_id, high_freq_defs, confusion_group
                _update_word_metadata(conn, book)
                continue

            word_count = len(book["words"])
            conn.execute(
                "INSERT INTO word_books (id, name, description, icon, word_count) VALUES (?, ?, ?, ?, ?)",
                (book["id"], book["name"], book["description"], book["icon"], word_count),
            )

            for idx, w in enumerate(book["words"]):
                # 查找词根
                root_id = root_id_map.get(WORD_ROOT_MAP.get(w["word"], ""), None)
                # 查找混淆组
                confusion_group = WORD_CONFUSION_MAP.get(w["word"], "")
                # 常考释义
                high_freq = HIGH_FREQ_DEFS.get(w["word"], "")
                # 助记法
                mnemonic = WORD_MNEMONICS.get(w["word"], "")
                # 近义词/反义词/派生词
                synonym = WORD_SYNONYMS.get(w["word"], "")
                antonym = WORD_ANTONYMS.get(w["word"], "")
                derivative = WORD_DERIVATIVES.get(w["word"], "")
                # 词根拆解格式
                note = WORD_NOTES.get(w["word"], "")

                conn.execute(
                    """INSERT INTO words
                       (book_id, word, phonetic, part_of_speech, definition_cn,
                        example_sentence, example_translation, sort_order, root_id, high_freq_defs, confusion_group,
                        mnemonic, synonym, antonym, derivative, note)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (book["id"], w["word"], w["phonetic"], w["pos"], w["def"],
                     w["ex"], w["exCn"], idx, root_id, high_freq, confusion_group,
                     mnemonic, synonym, antonym, derivative, note),
                )

            print(f"  ✅ 已导入词书: {book['name']} ({word_count} 词)")

        # 3. 初始化默认设置
        _init_settings(conn)
        conn.commit()
    finally:
        close_db(conn)


def _update_word_metadata(conn, book):
    """更新已有单词的 root_id, high_freq_defs, confusion_group, 及新字段"""
    for w_data in book["words"]:
        word = w_data["word"]
        root_text = WORD_ROOT_MAP.get(word, "")
        confusion_group = WORD_CONFUSION_MAP.get(word, "")
        high_freq = HIGH_FREQ_DEFS.get(word, "")
        mnemonic = WORD_MNEMONICS.get(word, "")
        synonym = WORD_SYNONYMS.get(word, "")
        antonym = WORD_ANTONYMS.get(word, "")
        derivative = WORD_DERIVATIVES.get(word, "")
        note = WORD_NOTES.get(word, "")

        # 获取 root_id
        root_id = None
        if root_text:
            row = conn.execute(
                "SELECT id FROM word_roots WHERE root_text = ?", (root_text,)
            ).fetchone()
            if row:
                root_id = row["id"]

        conn.execute(
            """UPDATE words SET root_id = ?, high_freq_defs = ?, confusion_group = ?,
               mnemonic = ?, synonym = ?, antonym = ?, derivative = ?, note = ?
               WHERE word = ?""",
            (root_id, high_freq, confusion_group, mnemonic, synonym, antonym, derivative, note, word),
        )


def _init_settings(conn):
    """初始化默认设置（如果不存在）"""
    defaults = [
        ("daily_new", "10"),
        ("daily_review", "30"),
        ("current_book_id", "cet4"),
        ("daily_new_words_limit", "15"),
        ("llm_api_key", ""),
        ("llm_api_base", "https://api.openai.com/v1"),
        ("llm_model", "gpt-3.5-turbo"),
        ("delay_hours", "4"),
    ]
    for key, value in defaults:
        existing = conn.execute(
            "SELECT key FROM settings WHERE key = ?", (key,)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?)", (key, value)
            )


def main():
    print("🚀 初始化 VocabMaster 数据库...")
    print("=" * 40)

    # 1. 建表
    print("📦 创建数据表...")
    init_tables()
    print("  ✅ 数据表创建完成")

    # 2. 导入词库数据
    print("📚 导入词库数据...")
    seed_data()

    print("=" * 40)
    print("🎉 数据库初始化完成！运行 python main.py 启动服务")


if __name__ == "__main__":
    main()
