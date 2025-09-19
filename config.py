import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# Lemonade Server 配置
LEMONADE_BASE_URL = os.getenv('LEMONADE_BASE_URL', 'http://localhost:8000/v1')
LEMONADE_API_KEY = os.getenv('LEMONADE_API_KEY', 'lemonade')

# 預設模型
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'Qwen-2.5-7B-Instruct-NPU')
