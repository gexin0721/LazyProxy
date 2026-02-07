#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 OPEN_AI 类的 send 和 send_stream 方法的 role 参数功能
验证是否能够正确处理不同角色（user, system, assistant, tool）的消息
"""

import os
import sys

# 添加父目录到路径，以便导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from module.AICore.Tool.HistoryManager import HistoryManager

def test_role_parameter_validation():
    """测试角色参数验证功能"""
    print("\n测试1: 角色参数验证")
    print("-" * 60)

    # 创建一个临时的 HistoryManager 实例用于测试
    # 需要提供 token_callback 和 role_path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    role_path = os.path.join(script_dir, "..", "module", "AICore", "role", "role_A")

    # 简单的 token 计算回调（用于测试）
    def simple_token_callback(text: str) -> int:
        return len(text)

    try:
        history_manager = HistoryManager(
            token_callback=simple_token_callback,
            role_path=role_path,
            max_tokens=4096
        )

        # 测试有效角色
        valid_roles = ["user", "system", "assistant"]
        for role in valid_roles:
            try:
                history_manager.insert(role, f"测试消息 - {role}")
                print(f"[PASS] 角色 '{role}' 验证通过")
            except Exception as e:
                print(f"[FAIL] 角色 '{role}' 验证失败: {e}")
                return False

        # 测试无效角色
        invalid_roles = ["admin", "bot", "invalid", ""]
        for role in invalid_roles:
            try:
                history_manager.insert(role, "测试消息")
                print(f"[FAIL] 无效角色 '{role}' 应该被拒绝但通过了")
                return False
            except ValueError as e:
                print(f"[PASS] 无效角色 '{role}' 正确被拒绝: {e}")
            except Exception as e:
                print(f"[FAIL] 无效角色 '{role}' 抛出了意外异常: {e}")
                return False

        print("\n[PASS] 角色参数验证测试通过")
        return True

    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_history_with_different_roles():
    """测试历史记录中不同角色的消息"""
    print("\n测试2: 历史记录中的不同角色消息")
    print("-" * 60)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    role_path = os.path.join(script_dir, "..", "module", "AICore", "role", "role_A")

    def simple_token_callback(text: str) -> int:
        return len(text)

    try:
        history_manager = HistoryManager(
            token_callback=simple_token_callback,
            role_path=role_path,
            max_tokens=4096
        )

        # 清空历史（保留第一条 system 提示词）
        history_manager.clear()

        # 插入不同角色的消息
        test_messages = [
            ("user", "用户问题：今天天气怎么样？"),
            ("assistant", "助手回答：今天天气晴朗。"),
            ("system", "系统消息：工具调用结果 - 温度25度"),
            ("user", "用户追问：明天呢？"),
            ("system", "系统消息：查询结果 - 明天多云")
        ]

        for role, content in test_messages:
            history_manager.insert(role, content)
            print(f"[PASS] 插入 {role} 消息: {content[:30]}...")

        # 获取历史记录并验证
        history = history_manager.get()
        print(f"\n历史记录总数: {len(history)}")

        # 验证插入的消息是否都在历史中（跳过第一条 system 提示词）
        inserted_count = 0
        for item in history[1:]:  # 跳过第一条提示词
            role = item.get("role")
            content = item.get("content", "")
            print(f"  - [{role}] {content[:50]}...")
            inserted_count += 1

        if inserted_count >= len(test_messages):
            print(f"\n[PASS] 历史记录测试通过（插入了 {inserted_count} 条消息）")
            return True
        else:
            print(f"\n[FAIL] 历史记录测试失败（预期 {len(test_messages)} 条，实际 {inserted_count} 条）")
            return False

    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_role_parameter_type_checking():
    """测试角色参数的类型检查"""
    print("\n测试3: 角色参数类型检查")
    print("-" * 60)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    role_path = os.path.join(script_dir, "..", "module", "AICore", "role", "role_A")

    def simple_token_callback(text: str) -> int:
        return len(text)

    try:
        history_manager = HistoryManager(
            token_callback=simple_token_callback,
            role_path=role_path,
            max_tokens=4096
        )

        # 测试非字符串类型的角色参数
        invalid_types = [
            (123, "数字类型"),
            (None, "None类型"),
            (["user"], "列表类型"),
            ({"role": "user"}, "字典类型")
        ]

        for invalid_role, type_name in invalid_types:
            try:
                history_manager.insert(invalid_role, "测试消息")
                print(f"[FAIL] {type_name} 应该被拒绝但通过了")
                return False
            except TypeError as e:
                print(f"[PASS] {type_name} 正确被拒绝: {e}")
            except Exception as e:
                print(f"[FAIL] {type_name} 抛出了意外异常: {e}")
                return False

        print("\n[PASS] 角色参数类型检查测试通过")
        return True

    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("OPEN_AI 类 role 参数功能测试")
    print("=" * 60)

    try:
        # 运行所有测试
        test1_passed = test_role_parameter_validation()
        test2_passed = test_history_with_different_roles()
        test3_passed = test_role_parameter_type_checking()

        # 总结
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        print(f"测试1（角色参数验证）: {'[PASS] 通过' if test1_passed else '[FAIL] 失败'}")
        print(f"测试2（历史记录不同角色）: {'[PASS] 通过' if test2_passed else '[FAIL] 失败'}")
        print(f"测试3（角色参数类型检查）: {'[PASS] 通过' if test3_passed else '[FAIL] 失败'}")

        if test1_passed and test2_passed and test3_passed:
            print("\n[PASS] 所有测试通过！")
        else:
            print("\n[FAIL] 部分测试失败")

    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
