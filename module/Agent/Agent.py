# -*- coding: utf-8 -*-
"""
简化的对话处理器
使用 MCP 工具实现简单的对话流程
"""
import json
import time
from typing import Callable, Any
import asyncio

import logging
from typing import List, Dict, Any, Generator, Tuple
from enum import Enum
# 配置日志
logger = logging.getLogger(__name__)

class State(Enum):
    """
    状态枚举：定义系统所有可能的状态
    """
    IDLE = 1                      #空闲状态
    MODEL_A_DECIDING = 2          #模型A正在做决策（判断走哪个分支）
    DIRECT_ANSWER = 3             #模型A直接回答问题
    CALL_MCP_TOOL = 4             #调用MCP工具
    COMPLEX_TASK_PLANNING = 5     #复杂任务：生成目标规划
    MODEL_B_JUDGING = 6           #模型B判断是否需要介入
    MODEL_B_EXECUTING = 7         #模型B细化规划并执行TODO
    MODEL_A_SUMMARIZING = 8       #模型A汇总模型B的数据
    ENDING = 9                    #结束状态


class Agent:
    """
    简化的对话处理器
Agent
    流程：
    1. while 循环：对话模型判断是否结束对话
    2. 第一个 for：知识模型生成并执行 TODO 列表（通过 MCP）
    3. 第二个 for：对话模型的 TODO 列表（通过 MCP）
    """

    def __init__(
        self,
        dialogue_callback: Callable[[str], Any],
        knowledge_callback: Callable[[str], Any],

        mcp_client_add_task_callback: Callable[[dict], Any],
        mcp_client_execute_task_callback: Callable[[dict], Any]
    ):
        """
        初始化简化对话处理器
        """
        self.dialogue_callback = dialogue_callback  # 对话模型回调函数
        self.knowledge_callback = knowledge_callback  # 知识模型回调函数


        self.mcp_client_add_task_callback = mcp_client_add_task_callback  # MCP 客户端添加任务回调函数
        self.mcp_client_execute_task_callback = mcp_client_execute_task_callback  # MCP 客户端获取结果回调函数


    def run(self, user_input: str):
        """
        运行对话循环

        这是一个自主决策的循环系统：
        - 对话模型会不断评估当前状态，决定下一步行动
        - 直到任务完成或用户结束对话
        """
        state = State.IDLE #初始化状态为空闲状态

        buffer = None #初始化缓冲区为空

        while True: #循环直到结束状态
            match state:
              case State.IDLE:
                
                response, tool_calls = self.gather(self.dialogue_callback(user_input)) # 向AI模型提问
                

                if len(response) > 0 :  #说明此刻AI模型已经回答了问题,结束本轮对话
                  state = State.ENDING
                if len(tool_calls) > 0 :  #说明此刻AI模型已经调用了工具，解析工具调用，并执行工具
                  tool_results = self.execute(self.merge(tool_calls)) # 合并并执行工具调用，获取工具执行结果

                  # 解析第一个工具的返回结果
                  if len(tool_results) > 0:
                    try:
                      result_data = json.loads(tool_results[0]) # 解析JSON结果
                      task_type = result_data.get("task_type", "") # 获取任务类型
                      # 根据任务类型决定下一个状态
                      if task_type == "PLAN":
                        buffer = result_data.get("description", "") # 获取规划数据
                        state = State.COMPLEX_TASK_PLANNING # 进入复杂任务规划状态
                      elif task_type == "EXIT":
                        return #退出指令，直接退出
                      else:
                        response, tool_calls = self.gather(self.dialogue_callback(problem=str(tool_results),role= "system")) # 走到这里说明已经调用了工具，该走到根据工具返回结果回复用户
                        return  #结束对话
                    except json.JSONDecodeError:
                      # 如果不是JSON格式（如普通工具调用结果），直接回答
                      state = State.ENDING
                  else:
                    state = State.ENDING

              case State.ENDING:
                return #回答完问题结束问答

              case State.COMPLEX_TASK_PLANNING:
                message = f"""
                请根据对话模型提供的规划，判断是否要介入,如果觉得需要介入，则强制调用工具generate_todo_list
                数据：{buffer}
                """
                response, tool_calls = self.gather(self.knowledge_callback(message)) # 向知识模型提问
                if tool_calls:#这里调用了工具说明知识模型选择介入，创建了TODO列表，准备收集数据
                  buffer = tool_calls
                  state = State.MODEL_B_JUDGING #模型B判断是否需要介入
                else:#这里输出的对话，说明知识模型选择不介入，直接跳跃到对话模型的交互
                  state = State.MODEL_A_SUMMARIZING

              case State.MODEL_B_JUDGING:
                # 执行知识模型生成的TODO列表
                # 首先执行generate_todo_list工具调用，获取TODO列表
                tool_results = self.execute(self.merge(buffer)) # 合并并执行工具调用，获取TODO列表

                # 解析TODO列表
                if tool_results and len(tool_results) > 0:
                  try:
                    todo_data = json.loads(tool_results[0]) # 解析JSON结果
                    todo_list = todo_data.get("todo_list", []) # 获取TODO列表

                    # 逐个执行TODO项
                    all_results = [] # 存储所有TODO项的执行结果
                    for todo_item in todo_list:
                      # 将TODO项发给知识模型，让它调用相应的MCP工具
                      message = f"请完成以下任务：{todo_item}"
                      response, tool_calls = self.gather(self.knowledge_callback(message))

                      # 如果知识模型调用了工具，执行工具并收集结果
                      if tool_calls:
                        item_results = self.execute(self.merge(tool_calls))
                        all_results.extend(item_results)

                      # 如果知识模型直接回答了，也收集回答
                      if response:
                        all_results.append(response)

                    # 将所有结果汇总到buffer
                    buffer = "\n".join(all_results) if all_results else ""
                  except json.JSONDecodeError:
                    # 如果解析失败，直接使用原始结果
                    buffer = "\n".join(tool_results)
                else:
                  buffer = ""

                state = State.MODEL_A_SUMMARIZING # 跳转到对话模型汇总阶段

              case State.MODEL_A_SUMMARIZING:
                # 构造消息：包含用户问题和知识模型收集的数据（如果有）
                message = f"""
                用户问题：{user_input}
                知识模型收集的数据：{buffer if buffer else "无"}

                请基于以上信息，生成并执行TODO列表来完成用户的任务。
                """
                # 对话模型生成并执行TODO列表
                response, tool_calls = self.gather(self.dialogue_callback(message) ) # 向对话模型提问

                if tool_calls: # 如果有工具调用，执行工具
                  tool_results = self.execute(self.merge(tool_calls)) # 合并并执行工具调用
                  buffer = "\n".join(tool_results) if tool_results else "" # 将结果存入buffer

                # 执行完后回到IDLE，让对话模型自己决定是回答用户还是继续
                state = State.IDLE

    def gather(self,response_generator: Generator) -> Tuple[str, List[Dict[str, Any]]]:
        """
        处理AI的流式响应，提取内容和工具调用

        AI的流式响应是一个生成器，每次yield一个字典，包含不同类型的数据：
        - content: AI生成的文本内容
        - tool_calls: AI决定调用的工具信息

        参数:
            response_generator: AI返回的流式响应生成器
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
            if chunk_type == "content": #文本内容
                response += content
                print(f"{content}", end='', flush=True)
            elif chunk_type == "thinking": #思考过程（思考无作用，仅打印，不返回）
                print(f"{content}", end='', flush=True)
            elif chunk_type == "tool_calls": #工具调用
                # content是一个列表，取第一个元素
                tool_calls.append(content[0])

        return response, tool_calls
    #  ================================================合并工具调用碎片================================================
    def merge(self,tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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

        merged = {}#合并后的工具调用列表
        
        for tool in tool_calls:#遍历工具调用列表
            index = tool.get("index", 0)#获取工具索引
            
            if index not in merged:#如果索引不在合并后的工具调用列表中
                # 初始化第一个碎片
                merged[index] = {#初始化第一个碎片
                    "index": index,
                    "id": tool.get("id", ""),#工具ID
                    "type": tool.get("type", ""),#工具类型
                    "function": {
                        "name": tool.get("function", {}).get("name", ""),#工具名称
                        "arguments": tool.get("function", {}).get("arguments", "")#工具参数
                    }
                }
            else:#如果索引在合并后的工具调用列表中
                # 合并后续碎片
                merged_tool = merged[index]#获取合并后的工具调用
                
                # 只更新非空值
                if tool.get("id"):
                    merged_tool["id"] = tool["id"]#更新工具ID
                if tool.get("type"):#更新工具类型
                    merged_tool["type"] = tool["type"]
                    
                func = tool.get("function", {})#获取工具函数
                if func.get("name"):
                    merged_tool["function"]["name"] = func["name"]#更新工具名称
                if func.get("arguments"):
                    merged_tool["function"]["arguments"] += func["arguments"]#更新工具参数
        
        return [merged[key] for key in sorted(merged.keys())]#按索引排序并返回列表

    #  ================================================执行工具调用并获取结果================================================
    def execute(self,merged_tools: List[Dict[str, Any]]) -> List[str]:
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
        # 第一步：批量提交所有工具调用任务
        task_ids = [] #创建任务ID列表
        for tool in merged_tools:#遍历合并后的工具调用列表
            task_id = self.mcp_client_add_task_callback(tool)#添加任务
            task_ids.append(task_id)#添加任务ID
            print(f"[OK] 已添加任务: {tool['function']['name']}")#打印添加任务信息

        # 第二步：批量获取所有任务的执行结果
        tool_results = []#创建工具执行结果列表
        for task_id in task_ids:
            result = self.mcp_client_execute_task_callback(task_id)#获取任务执行结果

            # 打印详细的执行结果信息（用于调试）
            print(f"  meta: {result.meta}")#打印元数据
            print(f"  content: {result.content}")#打印内容
            print(f"  structuredContent: {result.structuredContent}")#打印结构化内容
            print(f"  isError: {result.isError}")#打印是否出错

            # 检查是否执行出错
            if result.isError:#如果执行出错
                print(f"[WARNING] 工具执行出错: {result.content}")#打印工具执行出错信息

            # 提取工具结果的文本内容
            if result.content:#如果内容不为空
                # result.content 是一个列表，包含 TextContent 对象
                # 需要提取第一个 TextContent 对象的 text 属性
                if isinstance(result.content, list) and len(result.content) > 0:
                    # 如果是 TextContent 对象，提取 text 属性
                    if hasattr(result.content[0], 'text'):
                        tool_results.append(result.content[0].text)
                    else:
                        tool_results.append(str(result.content[0]))
                else:
                    tool_results.append(str(result.content))#添加工具执行结果

        return tool_results#返回工具执行结果列表