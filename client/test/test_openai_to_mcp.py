#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 OpenAI_to_MCP 方法的格式转换功能
"""

import os
import sys

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from module.MCP.client.MCPClient import MCPClient

def test_tool_definition_format():
    """测试工具定义格式转换"""
    print("\n测试1: 工具定义格式转换")
    print("-" * 60)

    client = MCPClient()

    # OpenAI 工具定义格式
    tool_definition = {
        "type": "function",
        "function": {
            "name": "file_directory",
            "description": "列出目录下的文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "目录路径"
                    }
                },
                "required": ["file_path"]
            }
        }
    }

    result = client.OpenAI_to_MCP(tool_definition)

    print(f"输入: {tool_definition}")
    print(f"输出: {result}")

    # 验证结果
    assert "name" in result, "缺少 name 字段"
    assert "description" in result, "缺少 description 字段"
    assert "inputSchema" in result, "缺少 inputSchema 字段"
    assert result["name"] == "file_directory", "name 字段不正确"
    assert result["description"] == "列出目录下的文件", "description 字段不正确"

    print("✓ 工具定义格式转换成功")
    return True

def test_tool_call_format():
    """测试工具调用格式转换"""
    print("\n测试2: 工具调用格式转换")
    print("-" * 60)

    client = MCPClient()

    # OpenAI 工具调用格式（arguments 是字符串）
    tool_call = {
        "index": 0,
        "id": "call_00_a1E5gOpHc6H5eQRPrqrY8wY8",
        "function": {
            "arguments": "{\"file_path\": \"Data\"}",
            "name": "file_directory"
        },
        "type": "function"
    }

    result = client.OpenAI_to_MCP(tool_call)

    print(f"输入: {tool_call}")
    print(f"输出: {result}")

    # 验证结果
    assert "name" in result, "缺少 name 字段"
    assert "arguments" in result, "缺少 arguments 字段"
    assert result["name"] == "file_directory", "name 字段不正确"
    assert isinstance(result["arguments"], dict), "arguments 应该是字典类型"
    assert result["arguments"]["file_path"] == "Data", "arguments 内容不正确"

    print("✓ 工具调用格式转换成功")
    return True

def test_tool_call_format_with_dict_arguments():
    """测试工具调用格式转换（arguments 已经是字典）"""
    print("\n测试3: 工具调用格式转换（arguments 是字典）")
    print("-" * 60)

    client = MCPClient()

    # OpenAI 工具调用格式（arguments 已经是字典）
    tool_call = {
        "index": 0,
        "id": "call_00_xyz",
        "function": {
            "arguments": {"file_path": "Data"},
            "name": "file_directory"
        },
        "type": "function"
    }

    result = client.OpenAI_to_MCP(tool_call)

    print(f"输入: {tool_call}")
    print(f"输出: {result}")

    # 验证结果
    assert "name" in result, "缺少 name 字段"
    assert "arguments" in result, "缺少 arguments 字段"
    assert result["name"] == "file_directory", "name 字段不正确"
    assert isinstance(result["arguments"], dict), "arguments 应该是字典类型"
    assert result["arguments"]["file_path"] == "Data", "arguments 内容不正确"

    print("✓ 工具调用格式转换成功（字典参数）")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("OpenAI_to_MCP 方法测试")
    print("=" * 60)

    try:
        # 运行所有测试
        test1_passed = test_tool_definition_format()
        test2_passed = test_tool_call_format()
        test3_passed = test_tool_call_format_with_dict_arguments()

        # 总结
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        print(f"测试1（工具定义格式）: {'✓ 通过' if test1_passed else '✗ 失败'}")
        print(f"测试2（工具调用格式-字符串参数）: {'✓ 通过' if test2_passed else '✗ 失败'}")
        print(f"测试3（工具调用格式-字典参数）: {'✓ 通过' if test3_passed else '✗ 失败'}")

        if test1_passed and test2_passed and test3_passed:
            print("\n✓ 所有测试通过！")
        else:
            print("\n✗ 部分测试失败")

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
