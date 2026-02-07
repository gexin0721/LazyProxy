"""
配置验证模块

该模块提供配置文件的验证功能，确保配置文件格式正确且包含必需的字段。

主要功能：
    - 验证 secret_key.json 格式和内容
    - 验证 config.json 格式和内容
    - 验证 assistant.json 格式和内容
    - 提供详细的错误信息

典型用法：
    >>> from tools import ConfigValidator
    >>> validator = ConfigValidator()
    >>> is_valid, errors = validator.validate_all()
    >>> if not is_valid:
    ...     for error in errors:
    ...         print(error)
"""

import os
import json
from typing import Tuple, List, Dict, Any, Optional


class ConfigValidator:
    """
    配置验证器

    验证AI模块的配置文件，确保格式正确且包含必需的字段。

    属性:
        base_dir: 配置文件基础目录（scripts目录）
        role_dir: 角色配置目录（Role目录）
    """

    # 支持的供应商列表
    SUPPORTED_VENDORS = ["deepseek", "qwen", "kimi", "doubao", "chatgpt", "claude", "gemini", "xinhuo"]

    # 必需的配置字段
    REQUIRED_MODEL_FIELDS = ["base_url", "model", "max_tokens"]

    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化配置验证器

        参数:
            base_dir: 配置文件基础目录。如果为None，则使用当前文件所在目录的父目录
        """
        if base_dir is None:
            # 默认使用当前文件所在目录的父目录（scripts目录）
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.base_dir = base_dir
        self.role_dir = os.path.join(base_dir, "role")

    def validate_all(self) -> Tuple[bool, List[str]]:
        """
        验证所有配置文件

        返回:
            (is_valid, errors):
                - is_valid: 是否全部验证通过
                - errors: 错误信息列表

        示例:
            >>> validator = ConfigValidator()
            >>> is_valid, errors = validator.validate_all()
            >>> if not is_valid:
            ...     for error in errors:
            ...         print(f"错误: {error}")
        """
        errors = []

        # 验证 secret_key.json
        is_valid, error_list = self.validate_secret_key()
        if not is_valid:
            errors.extend(error_list)

        # 验证 config.json
        is_valid, error_list = self.validate_config()
        if not is_valid:
            errors.extend(error_list)

        # 验证角色配置
        is_valid, error_list = self.validate_roles()
        if not is_valid:
            errors.extend(error_list)

        return len(errors) == 0, errors

    def validate_secret_key(self) -> Tuple[bool, List[str]]:
        """
        验证 secret_key.json 文件

        检查项：
            1. 文件是否存在
            2. 文件是否为有效的JSON格式
            3. 是否包含至少一个供应商的密钥
            4. 密钥值是否为非空字符串

        返回:
            (is_valid, errors): 验证结果和错误信息列表
        """
        errors = []
        file_path = os.path.join(self.role_dir, "secret_key.json")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            errors.append(f"secret_key.json 文件不存在: {file_path}")
            return False, errors

        # 检查是否为文件
        if not os.path.isfile(file_path):
            errors.append(f"secret_key.json 不是文件: {file_path}")
            return False, errors

        # 读取并解析JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"secret_key.json 不是有效的JSON格式: {e}")
            return False, errors
        except Exception as e:
            errors.append(f"读取 secret_key.json 失败: {e}")
            return False, errors

        # 检查是否为字典
        if not isinstance(data, dict):
            errors.append("secret_key.json 必须是一个JSON对象（字典）")
            return False, errors

        # 检查是否为空
        if not data:
            errors.append("secret_key.json 不能为空，至少需要配置一个供应商的密钥")
            return False, errors

        # 检查每个供应商的密钥
        for vendor, api_key in data.items():
            # 检查供应商名称
            if vendor not in self.SUPPORTED_VENDORS:
                errors.append(
                    f"不支持的供应商: {vendor}。"
                    f"支持的供应商: {', '.join(self.SUPPORTED_VENDORS)}"
                )

            # 检查密钥类型
            if not isinstance(api_key, (str, dict)):
                errors.append(f"供应商 '{vendor}' 的密钥必须是字符串或字典类型")
                continue

            # 如果是字符串，检查是否为空
            if isinstance(api_key, str):
                if not api_key.strip():
                    errors.append(f"供应商 '{vendor}' 的密钥不能为空")
            # 如果是字典（如讯飞星火），检查必需字段
            elif isinstance(api_key, dict):
                if vendor == "xinhuo":
                    required_fields = ["appid", "api_secret", "api_key"]
                    for field in required_fields:
                        if field not in api_key:
                            errors.append(f"供应商 '{vendor}' 缺少必需字段: {field}")
                        elif not isinstance(api_key[field], str) or not api_key[field].strip():
                            errors.append(f"供应商 '{vendor}' 的 {field} 不能为空")

        return len(errors) == 0, errors

    def validate_config(self) -> Tuple[bool, List[str]]:
        """
        验证 config.json 文件

        检查项：
            1. 文件是否存在
            2. 文件是否为有效的JSON格式
            3. 是否包含至少一个供应商的配置
            4. 每个模型配置是否包含必需字段
            5. 字段值的类型是否正确

        返回:
            (is_valid, errors): 验证结果和错误信息列表
        """
        errors = []
        file_path = os.path.join(self.role_dir, "config.json")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            errors.append(f"config.json 文件不存在: {file_path}")
            return False, errors

        # 检查是否为文件
        if not os.path.isfile(file_path):
            errors.append(f"config.json 不是文件: {file_path}")
            return False, errors

        # 读取并解析JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"config.json 不是有效的JSON格式: {e}")
            return False, errors
        except Exception as e:
            errors.append(f"读取 config.json 失败: {e}")
            return False, errors

        # 检查是否为字典
        if not isinstance(data, dict):
            errors.append("config.json 必须是一个JSON对象（字典）")
            return False, errors

        # 检查是否为空
        if not data:
            errors.append("config.json 不能为空，至少需要配置一个供应商的模型")
            return False, errors

        # 检查每个供应商的配置
        for vendor, models in data.items():
            # 检查供应商名称
            if vendor not in self.SUPPORTED_VENDORS:
                errors.append(
                    f"不支持的供应商: {vendor}。"
                    f"支持的供应商: {', '.join(self.SUPPORTED_VENDORS)}"
                )

            # 检查模型配置是否为字典
            if not isinstance(models, dict):
                errors.append(f"供应商 '{vendor}' 的配置必须是字典类型")
                continue

            # 检查是否为空
            if not models:
                errors.append(f"供应商 '{vendor}' 至少需要配置一个模型")
                continue

            # 检查每个模型的配置
            for model_name, model_config in models.items():
                # 检查模型配置是否为字典
                if not isinstance(model_config, dict):
                    errors.append(f"供应商 '{vendor}' 的模型 '{model_name}' 配置必须是字典类型")
                    continue

                # 检查必需字段
                for field in self.REQUIRED_MODEL_FIELDS:
                    if field not in model_config:
                        errors.append(
                            f"供应商 '{vendor}' 的模型 '{model_name}' 缺少必需字段: {field}"
                        )

                # 检查字段类型
                if "base_url" in model_config:
                    if not isinstance(model_config["base_url"], str):
                        errors.append(
                            f"供应商 '{vendor}' 的模型 '{model_name}' 的 base_url 必须是字符串"
                        )
                    elif not model_config["base_url"].strip():
                        errors.append(
                            f"供应商 '{vendor}' 的模型 '{model_name}' 的 base_url 不能为空"
                        )

                if "model" in model_config:
                    if not isinstance(model_config["model"], str):
                        errors.append(
                            f"供应商 '{vendor}' 的模型 '{model_name}' 的 model 必须是字符串"
                        )
                    elif not model_config["model"].strip():
                        errors.append(
                            f"供应商 '{vendor}' 的模型 '{model_name}' 的 model 不能为空"
                        )

                if "max_tokens" in model_config:
                    if not isinstance(model_config["max_tokens"], int):
                        errors.append(
                            f"供应商 '{vendor}' 的模型 '{model_name}' 的 max_tokens 必须是整数"
                        )
                    elif model_config["max_tokens"] <= 0:
                        errors.append(
                            f"供应商 '{vendor}' 的模型 '{model_name}' 的 max_tokens 必须大于0"
                        )

        return len(errors) == 0, errors

    def validate_roles(self) -> Tuple[bool, List[str]]:
        """
        验证角色配置目录

        检查项：
            1. role_A 和 role_B 目录是否存在
            2. 每个角色目录下是否有 assistant.json
            3. assistant.json 格式是否正确

        返回:
            (is_valid, errors): 验证结果和错误信息列表
        """
        errors = []

        # 检查角色目录
        for role_name in ["role_A", "role_B"]:
            role_path = os.path.join(self.role_dir, role_name)

            # 检查目录是否存在
            if not os.path.exists(role_path):
                errors.append(f"角色目录不存在: {role_path}")
                continue

            if not os.path.isdir(role_path):
                errors.append(f"角色路径不是目录: {role_path}")
                continue

            # 检查 assistant.json
            assistant_path = os.path.join(role_path, "assistant.json")
            is_valid, error_list = self._validate_assistant_json(assistant_path, role_name)
            if not is_valid:
                errors.extend(error_list)

        return len(errors) == 0, errors

    def _validate_assistant_json(self, file_path: str, role_name: str) -> Tuple[bool, List[str]]:
        """
        验证 assistant.json 文件

        参数:
            file_path: assistant.json 文件路径
            role_name: 角色名称（用于错误信息）

        返回:
            (is_valid, errors): 验证结果和错误信息列表
        """
        errors = []

        # 检查文件是否存在
        if not os.path.exists(file_path):
            errors.append(f"{role_name}/assistant.json 文件不存在: {file_path}")
            return False, errors

        # 检查是否为文件
        if not os.path.isfile(file_path):
            errors.append(f"{role_name}/assistant.json 不是文件: {file_path}")
            return False, errors

        # 读取并解析JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{role_name}/assistant.json 不是有效的JSON格式: {e}")
            return False, errors
        except Exception as e:
            errors.append(f"读取 {role_name}/assistant.json 失败: {e}")
            return False, errors

        # 检查是否为字典
        if not isinstance(data, dict):
            errors.append(f"{role_name}/assistant.json 必须是一个JSON对象（字典）")
            return False, errors

        # 检查必需字段
        if "role" not in data:
            errors.append(f"{role_name}/assistant.json 缺少必需字段: role")
        elif data["role"] != "system":
            errors.append(f"{role_name}/assistant.json 的 role 必须是 'system'")

        if "content" not in data:
            errors.append(f"{role_name}/assistant.json 缺少必需字段: content")
        elif not isinstance(data["content"], str):
            errors.append(f"{role_name}/assistant.json 的 content 必须是字符串")
        elif not data["content"].strip():
            errors.append(f"{role_name}/assistant.json 的 content 不能为空")

        return len(errors) == 0, errors

    def generate_sample_configs(self, output_dir: Optional[str] = None) -> None:
        """
        生成示例配置文件

        在指定目录下生成示例配置文件，方便用户参考。

        参数:
            output_dir: 输出目录。如果为None，则使用 role_dir

        生成的文件:
            - secret_key.json.example
            - config.json.example
            - role_A/assistant.json.example
            - role_B/assistant.json.example
        """
        if output_dir is None:
            output_dir = self.role_dir

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 生成 secret_key.json.example
        secret_key_example = {
            "deepseek": "sk-your-deepseek-api-key-here",
            "qwen": "sk-your-qwen-api-key-here",
            "kimi": "sk-your-kimi-api-key-here",
            "doubao": "sk-your-doubao-api-key-here"
        }
        with open(os.path.join(output_dir, "secret_key.json.example"), 'w', encoding='utf-8') as f:
            json.dump(secret_key_example, f, ensure_ascii=False, indent=2)

        # 生成 config.json.example
        config_example = {
            "deepseek": {
                "deepseek-chat": {
                    "base_url": "https://api.deepseek.com",
                    "model": "deepseek-chat",
                    "max_tokens": 4096
                }
            },
            "qwen": {
                "qwen-turbo": {
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "model": "qwen-turbo",
                    "max_tokens": 4096
                },
                "qwen-plus": {
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "model": "qwen-plus",
                    "max_tokens": 8192
                }
            },
            "kimi": {
                "moonshot-v1-8k": {
                    "base_url": "https://api.moonshot.cn/v1",
                    "model": "moonshot-v1-8k",
                    "max_tokens": 8192
                }
            },
            "doubao": {
                "doubao-pro-4k": {
                    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                    "model": "doubao-pro-4k",
                    "max_tokens": 4096
                }
            }
        }
        with open(os.path.join(output_dir, "config.json.example"), 'w', encoding='utf-8') as f:
            json.dump(config_example, f, ensure_ascii=False, indent=2)

        # 生成 role_A/assistant.json.example
        role_a_dir = os.path.join(output_dir, "role_A")
        os.makedirs(role_a_dir, exist_ok=True)
        assistant_a_example = {
            "role": "system",
            "content": "你是一个专业的对话AI助手，负责生成友好、准确的回答。"
        }
        with open(os.path.join(role_a_dir, "assistant.json.example"), 'w', encoding='utf-8') as f:
            json.dump(assistant_a_example, f, ensure_ascii=False, indent=2)

        # 生成 role_B/assistant.json.example
        role_b_dir = os.path.join(output_dir, "role_B")
        os.makedirs(role_b_dir, exist_ok=True)
        assistant_b_example = {
            "role": "system",
            "content": "你是一个专业的知识检索AI助手，负责规划查询任务和数据检索。"
        }
        with open(os.path.join(role_b_dir, "assistant.json.example"), 'w', encoding='utf-8') as f:
            json.dump(assistant_b_example, f, ensure_ascii=False, indent=2)

        print(f"示例配置文件已生成到: {output_dir}")


def main():
    """命令行工具：验证配置文件"""
    import sys

    validator = ConfigValidator()

    print("=" * 60)
    print("AI模块配置验证工具")
    print("=" * 60)

    # 验证所有配置
    is_valid, errors = validator.validate_all()

    if is_valid:
        print("\n✓ 所有配置文件验证通过！")
        sys.exit(0)
    else:
        print(f"\n✗ 发现 {len(errors)} 个配置错误：\n")
        for i, error in enumerate(errors, 1):
            print(f"{i}. {error}")

        print("\n提示：")
        print("1. 运行以下命令生成示例配置文件：")
        print("   python -c \"from tools.ConfigValidator import ConfigValidator; ConfigValidator().generate_sample_configs()\"")
        print("2. 参考示例配置文件修改你的配置")
        print("3. 确保所有必需的字段都已填写")

        sys.exit(1)


if __name__ == "__main__":
    main()
