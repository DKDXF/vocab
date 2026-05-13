"""
统计相关 API
"""
from datetime import date, timedelta
from fastapi import APIRouter
from database import get_db, close_db
from models import StatsOverviewOut, MasteryDistributionOut, WeeklyDayOut, WeeklyStatsOut, StageProgressOut

router = APIRouter(prefix="/api/stats", tags=["统计"])


def _get_setting(conn, key: str, default: str) -> str:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


@router.get("/overview", response_model=StatsOverviewOut, summary="总览统计")
def get_stats_overview():
    """获取当前词书的总览统计数据"""
    conn = get_db()
    try:
        book_id = _get_setting(conn, "current_book_id", "cet4")

        total_days = conn.execute(
            "SELECT COUNT(*) as cnt FROM checkins WHERE checked = 1"
        ).fetchone()["cnt"]

        stats = conn.execute(
            """SELECT
                 SUM(CASE WHEN wp.id IS NOT NULL AND wp.status != 'new' THEN 1 ELSE 0 END) as learned,
                 SUM(CASE WHEN wp.status = 'mastered' THEN 1 ELSE 0 END) as mastered
               FROM words w
               LEFT JOIN word_progress wp ON wp.word_id = w.id
               WHERE w.book_id = ?""",
            (book_id,),
        ).fetchone()

        # 双记忆率
        memory_rows = conn.execute(
            """SELECT wp.history
               FROM word_progress wp
               JOIN words w ON wp.word_id = w.id
               WHERE w.book_id = ? AND wp.history != ''""",
            (book_id,),
        ).fetchall()
        total_h_len = 0; total_h_zero = 0; total_r_len = 0; total_r_zero = 0
        for r in memory_rows:
            h = r["history"]
            total_h_len += len(h); total_h_zero += h.count('0')
            recent = h[-2:] if len(h) >= 2 else h
            total_r_len += len(recent); total_r_zero += recent.count('0')
        history_rate = round((1 - total_h_zero / total_h_len) * 100, 1) if total_h_len > 0 else 0
        recent_rate = round((1 - total_r_zero / total_r_len) * 100, 1) if total_r_len > 0 else 0

        return StatsOverviewOut(
            total_days=total_days,
            total_learned=stats["learned"] or 0,
            total_mastered=stats["mastered"] or 0,
            history_rate=history_rate,
            recent_rate=recent_rate,
        )
    finally:
        close_db(conn)


@router.get("/mastery", response_model=MasteryDistributionOut, summary="掌握度分布")
def get_mastery_distribution():
    """获取当前词书的掌握程度分布"""
    conn = get_db()
    try:
        book_id = _get_setting(conn, "current_book_id", "cet4")

        total = conn.execute(
            "SELECT COUNT(*) as cnt FROM words WHERE book_id = ?", (book_id,)
        ).fetchone()["cnt"]

        rows = conn.execute(
            """SELECT wp.status, COUNT(*) as cnt
               FROM words w
               LEFT JOIN word_progress wp ON wp.word_id = w.id
               WHERE w.book_id = ?
               GROUP BY wp.status""",
            (book_id,),
        ).fetchall()

        status_map = {r["status"]: r["cnt"] for r in rows}
        new_count = total - sum(v for k, v in status_map.items() if k and k != "new")

        return MasteryDistributionOut(
            new_count=new_count + status_map.get("new", 0),
            learning_count=status_map.get("learning", 0),
            familiar_count=status_map.get("familiar", 0),
            mastered_count=status_map.get("mastered", 0),
            total=total,
        )
    finally:
        close_db(conn)


@router.get("/stage-progress", response_model=StageProgressOut, summary="三轮进度统计")
def get_stage_progress():
    """获取当前词书的三轮进度统计"""
    conn = get_db()
    try:
        book_id = _get_setting(conn, "current_book_id", "cet4")

        row = conn.execute(
            """SELECT
                 SUM(CASE WHEN wp.id IS NULL OR wp.stage = 1 THEN 1 ELSE 0 END) as stage1,
                 SUM(CASE WHEN wp.stage = 2 THEN 1 ELSE 0 END) as stage2,
                 SUM(CASE WHEN wp.stage = 3 AND wp.stage_3_passed = 0 THEN 1 ELSE 0 END) as stage3,
                 SUM(CASE WHEN wp.stage_3_passed = 1 OR wp.status = 'mastered' THEN 1 ELSE 0 END) as mastered
               FROM words w
               LEFT JOIN word_progress wp ON wp.word_id = w.id
               WHERE w.book_id = ?""",
            (book_id,),
        ).fetchone()

        return StageProgressOut(
            new_count=row["stage1"] or 0,
            stage1_count=row["stage1"] or 0,
            stage2_count=row["stage2"] or 0,
            stage3_count=row["stage3"] or 0,
            mastered_count=row["mastered"] or 0,
        )
    finally:
        close_db(conn)


@router.get("/weekly", response_model=WeeklyStatsOut, summary="近7日学习数据")
def get_weekly_stats():
    """获取近7日的学习数据"""
    conn = get_db()
    try:
        days = []
        for i in range(6, -1, -1):
            d = date.today() - timedelta(days=i)
            ds = d.isoformat()
            row = conn.execute(
                "SELECT * FROM checkins WHERE checkin_date = ?", (ds,)
            ).fetchone()
            learned = row["words_learned"] if row else 0
            reviewed = row["words_reviewed"] if row else 0
            days.append(WeeklyDayOut(
                date=ds,
                words_learned=learned,
                words_reviewed=reviewed,
                total=learned + reviewed,
            ))
        return WeeklyStatsOut(days=days)
    finally:
        close_db(conn)


@router.get("/settings", summary="获取学习设置")
def get_settings():
    """获取当前学习设置"""
    conn = get_db()
    try:
        daily_new = int(_get_setting(conn, "daily_new", "10"))
        daily_review = int(_get_setting(conn, "daily_review", "30"))
        daily_new_words_limit = int(_get_setting(conn, "daily_new_words_limit", "15"))
        current_book_id = _get_setting(conn, "current_book_id", "cet4")
        learn_pass_threshold = float(_get_setting(conn, "learn_pass_threshold", "0.7"))
        return {
            "daily_new": daily_new,
            "daily_review": daily_review,
            "daily_new_words_limit": daily_new_words_limit,
            "current_book_id": current_book_id,
            "learn_pass_threshold": learn_pass_threshold,
        }
    finally:
        close_db(conn)


@router.post("/settings", summary="更新学习设置")
def update_settings(daily_new: int = None, daily_review: int = None,
                    daily_new_words_limit: int = None, current_book_id: str = None,
                    learn_pass_threshold: float = None):
    """更新学习设置"""
    conn = get_db()
    try:
        if daily_new is not None:
            daily_new = max(5, min(50, daily_new))
            conn.execute(
                "INSERT INTO settings (key, value) VALUES ('daily_new', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = ?",
                (str(daily_new), str(daily_new)),
            )
        if daily_review is not None:
            daily_review = max(10, min(100, daily_review))
            conn.execute(
                "INSERT INTO settings (key, value) VALUES ('daily_review', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = ?",
                (str(daily_review), str(daily_review)),
            )
        if daily_new_words_limit is not None:
            daily_new_words_limit = max(1, min(100, daily_new_words_limit))
            conn.execute(
                "INSERT INTO settings (key, value) VALUES ('daily_new_words_limit', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = ?",
                (str(daily_new_words_limit), str(daily_new_words_limit)),
            )
        if current_book_id is not None:
            conn.execute(
                "INSERT INTO settings (key, value) VALUES ('current_book_id', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = ?",
                (current_book_id, current_book_id),
            )
        if learn_pass_threshold is not None:
            learn_pass_threshold = max(0.5, min(0.9, learn_pass_threshold))
            conn.execute(
                "INSERT INTO settings (key, value) VALUES ('learn_pass_threshold', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = ?",
                (str(learn_pass_threshold), str(learn_pass_threshold)),
            )
        conn.commit()
        return {"message": "设置已保存"}
    finally:
        close_db(conn)


@router.post("/reset", summary="重置所有学习数据")
def reset_all_data():
    """清除所有学习进度（词书数据保留）"""
    conn = get_db()
    try:
        conn.execute("DELETE FROM word_progress")
        conn.execute("DELETE FROM checkins")
        conn.execute("DELETE FROM study_records")
        conn.execute("DELETE FROM writing_history")
        conn.commit()
        return {"message": "学习数据已重置"}
    finally:
        close_db(conn)
