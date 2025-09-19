# Lemonade Server 使用指南

## 伺服器連線資訊

**本機 IP 地址**: 192.168.107.209
**埠號**: 8000
**完整網址**: http://192.168.107.209:8000

## 如何連線到 Lemonade Server

### 本機使用者
- 瀏覽器開啟: http://localhost:8000
- 或使用: http://192.168.107.209:8000

### 同網路其他使用者
1. 確保與伺服器在同一個 WiFi 網路
2. 瀏覽器開啟: http://192.168.107.209:8000
3. 即可存取聊天介面、模型管理等功能

## 啟動伺服器

```bash
# 監聽所有網路介面（讓其他設備可以連線）
lemonade-server serve --host 0.0.0.0 --port 8000

# 只監聽本機
lemonade-server serve --host localhost --port 8000

連網路後使用ipconfig查看IPv4
```

## 環境變數配置

專案使用 `.env` 檔案管理配置，避免在程式碼中硬編碼 URL 和設定值。

### .env 檔案
```bash
# Lemonade Server 配置
LEMONADE_BASE_URL=http://192.168.107.209:8000/api/v1 #隨時變動
LEMONADE_API_KEY=lemonade

# 預設模型
DEFAULT_MODEL=Qwen-2.5-7B-Instruct-NPU
```

### 安裝依賴
```bash
uv pip install python-dotenv
```

## API 使用方式

### 使用 LemonadeClient 類別（推薦）
```python
from models.client import lemonade

# 簡單聊天
response = lemonade.simple_chat("你好！")
print(response)

# 複雜對話
messages = [
    {"role": "system", "content": "你是一個有用的助手"},
    {"role": "user", "content": "解釋量子計算"}
]
response = lemonade.chat(messages)
print(response)

# 取得可用模型
models = lemonade.get_available_models()
print(models)
```

### 直接使用 OpenAI 客戶端
```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LEMONADE_BASE_URL, LEMONADE_API_KEY, DEFAULT_MODEL
from openai import OpenAI

client = OpenAI(
    base_url=LEMONADE_BASE_URL,
    api_key=LEMONADE_API_KEY
)

response = client.chat.completions.create(
    model=DEFAULT_MODEL,
    messages=[
        {"role": "user", "content": "你好！"}
    ]
)
print(response.choices[0].message.content)
```
