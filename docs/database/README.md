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
| rating | REAL | 評分（空字串匯入時轉 NULL） |
| viewers_count | TEXT | 原始觀看/會員數字串（例：`487K`, `1.0M`；若需排序可另建 viewers_numeric） |
| genres_json | TEXT | 類型 JSON 陣列 ["Action","Comedy"] |
| platforms_json | TEXT | 播放平台 JSON 陣列 ["Netflix","Crunchyroll"] |
| image_path | TEXT | 圖片路徑或 URL |
| synopsis | TEXT | 劇情摘要（anime_story） |
| is_disliked | INTEGER | 0=正常 1=已標記不喜歡（推薦排除） |
| created_at | TIMESTAMP | 建立時間 |

> 變更：已移除 episodes；`viewers_count` 從 INTEGER 改為 TEXT；新增 `synopsis`。

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
- 自動補齊缺少欄位 (image_path, is_disliked, synopsis)
- 若偵測舊欄位 episodes 或 viewers_count 型別非 TEXT，會重建 anime 表並搬移資料

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


### 匯入資料
`utils/database/import_single_csv.py` 使用方式：
1. 直接執行（無參數）→ 掃描 `anime_data/data` 下所有 `*_with_image.csv` 依檔名推 season 匯入。
2. 判斷重複：以 `title` 為唯一，已存在則略過（不區分季節）。
3. 若 `anime_tag 3` 缺欄位，視為空不報錯。

### 查看總筆數 + 抽樣：
python -c "import sqlite3; c=sqlite3.connect('anime_database.db'); cur=c.cursor(); print('COUNT=', cur.execute('SELECT COUNT(*) FROM anime').fetchone()[0]); print(cur.execute('SELECT id,title,season FROM anime ORDER BY id DESC LIMIT 5').fetchall()); c.close()"

### 依季節統計：
python -c "import sqlite3; c=sqlite3.connect('anime_database.db'); cur=c.cursor(); print(cur.execute('SELECT season, COUNT(*) FROM anime GROUP BY season ORDER BY season').fetchall()); c.close()"

> 未來可選（尚未實作）： viewers_numeric、(title, season) UNIQUE（允許同名不同季重複紀錄）