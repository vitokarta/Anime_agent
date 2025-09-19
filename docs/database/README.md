# 資料庫說明 (Database Guide)

## 檔案
- `anime_database.db` ：SQLite 資料庫檔案
- `utils/database/create_schema.py` ：建立 / 遷移資料表（可重複執行）

## 資料表：anime
| 欄位 | 型態 | 說明 |
|------|------|------|
| id | INTEGER PK | 主鍵，自動遞增 |
| title | TEXT | 動漫標題 |
| season | TEXT | 季節 (例：2024-Winter) |
| episodes | INTEGER | 集數 |
| rating | REAL | 評分 |
| viewers_count | INTEGER | 觀看/會員數 |
| genres_json | TEXT | 類型 JSON 陣列 ["Action","Comedy"] |
| platforms_json | TEXT | 播放平台 JSON 陣列 ["Netflix","Crunchyroll"] |
| image_path | TEXT | 圖片路徑或 URL |
| is_disliked | INTEGER | 0=正常 1=已標記不喜歡（推薦排除） |
| created_at | TIMESTAMP | 建立時間 |

## 索引 (Indexes)
- idx_anime_rating (rating DESC)
- idx_anime_season (season)
- idx_anime_viewers (viewers_count)
- idx_anime_is_disliked (is_disliked)

## 建立 / 遷移 Schema
```bash
python utils/database/create_schema.py
```
腳本會：
- 設定 WAL 模式
- 若無則建立資料表 / 索引
- 若缺少新欄位 (image_path, is_disliked) 會自動新增

## 標記為「不喜歡」
```sql
UPDATE anime SET is_disliked = 1 WHERE id = ?;
```

## 查詢（排除不喜歡）
```sql
SELECT * FROM anime
WHERE is_disliked = 0
ORDER BY rating DESC
LIMIT 20;
```

## 重置 is_disliked（單筆 / 全部）
單筆：
```sql
UPDATE anime SET is_disliked = 0 WHERE id = ?;
```
全部：
```sql
UPDATE anime SET is_disliked = 0;
```

## 重新建立資料庫（破壞性）
```bash
# 刪除檔案後重建
rm anime_database.db  # PowerShell: del anime_database.db
python utils/database/create_schema.py
```


### SQLite
進入 SQLite 命令列工具：
```bash
sqlite3 anime_database.db
```
常用指令：
```sql
.tables           -- 查看所有資料表
.schema anime     -- 查看 anime 表結構
SELECT * FROM anime LIMIT 5;   -- 查詢前五筆
.quit             -- 離開 CLI
```

## 資料表：user_favorites（使用者收藏）
一位使用者可收藏多部動畫；同一動畫不可重複收藏（複合主鍵）。

| 欄位 | 型態 | 說明 |
|------|------|------|
| user_id | TEXT | 使用者識別（可為帳號 / UUID） |
| anime_id | INTEGER | 對應 anime.id |
| favorited_at | TIMESTAMP | 收藏時間 |

索引 / 主鍵：`PRIMARY KEY (user_id, anime_id)`，並有 `idx_user_fav_user_time` (user_id, favorited_at DESC)。

### 新增收藏（忽略已存在）
```sql
INSERT OR IGNORE INTO user_favorites (user_id, anime_id)
VALUES ('u01', 5);
```

### 取消收藏
```sql
DELETE FROM user_favorites
WHERE user_id = 'u01' AND anime_id = 5;
```

### 查詢使用者收藏列表
```sql
SELECT a.id, a.title, a.rating, f.favorited_at
FROM user_favorites f
JOIN anime a ON a.id = f.anime_id
WHERE f.user_id = 'u01'
ORDER BY f.favorited_at DESC
LIMIT 50;
```

### 檢查是否已收藏
```sql
SELECT 1 FROM user_favorites
WHERE user_id = 'u01' AND anime_id = 5
LIMIT 1;
```

### 統計最常被收藏的前 10 動畫
```sql
SELECT a.id, a.title, COUNT(*) AS fav_count
FROM user_favorites f
JOIN anime a ON a.id = f.anime_id
GROUP BY a.id
ORDER BY fav_count DESC
LIMIT 10;
```
