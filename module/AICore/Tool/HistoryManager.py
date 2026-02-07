import os
import json
from typing import Callable
from tools import logger

# assistant.json 的 token 数最大限制倍数
_assistant_Maximum_token_multiplier = 0.8
# 历史类
class HistoryManager:
    # 可选：验证列表内容的有效性
    # ================ 初始化 ===============
    # * 参数：token_callback: Callable[[str], int] (必需)
    # role_path: str (必需，指向role目录，如 "role/role_A")
    # max_tokens: int = 4096
    # * 功能：初始化 HistoryManager 类，role_path必须指向包含assistant.json的role目录
    # * 返回：None
    # * 示例：HistoryManager(token_callback=lambda x: len(x), role_path="role/role_A", max_tokens=4096)
    def __init__(self, token_callback: Callable[[str], int], role_path: str, max_tokens: int = 4096):
        """
        初始化 HistoryManager 类
        
        参数:
            token_callback: 计算token数的回调函数，接受str返回int
            role_path: role目录路径（必需），必须包含assistant.json文件，会自动创建history.json
            max_tokens: 最大token限制，默认4096
        """
        # ========== 第1步：验证 token_callback 回调函数 ==========
        if not callable(token_callback):
            raise ValueError("token_callback 必须是可调用对象")
        
        # 运行时验证：测试回调函数是否能正确工作
        try:
            test_result = token_callback("test")
            if not isinstance(test_result, int):
                raise ValueError(f"token_callback 必须返回 int 类型，但返回了 {type(test_result).__name__}")
            if test_result < 0:
                raise ValueError("token_callback 返回值不能为负数")
        except TypeError as e:
            raise ValueError(f"token_callback 签名错误，应接受一个 str 参数: {e}")

        # ========== 第2步：验证 max_tokens 参数 ==========
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            raise ValueError("max_tokens 必须是正整数")

        # ========== 第3步：验证 role_path 目录 ==========
        if not isinstance(role_path, str) or not role_path.strip():
            raise ValueError("role_path 必须是非空字符串")
        role_path = role_path.strip()
        
        if not os.path.exists(role_path) or not os.path.isdir(role_path):
            raise ValueError(f"role_path 目录不存在: {role_path}")

        # ========== 第4步：构建文件路径 ==========
        assistant_json_path = os.path.join(role_path, "assistant.json")  # 提示词文件
        history_json_path = os.path.join(role_path, "history.json")      # 历史文件

        # ========== 第5步：读取并验证 assistant.json（提示词）==========
        if not os.path.isfile(assistant_json_path):
            raise FileNotFoundError(f"{assistant_json_path} 文件不存在")

        try:
            # 读取提示词内容
            with open(assistant_json_path, 'r', encoding='utf-8') as f:
                assistant_content = json.load(f)
            
            # 计算提示词的token数
            assistant_tokens = token_callback(assistant_content.get("content", ""))
            
            # 检查是否超过限制（不能超过max_tokens的80%）
            if assistant_tokens > max_tokens * _assistant_Maximum_token_multiplier:
                raise ValueError(
                    f"assistant.json 的 token 数为 {assistant_tokens}，"
                    f"超过最大限制 {max_tokens * _assistant_Maximum_token_multiplier:.0f}"
                )
            
            # 保存提示词信息，供后续使用
            self._assistant_tokens = assistant_tokens      # 提示词的token数
            self._assistant_content = assistant_content    # 提示词的完整内容
        except Exception as e:
            raise RuntimeError(f"读取或分析 assistant.json token 失败: {e}")

        # ========== 第6步：初始化 history.json（确保第一条是最新提示词）==========
        self._history_path = history_json_path
        
        try:
            # 读取现有历史（如果文件不存在则为空）
            if os.path.isfile(history_json_path):
                with open(history_json_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                if not isinstance(history, list):
                    history = []
            else:
                history = []
            
            # 保留第2条及以后的对话内容
            other_messages = history[1:] if len(history) > 1 else []
            
            # 重建历史：[最新提示词] + [其他对话]
            history = [assistant_content] + other_messages
            
            # 写回文件
            with open(history_json_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"初始化历史文件失败: {e}")
            # 出错时创建只包含提示词的新文件
            with open(history_json_path, 'w', encoding='utf-8') as f:
                json.dump([assistant_content], f, ensure_ascii=False, indent=2)
        
        # ========== 第7步：保存实例属性 ==========
        self._token_callback = token_callback  # 计算token的回调函数
        self._max_tokens = max_tokens          # 最大token限制
        self._valid_roles = {"user", "system", "assistant"}  # 有效角色
    # ================ 设置历史路径 ===============
    def set_history_path(self, history_path: str):
        """
        重新设置历史文件路径，并初始化（如需）
        
        ⚠️ 警告：此方法会绕过 role_path 的约束，仅用于特殊场景。
        不建议常规使用，因为这可能导致历史文件散落各处。
        """
        if not isinstance(history_path, str) or not history_path.strip():
            raise ValueError("历史文件路径必须为非空字符串")  # 检查类型
        
        history_path = history_path.strip()
        
        # 检查路径是否是文件（不是目录）
        if os.path.exists(history_path) and os.path.isdir(history_path):
            raise ValueError("history_path 必须是文件路径，不能是目录")
            
        self._history_path = history_path  # 更新路径
        
        # 如果新路径下文件不存在，则创建文件并写入提示词作为第一条消息
        if not os.path.exists(self._history_path):
            # 确保目录存在
            dir_path = os.path.dirname(self._history_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            # 创建历史文件，包含提示词作为第一条消息
            self.write_JSON(self._history_path, [self._assistant_content])
    # ================ 清空对话历史 ===============
    def clear(self):
        """
        清空对话历史，重置为初始状态（只保留第一条提示词）
        """
        try:
            if not os.path.exists(self._history_path):
                raise ValueError("历史文件路径不存在")

            # 重置为初始状态：只包含提示词
            self.write_JSON(self._history_path, [self._assistant_content])
        except Exception as e:
            raise RuntimeError(f"无法清空历史文件: {e}")

    # ================ 清空所有 reasoning_content 字段 ===============
    def clear_reasoning_content(self):
        """
        清空所有历史记录中的 reasoning_content 字段

        功能：
            遍历所有历史记录，删除每条记录中的 reasoning_content 字段（如果存在）
            保留 role 和 content 字段不变

        返回：
            None

        异常：
            RuntimeError: 读取或写入历史文件失败
        """
        try:
            # 读取当前历史
            history = self.get()

            if not history:
                # 历史为空，无需处理
                return

            # 遍历所有记录，删除 reasoning_content 字段
            modified = False
            for entry in history:
                if isinstance(entry, dict) and "reasoning_content" in entry:
                    del entry["reasoning_content"]
                    modified = True

            # 如果有修改，写回文件
            if modified:
                self.write_JSON(self._history_path, history)

        except Exception as e:
            raise RuntimeError(f"清空 reasoning_content 字段失败: {e}")

    # ================ 获取对话历史 ===============
    def get(self) -> list:
        """
        获取完整对话历史，返回一个历史列表
        """
        if not os.path.exists(self._history_path):
            return []  # 如果历史文件不存在，返回空
        try:
            data = self.read_JSON(self._history_path)
            if isinstance(data, list):
                return data  # 返回历史列表
            return []
        except Exception as e:
            logger.error(f"获取对话历史失败: {e}")
            return []
    # ================ 插入对话历史 ===============
    def insert(self, role: str, content: str, reasoning_content: str = None):
        """
        插入单独一条对话，role 为角色（限 'user'、'system'、'assistant'），content 为问题或回答（均为字符串），追加到历史

        参数:
            role: 角色类型（'user'、'system'、'assistant'）
            content: 消息内容
            reasoning_content: 可选，思考过程内容（仅用于 assistant 角色）
        """
        # 严格类型检查
        if not isinstance(role, str) or not isinstance(content, str):
            raise TypeError("role 和 content 必须是字符串类型")

        if reasoning_content is not None and not isinstance(reasoning_content, str):
            raise TypeError("reasoning_content 必须是字符串类型或 None")

        # 判断数据是否为空
        if not role.strip() or not content.strip():
            raise ValueError("role 和 content 不能为空或空白字符串")

        role = role.strip()
        content = content.strip()

        # 处理 reasoning_content
        if reasoning_content is not None:
            reasoning_content = reasoning_content.strip()
            # 如果 reasoning_content 为空字符串，设置为 None
            if not reasoning_content:
                reasoning_content = None

        # 判断角色是否为有效值
        if role not in self._valid_roles:
            raise ValueError(f"role 必须为 {list(self._valid_roles)} 之一")

        # 检查内容本身的 token 数是否已经超过最大值，保护极端情况
        try:
            content_token_count = self._token_callback(content)
            if not isinstance(content_token_count, int) or content_token_count < 0:
                raise ValueError("token_callback 返回了无效的 token 数")
        except Exception as e:
            raise RuntimeError(f"计算 token 时发生错误: {e}")

        if content_token_count > self._max_tokens:
            raise ValueError("单条 content 的 token 数已超过最大限制，无法存储该对话。")

        # 构建新记录
        history = self.get()  # 读取历史
        entry = {"role": role, "content": content}  # 构建新记录

        # 如果有 reasoning_content，添加到记录中
        if reasoning_content is not None:
            entry["reasoning_content"] = reasoning_content

        history.append(entry)  # 追加新记录

        # 写入历史：如果未超出 token 限制则直接写入，否则调用 trim（裁剪中负责写入）
        token_counts = [self._token_callback(item.get("content", "")) for item in history]
        total_tokens = sum(token_counts)
        if total_tokens > self._max_tokens:
            self.trim(history, token_counts)  # 传入history和token_counts，避免重新读取和计算
        else:
            self.write_JSON(self._history_path, history)
    # ================ 在指定位置插入对话历史 ===============
    def insert_POS(self, index: int, role: str, content: str):
        """
        在指定位置插入对话历史，index 为索引，role 为角色（限 'user'、'system'、'assistant'），content 为问题或回答（均为字符串）
        注意：index 可以等于 len(history)，表示在末尾追加
        """
        # 类型检查
        if not isinstance(role, str):
            raise TypeError("role 必须是字符串类型")
        if not isinstance(content, str):
            raise TypeError("content 必须是字符串类型")
        if not isinstance(index, int):
            raise TypeError("index 必须是整数类型")
        
        # 值检查
        if role not in self._valid_roles:
            raise ValueError(f"role 必须为 {list(self._valid_roles)} 之一")
        if index < 0:
            raise ValueError("index 不能为负数")
        
        history = self.get()
        if index > len(history):
            raise ValueError(f"index ({index}) 超出范围，历史记录数为 {len(history)}，最大可插入位置为 {len(history)}（末尾）")
        
        history.insert(index, {"role": role, "content": content})
        self.overwrite(history)
    # ================ 批量插入对话历史 ===============
    def extend(self, entries: list):
        """
        批量扩展历史，多条对话（列表），一般entries为[{role:..., content:...}]
        参考单个插入逻辑，含类型校验、role校验和token裁剪
        """
        if not isinstance(entries, list):
            raise TypeError("entries 必须是列表类型")
        
        # 允许空列表，直接返回
        if not entries:
            return


        # 检查所有 entry 必须为字典且有正确的 role 和 content
        new_entries = []
        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise TypeError(f"第 {idx} 个 entry 不是字典类型")
            
            if "role" not in entry or "content" not in entry:
                raise ValueError(f"第 {idx} 个 entry 缺少 role 或 content 字段")
            
            # 严格类型检查
            if not isinstance(entry["role"], str) or not isinstance(entry["content"], str):
                raise TypeError(f"第 {idx} 个 entry 的 role 和 content 必须是字符串类型")
            
            role = entry["role"].strip()
            content = entry["content"].strip()
            
            if not role or not content:
                raise ValueError(f"第 {idx} 个 entry 的 role 和 content 不能为空或空白字符串")
            
            if role not in self._valid_roles:
                raise ValueError(f"第 {idx} 个 entry 的 role 必须为 {list(self._valid_roles)} 之一")
            
            # 补充: 检查每条 content 是否会直接超过最大限制
            try:
                content_token_count = self._token_callback(content)
                if not isinstance(content_token_count, int) or content_token_count < 0:
                    raise ValueError("token_callback 返回了无效的 token 数")
            except Exception as e:
                raise RuntimeError(f"计算第 {idx} 个 entry 的 token 时发生错误: {e}")
            
            if content_token_count > self._max_tokens:
                raise ValueError(
                    f"第 {idx} 个 entry 的 content token 数已超过最大限制，role: {role}，无法存储该对话。"
                )
            new_entries.append({"role": role, "content": content})

        # 读取历史，扩展
        history = self.get()
        history.extend(new_entries)

        # 检查是否需要裁剪
        token_counts = [self._token_callback(item.get("content", "")) for item in history]
        total_tokens = sum(token_counts)
        if total_tokens > self._max_tokens:
            # 需要裁剪，传入history和token_counts，由 trim() 内部负责写入
            self.trim(history, token_counts)
        else:
            # 不需要裁剪，直接写入
            try:
                with open(self._history_path, "w", encoding="utf-8") as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)
            except (OSError, IOError, PermissionError) as e:
                raise RuntimeError(f"无法写入历史文件: {e}")
    # ================ 删除对话历史 ================ 
    # * 参数：index: int = None, role: str = "assistant"
    # * 功能：删除对话历史，index 为索引，role 为角色（限 'user'、'system'、'assistant'）
    # * 返回：None
    # * 示例：delete(index=0) # 删除第一条对话
    # * 示例：delete(role="user") # 删除所有用户对话
    # * 示例：delete(index=0, role="user") # 删除第一条用户对话
    # * 示例：delete(index=0, role="assistant") # 删除第一条助手对话
    # * 示例：delete(index=0, role="system") # 删除第一条系统对话
    def delete(self, index: int = None):
        """
        删除对话历史，index 为索引（0为第一条），不传则不做任何操作

        如果 index 越界，抛出 ValueError。
        """
        # 如果不传 index，直接返回
        if index is None:
            return
        
        # 类型检查
        if not isinstance(index, int):
            raise TypeError("index 必须是整数类型")
        
        # 值检查
        if index < 0:
            raise ValueError("index 不能为负数")
        
        history = self.get()
        if not history:
            raise ValueError("历史记录为空，无法删除")
        if index >= len(history):
            raise ValueError(f"index ({index}) 超出范围，历史记录数为 {len(history)}")
        
        # 删除指定索引的历史记录
        history.pop(index)

        try:
            with open(self._history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except (OSError, IOError, PermissionError) as e:
            raise RuntimeError(f"无法删除历史文件: {e}")
    # ================ 替换对话历史 ===============
    def replace(self, index: int, role: str, content: str):
        """
        替换对话历史，index 为索引，role 为角色（限 'user'、'system'、'assistant'），content 为问题或回答（均为字符串）
        若索引指向的角色和传入的角色一致，则替换；否则抛出异常。
        {
          role: "user",
          content: "问题或回答"
        }
        """
        # 类型检查
        if not isinstance(index, int):
            raise TypeError("index 必须是整数类型")
        if not isinstance(content, str):
            raise TypeError("content 必须是字符串类型")
        if not isinstance(role, str):
            raise TypeError("role 必须是字符串类型")
        
        # 值检查
        if role not in self._valid_roles:
            raise ValueError(f"role 必须为 {list(self._valid_roles)} 之一")
        if index < 0:
            raise ValueError("index 不能为负数")
        
        history = self.get()
        if not history:
            raise ValueError("历史记录为空，无法替换")
        if index >= len(history):
            raise ValueError(f"index ({index}) 超出范围，历史记录数为 {len(history)}")

        # 检查 role 是否一致
        if history[index].get("role") != role:
            raise ValueError(f"索引位置的 role（{history[index].get('role')}）与传入的 role（{role}）不一致，无法替换")
        
        # 直接替换
        history[index] = {"role": role, "content": content}
        
        try:
            with open(self._history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except (OSError, IOError, PermissionError) as e:
            raise RuntimeError(f"无法写入历史文件: {e}")

    # ================ 裁剪历史 ===============
    def trim(self, history=None, token_counts=None):
        """
        裁剪历史：从后往前累加token，直到超过最大token数，只保留靠后的内容
        
        ⚠️ CRITICAL: 永久保留第一条 system 角色消息（提示词 = assistant.json）！
        后续的 system 消息（用于补充数据）可以被裁剪。

        可选参数:
        - history: None 或 List[dict]，要裁剪的历史列表。若为 None 则从文件读取
        - token_counts: None 或 List[int]（与 history 等长），表示历史中每条记录已提前算好的 token 数，若未提供则内部重新计算

        算法思路：
        - 永久保留第一条 system 角色消息（提示词 = assistant.json）
        - 对于其他消息（包括后续的system）：保留最新的对话，删除最旧的对话
        - 从末尾开始向前累加 token，找到第一个超过限制的点
        - 时间复杂度：O(k)，其中 k 是历史记录保留数（最差是O(n)，n是历史记录数）

        示例（假设有10条记录，索引0是第一条system，索引1-9是对话和补充数据）：
        - 第一条system (索引0) → 永久保留
        - 其他消息 (索引1-9) → 参与裁剪
        - 从后往前累加，找到超过限制的位置
        - 保留 history[0] + 裁剪后的其他消息
        """
        if history is None:
            history = self.get()
        if not history:
            raise RuntimeError("历史记录为空，无法裁剪")

        if token_counts is not None:
            if not isinstance(token_counts, list) or len(token_counts) != len(history):
                raise ValueError("token_counts 参数必须为与 history 等长的列表")
        else:
            # 预先计算所有记录的 token 数（避免重复调用回调函数）
            token_counts = [self._token_callback(item.get("content", "")) for item in history]
        
        # 只保留第一条 system 消息（提示词），其他所有消息参与裁剪
        first_system_msg = None
        first_system_tokens = 0
        other_messages = []
        other_token_counts = []
        
        for idx, item in enumerate(history):
            if idx == 0 and item.get("role") == "system":
                # 第一条是 system 消息（提示词 = assistant.json），永久保留
                first_system_msg = item
                first_system_tokens = self._assistant_tokens  # 使用初始化时计算的值
            else:
                # 其他所有消息（包括后续的system补充数据）都参与裁剪
                other_messages.append(item)
                other_token_counts.append(token_counts[idx])
        
        # 【方案2】检查第一条system消息是否超标
        if first_system_msg and first_system_tokens >= self._max_tokens:
            raise RuntimeError(
                f"第一条system消息(提示词)占用 {first_system_tokens} tokens，"
                f"已超过或等于max_tokens限制({self._max_tokens})，无法存储任何对话。"
                f"请增加max_tokens或精简assistant.json中的提示词。"
            )
        
        # 如果没有其他消息，无法裁剪
        if not other_messages:
            raise RuntimeError("除第一条system消息外没有其他可裁剪的历史记录")
        
        # 计算可用token额度
        available_tokens = self._max_tokens - first_system_tokens
        
        # 从后往前累加token，找到裁剪起始位置
        total = 0
        start_idx = 0
        
        for i in range(len(other_messages)-1, -1, -1):
            total += other_token_counts[i]
            if total > available_tokens:
                # 超过限制，从 i+1 开始保留
                start_idx = i + 1
                break
        
        # 裁剪：第一条system + 裁剪后的其他消息
        if first_system_msg:
            trimmed_history = [first_system_msg] + other_messages[start_idx:]
        else:
            # 如果第一条不是system，所有消息都参与裁剪
            trimmed_history = other_messages[start_idx:]
        
        # 保存裁剪后的历史
        try:
            with open(self._history_path, "w", encoding="utf-8") as f:
                json.dump(trimmed_history, f, ensure_ascii=False, indent=2)
        except (OSError, IOError, PermissionError) as e:
            raise RuntimeError(f"无法写入裁剪后的历史文件: {e}")
        
    # ================ 直接重写历史 ===============
    def overwrite(self, history: list):
        """
        用新的历史（列表）直接覆盖历史文件
        
        警告：此方法不做任何验证，请确保传入的数据格式正确
        """
        if not isinstance(history, list):
            raise TypeError("history 必须是列表类型")  # 必须为列表类型
        

        for idx, item in enumerate(history):
            if not isinstance(item, dict):
                raise TypeError(f"history 中第 {idx} 个元素不是字典类型")
            if "role" not in item or "content" not in item:
                raise ValueError(f"history 中第 {idx} 个元素缺少 role 或 content 字段")
            if not isinstance(item["role"], str) or not isinstance(item["content"], str):
                raise TypeError(f"history 中第 {idx} 个元素的 role 和 content 必须是字符串")
            if item["role"] not in self._valid_roles:
                raise ValueError(f"history 中第 {idx} 个元素的 role 无效: {item['role']}")
        
        try:
            with open(self._history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)  # 直接写入新历史
        except (OSError, IOError, PermissionError) as e:
            raise RuntimeError(f"无法覆写历史文件: {e}")

    
    # ================ JSON文件操作 ================
    #  -------------- 读取JSON文件 --------------
    def read_JSON(self, filepath,_encoding='utf-8'):
        """
        读取JSON文件
        :param filepath: 文件路径
        :param _encoding: 文件编码
        :return: JSON数据
        :error: 文件不存在
        """
        # 如果文件不存在，无法读取
        if not os.path.exists(filepath):
            return None
        try:
          # 读取文件
          with open(filepath, 'r', encoding=_encoding) as f:
              return json.load(f)
        except Exception as e:
          logger.error(f"读取JSON文件失败: {e}")
          return None

    
    #  -------------- 写入JSON文件 --------------
    def write_JSON(self, filepath, data, _encoding='utf-8'):
        """
        写入JSON文件（覆盖）
        :param filepath: 文件路径
        :param data: JSON数据
        :param _encoding: 文件编码
        :return: 是否成功
        :error: 文件不存在
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
            
            # 用'w'模式写入
            with open(filepath, 'w', encoding=_encoding) as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"写入JSON失败: {e}")
            return False
