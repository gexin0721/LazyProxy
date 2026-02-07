from openai import OpenAI
from typing import Callable
import json
import os
from .HistoryManager import HistoryManager

# OPEN_AI 类
class OPEN_AI:
    """
    OPEN_AI API封装类
    """
    def __init__(
            self,
            request_params: dict,
            max_tokens: int,
            get_params_callback: Callable[[list], dict],  # 接受list(对话历史)，返回dict(请求参数)   - 非流式参数生成回调函数
            get_params_callback_stream: Callable[[list], dict],  # 接受list(对话历史)，返回dict(请求参数)   - 流式参数生成回调函数
            token_callback: Callable[[str], int],        # 接受str(内容)，返回int(token数)
            is_stream_end_callback: Callable[[dict], bool] = None,  # 接受dict(chunk)，返回bool(是否结束) - 判断流式是否结束
            extract_stream_callback: Callable[[dict], dict] = None,   # 接受dict(chunk)，返回dict({"类型": 数据}) - 提取流式内容
            validate_file_callback: Callable[[str, str], tuple] = None,  # 接受str(file_path), str(purpose)，返回tuple(bool, str) - 验证文件是否合法
            get_upload_params_callback: Callable[[str], dict] = None,  # 接受str(purpose)，返回dict(上传参数) - 生成上传参数
            role_path: str = None  # role目录路径（必需），指向包含assistant.json的role目录，用于区分不同模型
        ):
        # 数据验证
        if not isinstance(request_params, dict):
            raise ValueError("request_params 必须是字典类型")
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            raise ValueError("max_tokens 必须是正整数")
        if not callable(get_params_callback):
            raise ValueError("get_params_callback 必须是可调用对象")
        if not callable(get_params_callback_stream):
            raise ValueError("get_params_callback_stream 必须是可调用对象")
        if not callable(token_callback):
            raise ValueError("token_callback 必须是可调用对象")
        
        # 运行时验证 token_callback
        try:
            test_token_result = token_callback("test")
            if not isinstance(test_token_result, int):
                raise ValueError(f"token_callback 必须返回 int 类型，但返回了 {type(test_token_result).__name__}")
            if test_token_result < 0:
                raise ValueError("token_callback 返回值不能为负数")
        except TypeError as e:
            raise ValueError(f"token_callback 签名错误，应接受一个 str 参数: {e}")
        
        # 运行时验证 get_params_callback
        try:
            test_params_result = get_params_callback("test")
            if not isinstance(test_params_result, dict):
                raise ValueError(f"get_params_callback 必须返回 dict 类型，但返回了 {type(test_params_result).__name__}")
        except TypeError as e:
            raise ValueError(f"get_params_callback 签名错误，应接受一个 str 参数: {e}")
        
        # 运行时验证 get_params_callback_stream
        try:
            test_params_stream_result = get_params_callback_stream("test")
            if not isinstance(test_params_stream_result, dict):
                raise ValueError(f"get_params_callback_stream 必须返回 dict 类型，但返回了 {type(test_params_stream_result).__name__}")
        except TypeError as e:
            raise ValueError(f"get_params_callback_stream 签名错误，应接受一个 str 参数: {e}")

        self._request_params = request_params # 生成链接参数

        self._max_tokens = max_tokens         # 保存最大token数

        self._get_params_callback = get_params_callback # 获取请求参数的回调函数（非流式）
        
        self._get_params_callback_stream = get_params_callback_stream # 获取请求参数的回调函数（流式）

        self._token_callback = token_callback # 计算token的回调函数（因为一家一种token的计算方式，没法统一封装，所以需要一个回调函数）
        
        self._is_stream_end_callback = is_stream_end_callback # 判断流式是否结束的回调函数
        
        self._extract_stream_callback = extract_stream_callback # 提取流式内容的回调函数
        
        self._validate_file_callback = validate_file_callback # 验证文件是否合法的回调函数
        
        self._get_upload_params_callback = get_upload_params_callback # 生成上传参数的回调函数

        self._client = OpenAI(**self._request_params) # 创建客户端

        self._history = HistoryManager(
            token_callback=self._token_callback, 
            role_path=role_path,
            max_tokens=self._max_tokens
        ) # 创建历史记录，token_callback为计算token的回调函数

        self._history.clear() #初始化的时候，清空历史，防止上一轮的数据，干扰到这一轮

    #  ================ 上传文件 ================
    def upload_file(self, file_path: str, purpose: str = "assistants"):
        """
        上传文件到 OpenAI
        
        参数:
            file_path: 文件路径（字符串）
            purpose: 文件用途，可选值: "assistants", "fine-tune", "batch"（具体取决于模型）
        
        返回:
            文件对象，包含 id、filename 等信息
        
        异常:
            TypeError: 参数类型错误
            ValueError: 参数值无效或文件不符合模型要求
            FileNotFoundError: 文件不存在
            RuntimeError: 上传失败
        
        注意:
            如果提供了 validate_file_callback，将使用模型特定的验证逻辑
            如果提供了 get_upload_params_callback，将使用模b型特定的上传参数
        """
        # ========== 基础验证（通用） ==========
        # 验证输入类型
        if not isinstance(file_path, str):
            raise TypeError("file_path 必须是字符串类型")
        if not isinstance(purpose, str):
            raise TypeError("purpose 必须是字符串类型")
        
        # 验证输入值
        if not file_path.strip():
            raise ValueError("file_path 不能为空或空白字符串")
        
        file_path = file_path.strip()
        purpose = purpose.strip()
        
        if not purpose:
            raise ValueError("purpose 不能为空或空白字符串")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 检查是否是文件（不是目录）
        if not os.path.isfile(file_path):
            raise ValueError(f"路径必须是文件，不能是目录: {file_path}")
        
        # 检查文件是否为空
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError("文件为空，无法上传")
        
        # ========== 模型特定验证（可选） ==========
        if self._validate_file_callback is not None:
            try:
                # 调用回调函数进行模型特定验证
                is_valid, error_message = self._validate_file_callback(file_path, purpose)
                
                # 验证返回值类型
                if not isinstance(is_valid, bool):
                    raise ValueError(f"validate_file_callback 必须返回 tuple(bool, str)，但 bool 部分返回了 {type(is_valid).__name__}")
                if not isinstance(error_message, str):
                    raise ValueError(f"validate_file_callback 必须返回 tuple(bool, str)，但 str 部分返回了 {type(error_message).__name__}")
                
                # 如果验证失败，抛出异常
                if not is_valid:
                    raise ValueError(f"文件验证失败: {error_message}")
                    
            except ValueError:
                # 重新抛出验证失败的异常
                raise
            except TypeError as e:
                raise ValueError(f"validate_file_callback 调用失败，签名错误: {e}")
            except Exception as e:
                raise RuntimeError(f"调用 validate_file_callback 时发生错误: {e}")
        
        # ========== 获取上传参数（可选） ==========
        upload_params = {}
        if self._get_upload_params_callback is not None:
            try:
                # 调用回调函数获取上传参数
                upload_params = self._get_upload_params_callback(purpose)
                
                # 验证返回值类型
                if not isinstance(upload_params, dict):
                    raise ValueError(f"get_upload_params_callback 必须返回 dict 类型，但返回了 {type(upload_params).__name__}")
                    
            except TypeError as e:
                raise ValueError(f"get_upload_params_callback 调用失败，签名错误: {e}")
            except Exception as e:
                raise RuntimeError(f"调用 get_upload_params_callback 时发生错误: {e}")
        
        # ========== 执行上传 ==========
        try:
            with open(file_path, "rb") as f:
                # 合并参数：文件、purpose 和模型特定参数
                params = {
                    "file": f,
                    "purpose": purpose,
                    **upload_params  # 展开模型特定参数
                }
                response = self._client.files.create(**params)
            
            # 验证返回值
            if not response or not hasattr(response, 'id'):
                raise ValueError("API 返回了无效的响应")
            
            return response
            
        except FileNotFoundError:
            # 重新抛出文件不存在错误（虽然前面已检查，但以防万一）
            raise FileNotFoundError(f"无法打开文件: {file_path}")
        except PermissionError as e:
            raise RuntimeError(f"没有权限读取文件: {e}")
        except Exception as e:
            raise RuntimeError(f"上传文件时发生错误: {e}")

    #  ================ 发送请求 （非流式）================
    def send(self, problem: str, role: str = "user"):
        """
        发送消息到 OpenAI API 并获取回答

        参数:
            problem: 消息内容（字符串）
            role: 消息角色，可选值：
                - "user": 用户消息（默认）
                - "system": 系统消息（用于MCP工具结果回传等）
                - "assistant": 助手消息（特殊场景）

        返回:
            API 的回答内容
        """
        # 验证输入
        if not isinstance(problem, str):
            raise TypeError("problem 必须是字符串类型")
        if not problem.strip():
            raise ValueError("problem 不能为空或空白字符串")
        if not isinstance(role, str):
            raise TypeError("role 必须是字符串类型")

        problem = problem.strip()
        role = role.strip()

        # 验证角色有效性
        valid_roles = {"user", "system", "assistant"}
        if role not in valid_roles:
            raise ValueError(f"role 必须是 {valid_roles} 之一，当前值为: {role}")

        # 先保存消息到历史（使用指定的角色）
        try:
            self._history.insert(role, problem)
        except Exception as e:
            # 如果保存失败，记录警告但继续执行
            print(f"警告：保存消息到历史记录失败: {e}")
        
        # 获取请求参数
        try:
            messages = self._history.get()
            request_params = self._get_params_callback(messages)
            if not isinstance(request_params, dict):
                raise ValueError("get_params_callback 返回值必须是字典类型")
        except Exception as e:
            raise RuntimeError(f"获取请求参数时发生错误: {e}")
        
        # 调用 chat.completions.create
        try:
            completion = self._client.chat.completions.create(**request_params)
            
            # 检查返回值
            if not completion or not hasattr(completion, 'choices'):
                raise ValueError("API 返回了无效的响应")
            
            if not completion.choices or len(completion.choices) == 0:
                raise ValueError("API 未返回任何回答选项")
            
            if not hasattr(completion.choices[0], 'message'):
                raise ValueError("API 响应缺少 message 字段")
            
            response = completion.choices[0].message.content
            
            # 检查响应内容
            if response is None:
                raise ValueError("API 返回了空的 content")
            
            if not isinstance(response, str):
                response = str(response)  # 尝试转换为字符串
                
        except Exception as e:
            raise RuntimeError(f"调用 OpenAI API 时发生错误: {e}")
        
        # 保存 AI 的回答到历史
        try:
            self._history.insert("assistant", response)
        except Exception as e:
            # 记录错误但不影响返回（因为 API 调用成功了）
            print(f"警告：保存 AI 回答到历史记录失败: {e}")
        
        return response

    #  ================ 发送请求 （流式）================
    def send_stream(self, problem: str, role: str = "user"):
        """
        发送消息到 OpenAI API 并获取流式回答

        参数:
            problem: 消息内容（字符串）
            role: 消息角色，可选值：
                - "user": 用户消息（默认）
                - "system": 系统消息（用于MCP工具结果回传等）
                - "assistant": 助手消息（特殊场景）

        返回:
            生成器（Generator），每次 yield 返回一个 content 片段（字符串） 和 类型（content或tool_calls）

        注意:
            - 需要在初始化时提供 extract_stream_callback 来提取流式内容
            - 可选提供 is_stream_end_callback 来判断流式是否结束

        示例用法:
            for chunk in client.send_stream("你好"):
                print(chunk, end="", flush=True)
        """
        # 检查是否提供了必要的流式回调
        if self._extract_stream_callback is None:
            raise RuntimeError("使用流式输出必须提供 extract_stream_callback 回调函数")

        # 验证输入
        if not isinstance(problem, str):
            raise TypeError("problem 必须是字符串类型")
        if not problem.strip():
            raise ValueError("problem 不能为空或空白字符串")
        if not isinstance(role, str):
            raise TypeError("role 必须是字符串类型")

        problem = problem.strip()
        role = role.strip()

        # 验证角色有效性
        valid_roles = {"user", "system", "assistant"}
        if role not in valid_roles:
            raise ValueError(f"role 必须是 {valid_roles} 之一，当前值为: {role}")

        # 先保存消息到历史（使用指定的角色）
        try:
            self._history.insert(role, problem)
        except Exception as e:
            # 如果保存失败，记录警告但继续执行
            print(f"警告：保存消息到历史记录失败: {e}")
        
        # 获取请求参数（使用流式回调）
        try:
            messages = self._history.get()
            request_params = self._get_params_callback_stream(messages)
            if not isinstance(request_params, dict):
                raise ValueError("get_params_callback_stream 返回值必须是字典类型")
        except Exception as e:
            raise RuntimeError(f"获取流式请求参数时发生错误: {e}")
        
        # 累积完整响应内容，用于最后保存到历史
        # 分离 content 和 thinking 的累积
        full_response = ""  # 普通回复内容
        full_thinking = ""  # 思考过程内容

        try:
            # 调用 chat.completions.create 获取流式响应
            stream = self._client.chat.completions.create(**request_params)

            # 遍历流式响应
            for chunk in stream:
                # 将chunk转换为dict（OpenAI返回的是对象，需要转换为dict供回调使用）
                try: # 将chunk转换为dict
                    chunk_dict = chunk.model_dump() if hasattr(chunk, 'model_dump') else chunk.dict()
                except:
                    # 如果转换失败，跳过这个chunk
                    continue

                # 使用回调判断是否结束（如果提供了回调）
                if self._is_stream_end_callback is not None:
                    try:
                        if self._is_stream_end_callback(chunk_dict):
                            break
                    except Exception as e:
                        print(f"警告：判断流式结束时发生错误: {e}")

                # 使用回调提取内容
                try:
                    result_dict = self._extract_stream_callback(chunk_dict)

                    # 如果返回的不是字典，跳过
                    if not isinstance(result_dict, dict):
                        continue

                    # 提取类型和数据

                    data_type = list(result_dict.keys())[0] if result_dict else "None"#提取类型
                    content = result_dict.get(data_type)#提取数据

                    # 如果提取的内容为空或None，跳过
                    if content is None or content == "":
                        continue

                    # 如果类型是None，跳过
                    if data_type == "None":
                        continue

                    # 分别累积 content 和 thinking
                    if data_type == "content":
                        if not isinstance(content, str):
                            content = str(content)
                        full_response += content
                    elif data_type == "thinking":
                        if not isinstance(content, str):
                            content = str(content)
                        full_thinking += content

                    # yield 当前片段（字典格式）
                    yield result_dict

                except Exception as e:
                    # 提取内容失败时记录警告并继续
                    print(f"警告：提取流式内容时发生错误: {e}")
                    continue

        except Exception as e:
            # 如果出现错误，尝试保存已经获取的部分响应
            if full_response or full_thinking:
                try:
                    self._history.insert("assistant", full_response, reasoning_content=full_thinking if full_thinking else None)
                except:
                    pass
            raise RuntimeError(f"调用 OpenAI API 流式接口时发生错误: {e}")

        # 保存完整的 AI 回答到历史（包括 reasoning_content）
        # 注意：只有当 full_response 不为空时才保存（content 字段不能为空）
        if full_response:
            try:
                self._history.insert("assistant", full_response, reasoning_content=full_thinking if full_thinking else None)
            except Exception as e:
                # 记录错误但不影响返回（因为 API 调用成功了）
                print(f"警告：保存 AI 回答到历史记录失败: {e}")
        elif full_thinking:
            # 如果只有 thinking 没有 content，使用占位符
            try:
                self._history.insert("assistant", "[思考中]", reasoning_content=full_thinking)
            except Exception as e:
                print(f"警告：保存 AI 回答到历史记录失败: {e}")

