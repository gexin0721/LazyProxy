import time
import sys
import os

# 添加父目录到路径以便导入 MCPClient
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'module', 'MCP', 'client'))

from MCPClient import MCPClient

# 创建客户端
client = MCPClient()

try:
    # 启动客户端
    print("启动客户端...")
    client.start()

    # 等待初始化
    while not client.get_initialized():
        time.sleep(0.1)
    print("客户端初始化完成")

    # 直接访问 self.tools 来检查数据结构
    print("\n" + "="*80)
    print("检查 tools 的类型和结构")
    print("="*80)

    print(f"\ntools 的类型: {type(client.tools)}")
    print(f"tools 的长度: {len(client.tools)}")

    if len(client.tools) > 0:
        first_tool = client.tools[0]
        print(f"\n第一个 tool 的类型: {type(first_tool)}")
        print(f"第一个 tool 的内容: {first_tool}")

        # 检查是否有属性
        print(f"\n第一个 tool 的属性列表:")
        if hasattr(first_tool, '__dict__'):
            print(f"  __dict__: {first_tool.__dict__}")

        # 尝试不同的访问方式
        print("\n尝试不同的访问方式:")

        # 方式1: 属性访问
        try:
            print(f"  tool.name: {first_tool.name}")
            print(f"  tool.description: {first_tool.description}")
            print(f"  tool.inputSchema: {first_tool.inputSchema}")
            print("  ✓ 属性访问成功")
        except Exception as e:
            print(f"  ✗ 属性访问失败: {e}")

        # 方式2: 字典访问
        try:
            print(f"  tool['name']: {first_tool['name']}")
            print(f"  tool['description']: {first_tool['description']}")
            print(f"  tool['inputSchema']: {first_tool['inputSchema']}")
            print("  ✓ 字典访问成功")
        except Exception as e:
            print(f"  ✗ 字典访问失败: {e}")

        # 方式3: 检查是否有 model_dump 或 dict 方法
        if hasattr(first_tool, 'model_dump'):
            print(f"\n  tool.model_dump(): {first_tool.model_dump()}")
        elif hasattr(first_tool, 'dict'):
            print(f"\n  tool.dict(): {first_tool.dict()}")

        # 打印所有可用的方法和属性
        print(f"\n第一个 tool 的所有属性和方法:")
        for attr in dir(first_tool):
            if not attr.startswith('_'):
                print(f"  - {attr}")

finally:
    print("\n关闭客户端...")
    client.close()
    print("完成")
