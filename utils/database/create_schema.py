import sqlite3
from pathlib import Path

DB_PATH = Path("anime_database.db")

SCHEMA_SQL_TABLES = """
CREATE TABLE IF NOT EXISTS anime (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    season TEXT,  -- e.g. 2024-Winter / 2024-Spring / 2024-Summer / 2024-Fall
    rating REAL,  -- numeric rating (e.g. 7.95). Empty string -> NULL when ingesting
    viewers_count TEXT,  -- raw string like '487K', '1.0M' (keep original). Consider adding viewers_numeric later.
    genres_json TEXT, -- JSON array of unique tags
    platforms_json TEXT, -- JSON array of unique platforms
    image_path TEXT,
    synopsis TEXT,  -- anime_story / storyline summary
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
        existing_info = cur.execute("PRAGMA table_info(anime);").fetchall()
        existing_cols = {r[1] for r in existing_info}
        alter_actions = []
        # Add new columns if missing
        if "image_path" not in existing_cols:
            alter_actions.append("ALTER TABLE anime ADD COLUMN image_path TEXT")
        if "is_disliked" not in existing_cols:
            alter_actions.append("ALTER TABLE anime ADD COLUMN is_disliked INTEGER DEFAULT 0")
        if "synopsis" not in existing_cols:
            alter_actions.append("ALTER TABLE anime ADD COLUMN synopsis TEXT")

        # Handle legacy columns: remove episodes, change viewers_count INTEGER->TEXT if required.
        legacy_has_episodes = "episodes" in existing_cols
        viewers_col = next((r for r in existing_info if r[1] == "viewers_count"), None)
        needs_viewers_type_change = viewers_col and viewers_col[2].upper() != "TEXT"

        for stmt in alter_actions:
            cur.execute(stmt)

        # SQLite doesn't support DROP COLUMN directly (before v3.35). We'll perform a table rebuild if needed
        if legacy_has_episodes or needs_viewers_type_change:
            print("⚙️ 進行 anime 資料表結構重建以移除 episodes 或更新 viewers_count 型別 ...")
            cur.execute("PRAGMA foreign_keys=off;")
            # Rename old table
            cur.execute("ALTER TABLE anime RENAME TO anime_old;")
            # Recreate new schema (only anime table portion)
            cur.execute("""
                CREATE TABLE anime (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    season TEXT,
                    rating REAL,
                    viewers_count TEXT,
                    genres_json TEXT,
                    platforms_json TEXT,
                    image_path TEXT,
                    synopsis TEXT,
                    is_disliked INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # Copy data (excluding episodes; cast viewers_count)
            cur.execute("""
                INSERT INTO anime (id, title, season, rating, viewers_count, genres_json, platforms_json, image_path, synopsis, is_disliked, created_at)
                SELECT id, title, season, rating,
                       CAST(viewers_count AS TEXT),
                       genres_json, platforms_json, image_path,
                       COALESCE(synopsis, NULL),
                       is_disliked, created_at
                FROM anime_old;
            """)
            cur.execute("DROP TABLE anime_old;")
            cur.execute("PRAGMA foreign_keys=on;")
            print("✅ 已重建 anime 表 (移除 episodes / viewers_count 改為 TEXT)")

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
