"""
Pydantic 数据模型 —— 用于 API 请求/响应校验
"""
from pydantic import BaseModel, Field
from typing import Optional, List


# ==================== 单词/词书 ====================
class WordOut(BaseModel):
    id: int
    book_id: str
    word: str
    phonetic: str = ""
    part_of_speech: str = ""
    definition_cn: str = ""
    example_sentence: str = ""
    example_translation: str = ""
    root_id: Optional[int] = None
    high_freq_defs: str = ""
    confusion_group: str = ""
    mnemonic: str = ""
    synonym: str = ""
    antonym: str = ""
    derivative: str = ""
    note: str = ""

    class Config:
        from_attributes = True


class WordWithRootOut(WordOut):
    root_text: str = ""
    root_meaning: str = ""


class BookOut(BaseModel):
    id: str
    name: str
    description: str = ""
    icon: str = "📘"
    word_count: int = 0
    learned: int = 0
    mastered: int = 0
    progress_pct: float = 0.0
    is_current: bool = False
    history_rate: float = 0.0
    recent_rate: float = 0.0


class BookProgressOut(BaseModel):
    book_id: str
    total: int
    learned: int
    mastered: int
    progress_pct: float


class ImportResult(BaseModel):
    success_count: int = 0
    fail_count: int = 0
    errors: List[str] = []
    book_id: str = ""
    book_name: str = ""


# ==================== 词根词缀 ====================
class RootOut(BaseModel):
    id: int
    root_text: str
    meaning: str = ""
    description: str = ""
    word_count: int = 0


class RootWithWordsOut(BaseModel):
    root: RootOut
    words: List[WordOut] = []


# ==================== 学习 ====================
class StudySubmitRequest(BaseModel):
    word_id: int
    rating: int = Field(..., ge=0, le=5, description="SM-2 评分 0-5")
    action: str = Field("study", pattern="^(study|review)$")


class StudyNextOut(BaseModel):
    word: Optional[WordWithRootOut] = None
    progress: Optional[dict] = None
    today_new_count: int = 0
    today_review_count: int = 0
    stage: int = 1


class TodayTaskOut(BaseModel):
    new_words_remaining: int = 0
    review_words_remaining: int = 0
    today_new: int = 0
    today_review: int = 0
    total_learned: int = 0
    total_mastered: int = 0
    streak: int = 0
    stage1_count: int = 0
    stage2_count: int = 0
    stage3_count: int = 0


# ==================== 复习 ====================
class ReviewNextOut(BaseModel):
    word: Optional[WordOut] = None
    progress: Optional[dict] = None
    remaining: int = 0


class ReviewSubmitRequest(BaseModel):
    word_id: int
    quality: int = Field(..., ge=0, le=5, description="SM-2 quality 0-5")
    mode: str = Field("choice", pattern="^(choice|spelling|listening|yesterday-review)$")


class DistractorOut(BaseModel):
    """用于选择题/听音辨意的干扰项"""
    word_id: int
    definition_cn: str


class ReviewModeContentOut(BaseModel):
    word: WordOut
    options: List[str] = []
    correct_index: int = 0


# ==================== 复习计划 ====================
class ReviewPlanItem(BaseModel):
    word_id: int
    word: str
    definition_cn: str = ""
    next_review_date: str = ""
    urgency: str = "normal"  # overdue / urgent / normal
    stage: int = 1


class ReviewPlanOut(BaseModel):
    items: List[ReviewPlanItem] = []
    total: int = 0


# ==================== 打卡 ====================
class CheckinOut(BaseModel):
    date: str
    words_learned: int = 0
    words_reviewed: int = 0
    checked: bool = False


class CheckinCalendarDay(BaseModel):
    date: str
    checked: bool = False
    words_learned: int = 0
    words_reviewed: int = 0


class CheckinCalendarOut(BaseModel):
    year: int
    month: int
    days: List[CheckinCalendarDay] = []


class CheckinStreakOut(BaseModel):
    streak: int


# ==================== 统计 ====================
class StatsOverviewOut(BaseModel):
    total_days: int
    total_learned: int
    total_mastered: int
    history_rate: float = 0.0
    recent_rate: float = 0.0


class MasteryDistributionOut(BaseModel):
    new_count: int
    learning_count: int
    familiar_count: int
    mastered_count: int
    total: int


class WeeklyDayOut(BaseModel):
    date: str
    words_learned: int
    words_reviewed: int
    total: int


class WeeklyStatsOut(BaseModel):
    days: List[WeeklyDayOut]


class StageProgressOut(BaseModel):
    stage1_count: int = 0
    stage2_count: int = 0
    stage3_count: int = 0
    mastered_count: int = 0
    new_count: int = 0


# ==================== 单词标签 ====================
class FlagUpdateRequest(BaseModel):
    flag: int = Field(..., ge=-1, le=10, description="-1重难词, 0默认, 1已掌握, 2很熟悉, 10太简单")


class FlagStatsOut(BaseModel):
    hard_count: int = 0       # flag=-1
    normal_count: int = 0     # flag=0
    mastered_count: int = 0   # flag=1
    familiar_count: int = 0   # flag=2
    easy_count: int = 0       # flag=10


# ==================== 用户笔记 ====================
class NoteUpdateRequest(BaseModel):
    user_note: str = Field(..., max_length=500)


# ==================== 熬夜模式 ====================
class DelayHoursRequest(BaseModel):
    delay_hours: int = Field(..., ge=0, le=12)


# ==================== 艾宾浩斯日历 ====================
class CalendarDayItem(BaseModel):
    date: str
    books: List[str] = []
    word_count: int = 0
    is_ebbinghaus: bool = False
    is_extra: bool = False


class CalendarMonthOut(BaseModel):
    year: int
    month: int
    days: List[CalendarDayItem] = []


# ==================== AI 配置 ====================
class LLMSettingsOut(BaseModel):
    api_key_set: bool = False
    api_key_masked: str = ""
    api_base: str = "https://api.openai.com/v1"
    model: str = "gpt-3.5-turbo"


class LLMSettingsUpdate(BaseModel):
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: Optional[str] = None


# ==================== AI 完形填空 ====================
class ClozeGenerateRequest(BaseModel):
    word_ids: List[int] = []


class ClozeSubmitRequest(BaseModel):
    answers: dict = {}  # {blank_index: selected_option_index}
    cloze_id: str = ""


# ==================== AI 作文优化 ====================
class WritingOptimizeRequest(BaseModel):
    text: Optional[str] = None
    mode: str = Field("text", pattern="^(text|image|file)$")


class WritingHistoryItem(BaseModel):
    id: int
    original: str
    optimized: str = ""
    feedback: str = ""
    score: int = 0
    mode: str = "text"
    created_at: str


# ==================== 每日新词上限 ====================
class DailyLimitOut(BaseModel):
    daily_new_words_limit: int = 15


class DailyLimitUpdate(BaseModel):
    daily_new_words_limit: int = Field(..., ge=1, le=100)
