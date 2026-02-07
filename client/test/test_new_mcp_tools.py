# -*- coding: utf-8 -*-
"""
测试新的 MCP 工具（WorkspaceManager 和 TaskManager）
"""
import sys
import os
import time

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from module.MCP.client.MCPClient import MCPClient

def test_workspace_manager():
    """测试 WorkspaceManager 工具"""
    print("\n" + "=" * 80)
    print("测试 WorkspaceManager 工具")
    print("=" * 80)

    client = MCPClient()

    try:
        # 启动客户端
        print("\n[1] 启动 MCP 客户端...")
        client.start()

        # 等待初始化
        while not client.get_initialized():
            time.sleep(0.1)
        print("✓ 客户端启动成功")

        # 获取工具列表
        print("\n[2] 获取工具列表...")
        tools = client.list_tools()
        workspace_tools = [t for t in tools if 'workspace' in t.name.lower() or 'scan' in t.name.lower()]
        print(f"✓ 找到 {len(workspace_tools)} 个 WorkspaceManager 工具:")
        for tool in workspace_tools:
            print(f"  - {tool.name}")

        # 测试 scan_workspace
        print("\n[3] 测试 scan_workspace...")
        test_dir = os.path.join(parent_dir, "Data")
        task_id = client.add({
            "name": "scan_workspace",
            "arguments": {
                "directory": test_dir,
                "max_depth": 2,
                "include_hidden": False
            }
        })
        result = client.get_result(task_id, timeout=10)
        print(f"✓ 扫描结果:")
        print(f"  根目录: {result.content[0].text if hasattr(result, 'content') else result}")

        # 测试 list_files_simple
        print("\n[4] 测试 list_files_simple...")
        task_id = client.add({
            "name": "list_files_simple",
            "arguments": {
                "directory": test_dir,
                "extensions": [".txt", ".json"]
            }
        })
        result = client.get_result(task_id, timeout=10)
        print(f"✓ 文件列表:")
        print(f"  {result.content[0].text if hasattr(result, 'content') else result}")

        print("\n✓ WorkspaceManager 工具测试完成")

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n[5] 关闭客户端...")
        client.close()
        print("✓ 客户端已关闭")

def test_task_manager():
    """测试 TaskManager 工具"""
    print("\n" + "=" * 80)
    print("测试 TaskManager 工具")
    print("=" * 80)

    client = MCPClient()

    try:
        # 启动客户端
        print("\n[1] 启动 MCP 客户端...")
        client.start()

        # 等待初始化
        while not client.get_initialized():
            time.sleep(0.1)
        print("✓ 客户端启动成功")

        # 获取工具列表
        print("\n[2] 获取工具列表...")
        tools = client.list_tools()
        task_tools = [t for t in tools if 'task' in t.name.lower()]
        print(f"✓ 找到 {len(task_tools)} 个 TaskManager 工具:")
        for tool in task_tools:
            print(f"  - {tool.name}")

        # 测试 create_task_list
        print("\n[3] 测试 create_task_list...")
        tasks = [
            {
                "task_id": "task_001",
                "description": "读取配置文件",
                "tool": "file_content",
                "arguments": {"file_path": "./Data/config.json"},
                "priority": 1
            },
            {
                "task_id": "task_002",
                "description": "查询数据库",
                "tool": "database_all_table",
                "arguments": {"db_name": "test.db"},
                "priority": 2,
                "depends_on": ["task_001"]
            }
        ]

        task_id = client.add({
            "name": "create_task_list",
            "arguments": {
                "tasks": tasks,
                "list_name": "测试任务列表"
            }
        })
        result = client.get_result(task_id, timeout=10)
        print(f"✓ 创建任务列表:")
        result_text = result.content[0].text if hasattr(result, 'content') else str(result)
        print(f"  {result_text}")

        # 从结果中提取 list_id
        import json
        try:
            result_dict = json.loads(result_text)
            list_id = result_dict.get("list_id")
        except:
            print("  警告: 无法解析 list_id，使用测试 ID")
            list_id = "test-list-id"

        if list_id and list_id != "test-list-id":
            # 测试 get_task_list
            print("\n[4] 测试 get_task_list...")
            task_id = client.add({
                "name": "get_task_list",
                "arguments": {"list_id": list_id}
            })
            result = client.get_result(task_id, timeout=10)
            print(f"✓ 获取任务列表:")
            print(f"  {result.content[0].text if hasattr(result, 'content') else result}")

            # 测试 get_next_task
            print("\n[5] 测试 get_next_task...")
            task_id = client.add({
                "name": "get_next_task",
                "arguments": {"list_id": list_id}
            })
            result = client.get_result(task_id, timeout=10)
            print(f"✓ 获取下一个任务:")
            print(f"  {result.content[0].text if hasattr(result, 'content') else result}")

            # 测试 get_task_summary
            print("\n[6] 测试 get_task_summary...")
            task_id = client.add({
                "name": "get_task_summary",
                "arguments": {"list_id": list_id}
            })
            result = client.get_result(task_id, timeout=10)
            print(f"✓ 获取任务摘要:")
            print(f"  {result.content[0].text if hasattr(result, 'content') else result}")

        print("\n✓ TaskManager 工具测试完成")

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\n[7] 关闭客户端...")
        client.close()
        print("✓ 客户端已关闭")

if __name__ == "__main__":
    print("=" * 80)
    print("MCP 新工具测试")
    print("=" * 80)

    # 测试 WorkspaceManager
    test_workspace_manager()

    # 等待一下
    time.sleep(2)

    # 测试 TaskManager
    test_task_manager()

    print("\n" + "=" * 80)
    print("所有测试完成")
    print("=" * 80)
