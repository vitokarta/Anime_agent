#!/usr/bin/env python3
"""
MCP 回傳格式調試腳本
專門用於觀察 SQLite MCP server 的原始回傳內容和格式
"""
import asyncio
import json
import os
import ast
from typing import Any

from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp import StdioServerParameters

# 數據庫路徑
DB_PATH = os.path.abspath("anime_database.db")

async def debug_mcp_raw_response():
    """調試 MCP 原始回傳內容"""

    print("🔍 開始調試 MCP 原始回傳格式...")

    # 設置 SQLite MCP server 參數
    server_params = StdioServerParameters(
        command="uvx",
        args=["mcp-server-sqlite", "--db-path", DB_PATH],
        env={}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 測試 1: 簡單計數查詢
            print("\n" + "="*60)
            print("🧪 測試 1: 簡單計數查詢")
            print("="*60)

            count_query = "SELECT COUNT(*) as total FROM anime;"
            print(f"📋 查詢: {count_query}")

            result = await session.call_tool("read_query", arguments={"query": count_query})

            print(f"🔍 result 類型: {type(result)}")
            print(f"🔍 result.content 類型: {type(result.content)}")
            print(f"🔍 result.content 長度: {len(result.content) if result.content else 0}")

            if result.content:
                for i, content in enumerate(result.content):
                    print(f"\n--- Content {i+1} ---")
                    print(f"🔍 content 類型: {type(content)}")

                    text = getattr(content, 'text', None)
                    if text:
                        print(f"🔍 text 類型: {type(text)}")
                        print(f"🔍 text 長度: {len(text)}")
                        print(f"🔍 原始 text: {repr(text)}")
                        print(f"🔍 text 內容: {text}")

                        # 嘗試不同的解析方法
                        print("\n--- 解析測試 ---")

                        # 方法 1: JSON
                        try:
                            json_data = json.loads(text)
                            print(f"✅ JSON 解析成功: {type(json_data)}")
                            print(f"   數據: {json_data}")
                        except json.JSONDecodeError as e:
                            print(f"❌ JSON 解析失敗: {e}")

                        # 方法 2: ast.literal_eval
                        try:
                            ast_data = ast.literal_eval(text)
                            print(f"✅ ast.literal_eval 解析成功: {type(ast_data)}")
                            print(f"   數據: {ast_data}")
                        except (ValueError, SyntaxError) as e:
                            print(f"❌ ast.literal_eval 解析失敗: {e}")

            # 測試 2: 查詢奇幻動漫（限制1筆）
            print("\n" + "="*60)
            print("🧪 測試 2: 查詢奇幻動漫（1筆）")
            print("="*60)

            fantasy_query = """
            SELECT id, title, genres_json
            FROM anime
            WHERE genres_json LIKE '%奇幻%'
            LIMIT 1;
            """
            print(f"📋 查詢: {fantasy_query}")

            result2 = await session.call_tool("read_query", arguments={"query": fantasy_query})

            if result2.content:
                for i, content in enumerate(result2.content):
                    print(f"\n--- Content {i+1} ---")
                    text = getattr(content, 'text', None)
                    if text:
                        print(f"🔍 原始內容: {repr(text)}")
                        print(f"🔍 格式化內容:")
                        print(text)

                        # 嘗試解析
                        try:
                            ast_data = ast.literal_eval(text)
                            print(f"✅ 解析成功！數據類型: {type(ast_data)}")
                            if isinstance(ast_data, list) and ast_data:
                                first_item = ast_data[0]
                                print(f"   第一筆資料: {first_item}")
                                print(f"   title: {first_item.get('title', 'N/A')}")
                                print(f"   genres_json: {first_item.get('genres_json', 'N/A')}")
                        except Exception as e:
                            print(f"❌ 解析失敗: {e}")

            # 測試 3: list_tables
            print("\n" + "="*60)
            print("🧪 測試 3: list_tables")
            print("="*60)

            tables_result = await session.call_tool("list_tables", arguments={})

            if tables_result.content:
                for i, content in enumerate(tables_result.content):
                    text = getattr(content, 'text', None)
                    if text:
                        print(f"🔍 tables 原始內容: {repr(text)}")
                        print(f"🔍 tables 格式化內容: {text}")

                        try:
                            ast_data = ast.literal_eval(text)
                            print(f"✅ tables 解析成功: {ast_data}")
                        except Exception as e:
                            print(f"❌ tables 解析失敗: {e}")

async def main():
    print("🔬 MCP 原始回傳格式調試器")
    print("=" * 50)

    try:
        await debug_mcp_raw_response()
    except Exception as e:
        print(f"❌ 調試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())