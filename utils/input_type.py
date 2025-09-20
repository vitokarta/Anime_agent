import os
import sys
import sqlite3
import json
from difflib import SequenceMatcher
from openai import OpenAI

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入分类函数
from utils.classify_genre import classify_by_features


def get_all_genres(db_path):
    """從資料庫取得所有類別"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT genres_json FROM anime")
    genres = set()
    for row in cursor.fetchall():
        genre_list = json.loads(row[0])
        genres.update(genre_list)
    conn.close()
    return list(genres)

def get_anime_genres(db_path, anime_name):
    """從資料庫中查找特定動漫的類別"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # 使用模糊匹配來查找動漫
    cursor.execute("SELECT title, genres_json FROM anime WHERE title LIKE ?", (f"%{anime_name}%",))
    results = cursor.fetchall()
    conn.close()
    
    if results:
        # 找到完全匹配的
        exact_match = next((r for r in results if r[0].lower() == anime_name.lower()), None)
        if exact_match:
            return json.loads(exact_match[1]), exact_match[0]
        # 否則返回第一個結果
        return json.loads(results[0][1]), results[0][0]
    return None, None


def classify_request_type(user_input, max_retries=3):
    """分類用戶請求類型
    返回: 
        tuple: (類型(1,2,3), 處理後的結果)
        類型1: 特定動漫推薦
        類型2: 類別或特徵推薦
        類型3: 無法處理或其他
    """
    try:
        from models.client import lemonade
        import time
        
        prompt = (
            f"請分析以下用戶輸入屬於哪種類型（只返回數字1,2,3）：\n"
            f"輸入文本：{user_input}\n\n"
            f"判斷規則：\n"
            f"1: 提到特定動漫名稱的推薦請求（例如：有沒有和火影忍者相似的動漫）\n"
            f"2: 提到動漫類別、特徵、題材的推薦請求 （例如：有沒有推薦的XX類型番劇）\n"
            f"3: 其他或無法判斷的請求\n\n"
            f"請只返回一個數字(1,2,3)，不要有任何其他文字"
        )
        
        # 使用本地 LLM 進行分類，添加重試機制
        for attempt in range(max_retries):
            try:
                print(f"嘗試進行請求類型判斷... (第 {attempt + 1} 次)")
                response = lemonade.simple_chat(prompt)
                request_type = int(response.strip())
                if request_type not in [1, 2, 3]:
                    print(f"LLM 返回了無效的類型：{response}")
                    request_type = 3
                break  # 成功獲得回應，跳出重試循環
            except Exception as e:
                if "timeout" in str(e).lower() and attempt < max_retries - 1:
                    print(f"請求超時，等待1秒後重試... ({attempt + 1}/{max_retries})")
                    time.sleep(1)
                    continue
                print(f"LLM 請求失敗：{str(e)}")
                request_type = 3
                break
        print(f"判斷結果為類型 {request_type}")
        # 根據類型進行處理
        if request_type == 1:
            print("屬於類型1：正在進行特定動漫名稱分析...")
            # 查找提到的動漫名稱
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'anime_database.db')
            anime_name = None
            
            # 再次使用 LLM 提取動漫名稱
            name_prompt = (
                f"請從以下文本中提取動漫名稱（只返回名稱本身，不要有其他文字）：\n"
                f"{user_input}"
            )
            
            # 添加重試機制
            for attempt in range(max_retries):
                try:
                    print(f"嘗試提取動漫名稱... (第 {attempt + 1} 次)")
                    anime_name = lemonade.simple_chat(name_prompt).strip()
                    print(f"提取到的動漫名稱：{anime_name}")
                    break
                except Exception as e:
                    if "timeout" in str(e).lower() and attempt < max_retries - 1:
                        print(f"提取名稱超時，等待1秒後重試... ({attempt + 1}/{max_retries})")
                        time.sleep(1)
                        continue
                    print(f"提取動漫名稱失敗：{str(e)}")
                    return (3, f"類型3：{user_input} (提取名稱失敗)")
                
            # 驗證動漫是否在資料庫中
            reference_genres, found_title = get_anime_genres(db_path, anime_name)
            if found_title:
                return (1, f"類型1：{found_title}")
            else:
                return (3, f"類型3：{user_input}")
                
        elif request_type == 2:
            print("屬於類型2：正在進行類別或特徵分析...")
            # 使用 classify_by_features 进行类别分类
            print("正在進行類別特徵分析...")
            classification_result = classify_by_features(user_input)
        
        else:
            print("屬於類型3：無法處理或其他請求")    
            
        return (3, f"類型3：{user_input}")
            
    except Exception as e:
        print(f"分類過程發生錯誤：{str(e)}")
        return (3, f"類型3：{user_input}")

def classify_anime_genre(user_input):
    """主要分類函數"""
    try:
        print(f"\n分析「{user_input}」...")
        
        # 先判斷請求類型
        request_type, processed_result = classify_request_type(user_input)
        print(processed_result)
        
        # 返回處理結果
        return request_type, processed_result
    except Exception as e:
        print(f"發生錯誤：{str(e)}")
        return (3, f"類型3：{user_input}")

if __name__ == "__main__":
    print("動漫類別分析工具")
    print("輸入描述文字，我會分析最相關的動漫類別")
    print("直接按 Enter 可結束程式")
    print("-" * 50)
    
    while True:
        user_input = input("\n請輸入描述（直接按 Enter 結束）：").strip()
        if not user_input:
            break
        classify_anime_genre(user_input)