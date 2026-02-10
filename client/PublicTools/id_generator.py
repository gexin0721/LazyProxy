# -*- coding: utf-8 -*-
"""
UUID ID 生成工具

基于 Python 标准库 uuid 模块，提供简洁的 ID 生成功能。
"""

import uuid


def generate_id(with_hyphen=True, uppercase=False):
    """
    生成一个 UUID v4 随机唯一标识符

    参数:
        with_hyphen (bool): 是否保留横杠，默认 True
            True  -> "550e8400-e29b-41d4-a716-446655440000"
            False -> "550e8400e29b41d4a716446655440000"
        uppercase (bool): 是否转为大写，默认 False

    返回:
        str: 生成的 UUID 字符串
    """
    result = str(uuid.uuid4())

    if not with_hyphen:
        result = result.replace("-", "")

    if uppercase:
        result = result.upper()

    return result
