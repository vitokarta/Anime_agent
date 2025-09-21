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

@app.route('/api/anime/like/<int:anime_id>', methods=['POST'])
def update_like_status(anime_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

    # 從請求中獲取狀態（like 或 dislike）
        action = request.json.get('action')

# 先獲取當前狀態
        cursor.execute('SELECT like, is_disliked FROM anime WHERE id = ?', (anime_id,))
        current_status = cursor.fetchone()

        if action == 'like':
            # 如果已經是喜歡狀態，則取消喜歡
            if current_status['like']:
                cursor.execute('UPDATE anime SET like = 0 WHERE id = ?', (anime_id,))
                print(f"Anime {anime_id} unmarked as liked")
            else:
                # 設置為喜歡，同時取消不喜歡
                cursor.execute('UPDATE anime SET like = 1, is_disliked = 0 WHERE id = ?', (anime_id,))
                print(f"Anime {anime_id} marked as like")
        elif action == 'dislike':
            # 如果已經是不喜歡狀態，則取消不喜歡
            if current_status['is_disliked']:
                cursor.execute('UPDATE anime SET is_disliked = 0 WHERE id = ?', (anime_id,))
                print(f"Anime {anime_id} unmarked as disliked")
            else:
                # 設置為不喜歡，同時取消喜歡
                cursor.execute('UPDATE anime SET is_disliked = 1, like = 0 WHERE id = ?', (anime_id,))
                print(f"Anime {anime_id} marked as disliked")

        conn.commit()
        return jsonify({"success": True, "message": f"Updated {action} status for anime {anime_id}"}), 200

    except Exception as e:
        print(f"Error updating like status: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
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

def parse_viewers_count(viewers_str):
    """解析觀眾數量字符串，轉換為數字"""
    if not viewers_str:
        return 100000  # 默認值
    
    viewers_str = str(viewers_str).strip().upper()
    
    try:
        # 處理 K (千) 後綴
        if viewers_str.endswith('K'):
            number = float(viewers_str[:-1])
            return int(number * 1000)
        
        # 處理 M (百萬) 後綴
        elif viewers_str.endswith('M'):
            number = float(viewers_str[:-1])
            return int(number * 1000000)
        
        # 處理純數字
        else:
            return int(float(viewers_str))
            
    except (ValueError, TypeError):
        return 100000  # 解析失敗時返回默認值

def process_external_api_response(api_response, count=5):
    """處理外部 API 的回應，轉換為前端需要的格式"""
    try:
        # 檢查外部 API 是否返回了正確的格式
        if not api_response:
            print("外部 API 回應為空")
            return []
            
        print(f"處理外部 API 回應: {api_response}")
        
        # 處理實際的外部 API 回應格式
        if 'anime' in api_response and 'reason' in api_response:
            # 解析動漫數據
            anime_data = json.loads(api_response['anime'])
            reason_data = json.loads(api_response['reason'])
            
            print(f"解析到 {len(anime_data)} 部動漫")
            print(f"解析到 {len(reason_data)} 個推薦理由")
            print(f"動漫數據: {[anime.get('title', 'Unknown') for anime in anime_data]}")
            print(f"理由數據: {[reason.get('title', 'Unknown') for reason in reason_data]}")
            
            # 如果外部 API 沒有返回動漫數據，但有推薦理由，則從本地數據庫查找
            if len(anime_data) == 0 and len(reason_data) > 0:
                print("外部 API 只返回推薦理由，嘗試從本地數據庫查找動漫數據")
                anime_data = []
                
                # 從本地數據庫查找動漫
                db_path = os.path.join(os.path.dirname(__file__), 'anime_database.db')
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                for reason_item in reason_data:
                    title = reason_item.get('title', '')
                    if title:
                        # 嘗試模糊匹配動漫標題
                        cursor.execute("SELECT * FROM anime WHERE title LIKE ? LIMIT 1", (f"%{title}%",))
                        result = cursor.fetchone()
                        if result:
                            anime_dict = dict(result)
                            anime_data.append(anime_dict)
                            print(f"找到匹配動漫: {anime_dict.get('title', 'Unknown')}")
                        else:
                            print(f"未找到匹配動漫: {title}")
                
                conn.close()
                print(f"從數據庫查找到 {len(anime_data)} 部動漫")
            
            result = []
            for i, anime in enumerate(anime_data[:count]):
                # 找到對應的推薦理由 - 根據 title 匹配
                reason = "基於外部 AI 分析推薦"
                anime_title = anime.get('title', '')
                
                # 嘗試根據 title 匹配推薦理由
                for reason_item in reason_data:
                    reason_title = reason_item.get('title', '')
                    if reason_title in anime_title or anime_title in reason_title:
                        reason = reason_item.get('reason', reason)
                        break
                
                # 如果沒有找到匹配的理由，使用索引匹配
                if reason == "基於外部 AI 分析推薦" and i < len(reason_data):
                    reason = reason_data[i].get('reason', reason)
                
                print(f"處理動漫 {i+1}: {anime_title} - 理由: {reason[:50]}...")
                
                # 處理 genres_json
                try:
                    genres = json.loads(anime.get('genres_json', '[]'))
                except:
                    genres = ['未知']
                
                # 處理 platforms_json
                try:
                    platforms = json.loads(anime.get('platforms_json', '[]'))
                except:
                    platforms = ['未知平台']
                
                # 構建圖片URL
                image_path = anime.get('image_path', '')
                image_filename = os.path.basename(image_path) if image_path else ''
                image_url = f'http://localhost:5000/images/{image_filename}' if image_filename else 'http://localhost:5000/images/default.jpg'
                
                # 處理觀眾數量
                viewers_count = anime.get('viewers_count', '100K')
                viewers = parse_viewers_count(viewers_count)
                
                anime_result = {
                    'id': anime.get('id', f'external_{i+1}'),
                    'title': anime.get('title', f'外部推薦動漫 {i+1}'),
                    'cover': image_url,
                    'season': anime.get('season', '2024-Winter'),
                    'rating': float(anime.get('rating', 8.0)),
                    'viewers': viewers,
                    'genres': genres,
                    'description': anime.get('synopsis', '暫無描述'),
                    'platforms': platforms,
                    'reason': reason
                }
                
                result.append(anime_result)
                print(f"添加動漫到結果: {anime_result['title']}")
            
            print(f"成功處理 {len(result)} 部推薦動漫")
            print(f"最終結果包含的動漫: {[r['title'] for r in result]}")
            return result
            
        else:
            print("外部 API 回應格式不正確")
            return []
        
    except Exception as e:
        print(f"處理外部 API 回應時發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

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
                'viewers': parse_viewers_count(anime_dict.get('viewers_count')),
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
@app.route('/api/anime/favorites', methods=['GET'])
def get_favorite_anime():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

#獲取所有被標記為喜歡的動漫
        cursor.execute('SELECT * FROM anime WHERE like = 1')
        favorites = cursor.fetchall()
        print(f"Retrieved {len(favorites)} favorite anime records")  # 診斷日誌
#轉換為列表格式
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

        classification_result = classify_input_request(description, season=season, count=count)
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
        elif classification_result[0] == 3:
            # 類型3：外部 API 推薦
            print(f"Classified as Type 3 (External API)")
            external_api_response = classification_result[1]  # 外部 API 的回應
            
            # 檢查外部 API 是否成功返回結果
            if external_api_response is None:
                print("外部 API 連接失敗，返回錯誤信息")
                return jsonify({
                    "error": "外部推薦服務暫時無法使用，請稍後再試或嘗試其他描述方式",
                    "suggestions": [
                        "嘗試描述具體的動漫名稱",
                        "描述喜歡的動漫類型或風格",
                        "檢查網路連接後重新嘗試"
                    ]
                }), 503
            else:
                result = process_external_api_response(external_api_response, count)
                print(f"即將返回 {len(result)} 部推薦動漫給前端")
                return jsonify(result)
        else:
            print("Classified as unknown type")
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
                'viewers': parse_viewers_count(anime_dict.get('viewers_count')),
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

    