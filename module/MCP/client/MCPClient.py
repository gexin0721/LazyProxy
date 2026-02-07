import threading
import time
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import queue
import uuid
import os
import ast
import json
import re
class MCPClient:
    """简单的线程类"""
    def __init__(self):
        self.thread = None#线程对象
        self.running = False#运行状态
        self.paused = False#暂停状态
        self.pause_lock = threading.Lock()#暂停锁

        # 获取当前文件所在目录
        # 获取当前文件所在目录的父目录（MCP目录）
        current_dir = os.path.dirname(os.path.abspath(__file__))  # client目录
        parent_dir = os.path.dirname(current_dir)  # MCP目录
        server_path = os.path.join(parent_dir, "server", "MCPServer.py")

        self.server_params = StdioServerParameters(
            command="python",
            args=[server_path]
        )#服务器参数

        self.context = None # 上下文
        self.session = None # 会话
        self.tools = [] # 工具列表
        self.initialized = False # 初始化状态

        self.message_queue = queue.Queue() # 消息队列
        self.results = {} # 结果字典，key 为 uuid，value 为结果
    # ==================== 启动 ==================== 
    def start(self):
        """启动MCP客户端"""
        if self.thread is None or not self.thread.is_alive():
            self.running = True#设置运行状态为True
            self.paused = False#设置暂停状态为False
            self.thread = threading.Thread(target=self._run_sync)#创建线程
            self.thread.start()#启动线程

    # ==================== 关闭 ====================
    def close(self):
        """关闭MCP客户端"""
        self.running = False#设置运行状态为False
        self.paused = False#设置暂停状态为False
        if self.thread is not None:
            self.thread.join()#等待线程结束
            self.thread = None#设置线程为None
        
    # ==================== 暂停====================
    def pause(self):
        """暂停MCP客户端"""
        self.paused = True
    # ==================== 恢复====================  
    def resume(self):
        """恢复MCP客户端"""
        self.paused = False

    # ==================== 同步运行包装 ====================
    def _run_sync(self):
        """同步包装方法，在线程中运行事件循环"""
        try:
            asyncio.run(self._run_async())
        except Exception as e:
            print(f"[MCPClient] 运行时错误: {e}")
            import traceback
            traceback.print_exc()
            self.running = False

    # ==================== 异步运行====================
    async def _run_async(self):
        try:
            # 创建客户端
            # 参数：服务器参数
            # 返回：一个上下文管理器
            self.context = stdio_client(self.server_params)
            # 创建通信管道
            # read  管道：用来接收服务器发来的消息
            # write 管道：用来发送消息给服务器
            read, write = await self.context.__aenter__()

            # 创建会话
            self.session = ClientSession(read, write)
            # 启动后台监听任务
            await self.session.__aenter__()

            # 初始化（握手）
            await self.session.initialize()

            # 获取工具列表
            result = await self.session.list_tools()
            self.tools = result.tools if hasattr(result, 'tools') else result
            self.initialized = True

            while self.running:
                if self.paused:
                    time.sleep(0.1)
                    continue

                #如果队列为空
                if self.message_queue.empty():
                    continue
                # 取出顶部元素
                task = self.message_queue.get()
                # 移除顶部元素
                self.message_queue.task_done()

                task_id = task["id"]
                result = await self.session.call_tool(
                    task["name"],
                    task.get("arguments", {})
                )
                # 将结果存入字典
                self.results[task_id] = result

        finally:
            # 在异步环境中正确关闭资源
            if self.session:
                await self.session.__aexit__(None, None, None)
            if self.context:
                await self.context.__aexit__(None, None, None)

    # ==================== 添加任务 ====================
    def add(self, _data: dict) -> str:
        """
        添加任务到队列

        参数:
            data: 任务数据，包含 name 和 arguments

        返回:
            任务的 UUID
        """
        if _data is None:
            raise ValueError("数据不能为空")
        if self.running is False:
            raise ValueError("MCP客户端未启动")
        data = self.OpenAI_to_MCP(_data) # 将OpenAI工具转换为MCP工具
        # 生成 UUID
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "name": data["name"],
            "arguments": data.get("arguments", {})
        }
        self.message_queue.put(task)
        return task_id

    # ==================== 获取结果 ====================
    def get_result(self, task_id: str, block=True, timeout=None):
        """
        根据任务 ID 获取工具调用结果

        参数:
            task_id: 任务的 UUID
            block: 是否阻塞等待，默认 True
            timeout: 超时时间（秒），None 表示无限等待

        返回:
            工具调用的结果
        """
        if self.running is False:
            raise ValueError("MCP客户端未启动")

        if block:
            # 阻塞等待结果
            start_time = time.time()
            while True:
                if task_id in self.results:
                    result = self.results.pop(task_id)
                    return result

                # 检查超时
                if timeout is not None:
                    if time.time() - start_time > timeout:
                        raise TimeoutError(f"等待任务 {task_id} 结果超时")

                time.sleep(0.01)
        else:
            # 非阻塞，直接返回
            if task_id in self.results:
                return self.results.pop(task_id)
            else:
                raise KeyError(f"任务 {task_id} 的结果尚未准备好")

    # ==================== 获得工具 ====================
    def list_tools(self) -> list:
        if self.running is False:
            raise ValueError("MCP客户端未启动")
        if self.tools is None:
            raise ValueError("工具列表为空")
        if len(self.tools) == 0:
            raise ValueError("工具列表为空")
        return [self.MCP_to_OpenAI(tool) for tool in self.tools] # 将MCP工具转换为OpenAI工具

    def get_initialized(self) -> bool:
        return self.initialized

    def MCP_to_OpenAI(self, tool) -> dict:
        """将MCP工具转换为OpenAI工具"""
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        }
    def OpenAI_to_MCP(self, tool: dict) -> dict:
        """将OpenAI格式转换为MCP格式

        支持两种OpenAI格式：
        1. 工具定义格式（tool definition）：包含 description 和 parameters
        2. 工具调用格式（tool call）：包含 name 和 arguments
        """
        function = tool.get("function", {})

        # 判断是工具调用格式还是工具定义格式
        if "arguments" in function:
            # 工具调用格式：只需要 name 和 arguments
            arguments = function["arguments"]
            # 如果 arguments 是字符串，需要解析为字典
            if isinstance(arguments, str):
                # 处理空字符串的情况
                if arguments.strip() == "":
                    arguments = {}
                else:
                    arguments = json.loads(arguments)

            return {
                "name": function["name"],
                "arguments": arguments
            }
        else:
            # 工具定义格式：需要 description 和 inputSchema
            return {
                "name": function["name"],
                "description": function.get("description", ""),
                "inputSchema": function.get("parameters", {})
            }



# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 80)
    print("MCP 客户端综合测试")
    print("=" * 80)

    # 创建客户端
    client = MCPClient()
    test_db = "test_mcp.db"
    test_table = "users"
    test_file = "test_file.txt"
    test_json = "test_data.json"

    try:
        # 启动客户端
        print("\n[1] 启动客户端...")
        client.start()
        while not client.get_initialized():
            time.sleep(0.1)
        print("✓ 客户端启动成功")

        # 获取工具列表
        print("\n[2] 获取工具列表...")
        tools = client.list_tools()
        print(f"✓ 找到 {len(tools)} 个工具")

        # ==================== 数据库工具测试 ====================
        print("\n" + "=" * 80)
        print("数据库工具测试")
        print("=" * 80)

        # 创建数据库和表
        print("\n[3] 创建数据库...")
        task_id = client.add({"name": "connect", "arguments": {"db_name": test_db}})
        result = client.get_result(task_id, timeout=5)
        print(f"✓ {result}")

        print("\n[4] 创建数据表...")
        task_id = client.add({"name": "create_table", "arguments": {"db_name": test_db, "table_name": test_table}})
        result = client.get_result(task_id, timeout=5)
        print(f"✓ {result}")

        # 插入测试数据
        print("\n[5] 插入测试数据...")
        test_users = [
            ("001", "张三 - 软件工程师"),
            ("002", "李四 - 产品经理"),
            ("003", "王五 - 设计师")
        ]
        for uid, info in test_users:
            task_id = client.add({
                "name": "write",
                "arguments": {"db_name": test_db, "table_name": test_table, "data_id": uid, "content": info}
            })
            result = client.get_result(task_id, timeout=5)
            print(f"  {uid}: {result}")

        # 查询数据
        print("\n[6] 查询数据...")
        task_id = client.add({
            "name": "read",
            "arguments": {"db_name": test_db, "table_name": test_table, "data_id": "001"}
        })
        result = client.get_result(task_id, timeout=5)
        print(f"✓ 读取结果: {result}")

        # 统计记录
        print("\n[7] 统计记录数...")
        task_id = client.add({
            "name": "count_records",
            "arguments": {"db_name": test_db, "table_name": test_table}
        })
        result = client.get_result(task_id, timeout=5)
        print(f"✓ 记录数: {result}")

        # ==================== 文件编辑工具测试 ====================
        print("\n" + "=" * 80)
        print("文件编辑工具测试")
        print("=" * 80)

        # 创建测试文件
        print("\n[8] 创建测试文件...")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("第一行内容\n第二行内容\n第三行内容\n")
        print(f"✓ 测试文件已创建: {test_file}")

        # 读取所有行
        print("\n[9] 读取所有行...")
        task_id = client.add({"name": "read_all", "arguments": {"filepath": test_file}})
        result = client.get_result(task_id, timeout=5)
        print(f"✓ 文件内容: {result}")

        # 读取指定行
        print("\n[10] 读取第2行...")
        task_id = client.add({"name": "read_line", "arguments": {"filepath": test_file, "line_num": 2}})
        result = client.get_result(task_id, timeout=5)
        print(f"✓ 第2行: {result}")

        # 更新行
        print("\n[11] 更新第2行...")
        task_id = client.add({
            "name": "update_line",
            "arguments": {"filepath": test_file, "line_num": 2, "content": "第二行已更新"}
        })
        result = client.get_result(task_id, timeout=5)
        print(f"✓ 更新结果: {result}")

        # 追加行
        print("\n[12] 追加新行...")
        task_id = client.add({
            "name": "append_line",
            "arguments": {"filepath": test_file, "content": "第四行新增内容"}
        })
        result = client.get_result(task_id, timeout=5)
        print(f"✓ 追加结果: {result}")

        # 插入行
        print("\n[13] 在第1行插入...")
        task_id = client.add({
            "name": "insert_line",
            "arguments": {"filepath": test_file, "line_num": 1, "content": "这是插入的第一行"}
        })
        result = client.get_result(task_id, timeout=5)
        print(f"✓ 插入结果: {result}")

        # ==================== JSON文件操作测试 ====================
        print("\n" + "=" * 80)
        print("JSON文件操作测试")
        print("=" * 80)

        # 写入JSON
        print("\n[14] 写入JSON文件...")
        json_data = {"name": "测试项目", "version": "1.0.0", "author": "测试用户"}
        task_id = client.add({
            "name": "write_JSON",
            "arguments": {"filepath": test_json, "data": json_data}
        })
        result = client.get_result(task_id, timeout=5)
        print(f"✓ 写入结果: {result}")

        # 读取JSON
        print("\n[15] 读取JSON文件...")
        task_id = client.add({"name": "read_JSON", "arguments": {"filepath": test_json}})
        result = client.get_result(task_id, timeout=5)
        print(f"✓ JSON内容: {result}")

        # ==================== 数据查询工具测试 ====================
        print("\n" + "=" * 80)
        print("数据查询工具测试")
        print("=" * 80)

        # 查询文件行数
        print("\n[16] 查询文件行数...")
        task_id = client.add({"name": "file_line_count", "arguments": {"file_path": test_file}})
        result = client.get_result(task_id, timeout=5)
        print(f"✓ 文件行数: {result}")

        # 查询文件内容
        print("\n[17] 查询文件内容...")
        task_id = client.add({"name": "file_content", "arguments": {"file_path": test_file}})
        result = client.get_result(task_id, timeout=5)
        print(f"✓ 文件内容: {result}")

        # 查询数据库所有表
        print("\n[18] 查询数据库所有表...")
        task_id = client.add({"name": "database_all_table", "arguments": {"db_name": test_db}})
        result = client.get_result(task_id, timeout=5)
        print(f"✓ 数据库表: {result}")

        # 查询表内容
        print("\n[19] 查询表内容...")
        task_id = client.add({
            "name": "database_table_content",
            "arguments": {"db_name": test_db, "table_name": test_table}
        })
        result = client.get_result(task_id, timeout=5)
        print(f"✓ 表内容: {result}")

        # 检查数据是否存在
        print("\n[20] 检查数据是否存在...")
        task_id = client.add({
            "name": "database_table_data_exists",
            "arguments": {"db_name": test_db, "table_name": test_table, "data_id": "001"}
        })
        result = client.get_result(task_id, timeout=5)
        print(f"✓ 数据存在: {result}")

        # ==================== 批量任务压力测试 ====================
        print("\n" + "=" * 80)
        print("批量任务压力测试")
        print("=" * 80)

        print("\n[21] 批量添加50个任务...")
        task_ids = []
        start_time = time.time()

        for i in range(50):
            task_id = client.add({
                "name": "write",
                "arguments": {
                    "db_name": test_db,
                    "table_name": test_table,
                    "data_id": f"batch_{i:03d}",
                    "content": f"批量测试数据 {i}"
                }
            })
            task_ids.append(task_id)

        print(f"✓ 已添加 {len(task_ids)} 个任务")

        print("\n[22] 等待所有任务完成...")
        success_count = 0
        fail_count = 0

        for i, task_id in enumerate(task_ids):
            try:
                result = client.get_result(task_id, timeout=10)
                success_count += 1
                if i % 10 == 0:
                    print(f"  进度: {i+1}/{len(task_ids)}")
            except Exception as e:
                fail_count += 1
                print(f"  任务 {i} 失败: {e}")

        end_time = time.time()
        elapsed = end_time - start_time

        print(f"\n✓ 压力测试完成:")
        print(f"  总任务数: {len(task_ids)}")
        print(f"  成功: {success_count}")
        print(f"  失败: {fail_count}")
        print(f"  总耗时: {elapsed:.2f} 秒")
        print(f"  平均每任务: {elapsed/len(task_ids):.3f} 秒")

        # ==================== 多路径文件操作测试 ====================
        print("\n" + "=" * 80)
        print("多路径文件操作测试")
        print("=" * 80)

        # 定义测试路径
        test_paths = [
            r"C:\Users\xinge\Desktop\Eromang\client\modules\ai_assistant\Data",
            r"C:\Users\xinge\Desktop\Eromang\client\modules\ai_assistant\module\MCP\client"
        ]

        created_files = []

        print("\n[23] 在不同路径下创建和操作文件...")
        for i, path in enumerate(test_paths, 1):
            test_file_path = os.path.join(path, f"test_file_{i}.txt")
            test_json_path = os.path.join(path, f"test_data_{i}.json")

            print(f"\n  路径 {i}: {path}")

            # 确保目录存在
            if not os.path.exists(path):
                os.makedirs(path)
                print(f"    创建目录: {path}")

            # 创建文本文件
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write(f"路径{i}的测试内容\n第二行\n第三行\n")
            created_files.append(test_file_path)
            print(f"    ✓ 创建文件: {test_file_path}")

            # 测试读取
            task_id = client.add({
                "name": "read_all",
                "arguments": {"filepath": test_file_path}
            })
            result = client.get_result(task_id, timeout=5)
            print(f"    ✓ 读取成功: {result}")

            # 测试追加
            task_id = client.add({
                "name": "append_line",
                "arguments": {"filepath": test_file_path, "content": f"追加的第{i}行"}
            })
            result = client.get_result(task_id, timeout=5)
            print(f"    ✓ 追加成功")

            # 测试JSON写入
            json_data = {
                "path_id": i,
                "path": path,
                "test_name": f"多路径测试{i}",
                "timestamp": time.time()
            }
            task_id = client.add({
                "name": "write_JSON",
                "arguments": {"filepath": test_json_path, "data": json_data}
            })
            result = client.get_result(task_id, timeout=5)
            created_files.append(test_json_path)
            print(f"    ✓ JSON写入成功: {test_json_path}")

            # 测试JSON读取
            task_id = client.add({
                "name": "read_JSON",
                "arguments": {"filepath": test_json_path}
            })
            result = client.get_result(task_id, timeout=5)
            print(f"    ✓ JSON读取成功: {result}")

        print(f"\n✓ 多路径测试完成，共操作 {len(created_files)} 个文件")

        # ==================== 清理测试数据 ====================
        print("\n" + "=" * 80)
        print("清理测试数据")
        print("=" * 80)

        # 删除数据库
        print("\n[24] 删除测试数据库...")
        task_id = client.add({"name": "delete", "arguments": {"db_name": test_db}})
        result = client.get_result(task_id, timeout=5)
        print(f"✓ {result}")

        # 删除基础测试文件
        print("\n[25] 删除基础测试文件...")
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"✓ 已删除: {test_file}")
        if os.path.exists(test_json):
            os.remove(test_json)
            print(f"✓ 已删除: {test_json}")

        # 删除多路径测试文件
        print("\n[26] 删除多路径测试文件...")
        for file_path in created_files:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✓ 已删除: {file_path}")

        print(f"\n✓ 清理完成，共删除 {len(created_files) + 2} 个测试文件")

    except Exception as e:
        print(f"\n✗ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 关闭客户端
        print("\n[27] 关闭客户端...")
        client.close()
        print("✓ 客户端已关闭")

    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)
