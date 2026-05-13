"""
SQLite 数据库初始化、连接管理
使用 Python 标准库 sqlite3，无需额外 ORM 依赖
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vocab_master.db")


def get_db() -> sqlite3.Connection:
    """获取数据库连接，启用外键约束和字典行工厂"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def close_db(conn: sqlite3.Connection):
    """关闭数据库连接"""
    if conn:
        conn.close()


# ==================== 建表 SQL ====================
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS word_books (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    icon        TEXT NOT NULL DEFAULT '📘',
    word_count  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS words (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id             TEXT NOT NULL,
    word                TEXT NOT NULL,
    phonetic            TEXT NOT NULL DEFAULT '',
    part_of_speech      TEXT NOT NULL DEFAULT '',
    definition_cn       TEXT NOT NULL DEFAULT '',
    example_sentence    TEXT NOT NULL DEFAULT '',
    example_translation TEXT NOT NULL DEFAULT '',
    sort_order          INTEGER NOT NULL DEFAULT 0,
    root_id             INTEGER,
    high_freq_defs      TEXT NOT NULL DEFAULT '',
    confusion_group     TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (book_id) REFERENCES word_books(id),
    FOREIGN KEY (root_id) REFERENCES word_roots(id)
);

CREATE TABLE IF NOT EXISTS word_roots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    root_text   TEXT NOT NULL,
    meaning     TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS word_progress (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id          INTEGER NOT NULL UNIQUE,
    status           TEXT NOT NULL DEFAULT 'new',   -- new / learning / familiar / mastered
    ease_factor      REAL NOT NULL DEFAULT 2.5,
    interval         INTEGER NOT NULL DEFAULT 0,
    repetitions      INTEGER NOT NULL DEFAULT 0,
    next_review_date TEXT,                           -- YYYY-MM-DD
    last_reviewed_at TEXT,
    learn_date       TEXT,                           -- YYYY-MM-DD 首次学习日期
    stage            INTEGER NOT NULL DEFAULT 1,     -- 1=初次学习, 2=间隔复习, 3=输出验证
    review_step      INTEGER NOT NULL DEFAULT 0,     -- 第几次间隔复习
    stage_1_done_at  TEXT,                           -- 第一轮完成时间
    stage_2_pass_count INTEGER NOT NULL DEFAULT 0,   -- 第二轮通过次数
    stage_3_attempts INTEGER NOT NULL DEFAULT 0,     -- 第三轮尝试次数
    stage_3_passed   INTEGER NOT NULL DEFAULT 0,     -- 第三轮是否通过 0/1
    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS checkins (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    checkin_date   TEXT NOT NULL UNIQUE,  -- YYYY-MM-DD
    words_learned  INTEGER NOT NULL DEFAULT 0,
    words_reviewed INTEGER NOT NULL DEFAULT 0,
    checked        INTEGER NOT NULL DEFAULT 0  -- 0=未打卡, 1=已打卡
);

CREATE TABLE IF NOT EXISTS study_records (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id    INTEGER NOT NULL,
    action     TEXT NOT NULL,    -- study / review
    rating     INTEGER NOT NULL, -- SM-2 quality 0-5
    created_at TEXT NOT NULL,
    FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS writing_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    original    TEXT NOT NULL,
    optimized   TEXT NOT NULL DEFAULT '',
    feedback    TEXT NOT NULL DEFAULT '',
    score       INTEGER NOT NULL DEFAULT 0,
    mode        TEXT NOT NULL DEFAULT 'text',
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    email           TEXT DEFAULT '',
    created_at      TEXT NOT NULL,
    last_login      TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- 索引：加速按词书查询单词、按状态查询进度
CREATE INDEX IF NOT EXISTS idx_words_book_id ON words(book_id);
CREATE INDEX IF NOT EXISTS idx_word_progress_status ON word_progress(status);
CREATE INDEX IF NOT EXISTS idx_word_progress_next_review ON word_progress(next_review_date);
CREATE INDEX IF NOT EXISTS idx_word_progress_stage ON word_progress(stage);
CREATE INDEX IF NOT EXISTS idx_checkins_date ON checkins(checkin_date);
CREATE INDEX IF NOT EXISTS idx_study_records_word_id ON study_records(word_id);
CREATE INDEX IF NOT EXISTS idx_words_root_id ON words(root_id);
CREATE INDEX IF NOT EXISTS idx_words_confusion_group ON words(confusion_group);
CREATE INDEX IF NOT EXISTS idx_writing_history_created ON writing_history(created_at);
"""


def init_tables():
    """创建所有表（如果不存在）"""
    conn = get_db()
    try:
        conn.executescript(CREATE_TABLES_SQL)
        conn.commit()
        # 迁移：为旧表添加新字段
        _migrate_tables(conn)
    finally:
        close_db(conn)


def _migrate_tables(conn):
    """为旧数据库添加新字段（如果不存在）"""
    # 检查 words 表是否有新字段
    words_cols = [row[1] for row in conn.execute("PRAGMA table_info(words)").fetchall()]
    if "root_id" not in words_cols:
        conn.execute("ALTER TABLE words ADD COLUMN root_id INTEGER")
    if "high_freq_defs" not in words_cols:
        conn.execute("ALTER TABLE words ADD COLUMN high_freq_defs TEXT NOT NULL DEFAULT ''")
    if "confusion_group" not in words_cols:
        conn.execute("ALTER TABLE words ADD COLUMN confusion_group TEXT NOT NULL DEFAULT ''")

    # 检查 word_progress 表是否有新字段
    wp_cols = [row[1] for row in conn.execute("PRAGMA table_info(word_progress)").fetchall()]
    if "stage" not in wp_cols:
        conn.execute("ALTER TABLE word_progress ADD COLUMN stage INTEGER NOT NULL DEFAULT 1")
    if "review_step" not in wp_cols:
        conn.execute("ALTER TABLE word_progress ADD COLUMN review_step INTEGER NOT NULL DEFAULT 0")
    if "stage_1_done_at" not in wp_cols:
        conn.execute("ALTER TABLE word_progress ADD COLUMN stage_1_done_at TEXT")
    if "stage_2_pass_count" not in wp_cols:
        conn.execute("ALTER TABLE word_progress ADD COLUMN stage_2_pass_count INTEGER NOT NULL DEFAULT 0")
    if "stage_3_attempts" not in wp_cols:
        conn.execute("ALTER TABLE word_progress ADD COLUMN stage_3_attempts INTEGER NOT NULL DEFAULT 0")
    if "stage_3_passed" not in wp_cols:
        conn.execute("ALTER TABLE word_progress ADD COLUMN stage_3_passed INTEGER NOT NULL DEFAULT 0")
    # WordReview 融合：标签、记忆历史、用户笔记
    if "flag" not in wp_cols:
        conn.execute("ALTER TABLE word_progress ADD COLUMN flag INTEGER NOT NULL DEFAULT 0")
    if "history" not in wp_cols:
        conn.execute("ALTER TABLE word_progress ADD COLUMN history TEXT NOT NULL DEFAULT ''")
    if "user_note" not in wp_cols:
        conn.execute("ALTER TABLE word_progress ADD COLUMN user_note TEXT NOT NULL DEFAULT ''")

    # WordReview 融合：words 表新增字段
    w_cols = [row[1] for row in conn.execute("PRAGMA table_info(words)").fetchall()]
    if "mnemonic" not in w_cols:
        conn.execute("ALTER TABLE words ADD COLUMN mnemonic TEXT NOT NULL DEFAULT ''")
    if "synonym" not in w_cols:
        conn.execute("ALTER TABLE words ADD COLUMN synonym TEXT NOT NULL DEFAULT ''")
    if "antonym" not in w_cols:
        conn.execute("ALTER TABLE words ADD COLUMN antonym TEXT NOT NULL DEFAULT ''")
    if "derivative" not in w_cols:
        conn.execute("ALTER TABLE words ADD COLUMN derivative TEXT NOT NULL DEFAULT ''")
    if "note" not in w_cols:
        conn.execute("ALTER TABLE words ADD COLUMN note TEXT NOT NULL DEFAULT ''")

    # 确保 settings 有 daily_new_words_limit
    row = conn.execute("SELECT value FROM settings WHERE key = 'daily_new_words_limit'").fetchone()
    if not row:
        daily_new = conn.execute("SELECT value FROM settings WHERE key = 'daily_new'").fetchone()
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('daily_new_words_limit', ?)",
            (daily_new["value"] if daily_new else "15",),
        )

    # 确保 settings 有 delay_hours（熬夜模式）
    row = conn.execute("SELECT value FROM settings WHERE key = 'delay_hours'").fetchone()
    if not row:
        conn.execute("INSERT INTO settings (key, value) VALUES ('delay_hours', '4')")

    conn.commit()
