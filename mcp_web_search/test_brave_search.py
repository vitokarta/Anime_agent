# brave_search_test.py
import asyncio
import json
import os
import sys
from datetime import datetime
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

# 從環境變數讀取 Brave API Key
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "BSAz3v8ht4qeaKvSFqCmfZaN-Y9NVvN")

# 預設查詢參數
DEFAULT_QUERY = "who is the president of taiwan in 2025?"
DEFAULT_COUNT = 10        # 搜索結果數量
DEFAULT_OFFSET = 0        # 分頁 offset

from typing import Sequence

def parse_brave_plain_text(text: str) -> Dict[str, Any]:
    """
    解析 Brave Search 返回的純文本格式
    """
    results = []
    current_result = {}

    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            # 空行表示一個結果的結束
            if current_result:
                results.append(current_result)
                current_result = {}
            continue

        if line.startswith('Title: '):
            # 開始新的結果
            if current_result:
                results.append(current_result)
            current_result = {'title': line[7:].strip()}
        elif line.startswith('Description: '):
            current_result['description'] = line[13:].strip()
        elif line.startswith('URL: '):
            current_result['url'] = line[5:].strip()
        elif line.startswith('Site: '):
            current_result['site'] = line[6:].strip()
        elif line.startswith('Published: '):
            current_result['published'] = line[11:].strip()

    # 添加最後一個結果
    if current_result:
        results.append(current_result)

    return {
        'results': results,
        'total_results': len(results),
        'format': 'plain_text'
    }

def resolve_brave_search_tool_name(tools: Sequence) -> str | None:
    """
    尋找 Brave 搜索工具
    """
    for t in tools:
        name = getattr(t, "name", None)
        if isinstance(name, str) and name in ["brave_web_search", "brave_local_search"]:
            return name
    return None

async def brave_search(
    query: str,
    count: int = DEFAULT_COUNT,
    offset: int = DEFAULT_OFFSET,
    search_type: str = "web"  # "web" 或 "local"
) -> Dict[str, Any]:
    """
    呼叫 Brave Search MCP 工具並回傳 JSON 結構化結果。
    """
    # 檢查 BRAVE_API_KEY
    if not BRAVE_API_KEY:
        raise RuntimeError("BRAVE_API_KEY is not set. Please check your .env file or environment variables.")

    print(f"DEBUG: Using BRAVE_API_KEY: {BRAVE_API_KEY[:8]}...")

    # 用 npx 啟動 Brave Search MCP Server
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-brave-search"],
        env={"BRAVE_API_KEY": BRAVE_API_KEY},
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 列工具，找出 Brave Search 工具名
            tools = await session.list_tools()
            print(f"DEBUG: Available tools: {[getattr(t, 'name', 'unknown') for t in tools.tools]}")

            # 選擇搜索工具
            tool_name = "brave_web_search" if search_type == "web" else "brave_local_search"

            # 確認工具是否可用
            available_tools = [getattr(t, 'name', 'unknown') for t in tools.tools]
            if tool_name not in available_tools:
                raise RuntimeError(f"Tool {tool_name} not found. Available tools: {available_tools}")

            print(f"DEBUG: Using tool: {tool_name}")

            # 準備參數
            args = {"query": query}
            if count:
                args["count"] = int(count)
            if offset and search_type == "web":
                args["offset"] = int(offset)

            print(f"DEBUG: Calling tool with args: {args}")
            result = await session.call_tool(tool_name, arguments=args)
            print(f"DEBUG: Tool call result type: {type(result)}")
            print(f"DEBUG: Result content length: {len(result.content) if result.content else 0}")

            # 解析 MCP 回傳的 content
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
                raise RuntimeError("Brave Search returned no text content.")

            # 調試：打印原始回傳內容
            print(f"DEBUG: Raw response content: {repr(payload_text[:200])}")

            # 嘗試解析 JSON，如果失敗則解析純文本格式
            try:
                payload = json.loads(payload_text)
                print("DEBUG: Successfully parsed as JSON")
                return payload
            except json.JSONDecodeError as e1:
                print(f"DEBUG: JSON decode failed, parsing as plain text: {e1}")
                # Brave Search 返回純文本格式，需要解析
                return parse_brave_plain_text(payload_text)

def pretty_print_brave_results(payload: Dict[str, Any], max_items: int = 10) -> None:
    """
    把 Brave Search 結果漂亮地印出來
    """
    print(f"\nBrave Search Results:")

    # 檢查是否是我們解析的純文本格式
    if payload.get('format') == 'plain_text':
        results = payload.get('results', [])
        total_count = payload.get('total_results', len(results))
        print(f"Parsed from plain text format")
        print(f"Total results found: {total_count}")
    else:
        # 嘗試不同的結果路徑 (JSON 格式)
        results = []
        if 'web' in payload and 'results' in payload['web']:
            results = payload['web']['results']
        elif 'results' in payload:
            results = payload['results']
        elif 'web_results' in payload:
            results = payload['web_results']
        else:
            # 如果結構不明，打印整個 payload 的鍵
            print(f"DEBUG: Payload keys: {list(payload.keys())}")
            print(f"DEBUG: Full payload structure: {json.dumps(payload, indent=2, ensure_ascii=False)[:1000]}")
            return

    if not results:
        print("No results found.")
        return

    print(f"Showing {min(len(results), max_items)} of {len(results)} results:\n")

    for i, item in enumerate(results[:max_items], 1):
        title = item.get("title", item.get("name", ""))
        url = item.get("url", item.get("link", ""))
        description = item.get("description", item.get("snippet", ""))
        site = item.get("site", "")
        published = item.get("published", "")

        print(f"[{i}] {title}")
        print(f"    URL: {url}")
        if site:
            print(f"    Site: {site}")
        if published:
            print(f"    Published: {published}")
        if description:
            print(f"    Description: {description}")
        print()

def save_search_results_to_txt(query: str, payload: Dict[str, Any], filename: str = None) -> str:
    """
    將搜索結果保存為 txt 文件

    Args:
        query: 搜索查詢
        payload: 搜索結果
        filename: 可選的文件名

    Returns:
        保存的文件路徑
    """
    if filename is None:
        # 生成基於時間和查詢的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_query = safe_query.replace(' ', '_')[:50]  # 限制長度
        filename = f"search_results_{safe_query}_{timestamp}.txt"

    # 確保在 mcp_web_search 目錄下
    output_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(output_dir, filename)

    # 提取結果
    results = []
    if payload.get('format') == 'plain_text':
        results = payload.get('results', [])
    elif 'web' in payload and 'results' in payload['web']:
        results = payload['web']['results']
    elif 'results' in payload:
        results = payload['results']

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Brave Search Results\n")
            f.write(f"Query: {query}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Results: {len(results)}\n")
            f.write("=" * 80 + "\n\n")

            for i, result in enumerate(results, 1):
                f.write(f"[{i}] {result.get('title', 'No Title')}\n")
                f.write(f"URL: {result.get('url', 'No URL')}\n")

                if result.get('site'):
                    f.write(f"Site: {result.get('site')}\n")
                if result.get('published'):
                    f.write(f"Published: {result.get('published')}\n")

                description = result.get('description', result.get('snippet', ''))
                if description:
                    # 清理 HTML 標籤
                    import re
                    clean_desc = re.sub(r'<[^>]+>', '', description)
                    f.write(f"Description: {clean_desc}\n")

                f.write("-" * 60 + "\n\n")

        print(f"搜索結果已保存到: {filepath}")
        return filepath

    except Exception as e:
        print(f"保存文件失敗: {e}")
        return None

def answer_question_with_lemonade(query: str, search_results: str) -> str:
    """
    使用 Lemonade Server 上的 Qwen 根據搜索結果回答用戶問題
    """
    client = OpenAI(base_url=LEMONADE_BASE_URL, api_key=LEMONADE_API_KEY)

    system_prompt = """你是一個專業的搜索結果分析助手。請根據提供的網路搜索結果來回答用戶的問題。

要求：
1. 仔細分析搜索結果中的資訊
2. 直接回答用戶的問題，並引用相關的搜索結果
3. 如果搜索結果不足以完全回答問題，請說明哪些部分無法確定
4. 保持客觀，不要添加搜索結果中沒有的資訊
5. 用繁體中文回答

格式：
- 先直接回答問題
- 然後列出支持答案的關鍵資訊
- 最後提及資料來源"""

    user_prompt = f"""用戶問題：{query}

搜索結果：
{search_results}

請根據以上搜索結果回答用戶的問題。"""

    completion = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
    )
    return completion.choices[0].message.content

def summarize_with_lemonade(text: str) -> str:
    """
    舊的摘要函數（保留向後兼容）
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
    # python test_brave_search.py "amd ai pc hackathon" 20 0 web
    query = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUERY
    count = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_COUNT
    offset = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_OFFSET
    search_type = sys.argv[4] if len(sys.argv) > 4 else "web"

    print(f"Brave Searching ({search_type}): {query}")
    payload = await brave_search(
        query=query,
        count=count,
        offset=offset,
        search_type=search_type
    )

    pretty_print_brave_results(payload, max_items=count)

    # 保存搜索結果到 txt 文件
    try:
        saved_file = save_search_results_to_txt(query, payload)
        if saved_file:
            print(f"搜索結果已保存到: {saved_file}")
    except Exception as e:
        print(f"保存文件時出錯: {e}")

    # 使用 Qwen 根據搜索結果回答用戶問題
    try:
        # 提取結果進行問答
        results = []
        if payload.get('format') == 'plain_text':
            results = payload.get('results', [])
        elif 'web' in payload and 'results' in payload['web']:
            results = payload['web']['results']
        elif 'results' in payload:
            results = payload['results']
        elif 'web_results' in payload:
            results = payload['web_results']

        if results:
            # 取前 N 個結果用於問答
            top_results = results[:count]

            # 格式化搜索結果給 Qwen
            formatted_results = []
            for i, r in enumerate(top_results, 1):
                title = r.get('title', r.get('name', ''))
                description = r.get('description', r.get('snippet', ''))
                url = r.get('url', '')

                if title or description:
                    # 清理 HTML 標籤
                    import re
                    clean_title = re.sub(r'<[^>]+>', '', title) if title else ''
                    clean_desc = re.sub(r'<[^>]+>', '', description) if description else ''

                    formatted_results.append(f"結果 {i}:\n標題: {clean_title}\n描述: {clean_desc}\n網址: {url}")

            if formatted_results:
                search_results_text = "\n\n".join(formatted_results)
                answer = answer_question_with_lemonade(query, search_results_text)
                print("\n" + "=" * 60)
                print("Qwen 根據搜索結果的回答")
                print("=" * 60)
                print(answer)
                print("=" * 60)
    except Exception as e:
        print(f"\nQwen 問答功能出錯: {e}")
        print("可能原因：Lemonade Server 未運行或配置錯誤")

if __name__ == "__main__":
    asyncio.run(main())