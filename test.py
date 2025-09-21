import time
from models.client import lemonade

# 簡單聊天
start_time = time.time()
response = lemonade.simple_chat("你好！")
print(response)
end_time = time.time()
print(f"聊天耗時: {end_time - start_time} 秒")