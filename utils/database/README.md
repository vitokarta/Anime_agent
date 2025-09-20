# 動漫資料庫查詢工具使用指南

## 功能概述

這個工具提供了兩個主要的查詢功能：

### 1. 智能標題匹配 (`query_anime_by_title`)

**功能特點：**
- 處理各種季數表示格式的差異
- 智能相似度計算
- 模糊匹配能力

**解決的問題：**
- 資料庫中存儲：`歡迎來到實力至上主義的教室 3rd Season`
- 用戶查詢：`歡迎來到實力至上主義的教室 第三季`
- ✅ 能夠成功匹配！

**支援的季數格式：**
- 中文：第一季、第二季、第三季...
- 英文：1st Season、2nd Season、3rd Season...
- 其他：第二幕、第二季度、續篇等

### 2. 標籤推薦系統 (`query_anime_by_tags`)

**功能特點：**
- 多標籤匹配
- 智能評分系統：基礎評分 + 標籤加分
- 可調整參數
- 避免推薦低分作品

**評分計算：**
```
總分 = 基礎評分 + (匹配標籤數 × 標籤加分係數)
```

## 快速開始

```python
from utils.database.anime_queries import create_anime_db

# 初始化資料庫
db = create_anime_db("anime_database.db")

# 1. 標題查詢
results = db.query_anime_by_title("歡迎來到實力至上主義的教室 第三季")
for anime in results:
    print(f"{anime['matched_title']} (相似度: {anime['similarity_score']:.3f})")

# 2. 標籤查詢
results = db.query_anime_by_tags(["動作", "冒險", "奇幻"], limit=5)
for anime in results:
    print(f"{anime['title']} - 總分: {anime['total_score']:.1f}")
```

## 詳細使用說明

### 標題查詢

```python
# 基本查詢
results = db.query_anime_by_title("動漫名稱")

# 調整相似度門檻
results = db.query_anime_by_title("動漫名稱", similarity_threshold=0.7)

# 限制結果數量
results = db.query_anime_by_title("動漫名稱", limit=5)
```

### 標籤查詢

```python
# 基本查詢
results = db.query_anime_by_tags(["動作", "冒險"])

# 自定義參數
db.set_tag_bonus_score(0.8)        # 每個標籤加0.8分
db.set_min_rating_threshold(7.5)   # 最低7.5分
results = db.query_anime_by_tags(["動作", "冒險"], limit=10)

# 鏈式調用
results = db.set_tag_bonus_score(1.0).set_min_rating_threshold(8.0).query_anime_by_tags(["奇幻"])
```

### 可用標籤

目前資料庫支援的標籤類別：
- 動作、冒險、喜劇、奇幻
- 戲劇、浪漫、科幻、恐怖
- 校園、日常、後宮等

```python
# 獲取所有可用標籤
all_genres = db.get_all_genres()
print(all_genres)
```

## 參數調整指南

### 標籤加分係數 (TAG_BONUS_SCORE)
- **預設值：** 0.5
- **建議範圍：** 0.3 - 1.0
- **說明：** 每匹配一個標籤增加的分數

### 最低評分門檻 (MIN_RATING_THRESHOLD)
- **預設值：** 6.0
- **建議範圍：** 5.0 - 8.0
- **說明：** 只推薦高於此評分的動漫

### 相似度門檻 (similarity_threshold)
- **預設值：** 0.6
- **建議範圍：** 0.4 - 0.8
- **說明：** 標題匹配的最低相似度要求

## 返回結果格式

### 標題查詢結果
```python
{
    'id': 1,
    'title': '歡迎來到實力至上主義的教室 3rd Season',
    'rating': 8.5,
    'similarity_score': 1.0,
    'query_title': '歡迎來到實力至上主義的教室 第三季',
    'matched_title': '歡迎來到實力至上主義的教室 3rd Season',
    'base_title': '歡迎來到實力至上主義的教室',
    # ... 其他資料庫欄位
}
```

### 標籤查詢結果
```python
{
    'id': 1,
    'title': 'BLEACH 千年血戰篇 相剋譚',
    'rating': 8.67,
    'matched_tags': ['動作', '冒險', '奇幻'],
    'matched_tag_count': 3,
    'tag_bonus_score': 1.5,
    'total_score': 10.17,
    'base_rating': 8.67,
    'anime_genres': ['動作', '冒險', '奇幻'],
    # ... 其他資料庫欄位
}
```

## 實際使用案例

### 為LLM提供推薦資料
```python
def get_anime_recommendations(user_preferences):
    db = create_anime_db()
    
    # 根據用戶偏好調整參數
    if user_preferences.get('high_quality_only'):
        db.set_min_rating_threshold(8.0)
    
    if user_preferences.get('prefer_niche'):
        db.set_tag_bonus_score(1.2)
    
    # 獲取推薦
    results = db.query_anime_by_tags(
        user_preferences['favorite_genres'], 
        limit=10
    )
    
    return results
```

### 智能搜索功能
```python
def smart_search(query):
    db = create_anime_db()
    
    # 嘗試標題匹配
    title_results = db.query_anime_by_title(query, similarity_threshold=0.6)
    
    if title_results:
        return title_results
    
    # 如果沒有標題匹配，嘗試作為標籤查詢
    tag_results = db.query_anime_by_tags([query], limit=5)
    
    return tag_results
```

## 注意事項

1. **資料庫路徑：** 確保 `anime_database.db` 檔案路徑正確
2. **標籤格式：** 標籤存儲在 `genres_json` 欄位中，格式為JSON陣列
3. **效能考量：** 大量查詢時建議重用資料庫連接
4. **編碼問題：** 確保Python環境支援UTF-8編碼

## 測試與驗證

運行測試：
```bash
python utils/database/anime_queries.py
```

這將執行完整的功能測試，包括：
- 標題匹配測試
- 標籤查詢測試
- 資料庫統計展示