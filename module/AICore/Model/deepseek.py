# 深度求索大模型API封装类
import json
import os
from transformers import AutoTokenizer

class DeepSeek:
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
        self.stop = message.get("params").get("stop", None)  # 停止词，可以是string或list（最多16个）
        self.response_format = message.get("params").get("response_format", {"type": "text"})  # 响应格式，默认text

        # ================ 高级功能参数 ================
        self.tools = message.get("params").get("tools", None)  # Function Calling工具列表
        self.tool_choice = message.get("params").get("tool_choice", None)  # 工具选择策略
        self.logprobs = message.get("params").get("logprobs", False)  # 是否返回log概率
        self.top_logprobs = message.get("params").get("top_logprobs", None)  # 返回top N个log概率

        # API模型名称到HuggingFace tokenizer路径的映射
        tokenizer_map = {
            "deepseek-chat": "deepseek-ai/DeepSeek-V2-Chat",
            "deepseek-reasoner": "deepseek-ai/DeepSeek-R1",
        }

        # 获取tokenizer路径
        tokenizer_path = tokenizer_map.get(self.model, self.model if "/" in self.model else "deepseek-ai/DeepSeek-V2-Chat")

        # 设置tokenizer缓存目录为AI模块的Data文件夹
        # 获取当前文件所在目录，向上查找ai_assistant模块目录
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

        
    def set_api_key(self, api_key: str):
        self.api_key = api_key

    def set_base_url(self, base_url: str):
        self.base_url = base_url

    def set_model(self, model: str):
        self.model = model
    
    # ================ 参数设置方法 ================
    def set_temperature(self, temperature: float = 0, pattern: str = "通用对话"):
        """设置温度参数，范围0-2"""
        if not 0 <= temperature <= 2:
            raise ValueError("temperature 必须在 0-2 之间")

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

        self.temperature = temperature_map.get(pattern, temperature)
    
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
        if isinstance(stop, list) and len(stop) > 16:
            raise ValueError("stop列表最多包含16个元素")
        self.stop = stop
    
    def set_response_format(self, response_format: dict):
        """设置响应格式，如 {"type": "json_object"}"""
        if not isinstance(response_format, dict) or "type" not in response_format:
            raise ValueError("response_format 必须是包含 type 字段的字典")
        if response_format["type"] not in ["text", "json_object"]:
            raise ValueError("response_format type 必须是 'text' 或 'json_object'")
        self.response_format = response_format
    
    def set_tools(self, tools: list):
        """设置Function Calling工具列表，自动转换MCP格式到OpenAI格式"""
        if not isinstance(tools, list):
            raise ValueError("tools 必须是列表类型")
        if len(tools) > 128:
            raise ValueError("tools列表最多包含128个工具")

        # 转换MCP工具格式到OpenAI Function Calling格式
        converted_tools = tools


        self.tools = converted_tools
    
    def set_tool_choice(self, tool_choice):
        """设置工具选择策略"""
        self.tool_choice = tool_choice
    
    def set_logprobs(self, logprobs: bool):
        """设置是否返回log概率"""
        self.logprobs = logprobs
    
    def set_top_logprobs(self, top_logprobs: int):
        """设置返回top N个log概率，范围0-20"""
        if not 0 <= top_logprobs <= 20:
            raise ValueError("top_logprobs 必须在 0-20 之间")
        self.top_logprobs = top_logprobs

    #  ============ 生成链接参数 ============
    def gen_params(self):
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
        }
    #  ============ 生成请求参数 ============
    def gen_request(self, messages: list):
        """
        生成请求参数，包含完整的DeepSeek API参数
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

        if self.logprobs:
            request_params["logprobs"] = self.logprobs

        if self.top_logprobs is not None:
            request_params["top_logprobs"] = self.top_logprobs

        return request_params
        
    #  ============ 生成请求参数(流式) ============
    def gen_params_stream(self, messages: list):
        """
        生成流式请求参数，包含完整的DeepSeek API参数
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
        对 deepseek，流式传输时 usage 字段为 None 表示还在传输；当 usage 存在且 choices 为空数组，则为流式的终结块（data: [DONE] 之前的 usage 块）。
        """
        # DeepSeek: 若有 usage 且 choices 为空数组，表示最后一个 usage 块；也允许处理 SSE 结束标志(data: [DONE])在外部完成
        usage = stream_options.get("usage", None)
        choices = stream_options.get("choices", None)
        if usage is not None and choices == []:
            return True  # 最后一块 usage，表示流式结束
        return False  # 其他情况都不是结束（包括 usage 为 None，或 choices 不为空等）

    #  ============ 提取流式信息数据 ============
    def extract_stream_info(self, stream_options: dict) -> dict:
        """
        提取流式信息数据, 提取delta.content字段或tool_calls字段，若为 usage 终结块则返回 None
        """

        # 如果是最后的usage块（choices==[]且usage非None），无内容，直接返回None
        choices = stream_options.get('choices', [])
        # print(f"\n需要提取的数据是: {choices}")
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

        thinking = delta.get('reasoning_content', None)
        # print(f"\n需要提取的数据是: {thinking}")
        if thinking is not None:
            return {"thinking": thinking}
        # 如果没有文本内容，检查是否有工具调用

        tool_calls = delta.get('tool_calls', None)
        print(f"\n需要提取的数据是: {tool_calls}")
        if tool_calls is not None and len(tool_calls) > 0:
            return {"tool_calls": tool_calls}

        return {"None": None}

    #  ============ 计算token的回调函数 ============
    def token_callback(self, content: str) -> int:
        """计算deepseek模型的token数（使用transformers tokenizer）"""
        if not content:
            return 0
        return len(self.tokenizer.encode(content, add_special_tokens=False))
