# VocabMaster 智能英语单词学习应用 - 详细设计说明书

**版本号**：V1.1  
**编写日期**：2026年5月  
**项目负责人**：[您的姓名]

---

## 1. 引言 (Introduction)

### 1.1 编写目的
本详细设计说明书旨在全面阐述 **VocabMaster** 智能英语单词学习应用的系统设计细节。本文档面向系统开发人员、测试人员及项目维护人员，详细描述系统的架构设计、模块接口、算法逻辑、数据结构及安全策略，为代码实现、系统测试及后续迭代提供完整的技术依据。

### 1.2 项目背景
在英语学习领域，词汇积累是核心难点。传统学习方式存在三大痛点：
1. **遗忘率高**：缺乏科学复习调度，导致“背了忘、忘了背”的低效循环。
2. **语境缺失**：孤立记忆中文释义，无法在阅读写作中灵活运用。
3. **反馈滞后**：学习者无法精准掌握记忆稳定性，缺乏成就感。

本项目基于认知心理学中的**艾宾浩斯遗忘曲线**与**SM-2间隔重复算法**，结合**大语言模型（LLM）**技术，构建了一套科学、高效、智能化的本地化单词学习系统。

### 1.3 适用范围
本文档适用于 VocabMaster V1.1 版本的开发与维护，涵盖后端 API、前端交互、数据库设计及核心算法实现。

### 1.4 参考文献
- SM-2 Algorithm: Piotr Wozniak's SuperMemo research
- Ebbinghaus Forgetting Curve: Hermann Ebbinghaus memory studies
- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLite Documentation: https://www.sqlite.org/docs.html

---

## 2. 总体设计 (System Architecture)

### 2.1 技术栈选型

| 层级 | 技术选型 | 版本 | 选型理由 |
| :--- | :--- | :--- | :--- |
| **后端框架** | Python FastAPI | >=0.100.0 | 高性能异步支持，自动生成 OpenAPI 文档，类型安全 |
| **ASGI 服务器** | Uvicorn | >=0.23.0 | 轻量级高性能 ASGI 服务器，支持热重载 |
| **数据库** | SQLite | 3.x | 零配置、本地化部署、适合个人数据隐私保护 |
| **模板引擎** | Jinja2 | >=3.1.0 | 服务端渲染（SSR），首屏加载速度快 |
| **前端交互** | 原生 JavaScript | ES6+ | 无依赖体积，Fetch API 实现无刷新页面切换 |
| **AI 集成** | OpenAI SDK | >=1.0.0 | 兼容 OpenAI 接口标准，支持自定义 Base URL |
| **文件解析** | openpyxl | >=3.1.0 | 支持 Excel (.xlsx) 文件读取与解析 |
| **网络爬虫** | requests + BeautifulSoup4 | 2.31.0 + 4.12.3 | 轻量级 HTTP 请求与 HTML 解析 |
| **XML/HTML解析** | lxml | 最新版本 | 高性能 XML/HTML 解析器 |

### 2.2 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    表现层 (Presentation Layer)            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ 登录注册  │  │ 学习界面  │  │ 统计图表  │  │ AI 技能  │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│         Jinja2 Templates + Native JavaScript (Fetch)     │
└─────────────────────────────────────────────────────────┘
                            ↓ HTTP/JSON
┌─────────────────────────────────────────────────────────┐
│                   业务逻辑层 (Business Layer)              │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌───────┐ │
│  │ Auth   │ │ Study  │ │ Review │ │ Skills │ │ Stats │ │
│  │ Router │ │ Router │ │ Router │ │ Router │ │Router │ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └───────┘ │
│              FastAPI Routers (Modular Design)             │
└─────────────────────────────────────────────────────────┘
                            ↓ SQLAlchemy-like Queries
┌─────────────────────────────────────────────────────────┐
│                   数据持久层 (Data Layer)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  words   │  │ progress │  │ checkins │  │ records │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│                    SQLite Database                        │
└─────────────────────────────────────────────────────────┘
```

### 2.3 目录结构说明

```
vocab-master/
├── main.py              # 应用入口，注册路由与启动事件，包含认证中间件
├── database.py          # 数据库连接池管理与初始化
├── models.py            # Pydantic 数据模型定义（请求/响应校验）
├── init_db.py           # 数据库初始化脚本（建表、预置数据）
├── crawler.py           # 爬虫核心逻辑（助记法、例句抓取）
├── routers/             # 业务路由模块
│   ├── auth.py          # 用户认证（注册、登录、会话管理）
│   ├── words.py         # 词书管理（导入、查询、切换）
│   ├── study.py         # 学习流程（三轮记忆法、SM-2 算法）
│   ├── review.py        # 复习模块（强干扰项、多模式测试）
│   ├── skills.py        # AI 技能（完形填空、作文优化）
│   ├── stats.py         # 统计分析（记忆率、日历、趋势）
│   ├── checkin.py       # 打卡功能（日历、连续天数）
│   ├── roots.py         # 词根词缀（关联查询、派生词展示）
│   ├── wordreview.py    # 高级复习（昨日重现、标签、笔记）
│   └── crawler.py       # 爬虫 API 接口
├── skills/              # AI 技能实现
│   ├── base.py          # Skill 基类定义
│   ├── ai_cloze/        # 完形填空技能
│   │   ├── skill.py     # 调用 LLM 生成完形填空
│   │   └── prompt.py    # Prompt 模板定义
│   └── ai_writing/      # 作文优化技能
│       ├── skill.py     # 调用 LLM 优化作文
│       └── prompt.py    # Prompt 模板定义
├── static/              # 静态资源（CSS、JS、图片）
├── templates/           # Jinja2 模板文件
└── vocab_master.db      # SQLite 数据库文件
```

---

## 3. 核心模块详细设计 (Module Details)

### 3.1 用户认证模块 (Auth Module)

#### 3.1.1 功能描述
提供用户注册、登录、登出及会话管理功能，确保用户数据安全与访问控制。

#### 3.1.2 密码加密机制
- **算法**：SHA-256 + Salt
- **存储格式**：`salt:hashed_password`（例如：`a3f2b1c4...:e99a18c428cb38d5f260853678922e03`）
- **加密流程**：
  1. 生成 16 字节随机 Salt（十六进制字符串）
  2. 拼接：`salt + password`
  3. 计算 SHA-256 哈希值
  4. 存储时以 `:` 分隔 salt 与 hash

#### 3.1.3 会话管理
- **实现方式**：基于 Cookie 的 Session Token
- **Token 生成**：使用 `secrets.token_urlsafe(32)` 生成 32 字节随机字符串
- **Cookie 属性**：
  - `HttpOnly=True`：防止 XSS 攻击窃取 Cookie
  - `Max-Age=604800`：7 天有效期
  - `SameSite=Lax`：防止 CSRF 攻击

#### 3.1.4 接口定义

**注册接口**
- **路径**：`POST /api/auth/register`
- **请求体**：
```json
{
  "username": "testuser",
  "password": "123456",
  "email": "test@example.com"
}
```
- **验证规则**：
  - 用户名：3-20 字符，唯一性约束
  - 密码：最少 6 字符
  - 邮箱：可选，格式校验
- **返回示例**：
```json
{
  "success": true,
  "message": "注册成功",
  "username": "testuser"
}
```

**登录接口**
- **路径**：`POST /api/auth/login`
- **请求体**：
```json
{
  "username": "testuser",
  "password": "123456"
}
```
- **响应头**：设置 `Set-Cookie: session_token=xxx; HttpOnly; Max-Age=604800`
- **返回示例**：
```json
{
  "success": true,
  "message": "登录成功",
  "user_id": 1,
  "username": "testuser"
}
```

---

### 3.2 三轮记忆法与 SM-2 算法 (Study Module)

#### 3.2.1 状态机流转设计

单词的学习过程被建模为有限状态机（FSM），包含以下状态：

```
[New] --学习--> [Learning] --复习2次--> [Familiar] --验证通过--> [Mastered]
   ^                |                         |                      |
   |                |--验证失败----------------|                      |
   |                |                                                  |
   |------------------质量评分<3--------------------------------------|
```

**状态定义**：
1.  **New (新词)**：尚未开始学习，`stage=1`，`status='new'`
2.  **Learning (学习中)**：已完成初次学习，进入间隔复习，`stage=2`，`status='learning'`
3.  **Familiar (熟悉)**：经过至少 2 次成功复习，`stage=3`，`status='familiar'`
4.  **Mastered (已掌握)**：通过第三轮输出验证，`stage_3_passed=1`，`status='mastered'`

#### 3.2.2 SM-2 算法详细实现

在 `routers/study.py` 中实现的 `sm2()` 函数逻辑如下：

**输入参数**：
- `ease_factor` (float)：当前难易系数，初始值 2.5，范围 [1.3, ∞)
- `interval` (int)：当前复习间隔天数
- `repetitions` (int)：连续正确次数
- `status` (str)：当前状态
- `quality` (int)：用户评分，0-5（0=完全忘记，5=轻松记住）

**算法逻辑**：
```python
def sm2(ease_factor, interval, repetitions, status, quality):
    # 1. 更新连续正确次数与间隔
    if quality >= 3:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * ease_factor)
        repetitions += 1
    else:
        repetitions = 0
        interval = 1
    
    # 2. 更新难易系数
    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if ease_factor < 1.3:
        ease_factor = 1.3
    
    # 3. 计算下次复习日期
    next_review = date.today() + timedelta(days=interval)
    
    # 4. 状态跃迁逻辑
    if status == "new":
        status = "learning"
    elif status == "learning" and quality >= 4 and repetitions >= 3:
        status = "familiar"
    elif status == "familiar" and quality >= 4 and repetitions >= 5:
        status = "mastered"
    if quality <= 1 and status == "mastered":
        status = "familiar"  # 严重遗忘则降级
    if quality == 0 and status == "familiar":
        status = "learning"  # 完全忘记则回到学习阶段
    
    return {
        "ease_factor": round(ease_factor, 2),
        "interval": interval,
        "repetitions": repetitions,
        "next_review_date": next_review.isoformat(),
        "status": status,
    }
```

#### 3.2.3 艾宾浩斯固定节点

在进入 SM-2 动态调整前，系统预设 6 个固定复习节点：

| 复习次序 | 时间间隔 | 说明 |
| :--- | :--- | :--- |
| 1 | 1 天 | 次日复习 |
| 2 | 2 天 | 第三天复习 |
| 3 | 4 天 | 一周内复习 |
| 4 | 7 天 | 周末复习 |
| 5 | 15 天 | 半月复习 |
| 6 | 30 天 | 月度复习 |
| 7+ | SM-2 动态 | 根据掌握度自动调整 |

#### 3.2.4 接口定义

**获取下一个学习单词**
- **路径**：`GET /api/study/next`
- **逻辑**：
  1. 检查今日新词上限（默认 15 个）
  2. 查询 `word_progress` 表中 `status='new'` 的单词
  3. 按 `sort_order` 排序返回第一个
- **返回示例**：
```json
{
  "word": {
    "id": 123,
    "word": "abandon",
    "phonetic": "əˈbændən",
    "definition_cn": "放弃；抛弃",
    "example_sentence": "He abandoned his car in the snow.",
    "root_text": "ban",
    "root_meaning": "禁止"
  },
  "stage": 1,
  "today_new_count": 5,
  "today_review_count": 0
}
```

**提交学习评分**
- **路径**：`POST /api/study/submit`
- **请求体**：
```json
{
  "word_id": 123,
  "rating": 4,
  "action": "study"
}
```
- **处理流程**：
  1. 调用 `sm2()` 算法更新进度
  2. 更新 `word_progress` 表
  3. 插入 `study_records` 日志
  4. 更新 `checkins` 打卡记录
  5. 追加 `history` 二进制序列（'1' 或 '0'）

---

### 3.3 强干扰项生成算法 (Review Module)

#### 3.3.1 干扰项生成策略

为了提升选择题的区分度，系统采用三级干扰项生成策略：

**优先级 1：混淆组优先**
- 查询条件：`confusion_group = target_word.confusion_group`
- 示例：target="adapt"，干扰项=["adopt", "adept"]
- 优势：形近词干扰，测试拼写与辨析能力

**优先级 2：同词书随机抽取**
- 查询条件：`book_id = current_book_id AND id != target_id`
- 过滤规则：排除正确答案，排除已选干扰项
- 补充数量：补足至 3 个干扰项

**优先级 3：全局兜底**
- 当上述两种策略仍不足时，从全库随机抽取
- 确保选项不重复且语义合理

#### 3.3.2 复习模式支持

| 模式 | 说明 | 适用场景 |
| :--- | :--- | :--- |
| **choice** | 四选一释义选择 | 快速复习，测试识别能力 |
| **spelling** | 拼写验证 | 深度掌握，测试输出能力 |
| **listening** | 听音辨意 | 听力训练，测试语音识别 |
| **yesterday-review** | 昨日重现 | 针对过去 4 天内遗忘的单词 |

#### 3.3.3 接口定义

**获取复习队列**
- **路径**：`GET /api/review/queue`
- **逻辑**：
  1. 查询 `next_review_date <= now()` 的单词
  2. 按 `next_review_date ASC` 排序
  3. 限制返回数量（默认 30 个）
- **返回示例**：
```json
[
  {
    "word": {"id": 123, "word": "abandon", ...},
    "progress": {"status": "learning", "stage": 2, ...},
    "options": ["保持", "放弃", "接受", "拒绝"],
    "correct_index": 1
  }
]
```

### 3.6 高级复习模块 (WordReview Module)

#### 3.6.1 功能描述
提供昨日重现、单词标签、用户笔记、熬夜模式、艾宾浩斯日历和双记忆率等高级复习功能，帮助用户更有效地管理学习进度。

#### 3.6.2 昨日重现功能
- **目标**：针对过去4天内遗忘的单词进行强化复习
- **实现**：查询最近4天内标记为遗忘的单词，优先安排复习
- **算法**：基于 `word_progress` 表中的 `history` 字段，筛选出包含 '0'（失败记录）或 `flag = -1`（重难词）的单词
- **接口**：`GET /api/review/yesterday-review`

#### 3.6.3 单词标签系统
- **标签类型**：
  - `-1`: 重难词
  - `0`: 默认
  - `1`: 已掌握
  - `2`: 很熟悉
  - `10`: 太简单
- **存储**：在 `word_progress` 表的 `flag` 字段中存储
- **应用**：用户可根据标签筛选单词，针对性复习
- **接口**：
  - `POST /api/words/{word_id}/flag` - 设置单词标签
  - `GET /api/words/flag-stats` - 获取标签统计

#### 3.6.4 用户笔记功能
- **存储**：在 `word_progress` 表的 `user_note` 字段中存储
- **长度限制**：最大500字符
- **用途**：用户可为每个单词添加个性化学习笔记
- **接口**：`POST /api/words/{word_id}/note`

#### 3.6.5 记忆历史追踪
- **存储格式**：二进制序列字符串，如 "1101101"
- **含义**：'1' 表示成功复习，'0' 表示失败复习
- **用途**：计算历史记忆率和近期记忆率
- **更新逻辑**：每次复习后追加 '1' 或 '0'，保留最近50次记录
- **接口**：`GET /api/words/memory-rates`

#### 3.6.6 熬夜模式
- **功能**：支持延迟打卡时间，避免深夜学习断签
- **配置**：可设置延迟小时数（0-12小时，默认4小时）
- **逻辑**：在延迟小时数之前的学习计入前一天
- **接口**：
  - `GET /api/settings/delay-hours` - 获取延迟小时数
  - `POST /api/settings/delay-hours` - 设置延迟小时数

#### 3.6.7 艾宾浩斯复习日历
- **功能**：展示指定月份的复习计划日历
- **数据源**：基于 `word_progress` 表中的 `next_review_date` 字段
- **显示内容**：每日计划复习的词书名称和单词数量
- **额外标记**：标记实际进行复习的日期（自愿额外复习）
- **接口**：`GET /api/review/calendar`

---

### 3.4 智能爬虫引擎 (Crawler Module)

#### 3.4.1 多源聚合策略
系统采用三级数据抓取策略，确保数据的丰富性与准确性：
1. **助记网 (Mnemonic Dictionary)**：优先抓取用户提交的趣味联想故事。
2. **海词词典 (Dict.cn)**：抓取简短释义与经典双语例句。
3. **词根网 (Wordsand)**：作为 Fallback，当无趣味助记时提供词根拆解分析。

#### 3.4.2 性能优化设计
- **解析器升级**：从 `html.parser` 升级为 `lxml`，显著提升对不规范 HTML 的容错率。
- **智能缓存**：后端在爬取前校验数据库，若已有完整数据则直接返回（毫秒级）。
- **异步预加载**：前端在进入学习页时，后台静默抓取今日词汇，实现“零等待”体验。

---

### 3.5 AI 技能集成 (Skills Module)

#### 3.5.1 AI 完形填空生成流程

1. **单词提取**：从 `study_records` 中提取今日学习的 10 个单词
2. **Prompt 构造**：
```
请基于以下单词生成一篇英文短文（约 150 词），并将这些单词挖空：
单词列表：[{"word": "abandon", "definition": "放弃"}, ...]

要求：
1. 文章主题连贯，语境自然
2. 每个目标单词出现一次并标记为 {{blank_N}}
3. 为每个空白提供 4 个选项（1 正确 + 3 干扰）
4. 返回 JSON 格式：{"article": "...", "blanks": [{"index": 0, "answer": "abandon", "options": [...], "explanation": "..."}], "translation": "..."}
```
3. **LLM 调用**：通过 OpenAI SDK 发送请求
4. **结果解析**：验证 JSON 结构，提取 blanks 与 translation
5. **前端渲染**：将文章中的 `{{blank_N}}` 替换为下拉选择框

#### 3.5.2 AI 作文优化多模态支持

**文本模式**：直接接收用户输入的英文作文
**图片模式**：
1. 前端将图片转为 Base64 编码
2. 后端接收后调用支持视觉的 LLM（如 GPT-4 Vision）
3. Prompt："请识别图片中的英文文本并优化"
**文件模式**：
1. 支持 `.txt` 和 `.docx` 格式
2. 使用 `python-docx` 库解析 Docx 文件段落
3. 提取纯文本后送入 LLM 优化

**优化维度**：
- **语法纠正**：时态、主谓一致、冠词使用
- **用词升级**：替换基础词汇为高级词汇（如 good → excellent）
- **句式改进**：简单句合并为复合句，增加从句使用
- **综合评分**：基于 CEFR 标准给出 0-100 分评分

#### 3.5.3 接口定义

**生成完形填空**
- **路径**：`POST /api/skills/cloze/generate`
- **请求体**：
```json
{
  "word_ids": [123, 124, 125]
}
```
- **返回示例**：
```json
{
  "article": "Yesterday, I decided to {{blank_0}} my old habits...",
  "blanks": [
    {
      "index": 0,
      "answer": "abandon",
      "options": ["keep", "abandon", "accept", "continue"],
      "explanation": "abandon 意为'放弃'，符合语境"
    }
  ],
  "translation": "昨天，我决定放弃我的旧习惯..."
}
```

**作文优化**
- **路径**：`POST /api/skills/writing/optimize`
- **请求体（multipart/form-data）**：
  - `mode`: "text" / "image" / "file"
  - `text`: 作文文本（mode=text 时必填）
  - `image`: 图片文件（mode=image 时必填）
  - `file`: 文档文件（mode=file 时必填）
- **返回示例**：
```json
{
  "original": "I think this book is very good.",
  "optimized": "I believe this book is exceptionally remarkable.",
  "feedback": "建议将 'think' 升级为 'believe'，'very good' 替换为 'exceptionally remarkable' 以提升表达力度。",
  "score": 75,
  "corrections": [
    {"original": "think", "suggested": "believe", "reason": "更正式的表达"}
  ]
}
```

---

## 4. 数据库设计 (Database Design)

### 4.1 数据库 ER 图

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│  word_books  │1     *│     words        │1     *│word_progress │
├──────────────┤───────├──────────────────┤───────├──────────────┤
│ id (PK)      │       │ id (PK)          │       │ id (PK)      │
│ name         │       │ book_id (FK)     │       │ word_id (FK) │
│ description  │       │ word             │       │ status       │
│ icon         │       │ phonetic         │       │ ease_factor  │
│ word_count   │       │ definition_cn    │       │ interval     │
└──────────────┘       │ example_sentence │       │ repetitions  │
                       │ root_id (FK)     │       │ next_review  │
┌──────────────┐1     *├──────────────────┤       │ stage        │
│  word_roots  │───────│ high_freq_defs   │       │ history      │
├──────────────┤       │ confusion_group  │       └──────────────┘
│ id (PK)      │       │ sort_order       │                *
│ root_text    │       └──────────────────┘                │
│ meaning      │                                           │
└──────────────┘                                           │
                                                           │
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│   checkins   │       │ study_records    │       │users         │
├──────────────┤       ├──────────────────┤       ├──────────────┤
│ id (PK)      │       │ id (PK)          │       │ id (PK)      │
│ checkin_date │       │ word_id (FK)     │       │ username     │
│ words_learned│       │ action           │       │ password_hash│
│ words_reviewd│       │ rating           │       │ email        │
│ checked      │       │ created_at       │       │ created_at   │
└──────────────┘       └──────────────────┘       └──────────────┘
```

### 4.2 核心表结构详解

#### 4.2.1 words（单词表）

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 单词唯一标识 |
| book_id | TEXT | NOT NULL, FOREIGN KEY | 所属词书 ID |
| word | TEXT | NOT NULL | 单词拼写 |
| phonetic | TEXT | DEFAULT '' | 音标 |
| part_of_speech | TEXT | DEFAULT '' | 词性 |
| definition_cn | TEXT | DEFAULT '' | 中文释义 |
| example_sentence | TEXT | DEFAULT '' | 英文例句 |
| example_translation | TEXT | DEFAULT '' | 例句翻译 |
| root_id | INTEGER | FOREIGN KEY | 关联词根 ID |
| high_freq_defs | TEXT | DEFAULT '' | 常考释义 |
| confusion_group | TEXT | DEFAULT '' | 混淆组标识 |
| mnemonic | TEXT | DEFAULT '' | 助记法 |
| sort_order | INTEGER | DEFAULT 0 | 排序序号 |

**索引**：
- `idx_words_book_id`: 加速按词书查询
- `idx_words_word`: 加速单词搜索

#### 4.2.2 word_progress（学习进度表）

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 进度记录 ID |
| word_id | INTEGER | NOT NULL, UNIQUE, FOREIGN KEY | 关联单词 ID |
| status | TEXT | DEFAULT 'new' | 状态：new/learning/familiar/mastered |
| ease_factor | REAL | DEFAULT 2.5 | SM-2 难易系数 |
| interval | INTEGER | DEFAULT 0 | 当前间隔天数 |
| repetitions | INTEGER | DEFAULT 0 | 连续正确次数 |
| next_review_date | TEXT | NOT NULL | 下次复习日期（ISO 格式） |
| last_reviewed_at | TEXT | DEFAULT '' | 最后复习时间 |
| learn_date | TEXT | DEFAULT '' | 初次学习日期 |
| stage | INTEGER | DEFAULT 1 | 学习阶段：1/2/3 |
| review_step | INTEGER | DEFAULT 0 | 复习步骤（1-6 为艾宾浩斯节点） |
| stage_1_done_at | TEXT | DEFAULT '' | 第一阶段完成时间 |
| stage_2_pass_count | INTEGER | DEFAULT 0 | 第二阶段通过次数 |
| stage_3_attempts | INTEGER | DEFAULT 0 | 第三轮尝试次数 |
| stage_3_passed | INTEGER | DEFAULT 0 | 第三轮是否通过（0/1） |
| history | TEXT | DEFAULT '' | 复习历史二进制序列（如 "11011"） |
| flag | INTEGER | DEFAULT 0 | 标签：-1重难/0默认/1掌握/2熟悉/10简单 |
| user_note | TEXT | DEFAULT '' | 用户笔记 |

**索引**：
- `idx_progress_next_review`: 加速复习队列查询（最关键索引）
- `idx_progress_status`: 加速按状态筛选
- `idx_progress_stage`: 加速按阶段筛选

#### 4.2.3 checkins（打卡表）

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 打卡记录 ID |
| checkin_date | TEXT | NOT NULL, UNIQUE | 打卡日期（ISO 格式） |
| words_learned | INTEGER | DEFAULT 0 | 今日新学单词数 |
| words_reviewed | INTEGER | DEFAULT 0 | 今日复习单词数 |
| checked | INTEGER | DEFAULT 0 | 是否手动打卡（0/1） |

**索引**：
- `idx_checkins_date`: 加速日期查询

#### 4.2.4 study_records（学习日志表）

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 日志 ID |
| word_id | INTEGER | NOT NULL, FOREIGN KEY | 关联单词 ID |
| action | TEXT | NOT NULL | 操作类型：study/review |
| rating | INTEGER | NOT NULL | 评分（0-5） |
| created_at | TEXT | NOT NULL | 操作时间（ISO 格式） |

**索引**：
- `idx_records_word_id`: 加速单词历史查询
- `idx_records_created_at`: 加速时间范围查询

#### 4.2.5 users（用户表）

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 用户 ID |
| username | TEXT | NOT NULL, UNIQUE | 用户名 |
| password_hash | TEXT | NOT NULL | 密码哈希（salt:hash） |
| email | TEXT | DEFAULT '' | 邮箱 |
| created_at | TEXT | NOT NULL | 注册时间 |
| last_login | TEXT | DEFAULT '' | 最后登录时间 |

### 4.3 关键字段设计说明

#### 4.3.1 history 字段（二进制序列压缩存储）

**设计目的**：高效记录单词的复习历史，用于计算记忆率。

**存储格式**：字符串，由 '0' 和 '1' 组成，例如 `"1101101"`
- `'1'`：表示该次复习成功（rating >= 3）
- `'0'`：表示该次复习失败（rating < 3）

**更新逻辑**：
```python
history = existing_progress["history"] + ('1' if rating >= 3 else '0')
if len(history) > 50:
    history = history[-50:]  # 只保留最近 50 次记录
```

**应用场景**：
- **历史记忆率**：`1 - (history.count('0') / len(history))`
- **近期记忆率**：取最后 2 位计算，反映最近学习状态

#### 4.3.2 next_review_date 字段（索引优化）

**设计目的**：快速筛选出当前需要复习的单词。

**查询示例**：
```sql
SELECT * FROM words w
JOIN word_progress wp ON wp.word_id = w.id
WHERE wp.next_review_date <= datetime('now')
ORDER BY wp.next_review_date ASC
LIMIT 30;
```

**性能优化**：
- 在 `next_review_date` 上建立 B-Tree 索引
- 查询复杂度从 O(n) 降至 O(log n)
- 实测在 5000 条记录中查询耗时 < 5ms

#### 4.3.3 confusion_group 字段（强干扰项支持）

**设计目的**：标记易混淆单词组，用于生成高质量选择题干扰项。

**示例数据**：
| word | confusion_group | 说明 |
| :--- | :--- | :--- |
| adapt | adapt_adopt | 适应 vs 采用 |
| adopt | adapt_adopt | 采用 vs 适应 |
| affect | affect_effect | 影响（动） vs 影响（名） |
| effect | affect_effect | 影响（名） vs 影响（动） |

---

## 5. 接口设计规范 (API Design Standards)

### 5.1 RESTful 规范

- **资源命名**：使用名词复数形式，如 `/api/books`, `/api/words`
- **HTTP 方法**：
  - `GET`：查询资源
  - `POST`：创建资源或执行操作
  - `PUT`：全量更新资源
  - `PATCH`：部分更新资源
  - `DELETE`：删除资源
- **响应格式**：统一返回 JSON，包含 `success`, `message`, `data` 字段

### 5.2 错误码定义

| HTTP 状态码 | 说明 | 示例场景 |
| :--- | :--- | :--- |
| 200 | 请求成功 | 正常返回数据 |
| 400 | 请求参数错误 | 缺少必填字段、格式不正确 |
| 401 | 未授权 | 未登录或 Token 失效 |
| 404 | 资源不存在 | 单词 ID 不存在 |
| 409 | 冲突 | 用户名已存在 |
| 500 | 服务器内部错误 | 数据库异常、AI 接口超时 |

### 5.3 核心接口清单

#### 5.3.1 认证模块

| 方法 | 路径 | 说明 | 认证要求 |
| :--- | :--- | :--- | :--- |
| POST | `/api/auth/register` | 用户注册 | 无 |
| POST | `/api/auth/login` | 用户登录 | 无 |
| POST | `/api/auth/logout` | 用户登出 | 需要 Session |
| GET | `/api/auth/me` | 获取当前用户信息 | 需要 Session |

#### 5.3.2 学习模块

| 方法 | 路径 | 说明 | 认证要求 |
| :--- | :--- | :--- | :--- |
| GET | `/api/study/next` | 获取下一个新词 | 需要 Session |
| GET | `/api/study/review-next` | 获取下一个复习词 | 需要 Session |
| POST | `/api/study/submit` | 提交学习评分 | 需要 Session |
| GET | `/api/study/today` | 获取今日任务概览 | 需要 Session |

#### 5.3.3 复习模块

| 方法 | 路径 | 说明 | 认证要求 |
| :--- | :--- | :--- | :--- |
| GET | `/api/review/next` | 获取下一个待复习词 | 需要 Session |
| GET | `/api/review/queue` | 获取复习队列 | 需要 Session |
| GET | `/api/review/mode/{mode}` | 按模式获取复习内容 | 需要 Session |
| POST | `/api/review/submit` | 提交复习结果 | 需要 Session |

#### 5.3.4 AI 技能模块

| 方法 | 路径 | 说明 | 认证要求 |
| :--- | :--- | :--- | :--- |
| POST | `/api/skills/cloze/generate` | 生成完形填空 | 需要 Session |
| POST | `/api/skills/cloze/submit` | 提交完形填空答案 | 需要 Session |
| POST | `/api/skills/writing/optimize` | 作文优化 | 需要 Session |
| GET | `/api/skills/writing/history` | 获取作文优化历史 | 需要 Session |

#### 5.3.5 统计模块

| 方法 | 路径 | 说明 | 认证要求 |
| :--- | :--- | :--- | :--- |
| GET | `/api/stats/overview` | 总览统计 | 需要 Session |
| GET | `/api/stats/mastery` | 掌握度分布 | 需要 Session |
| GET | `/api/stats/weekly` | 近 7 日学习数据 | 需要 Session |
| GET | `/api/review/calendar` | 艾宾浩斯复习日历 | 需要 Session |

#### 5.3.6 高级复习模块

| 方法 | 路径 | 说明 | 认证要求 |
| :--- | :--- | :--- | :--- |
| GET | `/api/review/yesterday-review` | 获取昨日重现单词 | 需要 Session |
| POST | `/api/words/{word_id}/flag` | 更新单词标签 | 需要 Session |
| GET | `/api/words/flag-stats` | 获取标签统计 | 需要 Session |
| POST | `/api/words/{word_id}/note` | 更新用户笔记 | 需要 Session |
| GET | `/api/settings/delay-hours` | 获取熬夜模式设置 | 需要 Session |
| POST | `/api/settings/delay-hours` | 设置熬夜模式延迟小时数 | 需要 Session |
| GET | `/api/review/calendar` | 艾宾浩斯复习日历 | 需要 Session |
| GET | `/api/words/memory-rates` | 获取双记忆率指标 | 需要 Session |

---

## 6. 安全与性能设计 (Security & Performance)

### 6.1 安全性设计

#### 6.1.1 认证拦截机制
- **中间件鉴权**：在 `main.py` 中实现 `AuthMiddleware`，对所有 `/api/` 路径进行 Session Token 校验。
- **页面重定向**：主页路由增加数据库有效性检查，未登录或 Token 过期自动重定向至 `/login`。
- **前端自动跳转**：封装的 `api()` 函数监听 401 状态码，触发时强制跳转登录页。

#### 6.1.2 密码安全
- **加密算法**：SHA-256 + Salt
- **Salt 生成**：使用 `secrets.token_hex(16)` 生成 16 字节随机盐值
- **防彩虹表攻击**：每个用户使用独立 Salt，即使密码相同，哈希值也不同
- **示例**：
  ```python
  salt = secrets.token_hex(16)  # 例如: "a3f2b1c4d5e6f7a8b9c0d1e2f3a4b5c6"
  hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
  stored_value = f"{salt}:{hashed}"
  ```

#### 6.1.3 会话安全
- **Token 生成**：`secrets.token_urlsafe(32)` 生成 32 字节随机字符串
- **Cookie 属性**：
  - `HttpOnly=True`：JavaScript 无法访问，防止 XSS 攻击
  - `SameSite=Lax`：防止 CSRF 攻击
  - `Max-Age=604800`：7 天自动过期
- **会话验证**：每次请求检查 Cookie 中的 `session_token`，无效则返回 401

#### 6.1.4 SQL 注入防护
- **参数化查询**：所有 SQL 语句使用占位符 `?`，禁止字符串拼接
- **示例**：
  ```python
  # 正确做法
  conn.execute("SELECT * FROM words WHERE id = ?", (word_id,))
  
  # 错误做法（禁止）
  conn.execute(f"SELECT * FROM words WHERE id = {word_id}")
  ```

#### 6.1.5 文件上传安全
- **格式校验**：仅允许 `.xlsx`, `.xls`, `.csv` 格式
- **大小限制**：单文件不超过 10MB
- **文件名 sanitization**：移除特殊字符，防止路径遍历攻击

### 6.2 性能优化

#### 6.2.1 爬虫加速策略
- **智能缓存 (Smart Caching)**：后端优先返回数据库已有数据，避免重复网络请求。
- **后台预加载 (Preloading)**：前端进入学习页时异步抓取今日词汇，实现“秒开”体验。
- **解析器升级**：采用 `lxml` 替代原生解析器，提升 HTML 解析速度与容错率。

#### 6.2.2 数据库索引优化

| 表名 | 索引字段 | 查询场景 | 性能提升 |
| :--- | :--- | :--- | :--- |
| word_progress | next_review_date | 复习队列查询 | 10x |
| word_progress | status | 按状态筛选 | 5x |
| words | book_id | 词书单词查询 | 8x |
| study_records | word_id | 单词历史查询 | 6x |
| checkins | checkin_date | 打卡日历查询 | 12x |

#### 6.2.3 事务管理

**应用场景**：学习进度更新涉及多表操作，需保证原子性。

**示例**：
```python
conn = get_db()
try:
    # 1. 更新 word_progress
    conn.execute("UPDATE word_progress SET ... WHERE word_id = ?", (word_id,))
    
    # 2. 插入 study_records
    conn.execute("INSERT INTO study_records ...")
    
    # 3. 更新 checkins
    conn.execute("INSERT INTO checkins ... ON CONFLICT DO UPDATE ...")
    
    conn.commit()  # 全部成功才提交
except Exception as e:
    conn.rollback()  # 任一失败则回滚
    raise e
finally:
    close_db(conn)
```

#### 6.2.4 查询优化

**避免 N+1 查询问题**：
```python
# 错误做法：循环查询
for word in words:
    progress = conn.execute("SELECT * FROM word_progress WHERE word_id = ?", (word['id'],))

# 正确做法：JOIN 一次性查询
rows = conn.execute("""
    SELECT w.*, wp.status, wp.ease_factor 
    FROM words w 
    LEFT JOIN word_progress wp ON wp.word_id = w.id
    WHERE w.book_id = ?
""", (book_id,))
```

#### 6.2.5 前端性能优化

- **服务端渲染（SSR）**：首屏加载时间 < 500ms
- **懒加载**：统计图表仅在用户滚动到可视区域时渲染
- **缓存策略**：词书列表等静态数据缓存 5 分钟
- **防抖处理**：搜索输入框增加 300ms 防抖，减少 API 调用次数
- **增量更新**：学习进度采用增量更新机制，减少数据传输量

### 6.3 本地化部署优势

- **零网络延迟**：所有资源本地运行，API 响应时间 < 50ms
- **数据隐私**：用户数据存储在本地 SQLite 数据库，不上传云端
- **离线可用**：除 AI 功能外，所有核心功能支持离线使用
- **跨平台兼容**：支持 Windows、macOS、Linux 系统

---

## 7. 测试与部署 (Testing & Deployment)

### 7.1 测试策略

#### 7.1.1 单元测试
- **测试框架**：pytest
- **覆盖模块**：SM-2 算法、干扰项生成、密码加密
- **示例**：
  ```python
  def test_sm2_algorithm():
      result = sm2(ease_factor=2.5, interval=1, repetitions=0, status="new", quality=4)
      assert result["interval"] == 1
      assert result["status"] == "learning"
  ```

#### 7.1.2 接口测试
- **测试工具**：curl / Postman
- **测试场景**：
  - 用户注册登录流程
  - 单词学习与复习流程
  - AI 完形填空生成
  - 词书导入功能
  - 单词标签和笔记功能
  - 昨日重现功能

#### 7.1.3 性能测试
- **测试工具**：Apache Bench (ab)
- **测试指标**：
  - 并发 100 用户，API 响应时间 < 200ms
  - 数据库查询耗时 < 10ms
  - 内存占用 < 200MB

### 7.2 部署指南

#### 7.2.1 环境要求
- Python >= 3.9
- pip >= 21.0
- 操作系统：Windows 10+/macOS 10.15+/Ubuntu 20.04+

#### 7.2.2 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/vocab-master.git
cd vocab-master

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库
python init_db.py

# 5. 启动应用
python main.py
```

#### 7.2.3 访问地址
- **主页面**：http://localhost:8000
- **登录页面**：http://localhost:8000/login
- **API 文档**：http://localhost:8000/docs（Swagger UI）

### 7.3 配置说明

#### 7.3.1 AI 配置
在设置页面配置以下参数：
- **API Key**：大模型 API 密钥（如 OpenAI、智谱、通义千问等）
- **API Base URL**：接口地址（默认 `https://api.openai.com/v1`）
- **Model**：模型名称（默认 `gpt-3.5-turbo`）

#### 7.3.2 学习设置
- **每日新词上限**：1-100 个（默认 15 个）
- **每日复习上限**：10-100 个（默认 30 个）
- **熬夜模式延迟**：0-12 小时（默认 4 小时）
- **单词标签**：支持自定义标签分类
- **用户笔记**：支持为每个单词添加个性化笔记

---

## 8. 未来规划 (Future Roadmap)

### 8.1 短期规划（V1.2）
- [ ] **TTS 语音合成**：集成 pyttsx3 或在线 TTS 服务，实现单词发音
- [ ] **听力训练模式**：听音选义、听音拼写
- [ ] **导出功能**：支持将学习进度导出为 CSV/Excel
- [ ] **快捷键扩展**：增加复习页面的键盘操作支持（如 H/G/F/E 评估键）
- [ ] **词书同步**：支持从云端同步词书资源

### 8.2 中期规划（V1.3）
- [ ] **社交功能**：学习排行榜、好友 PK、学习小组
- [ ] **云端同步**：支持多设备数据同步（需用户注册云端账号）
- [ ] **移动端适配**：开发 PWA 应用，支持手机浏览器安装
- [ ] **智能推荐**：基于学习历史推荐个性化复习计划

### 8.3 长期规划（V2.0）
- [ ] **智能推荐系统**：基于用户学习历史推荐个性化词书
- [ ] **游戏化学习**：积分系统、成就徽章、连胜奖励
- [ ] **多语言支持**：扩展至日语、法语、德语等语种
- [ ] **AI 对话练习**：与 AI 进行英语对话练习

---

## 9. 附录 (Appendix)

### 9.1 术语表

| 术语 | 英文 | 说明 |
| :--- | :--- | :--- |
| 艾宾浩斯遗忘曲线 | Ebbinghaus Forgetting Curve | 描述记忆随时间衰减规律的曲线 |
| SM-2 算法 | SuperMemo 2 Algorithm | 间隔重复算法，动态调整复习间隔 |
| 三轮记忆法 | Three-Round Memory | 初次学习、间隔复习、输出验证三阶段 |
| 难易系数 | Ease Factor | SM-2 算法中反映单词难度的参数 |
| 混淆组 | Confusion Group | 易混淆单词的分组标识 |
| 昨日重现 | Yesterday Review | 针对过去4天内遗忘单词的强化复习功能 |
| 单词标签 | Word Flag | 用于标记单词掌握程度的分类标签 |
| 记忆历史 | Memory History | 记录每次复习结果的二进制序列 |

### 9.2 常见问题 (FAQ)

**Q1: 如何重置学习进度？**
A: 在设置页面点击"重置所有数据"，会清除 `word_progress`、`checkins`、`study_records` 表，但保留词书数据。

**Q2: AI 功能必须配置 API Key 吗？**
A: 是的。未配置 API Key 时，AI 完形填空和作文优化功能不可用，但不影响其他核心功能。

**Q3: 如何导入自定义词书？**
A: 准备 CSV 或 Excel 文件，第一行为表头（必须包含 `word` 列），然后在词书页面点击"导入"按钮上传。

**Q4: 熬夜模式如何工作？**
A: 设置延迟小时数（如 4 小时）后，凌晨 4 点前的学习仍计入"昨天"，避免深夜学习者打卡断签。

**Q5: 如何使用单词标签功能？**
A: 在单词详情页，可以点击标签按钮为单词标记为重难词、已掌握、很熟悉或太简单，方便后续针对性复习。

**Q6: 昨日重现功能是什么？**
A: 昨日重现功能会筛选出过去4天内遗忘的单词，优先安排复习，帮助用户巩固薄弱环节。

**Q7: 如何查看我的学习历史？**
A: 在统计页面可以查看总览统计、掌握度分布、周学习趋势等详细数据，还可以查看每个单词的记忆历史。

### 9.3 联系方式

- **项目地址**：[GitHub Repository Link]
- **问题反馈**：[Issues Page Link]
- **邮箱**：[Your Email]

---

**文档版本历史**：

| 版本 | 日期 | 作者 | 修改说明 |
| :--- | :--- | :--- | :--- |
| V1.0 | 2026-05-17 | [您的姓名] | 初始版本，完成核心模块设计 |
| V1.1 | 2026-05-17 | [您的姓名] | 增加高级复习功能、更新SM-2算法细节、完善数据库设计 |

---

**审批签字**：

| 角色 | 姓名 | 签字 | 日期 |
| :--- | :--- | :--- | :--- |
| 项目经理 | | | |
| 技术负责人 | | | |
| 测试负责人 | | | |
