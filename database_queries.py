import sqlite3
import re
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher

class AnimeDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # 可調整的標籤匹配加分係數
        self.TAG_BONUS_SCORE = 0.5
        # 最低評分門檻
        self.MIN_RATING_THRESHOLD = 6.0
    
    def get_connection(self):
        """建立資料庫連接"""
        return sqlite3.connect(self.db_path)
    
    def normalize_title(self, title: str) -> str:
        """標準化標題，處理常見的變體"""
        if not title:
            return ""
        
        # 移除多餘空格
        title = re.sub(r'\s+', ' ', title.strip())
        
        # 處理季數的各種表示方法 - 根據實際資料庫內容擴展
        season_mappings = {
            # 中文數字季數
            '第一季': '第1季',
            '第二季': '第2季', 
            '第三季': '第3季',
            '第四季': '第4季',
            '第五季': '第5季',
            '第六季': '第6季',
            '第七季': '第7季',
            '第八季': '第8季',
            '第九季': '第9季',
            '第十季': '第10季',
            
            # 英文季數轉換
            '1st Season': '第1季',
            '2nd Season': '第2季',
            '3rd Season': '第3季',
            '4th Season': '第4季',
            '5th Season': '第5季',
            
            # 其他格式
            '第二幕': '第2季',
            '第三幕': '第3季',
            '第二季度': '第2季',
            '第三季度': '第3季',
            '第二部份': '第2季',
            '第三部份': '第3季',
            '續篇': '第2季',
            
            # 簡化格式
            'Season 1': '第1季',
            'Season 2': '第2季',
            'Season 3': '第3季',
            'S1': '第1季',
            'S2': '第2季',
            'S3': '第3季',
        }
        
        normalized_title = title
        for old_format, new_format in season_mappings.items():
            normalized_title = normalized_title.replace(old_format, new_format)
        
        return normalized_title
    
    def extract_base_title(self, title: str) -> str:
        """提取動漫的基礎標題（去除季數等後綴）"""
        normalized = self.normalize_title(title)
        
        # 移除季數相關的後綴
        patterns_to_remove = [
            r'\s*第\d+季\s*$',
            r'\s*\d+(st|nd|rd|th)\s+Season\s*$',
            r'\s*Season\s+\d+\s*$',
            r'\s*第[一二三四五六七八九十]+季\s*$',
            r'\s*第\d+季度\s*$',
            r'\s*第\d+部份?\s*$',
            r'\s*續篇\s*$',
            r'\s*S\d+\s*$'
        ]
        
        base_title = normalized
        for pattern in patterns_to_remove:
            base_title = re.sub(pattern, '', base_title, flags=re.IGNORECASE)
        
        return base_title.strip()
    
    def calculate_similarity(self, query: str, db_title: str) -> float:
        """計算兩個標題的相似度"""
        # 基本字串相似度
        basic_similarity = SequenceMatcher(None, query.lower(), db_title.lower()).ratio()
        
        # 標準化後的相似度
        norm_query = self.normalize_title(query)
        norm_db_title = self.normalize_title(db_title)
        normalized_similarity = SequenceMatcher(None, norm_query.lower(), norm_db_title.lower()).ratio()
        
        # 基礎標題相似度（去除季數）
        base_query = self.extract_base_title(query)
        base_db_title = self.extract_base_title(db_title)
        base_similarity = SequenceMatcher(None, base_query.lower(), base_db_title.lower()).ratio()
        
        # 特殊匹配規則
        bonus_score = 0
        
        # 如果基礎標題完全匹配，給予高分
        if base_query.lower() == base_db_title.lower() and base_query:
            bonus_score += 0.3
        
        # 如果其中一個包含另一個，給予加分
        if (base_query.lower() in base_db_title.lower() or 
            base_db_title.lower() in base_query.lower()) and len(base_query) > 2:
            bonus_score += 0.2
        
        # 如果標準化後完全匹配
        if norm_query.lower() == norm_db_title.lower():
            return 1.0
        
        # 綜合相似度計算
        final_similarity = max(basic_similarity, normalized_similarity, base_similarity) + bonus_score
        
        return min(1.0, final_similarity)
    
    def query_anime_by_title(self, query_title: str, 
                           similarity_threshold: float = 0.6,
                           limit: int = 10) -> List[Dict]:
        """
        根據標題查詢動漫
        
        Args:
            query_title: 查詢的動漫標題
            similarity_threshold: 相似度門檻值 (0.0-1.0)
            limit: 返回結果數量限制
        
        Returns:
            匹配的動漫資料列表，按相似度排序
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 獲取所有動漫
            cursor.execute("SELECT * FROM anime")
            all_anime = cursor.fetchall()
            
            # 獲取欄位名稱
            column_names = [description[0] for description in cursor.description]
            
            # 計算相似度並篩選
            results = []
            for anime_row in all_anime:
                anime_dict = dict(zip(column_names, anime_row))
                db_title = anime_dict.get('title', '')
                
                similarity = self.calculate_similarity(query_title, db_title)
                
                if similarity >= similarity_threshold:
                    anime_dict['similarity_score'] = similarity
                    anime_dict['query_title'] = query_title
                    anime_dict['matched_title'] = db_title
                    results.append(anime_dict)
            
            # 按相似度排序（降序）
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return results[:limit]
    
    def query_anime_by_tags(self, 
                           tags: List[str], 
                           limit: int = 10,
                           tag_bonus: float = None,
                           min_rating: float = None) -> List[Dict]:
        """
        根據標籤查詢動漫
        
        Args:
            tags: 標籤列表
            limit: 返回結果數量限制
            tag_bonus: 每個匹配標籤的加分（可選，使用預設值）
            min_rating: 最低評分門檻（可選，使用預設值）
        
        Returns:
            推薦的動漫列表，按總分排序
        """
        import json
        
        if tag_bonus is None:
            tag_bonus = self.TAG_BONUS_SCORE
        if min_rating is None:
            min_rating = self.MIN_RATING_THRESHOLD
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 基本查詢：評分高於門檻
            cursor.execute("SELECT * FROM anime WHERE rating >= ?", (min_rating,))
            all_qualified_anime = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            
            # 計算每部動漫的總分
            results = []
            for anime_row in all_qualified_anime:
                anime_dict = dict(zip(column_names, anime_row))
                
                # 解析標籤JSON
                genres_json = anime_dict.get('genres_json', '[]')
                try:
                    anime_genres = json.loads(genres_json) if genres_json else []
                    # 轉換為小寫以便比較
                    anime_genres_lower = [genre.lower() for genre in anime_genres]
                except (json.JSONDecodeError, TypeError):
                    anime_genres_lower = []
                
                # 計算匹配的標籤數量
                matched_tags = 0
                matched_tag_list = []
                
                for tag in tags:
                    if tag.lower() in anime_genres_lower:
                        matched_tags += 1
                        matched_tag_list.append(tag)
                
                # 只保留至少匹配一個標籤的動漫
                if matched_tags > 0:
                    # 計算總分：基礎評分 + 標籤加分
                    base_rating = anime_dict.get('rating', 0)
                    tag_bonus_score = matched_tags * tag_bonus
                    total_score = base_rating + tag_bonus_score
                    
                    anime_dict['matched_tags'] = matched_tag_list
                    anime_dict['matched_tag_count'] = matched_tags
                    anime_dict['tag_bonus_score'] = tag_bonus_score
                    anime_dict['total_score'] = total_score
                    anime_dict['base_rating'] = base_rating
                    anime_dict['anime_genres'] = anime_genres  # 原始標籤列表
                    results.append(anime_dict)
            
            # 按總分排序（降序）
            results.sort(key=lambda x: x['total_score'], reverse=True)
            
            return results[:limit]
    
    def set_tag_bonus_score(self, bonus: float):
        """設置標籤匹配加分係數"""
        self.TAG_BONUS_SCORE = bonus
    
    def set_min_rating_threshold(self, threshold: float):
        """設置最低評分門檻"""
        self.MIN_RATING_THRESHOLD = threshold

# 測試函數
def test_title_matching():
    """測試標題匹配功能"""
    db = AnimeDatabase("anime_database.db")
    
    # 測試案例
    test_cases = [
        "歡迎來到實力至上主義的教室 第三季",
        "歡迎來到實力至上主義的教室",
        "DAN DA DAN",
        "我內心的糟糕念頭",
        "迷宮飯",
        "我獨自升級"
    ]
    
    print("=== 標題匹配測試 ===")
    for query in test_cases:
        print(f"\n查詢: '{query}'")
        results = db.query_anime_by_title(query, similarity_threshold=0.5, limit=3)
        
        if results:
            for i, anime in enumerate(results, 1):
                print(f"  {i}. {anime['matched_title']} (相似度: {anime['similarity_score']:.3f})")
        else:
            print("  未找到匹配結果")

def test_tag_matching():
    """測試標籤匹配功能"""
    db = AnimeDatabase("anime_database.db")
    
    # 設置參數
    db.set_tag_bonus_score(0.8)
    db.set_min_rating_threshold(7.0)
    
    print("\n=== 標籤匹配測試 ===")
    test_tags = ["動作", "冒險", "奇幻"]
    
    results = db.query_anime_by_tags(test_tags, limit=5)
    
    if results:
        for i, anime in enumerate(results, 1):
            print(f"{i}. {anime['title']}")
            print(f"   基礎評分: {anime['base_rating']}")
            print(f"   匹配標籤: {anime['matched_tags']} ({anime['matched_tag_count']}個)")
            print(f"   總分: {anime['total_score']:.1f}")
            print()
    else:
        print("未找到匹配結果")

if __name__ == "__main__":
    test_title_matching()
    test_tag_matching()