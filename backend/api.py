from flask import Flask, jsonify, send_from_directory
import sqlite3
from flask_cors import CORS
import os
import json
from flask_cors import CORS
import os

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

if __name__ == '__main__':
    app.run(port=5000, debug=True)