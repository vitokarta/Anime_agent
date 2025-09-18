import pandas as pd
import sqlite3
import json
import os
import glob

def clean_episodes(episodes_str):
    """清理集數資料"""
    if pd.isna(episodes_str) or episodes_str == '':
        return None

    # 提取數字部分 (如 "12 eps" -> 12)
    import re
    match = re.search(r'(\d+)', str(episodes_str))
    return int(match.group(1)) if match else None

def clean_duration(duration_str):
    """清理時長資料"""
    if pd.isna(duration_str) or duration_str == '':
        return None

    # 提取數字部分 (如 "23 min" -> 23)
    import re
    match = re.search(r'(\d+)', str(duration_str))
    return int(match.group(1)) if match else None

def clean_rating(rating_str):
    """清理評分資料"""
    if pd.isna(rating_str) or rating_str == '':
        return None

    try:
        return float(rating_str)
    except:
        return None

def extract_genres(row):
    """從行資料中提取所有類型標籤"""
    genres = []

    # 檢查所有可能的類型欄位 (根據你的CSV結構調整)
    genre_columns = ['genre', 'genre 2', 'genre 3']

    for col in genre_columns:
        if col in row and pd.notna(row[col]) and row[col].strip():
            genres.append(row[col].strip())

    # 檢查 demographic 欄位
    if 'Demographic' in row and pd.notna(row['Demographic']) and row['Demographic'].strip():
        genres.append(row['Demographic'].strip())

    return json.dumps(genres) if genres else json.dumps([])

def import_csv_to_database(csv_file_path, season_name):
    """將CSV檔案匯入資料庫"""

    try:
        # 讀取CSV檔案
        df = pd.read_csv(csv_file_path)
        print(f"📂 正在處理: {csv_file_path}")
        print(f"📊 資料筆數: {len(df)}")

        # 連接資料庫
        conn = sqlite3.connect('anime_database.db')
        cursor = conn.cursor()

        imported_count = 0

        for index, row in df.iterrows():
            try:
                # 檢查必要欄位
                if pd.isna(row.get('link-title', '')) or row.get('link-title', '').strip() == '':
                    continue

                # 準備資料
                title = row['link-title'].strip()
                episodes = clean_episodes(row.get('item 3', ''))
                duration = clean_duration(row.get('item 4', ''))
                genres = extract_genres(row)
                description = row.get('preline', '').strip() if pd.notna(row.get('preline', '')) else ''
                studio = row.get('item 5', '').strip() if pd.notna(row.get('item 5', '')) else ''
                source = row.get('item 6', '').strip() if pd.notna(row.get('item 6', '')) else ''
                demographic = row.get('item 7', '').strip() if pd.notna(row.get('item 7', '')) else ''
                rating = clean_rating(row.get('item 8', ''))
                member_count = row.get('item 9', '').strip() if pd.notna(row.get('item 9', '')) else ''

                # 插入資料
                cursor.execute('''
                    INSERT OR REPLACE INTO anime
                    (title, episodes, duration_minutes, genres, description, studio, source, demographic, rating, member_count, season)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    title, episodes, duration, genres, description,
                    studio, source, demographic, rating, member_count, season_name
                ))

                imported_count += 1

            except Exception as e:
                print(f"⚠️  第 {index+1} 筆資料處理失敗: {e}")
                continue

        conn.commit()
        conn.close()

        print(f"✅ 成功匯入 {imported_count} 筆動漫資料")
        return imported_count

    except Exception as e:
        print(f"❌ 檔案處理失敗: {e}")
        return 0

def import_all_csv_files():
    """匯入所有CSV檔案"""

    # 建立資料庫
    from create_database import create_anime_database
    create_anime_database()

    csv_files = glob.glob('raw_data/*.csv')
    total_imported = 0

    for csv_file in csv_files:
        # 從檔案名取得季節資訊
        season_name = os.path.basename(csv_file).replace('.csv', '')
        count = import_csv_to_database(csv_file, season_name)
        total_imported += count

    print(f"\n🎉 總共匯入 {total_imported} 筆動漫資料")

    # 顯示統計資訊
    show_database_stats()

def show_database_stats():
    """顯示資料庫統計資訊"""
    conn = sqlite3.connect('anime_database.db')
    cursor = conn.cursor()

    # 總數量
    total_count = cursor.execute('SELECT COUNT(*) FROM anime').fetchone()[0]
    print(f"📊 資料庫總動漫數量: {total_count}")

    # 按季節統計
    season_stats = cursor.execute('''
        SELECT season, COUNT(*)
        FROM anime
        GROUP BY season
        ORDER BY season
    ''').fetchall()

    print("\n📅 各季節統計:")
    for season, count in season_stats:
        print(f"  - {season}: {count} 部")

    # 評分統計
    rating_stats = cursor.execute('''
        SELECT AVG(rating), MIN(rating), MAX(rating), COUNT(rating)
        FROM anime
        WHERE rating IS NOT NULL
    ''').fetchone()

    if rating_stats[3] > 0:
        print(f"\n⭐ 評分統計:")
        print(f"  - 平均評分: {rating_stats[0]:.2f}")
        print(f"  - 最低評分: {rating_stats[1]}")
        print(f"  - 最高評分: {rating_stats[2]}")
        print(f"  - 有評分動漫: {rating_stats[3]} 部")

    conn.close()

if __name__ == "__main__":
    import_all_csv_files()