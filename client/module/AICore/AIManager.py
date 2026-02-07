"""
AI工厂模块

该模块提供了AI模型的工厂类，用于创建和管理不同供应商的AI客户端。

主要功能：
    - 支持多种AI模型供应商（DeepSeek、Qwen、Kimi、Doubao等）
    - 单AI实例架构
    - 统一的模型切换接口
    - 配置文件管理（secret_key.json + config.json）

典型用法：
    >>> factory = AIFactory()
    >>> factory.connect(vendor="deepseek", model_name="deepseek-chat")
    >>> # 使用 factory.callback
"""

import os
import json
from typing import Optional, Dict, Any, Generator

from .Client import OPEN_AI
from .Model import DeepSeek
from .Model import Doubao
from .Model import Kimi
from .Model import Qwen
from logger import logger
class AIFactory:
    """
    AI工厂类 - 管理单AI实例

    该类负责创建和管理一个AI客户端。

    属性:
        ai: AI模型实例（DeepSeek/Qwen/Kimi/Doubao等）
        ai_client: AI模型的OPEN_AI客户端

    配置文件:
        - role/secret_key.json: 存储各供应商的API密钥
        - role/config.json: 存储各模型的配置参数
        - role/role/: 角色目录（包含assistant.json和history.json）
    """

    def __init__(self) -> None:
        """
        初始化AI工厂
        """
        self.ai = None  # AI模型实例
        self.ai_client = None  # AI模型客户端
    
    def connect(
        self,
        vendor: str,
        model_name: str
    ) -> None:
        """
        连接AI模型

        参数:
            vendor: 模型供应商（如 "deepseek", "qwen", "kimi", "doubao"）
            model_name: 模型名称（如 "deepseek-chat", "qwen-turbo"）

        异常:
            FileNotFoundError: 配置文件不存在
            ValueError: 供应商或模型配置无效

        示例:
            >>> factory = AIFactory()
            >>> factory.connect(vendor="deepseek", model_name="deepseek-chat")
        """
        self.switch_model(vendor, model_name)

    def disconnect(self) -> None:
        """
        断开AI模型连接

        释放AI模型的资源，将所有客户端设置为None。
        """
        self.ai = None
        self.ai_client = None
    def switch_model(
        self,
        vendor: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> None:
        """
        切换AI模型

        参数:
            vendor: 模型供应商（如 "deepseek", "qwen", "kimi", "doubao"）
            model_name: 模型具体型号（如 "deepseek-chat", "qwen-turbo"）

        异常:
            FileNotFoundError: 配置文件不存在
            ValueError: 供应商或模型配置无效

        示例:
            >>> factory.switch_model(vendor="kimi", model_name="moonshot-v1-8k")
        """
        if vendor and model_name:
            # 提取模型参数
            ai_message = self._compose_params(self._extract_key(vendor), self._extract_params(vendor, model_name))
            # 调用模型(相对应的模型工厂函数)
            self.ai = self.call_model(vendor, ai_message)

            # 获取角色目录路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            role_path = os.path.join(script_dir, "role", "role")

            # 创建模型客户端
            self.ai_client = OPEN_AI(
                request_params=self.ai.gen_params(),
                max_tokens=self.ai.max_tokens,
                get_params_callback=self.ai.gen_request,
                get_params_callback_stream=self.ai.gen_params_stream,
                token_callback=self.ai.token_callback,
                is_stream_end_callback=self.ai.is_stream_end,
                extract_stream_callback=self.ai.extract_stream_info,
                role_path=role_path
        )
            # 注：HistoryManager初始化时已自动加载assistant.json作为第一条消息
 
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

    def _extract_key(self, vendor: str) -> str:
        """
        从配置文件中提取API密钥

        从 role/secret_key.json 中读取指定供应商的API密钥。

        参数:
            vendor: 供应商名称（如 "deepseek", "qwen"）

        返回:
            API密钥字符串

        异常:
            FileNotFoundError: 配置文件不存在
            ValueError: 供应商配置无效
        """
        # 获取当前文件所在目录，确保路径正确
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "role", "secret_key.json")
        
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"配置文件未找到: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        api_key = config.get(vendor)
        if api_key is None:
            raise ValueError(f"在配置文件中未找到供应商 '{vendor}' 的密钥")
        return api_key

    def _compose_params(self, key: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        组合API密钥和模型参数

        将API密钥和模型配置参数组合成模型类初始化所需的格式。

        参数:
            key: API密钥
            params: 模型配置参数字典

        返回:
            组合后的参数字典，格式为 {"key": "...", "params": {...}}
        """
        return {
            "key": key,
            "params": params
        }

    def call_model(self, vendor: str, message: Dict[str, Any]) -> Any:
        """
        根据供应商名称实例化对应的模型类

        参数:
            vendor: 供应商名称（"deepseek", "qwen", "kimi", "doubao"）
            message: 包含API密钥和配置参数的字典

        返回:
            实例化的模型对象

        异常:
            ValueError: 不支持的供应商或供应商暂未实现

        支持的供应商:
            - deepseek: DeepSeek模型
            - qwen: 通义千问模型
            - kimi: Kimi（月之暗面）模型
            - doubao: 豆包模型

        待实现的供应商:
            - chatgpt, claude, gemini, xinhuo
        """
        if vendor == "deepseek":
            return DeepSeek(message)
        elif vendor == "doubao":
            return Doubao(message)
        elif vendor == "kimi":
            return Kimi(message)
        elif vendor == "qwen":
            return Qwen(message)
        elif vendor in ["chatgpt", "claude", "gemini", "xinhuo"]:
            raise ValueError(f"暂不支持的供应商: {vendor}")
        else:
            raise ValueError(f"不支持的供应商: {vendor}")

    def callback(self, problem: str, role: str = "user") -> Generator[dict, None, None]:
        """
        AI模型流式输出回调函数

        封装 ai_client.send_stream，以生成器方式逐块输出内容。

        参数:
            problem: 用户输入的消息
            role: 消息角色，可选值为 "user" 或 "system"，默认为 "user"

        返回:
            生成器，逐块yield输出的内容和类型

        异常:
            RuntimeError: AI模型客户端未连接

        示例:
            >>> for chunk in factory.callback("你好"):
            ...     print(chunk, end="", flush=True)
        """
        if not self.ai_client:
            raise RuntimeError("AI模型客户端未连接")
        for chunk in self.ai_client.send_stream(problem, role):
            yield chunk

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