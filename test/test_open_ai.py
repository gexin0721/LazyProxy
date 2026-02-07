# -*- coding: utf-8 -*-
"""
OPEN_AI 类测试脚本
"""
import sys
import os
import json
import asyncio

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
sys.path.insert(0, project_root)

from Software.AI.module.AICore.Client.OPEN_AI import OPEN_AI
from Software.AI.module.AICore.Model.deepseek import DeepSeek

# 配置路径
CONFIG_PATH = os.path.join(project_root, "Software", "AI", "module", "AICore", "role", "config.json")
SECRET_PATH = os.path.join(project_root, "Software", "AI", "module", "AICore", "role", "secret_key.json")

# 加载配置
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)
with open(SECRET_PATH, "r", encoding="utf-8") as f:
    secrets = json.load(f)

# 构造 DeepSeek 模型实例
model_config = config["deepseek"]["deepseek-reasoner"]
api_key = secrets["deepseek"]
model = DeepSeek({"key": api_key, "params": model_config})


def test_get_params():
    """测试获取参数"""
    print("=== test_get_params ===")
    client = OPEN_AI(model=model, system_prompt="测试系统提示")
    params = client.get_params()
    print(f"参数: {params}")
    assert "temperature" in params
    assert "max_tokens" in params
    print("PASS\n")


def test_set_params():
    """测试批量设置参数"""
    print("=== test_set_params ===")
    client = OPEN_AI(model=model, system_prompt="测试系统提示")
    client.set_params({"temperature": 0.5, "top_p": 0.9})
    params = client.get_params()
    assert params["temperature"] == 0.5
    assert params["top_p"] == 0.9
    print(f"设置后参数: temperature={params['temperature']}, top_p={params['top_p']}")
    print("PASS\n")


def test_set_tools():
    """测试工具设置"""
    print("=== test_set_tools ===")
    client = OPEN_AI(model=model, system_prompt="测试系统提示")
    tools = [{"type": "function", "function": {"name": "test_func", "description": "测试函数"}}]
    client.set_tools(tools)
    params = client.get_params()
    assert params["tools"] == tools
    print(f"工具已设置: {params['tools']}")
    print("PASS\n")


async def test_send_stream():
    """测试流式调用"""
    print("=== test_send_stream ===")
    client = OPEN_AI(model=model, system_prompt="你是一个助手")

    thinking = ""
    content = ""
    tool_calls = []

    async for chunk in client.send_stream("你好，请简短回复"):
        if "thinking" in chunk:
            print(chunk["thinking"], end="")
        if "content" in chunk:
            print(chunk["content"], end="")
        if "tool_calls" in chunk:
            tool_calls.extend(chunk["tool_calls"])

    # print(f"思考: {thinking}")
    # print(f"回复: {content}")
    if tool_calls:
        print(f"工具调用: {tool_calls}")
    print("PASS\n")


async def test_think_clear_without_tools():
    """测试无工具调用时思考内容被清除（多轮）"""
    print("=== test_think_clear_without_tools ===")

    rounds = 3  # 测试轮数
    for i in range(rounds):
        print(f"\n--- 第 {i+1}/{rounds} 轮 ---")
        client = OPEN_AI(model=model, system_prompt="你是一个助手")

        # 发送普通问题（不会触发工具调用）
        async for chunk in client.send_stream("你好，请简短回复"):
            if "thinking" in chunk:
                print(chunk["thinking"], end="")
            if "content" in chunk:
                print(chunk["content"], end="")

        print()  # 换行

        # 检查思考内容是否被清除
        think_counts = client._history.think_token_counts
        messages = client._history.messages

        print(f"  think_token_counts: {think_counts}")
        print(f"  messages数量: {len(messages)}")

        # 验证：无工具调用时，思考应该被清除
        assert len(think_counts) == 0, f"第{i+1}轮失败：think_token_counts应为空，实际为{think_counts}"

        # 验证：消息中不应包含 reasoning_content 字段
        for msg in messages:
            assert "reasoning_content" not in msg, f"第{i+1}轮失败：消息中不应包含reasoning_content字段"

        print(f"  第 {i+1} 轮验证通过")

    print("\nPASS\n")


async def test_think_keep_with_tools():
    """测试有工具调用时思考内容被保留（多轮）"""
    print("=== test_think_keep_with_tools ===")

    # 定义一个简单的工具
    tools = [{
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前时间",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }]

    rounds = 3  # 测试轮数
    for i in range(rounds):
        print(f"\n--- 第 {i+1}/{rounds} 轮 ---")
        client = OPEN_AI(model=model, system_prompt="你是一个助手，当用户询问时间时必须调用get_current_time工具")
        client.set_tools(tools)

        has_tool_calls = False

        # 发送会触发工具调用的问题
        async for chunk in client.send_stream("现在几点了？请调用工具获取时间"):
            if "thinking" in chunk:
                print(chunk["thinking"], end="")
            if "content" in chunk:
                print(chunk["content"], end="")
            if "tool_calls" in chunk:
                has_tool_calls = True
                print(f"\n  [工具调用]: {chunk['tool_calls']}")

        print()  # 换行

        # 检查结果
        think_counts = client._history.think_token_counts
        messages = client._history.messages

        print(f"  has_tool_calls: {has_tool_calls}")
        print(f"  think_token_counts: {think_counts}")
        print(f"  messages数量: {len(messages)}")

        # 如果有工具调用，思考应该被保留
        if has_tool_calls:
            # 检查是否有思考内容（可能模型没有思考）
            if len(think_counts) > 0:
                print(f"  验证通过：有工具调用，思考被保留")
                # 验证消息中包含 reasoning_content 字段
                last_msg = messages[-1]
                assert "reasoning_content" in last_msg, f"第{i+1}轮失败：有思考时消息应包含reasoning_content字段"
            else:
                print(f"  注意：模型本轮没有产生思考内容")
        else:
            # 没有工具调用，思考应该被清除
            assert len(think_counts) == 0, f"第{i+1}轮：无工具调用，思考应被清除"
            print(f"  注意：模型本轮没有调用工具，思考已清除")

        print(f"  第 {i+1} 轮完成")

    print("\nPASS\n")


async def test_think_clear_after_tool_result():
    """测试完整MCP调用链：工具调用后回传结果，最终回复时清除思考"""
    print("=== test_think_clear_after_tool_result ===")

    # 定义工具
    tools = [{
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前时间",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }]

    rounds = 2
    for i in range(rounds):
        print(f"\n--- 第 {i+1}/{rounds} 轮 ---")
        client = OPEN_AI(model=model, system_prompt="你是助手，询问时间时必须调用get_current_time工具")
        client.set_tools(tools)
        has_tool_calls = False

        # 步骤1：触发工具调用
        print("\n  [步骤1] 触发工具调用")
        async for chunk in client.send_stream("现在几点了？"):
            if "thinking" in chunk:
                print(chunk["thinking"], end="")
            if "content" in chunk:
                print(chunk["content"], end="")
            if "tool_calls" in chunk:
                has_tool_calls = True
                print(f"\n  [工具调用]: {chunk['tool_calls']}")

        print()
        think_step1 = len(client._history.think_token_counts)
        print(f"  步骤1后 think_token_counts长度: {think_step1}")

        if not has_tool_calls:
            print(f"  模型没有调用工具，跳过本轮")
            continue

        # 步骤2+：循环回传工具结果，直到模型不再调用工具
        step = 2
        while True:
            print(f"\n  [步骤{step}] 回传工具结果")
            has_more_tool_calls = False

            async for chunk in client.send_stream("当前时间是 2025-01-15 14:30:00", role="system"):
                if "thinking" in chunk:
                    print(chunk["thinking"], end="")
                if "content" in chunk:
                    print(chunk["content"], end="")
                if "tool_calls" in chunk:
                    has_more_tool_calls = True
                    print(f"\n  [工具调用]: {chunk['tool_calls']}")

            print()
            think_now = client._history.think_token_counts
            print(f"  步骤{step}后 think_token_counts: {think_now}")

            if not has_more_tool_calls:
                # 模型不再调用工具，MCP链结束
                break

            step += 1
            if step > 5:
                print("  警告：超过5轮工具调用，强制退出")
                break

        # 验证：最终回复后思考被清除
        think_final = client._history.think_token_counts
        assert len(think_final) == 0, f"第{i+1}轮失败：最终回复后思考应被清除"
        print(f"  验证通过：MCP链结束后，思考被清除 ✓")

    print("\nPASS\n")


# 运行测试
if __name__ == "__main__":
    test_get_params()
    test_set_params()
    test_set_tools()
    asyncio.run(test_send_stream())
    asyncio.run(test_think_clear_without_tools())
    asyncio.run(test_think_keep_with_tools())
    asyncio.run(test_think_clear_after_tool_result())
