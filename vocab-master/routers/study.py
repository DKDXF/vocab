"""
学习相关 API —— 三轮记忆法 + SM-2 间隔重复算法
"""
from datetime import date, datetime, timedelta
from fastapi import APIRouter, HTTPException
from database import get_db, close_db
from models import StudySubmitRequest, StudyNextOut, TodayTaskOut, WordWithRootOut, DailyLimitOut, DailyLimitUpdate

router = APIRouter(prefix="/api/study", tags=["学习"])


def _get_setting(conn, key: str, default: str) -> str:
    """从 settings 表读取配置"""
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


# ==================== 艾宾浩斯遗忘曲线间隔 ====================
EBBINGHAUS_INTERVALS = [
    timedelta(minutes=5),    # 第1次复习：5分钟
    timedelta(minutes=30),   # 第2次复习：30分钟
    timedelta(hours=12),     # 第3次复习：12小时
    timedelta(days=1),       # 第4次复习：1天
    timedelta(days=2),       # 第5次复习：2天
    timedelta(days=4),       # 第6次复习：4天
    timedelta(days=7),       # 第7次复习：7天
    timedelta(days=15),      # 第8次复习：15天
]


def sm2(ease_factor: float, interval: int, repetitions: int, status: str, quality: int) -> dict:
    """
    SM-2 间隔重复算法（变体）
    quality: 0-5 评分
    返回: 更新后的 {ease_factor, interval, repetitions, next_review_date, status}
    """
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

    ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if ease_factor < 1.3:
        ease_factor = 1.3

    next_review = date.today() + timedelta(days=interval)

    if status == "new":
        status = "learning"
    elif status == "learning" and quality >= 4 and repetitions >= 3:
        status = "familiar"
    elif status == "familiar" and quality >= 4 and repetitions >= 5:
        status = "mastered"
    if quality <= 1 and status == "mastered":
        status = "familiar"
    if quality == 0 and status == "familiar":
        status = "learning"

    return {
        "ease_factor": round(ease_factor, 2),
        "interval": interval,
        "repetitions": repetitions,
        "next_review_date": next_review.isoformat(),
        "status": status,
    }


def calc_next_review_time(review_step: int, last_time: datetime, ease_factor: float = 2.5) -> datetime:
    """
    根据复习步骤计算下次复习时间
    review_step 1-8 使用固定艾宾浩斯间隔
    review_step 9+ 使用 SM-2 动态间隔
    """
    if 1 <= review_step <= len(EBBINGHAUS_INTERVALS):
        return last_time + EBBINGHAUS_INTERVALS[review_step - 1]
    else:
        # SM-2 动态间隔：用 ease_factor 递推
        days = round(15 * ease_factor / 2.5)  # 基于15天基准
        if days < 1:
            days = 1
        return last_time + timedelta(days=days)


@router.get("/next", summary="获取下一个待学习的新词（第一轮）")
def get_next_study_word():
    """获取当前词书中下一个未学习的单词（第一轮：初次学习）"""
    conn = get_db()
    try:
        book_id = _get_setting(conn, "current_book_id", "cet4")
        daily_new = int(_get_setting(conn, "daily_new_words_limit", "15"))

        # 计算今日已学新词数
        today = date.today().isoformat()
        checkin = conn.execute(
            "SELECT words_learned FROM checkins WHERE checkin_date = ?", (today,)
        ).fetchone()
        already_learned = checkin["words_learned"] if checkin else 0
        remaining = max(0, daily_new - already_learned)

        if remaining <= 0:
            return {"word": None, "progress": None, "today_new_count": already_learned, "today_review_count": 0, "stage": 1}

        # 查找下一个未学习的单词（stage=1 且没有进度记录，或状态为 new）
        row = conn.execute(
            """SELECT w.*, wr.root_text, wr.meaning as root_meaning
               FROM words w
               LEFT JOIN word_progress wp ON wp.word_id = w.id
               LEFT JOIN word_roots wr ON w.root_id = wr.id
               WHERE w.book_id = ?
                 AND (wp.id IS NULL OR wp.status = 'new')
               ORDER BY w.sort_order
               LIMIT 1""",
            (book_id,),
        ).fetchone()

        if not row:
            return {"word": None, "progress": None, "today_new_count": already_learned, "today_review_count": 0, "stage": 1}

        word_out = WordWithRootOut(
            id=row["id"], book_id=row["book_id"], word=row["word"],
            phonetic=row["phonetic"], part_of_speech=row["part_of_speech"],
            definition_cn=row["definition_cn"], example_sentence=row["example_sentence"],
            example_translation=row["example_translation"],
            root_id=row["root_id"], high_freq_defs=row["high_freq_defs"],
            confusion_group=row["confusion_group"],
            root_text=row["root_text"] or "", root_meaning=row["root_meaning"] or "",
        )

        return StudyNextOut(
            word=word_out,
            progress=None,
            today_new_count=already_learned,
            today_review_count=0,
            stage=1,
        )
    finally:
        close_db(conn)


@router.get("/review-next", summary="获取下一个待复习单词（第二/三轮）")
def get_next_review_study():
    """获取当前词书中待复习的单词（第二轮间隔复习 或 第三轮输出验证）"""
    conn = get_db()
    try:
        book_id = _get_setting(conn, "current_book_id", "cet4")
        now_str = datetime.now().isoformat()

        # 优先获取第三轮待验证的单词
        row = conn.execute(
            """SELECT w.*, wp.*, wr.root_text, wr.meaning as root_meaning
               FROM words w
               JOIN word_progress wp ON wp.word_id = w.id
               LEFT JOIN word_roots wr ON w.root_id = wr.id
               WHERE w.book_id = ?
                 AND wp.stage = 3
                 AND wp.stage_3_passed = 0
                 AND wp.next_review_date <= ?
               ORDER BY wp.next_review_date ASC
               LIMIT 1""",
            (book_id, now_str),
        ).fetchone()

        stage = 2
        if not row:
            # 获取第二轮待复习的单词
            row = conn.execute(
                """SELECT w.*, wp.*, wr.root_text, wr.meaning as root_meaning
                   FROM words w
                   JOIN word_progress wp ON wp.word_id = w.id
                   LEFT JOIN word_roots wr ON w.root_id = wr.id
                   WHERE w.book_id = ?
                     AND wp.stage = 2
                     AND wp.next_review_date <= ?
                   ORDER BY wp.next_review_date ASC
                   LIMIT 1""",
                (book_id, now_str),
            ).fetchone()
        else:
            stage = 3

        if not row:
            return {"word": None, "progress": None, "stage": stage}

        word_out = WordWithRootOut(
            id=row["id"], book_id=row["book_id"], word=row["word"],
            phonetic=row["phonetic"], part_of_speech=row["part_of_speech"],
            definition_cn=row["definition_cn"], example_sentence=row["example_sentence"],
            example_translation=row["example_translation"],
            root_id=row["root_id"], high_freq_defs=row["high_freq_defs"],
            confusion_group=row["confusion_group"],
            root_text=row["root_text"] or "", root_meaning=row["root_meaning"] or "",
        )

        progress = {
            "status": row["status"],
            "ease_factor": row["ease_factor"],
            "interval": row["interval"],
            "repetitions": row["repetitions"],
            "next_review_date": row["next_review_date"],
            "stage": row["stage"],
            "review_step": row["review_step"],
            "stage_2_pass_count": row["stage_2_pass_count"],
            "stage_3_attempts": row["stage_3_attempts"],
            "stage_3_passed": row["stage_3_passed"],
        }
        stage = row["stage"]

        return {"word": word_out, "progress": progress, "stage": stage}
    finally:
        close_db(conn)


@router.post("/submit", summary="提交学习评分（三轮记忆法）")
def submit_study(req: StudySubmitRequest):
    """
    提交学习评分，更新进度（三轮记忆法）
    第一轮：用户标记"我认识了"，进入第二轮
    第二轮：间隔复习，自评掌握程度
    第三轮：输出验证，通过则标记已掌握
    """
    conn = get_db()
    try:
        progress = conn.execute(
            "SELECT * FROM word_progress WHERE word_id = ?", (req.word_id,)
        ).fetchone()

        today = date.today().isoformat()
        now_str = datetime.now().isoformat()

        if progress:
            stage = progress["stage"]
            review_step = progress["review_step"]
            stage_2_pass_count = progress["stage_2_pass_count"]
            stage_3_attempts = progress["stage_3_attempts"]
            stage_3_passed = progress["stage_3_passed"]
            ease_factor = progress["ease_factor"]
            interval = progress["interval"]
            repetitions = progress["repetitions"]
            status = progress["status"]
        else:
            stage = 1
            review_step = 0
            stage_2_pass_count = 0
            stage_3_attempts = 0
            stage_3_passed = 0
            ease_factor = 2.5
            interval = 0
            repetitions = 0
            status = "new"

        if req.action == "study" or stage == 1:
            # ===== 第一轮：初次学习 =====
            # 标记第一轮完成，进入第二轮
            next_review = calc_next_review_time(1, datetime.now(), ease_factor)
            if progress:
                conn.execute(
                    """UPDATE word_progress SET
                       status = 'learning', stage = 2, review_step = 1,
                       stage_1_done_at = ?, next_review_date = ?,
                       last_reviewed_at = ?, learn_date = COALESCE(learn_date, ?),
                       ease_factor = 2.5, interval = 0, repetitions = 0
                       WHERE word_id = ?""",
                    (now_str, next_review.isoformat(), now_str, today, req.word_id),
                )
            else:
                conn.execute(
                    """INSERT INTO word_progress
                       (word_id, status, ease_factor, interval, repetitions,
                        next_review_date, last_reviewed_at, learn_date,
                        stage, review_step, stage_1_done_at,
                        stage_2_pass_count, stage_3_attempts, stage_3_passed)
                       VALUES (?, 'learning', 2.5, 0, 0, ?, ?, ?, 2, 1, ?, 0, 0, 0)""",
                    (req.word_id, next_review.isoformat(), now_str, today, now_str),
                )
            result = {"stage": 2, "next_review_date": next_review.isoformat(), "status": "learning"}

        elif stage == 2:
            # ===== 第二轮：间隔复习 =====
            quality = req.rating
            if quality >= 3:
                stage_2_pass_count += 1

            review_step += 1

            # 计算下次复习时间
            next_review = calc_next_review_time(review_step, datetime.now(), ease_factor)

            # SM-2 更新 ease_factor
            sm2_result = sm2(ease_factor, interval, repetitions, status, quality)

            # 判断是否进入第三轮
            if stage_2_pass_count >= 2:
                new_stage = 3
                new_status = "familiar" if status != "mastered" else status
            else:
                new_stage = 2
                new_status = sm2_result["status"]

            conn.execute(
                """UPDATE word_progress SET
                   status = ?, ease_factor = ?, interval = ?, repetitions = ?,
                   next_review_date = ?, last_reviewed_at = ?,
                   stage = ?, review_step = ?, stage_2_pass_count = ?
                   WHERE word_id = ?""",
                (new_status, sm2_result["ease_factor"], sm2_result["interval"],
                 sm2_result["repetitions"], next_review.isoformat(), now_str,
                 new_stage, review_step, stage_2_pass_count, req.word_id),
            )
            result = {"stage": new_stage, "next_review_date": next_review.isoformat(),
                      "status": new_status, "stage_2_pass_count": stage_2_pass_count}

        elif stage == 3:
            # ===== 第三轮：输出验证 =====
            stage_3_attempts += 1
            quality = req.rating

            if quality >= 3:
                # 验证通过
                stage_3_passed = 1
                status = "mastered"
                result = {"stage": 3, "status": "mastered", "stage_3_passed": 1}
            else:
                # 验证失败，回退到第二轮
                stage = 2
                stage_2_pass_count = 0
                review_step = max(1, review_step)
                next_review = calc_next_review_time(review_step, datetime.now(), ease_factor)
                status = "learning"
                result = {"stage": 2, "status": "learning", "stage_3_passed": 0,
                          "next_review_date": next_review.isoformat()}

            conn.execute(
                """UPDATE word_progress SET
                   status = ?, stage = ?, stage_3_attempts = ?, stage_3_passed = ?,
                   last_reviewed_at = ?, stage_2_pass_count = ?,
                   next_review_date = COALESCE(?, next_review_date)
                   WHERE word_id = ?""",
                (status, stage, stage_3_attempts, stage_3_passed, now_str,
                 stage_2_pass_count if stage == 3 else 0,
                 result.get("next_review_date"), req.word_id),
            )
        else:
            result = {"stage": stage}

        # 记录学习记录
        conn.execute(
            "INSERT INTO study_records (word_id, action, rating, created_at) VALUES (?, ?, ?, ?)",
            (req.word_id, req.action, req.rating, now_str),
        )

        # 更新记忆历史
        existing_progress = conn.execute(
            "SELECT history FROM word_progress WHERE word_id = ?", (req.word_id,)
        ).fetchone()
        if existing_progress:
            history = existing_progress["history"] if "history" in existing_progress.keys() else ""
            history += '1' if req.rating >= 3 else '0'
            if len(history) > 50:
                history = history[-50:]
            conn.execute(
                "UPDATE word_progress SET history = ? WHERE word_id = ?",
                (history, req.word_id),
            )

        # 更新打卡表
        if req.action == "study":
            conn.execute(
                """INSERT INTO checkins (checkin_date, words_learned, words_reviewed, checked)
                   VALUES (?, 1, 0, 0)
                   ON CONFLICT(checkin_date) DO UPDATE SET words_learned = words_learned + 1""",
                (today,),
            )
        else:
            conn.execute(
                """INSERT INTO checkins (checkin_date, words_learned, words_reviewed, checked)
                   VALUES (?, 0, 1, 0)
                   ON CONFLICT(checkin_date) DO UPDATE SET words_reviewed = words_reviewed + 1""",
                (today,),
            )

        conn.commit()
        return {"message": "提交成功", "progress": result}
    finally:
        close_db(conn)


@router.get("/today", response_model=TodayTaskOut, summary="获取今日学习任务概览")
def get_today_task():
    """获取今日的学习和复习任务概览（含三轮进度）"""
    conn = get_db()
    try:
        book_id = _get_setting(conn, "current_book_id", "cet4")
        daily_new = int(_get_setting(conn, "daily_new_words_limit", "15"))
        daily_review = int(_get_setting(conn, "daily_review", "30"))
        today = date.today().isoformat()
        now_str = datetime.now().isoformat()

        # 今日已学新词/复习数
        checkin = conn.execute(
            "SELECT * FROM checkins WHERE checkin_date = ?", (today,)
        ).fetchone()
        today_new = checkin["words_learned"] if checkin else 0
        today_review = checkin["words_reviewed"] if checkin else 0

        # 剩余新词
        new_remaining = conn.execute(
            """SELECT COUNT(*) as cnt FROM words w
               LEFT JOIN word_progress wp ON wp.word_id = w.id
               WHERE w.book_id = ? AND (wp.id IS NULL OR wp.status = 'new')""",
            (book_id,),
        ).fetchone()["cnt"]
        new_remaining = min(new_remaining, max(0, daily_new - today_new))

        # 剩余待复习词
        review_remaining = conn.execute(
            """SELECT COUNT(*) as cnt FROM words w
               JOIN word_progress wp ON wp.word_id = w.id
               WHERE w.book_id = ?
                 AND wp.stage IN (2, 3)
                 AND wp.next_review_date <= ?""",
            (book_id, now_str),
        ).fetchone()["cnt"]
        review_remaining = min(review_remaining, daily_review)

        # 总已学/已掌握
        total_stats = conn.execute(
            """SELECT
                 SUM(CASE WHEN wp.id IS NOT NULL AND wp.status != 'new' THEN 1 ELSE 0 END) as learned,
                 SUM(CASE WHEN wp.status = 'mastered' THEN 1 ELSE 0 END) as mastered
               FROM words w
               LEFT JOIN word_progress wp ON wp.word_id = w.id
               WHERE w.book_id = ?""",
            (book_id,),
        ).fetchone()
        total_learned = total_stats["learned"] or 0
        total_mastered = total_stats["mastered"] or 0

        # 连续打卡天数
        streak = _calc_streak(conn)

        # 三轮进度统计
        stage_stats = conn.execute(
            """SELECT
                 SUM(CASE WHEN wp.stage = 1 OR wp.id IS NULL THEN 1 ELSE 0 END) as stage1,
                 SUM(CASE WHEN wp.stage = 2 THEN 1 ELSE 0 END) as stage2,
                 SUM(CASE WHEN wp.stage = 3 AND wp.stage_3_passed = 0 THEN 1 ELSE 0 END) as stage3,
                 SUM(CASE WHEN wp.stage_3_passed = 1 OR wp.status = 'mastered' THEN 1 ELSE 0 END) as mastered
               FROM words w
               LEFT JOIN word_progress wp ON wp.word_id = w.id
               WHERE w.book_id = ?""",
            (book_id,),
        ).fetchone()

        return TodayTaskOut(
            new_words_remaining=new_remaining,
            review_words_remaining=review_remaining,
            today_new=today_new,
            today_review=today_review,
            total_learned=total_learned,
            total_mastered=total_mastered,
            streak=streak,
            stage1_count=stage_stats["stage1"] or 0,
            stage2_count=stage_stats["stage2"] or 0,
            stage3_count=stage_stats["stage3"] or 0,
        )
    finally:
        close_db(conn)


@router.get("/daily-limit", response_model=DailyLimitOut, summary="获取每日新词上限")
def get_daily_limit():
    conn = get_db()
    try:
        limit = int(_get_setting(conn, "daily_new_words_limit", "15"))
        return DailyLimitOut(daily_new_words_limit=limit)
    finally:
        close_db(conn)


@router.post("/daily-limit", summary="设置每日新词上限")
def set_daily_limit(req: DailyLimitUpdate):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('daily_new_words_limit', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = ?",
            (str(req.daily_new_words_limit), str(req.daily_new_words_limit)),
        )
        conn.commit()
        return {"message": "设置已保存", "daily_new_words_limit": req.daily_new_words_limit}
    finally:
        close_db(conn)


def _calc_streak(conn) -> int:
    """计算连续打卡天数"""
    streak = 0
    d = date.today()
    while True:
        row = conn.execute(
            "SELECT checked FROM checkins WHERE checkin_date = ?", (d.isoformat(),)
        ).fetchone()
        if row and row["checked"]:
            streak += 1
            d -= timedelta(days=1)
        else:
            break
    return streak
