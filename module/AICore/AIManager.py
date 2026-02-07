"""
AI工厂模块

该模块提供了AI模型的工厂类，用于创建和管理不同供应商的AI客户端。

主要功能：
    - 支持多种AI模型供应商（DeepSeek、Qwen、Kimi、Doubao等）
    - 双AI协同架构（对话模型 + 知识模型）
    - 统一的模型切换接口
    - 配置文件管理（secret_key.json + config.json）

典型用法：
    >>> factory = AIFactory()
    >>> factory.connect(
    ...     dialogue_vendor="deepseek",
    ...     dialogue_model_name="deepseek-chat",
    ...     knowledge_vendor="qwen",
    ...     knowledge_model_name="qwen-turbo"
    ... )
    >>> # 使用 factory.dialogue_callback 和 factory.knowledge_callback
"""

import os
import json
from typing import Optional, Dict, Any, Generator

from .Tool.OPEN_AI import OPEN_AI
from .Model import DeepSeek
from .Model import Doubao
from .Model import Kimi
from .Model import Qwen
from tools import logger
class AIFactory:
    """
    AI工厂类 - 管理双AI协同系统

    该类负责创建和管理两个AI客户端：
    1. 对话模型（dialogue_ai）：负责生成最终的对话回答
    2. 知识模型（knowledge_ai）：负责查询规划和数据检索

    属性:
        dialogue_ai: 对话模型实例（DeepSeek/Qwen/Kimi/Doubao等）
        knowledge_ai: 知识模型实例
        dialogue_ai_client: 对话模型的OPEN_AI客户端
        knowledge_ai_client: 知识模型的OPEN_AI客户端

    配置文件:
        - role/secret_key.json: 存储各供应商的API密钥
        - role/config.json: 存储各模型的配置参数
        - role/role_A/: 对话模型的角色目录（包含assistant.json和history.json）
        - role/role_B/: 知识模型的角色目录
    """

    def __init__(self) -> None:
        """
        初始化AI工厂
        """
        self.dialogue_ai = None  # 对话模型实例
        self.knowledge_ai = None  # 知识模型实例
        self.dialogue_ai_client = None  # 对话模型客户端
        self.knowledge_ai_client = None  # 知识模型客户端
    
    def connect(
        self,
        dialogue_vendor: str,
        dialogue_model_name: str,
        knowledge_vendor: str,
        knowledge_model_name: str
    ) -> None:
        """
        连接双AI模型

        参数:
            dialogue_vendor: 对话模型供应商（如 "deepseek", "qwen", "kimi", "doubao"）
            dialogue_model_name: 对话模型名称（如 "deepseek-chat", "qwen-turbo"）
            knowledge_vendor: 知识模型供应商
            knowledge_model_name: 知识模型名称

        异常:
            FileNotFoundError: 配置文件不存在
            ValueError: 供应商或模型配置无效

        示例:
            >>> factory = AIFactory()
            >>> factory.connect(
            ...     dialogue_vendor="deepseek",
            ...     dialogue_model_name="deepseek-chat",
            ...     knowledge_vendor="qwen",
            ...     knowledge_model_name="qwen-turbo"
            ... )
        """
        self.switch_model(dialogue_vendor, dialogue_model_name, knowledge_vendor, knowledge_model_name)

    def disconnect(self) -> None:
        """
        断开所有AI模型连接

        释放对话模型和知识模型的资源，将所有客户端设置为None。
        """
        self.dialogue_ai = None
        self.knowledge_ai = None
        self.dialogue_ai_client = None
        self.knowledge_ai_client = None
    def switch_model(
        self,
        dialogue_vendor: Optional[str] = None,
        dialogue_model_name: Optional[str] = None,
        knowledge_vendor: Optional[str] = None,
        knowledge_model_name: Optional[str] = None
    ) -> None:
        """
        切换对话模型或知识模型

        可以单独切换对话模型或知识模型，也可以同时切换两者。
        如果某个模型的参数为None，则不切换该模型。

        参数:
            dialogue_vendor: 对话模型供应商（如 "deepseek", "qwen", "kimi", "doubao"）
            dialogue_model_name: 对话模型具体型号（如 "deepseek-chat", "qwen-turbo"）
            knowledge_vendor: 知识模型供应商
            knowledge_model_name: 知识模型具体型号

        异常:
            FileNotFoundError: 配置文件不存在
            ValueError: 供应商或模型配置无效

        示例:
            >>> # 只切换对话模型
            >>> factory.switch_model(
            ...     dialogue_vendor="kimi",
            ...     dialogue_model_name="moonshot-v1-8k"
            ... )
            >>> # 同时切换两个模型
            >>> factory.switch_model(
            ...     dialogue_vendor="deepseek",
            ...     dialogue_model_name="deepseek-chat",
            ...     knowledge_vendor="qwen",
            ...     knowledge_model_name="qwen-turbo"
            ... )
        """
        if dialogue_vendor and dialogue_model_name:
            # 提取模型参数
            dialogue_ai_message = self._compose_params(self._extract_key(dialogue_vendor), self._extract_params(dialogue_vendor, dialogue_model_name))
            # 调用模型(相对应的模型工厂函数)
            self.dialogue_ai = self.call_model(dialogue_vendor, dialogue_ai_message)
            
            # 获取对话模型的角色目录路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            dialogue_history_path = os.path.join(script_dir, "role", "role_A")
            
            # 创建模型客户端
            self.dialogue_ai_client = OPEN_AI(
                request_params=self.dialogue_ai.gen_params(),
                max_tokens=self.dialogue_ai.max_tokens,  # 或其他合适的值
                get_params_callback=self.dialogue_ai.gen_request,
                get_params_callback_stream=self.dialogue_ai.gen_params_stream,
                token_callback=self.dialogue_ai.token_callback,
                is_stream_end_callback=self.dialogue_ai.is_stream_end,
                extract_stream_callback=self.dialogue_ai.extract_stream_info,
                role_path=dialogue_history_path  # 指定对话模型专用角色目录
            )
            # 注：HistoryManager初始化时已自动加载assistant.json作为第一条消息


        if knowledge_vendor and knowledge_model_name:
            # 提取模型参数
            knowledge_ai_message = self._compose_params(self._extract_key(knowledge_vendor), self._extract_params(knowledge_vendor, knowledge_model_name))
            # 调用模型(相对应的模型工厂函数)
            self.knowledge_ai = self.call_model(knowledge_vendor, knowledge_ai_message)
            
            # 获取知识模型的角色目录路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            knowledge_history_path = os.path.join(script_dir, "role", "role_B")
            
            # 创建模型客户端
            self.knowledge_ai_client = OPEN_AI(
                request_params=self.knowledge_ai.gen_params(),
                max_tokens=self.knowledge_ai.max_tokens,
                get_params_callback=self.knowledge_ai.gen_request,
                get_params_callback_stream=self.knowledge_ai.gen_params_stream,
                token_callback=self.knowledge_ai.token_callback,
                is_stream_end_callback=self.knowledge_ai.is_stream_end,
                extract_stream_callback=self.knowledge_ai.extract_stream_info,
                role_path=knowledge_history_path  # 指定知识模型专用角色目录
            )  # 知识模型
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

    def knowledge_callback(self, problem: str, role: str = "user") -> Generator[dict, None, None]:
        """
        知识模型流式输出回调函数

        封装 knowledge_ai_client.send_stream，以生成器方式逐块输出内容。

        参数:
            message: 用户输入的消息

        返回:
            生成器，逐块yield输出的内容和类型

        异常:
            RuntimeError: 知识模型客户端未连接

        示例:
            >>> for chunk in factory.knowledge_callback("查询数据"):
            ...     print(chunk, end="", flush=True)
        """
        if not self.knowledge_ai_client:
            raise RuntimeError("知识模型客户端未连接")
        for chunk in self.knowledge_ai_client.send_stream(problem,role):
            yield chunk

    def dialogue_callback(self, problem: str, role: str = "user") -> Generator[dict, None, None]:
        """
        对话模型流式输出回调函数

        封装 dialogue_ai_client.send_stream，以生成器方式逐块输出内容。

        参数:
            message: 用户输入的消息
            role: 消息角色，可选值为 "user" 或 "system"，默认为 "user"

        返回:
            生成器，逐块yield输出的内容和类型

        异常:
            RuntimeError: 对话模型客户端未连接

        示例:
            >>> for chunk in factory.dialogue_callback("你好"):
            ...     print(chunk, end="", flush=True)
        """
        if not self.dialogue_ai_client:
            raise RuntimeError("对话模型客户端未连接")
        for chunk in self.dialogue_ai_client.send_stream(problem, role):
            yield chunk

    def add_tools(self, tools: list, model_type: str = "dialogue") -> None:
        """
        为指定模型添加工具列表
        
        参数:
            tools: 工具列表，符合OpenAI Function Calling格式
            model_type: 模型类型，"dialogue"（对话模型）或"knowledge"（知识模型）
        异常:
            RuntimeError: 指定的模型未连接
            ValueError: model_type参数无效
        """
        if model_type == "dialogue":
            if not self.dialogue_ai:
                raise RuntimeError("对话模型未连接")
            self.dialogue_ai.set_tools(tools)
        elif model_type == "knowledge":
            if not self.knowledge_ai:
                raise RuntimeError("知识模型未连接")
            self.knowledge_ai.set_tools(tools)
        else:
            raise ValueError(f"无效的model_type: {model_type}，必须是'dialogue'或'knowledge'")