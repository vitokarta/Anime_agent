#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 動漫選擇器
使用本地 LLM 從推薦結果中選擇最符合用戶描述的動漫
"""

import os
import json
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class LLMAnimeSelector:
    def __init__(self):
        # 從環境變數獲取設定
        self.base_url = os.getenv("LEMONADE_BASE_URL", "http://192.168.1.10:8000/api/v1")
        self.api_key = os.getenv("LEMONADE_API_KEY", "lemonade")
        self.model = os.getenv("DEFAULT_MODEL", "Qwen3-14B-GGUF")
        
        # LLM API 端點
        self.chat_url = f"{self.base_url}/chat/completions"
        
    def format_anime_for_llm(self, anime_list: List[Dict]) -> str:
        """將動漫資料格式化為 LLM 可讀的文字"""
        formatted_text = "以下是候選的動漫列表：\n\n"
        
        for i, anime in enumerate(anime_list, 1):
            title = anime.get('title', '未知標題')
            synopsis = anime.get('synopsis', '暫無描述')
            genres = anime.get('anime_genres', anime.get('genres_json', []))
            rating = anime.get('rating', 0)
            season = anime.get('season', '未知季度')
            
            # 處理 genres 如果是 JSON 字符串
            if isinstance(genres, str):
                try:
                    genres = json.loads(genres)
                except:
                    genres = genres.split(',') if genres else []
            
            formatted_text += f"{i}. 標題：{title}\n"
            formatted_text += f"   類型：{', '.join(genres) if genres else '未分類'}\n"
            formatted_text += f"   評分：{rating}\n"
            formatted_text += f"   季度：{season}\n"
            if synopsis and synopsis != '暫無描述':
                formatted_text += f"   簡介：{synopsis}\n"
            formatted_text += "\n"
            
        return formatted_text
    
    def call_llm(self, user_description: str, anime_list: List[Dict], count: int) -> tuple[List[int], List[str]]:
        """呼叫本地 LLM 選擇最符合的動漫並生成推薦理由"""
        
        # 格式化動漫資料
        anime_text = self.format_anime_for_llm(anime_list)
        
        # 構建提示詞
        prompt = f"""用戶描述：{user_description}

{anime_text}

請根據用戶的描述，從上述動漫列表中選擇最符合的 {count} 部動漫。
請考慮以下因素：
1. 動漫類型是否符合用戶需求
2. 劇情內容是否與用戶描述相關
3. 評分和品質
4. 用戶可能的偏好

請按以下格式回覆，每行一個結果：
編號:理由
編號:理由

例如：
1:這部動漫的奇幻元素和冒險劇情非常符合您的需求
3:高評分作品，劇情精彩且製作精良
5:同類型中的經典作品，值得推薦

如果候選動漫數量少於 {count} 部，請返回所有候選動漫的編號和理由。
"""

        try:
            # 準備請求資料
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 300
            }
            
            print(f"呼叫本地 LLM: {self.chat_url}")
            print(f"使用模型: {self.model}")
            
            # 發送請求
            response = requests.post(
                self.chat_url, 
                headers=headers, 
                json=data, 
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                
                print(f"LLM 回應：{llm_response}")
                
                # 解析 LLM 回應
                selected_indices, reasons = self.parse_llm_response_with_reasons(llm_response, len(anime_list))
                return selected_indices, reasons
                
            else:
                print(f"LLM API 請求失敗: {response.status_code}, {response.text}")
                return self.fallback_selection(anime_list, count), []
                
        except Exception as e:
            print(f"呼叫 LLM 時發生錯誤: {str(e)}")
            return self.fallback_selection(anime_list, count), []
    
    def parse_llm_response_with_reasons(self, response: str, max_index: int) -> tuple[List[int], List[str]]:
        """解析 LLM 回應，提取動漫編號和推薦理由"""
        try:
            indices = []
            reasons = []
            
            for line in response.strip().split('\n'):
                line = line.strip()
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        try:
                            num = int(parts[0].strip())
                            reason = parts[1].strip()
                            if 1 <= num <= max_index:
                                indices.append(num - 1)  # 轉換為 0-based 索引
                                reasons.append(reason)
                        except ValueError:
                            continue
            
            # 如果解析失敗，至少返回第一個
            if not indices:
                return [0], ["為您精心挑選的優質作品"]
                
            return indices, reasons
            
        except Exception as e:
            print(f"解析 LLM 回應時發生錯誤: {str(e)}")
            return [0], ["為您精心挑選的優質作品"]
    
    def parse_llm_response(self, response: str, max_index: int) -> List[int]:
        """解析 LLM 回應，提取動漫編號"""
        try:
            # 提取數字
            numbers = []
            for part in response.replace('，', ',').split(','):
                part = part.strip()
                if part.isdigit():
                    num = int(part)
                    if 1 <= num <= max_index:
                        numbers.append(num - 1)  # 轉換為 0-based 索引
            
            return numbers if numbers else [0]  # 如果解析失敗，至少返回第一個
            
        except Exception as e:
            print(f"解析 LLM 回應時發生錯誤: {str(e)}")
            return [0]  # 返回第一個作為備選
    
    def fallback_selection(self, anime_list: List[Dict], count: int) -> List[int]:
        """備選方案：按評分排序選擇"""
        print("使用備選方案：按評分排序選擇動漫")
        
        # 按評分排序
        sorted_anime = sorted(
            enumerate(anime_list), 
            key=lambda x: x[1].get('total_score', x[1].get('rating', 0)), 
            reverse=True
        )
        
        # 返回前 count 個的索引
        return [i for i, _ in sorted_anime[:count]]
    
    def select_anime(self, user_description: str, anime_list: List[Dict], count: int) -> tuple[List[Dict], List[str]]:
        """
        從動漫列表中選擇最符合用戶描述的動漫
        
        Args:
            user_description: 用戶的描述文字
            anime_list: 候選動漫列表
            count: 需要返回的動漫數量
            
        Returns:
            tuple: (選中的動漫列表, 對應的推薦理由列表)
        """
        
        if not anime_list:
            return [], []
        
        # 如果候選動漫數量不超過需求數量，直接返回全部
        if len(anime_list) <= count:
            default_reasons = ["為您精心挑選的優質作品"] * len(anime_list)
            return anime_list, default_reasons
        
        print(f"從 {len(anime_list)} 部候選動漫中選擇 {count} 部")
        
        # 使用 LLM 選擇
        selected_indices, reasons = self.call_llm(user_description, anime_list, count)
        
        # 根據索引提取選中的動漫
        selected_anime = []
        final_reasons = []
        
        for i, index in enumerate(selected_indices[:count]):
            if 0 <= index < len(anime_list):
                selected_anime.append(anime_list[index])
                # 使用對應的理由，如果沒有則使用默認理由
                if i < len(reasons):
                    final_reasons.append(reasons[i])
                else:
                    final_reasons.append("為您精心挑選的優質作品")
        
        # 如果選中的數量不足，用評分高的補足
        if len(selected_anime) < count:
            remaining_count = count - len(selected_anime)
            selected_ids = {anime.get('id') for anime in selected_anime}
            
            # 按評分排序剩餘的動漫
            remaining_anime = [
                anime for anime in anime_list 
                if anime.get('id') not in selected_ids
            ]
            remaining_anime.sort(
                key=lambda x: x.get('total_score', x.get('rating', 0)), 
                reverse=True
            )
            
            selected_anime.extend(remaining_anime[:remaining_count])
            # 為補足的動漫添加默認理由
            final_reasons.extend(["高評分優質作品推薦"] * remaining_count)
        
        print(f"最終選擇了 {len(selected_anime)} 部動漫")
        return selected_anime, final_reasons

def create_llm_selector() -> LLMAnimeSelector:
    """創建 LLM 動漫選擇器實例"""
    return LLMAnimeSelector()

# 使用範例
if __name__ == "__main__":
    # 測試用範例資料
    sample_anime_list = [
        {
            'id': 1,
            'title': '測試動漫1',
            'synopsis': '這是一部關於冒險的動漫',
            'anime_genres': ['冒險', '奇幻'],
            'rating': 8.5,
            'season': '2024-Spring'
        },
        {
            'id': 2,
            'title': '測試動漫2',
            'synopsis': '這是一部關於戀愛的動漫',
            'anime_genres': ['戀愛', '校園'],
            'rating': 7.8,
            'season': '2024-Summer'
        }
    ]
    
    selector = create_llm_selector()
    result = selector.select_anime("我想看冒險類型的動漫", sample_anime_list, 1)
    print("選擇結果:", result)