#!/usr/bin/env python3
"""
SQLite MCP server 連接調試腳本
用於測試 SQLite MCP server 基本連接和功能
"""
import asyncio
import json
import os
from pathlib import Path

from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp import StdioServerParameters

# 數據庫路徑
DB_PATH = os.path.abspath("anime_database.db")

async def test_sqlite_mcp_connection():
    """測試 SQLite MCP server 連接和基本功能"""

    print("🔍 開始測試 SQLite MCP server 連接...")
    print(f"📂 數據庫路徑: {DB_PATH}")

    # 檢查數據庫文件是否存在
    if not os.path.exists(DB_PATH):
        print(f"❌ 數據庫文件不存在: {DB_PATH}")
        print("💡 請先創建數據庫或檢查路徑是否正確")
        return False

    print(f"✅ 數據庫文件存在: {os.path.getsize(DB_PATH)} bytes")

    try:
        # 設置 SQLite MCP server 參數
        server_params = StdioServerParameters(
            command="uvx",
            args=["mcp-server-sqlite", "--db-path", DB_PATH],
            env={}
        )
        print("✅ SQLite MCP server 參數設置完成")

        # 嘗試連接
        print("🔌 正在連接 SQLite MCP server...")
        async with stdio_client(server_params) as (read, write):
            print("✅ stdio_client 連接成功")

            async with ClientSession(read, write) as session:
                print("✅ ClientSession 建立成功")

                # 初始化會話
                print("🔄 正在初始化會話...")
                await session.initialize()
                print("✅ 會話初始化完成")

                # 列出可用工具
                print("🛠️ 正在獲取可用工具...")
                tools = await session.list_tools()
                print(f"✅ 獲取到 {len(tools.tools)} 個工具")

                tool_names = []
                for i, tool in enumerate(tools.tools):
                    tool_name = getattr(tool, 'name', 'unknown')
                    tool_desc = getattr(tool, 'description', 'no description')
                    print(f"  [{i+1}] {tool_name}: {tool_desc[:100]}...")
                    tool_names.append(tool_name)

                # 檢查必要工具
                required_tools = ['read_query', 'list_tables', 'describe_table']
                missing_tools = [tool for tool in required_tools if tool not in tool_names]

                if missing_tools:
                    print(f"❌ 缺少必要工具: {missing_tools}")
                    return False

                print("✅ 所有必要工具都可用")

                # 測試 list_tables
                print("\n📋 測試 list_tables 功能...")
                tables_result = await session.call_tool("list_tables", arguments={})

                if tables_result.content:
                    for content in tables_result.content:
                        content_text = getattr(content, 'text', None)
                        if content_text:
                            try:
                                # 嘗試 JSON 解析
                                tables_data = json.loads(content_text)
                                print(f"✅ 找到 {len(tables_data)} 個數據表:")
                                for table in tables_data:
                                    print(f"  - {table}")
                            except json.JSONDecodeError:
                                try:
                                    # 嘗試 ast.literal_eval
                                    import ast
                                    tables_data = ast.literal_eval(content_text)
                                    print(f"✅ 找到 {len(tables_data)} 個數據表:")
                                    for table in tables_data:
                                        table_name = table.get('name', table) if isinstance(table, dict) else table
                                        print(f"  - {table_name}")
                                except (ValueError, SyntaxError):
                                    print(f"⚠️ Tables 解析失敗: {content_text}")

                # 測試 describe_table (如果 anime 表存在)
                print("\n🔍 測試 describe_table 功能...")
                try:
                    describe_result = await session.call_tool(
                        "describe_table",
                        arguments={"table_name": "anime"}
                    )

                    if describe_result.content:
                        for content in describe_result.content:
                            content_text = getattr(content, 'text', None)
                            if content_text:
                                try:
                                    # 嘗試 JSON 解析
                                    schema_data = json.loads(content_text)
                                    print(f"✅ anime 表結構:")
                                    for column in schema_data:
                                        col_name = column.get('name', 'unknown')
                                        col_type = column.get('type', 'unknown')
                                        col_notnull = column.get('notnull', False)
                                        print(f"  - {col_name}: {col_type} {'(NOT NULL)' if col_notnull else ''}")
                                except json.JSONDecodeError:
                                    try:
                                        # 嘗試 ast.literal_eval
                                        import ast
                                        schema_data = ast.literal_eval(content_text)
                                        print(f"✅ anime 表結構:")
                                        for column in schema_data:
                                            col_name = column.get('name', 'unknown')
                                            col_type = column.get('type', 'unknown')
                                            col_notnull = column.get('notnull', False)
                                            print(f"  - {col_name}: {col_type} {'(NOT NULL)' if col_notnull else ''}")
                                    except (ValueError, SyntaxError):
                                        print(f"⚠️ Schema 解析失敗: {content_text}")
                except Exception as e:
                    print(f"⚠️ describe_table 測試失敗: {e}")

                # 測試簡單的 read_query
                print("\n🔍 測試 read_query 功能...")
                try:
                    query_result = await session.call_tool(
                        "read_query",
                        arguments={"query": "SELECT COUNT(*) as total FROM anime;"}
                    )

                    if query_result.content:
                        for content in query_result.content:
                            content_text = getattr(content, 'text', None)
                            if content_text:
                                try:
                                    # 嘗試 JSON 解析
                                    data = json.loads(content_text)
                                    if isinstance(data, list) and data:
                                        total_count = data[0].get('total', 0)
                                        print(f"✅ 數據庫中共有 {total_count} 條動漫記錄")
                                    else:
                                        print(f"⚠️ 查詢結果格式異常: {data}")
                                except json.JSONDecodeError:
                                    try:
                                        # 嘗試 ast.literal_eval
                                        import ast
                                        data = ast.literal_eval(content_text)
                                        if isinstance(data, list) and data:
                                            total_count = data[0].get('total', 0)
                                            print(f"✅ 數據庫中共有 {total_count} 條動漫記錄")
                                        else:
                                            print(f"⚠️ 查詢結果格式異常: {data}")
                                    except (ValueError, SyntaxError):
                                        print(f"⚠️ Query 解析失敗: {content_text}")
                except Exception as e:
                    print(f"⚠️ read_query 測試失敗: {e}")

                print("\n✅ SQLite MCP server 連接測試完成")
                return True

    except Exception as e:
        print(f"❌ 測試失敗: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("=" * 60)
    print("SQLite MCP Server 連接測試")
    print("=" * 60)

    success = await test_sqlite_mcp_connection()

    print("\n" + "=" * 60)
    if success:
        print("🎉 測試成功！SQLite MCP server 工作正常")
        print("💡 你可以使用 test_sqlite.py 進行動漫搜索")
        print("📝 使用方法:")
        print("   python mcp_sqlite\\test_sqlite.py")
        print("   python mcp_sqlite\\test_sqlite.py 奇幻 5")
    else:
        print("💥 測試失敗！請檢查以下項目：")
        print("1. 數據庫文件是否存在:")
        print(f"   - 檢查路徑: {DB_PATH}")
        print("   - 運行: python utils/database/create_schema.py")
        print("2. SQLite MCP server 是否已安裝:")
        print("   - 運行: uvx mcp-server-sqlite --help")
        print("3. MCP 依賴是否已安裝:")
        print("   - 運行: uv pip install mcp")
        print("4. 網絡連接和權限是否正常")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())