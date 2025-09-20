#!/usr/bin/env python3
"""
簡化的 MCP SmartSearch 調試腳本
用於診斷連接和設置問題
"""
import asyncio
import json
import os
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp import StdioServerParameters

# 從環境變數讀取配置
SERVER_KEY = os.getenv("SERVER_KEY", "Aiim9UL2eRRsSPsU5hvx")

async def test_mcp_connection():
    """測試 MCP 服務器連接和基本功能"""

    print("🔍 開始測試 MCP SmartSearch 連接...")
    print(f"📋 SERVER_KEY: {SERVER_KEY[:8]}...{'*' * 8}")

    try:
        # 設置服務器參數
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@cloudsway-ai/smartsearch"],
            env={"SERVER_KEY": SERVER_KEY},
        )
        print("✅ 服務器參數設置完成")

        # 嘗試連接
        print("🔌 正在連接 MCP 服務器...")
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

                # 檢查是否有 SmartSearch 工具
                smartsearch_tool = None
                for tool in tools.tools:
                    if getattr(tool, 'name', '').lower() == 'smartsearch':
                        smartsearch_tool = tool
                        break

                if not smartsearch_tool:
                    print("❌ 未找到 SmartSearch 工具")
                    return False

                print("✅ 找到 SmartSearch 工具")

                # 嘗試一個簡單的搜索請求
                print("🔍 正在測試簡單搜索...")
                simple_args = {
                    "query": "hello world",
                    "count": 3
                }

                result = await session.call_tool("smartsearch", arguments=simple_args)
                print(f"✅ 工具調用完成，返回內容數量: {len(result.content) if result.content else 0}")

                # 檢查返回內容
                if result.content:
                    for i, content in enumerate(result.content):
                        content_text = getattr(content, 'text', None)
                        if content_text:
                            print(f"📄 內容 {i+1} (前100字符): {content_text[:100]}")
                            # 嘗試解析 JSON
                            try:
                                parsed = json.loads(content_text)
                                print(f"✅ JSON 解析成功，包含鍵: {list(parsed.keys())}")
                                return True
                            except json.JSONDecodeError as e:
                                print(f"❌ JSON 解析失敗: {e}")
                                print(f"📄 原始內容: {content_text}")
                                return False
                else:
                    print("❌ 沒有返回內容")
                    return False

    except Exception as e:
        print(f"❌ 測試失敗: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("=" * 50)
    print("MCP SmartSearch 連接測試")
    print("=" * 50)

    success = await test_mcp_connection()

    print("\n" + "=" * 50)
    if success:
        print("🎉 測試成功！MCP SmartSearch 工作正常")
        print("💡 你可以繼續使用 test_web_search.py")
    else:
        print("💥 測試失敗！請檢查以下項目：")
        print("1. SERVER_KEY 格式問題：")
        print("   - 需要格式: endpoint-accesskey")
        print("   - 請到 https://console.cloudsway.ai 註冊")
        print("   - 獲取你的 Endpoint 和 AccessKey")
        print("   - 在 .env 文件中設置: SERVER_KEY=your-endpoint-your-accesskey")
        print("2. 網絡連接是否正常")
        print("3. npx 和 @cloudsway-ai/smartsearch 是否已安裝")
        print("4. 防火牆是否阻止了連接")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())