#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合輸入分類器
結合 input_type.py 和 classify_genre.py 的功能
根據用戶輸入判斷請求類型並返回相應的推薦結果
使用 OpenAI API 進行分類
"""

import os
import sys
import sqlite3
import json
import time
from datetime import datetime
from openai import OpenAI

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sample_queries_basic import recommend_similar_anime, basic_tag_search
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 載入 .env 文件
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# OpenAI API 設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("請在 .env 文件中設定 OPENAI_API_KEY")
    
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def get_all_genres(db_path):
    """從資料庫取得所有類別"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT genres_json FROM anime")
    genres = set()
    for row in cursor.fetchall():
        try:
            genre_list = json.loads(row[0])
            genres.update(genre_list)
        except:
            continue
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

def use_openai_for_genre_classification(user_input, genres_list, max_retries=3):
    """使用 OpenAI API 進行類別分類"""
    try:
        prompt = (
            f"請從以下動漫類別中，選出最符合「{user_input}」的0至2個類別若沒有符合的不強制選擇：\n"
            + "\n".join(f"{i+1}. {genre}" for i, genre in enumerate(genres_list))
            + "\n\n"
            f"要求：\n"
            f"1. 必須從上述列表中選擇\n"
            f"2. 選擇0至2個最相關的類別\n"
            f"3. 嚴格按照以下格式回覆，每行一個結果：\n"
            f"範例輸出：\n"
            f"奇幻\n"
            f"冒險\n"
            f"請直接返回結果，不要有任何解釋或其他文字。"
        )

        # 使用 OpenAI API 進行分類，添加重試機制
        for attempt in range(max_retries):
            try:
                print(f"嘗試進行類別分類... (第 {attempt + 1} 次)")
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=100,
                    timeout=60
                )

                # 解析回應並提取類別
                result_text = response.choices[0].message.content.strip()
                print(f"OpenAI 原始回應：{result_text}")

                valid_results = []
                for line in result_text.split('\n'):
                    line = line.strip()
                    if line and line in genres_list:
                        valid_results.append(line)
                        print(f"找到有效類別：{line}")

                # 返回0至2個有效結果
                return valid_results[:2] if valid_results else []

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"OpenAI 請求失敗，等待1秒後重試... ({attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(1)
                    continue
                print(f"OpenAI 分類失敗：{str(e)}")
                break

        return []

    except Exception as e:
        print(f"OpenAI 分類失敗：{str(e)}")
        return []

def classify_input_request(user_input, season, max_retries=3):
    """
    分類用戶輸入請求
    返回格式：
    - 類型1：[1, 動漫名稱]
    - 類型2：[2, 類別1, 類別2] (0至2個類別)
    - 類型3：[3, 使用者輸入]
    """
    try:
        prompt = (
            f"請分析以下用戶輸入屬於哪種類型：\n"
            f"輸入文本：{user_input}\n\n"
            f"判斷規則：\n"
            f"1: 提到特定動漫名稱的推薦請求（例如：有沒有和火影忍者相似的動漫）\n"
            f"2: 提到動漫類別、特徵、題材的推薦請求 （例如：有沒有推薦的XX類型番劇）\n"
            f"3: 其他或無法判斷的請求\n\n"
            f"請只返回一個數字(1,2,3)，不要有任何其他文字"
        )

        # 使用 OpenAI API 進行分類，添加重試機制
        request_type = 3  # 默認為類型3
        for attempt in range(max_retries):
            try:
                print(f"嘗試進行請求類型判斷... (第 {attempt + 1} 次)")
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=10,
                    timeout=60
                )

                result = response.choices[0].message.content.strip()
                request_type = int(result)
                if request_type not in [1, 2, 3]:
                    print(f"OpenAI 返回了無效的類型：{result}")
                    request_type = 3
                print(f"分類結果：類型 {request_type}")
                break  # 成功獲得回應，跳出重試循環
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"OpenAI 請求失敗，等待1秒後重試... ({attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(1)
                    continue
                print(f"OpenAI 請求失敗：{str(e)}")
                request_type = 3
                break

        # 資料庫路徑
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'anime_database.db')

        # 根據類型進行處理
        if request_type == 1:
            # 類型1：提取動漫名稱
            name_prompt = (
                f"請從以下文本中提取動漫名稱（只返回名稱本身，不要有其他文字）：\n"
                f"{user_input}"
            )

            anime_name = None
            for attempt in range(max_retries):
                try:
                    print(f"嘗試提取動漫名稱... (第 {attempt + 1} 次)")
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": name_prompt}],
                        temperature=0.1,
                        max_tokens=50,
                        timeout=60
                    )
                    anime_name = response.choices[0].message.content.strip()
                    print(f"提取到的動漫名稱：{anime_name}")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"提取名稱失敗，等待1秒後重試... ({attempt + 1}/{max_retries}): {str(e)}")
                        time.sleep(1)
                        continue
                    print(f"提取動漫名稱失敗：{str(e)}")
                    return [3, user_input]

            if anime_name:
                # 驗證動漫是否在資料庫中
                reference_genres, found_title = get_anime_genres(db_path, anime_name)

                if found_title:
                    # 使用找到的標題進行推薦
                    result = recommend_similar_anime(found_title, limit=10, season=season)
                    #print(f"推薦結果：{result}")
                    return [1, result]
                else:
                    # 如果資料庫中找不到該動漫，使用原始名稱
                    result = recommend_similar_anime(anime_name, limit=10, season=season)
                    #print(f"推薦結果：{result}")
                    return [1, result]

        elif request_type == 2:
            # 類型2：類別推薦
            print("獲取資料庫中的所有類別...")
            genres_list = get_all_genres(db_path)
            print(f"找到 {len(genres_list)} 個可用類別")

            # 使用 OpenAI 進行類別分類
            recommended_genres = use_openai_for_genre_classification(user_input, genres_list)
            result = basic_tag_search(recommended_genres, season=season)

            return [2, result]
        else:
            # 類型3：其他
            return [3, user_input]

    except Exception as e:
        print(f"分類過程發生錯誤：{str(e)}")
        return [3, user_input]

def save_result_to_json(result, filename="return.json"):
    """將結果保存到JSON檔案"""
    try:
        json_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "result": result
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"結果已保存到 {filename}")

    except Exception as e:
        print(f"保存JSON檔案失敗：{str(e)}")

def main():
    """主函數"""
    print("整合輸入分類器")
    print("=" * 50)

    if len(sys.argv) > 1:
        # 從命令行參數獲取輸入
        user_input = " ".join(sys.argv[1:])
    else:
        # 互動模式
        user_input = input("請輸入您的請求：").strip()

    if not user_input:
        print("未提供輸入內容")
        return

    print(f"\n分析輸入：{user_input}")
    print("-" * 50)

    # 進行分類
    result = classify_input_request(user_input)

    # 輸出結果到終端機
    print(f"\n分類結果：{result}")

    # 保存到JSON檔案
    save_result_to_json(result)

if __name__ == "__main__":
    main()