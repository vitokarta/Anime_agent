"""
動漫資料庫查詢工具
提供基於標題和標籤的智能查詢功能

功能:
1. 智能標題匹配 - 處理季數變體、相似度計算
2. 標籤查詢 - 多標籤匹配、評分系統
3. 可調整參數 - 自定義加分係數和門檻值
"""

import sqlite3
import re
import json
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher

class AnimeDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # 可調整的標籤匹配加分係數
        self.TAG_BONUS_SCORE = 0.5
        # 最低評分門檻
        self.MIN_RATING_THRESHOLD = 2.0
    
    def get_connection(self):
        """建立資料庫連接"""
        return sqlite3.connect(self.db_path)
    
    def normalize_title(self, title: str) -> str:
        """
        標準化標題，處理常見的變體
        
        基於實際資料庫分析結果，處理各種季數表示方法：
        - 中文季數：第一季、第二季等
        - 英文季數：1st Season、2nd Season等
        - 其他格式：第二幕、第二季度、續篇等
        """
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
            r'\s*S\d+\s*$',
            r'\s*-.*-\s*$',  # 處理副標題
        ]
        
        base_title = normalized
        for pattern in patterns_to_remove:
            base_title = re.sub(pattern, '', base_title, flags=re.IGNORECASE)
        
        return base_title.strip()
    
    def calculate_similarity(self, query: str, db_title: str) -> float:
        """
        計算兩個標題的相似度
        
        使用多層次比較：
        1. 基本字串相似度
        2. 標準化後相似度
        3. 基礎標題相似度（去除季數）
        4. 特殊匹配規則加分
        """
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
                           limit: int = 1,
                           season: str = None) -> List[Dict]:
        """
        根據標題查詢動漫
        
        Args:
            query_title: 查詢的動漫標題
            similarity_threshold: 相似度門檻值 (0.0-1.0)
            limit: 返回結果數量限制
            season: 季度篩選 (可選)。接受格式:
                - 資料庫原生: 2024-Winter / 2024-Spring / 2024-Summer / 2024-Fall
                - 前端代碼: 2024-1 / 2024-2 / 2024-3 / 2024-4 (1=Winter)
                - 變體: 2024_1, 2024Q1
              若格式不合法則忽略 (不套用季度過濾)。
        
        Returns:
            匹配的動漫資料列表，按相似度排序
            
        Examples:
            # 查詢"歡迎來到實力至上主義的教室 第三季"
            # 能匹配到"歡迎來到實力至上主義的教室 3rd Season"
            results = db.query_anime_by_title("歡迎來到實力至上主義的教室 第三季")
            
            # 指定季度查詢
            results = db.query_anime_by_title("動漫名稱", season="2024-Fall")
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 處理季度代碼 (允許格式: 2024-1, 2024_1, 2024Q1, 2024-Winter, 2024-Winter 類型)
            db_season = None
            if season:
                db_season = self._convert_season_code(season)

            # 根據是否指定季度來構建查詢
            if db_season:
                cursor.execute("SELECT * FROM anime WHERE season = ?", (db_season,))
            else:
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
                    anime_dict['base_title'] = self.extract_base_title(db_title)
                    results.append(anime_dict)
            
            # 按相似度排序（降序）
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return results[:limit]
    
    def query_anime_by_tags(self, 
                           tags: List[str], 
                           limit: int = 10,
                           tag_bonus: float = None,
                           min_rating: float = None,
                           season: str = None) -> List[Dict]:
        """
        根據標籤查詢動漫
        
        Args:
            tags: 標籤列表（如：["動作", "冒險", "奇幻"]）
            limit: 返回結果數量限制
            tag_bonus: 每個匹配標籤的加分（可選，使用預設值）
            min_rating: 最低評分門檻（可選，使用預設值）
            season: 季度篩選 (可選)。接受格式同 query_anime_by_title 的 season 參數。
        
        Returns:
            推薦的動漫列表，按總分排序
            
        Examples:
            # 查詢動作冒險類動漫
            results = db.query_anime_by_tags(["動作", "冒險"], limit=5)
            
            # 自定義參數
            db.set_tag_bonus_score(0.8)  # 每個標籤加0.8分
            results = db.query_anime_by_tags(["學校", "戀愛"], min_rating=7.5)
            
            # 指定季度查詢
            results = db.query_anime_by_tags(["奇幻"], season="2024-Fall")
        """
        print("season")
        if tag_bonus is None:
            tag_bonus = self.TAG_BONUS_SCORE
        if min_rating is None:
            min_rating = self.MIN_RATING_THRESHOLD
        print("season")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 處理季度代碼
            db_season = None
            if season:
                db_season = self._convert_season_code(season)

            # 根據是否指定季度來構建查詢
            if db_season:
                cursor.execute("SELECT * FROM anime WHERE rating >= ? AND season = ?", (min_rating, db_season))
            else:
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
    
    def get_all_genres(self) -> List[str]:
        """獲取資料庫中所有的標籤類別"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT genres_json FROM anime WHERE genres_json IS NOT NULL")
            
            all_genres = set()
            for row in cursor.fetchall():
                try:
                    genres = json.loads(row[0])
                    all_genres.update(genres)
                except (json.JSONDecodeError, TypeError):
                    continue
            
            return sorted(list(all_genres))
    
    def get_anime_statistics(self) -> Dict:
        """獲取資料庫統計資訊"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 總數量
            cursor.execute("SELECT COUNT(*) FROM anime")
            total_count = cursor.fetchone()[0]
            
            # 評分統計
            cursor.execute("SELECT AVG(rating), MIN(rating), MAX(rating) FROM anime WHERE rating IS NOT NULL")
            rating_stats = cursor.fetchone()
            
            # 最高評分的動漫
            cursor.execute("SELECT title, rating FROM anime WHERE rating IS NOT NULL ORDER BY rating DESC LIMIT 5")
            top_rated = cursor.fetchall()
            
            return {
                'total_count': total_count,
                'avg_rating': rating_stats[0] if rating_stats[0] else 0,
                'min_rating': rating_stats[1] if rating_stats[1] else 0,
                'max_rating': rating_stats[2] if rating_stats[2] else 0,
                'top_rated': top_rated,
                'available_genres': self.get_all_genres()
            }
    
    def set_tag_bonus_score(self, bonus: float):
        """設置標籤匹配加分係數"""
        self.TAG_BONUS_SCORE = bonus
        return self
    
    def set_min_rating_threshold(self, threshold: float):
        """設置最低評分門檻"""
        self.MIN_RATING_THRESHOLD = threshold
        return self

    # ===== 新增: 季度代碼轉換 =====
    def _convert_season_code(self, code: str) -> Optional[str]:
        """處理前端傳入的季度代碼。

        前端現在直接傳送標準格式: 2025-Winter / 2025-Spring / 2025-Summer / 2025-Fall
        或者空值（不進行季度過濾）

        Args:
            code: 季度代碼字符串，可能為空

        Returns:
            str: 標準格式的季度代碼（如 '2025-Winter'）
            None: 當輸入為空或無效時，不進行季度過濾
        """
        if not code or not code.strip():
            return None
        
        raw = code.strip()

        # 檢查是否為標準格式: YYYY-Season
        if re.match(r"^\d{4}-(Winter|Spring|Summer|Fall)$", raw, re.IGNORECASE):
            # 標準化首字母大寫
            year, season_name = raw.split('-')
            season_name_cap = season_name.capitalize()
            return f"{year}-{season_name_cap}"

        # 如果不是標準格式，返回 None（不進行季度過濾）
        return None

    def recommend_similar_anime(self, anime_name: str, limit: int = 10, season: str = None) -> List[Dict]:
        """根據指定動漫推薦相似的動漫
        
        Args:
            anime_name: 要搜尋的動漫名稱
            limit: 推薦結果數量限制
            season: 可選季度過濾
            
        Returns:
            推薦的動漫列表 (按標籤匹配度排序)
            
        流程:
            1. 透過 query_anime_by_title 找到指定動漫
            2. 提取該動漫的 genres_json 作為標籤
            3. 使用這些標籤透過 query_anime_by_tags 找相似動漫
            4. 排除原本搜尋的動漫本身
        """
        # 步驟1: 先找到指定的動漫
        search_results = self.query_anime_by_title(anime_name, limit=1)
        if not search_results:
            return []
        
        target_anime = search_results[0]
        
        # 步驟2: 提取該動漫的標籤
        try:
            genres_json = target_anime.get('genres_json', '[]')
            anime_tags = json.loads(genres_json) if genres_json else []
        except (json.JSONDecodeError, TypeError):
            anime_tags = []
        
        if not anime_tags:
            return []
        # 步驟3: 使用標籤查詢相似動漫
        similar_results = self.query_anime_by_tags(
            tags=anime_tags, 
            limit=limit + 5,  # 多取一些，排除原動漫後可能不足
            season=season
        )
        #print(similar_results)
        
        # 步驟4: 排除原本的動漫 (比較 title 或 id)
        target_title = target_anime.get('title', '').lower()
        target_id = target_anime.get('id')
        
        filtered_results = []
        for anime in similar_results:
            # 排除相同的動漫
            if (anime.get('title', '').lower() != target_title and 
                anime.get('id') != target_id):
                filtered_results.append(anime)
                
            # 達到所需數量就停止
            if len(filtered_results) >= limit:
                break
        
        return filtered_results

# 便利函數
def create_anime_db(db_path: str = "anime_database.db") -> AnimeDatabase:
    """創建AnimeDatabase實例的便利函數"""
    return AnimeDatabase(db_path)