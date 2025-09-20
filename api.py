from flask import Flask, jsonify, send_from_directory, request
import sqlite3
from flask_cors import CORS
import os
import json
import sys

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.integrated_input_classifier import classify_input_request
from utils.database.anime_queries import create_anime_db
from utils.llm_anime_selector import create_llm_selector

app = Flask(__name__)
CORS(app)

# 添加圖片路由
@app.route('/images/<path:filename>')
def serve_image(filename):
    # 使用絕對路徑指向 images 目錄
    image_path = os.path.join(os.path.dirname(__file__), 'anime_data', 'images')
    try:
        return send_from_directory(image_path, filename)
    except Exception as e:
        print(f"Error serving image {filename}: {str(e)}")
        return "Image not found", 404

def get_db_connection():
    # 使用絕對路徑
    db_path = os.path.join(os.path.dirname(__file__), 'anime_database.db')
    print(f"Trying to connect to database at: {db_path}")  # 診斷日誌
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/anime/<int:count>', methods=['GET'])
def get_anime_list(count):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 確認資料表存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='anime'")
        if not cursor.fetchone():
            print("Error: anime table does not exist")  # 診斷日誌
            return jsonify({"error": "Database table not found"}), 500
        
        # 獲取指定數量的動漫
        cursor.execute('SELECT * FROM anime LIMIT ?', (count,))
        animes = cursor.fetchall()
        
        # 診斷日誌
        print(f"Retrieved {len(animes)} anime records")
        
        # 轉換為列表格式
        result = []
        for anime in animes:
            anime_dict = dict(anime)
            
            # 處理 genres_json（可能是 JSON 字串或逗號分隔的字串）
            try:
                import json
                genres = json.loads(anime_dict.get('genres_json', '[]'))
            except:
                genres = anime_dict.get('genres_json', '').split(',') if anime_dict.get('genres_json') else []
            
            # 處理 platforms_json
            try:
                platforms = json.loads(anime_dict.get('platforms_json', '[]'))
            except:
                platforms = ['Crunchyroll', 'Netflix']  # 默認平台
            
            # 構建圖片URL
            image_path = anime_dict.get('image_path', '')
            # 從完整路徑中提取文件名
            image_filename = os.path.basename(image_path) if image_path else ''
            image_url = f'http://localhost:5000/images/{image_filename}' if image_filename else '預設圖片URL'
            print(f"Generated image URL: {image_url}")  # 診斷日誌

            # 構建返回數據
            result.append({
                'id': anime_dict.get('id'),
                'title': anime_dict.get('title', '未知標題'),
                'cover': image_url,  # 使用構建的圖片URL
                'season': anime_dict.get('season', '2024-1月'),
                'rating': float(anime_dict.get('rating', 0)) if anime_dict.get('rating') else 0.0,
                'viewers': anime_dict.get('viewers_count', 100000),
                'genres': genres,
                'description': anime_dict.get('synopsis', '暫無描述'),
                'platforms': platforms,
                'reason': '基於你的偏好推薦',  # 之後可以基於用戶偏好生成
                'created_at': anime_dict.get('created_at')
            })
            
        # 診斷日誌
        print(f"Formatted {len(result)} anime records for response")
        
        conn.close()
        return jsonify(result)
    except Exception as e:
        print(f"Error in get_anime_list: {str(e)}")  # 診斷日誌
        return jsonify({"error": str(e)}), 500
    
    conn.close()
    return jsonify(result)

@app.route('/api/anime/recommend', methods=['POST'])
def get_anime_recommendations():
    try:
        print("\n=== New Recommendation Request ===")
        data = request.get_json()
        print(f"Raw request data: {data}")
        
        count = data.get('count', 5)
        season = data.get('season', '')
        description = data.get('description', '')
        use_favorites = data.get('useFavorites', False)
        favorites = data.get('favorites', [])

        classification_result = classify_input_request(description, season=season)
        #print(f"Classification result: {classification_result}")

        if classification_result[0] == 1 :
            # 類型1：動漫名稱推薦
            print(f"Classified as Type 1 (Anime Name)")
            candidate_anime = classification_result[1]  # 已經是查詢出來的前10部動漫
            llm_selector = create_llm_selector()
            selected_anime, llm_reasons = llm_selector.select_anime(description, candidate_anime, count)
        elif classification_result[0] == 2:
            # 類型2：標籤推薦
            print(f"Classified as Type 2 (Tags)")
            candidate_anime = classification_result[1]  # 已經是查詢出來的前10部動漫
            llm_selector = create_llm_selector()
            selected_anime, llm_reasons = llm_selector.select_anime(description, candidate_anime, count)
        else:
            print("Classified as Type 3 (Other)")
            return jsonify({"error": "暫不支援此類型的推薦"}), 400
        
        print(f"Selected anime count: {len(selected_anime)}")
        print(f"LLM reasons count: {len(llm_reasons)}")

        #整理回傳內容
        result = []
        for i, anime_dict in enumerate(selected_anime):
            # 處理 genres_json（可能是 JSON 字串或逗號分隔的字串）
            try:
                import json
                genres = json.loads(anime_dict.get('genres_json', '[]'))
            except:
                genres = anime_dict.get('genres_json', '').split(',') if anime_dict.get('genres_json') else []
            
            # 處理 platforms_json
            try:
                platforms = json.loads(anime_dict.get('platforms_json', '[]'))
            except:
                platforms = ['Crunchyroll', 'Netflix']  # 默認平台
            
            # 構建圖片URL
            image_path = anime_dict.get('image_path', '')
            # 從完整路徑中提取文件名
            image_filename = os.path.basename(image_path) if image_path else ''
            image_url = f'http://localhost:5000/images/{image_filename}' if image_filename else '預設圖片URL'
            print(f"Generated image URL: {image_url}")  # 診斷日誌

            # 使用 LLM 生成的理由，如果沒有則使用默認理由
            if i < len(llm_reasons) and llm_reasons[i]:
                reason = llm_reasons[i]
                print(f"使用 LLM 理由 [{i}]: {reason}")
            else:
                reason = "基於你的偏好推薦"
                print(f"使用預設理由 [{i}]: {reason}")

            # 整理回傳內容
            result.append({
                'id': anime_dict.get('id'),
                'title': anime_dict.get('title', '未知標題'),
                'cover': image_url,
                'season': anime_dict.get('season', '2024-1月'),
                'rating': float(anime_dict.get('rating', 0)) if anime_dict.get('rating') else 0.0,
                'viewers': anime_dict.get('viewers_count', 100000),
                'genres': genres,
                'description': anime_dict.get('synopsis', '暫無描述'),
                'platforms': platforms,
                'reason': reason
            })
        return jsonify(result)
        #sample return
        # result.append({
        #         'id': anime_dict.get('id'),
        #         'title': anime_dict.get('title', '未知標題'),
        #         'cover': image_url,
        #         'season': anime_dict.get('season', '2024-1月'),
        #         'rating': float(anime_dict.get('rating', 0)) if anime_dict.get('rating') else 0.0,
        #         'viewers': anime_dict.get('viewers_count', 100000),
        #         'genres': genres,
        #         'description': anime_dict.get('synopsis', '暫無描述'),
        #         'platforms': platforms,
        #         'reason': reason
        #     })
        # return jsonify(result)

    except Exception as e:
        print(f"Error getting anime recommendations: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)

    