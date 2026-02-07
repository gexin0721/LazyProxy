# -*- coding: utf-8 -*-
# from openai import OpenAI
import os
from ..Historyfile.HistoryManager import HistHistoryManager
from ..Model.base_model import BaseModel
from logger import logger
from openai import OpenAI

# OPEN_AI 类
class OPEN_AI:
    """
    OPEN_AI API封装类

    通过接收BaseModel子类实例来获取模型特定的参数和方法
    """
    def __init__(
            self,
            model: BaseModel,  # BaseModel子类实例，提供所有模型特定的方法
            system_prompt: str,  # 系统提示词
            user_name: str = None,  # 预留：用户名（用户历史管理）
            user_level: int = 0  # 预留：用户等级（VIP/MCP服务/工具权限）
        ):
        # 数据验证
        if not isinstance(model, BaseModel):
            raise ValueError("model 必须是 BaseModel 的子类实例")
        if not isinstance(system_prompt, str):
            raise TypeError("system_prompt 必须是字符串类型")
        if not system_prompt.strip():
            raise ValueError("system_prompt 不能为空")

        # 保存模型实例
        self._model = model

        # 保存预留参数
        self._user_name = user_name
        self._user_level = user_level

        # 创建客户端（使用模型的gen_params方法获取连接参数）
        self._client = OpenAI(**self._model.gen_params())

        # 创建历史记录管理器
        self._history = HistHistoryManager(
            messages=[],
            system_prompt=system_prompt,
            token_callback=self._model.token_callback,
            maxtoken=self._model.max_tokens
        )

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
            如果提供了 get_upload_params_callback，将使用模型特定的上传参数
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
        
        # ========== 模型特定验证 ==========
        # 调用模型的validate_file方法进行验证
        if hasattr(self._model, 'validate_file'):
            try:
                is_valid, error_message = self._model.validate_file(file_path, purpose)

                # 验证返回值类型
                if not isinstance(is_valid, bool):
                    raise ValueError(f"validate_file 必须返回 tuple(bool, str)，但 bool 部分返回了 {type(is_valid).__name__}")
                if not isinstance(error_message, str):
                    raise ValueError(f"validate_file 必须返回 tuple(bool, str)，但 str 部分返回了 {type(error_message).__name__}")

                # 如果验证失败，抛出异常
                if not is_valid:
                    raise ValueError(f"文件验证失败: {error_message}")

            except ValueError:
                # 重新抛出验证失败的异常
                raise
            except TypeError as e:
                raise ValueError(f"validate_file 调用失败，签名错误: {e}")
            except Exception as e:
                raise RuntimeError(f"调用 validate_file 时发生错误: {e}")

        # ========== 获取上传参数 ==========
        upload_params = {}
        if hasattr(self._model, 'get_upload_params'):
            try:
                # 调用模型的get_upload_params方法获取上传参数
                upload_params = self._model.get_upload_params(purpose)

                # 验证返回值类型
                if not isinstance(upload_params, dict):
                    raise ValueError(f"get_upload_params 必须返回 dict 类型，但返回了 {type(upload_params).__name__}")

            except TypeError as e:
                raise ValueError(f"get_upload_params 调用失败，签名错误: {e}")
            except Exception as e:
                raise RuntimeError(f"调用 get_upload_params 时发生错误: {e}")
        
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

    #  ================ 私有方法 ================
    def _validate_message_params(self, problem: str, role: str) -> tuple:
        """
        验证消息参数

        参数:
            problem: 消息内容
            role: 消息角色

        返回:
            tuple: (处理后的problem, 处理后的role)

        异常:
            TypeError: 参数类型错误
            ValueError: 参数值无效
        """
        if not isinstance(problem, str):
            raise TypeError("problem 必须是字符串类型")
        if not problem.strip():
            raise ValueError("problem 不能为空或空白字符串")
        if not isinstance(role, str):
            raise TypeError("role 必须是字符串类型")

        problem = problem.strip()
        role = role.strip()

        valid_roles = {"user", "system", "assistant"}
        if role not in valid_roles:
            raise ValueError(f"role 必须是 {valid_roles} 之一，当前值为: {role}")

        return problem, role

    def _process_stream_chunk(self, chunk) -> dict:
        """
        处理单个流式chunk

        参数:
            chunk: OpenAI返回的chunk对象

        返回:
            dict: 处理后的结果字典，如 {"content": "..."} 或 {"thinking": "..."} 或 {"None": None}
        """
        # 将chunk转换为dict
        try:
            chunk_dict = chunk.model_dump() if hasattr(chunk, 'model_dump') else chunk.dict()
        except:
            return {"None": None}

        # 使用模型方法判断是否结束
        try:
            if self._model.is_stream_end(chunk_dict):
                return {"end": True}
        except Exception as e:
            logger.warning(f"判断流式结束时发生错误: {e}")

        # 使用模型方法提取内容
        try:
            result_dict = self._model.extract_stream_info(chunk_dict)
            if not isinstance(result_dict, dict):
                return {"None": None}
            return result_dict
        except Exception as e:
            logger.warning(f"提取流式内容时发生错误: {e}")
            return {"None": None}

    async def _save_response_to_history(self, content: str, thinking: str = None):
        """
        保存响应到历史记录

        参数:
            content: 回复内容
            thinking: 思考过程内容
        """
        try:
            await self._history.write("assistant", content,thinking)
        except Exception as e:
            logger.warning(f"保存 AI 回答到历史记录失败: {e}")


    #  ================ 发送请求 （流式）================
    async def send_stream(self, problem: str, role: str = "user"):
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

        示例用法:
            for chunk in client.send_stream("你好"):
                print(chunk, end="", flush=True)
        """
        # 验证输入参数
        problem, role = self._validate_message_params(problem, role)

        # 先保存消息到历史（使用指定的角色）
        try:
            # 如果是工具结果且已有思考记录，插入空占位
            if role == "system" and len(self._history.think_token_counts) > 0:
                await self._history.write(role, problem, think_content="")
            else:
                await self._history.write(role, problem)
        except Exception as e:
            # 如果保存失败，记录警告但继续执行
            logger.warning(f"保存消息到历史记录失败: {e}")

        # 获取请求参数（使用模型的流式参数生成方法）
        try:
            messages = self._history.read()
            request_params = self._model.gen_params_stream(messages)
            if not isinstance(request_params, dict):
                raise ValueError("gen_params_stream 返回值必须是字典类型")
        except Exception as e:
            raise RuntimeError(f"获取流式请求参数时发生错误: {e}")

        # 累积完整响应内容，用于最后保存到历史
        # 分离 content 和 thinking 的累积
        full_response = ""  # 普通回复内容
        full_thinking = ""  # 思考过程内容
        full_tool_calls = []  # 工具调用累积

        try:
            # 调用 chat.completions.create 获取流式响应
            stream = self._client.chat.completions.create(**request_params)

            # 遍历流式响应
            for chunk in stream:
                # 使用私有方法处理chunk
                result_dict = self._process_stream_chunk(chunk)

                # 检查是否结束
                if result_dict.get("end"):
                    break

                # 提取类型和数据
                data_type = list(result_dict.keys())[0] if result_dict else "None"
                content = result_dict.get(data_type)

                # 如果提取的内容为空或None，跳过
                if content is None or content == "" or data_type == "None":
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
                elif data_type == "tool_calls":
                    full_tool_calls.extend(content)

                # yield 当前片段（字典格式）
                yield result_dict

        except Exception as e:
            # 如果出现错误，尝试保存已经获取的部分响应
            await self._save_response_to_history(full_response, full_thinking)
            raise RuntimeError(f"调用 OpenAI API 流式接口时发生错误: {e}")

        finally:
            # 保存完整的 AI 回答到历史
            await self._save_response_to_history(full_response, full_thinking)

            # 如果没有工具调用，清除思考内容（释放token）
            if not full_tool_calls:
                self._history.clear_think()

    #  ================ 预留接口 ================
    def _on_token_usage(self, tokens: int):
        """
        token使用监控接口（预留）
        上层可通过继承重写此方法来管理用户token消耗
        """
        pass

    #  ================ 参数管理接口 ================
    def get_params(self) -> dict:
        """
        获取当前所有可配置参数

        返回:
            dict: 包含所有可配置参数的字典
        """
        return {
            "temperature": self._model.temperature,
            "top_p": self._model.top_p,
            "max_tokens": self._model.max_tokens,
            "frequency_penalty": self._model.frequency_penalty,
            "presence_penalty": self._model.presence_penalty,
            "stop": self._model.stop,
            "response_format": self._model.response_format,
            "tools": self._model.tools,
            "tool_choice": self._model.tool_choice,
            "logprobs": self._model.logprobs,
        }

    def set_params(self, params: dict):
        """
        批量设置参数

        参数:
            params: 参数字典，支持的键：
                - temperature: 温度参数 (0-2)
                - top_p: 核采样参数 (0-1)
                - max_tokens: 最大token数
                - frequency_penalty: 频率惩罚 (-2到2)
                - presence_penalty: 存在惩罚 (-2到2)
                - stop: 停止词
                - response_format: 响应格式
                - logprobs: 是否返回log概率

        异常:
            TypeError: params 不是字典类型
            ValueError: 参数值无效
        """
        if not isinstance(params, dict):
            raise TypeError("params 必须是字典类型")

        # 参数名到 setter 方法的映射
        setter_map = {
            "temperature": self._model.set_temperature,
            "top_p": self._model.set_top_p,
            "max_tokens": self._model.set_max_tokens,
            "frequency_penalty": self._model.set_frequency_penalty,
            "presence_penalty": self._model.set_presence_penalty,
            "stop": self._model.set_stop,
            "response_format": self._model.set_response_format,
            "logprobs": self._model.set_logprobs,
        }

        # 遍历参数并调用对应的 setter
        for key, value in params.items():
            if key in setter_map:
                setter_map[key](value)
            else:
                logger.warning(f"未知参数: {key}，已忽略")

    #  ================ 工具设置接口 ================
    def set_tools(self, tools: list):
        """
        设置工具列表

        参数:
            tools: 工具列表

        异常:
            ValueError: tools 不是列表类型或超过128个
        """
        self._model.set_tools(tools)
