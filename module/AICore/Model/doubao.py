# 豆包大模型API封装类（字节跳动）
import json
import tiktoken

class Doubao:
    def __init__(self, message: dict):
        self.api_key = message.get("key")
        self.base_url = message.get("params").get("base_url")
        self.model = message.get("params").get("model")

        # ================ 基础参数 ================
        self.max_tokens = message.get("params").get("max_tokens", 32000)  # 从配置读取，默认32000

        # ================ 采样参数 ================
        self.temperature = message.get("params").get("temperature", 1.0)  # 温度参数，范围0-2，默认1
        self.top_p = message.get("params").get("top_p", 1.0)  # 核采样参数，范围0-1，默认1

        # ================ 惩罚参数 ================
        self.frequency_penalty = message.get("params").get("frequency_penalty", 0.0)  # 频率惩罚，范围-2到2，默认0
        self.presence_penalty = message.get("params").get("presence_penalty", 0.0)  # 存在惩罚，范围-2到2，默认0

        # ================ 控制参数 ================
        self.stop = message.get("params").get("stop", None)  # 停止词，可以是string或list
        self.response_format = message.get("params").get("response_format", {"type": "text"})  # 响应格式，默认text

        # ================ 高级功能参数 ================
        self.tools = message.get("params").get("tools", None)  # Function Calling工具列表
        self.tool_choice = message.get("params").get("tool_choice", None)  # 工具选择策略

        # 豆包模型兼容OpenAI接口，使用tiktoken进行token计算
        # 根据官方文档，豆包使用cl100k_base编码器（与OpenAI的GPT-3.5/4相同）
        try:
            print(f"正在加载 Doubao tokenizer (cl100k_base)...")
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            print(f"✓ Tokenizer 加载成功")
        except Exception as e:
            print(f"警告：无法加载tiktoken，将回退到字符计数估算。错误: {e}")
            self.tokenizer = None
        
    def set_api_key(self, api_key: str):
        self.api_key = api_key

    def set_base_url(self, base_url: str):
        self.base_url = base_url

    def set_model(self, model: str):
        self.model = model

    # ================ 参数设置方法 ================
    def set_temperature(self, temperature: float):
        """设置温度参数，范围0-2"""
        if not 0 <= temperature <= 2:
            raise ValueError("temperature 必须在 0-2 之间")
        self.temperature = temperature

    def set_top_p(self, top_p: float):
        """设置top_p参数，范围0-1"""
        if not 0 <= top_p <= 1:
            raise ValueError("top_p 必须在 0-1 之间")
        self.top_p = top_p

    def set_frequency_penalty(self, frequency_penalty: float):
        """设置频率惩罚参数，范围-2到2"""
        if not -2 <= frequency_penalty <= 2:
            raise ValueError("frequency_penalty 必须在 -2 到 2 之间")
        self.frequency_penalty = frequency_penalty

    def set_presence_penalty(self, presence_penalty: float):
        """设置存在惩罚参数，范围-2到2"""
        if not -2 <= presence_penalty <= 2:
            raise ValueError("presence_penalty 必须在 -2 到 2 之间")
        self.presence_penalty = presence_penalty

    def set_max_tokens(self, max_tokens: int):
        """设置最大token数"""
        if max_tokens <= 0:
            raise ValueError("max_tokens 必须大于0")
        self.max_tokens = max_tokens

    def set_stop(self, stop):
        """设置停止词，可以是string或list"""
        self.stop = stop

    def set_response_format(self, response_format: dict):
        """设置响应格式，如 {"type": "json_object"}"""
        if not isinstance(response_format, dict) or "type" not in response_format:
            raise ValueError("response_format 必须是包含 type 字段的字典")
        if response_format["type"] not in ["text", "json_object"]:
            raise ValueError("response_format type 必须是 'text' 或 'json_object'")
        self.response_format = response_format

    def set_tools(self, tools: list):
        """设置Function Calling工具列表"""
        if not isinstance(tools, list):
            raise ValueError("tools 必须是列表类型")
        self.tools = tools

    def set_tool_choice(self, tool_choice):
        """设置工具选择策略"""
        self.tool_choice = tool_choice

    #  ============ 生成链接参数 ============
    def gen_params(self):
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
        }
    #  ============ 生成请求参数 ============
    def gen_request(self, messages: list):
        """
        生成请求参数，包含完整的豆包 API 参数
        会读取和保存对话历史，并生成请求体
        """
        # 基础请求参数
        request_params = {
            "model": self.model,
            "messages": messages,
        }

        if self.temperature != 1.0:  # 默认值是1.0
            request_params["temperature"] = self.temperature

        if self.top_p != 1.0:  # 默认值是1.0
            request_params["top_p"] = self.top_p

        if self.frequency_penalty != 0.0:  # 默认值是0.0
            request_params["frequency_penalty"] = self.frequency_penalty

        if self.presence_penalty != 0.0:  # 默认值是0.0
            request_params["presence_penalty"] = self.presence_penalty

        if self.stop is not None:
            request_params["stop"] = self.stop

        if self.response_format is not None and self.response_format.get("type") != "text":
            request_params["response_format"] = self.response_format

        if self.tools is not None:
            request_params["tools"] = self.tools

        if self.tool_choice is not None:
            request_params["tool_choice"] = self.tool_choice

        return request_params
        
    #  ============ 生成请求参数(流式) ============
    def gen_params_stream(self, messages: list):
        """
        生成流式请求参数，包含完整的豆包 API 参数
        """
        # 先获取非流式的完整参数
        request_params = self.gen_request(messages)

        # 添加流式特定参数
        request_params["stream"] = True
        request_params["stream_options"] = {"include_usage": True}

        return request_params

    #  ============ 判断流式是否结束 ============
    def is_stream_end(self, stream_options: dict) -> bool:
        """
        判断流式是否结束
        usage 字段为 None 表示还在传输数据，否则为结束
        """
        # usage 字段为 None，则说明还在传输，非None视为结束
        usage = stream_options.get("usage", None)
        return usage is not None
        
    #  ============ 提取流式信息数据 ============
    def extract_stream_info(self, stream_options: dict) -> dict:
        """
        提取流式信息数据, 提取delta.content字段或tool_calls字段
        返回格式: {"content": "文本内容"} 或 {"tool_calls": [...]} 或 {"None": None}
        """
        # 如果是最后的usage块（choices==[]且usage非None），无内容，直接返回None
        choices = stream_options.get('choices', [])
        if choices == []:
            return {"None": None}
        if not choices or not isinstance(choices, list):
            return {"None": None}
        choice = choices[0]
        delta = choice.get('delta', {}) if isinstance(choice, dict) else {}

        # 优先提取文本内容
        content = delta.get('content', None)
        if content is not None:
            return {"content": content}

        # 如果没有文本内容，检查是否有工具调用
        tool_calls = delta.get('tool_calls', None)
        if tool_calls is not None and len(tool_calls) > 0:
            return {"tool_calls": tool_calls}

        return {"None": None}

    #  ============ 计算token的回调函数 ============
    def token_callback(self, content: str) -> int:
        """
        计算豆包模型的token数
        豆包兼容OpenAI接口，使用tiktoken的cl100k_base编码器计算token
        如果tiktoken不可用，则回退到字符数估算（1个汉字≈2token，英文约4字符≈1token）
        """
        if not content:
            return 0
        
        if self.tokenizer:
            # 使用tiktoken计算（精确）
            return len(self.tokenizer.encode(content))
        else:
            # 回退方案：简单估算
            # 统计中文字符和其他字符
            chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
            other_chars = len(content) - chinese_chars
            # cl100k_base编码：1个汉字≈2token（根据官方数据），英文约4字符≈1token
            return int(chinese_chars * 2 + other_chars / 4)
