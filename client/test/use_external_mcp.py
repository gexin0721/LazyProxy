"""
调用外部 MCP 服务器
支持同时连接多个 MCP 服务器
"""

import json
import sys
import subprocess
from typing import List, Dict, Any, Optional

# 设置控制台编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class MCPClient:
    """MCP 客户端 - 用于连接单个 MCP 服务器"""

    def __init__(self, command: List[str], name: str = ""):
        """
        初始化客户端

        参数:
            command: 启动 MCP 服务器的命令
            name: 服务器名称（用于区分多个服务器）
        """
        self.name = name or command[0]
        print(f"启动 MCP 服务器 [{self.name}]: {' '.join(command)}")

        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self.request_id = 0
        self.tools = []

        # 获取工具列表
        self._discover_tools()

    def _send_request(self, method: str, params: Dict = None) -> Dict:
        """发送 JSON-RPC 请求"""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self.request_id
        }
        if params:
            request["params"] = params

        # 发送
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()

        # 接收
        response_line = self.process.stdout.readline()
        return json.loads(response_line)

    def _discover_tools(self):
        """获取工具列表"""
        response = self._send_request("tools/list")
        self.tools = response.get("result", {}).get("tools", [])
        print(f"  ✓ 发现 {len(self.tools)} 个工具")

    def list_tools(self) -> List[Dict]:
        """列出所有工具"""
        return self.tools

    def call_tool(self, name: str, arguments: Dict[str, Any] = None) -> str:
        """
        调用工具

        参数:
            name: 工具名称
            arguments: 工具参数

        返回:
            str: 工具执行结果
        """
        if arguments is None:
            arguments = {}

        response = self._send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })

        if "error" in response:
            raise Exception(f"错误: {response['error']['message']}")

        return response["result"]["content"][0]["text"]

    def close(self):
        """关闭客户端"""
        self.process.terminate()
        self.process.wait()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class MCPManager:
    """MCP 管理器 - 同时管理多个 MCP 服务器"""

    def __init__(self):
        """初始化管理器"""
        self.clients: Dict[str, MCPClient] = {}

    def add_server(self, name: str, command: List[str]) -> MCPClient:
        """
        添加一个 MCP 服务器

        参数:
            name: 服务器名称
            command: 启动命令

        返回:
            MCPClient: 客户端实例
        """
        if name in self.clients:
            raise ValueError(f"服务器 {name} 已存在")

        client = MCPClient(command, name)
        self.clients[name] = client
        return client

    def get_client(self, name: str) -> Optional[MCPClient]:
        """获取指定的客户端"""
        return self.clients.get(name)

    def list_all_tools(self) -> Dict[str, List[Dict]]:
        """列出所有服务器的工具"""
        all_tools = {}
        for name, client in self.clients.items():
            all_tools[name] = client.list_tools()
        return all_tools

    def call_tool(self, server_name: str, tool_name: str, arguments: Dict = None) -> str:
        """
        调用指定服务器的工具

        参数:
            server_name: 服务器名称
            tool_name: 工具名称
            arguments: 工具参数

        返回:
            str: 工具执行结果
        """
        client = self.clients.get(server_name)
        if not client:
            raise ValueError(f"服务器 {server_name} 不存在")

        return client.call_tool(tool_name, arguments)

    def close_all(self):
        """关闭所有客户端"""
        for name, client in self.clients.items():
            print(f"关闭服务器 [{name}]")
            client.close()
        self.clients.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_all()


# ============================================================================
# 可用的 MCP 服务器列表（正确的包名）
# ============================================================================

AVAILABLE_SERVERS = {
    "filesystem": {
        "package": "@modelcontextprotocol/server-filesystem",
        "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "."],
        "description": "文件系统操作（读写文件、列目录等）",
        "tools": ["read_file", "write_file", "list_directory", "search_files"]
    },
    "memory": {
        "package": "@modelcontextprotocol/server-memory",
        "command": ["npx", "-y", "@modelcontextprotocol/server-memory"],
        "description": "内存存储（键值对存储）",
        "tools": ["store_memory", "retrieve_memory"]
    },
    "fetch": {
        "package": "@modelcontextprotocol/server-fetch",
        "command": ["npx", "-y", "@modelcontextprotocol/server-fetch"],
        "description": "HTTP 请求（获取网页内容）",
        "tools": ["fetch"]
    },
    "brave-search": {
        "package": "@modelcontextprotocol/server-brave-search",
        "command": ["npx", "-y", "@modelcontextprotocol/server-brave-search"],
        "description": "Brave 搜索引擎（需要 BRAVE_API_KEY）",
        "tools": ["brave_web_search"],
        "requires_env": "BRAVE_API_KEY"
    },
    "github": {
        "package": "@modelcontextprotocol/server-github",
        "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
        "description": "GitHub API（需要 GITHUB_TOKEN）",
        "tools": ["search_repositories", "get_repository"],
        "requires_env": "GITHUB_TOKEN"
    }
}


# ============================================================================
# 示例 1: 单个服务器
# ============================================================================

def example_single_server():
    """使用单个 MCP 服务器"""
    print("="*80)
    print("示例 1: 使用单个 MCP 服务器（文件系统）")
    print("="*80)
    print()

    with MCPClient(["npx", "-y", "@modelcontextprotocol/server-filesystem", "."], "filesystem") as client:
        # 列出工具
        print("\n【可用工具】")
        for i, tool in enumerate(client.list_tools(), 1):
            print(f"{i}. {tool['name']}: {tool['description']}")

        # 调用工具
        print("\n【列出当前目录】")
        result = client.call_tool("list_directory", {"path": "."})
        print(result)

        print("\n【搜索 Python 文件】")
        result = client.call_tool("search_files", {"path": ".", "pattern": "*.py"})
        print(result)


# ============================================================================
# 示例 2: 多个服务器
# ============================================================================

def example_multiple_servers():
    """同时使用多个 MCP 服务器"""
    print("\n" + "="*80)
    print("示例 2: 同时使用多个 MCP 服务器")
    print("="*80)
    print()

    with MCPManager() as manager:
        # 添加文件系统服务器
        print("【添加服务器】")
        manager.add_server("filesystem", [
            "npx", "-y", "@modelcontextprotocol/server-filesystem", "."
        ])

        # 添加内存服务器
        manager.add_server("memory", [
            "npx", "-y", "@modelcontextprotocol/server-memory"
        ])

        # 添加 HTTP 请求服务器
        manager.add_server("fetch", [
            "npx", "-y", "@modelcontextprotocol/server-fetch"
        ])

        print()

        # 列出所有工具
        print("【所有服务器的工具】")
        all_tools = manager.list_all_tools()
        for server_name, tools in all_tools.items():
            print(f"\n服务器 [{server_name}]:")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")

        # 使用文件系统服务器
        print("\n【使用文件系统服务器】")
        result = manager.call_tool("filesystem", "list_directory", {"path": "."})
        print(result[:300] + "..." if len(result) > 300 else result)

        # 使用内存服务器
        print("\n【使用内存服务器 - 存储数据】")
        result = manager.call_tool("memory", "store_memory", {
            "key": "test_key",
            "value": "这是测试数据"
        })
        print(result)

        print("\n【使用内存服务器 - 读取数据】")
        result = manager.call_tool("memory", "retrieve_memory", {
            "key": "test_key"
        })
        print(result)

        # 使用 HTTP 请求服务器
        print("\n【使用 HTTP 请求服务器】")
        try:
            result = manager.call_tool("fetch", "fetch", {
                "url": "https://example.com"
            })
            print(result[:300] + "..." if len(result) > 300 else result)
        except Exception as e:
            print(f"请求失败: {e}")


# ============================================================================
# 示例 3: 实际应用场景
# ============================================================================

def example_real_world():
    """实际应用场景：AI 助手使用多个工具"""
    print("\n" + "="*80)
    print("示例 3: 实际应用场景 - AI 助手")
    print("="*80)
    print()

    with MCPManager() as manager:
        # 添加多个服务器
        print("【初始化 AI 助手的工具】")
        manager.add_server("filesystem", [
            "npx", "-y", "@modelcontextprotocol/server-filesystem", "."
        ])
        manager.add_server("memory", [
            "npx", "-y", "@modelcontextprotocol/server-memory"
        ])

        print()

        # 模拟 AI 助手的工作流程
        print("【场景：用户要求分析项目文件】")
        print("用户: '列出所有 Python 文件，并记住文件数量'\n")

        # 1. 搜索文件
        print("AI: 正在搜索 Python 文件...")
        files_result = manager.call_tool("filesystem", "search_files", {
            "path": ".",
            "pattern": "*.py"
        })
        print(files_result)

        # 2. 存储到内存
        print("\nAI: 正在记录文件数量...")
        file_count = files_result.count(".py")
        manager.call_tool("memory", "store_memory", {
            "key": "python_file_count",
            "value": str(file_count)
        })
        print(f"✓ 已记录: 找到 {file_count} 个 Python 文件")

        # 3. 后续查询
        print("\n【场景：用户询问之前的统计】")
        print("用户: '刚才找到了多少个 Python 文件？'\n")

        print("AI: 正在查询记录...")
        count = manager.call_tool("memory", "retrieve_memory", {
            "key": "python_file_count"
        })
        print(f"AI: 之前找到了 {count} 个 Python 文件")


# ============================================================================
# 交互模式
# ============================================================================

def interactive_mode():
    """交互模式 - 手动测试多个服务器"""
    print("\n" + "="*80)
    print("交互模式")
    print("="*80)
    print()

    with MCPManager() as manager:
        # 添加默认服务器
        print("【初始化服务器】")
        manager.add_server("filesystem", [
            "npx", "-y", "@modelcontextprotocol/server-filesystem", "."
        ])
        manager.add_server("memory", [
            "npx", "-y", "@modelcontextprotocol/server-memory"
        ])

        print("\n命令:")
        print("  list - 列出所有服务器和工具")
        print("  call <server> <tool> <json_args> - 调用工具")
        print("  quit - 退出")

        while True:
            try:
                cmd = input("\n> ").strip()

                if not cmd:
                    continue

                if cmd == "quit":
                    break

                elif cmd == "list":
                    all_tools = manager.list_all_tools()
                    for server_name, tools in all_tools.items():
                        print(f"\n服务器 [{server_name}]:")
                        for i, tool in enumerate(tools, 1):
                            print(f"  {i}. {tool['name']}: {tool['description']}")

                elif cmd.startswith("call "):
                    parts = cmd.split(maxsplit=3)
                    if len(parts) < 3:
                        print("用法: call <server> <tool> <json_args>")
                        continue

                    server_name = parts[1]
                    tool_name = parts[2]
                    args = json.loads(parts[3]) if len(parts) > 3 else {}

                    result = manager.call_tool(server_name, tool_name, args)
                    print(result)

                else:
                    print("未知命令")

            except KeyboardInterrupt:
                print("\n")
                break
            except Exception as e:
                print(f"错误: {e}")


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + " "*20 + "调用外部 MCP 服务器示例" + " "*20 + "█")
    print("█" + " "*78 + "█")
    print("█"*80)

    print("""
本示例演示:
1. 如何调用单个 MCP 服务器
2. 如何同时使用多个 MCP 服务器
3. 实际应用场景（AI 助手）
4. 交互模式

前提条件:
- 安装 Node.js (https://nodejs.org/)
- 使用 npx 自动下载并运行 MCP 服务器

可用的官方 MCP 服务器:
""")

    for name, info in AVAILABLE_SERVERS.items():
        env_note = f" (需要 {info['requires_env']})" if 'requires_env' in info else ""
        print(f"  - {name}: {info['description']}{env_note}")

    print()

    while True:
        print("\n请选择示例:")
        print("1. 单个服务器")
        print("2. 多个服务器")
        print("3. 实际应用场景")
        print("4. 交互模式")
        print("0. 退出")

        choice = input("\n请输入选项 (0-4): ").strip()

        try:
            if choice == "0":
                break
            elif choice == "1":
                example_single_server()
            elif choice == "2":
                example_multiple_servers()
            elif choice == "3":
                example_real_world()
            elif choice == "4":
                interactive_mode()
            else:
                print("无效选项")

        except FileNotFoundError:
            print("\n❌ 错误: 未找到 npx 命令")
            print("请先安装 Node.js: https://nodejs.org/")
            break
        except KeyboardInterrupt:
            print("\n\n用户中断")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()

    print("\n再见！")


if __name__ == "__main__":
    main()
