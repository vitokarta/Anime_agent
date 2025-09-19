# from openai import OpenAI

# # Initialize the client to use Lemonade Server
# client = OpenAI(
#     base_url="http://localhost:8000/api/v1",
#     api_key="lemonade"  # required but unused
# )

# # Create a chat completion
# completion = client.chat.completions.create(
#     model = "Qwen-2.5-7B-Instruct-NPU",
#     #model="Qwen2.5-0.5B-Instruct-CPU",  # or any other available model
#     messages=[
#         {"role": "user", "content": "What is the capital of France?"}
#     ]
# )

# # Print the response
# print(completion.choices[0].message.content)

# mcp_fetch_test.py
import asyncio
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp import StdioServerParameters
from openai import OpenAI

FETCH_URL = "https://acgsecrets.hk/bangumi/202507/"   # 換成你想測的網址
MAX_LEN   = 2000                    # 一次取回的最大字元數

async def fetch_markdown(url, max_length=5000, start_index=0, raw=False):
    # 啟動 fetch server
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_server_fetch"]
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化連接
            await session.initialize()

            # 調用 fetch 工具
            result = await session.call_tool(
                "fetch",
                arguments={
                    "url": url,
                    "max_length": max_length,
                    "start_index": start_index,
                    "raw": raw,
                }
            )

            # 返回結果
            if result.content:
                for content in result.content:
                    if hasattr(content, 'text'):
                        return content.text
                    elif isinstance(content, dict) and 'text' in content:
                        return content['text']
            return None


def summarize_with_lemonade(markdown_text: str) -> str:
    """
    把抓到的 markdown 丟給 Lemonade Server 上的 Qwen-2.5-7B-Instruct-NPU 做簡短摘要。
    若只想確認抓取成功，你也可以只 print markdown，不用這段。
    """
    client = OpenAI(
        base_url="http://localhost:8000/api/v1",
        api_key="lemonade",
    )

    completion = client.chat.completions.create(
        model="Qwen-2.5-7B-Instruct-NPU",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes web content."},
            {
                "role": "user",
                "content": f"Summarize the following webpage content in 3 bullet points:\n\n{markdown_text}"
            },
        ],
    )
    return completion.choices[0].message.content


async def main():
    print(f"Fetching: {FETCH_URL}")
    md = await fetch_markdown(FETCH_URL, max_length=MAX_LEN, start_index=0, raw=False)

    if not md:
        print("No content returned from fetch server.")
        return

    # 先印出前 500 個字元，確認真的有拿到 markdown
    print("\n=== Fetched Markdown (first 500 chars) ===")
    print(md[:500])

    # （可選）用本地 Qwen 做摘要驗證
    try:
        summary = summarize_with_lemonade(md[:40])  # 避免太長
        print("\n=== Qwen Summary ===")
        print(summary)
    except Exception as e:
        print("\n(Qwen summarize step skipped / failed)")
        print(e)


if __name__ == "__main__":
    asyncio.run(main())
