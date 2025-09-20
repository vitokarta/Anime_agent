"""
動漫資料庫查詢範例
基本使用方法示範
"""

import sys
import os
from typing import List

# 引入資料庫模組
from utils.database.anime_queries import create_anime_db

def basic_title_search(query_title: str = "", season: str | None = None):
    """基本標題查詢範例

    參數:
        query_title: 查詢關鍵字 (可模糊匹配)
        season: 可選季度 (支援格式: 2024-1 / 2024_1 / 2024Q1 / 2024-Winter / 2024-Fall 等)
    """
    print("=== 基本標題查詢 ===")

    db = create_anime_db("anime_database.db")

    # 查詢 (若 season 為 None 則不限制季度)
    results = db.query_anime_by_title(query_title, season=season)

    for anime in results:
        print(anime)
    
    return results

    # season_info = f" (季度: {season})" if season else ""
    # print(f"查詢結果{season_info}:")
    # for i, anime in enumerate(results[:3], 1):
    #     print(f"  {i}. {anime['matched_title']} (相似度: {anime['similarity_score']:.3f}, {anime['season']})")

    # print()

def basic_tag_search(tags: List[str] | None = None, season: str | None = None):
    """基本標籤查詢範例

    參數:
        tags: 標籤清單 (例如 ["冒險", "奇幻"])。若為 None 則不過濾標籤。
        season: 可選季度 (支援格式同上)。
    """
    print("=== 基本標籤查詢 ===")

    db = create_anime_db("anime_database.db")

    # 基本查詢 (需用關鍵字參數 season=season，避免被當成 limit )
    results = db.query_anime_by_tags(tags or [], season=season, limit=5)

    for anime in results:
        print(anime)
    
    return results

    # season_info = f" (季度: {season})" if season else ""
    # print(f"推薦結果{season_info}:")
    # for i, anime in enumerate(results, 1):
    #     print(f"  {i}. {anime['title']}")
    #     print(f"     評分: {anime['base_rating']} + {anime['tag_bonus_score']} = {anime['total_score']}")
    #     print(f"     匹配標籤: {anime['matched_tags']}")
    #     print()

def recommend_similar_anime(anime_name: str, limit: int = 10, season: str | None = None):
    """相似動漫推薦範例"""
    print(f"=== 推薦與「{anime_name}」相似的動漫 ===")
    
    db = create_anime_db("anime_database.db")
    results = db.recommend_similar_anime(anime_name, limit=limit, season=season)
    
    for anime in results:
        print(anime)
    
    return results

## 原本的 season_search 功能已整合進 basic_title_search / basic_tag_search，故移除。

# def custom_parameters():
#     """自定義參數範例 (註解掉)"""
#     print("=== 自定義參數範例 ===")
    
#     db = create_anime_db("../anime_database.db")
    
#     # 調整標籤加分和評分門檻
#     db.set_tag_bonus_score(0.8)        # 每個標籤加0.8分
#     db.set_min_rating_threshold(7.5)   # 最低7.5分
    
#     results = db.query_anime_by_tags(["喜劇", "浪漫"], limit=3)
    
#     print("高品質喜劇浪漫動漫:")
#     for anime in results:
#         print(f"  - {anime['title']} (總分: {anime['total_score']:.1f})")
    
#     print()

def main():
    """執行基本範例"""
    import json
    with open("return.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    number = data.get("result")
    print(f"讀取到的結果: {number}",number[0],",",number[1])
    if number[0] == 1:
        # 1) 特定動漫推薦 1
        recommend_similar_anime(number[1])
    elif number[0] == 2:
        # 2) 標籤查詢 2
        basic_tag_search(number[1]) 
    elif number[0] == 3:
        # 3) 其他查詢 3
        basic_title_search(number[1])
    else:
        print("未知的查詢類型")
    # # 1) 不指定季度的標題查詢 3
    # basic_title_search("香格里拉·開拓異境")

    # # 2) 指定季度 (前端格式) 的標題查詢，例如 2024-4 對應 2024-Fall 3
    # basic_title_search("DAN DA DAN", season="2024-4")

    # 3) 相似動漫推薦, 1
    # recommend_similar_anime("DAN DA DAN")

    # # 4) 標籤 + 季度查詢 (可組合) 2
    # basic_tag_search(["奇幻"], season="2024-4")

    # # 5) 純標籤查詢 (無季度) 2
    #basic_tag_search(["奇幻", "冒險"]) 

if __name__ == "__main__":
    main()