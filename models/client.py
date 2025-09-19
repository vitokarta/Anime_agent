import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import LEMONADE_BASE_URL, LEMONADE_API_KEY, DEFAULT_MODEL
from openai import OpenAI

class LemonadeClient:
    def __init__(self, model=None, base_url=None, api_key=None):
        self.model = model or DEFAULT_MODEL
        self.client = OpenAI(
            base_url=base_url or LEMONADE_BASE_URL,
            api_key=api_key or LEMONADE_API_KEY
        )

    def chat(self, messages, model=None):
        """
        發送聊天請求

        Args:
            messages: 訊息列表 [{"role": "user", "content": "你好！"}]
            model: 可選的模型名稱，預設使用初始化時的模型

        Returns:
            str: 模型回應內容
        """
        response = self.client.chat.completions.create(
            model=model or self.model,
            messages=messages
        )
        return response.choices[0].message.content

    def simple_chat(self, message, model=None):
        """
        簡單聊天，只需傳入使用者訊息

        Args:
            message: 使用者訊息字串
            model: 可選的模型名稱

        Returns:
            str: 模型回應內容
        """
        messages = [{"role": "user", "content": message}]
        return self.chat(messages, model)

    def get_available_models(self):
        """
        取得可用的模型列表

        Returns:
            list: 模型列表
        """
        models = self.client.models.list()
        return [model.id for model in models.data]

# 預設客戶端實例
lemonade = LemonadeClient()

if __name__ == "__main__":
    # 測試範例
    print("=== 簡單聊天測試 ===")
    response = lemonade.simple_chat("你好！")
    print(response)

    print("\n=== 取得可用模型 ===")
    models = lemonade.get_available_models()
    for model in models:
        print(f"- {model}")