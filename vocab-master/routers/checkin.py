"""
打卡相关 API
"""
from datetime import date, timedelta
from fastapi import APIRouter
from database import get_db, close_db
from models import CheckinOut, CheckinCalendarOut, CheckinCalendarDay, CheckinStreakOut

router = APIRouter(prefix="/api/checkin", tags=["打卡"])


@router.post("", summary="今日打卡")
def do_checkin():
    """标记今日为已打卡"""
    conn = get_db()
    try:
        today = date.today().isoformat()
        existing = conn.execute(
            "SELECT * FROM checkins WHERE checkin_date = ?", (today,)
        ).fetchone()

        if existing and existing["checked"]:
            return {"message": "今日已打卡", "already": True}

        if existing:
            conn.execute(
                "UPDATE checkins SET checked = 1 WHERE checkin_date = ?", (today,)
            )
        else:
            conn.execute(
                "INSERT INTO checkins (checkin_date, words_learned, words_reviewed, checked) VALUES (?, 0, 0, 1)",
                (today,),
            )

        conn.commit()
        return {"message": "打卡成功！", "already": False, "date": today}
    finally:
        close_db(conn)


@router.get("/status", summary="获取今日打卡状态")
def get_checkin_status():
    """获取今日打卡状态"""
    conn = get_db()
    try:
        today = date.today().isoformat()
        row = conn.execute(
            "SELECT * FROM checkins WHERE checkin_date = ?", (today,)
        ).fetchone()

        if row:
            return CheckinOut(
                date=today,
                words_learned=row["words_learned"],
                words_reviewed=row["words_reviewed"],
                checked=bool(row["checked"]),
            )
        return CheckinOut(date=today, words_learned=0, words_reviewed=0, checked=False)
    finally:
        close_db(conn)


@router.get("/calendar", response_model=CheckinCalendarOut, summary="获取打卡日历数据")
def get_checkin_calendar(year: int = None, month: int = None):
    """获取指定年月的打卡日历数据"""
    today = date.today()
    year = year or today.year
    month = month or today.month

    conn = get_db()
    try:
        month_start = f"{year}-{month:02d}-01"
        if month == 12:
            month_end = f"{year + 1}-01-01"
        else:
            month_end = f"{year}-{month + 1:02d}-01"

        rows = conn.execute(
            "SELECT * FROM checkins WHERE checkin_date >= ? AND checkin_date < ?",
            (month_start, month_end),
        ).fetchall()

        checkin_map = {}
        for r in rows:
            checkin_map[r["checkin_date"]] = {
                "checked": bool(r["checked"]),
                "words_learned": r["words_learned"],
                "words_reviewed": r["words_reviewed"],
            }

        import calendar
        days_in_month = calendar.monthrange(year, month)[1]
        days = []
        for d in range(1, days_in_month + 1):
            ds = f"{year}-{month:02d}-{d:02d}"
            info = checkin_map.get(ds, {})
            days.append(CheckinCalendarDay(
                date=ds,
                checked=info.get("checked", False),
                words_learned=info.get("words_learned", 0),
                words_reviewed=info.get("words_reviewed", 0),
            ))

        return CheckinCalendarOut(year=year, month=month, days=days)
    finally:
        close_db(conn)


@router.get("/streak", response_model=CheckinStreakOut, summary="获取连续打卡天数")
def get_streak():
    """计算从今天往回连续打卡的天数"""
    conn = get_db()
    try:
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
        return CheckinStreakOut(streak=streak)
    finally:
        close_db(conn)
