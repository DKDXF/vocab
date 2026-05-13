"""
复习相关 API —— 强干扰项选择题 + 智能复习调度
"""
import random
from datetime import date, datetime, timedelta
from fastapi import APIRouter
from database import get_db, close_db
from models import ReviewNextOut, ReviewSubmitRequest, WordOut, ReviewModeContentOut, ReviewPlanOut, ReviewPlanItem

router = APIRouter(prefix="/api/review", tags=["复习"])


def _get_setting(conn, key: str, default: str) -> str:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


@router.get("/next", summary="获取下一个待复习单词")
def get_next_review_word():
    """获取当前词书中下一个待复习的单词"""
    conn = get_db()
    try:
        book_id = _get_setting(conn, "current_book_id", "cet4")
        now_str = datetime.now().isoformat()

        row = conn.execute(
            """SELECT w.*, wp.status as p_status, wp.ease_factor, wp.interval,
                      wp.repetitions, wp.next_review_date, wp.stage
               FROM words w
               JOIN word_progress wp ON wp.word_id = w.id
               WHERE w.book_id = ?
                 AND wp.status != 'new'
                 AND wp.next_review_date <= ?
               ORDER BY wp.next_review_date ASC
               LIMIT 1""",
            (book_id, now_str),
        ).fetchone()

        if not row:
            return {"word": None, "progress": None, "remaining": 0}

        remaining = conn.execute(
            """SELECT COUNT(*) as cnt FROM words w
               JOIN word_progress wp ON wp.word_id = w.id
               WHERE w.book_id = ?
                 AND wp.status != 'new'
                 AND wp.next_review_date <= ?""",
            (book_id, now_str),
        ).fetchone()["cnt"]

        word_out = WordOut(
            id=row["id"], book_id=row["book_id"], word=row["word"],
            phonetic=row["phonetic"], part_of_speech=row["part_of_speech"],
            definition_cn=row["definition_cn"], example_sentence=row["example_sentence"],
            example_translation=row["example_translation"],
            root_id=row["root_id"] if "root_id" in row.keys() else None,
            high_freq_defs=row["high_freq_defs"] if "high_freq_defs" in row.keys() else "",
            confusion_group=row["confusion_group"] if "confusion_group" in row.keys() else "",
            mnemonic=row["mnemonic"] if "mnemonic" in row.keys() else "",
            synonym=row["synonym"] if "synonym" in row.keys() else "",
            antonym=row["antonym"] if "antonym" in row.keys() else "",
            derivative=row["derivative"] if "derivative" in row.keys() else "",
            note=row["note"] if "note" in row.keys() else "",
        )
        progress = {
            "status": row["p_status"],
            "ease_factor": row["ease_factor"],
            "interval": row["interval"],
            "repetitions": row["repetitions"],
            "next_review_date": row["next_review_date"],
            "stage": row["stage"] if "stage" in row.keys() else 1,
            "flag": row["flag"] if "flag" in row.keys() else 0,
            "history": row["history"] if "history" in row.keys() else "",
            "user_note": row["user_note"] if "user_note" in row.keys() else "",
        }
        return ReviewNextOut(word=word_out, progress=progress, remaining=remaining)
    finally:
        close_db(conn)


@router.get("/count", summary="获取待复习单词数量")
def get_review_count():
    """获取当前待复习的单词数量"""
    conn = get_db()
    try:
        book_id = _get_setting(conn, "current_book_id", "cet4")
        now_str = datetime.now().isoformat()
        daily_review = int(_get_setting(conn, "daily_review", "30"))

        count = conn.execute(
            """SELECT COUNT(*) as cnt FROM words w
               JOIN word_progress wp ON wp.word_id = w.id
               WHERE w.book_id = ?
                 AND wp.status != 'new'
                 AND wp.next_review_date <= ?""",
            (book_id, now_str),
        ).fetchone()["cnt"]
        return {"count": min(count, daily_review)}
    finally:
        close_db(conn)


@router.get("/queue", summary="获取待复习单词队列")
def get_review_queue():
    """获取当前词书所有待复习的单词列表"""
    conn = get_db()
    try:
        book_id = _get_setting(conn, "current_book_id", "cet4")
        now_str = datetime.now().isoformat()
        daily_review = int(_get_setting(conn, "daily_review", "30"))

        rows = conn.execute(
            """SELECT w.*, wp.status as p_status, wp.ease_factor, wp.interval,
                      wp.repetitions, wp.next_review_date, wp.stage
               FROM words w
               JOIN word_progress wp ON wp.word_id = w.id
               WHERE w.book_id = ?
                 AND wp.status != 'new'
                 AND wp.next_review_date <= ?
               ORDER BY wp.next_review_date ASC
               LIMIT ?""",
            (book_id, now_str, daily_review),
        ).fetchall()

        result = []
        for row in rows:
            word_out = WordOut(
                id=row["id"], book_id=row["book_id"], word=row["word"],
                phonetic=row["phonetic"], part_of_speech=row["part_of_speech"],
                definition_cn=row["definition_cn"], example_sentence=row["example_sentence"],
                example_translation=row["example_translation"],
                root_id=row["root_id"] if "root_id" in row.keys() else None,
                high_freq_defs=row["high_freq_defs"] if "high_freq_defs" in row.keys() else "",
                confusion_group=row["confusion_group"] if "confusion_group" in row.keys() else "",
                mnemonic=row["mnemonic"] if "mnemonic" in row.keys() else "",
                synonym=row["synonym"] if "synonym" in row.keys() else "",
                antonym=row["antonym"] if "antonym" in row.keys() else "",
                derivative=row["derivative"] if "derivative" in row.keys() else "",
                note=row["note"] if "note" in row.keys() else "",
            )
            progress = {
                "status": row["p_status"],
                "ease_factor": row["ease_factor"],
                "interval": row["interval"],
                "repetitions": row["repetitions"],
                "next_review_date": row["next_review_date"],
                "stage": row["stage"] if "stage" in row.keys() else 1,
            }
            result.append({"word": word_out, "progress": progress})
        return result
    finally:
        close_db(conn)


@router.get("/plan", response_model=ReviewPlanOut, summary="获取今日复习计划")
def get_review_plan():
    """获取今日复习计划，按优先级排序"""
    conn = get_db()
    try:
        book_id = _get_setting(conn, "current_book_id", "cet4")
        now_str = datetime.now().isoformat()
        today = date.today().isoformat()

        rows = conn.execute(
            """SELECT w.id, w.word, w.definition_cn, wp.next_review_date, wp.stage
               FROM words w
               JOIN word_progress wp ON wp.word_id = w.id
               WHERE w.book_id = ?
                 AND wp.status != 'new'
                 AND wp.next_review_date <= ?
               ORDER BY 
                 CASE WHEN wp.next_review_date < ? THEN 0 ELSE 1 END,
                 wp.next_review_date ASC""",
            (book_id, now_str, today),
        ).fetchall()

        items = []
        for row in rows:
            nrd = row["next_review_date"] or today
            if nrd < today:
                urgency = "overdue"
            elif nrd == today:
                urgency = "urgent"
            else:
                urgency = "normal"
            items.append(ReviewPlanItem(
                word_id=row["id"],
                word=row["word"],
                definition_cn=row["definition_cn"],
                next_review_date=nrd,
                urgency=urgency,
                stage=row["stage"] if "stage" in row.keys() else 1,
            ))

        return ReviewPlanOut(items=items, total=len(items))
    finally:
        close_db(conn)


# ==================== 强干扰项生成 ====================

def _get_distractors(conn, word_row, book_id: str, count: int = 3) -> list:
    """
    生成强干扰项
    优先级：形近词(confusion_group) > 义近词 > 同词书随机词
    """
    target_id = word_row["id"]
    target_def = word_row["definition_cn"]
    target_group = word_row["confusion_group"] if "confusion_group" in word_row.keys() else ""

    distractors = []

    # 1. 形近词：同 confusion_group 的词
    if target_group:
        similar = conn.execute(
            """SELECT id, definition_cn FROM words
               WHERE confusion_group = ? AND id != ?
               LIMIT ?""",
            (target_group, target_id, count),
        ).fetchall()
        distractors.extend([d["definition_cn"] for d in similar])

    # 2. 补充同词书随机词
    if len(distractors) < count:
        random_words = conn.execute(
            """SELECT id, definition_cn FROM words
               WHERE book_id = ? AND id != ?
               ORDER BY RANDOM() LIMIT ?""",
            (book_id, target_id, count * 3),
        ).fetchall()
        for r in random_words:
            if r["definition_cn"] not in distractors and r["definition_cn"] != target_def:
                distractors.append(r["definition_cn"])
            if len(distractors) >= count:
                break

    # 3. 还不够就硬凑
    if len(distractors) < count:
        all_defs = conn.execute(
            "SELECT id, definition_cn FROM words WHERE book_id = ? AND id != ?",
            (book_id, target_id),
        ).fetchall()
        for d in all_defs:
            if d["definition_cn"] not in distractors and d["definition_cn"] != target_def:
                distractors.append(d["definition_cn"])
            if len(distractors) >= count:
                break

    return distractors[:count]


@router.get("/mode/{mode}", summary="按指定模式获取复习内容（含强干扰项）")
def get_review_by_mode(mode: str):
    """
    按指定模式获取复习内容
    mode: choice(选择题) / spelling(拼写) / listening(听音辨意)
    返回包含强干扰选项的数据
    """
    if mode not in ("choice", "spelling", "listening"):
        return {"error": "无效的复习模式"}

    conn = get_db()
    try:
        book_id = _get_setting(conn, "current_book_id", "cet4")
        now_str = datetime.now().isoformat()
        daily_review = int(_get_setting(conn, "daily_review", "30"))

        # 获取待复习单词
        rows = conn.execute(
            """SELECT w.*, wp.status as p_status, wp.ease_factor, wp.interval,
                      wp.repetitions, wp.next_review_date, wp.stage
               FROM words w
               JOIN word_progress wp ON wp.word_id = w.id
               WHERE w.book_id = ?
                 AND wp.status != 'new'
                 AND wp.next_review_date <= ?
               ORDER BY wp.next_review_date ASC
               LIMIT ?""",
            (book_id, now_str, daily_review),
        ).fetchall()

        if not rows:
            return {"words": [], "total": 0}

        result = []
        for row in rows:
            word_out = WordOut(
                id=row["id"], book_id=row["book_id"], word=row["word"],
                phonetic=row["phonetic"], part_of_speech=row["part_of_speech"],
                definition_cn=row["definition_cn"],
                example_sentence=row["example_sentence"],
                example_translation=row["example_translation"],
                root_id=row["root_id"] if "root_id" in row.keys() else None,
                high_freq_defs=row["high_freq_defs"] if "high_freq_defs" in row.keys() else "",
                confusion_group=row["confusion_group"] if "confusion_group" in row.keys() else "",
                mnemonic=row["mnemonic"] if "mnemonic" in row.keys() else "",
                synonym=row["synonym"] if "synonym" in row.keys() else "",
                antonym=row["antonym"] if "antonym" in row.keys() else "",
                derivative=row["derivative"] if "derivative" in row.keys() else "",
                note=row["note"] if "note" in row.keys() else "",
            )
            progress = {
                "status": row["p_status"],
                "ease_factor": row["ease_factor"],
                "interval": row["interval"],
                "repetitions": row["repetitions"],
                "next_review_date": row["next_review_date"],
                "stage": row["stage"] if "stage" in row.keys() else 1,
            }

            options = []
            correct_index = 0
            if mode in ("choice", "listening"):
                # 使用强干扰项生成
                distractor_defs = _get_distractors(conn, row, book_id, 3)
                options = distractor_defs + [row["definition_cn"]]
                random.shuffle(options)
                correct_index = options.index(row["definition_cn"])

            result.append({
                "word": word_out,
                "progress": progress,
                "options": options,
                "correct_index": correct_index,
            })

        return {"words": result, "total": len(result)}
    finally:
        close_db(conn)


@router.post("/submit", summary="提交复习结果")
def submit_review(req: ReviewSubmitRequest):
    """
    提交复习结果，更新进度
    quality: 0-5（前端根据正确/错误映射: 正确=4, 错误=1）
    """
    from routers.study import sm2

    conn = get_db()
    try:
        progress = conn.execute(
            "SELECT * FROM word_progress WHERE word_id = ?", (req.word_id,)
        ).fetchone()

        if not progress:
            return {"error": "该单词没有学习进度"}

        # 执行 SM-2 算法
        result = sm2(
            progress["ease_factor"], progress["interval"],
            progress["repetitions"], progress["status"], req.quality
        )
        now_str = datetime.now().isoformat()
        today = date.today().isoformat()

        # 更新记忆历史：追加 '1'(记得) 或 '0'(忘记)
        history = progress["history"] if "history" in progress.keys() else ""
        history += '1' if req.quality >= 3 else '0'
        # 只保留最近50次
        if len(history) > 50:
            history = history[-50:]

        # 更新进度
        conn.execute(
            """UPDATE word_progress SET
               status = ?, ease_factor = ?, interval = ?, repetitions = ?,
               next_review_date = ?, last_reviewed_at = ?, history = ?
               WHERE word_id = ?""",
            (result["status"], result["ease_factor"], result["interval"],
             result["repetitions"], result["next_review_date"], now_str, history, req.word_id),
        )

        # 记录学习记录
        conn.execute(
            "INSERT INTO study_records (word_id, action, rating, created_at) VALUES (?, ?, ?, ?)",
            (req.word_id, "review", req.quality, now_str),
        )

        # 更新打卡表复习数
        conn.execute(
            """INSERT INTO checkins (checkin_date, words_learned, words_reviewed, checked)
               VALUES (?, 0, 1, 0)
               ON CONFLICT(checkin_date) DO UPDATE SET words_reviewed = words_reviewed + 1""",
            (today,),
        )

        conn.commit()
        return {"message": "复习提交成功", "progress": result}
    finally:
        close_db(conn)
