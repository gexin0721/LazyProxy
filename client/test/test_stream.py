# -*- coding: utf-8 -*-
"""
极简流式调用测试 - 观察数据流
"""
from openai import OpenAI
import json

# DeepSeek配置
client = OpenAI(
    api_key="sk-3cc5da1170e244ddbf0ef474cabb0517",
    base_url="https://api.deepseek.com"
)

# 定义一个简单的MCP工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"}
                },
                "required": ["city"]
            }
        }
    }
]

messages = [
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "北京今天天气怎么样？"}
]

print("=" * 60)
print("开始流式请求...")
print("=" * 60)

stream = client.chat.completions.create(
    model="deepseek-reasoner",  # 或 deepseek-chat
    messages=messages,
    tools=tools,
    stream=True
)

for i, chunk in enumerate(stream):
    print(f"\n--- chunk {i} ---")
    # 打印原始数据
    chunk_dict = chunk.model_dump()
    print(json.dumps(chunk_dict, ensure_ascii=False, indent=2))
