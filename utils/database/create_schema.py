import sqlite3
from pathlib import Path

DB_PATH = Path("anime_database.db")

SCHEMA_SQL_TABLES = """
CREATE TABLE IF NOT EXISTS anime (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    season TEXT,
    episodes INTEGER,
    rating REAL,
    viewers_count INTEGER,
    genres_json TEXT,
    platforms_json TEXT,
    image_path TEXT,
    is_disliked INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_favorites (
    user_id TEXT NOT NULL,
    anime_id INTEGER NOT NULL,
    favorited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, anime_id),
    FOREIGN KEY (anime_id) REFERENCES anime(id)
);
"""

INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_anime_rating ON anime(rating DESC);
CREATE INDEX IF NOT EXISTS idx_anime_season ON anime(season);
CREATE INDEX IF NOT EXISTS idx_anime_viewers ON anime(viewers_count);
CREATE INDEX IF NOT EXISTS idx_anime_is_disliked ON anime(is_disliked);
CREATE INDEX IF NOT EXISTS idx_user_fav_user_time ON user_favorites(user_id, favorited_at DESC);
"""

def create_schema(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path.as_posix())
    try:
        cur = conn.cursor()
    # 可選 PRAGMA：提升寫入效能 / 讀取並發 (WAL)
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA synchronous=NORMAL;")
        # 先建立資料表 (不含索引)
        for statement in filter(None, (s.strip() for s in SCHEMA_SQL_TABLES.split(";"))):
            if statement:
                cur.execute(statement)

    # 遷移：若舊版資料表缺少新欄位則補上
        existing_cols = {r[1] for r in cur.execute("PRAGMA table_info(anime);").fetchall()}
        alter_actions = []
        if "image_path" not in existing_cols:
            alter_actions.append("ALTER TABLE anime ADD COLUMN image_path TEXT")
        if "is_disliked" not in existing_cols:
            alter_actions.append("ALTER TABLE anime ADD COLUMN is_disliked INTEGER DEFAULT 0")
        for stmt in alter_actions:
            cur.execute(stmt)

        if alter_actions:
            print(f"🔄 已新增欄位: {', '.join(a.split()[3] for a in alter_actions)}")

        # 再建立索引（確保欄位都存在）
        for statement in filter(None, (s.strip() for s in INDEX_SQL.split(";"))):
            if statement:
                cur.execute(statement)
        conn.commit()
        print("✅ 資料表已建立/確認 (anime)")
        print(f"📂 資料庫檔案: {db_path}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_schema()
