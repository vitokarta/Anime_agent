from flask import Flask, jsonify, send_from_directory, request
import sqlite3
from flask_cors import CORS
import os
import json

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

@app.route('/api/anime/like/<int:anime_id>', methods=['POST'])
def update_like_status(anime_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 從請求中獲取狀態（like 或 dislike）
        action = request.json.get('action')
        
        # 先獲取當前狀態
        cursor.execute('SELECT liked, is_disliked FROM anime WHERE id = ?', (anime_id,))
        current_status = cursor.fetchone()
        
        if action == 'like':
            # 如果已經是喜歡狀態，則取消喜歡
            if current_status['liked']:
                cursor.execute('UPDATE anime SET liked = 0 WHERE id = ?', (anime_id,))
                print(f"Anime {anime_id} unmarked as liked")
            else:
                # 設置為喜歡，同時取消不喜歡
                cursor.execute('UPDATE anime SET liked = 1, is_disliked = 0 WHERE id = ?', (anime_id,))
                print(f"Anime {anime_id} marked as liked")
        elif action == 'dislike':
            # 如果已經是不喜歡狀態，則取消不喜歡
            if current_status['is_disliked']:
                cursor.execute('UPDATE anime SET is_disliked = 0 WHERE id = ?', (anime_id,))
                print(f"Anime {anime_id} unmarked as disliked")
            else:
                # 設置為不喜歡，同時取消喜歡
                cursor.execute('UPDATE anime SET is_disliked = 1, liked = 0 WHERE id = ?', (anime_id,))
                print(f"Anime {anime_id} marked as disliked")
            
        conn.commit()
        return jsonify({"success": True, "message": f"Updated {action} status for anime {anime_id}"}), 200
        
    except Exception as e:
        print(f"Error updating like status: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/anime/favorites', methods=['GET'])
def get_favorite_anime():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 獲取所有被標記為喜歡的動漫
        cursor.execute('SELECT * FROM anime WHERE liked = 1')
        favorites = cursor.fetchall()
        
        # 轉換為列表格式
        result = []
        for anime in favorites:
            anime_dict = dict(anime)
            # 確保 JSON 字段被正確解析
            for field in ['genres_json', 'platforms_json']:
                if anime_dict[field]:
                    anime_dict[field] = json.loads(anime_dict[field])
            result.append(anime_dict)
            
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error fetching favorites: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

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
                'created_at': anime_dict.get('created_at'),
                'liked': bool(anime_dict.get('liked', 0)),
                'is_disliked': bool(anime_dict.get('is_disliked', 0))
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
        
        # 列出所有可用的季度
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT season FROM anime')
        available_seasons = [s[0] for s in cursor.fetchall()]
        print(f"Available seasons in database: {available_seasons}")

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 建立基礎查詢
        query = 'SELECT * FROM anime WHERE 1=1'
        params = []

        print(f"Received parameters: count={count}, season={season}, description={description}, use_favorites={use_favorites}")

        # 加入季度過濾（主要條件）
        results = []
        if season:
            print(f"Filtering by season: {season}")
            query += ' AND season = ?'
            params.append(season)
            
            # 先執行季度查詢
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # 如果有找到結果，直接返回
            if results:
                print(f"Found {len(results)} results for season {season}")
            else:
                print(f"No results found for season {season}")
                return []

        # 將描述文字記錄在日誌中，但不用於過濾結果
        if description:
            print(f"Received description (for logging only): {description}")
        else:
            print("No season specified, will return anime from any season")
            
        # 執行初步查詢以檢查結果
        test_query = query
        if params:
            cursor.execute(test_query, params)
        else:
            cursor.execute(test_query)
        initial_results = cursor.fetchall()
        initial_count = len(initial_results)
        print(f"Initial query found {initial_count} results")
        print(f"Query: {test_query}")
        print(f"Params: {params}")
        if initial_count == 0:
            print("No results found, removing season filter...")
            query = 'SELECT * FROM anime'
            params = []
            cursor.execute(query)
            initial_results = cursor.fetchall()
            initial_count = len(initial_results)
            print(f"After removing season filter: found {initial_count} results")

        # 如果使用收藏，根據收藏的動漫類型進行推薦
        if use_favorites and favorites:
            # 從收藏中獲取類型
            favorite_ids = [f['id'] for f in favorites]
            if favorite_ids:
                favorite_ids_str = ','.join('?' * len(favorite_ids))
                cursor.execute(f'SELECT GROUP_CONCAT(genres_json) as genres FROM anime WHERE id IN ({favorite_ids_str})', favorite_ids)
                result = cursor.fetchone()
                if result and result['genres']:
                    # 將所有類型拆分成列表並去重
                    try:
                        all_genres = set()
                        for genres_json in result['genres'].split(','):
                            genres = json.loads(genres_json)
                            all_genres.update(genres)
                        
                        if all_genres:
                            # 構建 genres_json LIKE 查詢
                            genre_conditions = []
                            for genre in all_genres:
                                genre_conditions.append('genres_json LIKE ?')
                                params.append(f'%{genre}%')
                            query += f' AND ({" OR ".join(genre_conditions)})'
                    except json.JSONDecodeError:
                        # 如果解析 JSON 失敗，嘗試直接用逗號分隔的方式
                        genres = set(g.strip() for g in result['genres'].split(','))
                        if genres:
                            genre_conditions = []
                            for genre in genres:
                                genre_conditions.append('genres_json LIKE ?')
                                params.append(f'%{genre}%')
                            query += f' AND ({" OR ".join(genre_conditions)})'

        # 如果沒有指定季度，或者季度查詢沒有結果，則進行隨機查詢
        if not season:
            query = 'SELECT * FROM anime ORDER BY RANDOM() LIMIT ?'
            params = [count]
            cursor.execute(query, params)
            results = cursor.fetchall()

        # 無論是季度查詢還是隨機查詢的結果，都隨機選擇指定數量
        if len(results) > count:
            import random
            results = random.sample(results, count)
            
        # 保存結果到 animes 變量，供後續處理使用
        animes = results
        
        # 轉換為列表格式
        result = []
        for anime in animes:
            anime_dict = dict(anime)
            
            # 處理 genres_json
            try:
                genres = json.loads(anime_dict.get('genres_json', '[]'))
            except:
                genres = anime_dict.get('genres_json', '').split(',') if anime_dict.get('genres_json') else []
            
            # 處理 platforms_json
            try:
                platforms = json.loads(anime_dict.get('platforms_json', '[]'))
            except:
                platforms = ['Crunchyroll', 'Netflix']
            
            # 構建圖片URL
            image_path = anime_dict.get('image_path', '')
            image_filename = os.path.basename(image_path) if image_path else ''
            image_url = f'http://localhost:5000/images/{image_filename}' if image_filename else '預設圖片URL'

            # 構建推薦理由
            reasons = []
            if season:
                reasons.append(f'來自 {season} 季度')
            if description:
                reasons.append(f'符合你的描述：{description}')
            if use_favorites and favorites:
                reasons.append('根據你收藏的作品類型')
            
            reason = '、'.join(reasons) if reasons else '隨機推薦'
            
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
                'reason': reason,
                'created_at': anime_dict.get('created_at'),
                'liked': bool(anime_dict.get('liked', 0)),
                'is_disliked': bool(anime_dict.get('is_disliked', 0))
            })
        
        conn.close()
        return jsonify(result)

    except Exception as e:
        print(f"Error getting anime recommendations: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
    