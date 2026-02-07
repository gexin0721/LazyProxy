# -*- coding: utf-8 -*-
# Kimi大模型API封装类（月之暗面 Moonshot AI）
import os
import time
from transformers import AutoTokenizer
from .base_model import BaseModel


class Kimi(BaseModel):
    """
    Kimi大模型API封装类

    官方速率限制说明（来源：https://platform.moonshot.cn/docs/pricing）：
    ┌──────────┬────────────┬──────┬──────┬─────────┬─────────────┐
    │ 用户等级 │ 累计充值金额 │ 并发 │ RPM  │   TPM   │     TPD     │
    ├──────────┼────────────┼──────┼──────┼─────────┼─────────────┤
    │ Free     │ ¥ 0        │  1   │  3   │ 32,000  │ 1,500,000   │
    │ Tier1    │ ¥ 50       │  50  │ 200  │ 128,000 │ 10,000,000  │
    │ Tier2    │ ¥ 100      │ 100  │ 500  │ 128,000 │ 20,000,000  │
    │ Tier3    │ ¥ 500      │ 200  │5,000 │ 384,000 │ Unlimited   │
    │ Tier4    │ ¥ 5,000    │ 400  │5,000 │ 768,000 │ Unlimited   │
    │ Tier5    │ ¥ 20,000   │1,000 │10,000│2,000,000│ Unlimited   │
    └──────────┴────────────┴──────┴──────┴─────────┴─────────────┘

    限速概念解释：
    - 并发：同一时间内最多处理的来自您的请求数
    - RPM (request per minute)：一分钟内您最多向我们发起的请求次数
    - TPM (token per minute)：一分钟内您最多和我们交互的token数
    - TPD (token per day)：一天内您最多和我们交互的token数

    注意：本类默认按Free账户（RPM=3）设置速率限制
    使用方法：在初始化时传入tier参数，如 Kimi(..., tier="Tier1") 来设置对应的速率限制
    """

    # ================ 配置属性 ================
    _thinking_field = "reasoning_content"
    _tokenizer_type = "transformers"

    # tokenizer映射（Kimi没有公开tokenizer，使用Qwen近似）
    _tokenizer_map = {
        "moonshot-v1-8k": "Qwen/Qwen-7B-Chat",
        "moonshot-v1-32k": "Qwen/Qwen-7B-Chat",
        "moonshot-v1-128k": "Qwen/Qwen-7B-Chat",
    }

    # 各等级对应的RPM（每分钟请求数）限制
    TIER_RPM_LIMITS = {
        "Free": 3,
        "Tier1": 200,
        "Tier2": 500,
        "Tier3": 5000,
        "Tier4": 5000,
        "Tier5": 10000,
    }

    def __init__(self, message: dict):
        """
        初始化Kimi客户端

        参数：
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称（如 moonshot-v1-8k）
            tier: 账户等级，可选值：Free, Tier1, Tier2, Tier3, Tier4, Tier5（默认：Free）
        """
        # 调用基类初始化
        super().__init__(message)

        # Kimi特有参数
        self.tier = message.get("params").get("tier", "Free")

        # 验证tier有效性
        if self.tier not in self.TIER_RPM_LIMITS:
            raise ValueError(f"无效的账户等级：{self.tier}，可选值：{list(self.TIER_RPM_LIMITS.keys())}")

        # 速率限制控制：根据账户等级自动设置RPM限制
        self.last_request_time = 0
        rpm_limit = self.TIER_RPM_LIMITS[self.tier]
        # 计算最小请求间隔（留一点余量，乘以1.05确保不超限）
        self.min_request_interval = (60.0 / rpm_limit) * 1.05

        print(f"[Kimi初始化] 账户等级：{self.tier}，RPM限制：{rpm_limit}，请求间隔：{self.min_request_interval:.2f}秒")

        # API模型名称到HuggingFace tokenizer路径的映射
        # Kimi使用通用的tokenizer进行近似计算
        tokenizer_map = {
            "moonshot-v1-8k": "Qwen/Qwen-7B-Chat",
            "moonshot-v1-32k": "Qwen/Qwen-7B-Chat",
            "moonshot-v1-128k": "Qwen/Qwen-7B-Chat",
        }

        # 获取tokenizer路径，Kimi没有公开的tokenizer，使用Qwen作为近似
        tokenizer_path = tokenizer_map.get(self.model, "Qwen/Qwen-7B-Chat")

        # 设置tokenizer缓存目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ai_module_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        cache_dir = os.path.join(ai_module_root, "Data", "models", "tokenizers")
        os.makedirs(cache_dir, exist_ok=True)

        # 加载tokenizer
        print(f"正在加载 Kimi tokenizer: {tokenizer_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_path,
            trust_remote_code=True,
            resume_download=True,
            cache_dir=cache_dir
        )
        print(f"Tokenizer 加载成功")

    # ================ Kimi特有方法 ================
    def set_tier(self, tier: str):
        """
        设置账户等级并更新速率限制

        参数：
            tier: 账户等级，可选值：Free, Tier1, Tier2, Tier3, Tier4, Tier5
        """
        if tier not in self.TIER_RPM_LIMITS:
            raise ValueError(f"无效的账户等级：{tier}，可选值：{list(self.TIER_RPM_LIMITS.keys())}")

        self.tier = tier
        rpm_limit = self.TIER_RPM_LIMITS[tier]
        self.min_request_interval = (60.0 / rpm_limit) * 1.05
        print(f"[Kimi] 已更新账户等级为：{tier}，RPM限制：{rpm_limit}，请求间隔：{self.min_request_interval:.2f}秒")

    def _wait_for_rate_limit(self):
        """速率限制等待"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last_request
            print(f"[Kimi速率限制] 等待 {wait_time:.1f} 秒以避免超过API限制...")
            time.sleep(wait_time)

        self.last_request_time = time.time()

    #  ============ 生成请求参数 ============
    def gen_request(self, messages: list):
        """
        生成请求参数
        Kimi API使用标准的OpenAI兼容格式
        自动处理速率限制：确保请求间隔不少于设定时间
        """
        self._wait_for_rate_limit()
        return super().gen_request(messages)

    #  ============ 生成请求参数(流式) ============
    def gen_params_stream(self, messages: list):
        """
        生成流式请求参数
        Kimi支持流式输出
        自动处理速率限制：确保请求间隔不少于设定时间
        """
        self._wait_for_rate_limit()
        return super().gen_params_stream(messages)

    #  ============ 提取流式信息数据 ============
    def extract_stream_info(self, stream_options: dict) -> dict:
        """
        提取流式信息数据，提取delta.content字段
        若为 usage 终结块则返回 None
        """
        # 如果是最后的usage块（choices==[]且usage非None），无内容，直接返回None
        choices = stream_options.get('choices', [])
        if choices == []:
            return {"None": None}
        if not choices or not isinstance(choices, list):
            return {"None": None}
        choice = choices[0]
        delta = choice.get('delta', {}) if isinstance(choice, dict) else {}

        content = delta.get('content', None)
        if content is not None:
            return {"content": content}
        return {"None": None}

    #  ============ 计算token的回调函数 ============
    def token_callback(self, content: str) -> int:
        """
        计算Kimi模型的token数（使用Qwen tokenizer进行近似估算）
        Kimi没有公开的tokenizer，使用相似的中文tokenizer进行估算
        """
        if not content:
            return 0
        return len(self.tokenizer.encode(content, add_special_tokens=False))
