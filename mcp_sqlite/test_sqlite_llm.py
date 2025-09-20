#!/usr/bin/env python3
"""
LLM 驅動的 SQLite MCP 查詢系統
使用 LLM 生成 SQL 語法並通過 MCP server 執行
"""
import asyncio
import json
import os
import sys
import ast
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp import StdioServerParameters

# Lemonade Server 集成
from openai import OpenAI

# 配置
DB_PATH = os.path.abspath("anime_database.db")
LEMONADE_BASE_URL = os.getenv("LEMONADE_BASE_URL", "http://localhost:8000/api/v1")
LEMONADE_API_KEY = os.getenv("LEMONADE_API_KEY", "lemonade")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "Qwen-2.5-7B-Instruct-NPU")

class LLMDrivenSQLiteClient:
    """LLM 驅動的 SQLite 客戶端"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.llm_client = OpenAI(
            base_url=LEMONADE_BASE_URL,
            api_key=LEMONADE_API_KEY
        )
        self.database_schema = None
        self.available_tools = []

    async def initialize(self):
        """初始化：獲取數據庫結構和可用工具"""
        print("正在初始化 LLM 驅動的 SQLite 客戶端...")

        # 獲取數據庫結構
        await self._get_database_schema()
        print(f"✅ 已獲取數據庫結構")

    async def _execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """執行 MCP 工具"""
        server_params = StdioServerParameters(
            command="uvx",
            args=["mcp-server-sqlite", "--db-path", self.db_path],
            env={}
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # 獲取可用工具（第一次調用時）
                if not self.available_tools:
                    tools = await session.list_tools()
                    self.available_tools = [
                        {
                            "name": getattr(t, 'name', 'unknown'),
                            "description": getattr(t, 'description', 'no description')
                        }
                        for t in tools.tools
                    ]

                # 執行工具
                result = await session.call_tool(tool_name, arguments=arguments)

                # 解析結果
                if result.content:
                    for content in result.content:
                        content_text = getattr(content, 'text', None)
                        if content_text:
                            try:
                                # 嘗試 JSON 解析
                                return json.loads(content_text)
                            except json.JSONDecodeError:
                                try:
                                    # 嘗試 ast.literal_eval
                                    return ast.literal_eval(content_text)
                                except (ValueError, SyntaxError):
                                    # 返回原始文本
                                    return content_text
                return None

    async def _get_database_schema(self):
        """獲取數據庫完整結構"""
        # 獲取所有表
        tables = await self._execute_mcp_tool("list_tables", {})

        schema_info = {"tables": {}}

        if tables:
            for table in tables:
                table_name = table.get('name', table) if isinstance(table, dict) else table

                # 獲取表結構
                table_schema = await self._execute_mcp_tool("describe_table", {"table_name": table_name})

                if table_schema:
                    schema_info["tables"][table_name] = {
                        "columns": table_schema,
                        "name": table_name
                    }

        self.database_schema = schema_info

    def _create_system_prompt(self) -> str:
        """創建給 LLM 的系統提示詞"""
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in self.available_tools
        ])

        schema_description = ""
        if self.database_schema and "tables" in self.database_schema:
            for table_name, table_info in self.database_schema["tables"].items():
                schema_description += f"\n表 '{table_name}':\n"
                for column in table_info["columns"]:
                    col_name = column.get('name', 'unknown')
                    col_type = column.get('type', 'unknown')
                    col_notnull = column.get('notnull', False)
                    pk = column.get('pk', False)
                    schema_description += f"  - {col_name} ({col_type})"
                    if pk:
                        schema_description += " PRIMARY KEY"
                    if col_notnull:
                        schema_description += " NOT NULL"
                    schema_description += "\n"

        return f"""你是一個專業的 SQL 查詢生成助手。你的任務是根據用戶的自然語言需求生成正確的 SQL 語句。

## 數據庫結構
{schema_description}

## 可用的 MCP 工具
{tools_description}

## 重要說明
1. anime 表中的 genres_json 欄位存儲 JSON 格式的類型數組，例如: ["動作", "冒險", "奇幻"]
2. 當搜索類型時，使用 LIKE 操作符或 JSON 函數
3. rating 是數值類型，可以用於排序和比較
4. viewers_count 是文本類型（如 "520K", "1.2M"）
5. 只生成 SELECT 查詢語句，不要包含 INSERT/UPDATE/DELETE
6. 請確保 SQL 語法正確且安全

## 回應格式
請只回應 SQL 語句，不要包含任何其他文字或解釋。

例如：
用戶: "找出評分最高的5部奇幻動漫"
你的回應: SELECT title, rating, genres_json FROM anime WHERE genres_json LIKE '%奇幻%' ORDER BY rating DESC LIMIT 5;
"""

    async def natural_language_query(self, user_query: str) -> List[Dict[str, Any]]:
        """
        使用自然語言查詢數據庫

        Args:
            user_query: 用戶的自然語言查詢

        Returns:
            查詢結果列表
        """
        print(f"🧠 LLM 正在處理查詢: {user_query}")

        # 使用 LLM 生成 SQL
        system_prompt = self._create_system_prompt()

        response = self.llm_client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.1  # 降低隨機性，確保 SQL 準確性
        )

        generated_sql = response.choices[0].message.content.strip()

        # 清理 SQL（移除可能的 markdown 標記）
        if generated_sql.startswith("```sql"):
            generated_sql = generated_sql[6:]
        if generated_sql.endswith("```"):
            generated_sql = generated_sql[:-3]
        generated_sql = generated_sql.strip()

        print(f" LLM 生成的 SQL: {generated_sql}")

        # 基本安全檢查
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
        sql_upper = generated_sql.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                raise ValueError(f"安全檢查失敗：SQL 包含危險操作 {keyword}")

        # 執行 SQL
        try:
            results = await self._execute_mcp_tool("read_query", {"query": generated_sql})
            print(f" 查詢執行成功，返回 {len(results) if results else 0} 條記錄")
            return results if results else []
        except Exception as e:
            print(f" SQL 執行失敗: {e}")
            raise

    async def get_database_stats(self) -> Dict[str, Any]:
        """獲取數據庫統計信息"""
        stats_sql = """
        SELECT
            COUNT(*) as total_anime,
            COUNT(CASE WHEN rating IS NOT NULL THEN 1 END) as rated_anime,
            AVG(rating) as avg_rating,
            MAX(rating) as max_rating,
            MIN(rating) as min_rating,
            COUNT(DISTINCT season) as total_seasons
        FROM anime;
        """

        results = await self._execute_mcp_tool("read_query", {"query": stats_sql})
        return results[0] if results else {}

    async def get_all_genres(self) -> List[str]:
        """獲取所有動漫類型"""
        genres_sql = """
        SELECT DISTINCT genres_json
        FROM anime
        WHERE genres_json IS NOT NULL AND genres_json != '';
        """

        results = await self._execute_mcp_tool("read_query", {"query": genres_sql})
        all_genres = set()

        if results:
            for result in results:
                if 'genres_json' in result:
                    try:
                        genres = json.loads(result['genres_json'])
                        if isinstance(genres, list):
                            all_genres.update(genres)
                    except (json.JSONDecodeError, TypeError):
                        continue

        return sorted(list(all_genres))

def print_query_results(results: List[Dict[str, Any]], query_description: str):
    """格式化打印查詢結果"""
    print(f"\n{'='*70}")
    print(f"🎌 {query_description}")
    print(f"{'='*70}")

    if not results:
        print(" 沒有找到符合條件的結果")
        return

    print(f" 找到 {len(results)} 條記錄:\n")

    for i, item in enumerate(results, 1):
        print(f"[{i}] ", end="")

        # 如果有 title 欄位，優先顯示
        if 'title' in item:
            print(f"{item['title']}")

            # 顯示其他重要欄位
            if 'rating' in item and item['rating']:
                print(f"     評分: {item['rating']}")
            if 'viewers_count' in item and item['viewers_count']:
                print(f"     觀看人數: {item['viewers_count']}")
            if 'season' in item and item['season']:
                print(f"     季節: {item['season']}")

            # 處理 genres_json
            if 'genres_json' in item and item['genres_json']:
                try:
                    genres = json.loads(item['genres_json'])
                    if isinstance(genres, list) and genres:
                        print(f"     類型: {', '.join(genres)}")
                except (json.JSONDecodeError, TypeError):
                    print(f"     類型: {item['genres_json']}")

            # 顯示簡介（如果有）
            if 'synopsis' in item and item['synopsis']:
                synopsis = item['synopsis'][:100] + "..." if len(str(item['synopsis'])) > 100 else item['synopsis']
                print(f"     簡介: {synopsis}")
        else:
            # 如果沒有 title，顯示所有欄位
            for key, value in item.items():
                if value is not None:
                    print(f"    {key}: {value}")

        print()

async def main():
    """主函數"""
    print("LLM 驅動的動漫數據庫查詢系統")
    print("=" * 50)

    # 初始化客戶端
    client = LLMDrivenSQLiteClient()

    try:
        await client.initialize()

        # 顯示數據庫統計
        print("\n 數據庫統計信息:")
        stats = await client.get_database_stats()
        if stats:
            print(f" 總動漫數: {stats.get('total_anime', 0)}")
            print(f" 有評分動漫: {stats.get('rated_anime', 0)}")
            print(f" 平均評分: {stats.get('avg_rating', 0):.2f}")
            print(f" 最高評分: {stats.get('max_rating', 0)}")

        # 示例查詢
        example_queries = [
            "找出評分最高的5部奇幻動漫",
            "顯示2024年秋季的所有動漫，按評分排序",
            "查找包含'冒險'類型且評分超過8.0的動漫",
            "統計每個季節的動漫數量"
        ]

        print(f"\n 示例查詢:")
        for i, query in enumerate(example_queries, 1):
            print(f"  {i}. {query}")

        # 執行示例查詢
        for query in example_queries[:2]:  # 執行前兩個示例
            try:
                results = await client.natural_language_query(query)
                print_query_results(results, f"查詢結果: {query}")
            except Exception as e:
                print(f" 查詢失敗: {e}")

        # 獲取所有類型
        print(f"\n 數據庫中的所有動漫類型:")
        all_genres = await client.get_all_genres()
        if all_genres:
            print(f"總共 {len(all_genres)} 種類型:")
            for i, genre in enumerate(all_genres[:20]):  # 只顯示前20個
                print(f"  {i+1:2d}. {genre}")
            if len(all_genres) > 20:
                print(f"  ... 還有 {len(all_genres) - 20} 種類型")

    except Exception as e:
        print(f" 系統錯誤: {e}")
        import traceback
        traceback.print_exc()

async def interactive_mode():
    """互動模式"""
    print(" 進入互動查詢模式")
    print("輸入自然語言查詢，例如: '找出評分最高的5部奇幻動漫'")
    print("輸入 'quit' 或 'exit' 結束")
    print("-" * 50)

    client = LLMDrivenSQLiteClient()
    await client.initialize()

    while True:
        try:
            user_input = input("\n 請輸入查詢: ").strip()

            if user_input.lower() in ['quit', 'exit', '退出']:
                print(" 再見！")
                break

            if not user_input:
                continue

            results = await client.natural_language_query(user_input)
            print_query_results(results, f"查詢結果: {user_input}")

        except KeyboardInterrupt:
            print("\n 再見！")
            break
        except Exception as e:
            print(f" 查詢錯誤: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            # 互動模式
            asyncio.run(interactive_mode())
        else:
            # 直接查詢模式
            query = " ".join(sys.argv[1:])

            async def single_query():
                client = LLMDrivenSQLiteClient()
                await client.initialize()
                results = await client.natural_language_query(query)
                print_query_results(results, f"查詢結果: {query}")

            asyncio.run(single_query())
    else:
        # 默認示例模式
        asyncio.run(main())