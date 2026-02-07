# -*- coding: utf-8 -*-
# Gemini大模型API封装类（Google）
import tiktoken
from .base_model import BaseModel


class Gemini(BaseModel):
    """
    Gemini大模型API封装类

    使用tiktoken进行token计算（近似）
    """

    # ================ 配置属性 ================
    _tokenizer_type = "tiktoken"
    _tokenizer_encoding = "cl100k_base"

    def __init__(self, message: dict):
        # 调用基类初始化
        super().__init__(message)

        # 加载tiktoken编码器
        self.tokenizer = tiktoken.get_encoding(self._tokenizer_encoding)

    #  ============ 计算token的回调函数 ============
    def token_callback(self, content: str) -> int:
        """计算Gemini模型的token数（近似）"""
        if not content:
            return 0
        return len(self.tokenizer.encode(content))
