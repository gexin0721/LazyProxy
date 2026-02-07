# -*- coding: utf-8 -*-
# 通义千问大模型API封装类
import os
from transformers import AutoTokenizer
from .base_model import BaseModel


class Qwen(BaseModel):
    def __init__(self, message: dict):
        # 调用基类初始化
        super().__init__(message)

        # ================ Qwen特有参数 ================
        self.stream_options = True  # 是否启用深度思考模式
        self.top_k = 5  # 从k个候选中随机选择一个
        self.auditing = "default"  # 审核设置

        # ================ 模型名称到HuggingFace tokenizer路径的映射 ================
        # API模型名称到HuggingFace tokenizer路径的映射
        tokenizer_map = {
            "qwen-turbo": "Qwen/Qwen-7B-Chat",
            "qwen-plus": "Qwen/Qwen-14B-Chat",
            "qwen-max": "Qwen/Qwen-72B-Chat",
            "qwen-max-longcontext": "Qwen/Qwen-72B-Chat",
        }

        # 如果model在映射表中，使用映射的路径；否则假定model本身就是HuggingFace路径
        tokenizer_path = tokenizer_map.get(self.model, "Qwen/Qwen-7B-Chat")

        # 设置tokenizer缓存目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ai_module_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        cache_dir = os.path.join(ai_module_root, "Data", "models", "tokenizers")
        os.makedirs(cache_dir, exist_ok=True)

        self.tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_path,
            trust_remote_code=True,
            cache_dir=cache_dir
        )

    #  ============ 提取流式信息数据 ============
    def extract_stream_info(self, stream_options: dict) -> dict:
        """
        提取流式信息数据, 提取delta.content和delta.thinking字段
        优先返回thinking（思考过程），如果没有则返回content（最终答案）
        """
        # 'choices' 应为一个list
        choices = stream_options.get('choices', [])
        if not choices or not isinstance(choices, list):
            return {"None": None}
        choice = choices[0]
        delta = choice.get('delta', {}) if isinstance(choice, dict) else {}

        # 优先提取thinking字段（深度思考模式）
        thinking = delta.get('thinking', None)
        if thinking:
            return {"thinking": thinking}

        # 如果没有thinking，提取content（最终答案）
        content = delta.get('content', None)
        if content is not None:
            return {"content": content}

        return {"None": None}

    #  ============ 计算token的回调函数 ============
    # 阿里（通义千问：Qwen 系列）
    # 工具：transformers库加载 Qwen 的 tokenizer（开源模型）或官方 API 的usage字段
    # 原理：基于 BPE，中文分词粒度较细（单字或词）。
    def token_callback(self, content: str) -> int:
        """计算通义千问模型的token数"""
        if not content:
            return 0
        return len(self.tokenizer.encode(content, add_special_tokens=False))
