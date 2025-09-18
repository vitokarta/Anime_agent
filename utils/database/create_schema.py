import sqlite3
from pathlib import Path

DB_PATH = Path("anime_database.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS anime (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    season TEXT,                       -- 季節 (例: 2024-Winter)
    episodes INTEGER,                  -- 集數
    rating REAL,                       -- 評分 (例: 8.72)
    viewers_count INTEGER,             -- 觀看 / 會員數
    genres_json TEXT,                  -- 類型 JSON 陣列 ["Action","Comedy"]
    platforms_json TEXT,               -- 平台 JSON 陣列 ["Netflix","Crunchyroll"]
    image_path TEXT,                   -- 圖片路徑或 URL
    is_disliked INTEGER DEFAULT 0,     -- 0=正常 1=不喜歡 (排除推薦)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_anime_rating ON anime(rating DESC);
CREATE INDEX IF NOT EXISTS idx_anime_season ON anime(season);
CREATE INDEX IF NOT EXISTS idx_anime_viewers ON anime(viewers_count);
CREATE INDEX IF NOT EXISTS idx_anime_is_disliked ON anime(is_disliked);
"""

def create_schema(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path.as_posix())
    try:
        cur = conn.cursor()
    # 可選 PRAGMA：提升寫入效能 / 讀取並發 (WAL)
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("PRAGMA synchronous=NORMAL;")
        for statement in filter(None, (s.strip() for s in SCHEMA_SQL.split(";"))):
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
        conn.commit()
        print("✅ 資料表已建立/確認 (anime)")
        print(f"📂 資料庫檔案: {db_path}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_schema()
