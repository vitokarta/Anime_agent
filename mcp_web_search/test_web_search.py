# mcp_smartsearch_test.py
import asyncio
import json
import os
import sys
from typing import Any, Dict, Optional

from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp import StdioServerParameters

# （可選）若你要保留 Lemonade / Qwen 摘要功能才需要
from openai import OpenAI

# === （可選）你的 Lemonade 伺服器設定，若不需要摘要可刪掉整段 ===
LEMONADE_BASE_URL = os.getenv("LEMONADE_BASE_URL", "http://localhost:8000/api/v1")
LEMONADE_API_KEY = os.getenv("LEMONADE_API_KEY", "lemonade")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "Qwen-2.5-7B-Instruct-NPU")
# ========================================================================

# 從環境變數讀取 SERVER_KEY；若沒有，退回你提供的字串（請確認是完整的 endpoint-accesskey）
SERVER_KEY = os.getenv("SERVER_KEY", "Aiim9UL2eRRsSPsU5hvx")

# 預設查詢參數（你可以改）
DEFAULT_QUERY = "who is the president of taiwan in 2025?"  # 查詢字串
DEFAULT_COUNT = 10        # 10,20,30,40,50
DEFAULT_OFFSET = 0        # 分頁 offset（從 0 起算）
DEFAULT_LANG = "en-US"    # 推薦使用 4 碼，如 en-US / zh-TW
DEFAULT_FRESHNESS = ""    # "", "Day", "Week", "Month" 或 "YYYY-MM-DD..YYYY-MM-DD"
DEFAULT_SITES = ""        # 例如 "github.com"（單一 host）

from typing import Sequence
from mcp.types import Tool  # 可選：只為了型別提示；沒裝也可不引入

def resolve_smartsearch_tool_name(tools: Sequence) -> str | None:
    """
    tools 為 Tool 物件清單（Pydantic model），用屬性讀取 name。
    """
    for t in tools:
        # Tool 物件通常有 .name 屬性；保守一點用 getattr
        name = getattr(t, "name", None)
        if isinstance(name, str) and name.lower() == "smartsearch":
            return name
    return None

async def smartsearch(
    query: str,
    count: int = DEFAULT_COUNT,
    offset: int = DEFAULT_OFFSET,
    setLang: str = DEFAULT_LANG,
    freshness: str = DEFAULT_FRESHNESS,
    sites: str = DEFAULT_SITES,
) -> Dict[str, Any]:
    """
    呼叫 SmartSearch MCP 工具並回傳 JSON 結構化結果。
    """
    # 檢查 SERVER_KEY
    if not SERVER_KEY:
        raise RuntimeError("SERVER_KEY is not set. Please check your .env file or environment variables.")

    print(f"DEBUG: Using SERVER_KEY: {SERVER_KEY[:8]}...")  # 只顯示前8個字符

    # 用 npx 啟動 SmartSearch MCP Server
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@cloudsway-ai/smartsearch"],
        env={"SERVER_KEY": SERVER_KEY},  # 把 key 傳給子行程
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 列工具，找出 SmartSearch 工具名
            tools = await session.list_tools()
            print(f"DEBUG: Available tools: {[getattr(t, 'name', 'unknown') for t in tools.tools]}")

            tool_name = resolve_smartsearch_tool_name(tools.tools)
            if not tool_name:
                available = [getattr(t, 'name', 'unknown') for t in tools.tools]
                raise RuntimeError(
                    f"SmartSearch tool not found. Available tools: {available}"
                )

            print(f"DEBUG: Using tool: {tool_name}")

            # 準備參數（空字串就不傳）
            args = {"query": query}
            if count: args["count"] = int(count)
            if offset: args["offset"] = int(offset)
            if setLang: args["setLang"] = setLang
            if freshness: args["freshness"] = freshness
            if sites: args["sites"] = sites

            print(f"DEBUG: Calling tool with args: {args}")
            result = await session.call_tool(tool_name, arguments=args)
            print(f"DEBUG: Tool call result type: {type(result)}")
            print(f"DEBUG: Result content length: {len(result.content) if result.content else 0}")

            # 解析 MCP 回傳的 content
            # 通常會是一個 JSON 字串放在 text 內容
            payload_text = None
            if result.content:
                for c in result.content:
                    text = getattr(c, "text", None)
                    if isinstance(text, str) and text.strip():
                        payload_text = text
                        break
                    if isinstance(c, dict) and isinstance(c.get("text"), str):
                        payload_text = c["text"]
                        break

            if not payload_text:
                raise RuntimeError("SmartSearch returned no text content.")

            # 調試：打印原始回傳內容
            print(f"DEBUG: Raw response content: {repr(payload_text)}")

            # 轉 JSON
            try:
                payload = json.loads(payload_text)
            except json.JSONDecodeError as e1:
                print(f"DEBUG: First JSON decode failed: {e1}")
                try:
                    # 有些伺服器可能會嵌套 JSON 字串，再試一次
                    payload = json.loads(json.loads(payload_text))
                except json.JSONDecodeError as e2:
                    print(f"DEBUG: Second JSON decode failed: {e2}")
                    print(f"DEBUG: Payload text length: {len(payload_text)}")
                    print(f"DEBUG: First 200 chars: {payload_text[:200]}")
                    raise RuntimeError(f"Failed to parse JSON response: {e1}. Raw content: {payload_text[:500]}")
            return payload

def pretty_print_results(payload: Dict[str, Any], max_items: int = 10) -> None:
    """
    把結果漂亮地印出來，便於檢視。
    """
    ctx = payload.get("queryContext", {})
    print(f"\nOriginal Query: {ctx.get('originalQuery','')}")
    pages = payload.get("webPages", {}).get("value", [])
    if not pages:
        print("No results.")
        return
    print(f"Total items shown (up to {max_items}): {min(len(pages), max_items)}\n")
    for i, item in enumerate(pages[:max_items], 1):
        name = item.get("name", "")
        url = item.get("url", "")
        snippet = item.get("snippet", "")
        site = item.get("siteName", "")
        date_pub = item.get("datePublished", "")
        score = item.get("score", "")
        print(f"[{i}] {name}")
        print(f"    URL      : {url}")
        if site:     print(f"    Site     : {site}")
        if date_pub: print(f"    Published: {date_pub}")
        if score:    print(f"    Score    : {score}")
        if snippet:  print(f"    Snippet  : {snippet}")
        print()

def summarize_with_lemonade(text: str) -> str:
    """
    （可選）把前幾筆搜尋結果的摘要丟到本地 Lemonade Server 上的 Qwen 做 3 點整理。
    """
    client = OpenAI(base_url=LEMONADE_BASE_URL, api_key=LEMONADE_API_KEY)
    completion = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes search results."},
            {"role": "user", "content": f"Summarize the following text into 3 concise bullet points:\n\n{text}"}
        ],
    )
    return completion.choices[0].message.content

async def main():
    # 可從命令列帶入查詢字串
    # python mcp_smartsearch_test.py "amd ai pc hackathon" 20 0 zh-TW Week github.com
    query     = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUERY
    count     = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_COUNT
    offset    = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_OFFSET
    setLang   = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_LANG
    freshness = sys.argv[5] if len(sys.argv) > 5 else DEFAULT_FRESHNESS
    sites     = sys.argv[6] if len(sys.argv) > 6 else DEFAULT_SITES

    print(f"Searching: {query}")
    payload = await smartsearch(
        query=query,
        count=count,
        offset=offset,
        setLang=setLang,
        freshness=freshness,
        sites=sites,
    )

    pretty_print_results(payload, max_items=count)

    # （可選）把前幾筆的標題+摘要拼起來做總結
    try:
        pages = payload.get("webPages", {}).get("value", [])[:min(5, count)]
        concat = "\n\n".join([f"{p.get('name','')}\n{p.get('snippet','')}" for p in pages])
        if concat.strip():
            summary = summarize_with_lemonade(concat)
            print("\n=== Qwen Summary ===")
            print(summary)
    except Exception as e:
        print("\n(Qwen summarize step skipped / failed)")
        print(e)

if __name__ == "__main__":
    asyncio.run(main())
