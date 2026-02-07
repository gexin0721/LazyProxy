#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试数学工具调用
"""

import os
import sys

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from module.AICore.AIManager import AIFactory
from module.MCP.client.MCPClient import MCPClient
import time
import json
from typing import List, Dict, Any, Generator, Tuple


def merge_tool_calls(tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    合并流式返回的工具调用碎片

    在流式响应中，AI模型会将工具调用分成多个碎片返回：
    - 第一个碎片包含完整的工具调用结构（id, type, function.name等），但arguments字段为空
    - 后续碎片只包含arguments的部分内容，需要拼接起来

    参数:
        tool_calls: 从AI流式响应中收集的工具调用碎片列表

    返回:
        合并后的完整工具调用列表，每个工具调用的arguments已完整拼接

    示例:
        输入: [
              {'index': 0, 'id': 'call_00_5mkYO9b2I0Myf5IGSxbl6o4D', 'function': {'arguments': '', 'name': 'add'}, 'type': 'function'}
              {'index': 0, 'id': None, 'function': {'arguments': '{', 'name': None}, 'type': None}
              {'index': 0, 'id': None, 'function': {'arguments': '"', 'name': None}, 'type': None}
              {'index': 0, 'id': None, 'function': {'arguments': 'a', 'name': None}, 'type': None}
              {'index': 0, 'id': None, 'function': {'arguments': '"', 'name': None}, 'type': None}
              {'index': 0, 'id': None, 'function': {'arguments': ': ', 'name': None}, 'type': None}
              {'index': 0, 'id': None, 'function': {'arguments': '123', 'name': None}, 'type': None}
              {'index': 0, 'id': None, 'function': {'arguments': ', ', 'name': None}, 'type': None}
              {'index': 0, 'id': None, 'function': {'arguments': '"', 'name': None}, 'type': None}
              {'index': 0, 'id': None, 'function': {'arguments': 'b', 'name': None}, 'type': None}
              {'index': 0, 'id': None, 'function': {'arguments': '"', 'name': None}, 'type': None}
              {'index': 0, 'id': None, 'function': {'arguments': ': ', 'name': None}, 'type': None}
              {'index': 0, 'id': None, 'function': {'arguments': '456', 'name': None}, 'type': None}
              {'index': 0, 'id': None, 'function': {'arguments': '}', 'name': None}, 'type': None}
        ]
        输出: [
              {'index': 0,'id': '1', 'function': {'name': 'add', 'arguments': '{"a":123,"b":456}'}, 'type': 'function'}
        ]
    """
    if not tool_calls:
        return []

    merged = {}
    
    for tool in tool_calls:
        index = tool.get("index", 0)
        
        if index not in merged:
            # 初始化第一个碎片
            merged[index] = {
                "index": index,
                "id": tool.get("id", ""),
                "type": tool.get("type", ""),
                "function": {
                    "name": tool.get("function", {}).get("name", ""),
                    "arguments": tool.get("function", {}).get("arguments", "")
                }
            }
        else:
            # 合并后续碎片
            merged_tool = merged[index]
            
            # 只更新非空值
            if tool.get("id"):
                merged_tool["id"] = tool["id"]
            if tool.get("type"):
                merged_tool["type"] = tool["type"]
                
            func = tool.get("function", {})
            if func.get("name"):
                merged_tool["function"]["name"] = func["name"]
            if func.get("arguments"):
                merged_tool["function"]["arguments"] += func["arguments"]
    
    # 按索引排序并返回列表
    return [merged[key] for key in sorted(merged.keys())]


def process_ai_response(response_generator: Generator, print_output: bool = True) -> Tuple[str, List[Dict[str, Any]]]:
    """
    处理AI的流式响应，提取内容和工具调用

    AI的流式响应是一个生成器，每次yield一个字典，包含不同类型的数据：
    - content: AI生成的文本内容
    - thinking: AI的思考过程（如果模型支持）
    - tool_calls: AI决定调用的工具信息

    参数:
        response_generator: AI返回的流式响应生成器
        print_output: 是否实时打印输出内容，默认为True

    返回:
        (完整响应文本, 工具调用列表) 的元组
    """
    response = ""
    tool_calls = []

    # 遍历流式响应的每个数据块
    for chunk in response_generator:
        # 获取数据块的类型（content/thinking/tool_calls等）
        chunk_type = list(chunk.keys())[0] if chunk else "None"
        content = chunk.get(chunk_type)

        # 处理文本内容和思考过程
        if chunk_type in ["content", "thinking"]:
            response += content
            if print_output:
                print(content, end='', flush=True)

        # 收集工具调用信息
        elif chunk_type == "tool_calls":
            # content是一个列表，取第一个元素
            tool_calls.append(content[0])

    if print_output:
        print()  # 换行

    return response, tool_calls


def execute_tools(mcp_client: MCPClient, merged_tools: List[Dict[str, Any]]) -> List[str]:
    """
    批量执行工具调用并获取结果

    将合并后的工具调用提交给MCP客户端执行，并收集所有工具的执行结果。
    MCP（Model Context Protocol）客户端负责实际执行工具调用。

    参数:
        mcp_client: MCP客户端实例，用于执行工具调用
        merged_tools: 合并后的完整工具调用列表

    返回:
        工具执行结果的文本列表

    异常处理:
        如果工具执行出错（result.isError为True），会打印错误信息但不会中断流程
    """
    # 打印工具调用统计信息
    print(f"\n{'='*80}")
    print(f"检测到 {len(merged_tools)} 个工具调用")
    print(f"{'='*80}")

    # 第一步：批量提交所有工具调用任务
    task_ids = []
    for i, tool in enumerate(merged_tools, 1):
        tool_name = tool['function']['name']
        tool_args = tool['function']['arguments']

        task_id = mcp_client.add(tool)
        task_ids.append(task_id)

        print(f"\n[工具 {i}] {tool_name}")
        print(f"  参数: {tool_args}")
        print(f"  任务ID: {task_id}")

    # 第二步：批量获取所有任务的执行结果
    print(f"\n{'='*80}")
    print("执行结果")
    print(f"{'='*80}")

    tool_results = []
    for i, task_id in enumerate(task_ids, 1):
        result = mcp_client.get_result(task_id)

        print(f"\n[结果 {i}]")
        print(f"  任务ID: {task_id}")
        print(f"  内容: {result.content}")
        print(f"  是否出错: {result.isError}")

        # 检查是否执行出错
        if result.isError:
            print(f"  [WARNING] 工具执行出错!")

        # 提取工具结果的文本内容
        if result.content:
            tool_results.append(str(result.content))

    return tool_results


def test_math_tools():
    """测试数学工具调用"""
    #print("\n" + "=" * 80)
    #print("测试：数学工具调用")
    #print("=" * 80)

    # 初始化AI
    factory = AIFactory()
    factory.connect(
        dialogue_vendor="deepseek",
        dialogue_model_name="deepseek-reasoner",
        knowledge_vendor="deepseek",
        knowledge_model_name="deepseek-reasoner"
    )

    # 启动MCP客户端
    mcp_client = MCPClient()
    mcp_client.start()

    # 等待MCP初始化
    #print("\n等待MCP初始化...")
    while not mcp_client.get_initialized():
        time.sleep(0.1)

    # 获取工具列表
    tools = mcp_client.list_tools()
    #print(f"\n✓ 已获取 {len(tools)} 个工具")
    # for tool in tools:
        #print(f"  - {tool['function']['name']}: {tool['function'].get('description', '无描述')}")

    # 添加工具到对话模型
    factory.add_tools(tools, "dialogue")

    # 测试数学计算 - 使用需要多个工具调用的复杂问题
    message = "请帮我计算两个结果：第一个是 123 + 456 的和，第二个是 1000 - 234 的差"

    # 第一步：发送用户消息，获取AI的初始响应
    print(f"\n用户输入: {message}")
    print("\nAI回复: ", end='', flush=True)
    response, tool_calls = process_ai_response(factory.dialogue_callback(message))

    print("\n" + "-" * 80)
    print(f"工具调用原始数据: {tool_calls}")

    # 第二步：如果AI决定调用工具，则处理工具调用
    if tool_calls:
        # 合并流式返回的工具调用碎片
        merged_tools = merge_tool_calls(tool_calls)
        print(f"\n合并后的工具调用: {merged_tools}")

        # 执行工具调用并获取结果
        tool_results = execute_tools(mcp_client, merged_tools)

        # 第三步：将工具执行结果传回给AI，生成最终回复
        if tool_results:
            print("\n" + "-" * 80)
            print("将工具结果传回AI...")

            # 构建包含工具结果的消息
            tool_result_message = f"工具执行结果: {', '.join(tool_results)}"

            print(f"\n最终AI回复: ", end='', flush=True)
            _, _ = process_ai_response(factory.dialogue_callback(tool_result_message))
            print()

        # 打印测试总结
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)
        print(f"✓ 用户问题: {message}")
        print(f"✓ AI调用工具数量: {len(merged_tools)} 个")

        if len(merged_tools) > 1:
            print(f"✓ 多工具调用测试: 成功 - AI在一次问答中调用了 {len(merged_tools)} 个工具")
        elif len(merged_tools) == 1:
            print(f"✓ 单工具调用测试: 成功 - AI只调用了 1 个工具")

        print(f"✓ 工具列表:")
        for i, tool in enumerate(merged_tools, 1):
            print(f"  {i}. {tool['function']['name']} - 参数: {tool['function']['arguments']}")

        print("=" * 80)

    else:
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)
        print("✗ 未检测到工具调用 - AI没有使用任何工具")
        print("=" * 80)

    # 清理
    mcp_client.close()

    return response


if __name__ == "__main__":
    try:
        test_math_tools()


    except Exception as e:
        #print(f"\n\n测试失败: {e}")
        import traceback
        traceback.print_exc()
