"""
WordReview 融合功能 API
包含：昨日重现、单词标签、笔记、记忆历史、熬夜模式、艾宾浩斯日历
"""
import calendar as cal_mod
from datetime import date, datetime, timedelta
from fastapi import APIRouter, HTTPException
from database import get_db, close_db
from models import (
    FlagUpdateRequest, FlagStatsOut, NoteUpdateRequest,
    DelayHoursRequest, CalendarMonthOut, CalendarDayItem,
)

router = APIRouter(prefix="/api", tags=["WordReview 融合"])


def _get_setting(conn, key: str, default: str) -> str:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def _get_study_date(conn) -> date:
    """获取学习日期（考虑熬夜模式延迟）"""
    delay_hours = int(_get_setting(conn, "delay_hours", "4"))
    now = datetime.now()
    if delay_hours > 0 and now.hour < delay_hours:
        return (now - timedelta(days=1)).date()
    return now.date()


# ==================== 1. 昨日重现 ====================
@router.get("/review/yesterday-review", summary="获取昨日重现单词")
def get_yesterday_review():
    """筛选过去4天内遗忘过的单词（困难或复习未通过）"""
    conn = get_db()
    try:
        book_id = _get_setting(conn, "current_book_id", "cet4")
        cutoff = (date.today() - timedelta(days=4)).isoformat()

        rows = conn.execute(
            """SELECT w.*, wp.status as p_status, wp.ease_factor, wp.interval,
                      wp.repetitions, wp.next_review_date, wp.stage, wp.flag,
                      wp.history, wp.user_note
               FROM words w
               JOIN word_progress wp ON wp.word_id = w.id
               WHERE w.book_id = ?
                 AND wp.status != 'new'
                 AND wp.last_reviewed_at >= ?
                 AND (wp.history LIKE '%0' OR wp.flag = -1)
                 AND wp.flag NOT IN (2, 10)
               ORDER BY wp.last_reviewed_at DESC
               LIMIT 30""",
            (book_id, cutoff),
        ).fetchall()

        result = []
        for row in rows:
            word_data = _row_to_word_dict(row)
            progress = {
                "status": row["p_status"],
                "ease_factor": row["ease_factor"],
                "interval": row["interval"],
                "repetitions": row["repetitions"],
                "next_review_date": row["next_review_date"],
                "stage": row["stage"],
                "flag": row["flag"] if "flag" in row.keys() else 0,
                "history": row["history"] if "history" in row.keys() else "",
                "user_note": row["user_note"] if "user_note" in row.keys() else "",
            }
            result.append({"word": word_data, "progress": progress})
        return {"words": result, "total": len(result)}
    finally:
        close_db(conn)


# ==================== 3. 单词标签 ====================
@router.post("/words/{word_id}/flag", summary="设置单词标签")
def set_word_flag(word_id: int, req: FlagUpdateRequest):
    """设置单词标签: -1重难词, 0默认, 1已掌握, 2很熟悉, 10太简单"""
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM word_progress WHERE word_id = ?", (word_id,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE word_progress SET flag = ? WHERE word_id = ?",
                (req.flag, word_id),
            )
        else:
            conn.execute(
                "INSERT INTO word_progress (word_id, flag, status, ease_factor, interval, repetitions) VALUES (?, ?, 'new', 2.5, 0, 0)",
                (word_id, req.flag),
            )
        conn.commit()
        return {"message": "标签已更新", "flag": req.flag}
    finally:
        close_db(conn)


@router.get("/words/flag-stats", summary="获取标签统计")
def get_flag_stats():
    """获取当前词书各标签单词数量"""
    conn = get_db()
    try:
        book_id = _get_setting(conn, "current_book_id", "cet4")
        rows = conn.execute(
            """SELECT wp.flag, COUNT(*) as cnt
               FROM word_progress wp
               JOIN words w ON wp.word_id = w.id
               WHERE w.book_id = ?
               GROUP BY wp.flag""",
            (book_id,),
        ).fetchall()
        flag_map = {r["flag"]: r["cnt"] for r in rows}
        return FlagStatsOut(
            hard_count=flag_map.get(-1, 0),
            normal_count=flag_map.get(0, 0),
            mastered_count=flag_map.get(1, 0),
            familiar_count=flag_map.get(2, 0),
            easy_count=flag_map.get(10, 0),
        )
    finally:
        close_db(conn)


# ==================== 11. 笔记功能 ====================
@router.post("/words/{word_id}/note", summary="保存用户笔记")
def save_user_note(word_id: int, req: NoteUpdateRequest):
    """保存/更新用户对单词的个人笔记"""
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM word_progress WHERE word_id = ?", (word_id,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE word_progress SET user_note = ? WHERE word_id = ?",
                (req.user_note, word_id),
            )
        else:
            conn.execute(
                "INSERT INTO word_progress (word_id, user_note, status, ease_factor, interval, repetitions) VALUES (?, ?, 'new', 2.5, 0, 0)",
                (word_id, req.user_note),
            )
        conn.commit()
        return {"message": "笔记已保存"}
    finally:
        close_db(conn)


# ==================== 12. 熬夜模式 ====================
@router.get("/settings/delay-hours", summary="获取熬夜模式延迟小时数")
def get_delay_hours():
    conn = get_db()
    try:
        val = int(_get_setting(conn, "delay_hours", "4"))
        return {"delay_hours": val}
    finally:
        close_db(conn)


@router.post("/settings/delay-hours", summary="设置熬夜模式延迟小时数")
def set_delay_hours(req: DelayHoursRequest):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('delay_hours', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = ?",
            (str(req.delay_hours), str(req.delay_hours)),
        )
        conn.commit()
        return {"message": "熬夜模式已更新", "delay_hours": req.delay_hours}
    finally:
        close_db(conn)


# ==================== 6. 艾宾浩斯日历 ====================
@router.get("/review/calendar", summary="获取艾宾浩斯复习日历")
def get_ebbinghaus_calendar(year: int = None, month: int = None):
    """返回指定月份的艾宾浩斯复习计划日历"""
    today = date.today()
    year = year or today.year
    month = month or today.month

    conn = get_db()
    try:
        days_in_month = cal_mod.monthrange(year, month)[1]
        month_start = f"{year}-{month:02d}-01"
        if month < 12:
            month_end = f"{year}-{month + 1:02d}-01"
        else:
            month_end = f"{year + 1}-01-01"

        # 获取艾宾浩斯计划复习日期（基于 next_review_date）
        plan_rows = conn.execute(
            """SELECT DATE(wp.next_review_date) as review_date, wb.name as book_name, COUNT(*) as cnt
               FROM word_progress wp
               JOIN words w ON wp.word_id = w.id
               JOIN word_books wb ON w.book_id = wb.id
               WHERE wp.next_review_date >= ? AND wp.next_review_date < ?
                 AND wp.status != 'new'
                 AND wp.flag NOT IN (2, 10)
               GROUP BY DATE(wp.next_review_date), w.book_id, wb.name
               ORDER BY review_date""",
            (month_start, month_end),
        ).fetchall()

        # 获取实际打卡/复习日期（自愿额外复习）
        checkin_rows = conn.execute(
            "SELECT checkin_date, words_reviewed FROM checkins WHERE checkin_date >= ? AND checkin_date < ? AND words_reviewed > 0",
            (month_start, month_end),
        ).fetchall()

        # 构建日历数据
        plan_map = {}  # date -> [{book_name, count}]
        for r in plan_rows:
            d = r["review_date"]
            if d not in plan_map:
                plan_map[d] = []
            plan_map[d].append({"book_name": r["book_name"], "count": r["cnt"]})

        extra_dates = set()
        for r in checkin_rows:
            extra_dates.add(r["checkin_date"])

        days = []
        for d in range(1, days_in_month + 1):
            ds = f"{year}-{month:02d}-{d:02d}"
            books = []
            word_count = 0
            is_ebbinghaus = ds in plan_map
            is_extra = ds in extra_dates

            if is_ebbinghaus:
                for item in plan_map[ds]:
                    books.append(item["book_name"])
                    word_count += item["count"]

            days.append(CalendarDayItem(
                date=ds,
                books=books,
                word_count=word_count,
                is_ebbinghaus=is_ebbinghaus,
                is_extra=is_extra,
            ))

        return CalendarMonthOut(year=year, month=month, days=days)
    finally:
        close_db(conn)


# ==================== 5. 双记忆率 ====================
@router.get("/words/memory-rates", summary="获取双记忆率指标")
def get_memory_rates():
    """获取当前词书的历史记忆率和近期记忆率"""
    conn = get_db()
    try:
        book_id = _get_setting(conn, "current_book_id", "cet4")

        rows = conn.execute(
            """SELECT wp.history
               FROM word_progress wp
               JOIN words w ON wp.word_id = w.id
               WHERE w.book_id = ? AND wp.history != ''""",
            (book_id,),
        ).fetchall()

        total_history_len = 0
        total_history_zeros = 0
        total_recent_len = 0
        total_recent_zeros = 0

        for r in rows:
            h = r["history"]
            if not h:
                continue
            total_history_len += len(h)
            total_history_zeros += h.count('0')
            # 近期：最后2次
            recent = h[-2:] if len(h) >= 2 else h
            total_recent_len += len(recent)
            total_recent_zeros += recent.count('0')

        history_rate = round((1 - total_history_zeros / total_history_len) * 100, 1) if total_history_len > 0 else 0
        recent_rate = round((1 - total_recent_zeros / total_recent_len) * 100, 1) if total_recent_len > 0 else 0

        return {
            "history_rate": history_rate,
            "recent_rate": recent_rate,
        }
    finally:
        close_db(conn)


# ==================== 辅助函数 ====================
def _row_to_word_dict(row):
    """将数据库行转为单词字典"""
    return {
        "id": row["id"],
        "book_id": row["book_id"],
        "word": row["word"],
        "phonetic": row["phonetic"],
        "part_of_speech": row["part_of_speech"],
        "definition_cn": row["definition_cn"],
        "example_sentence": row["example_sentence"],
        "example_translation": row["example_translation"],
        "root_id": row["root_id"] if "root_id" in row.keys() else None,
        "high_freq_defs": row["high_freq_defs"] if "high_freq_defs" in row.keys() else "",
        "confusion_group": row["confusion_group"] if "confusion_group" in row.keys() else "",
        "mnemonic": row["mnemonic"] if "mnemonic" in row.keys() else "",
        "synonym": row["synonym"] if "synonym" in row.keys() else "",
        "antonym": row["antonym"] if "antonym" in row.keys() else "",
        "derivative": row["derivative"] if "derivative" in row.keys() else "",
        "note": row["note"] if "note" in row.keys() else "",
    }
