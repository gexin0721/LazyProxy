# -*- coding: utf-8 -*-
"""
深度求索大模型API封装类

继承自BaseModel，保留DeepSeek特有功能：
- tokenizer初始化
- 带pattern参数的set_temperature
- token_callback
"""

import os
from transformers import AutoTokenizer
from .base_model import BaseModel


class DeepSeek(BaseModel):
    def __init__(self, message: dict):
        # 调用基类初始化
        super().__init__(message)

        # API模型名称到HuggingFace tokenizer路径的映射
        tokenizer_map = {
            "deepseek-chat": "deepseek-ai/DeepSeek-V2-Chat",
            "deepseek-reasoner": "deepseek-ai/DeepSeek-R1",
        }

        # 获取tokenizer路径
        tokenizer_path = tokenizer_map.get(self.model, self.model if "/" in self.model else "deepseek-ai/DeepSeek-V2-Chat")

        # 设置tokenizer缓存目录为AI模块的Data文件夹
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ai_module_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        cache_dir = os.path.join(ai_module_root, "Data", "models", "tokenizers")

        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)

        # 加载tokenizer（只使用本地缓存，不联网下载，并指定缓存目录）
        self.tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_path,
            trust_remote_code=True,
            resume_download=True,
            local_files_only=True,
            cache_dir=cache_dir
        )

    # ================ DeepSeek特有方法 ================
    def set_temperature(self, temperature: float = 0, pattern: str = "通用对话"):
        """
        设置温度参数，支持按场景自动选择温度

        参数:
            temperature: 手动指定的温度值，范围0-2
            pattern: 场景模式，可选值见temperature_map
        """
        temperature_map = {
            "代码生成": 0.0,
            "数学解题": 0.0,
            "数据抽取": 1.0,
            "分析": 1.0,
            "通用对话": 1.3,
            "翻译": 1.3,
            "创意类写作": 1.5,
            "诗歌创作": 1.5,
        }

        self.temperature = temperature_map.get(pattern, temperature) if temperature == 0 else temperature

    # ================ 计算token的回调函数 ================
    def token_callback(self, content: str) -> int:
        """计算deepseek模型的token数（使用transformers tokenizer）"""
        if not content:
            return 0
        return len(self.tokenizer.encode(content, add_special_tokens=False))
