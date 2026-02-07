# -*- coding: utf-8 -*-
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

class TaskManager:
    """
    任务管理工具类
    提供退出、规划和TODO列表生成等静态工具方法
    这是一个无状态的工具类，所有方法都是静态方法
    """
    def exit_task(self) -> Dict[str, Any]:
        """
        退出工具
        用于标记当前任务退出，结束当前的工作流程

        参数：
            无

        返回值：
            Dict[str, Any]: 包含以下字段的字典
                - task_type: 任务类型，固定为 "EXIT"
                - task_name: 任务名称，固定为 "退出任务"
                - message: 退出消息
                - timestamp: 退出时间戳
        """
        result = {
            "task_type": "EXIT",
            "message": "任务已退出",
        }
        return result

    def plan_task(self,plan_description: str) -> Dict[str, Any]:
        """
        规划工具
        用于创建任务规划，制定任务的执行计划和步骤

        参数：
            plan_description (str): 规划描述字符串，详细说明任务的规划内容

        返回值：
            Dict[str, Any]: 包含以下字段的字典
                - task_type: 任务类型，固定为 "PLAN"
                - description: 规划描述内容
        """

        result = {
            "task_type": "PLAN",
            "description": plan_description,
        }

        return result

    def generate_todo_list(self,tasks: List[str]) -> Dict[str, Any]:
        """
        TODO列表生成工具
        将输入的任务描述数组转换为结构化的TODO列表

        参数：
            tasks (List[str]): 任务描述的字符串数组，每个元素代表一个待办任务

        返回值：
            Dict[str, Any]: 包含以下字段的字典
                - task_type: 任务类型，固定为 "TODO_LIST"
                - todo_list: 生成的TODO列表，每个TODO项包含：
                    - description: 任务描述
                - total_count: TODO项总数
        """
        todo_list = []

        # 为每个任务创建结构化的TODO项
        for task_desc in tasks:
            todo_item = task_desc

            todo_list.append(todo_item)

        result = {
            "task_type": "TODO_LIST",
            "todo_list": todo_list,
            "total_count": len(todo_list),
        }

        return result

    def need_intervention(self, reason: str) -> Dict[str, Any]:
        """
        模型B表示需要介入的工具
        当模型B判断需要自己介入处理复杂任务时调用此工具

        参数：
            reason (str): 需要介入的原因说明

        返回值：
            Dict[str, Any]: 包含以下字段的字典
                - task_type: 任务类型，固定为 "NEED_INTERVENTION"
                - reason: 需要介入的原因
        """
        result = {
            "task_type": "NEED_INTERVENTION",
            "reason": reason,
        }
        return result

    def no_intervention(self, reason: str) -> Dict[str, Any]:
        """
        模型B表示不需要介入的工具
        当模型B判断不需要自己介入，对话模型可以直接处理时调用此工具

        参数：
            reason (str): 不需要介入的原因说明

        返回值：
            Dict[str, Any]: 包含以下字段的字典
                - task_type: 任务类型，固定为 "NO_INTERVENTION"
                - reason: 不需要介入的原因
        """
        result = {
            "task_type": "NO_INTERVENTION",
            "reason": reason,
        }
        return result

