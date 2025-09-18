import sqlite3
import json
import os

def create_anime_database():
    """建立動漫資料庫和資料表"""

    # 建立資料庫連接
    conn = sqlite3.connect('anime_database.db')
    cursor = conn.cursor()

    # 建立動漫資料表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anime (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            episodes INTEGER,
            duration_minutes INTEGER,
            genres TEXT,  -- JSON格式儲存: ["Action", "Comedy"]
            description TEXT,
            studio TEXT,
            source TEXT,  -- Manga, Light Novel 等
            demographic TEXT,  -- Shounen, Seinen 等
            rating REAL,
            member_count TEXT,  -- 如 "829K"
            season TEXT,  -- 如 "2024_fall"
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 建立索引以提升查詢效能
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rating ON anime(rating DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_season ON anime(season)')

    conn.commit()
    conn.close()

    print("✅ 資料庫建立成功！")
    print("📂 資料庫檔案: anime_database.db")

def get_anime_by_tags(tags_list, limit=10):
    """根據標籤查詢動漫"""
    conn = sqlite3.connect('anime_database.db')
    cursor = conn.cursor()

    # 建構查詢條件
    conditions = []
    for tag in tags_list:
        conditions.append(f"genres LIKE '%{tag}%'")

    where_clause = " AND ".join(conditions)

    query = f'''
        SELECT title, rating, genres, description
        FROM anime
        WHERE {where_clause}
        ORDER BY rating DESC
        LIMIT ?
    '''

    cursor.execute(query, (limit,))
    results = cursor.fetchall()

    conn.close()
    return results

def test_database():
    """測試資料庫功能"""
    # 測試資料
    test_anime = {
        'title': 'Dandadan',
        'episodes': 12,
        'duration_minutes': 23,
        'genres': '["Action", "Comedy", "Supernatural"]',
        'description': 'Test description',
        'studio': 'Science SARU',
        'rating': 8.47,
        'season': '2024_fall'
    }

    conn = sqlite3.connect('anime_database.db')
    cursor = conn.cursor()

    # 插入測試資料
    cursor.execute('''
        INSERT INTO anime (title, episodes, duration_minutes, genres, description, studio, rating, season)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        test_anime['title'],
        test_anime['episodes'],
        test_anime['duration_minutes'],
        test_anime['genres'],
        test_anime['description'],
        test_anime['studio'],
        test_anime['rating'],
        test_anime['season']
    ))

    conn.commit()

    # 測試查詢
    results = cursor.execute('SELECT * FROM anime WHERE title = ?', (test_anime['title'],)).fetchall()
    conn.close()

    if results:
        print("✅ 資料庫測試成功！")
        print(f"查詢結果: {results[0][1]} - 評分: {results[0][-3]}")
    else:
        print("❌ 資料庫測試失敗")

if __name__ == "__main__":
    create_anime_database()
    test_database()

    # 測試標籤查詢
    print("\n🔍 測試標籤查詢:")
    results = get_anime_by_tags(["Action", "Comedy"])
    for result in results:
        print(f"- {result[0]} (評分: {result[1]})")