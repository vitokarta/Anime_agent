#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain ConversationSummaryBufferMemory Implementation
專注於實作 ConversationSummaryBufferMemory 記憶體機制
整合 Lemonade Server 提供帶記憶的動漫推薦對話
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Mapping

# 添加項目根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# LangChain imports
from langchain.memory import ConversationSummaryBufferMemory, ConversationBufferWindowMemory, ConversationSummaryMemory
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun

# 本地模組
from config import LEMONADE_BASE_URL, LEMONADE_API_KEY, DEFAULT_MODEL
from models.client import LemonadeClient

class LemonadeLanguageModel(LLM):
    """
    LangChain 兼容的 Lemonade Server 語言模型包裝器
    """

    def __init__(self, client: LemonadeClient, **kwargs):
        super().__init__(**kwargs)
        self._client = client

    @property
    def client(self) -> LemonadeClient:
        return self._client

    @property
    def _llm_type(self) -> str:
        return "lemonade"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """調用模型生成回應"""
        try:
            return self.client.simple_chat(prompt)
        except Exception as e:
            print(f"LLM 調用錯誤: {e}")
            return f"抱歉，無法生成回應: {e}"

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """獲取識別參數"""
        return {"model_name": "lemonade"}

class AnimeMemoryChat:
    """
    帶 ConversationSummaryBufferMemory 的動漫推薦對話系統
    """

    def __init__(self, user_id: str = "default_user", max_token_limit: int = 2000):
        self.user_id = user_id
        self.max_token_limit = max_token_limit

        # 初始化 Lemonade 客戶端和語言模型
        self.lemonade_client = LemonadeClient()
        self.llm = LemonadeLanguageModel(self.lemonade_client)

        # 初始化 ConversationSummaryBufferMemory
        self._init_memory()

        # 動漫推薦系統提示詞
        self.system_prompt = """
你是一個專業的動漫推薦助手。你的任務是根據用戶的喜好和對話歷史為他們推薦合適的動漫。

請注意以下幾點：
1. 記住用戶之前提到的喜好和已看過的動漫
2. 根據對話歷史了解用戶的口味變化
3. 提供個性化的推薦理由
4. 如果用戶提到具體的動漫，記住這些信息用於未來推薦
5. 回應要簡潔且有幫助

當前對話上下文：
{context}

請基於以上信息回應用戶的查詢。
"""

    def _init_memory(self):
        """初始化 ConversationSummaryBufferMemory"""
        try:
            self.memory = ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=self.max_token_limit,
                memory_key="chat_history",
                return_messages=False,  # 返回字符串而不是消息對象
                input_key="input",
                output_key="output"
            )
            print(f" ConversationSummaryBufferMemory 初始化成功 (token limit: {self.max_token_limit})")
        except Exception as e:
            print(f" Memory 初始化失敗: {e}")
            # 備用方案：使用基本記憶
            self.memory = None

    def chat(self, user_input: str, use_memory: bool = True) -> str:
        """
        進行帶記憶的對話

        Args:
            user_input: 用戶輸入
            use_memory: 是否使用記憶體上下文

        Returns:
            AI 回應
        """
        try:
            # 獲取記憶體上下文
            context = ""
            if use_memory and self.memory:
                memory_vars = self.memory.load_memory_variables({})
                context = memory_vars.get("chat_history", "")

            # 構建完整提示詞
            full_prompt = self.system_prompt.format(context=context)
            messages = [
                {"role": "system", "content": full_prompt},
                {"role": "user", "content": user_input}
            ]

            # 生成回應
            ai_response = self.lemonade_client.chat(messages)

            # 保存到記憶體
            if use_memory and self.memory:
                self.memory.save_context(
                    {"input": user_input},
                    {"output": ai_response}
                )

            return ai_response

        except Exception as e:
            return f"抱歉，發生錯誤: {e}"

    def get_memory_summary(self) -> str:
        """獲取記憶體摘要信息"""
        if not self.memory:
            return "記憶體未初始化"

        try:
            memory_vars = self.memory.load_memory_variables({})
            chat_history = memory_vars.get("chat_history", "")

            # 獲取記憶體統計
            buffer_length = len(self.memory.chat_memory.messages) if hasattr(self.memory, 'chat_memory') else 0

            return f"""
記憶體統計：
- Token 限制: {self.max_token_limit}
- 當前對話數: {buffer_length}
- 記憶體內容長度: {len(chat_history)} 字符

記憶體內容預覽:
{chat_history[:200]}{'...' if len(chat_history) > 200 else ''}
"""
        except Exception as e:
            return f"獲取記憶體信息時發生錯誤: {e}"

    def clear_memory(self):
        """清除記憶體"""
        if self.memory:
            try:
                self.memory.clear()
                print("記憶體已清除")
            except Exception as e:
                print(f"清除記憶體失敗: {e}")
        else:
            print("記憶體未初始化")

    def save_conversation_to_file(self, filename: str = None):
        """將對話記憶保存到文件"""
        if not filename:
            filename = f"conversation_{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        try:
            if self.memory:
                memory_vars = self.memory.load_memory_variables({})
                chat_history = memory_vars.get("chat_history", "")

                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"動漫推薦對話記錄 - 用戶: {self.user_id}\n")
                    f.write(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(chat_history)

                print(f"對話記錄已保存到: {filename}")
            else:
                print("沒有記憶體可保存")
        except Exception as e:
            print(f"保存對話記錄失敗: {e}")

def test_memory_functionality():
    """測試記憶體功能"""
    print("測試 ConversationSummaryBufferMemory 功能")
    print("=" * 60)

    # 創建對話系統
    chat = AnimeMemoryChat("test_user", max_token_limit=1000)

    # 測試對話列表
    test_conversations = [
        "我喜歡熱血動漫",
        "推薦更多類似的動漫",
        "請問你剛剛推薦我哪些動漫"
    ]

    print("\n進行測試對話...")
    for i, user_input in enumerate(test_conversations, 1):
        print(f"\n[{i}] 用戶: {user_input}")
        response = chat.chat(user_input)
        print(f"[{i}] AI: {response[:100]}{'...' if len(response) > 100 else ''}")

    # 顯示記憶體統計
    print("\n" + "=" * 60)
    print("記憶體統計信息")
    print("=" * 60)
    print(chat.get_memory_summary())

    # 保存對話記錄
    chat.save_conversation_to_file()

    # 清理
    chat.clear_memory()
    print("\n測試完成")

def interactive_chat_demo():
    """交互式對話演示"""
    print("\n動漫推薦記憶對話系統")
    print("=" * 60)
    print("基於 ConversationSummaryBufferMemory")
    print("輸入 'quit' 結束對話")
    print("輸入 'memory' 查看記憶體統計")
    print("輸入 'clear' 清除記憶體")
    print("輸入 'save' 保存對話記錄")
    print("-" * 60)

    # 設置記憶體參數
    token_limit = input("設置 token 限制 (默認 2000): ").strip()
    if not token_limit.isdigit():
        token_limit = 2000
    else:
        token_limit = int(token_limit)

    chat = AnimeMemoryChat("demo_user", max_token_limit=token_limit)

    while True:
        try:
            user_input = input("\n你: ").strip()

            if user_input.lower() in ['quit', 'exit', '退出']:
                print("再見！")
                break

            elif user_input.lower() == 'memory':
                print(chat.get_memory_summary())
                continue

            elif user_input.lower() == 'clear':
                chat.clear_memory()
                continue

            elif user_input.lower() == 'save':
                chat.save_conversation_to_file()
                continue

            elif not user_input:
                continue

            # 進行對話
            response = chat.chat(user_input)
            print(f"AI: {response}")

        except KeyboardInterrupt:
            print("\n 再見！")
            break
        except Exception as e:
            print(f" 錯誤: {e}")

def main():
    """主函數"""
    print(" LangChain ConversationSummaryBufferMemory 測試")
    print("=" * 60)

    # 先進行功能測試
    test_memory_functionality()

    # 詢問是否進行交互式演示
    # try:
    #     print("\n是否要進行交互式演示？ (y/n)")
    #     choice = input().strip().lower()
    #     if choice == 'y':
    #         interactive_chat_demo()
    # except (EOFError, KeyboardInterrupt):
    #     print("\n程序結束")

if __name__ == "__main__":
    main()