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
