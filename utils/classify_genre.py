import os
import sys
import sqlite3
import json
from openai import OpenAI

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


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

def use_llm_for_classification(user_input, genres, max_retries=3):
    """使用 OpenAI 進行分類（當傳統方法信心分數不夠時）"""
    try:
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        genres_list = sorted(list(genres))  # 確保有序列表
        print(f"可用類別：{', '.join(genres_list)}")
        
        # 更明確的提示詞，強調必須從給定類別中選擇
        prompt = (
            f"請從以下動漫類別中，選出最符合「{user_input}」的三個類別：\n"
            + "\n".join(f"{i+1}. {genre}" for i, genre in enumerate(genres_list))
            + "\n\n"
            f"要求：\n"
            f"1. 必須從上述列表中選擇\n"
            f"2. 選擇三個最相關的類別\n"
            f"3. 給出關聯度分數(0.0到1.0之間)\n"
            f"4. 按關聯度從高到低排序\n"
            f"5. 嚴格按照以下格式回覆，每行一個結果：\n"
            f"類別名(0.xx)\n\n"
            f"請直接返回結果，不要有任何解釋或其他文字。"
        )
        
        print("發送 OpenAI 請求...")
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,  # 降低隨機性
                    max_tokens=100,   # 減少token數
                    timeout=60        # 增加超時時間
                )
                print("收到 OpenAI 回應...")
                
                # 驗證和過濾結果
                result = response.choices[0].message.content.strip()
                valid_results = []
                
                for line in result.split('\n'):
                    if not line.strip():
                        continue
                    # 嘗試解析類別名和分數
                    try:
                        genre = line.split('(')[0].strip()
                        score = float(line.split('(')[1].rstrip(')'))
                        # 驗證類別是否在允許列表中
                        if genre in genres:
                            valid_results.append(f"{genre}({score:.2f})")
                    except:
                        continue
                
                # 確保只返回前三個有效結果
                return '\n'.join(valid_results[:3]) if valid_results else None
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"重試第 {attempt + 1} 次... ({str(e)})")
                    import time
                    time.sleep(1)  # 等待1秒後重試
                else:
                    print(f"OpenAI API 請求失敗：{str(e)}")
                    return None
            
    except ImportError:
        print("OpenAI 初始化失敗")
        return None
    except Exception as e:
        print(f"OpenAI 分類失敗：{str(e)}")
        return None

def classify_by_features(user_input):
    """使用 OpenAI 根據用戶描述進行動漫類別分類
    
    Args:
        user_input (str): 用戶輸入的描述文字
        
    Returns:
        str: 分類結果，格式為每行一個"類別名(分數)"
    """
    print(f"\n開始分析：「{user_input}」")
    
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'anime_database.db')
        print("讀取資料庫中的類別...")
        genres = get_all_genres(db_path)
        print(f"找到 {len(genres)} 個可用類別")
        
        print("使用 OpenAI 進行分類...")
        result = use_llm_for_classification(user_input, genres)
        
        if not result:
            print("未能獲得分類結果")
            return None
            
        return result
            
    except Exception as e:
        print(f"特徵分類過程發生錯誤：{str(e)}")
        import traceback
        print("錯誤詳情：")
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    print("動漫特徵分類工具")
    print("輸入描述文字，我會分析最相關的動漫類別")
    print("直接按 Enter 可結束程式")
    print("-" * 50)
    
    while True:
        user_input = input("\n請輸入描述（直接按 Enter 結束）：").strip()
        if not user_input:
            break
        
        result = classify_by_features(user_input)
        if result:
            print("\n=== 分類結果 ===")
            print(result)
        else:
            print("\n無法完成分類，請重試")