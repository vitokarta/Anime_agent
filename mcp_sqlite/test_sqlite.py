#!/usr/bin/env python3
"""
SQLite MCP server 測試程式
用於查詢 anime 數據庫中的奇幻類作品
"""
import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp import StdioServerParameters

# 數據庫路徑（相對於項目根目錄）
DB_PATH = os.path.abspath("anime_database.db")

class AnimeSQLiteClient:
    """動漫數據庫 SQLite MCP 客戶端"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def connect_and_query(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        連接 SQLite MCP server 並執行查詢

        Args:
            sql_query: SQL 查詢語句

        Returns:
            查詢結果列表
        """
        # 檢查數據庫文件是否存在
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"數據庫文件不存在: {self.db_path}")

        # 設置 SQLite MCP server 參數
        server_params = StdioServerParameters(
            command="uvx",
            args=["mcp-server-sqlite", "--db-path", self.db_path],
            env={}
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    # 檢查可用工具
                    tools = await session.list_tools()
                    available_tools = [getattr(t, 'name', 'unknown') for t in tools.tools]
                    print(f"🛠️ 可用工具: {available_tools}")

                    if 'read_query' not in available_tools:
                        raise RuntimeError("read_query 工具不可用")

                    # 執行查詢
                    print(f"📋 執行查詢: {sql_query}")
                    result = await session.call_tool(
                        "read_query",
                        arguments={"query": sql_query}
                    )

                    # 解析結果
                    if result.content:
                        for content in result.content:
                            content_text = getattr(content, 'text', None)
                            if content_text:
                                # 添加調試信息
                                print(f"🔍 原始返回內容: {content_text}")
                                print(f"🔍 內容類型: {type(content_text)}")
                                print(f"🔍 內容長度: {len(content_text)}")

                                try:
                                    # 嘗試 JSON 解析
                                    data = json.loads(content_text)
                                    print(f"✅ JSON 解析成功")
                                    return data if isinstance(data, list) else [data]
                                except json.JSONDecodeError:
                                    print(f"⚠️ JSON 解析失敗，嘗試 literal_eval")
                                    try:
                                        # 嘗試使用 ast.literal_eval 解析 Python 字典
                                        import ast
                                        data = ast.literal_eval(content_text)
                                        print(f"✅ literal_eval 解析成功")
                                        return data if isinstance(data, list) else [data]
                                    except (ValueError, SyntaxError) as e:
                                        print(f"⚠️ literal_eval 解析也失敗: {e}")
                                        # 如果都失敗，嘗試直接返回文本內容進行手動解析
                                        print(f"🔧 返回原始內容進行手動處理")
                                        return content_text

                    return []

        except Exception as e:
            print(f"❌ 連接或查詢失敗: {e}")
            raise

    async def search_anime_by_genre(self, genre: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        根據類型搜索動漫作品

        Args:
            genre: 動漫類型（如 "奇幻", "Fantasy", "冒險" 等）
            limit: 結果數量限制

        Returns:
            動漫作品列表
        """
        # 使用 JSON 查詢來查找包含特定類型的作品
        sql_query = f"""
        SELECT
            id,
            title,
            season,
            rating,
            viewers_count,
            genres_json,
            platforms_json,
            synopsis
        FROM anime
        WHERE
            -- 方法1: 直接字串匹配（適用於大部分情況）
            (genres_json LIKE '%{genre}%'
            OR genres_json LIKE '%{genre.lower()}%'
            OR genres_json LIKE '%{genre.upper()}%'
            OR genres_json LIKE '%{genre.capitalize()}%')
            -- 方法2: 如果 SQLite 版本支援 JSON 函數，可以使用更精確的匹配
            OR EXISTS (
                SELECT 1 FROM json_each(genres_json)
                WHERE json_each.value LIKE '%{genre}%'
            )
        ORDER BY rating DESC, viewers_count DESC
        LIMIT {limit};
        """

        return await self.connect_and_query(sql_query)

    async def search_anime_by_multiple_genres(self, genres: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """
        根據多個類型搜索動漫作品（AND 邏輯）

        Args:
            genres: 動漫類型列表
            limit: 結果數量限制

        Returns:
            動漫作品列表
        """
        # 建構多個類型的 AND 查詢
        genre_conditions = []
        for genre in genres:
            condition = f"""(
                genres_json LIKE '%{genre}%'
                OR genres_json LIKE '%{genre.lower()}%'
                OR genres_json LIKE '%{genre.upper()}%'
                OR genres_json LIKE '%{genre.capitalize()}%'
            )"""
            genre_conditions.append(condition)

        where_clause = " AND ".join(genre_conditions)

        sql_query = f"""
        SELECT
            id,
            title,
            season,
            rating,
            viewers_count,
            genres_json,
            platforms_json,
            synopsis
        FROM anime
        WHERE {where_clause}
        ORDER BY rating DESC, viewers_count DESC
        LIMIT {limit};
        """

        return await self.connect_and_query(sql_query)

    async def get_all_genres(self) -> List[str]:
        """
        獲取數據庫中所有的動漫類型

        Returns:
            類型列表
        """
        sql_query = """
        SELECT DISTINCT genres_json
        FROM anime
        WHERE genres_json IS NOT NULL
        AND genres_json != '';
        """

        results = await self.connect_and_query(sql_query)
        all_genres = set()

        for result in results:
            if 'genres_json' in result:
                try:
                    genres = json.loads(result['genres_json'])
                    if isinstance(genres, list):
                        all_genres.update(genres)
                except (json.JSONDecodeError, TypeError):
                    # 如果不是 JSON 格式，跳過
                    continue

        return sorted(list(all_genres))

    async def get_database_stats(self) -> Dict[str, Any]:
        """
        獲取數據庫統計信息

        Returns:
            統計信息字典
        """
        sql_query = """
        SELECT
            COUNT(*) as total_anime,
            COUNT(CASE WHEN rating IS NOT NULL THEN 1 END) as rated_anime,
            AVG(rating) as avg_rating,
            MAX(rating) as max_rating,
            MIN(rating) as min_rating,
            COUNT(DISTINCT season) as total_seasons
        FROM anime;
        """

        results = await self.connect_and_query(sql_query)
        return results[0] if results else {}

def print_anime_results(results: Any, query_description: str):
    """格式化打印動漫搜索結果"""

    print(f"\n{'='*60}")
    print(f"🎌 {query_description}")
    print(f"{'='*60}")

    # 添加調試信息
    print(f"🔍 results 類型: {type(results)}")
    print(f"🔍 results 內容: {repr(results)[:200]}...")

    # 處理不同類型的返回結果
    if isinstance(results, str):
        print("🔧 處理字符串格式的結果")
        try:
            import ast
            results = ast.literal_eval(results)
        except (ValueError, SyntaxError):
            print("❌ 無法解析結果字符串")
            return

    if not results:
        print("❌ 沒有找到符合條件的動漫")
        return

    if not isinstance(results, list):
        print(f"⚠️ 結果不是列表格式: {type(results)}")
        return

    print(f"✅ 找到 {len(results)} 部動漫:\n")

    for i, anime in enumerate(results, 1):
        print(f"[{i}] {anime.get('title', 'Unknown')}")

        # 評分信息
        rating = anime.get('rating')
        if rating:
            print(f"    ⭐ 評分: {rating}")

        # 觀看人數
        viewers = anime.get('viewers_count')
        if viewers:
            print(f"    👥 觀看人數: {viewers}")

        # 季節信息
        season = anime.get('season')
        if season:
            print(f"    📅 季節: {season}")

        # 類型信息
        genres_json = anime.get('genres_json')
        if genres_json:
            try:
                genres = json.loads(genres_json)
                if isinstance(genres, list) and genres:
                    print(f"    🏷️ 類型: {', '.join(genres)}")
            except (json.JSONDecodeError, TypeError):
                print(f"    🏷️ 類型: {genres_json}")

        # 簡介（如果有的話，只顯示前100字符）
        synopsis = anime.get('synopsis')
        if synopsis and synopsis.strip():
            synopsis_preview = synopsis[:100] + "..." if len(synopsis) > 100 else synopsis
            print(f"    📖 簡介: {synopsis_preview}")

        print()

async def main():
    """主函數"""
    print("🎌 動漫數據庫 SQLite MCP 測試")
    print("=" * 50)

    # 創建客戶端
    client = AnimeSQLiteClient()

    try:
        # 1. 獲取數據庫統計信息
        print("📊 獲取數據庫統計信息...")
        stats = await client.get_database_stats()
        if stats:
            print(f"📚 總動漫數: {stats.get('total_anime', 0)}")
            print(f"⭐ 有評分動漫: {stats.get('rated_anime', 0)}")
            print(f"📈 平均評分: {stats.get('avg_rating', 0):.2f}")
            print(f"🏆 最高評分: {stats.get('max_rating', 0)}")
            print(f"📅 總季節數: {stats.get('total_seasons', 0)}")

        # 2. 搜索奇幻類動漫
        fantasy_results = await client.search_anime_by_genre("奇幻", limit=5)
        print_anime_results(fantasy_results, "奇幻類動漫搜索結果")

        # 3. 搜索冒險類動漫
        adventure_results = await client.search_anime_by_genre("冒險", limit=5)
        print_anime_results(adventure_results, "冒險類動漫搜索結果")

        # 4. 搜索同時包含多個類型的動漫
        multi_genre_results = await client.search_anime_by_multiple_genres(["奇幻", "冒險"], limit=3)
        print_anime_results(multi_genre_results, "奇幻 + 冒險類動漫搜索結果")

        # 5. 獲取所有類型
        print("\n" + "="*60)
        print("🏷️ 數據庫中的所有動漫類型")
        print("="*60)
        all_genres = await client.get_all_genres()
        if all_genres:
            print(f"總共 {len(all_genres)} 種類型:")
            for i, genre in enumerate(all_genres):
                print(f"  {i+1:2d}. {genre}")
        else:
            print("❌ 未能獲取類型信息")

    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 支持命令行參數
    if len(sys.argv) > 1:
        # 自定義搜索
        search_genre = sys.argv[1]
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10

        async def custom_search():
            client = AnimeSQLiteClient()
            results = await client.search_anime_by_genre(search_genre, limit)
            print_anime_results(results, f"'{search_genre}' 類動漫搜索結果")

        asyncio.run(custom_search())
    else:
        # 運行完整測試
        asyncio.run(main())