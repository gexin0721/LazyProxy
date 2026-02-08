# -*- coding: utf-8 -*-
"""
AI工厂模块 - 纯参数组装

该模块提供了AI模型的工厂类，用于组装不同供应商的请求参数。
不直接发送请求，由外部（服务器中转）负责实际通信。

主要功能：
    - 支持多种AI模型供应商（DeepSeek、Qwen、Kimi、Doubao等）
    - 单AI实例架构
    - 统一的模型切换接口
    - 工厂级别的历史消息管理（切换模型共享历史）
    - 组装链接参数和请求体参数

典型用法：
    >>> factory = AIFactory()
    >>> factory.set_token("临时令牌")
    >>> factory.connect(vendor="deepseek", model_name="deepseek-chat", system_prompt="你是助手")
    >>> link_params = factory.gen_link_params()
    >>> question_params = await factory.gen_question_params("你好")
"""

import os
import json
from typing import Optional, Dict, Any

from .Model import DeepSeek
from .Model import Doubao
from .Model import Kimi
from .Model import Qwen
from .Historyfile.HistoryManager import HistHistoryManager
from logger import logger
class AIFactory:
    """
    AI工厂类 - 纯参数组装器

    该类负责组装AI请求所需的链接参数和问题参数。
    不直接发送请求，由外部（服务器中转）负责实际通信。

    属性:
        token: 临时令牌（所有模型共用，会过期）
        ai: AI模型实例（DeepSeek/Qwen/Kimi/Doubao等）
        history: 历史消息管理器（工厂级别，切换模型共享）
    """

    def __init__(self) -> None:
        self.token = None       # 临时令牌，所有模型共用
        self.ai = None          # AI模型实例
        self.history = None     # 历史消息管理器（工厂级别）

    def set_token(self, token: str) -> None:
        """设置/更新临时令牌"""
        self.token = token

    def connect(
        self,
        vendor: str,
        model_name: str,
        system_prompt: str
    ) -> None:
        """
        连接AI模型

        参数:
            vendor: 模型供应商（如 "deepseek", "qwen", "kimi", "doubao"）
            model_name: 模型名称（如 "deepseek-chat", "qwen-turbo"）
            system_prompt: 系统提示词
        """
        self.switch_model(vendor, model_name, system_prompt)

    def disconnect(self) -> None:
        """断开AI模型连接，释放资源"""
        self.ai = None
        self.history = None
    def switch_model(
        self,
        vendor: str,
        model_name: str,
        system_prompt: Optional[str] = None
    ) -> None:
        """
        切换AI模型

        参数:
            vendor: 模型供应商（如 "deepseek", "qwen", "kimi", "doubao"）
            model_name: 模型具体型号（如 "deepseek-chat", "qwen-turbo"）
            system_prompt: 系统提示词（首次连接必传，切换模型时可选）
        """
        if vendor and model_name:
            # 从config.json提取模型参数
            params = self._extract_params(vendor, model_name)
            # 实例化对应的模型
            self.ai = self.call_model(vendor, params)

            # 初始化或更新历史管理器
            if self.history is None:
                if system_prompt is None:
                    raise ValueError("首次连接必须提供 system_prompt")
                self.history = HistHistoryManager(
                    messages=[],
                    system_prompt=system_prompt,
                    token_callback=self.ai.token_callback,
                    maxtoken=self.ai.max_tokens
                )
            else:
                # TODO: 切换模型时需要更新 token_callback，待 HistoryManager 增加 set_token_callback 方法
                pass
 
    def _extract_params(self, vendor: str, model_name: str) -> Dict[str, Any]:
        """
        从配置文件中提取模型参数

        从 role/config.json 中读取指定供应商和模型的配置参数。

        参数:
            vendor: 供应商名称（如 "deepseek", "qwen"）
            model_name: 模型名称（如 "deepseek-chat", "qwen-turbo"）

        返回:
            包含模型配置参数的字典

        异常:
            FileNotFoundError: 配置文件不存在
            ValueError: 供应商或模型配置无效

        配置文件格式:
            {
                "deepseek": {
                    "deepseek-chat": {
                        "base_url": "https://api.deepseek.com",
                        "model": "deepseek-chat",
                        "max_tokens": 4096
                    }
                }
            }
        """
        # 获取当前文件所在目录，确保路径正确
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "role", "config.json")
        
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"配置文件未找到: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        vendor_dict = config.get(vendor)
        if vendor_dict is None or not isinstance(vendor_dict, dict):
            raise ValueError(f"在配置文件中未找到供应商 '{vendor}' 的配置")

        params = vendor_dict.get(model_name)
        if params is None:
            raise ValueError(f"在供应商 '{vendor}' 的配置下未找到模型 '{model_name}' 的参数")
        return params

    def call_model(self, vendor: str, params: Dict[str, Any]) -> Any:
        """
        根据供应商名称实例化对应的模型类

        参数:
            vendor: 供应商名称（"deepseek", "qwen", "kimi", "doubao"）
            params: 模型配置参数字典（直接从config.json提取）
        """
        if vendor == "deepseek":
            return DeepSeek(params)
        elif vendor == "doubao":
            return Doubao(params)
        elif vendor == "kimi":
            return Kimi(params)
        elif vendor == "qwen":
            return Qwen(params)
        elif vendor in ["chatgpt", "claude", "gemini", "xinhuo"]:
            raise ValueError(f"暂不支持的供应商: {vendor}")
        else:
            raise ValueError(f"不支持的供应商: {vendor}")

    def gen_link_params(self) -> Dict[str, Any]:
        """
        生成链接参数

        返回:
            {"base_url": "...", "token": "..."}
        """
        if not self.ai:
            raise RuntimeError("AI模型未连接")
        return {
            "base_url": self.ai.base_url,
            "token": self.token
        }

    async def gen_question_params(self, problem: str, role: str = "user") -> Dict[str, Any]:
        """
        输入问题，写入历史，返回完整请求体参数

        参数:
            problem: 用户输入的消息
            role: 消息角色，默认 "user"

        返回:
            完整的请求体参数字典
        """
        if not self.ai:
            raise RuntimeError("AI模型未连接")
        if not self.history:
            raise RuntimeError("历史管理器未初始化")

        # 写入历史
        await self.history.write(role, problem)

        # 读取完整历史消息
        messages = self.history.read()

        # 通过Model生成请求体参数
        return self.ai.gen_request(messages)

    def add_tools(self, tools: list) -> None:
        """
        为AI模型添加工具列表

        参数:
            tools: 工具列表，符合OpenAI Function Calling格式
        异常:
            RuntimeError: AI模型未连接
        """
        if not self.ai:
            raise RuntimeError("AI模型未连接")
        self.ai.set_tools(tools)