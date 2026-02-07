# -*- coding: utf-8 -*-
"""
豆包大模型API封装类（字节跳动）

继承自BaseModel，使用tiktoken tokenizer。
"""

from .base_model import BaseModel


class Doubao(BaseModel):
    """
    豆包大模型API封装类
    """

    # 配置属性
    _thinking_field = "reasoning_content"
    _tokenizer_type = "tiktoken"
    _tokenizer_encoding = "cl100k_base"

    def _get_tokenizer_path(self) -> str:
        """获取tokenizer编码名"""
        return self._tokenizer_encoding
