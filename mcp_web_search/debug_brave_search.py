#!/usr/bin/env python3
"""
Brave Search MCP 調試腳本
用於診斷 Brave Search 連接和設置問題
"""
import asyncio
import json
import os
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp import StdioServerParameters

# 從環境變數讀取配置
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "BSAz3v8ht4qeaKvSFqCmfZaN-Y9NVvN")

async def test_brave_connection():
    """測試 Brave Search MCP 服務器連接和基本功能"""

    print("🔍 開始測試 Brave Search MCP 連接...")
    print(f"📋 BRAVE_API_KEY: {BRAVE_API_KEY[:8]}...{'*' * 8}")

    try:
        # 設置服務器參數
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-brave-search"],
            env={"BRAVE_API_KEY": BRAVE_API_KEY},
        )
        print("✅ 服務器參數設置完成")

        # 嘗試連接
        print("🔌 正在連接 Brave Search MCP 服務器...")
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

                for i, tool in enumerate(tools.tools):
                    tool_name = getattr(tool, 'name', 'unknown')
                    tool_desc = getattr(tool, 'description', 'no description')
                    print(f"  [{i+1}] {tool_name}: {tool_desc}")

                # 檢查是否有 Brave Search 工具
                brave_tools = []
                for tool in tools.tools:
                    tool_name = getattr(tool, 'name', '')
                    if 'brave' in tool_name.lower():
                        brave_tools.append(tool_name)

                if not brave_tools:
                    print("❌ 未找到 Brave Search 工具")
                    return False

                print(f"✅ 找到 Brave Search 工具: {brave_tools}")

                # 測試 Web 搜索
                if "brave_web_search" in brave_tools:
                    print("🔍 正在測試 Web 搜索...")
                    web_args = {
                        "query": "hello world test",
                        "count": 3
                    }

                    web_result = await session.call_tool("brave_web_search", arguments=web_args)
                    print(f"✅ Web 搜索調用完成，返回內容數量: {len(web_result.content) if web_result.content else 0}")

                    # 檢查返回內容
                    if web_result.content:
                        for i, content in enumerate(web_result.content):
                            content_text = getattr(content, 'text', None)
                            if content_text:
                                print(f"📄 Web 搜索內容 {i+1} (前200字符): {content_text[:200]}")

                                # 嘗試解析 JSON
                                try:
                                    parsed = json.loads(content_text)
                                    print(f"✅ Web 搜索 JSON 解析成功，包含鍵: {list(parsed.keys())}")

                                    # 檢查搜索結果結構
                                    if 'web' in parsed and 'results' in parsed['web']:
                                        results_count = len(parsed['web']['results'])
                                        print(f"📊 找到 {results_count} 個 Web 搜索結果")
                                    elif 'results' in parsed:
                                        results_count = len(parsed['results'])
                                        print(f"📊 找到 {results_count} 個搜索結果")

                                except json.JSONDecodeError:
                                    # Brave Search 返回純文本格式，這是正常的
                                    print(f"✅ Web 搜索返回純文本格式 (這是正常的)")

                                    # 解析純文本結果
                                    lines = content_text.split('\n')
                                    result_count = 0
                                    for line in lines:
                                        if line.startswith('Title:'):
                                            result_count += 1

                                    print(f"📊 從純文本中解析到 {result_count} 個搜索結果")
                                    print(f"📄 示例結果: {lines[0] if lines else 'No content'}")

                                    # 如果有結果就算成功
                                    if result_count > 0:
                                        break
                                    else:
                                        print("⚠️ 沒有找到有效的搜索結果")
                                        return False

                # 測試 Local 搜索 (如果可用)
                if "brave_local_search" in brave_tools:
                    print("🏪 正在測試 Local 搜索...")
                    local_args = {
                        "query": "restaurant near me",
                        "count": 3
                    }

                    try:
                        local_result = await session.call_tool("brave_local_search", arguments=local_args)
                        print(f"✅ Local 搜索調用完成，返回內容數量: {len(local_result.content) if local_result.content else 0}")

                        if local_result.content:
                            for i, content in enumerate(local_result.content):
                                content_text = getattr(content, 'text', None)
                                if content_text:
                                    print(f"📄 Local 搜索內容 {i+1} (前200字符): {content_text[:200]}")
                    except Exception as e:
                        print(f"⚠️ Local 搜索測試失敗 (可能不支持): {e}")

                return True

    except Exception as e:
        print(f"❌ 測試失敗: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("=" * 60)
    print("Brave Search MCP 連接測試")
    print("=" * 60)

    success = await test_brave_connection()

    print("\n" + "=" * 60)
    if success:
        print("🎉 測試成功！Brave Search MCP 工作正常")
        print("💡 你可以使用 test_brave_search.py 進行搜索")
        print("📝 使用方法:")
        print("   python mcp_web_search\\test_brave_search.py \"your query\"")
        print("   python mcp_web_search\\test_brave_search.py \"your query\" 10 0 web")
    else:
        print("💥 測試失敗！請檢查以下項目：")
        print("1. BRAVE_API_KEY 是否正確")
        print("   - 檢查 .env 文件中的 BRAVE_API_KEY")
        print("   - 確認 API key 有效且未過期")
        print("2. 網絡連接是否正常")
        print("3. npx 和 @modelcontextprotocol/server-brave-search 是否已安裝")
        print("   - 運行: npx @modelcontextprotocol/server-brave-search --version")
        print("4. 防火牆是否阻止了連接")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())