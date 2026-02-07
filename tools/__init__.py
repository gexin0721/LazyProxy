# -*- coding: utf-8 -*-
"""
工具模块

提供AI模块所需的各种工具类和函数。

主要工具：
    - HistoryManager: 对话历史管理
    - JSONProcessor: JSON文件处理
    - FileEditor: 文件编辑操作
    - DatabaseEditor: 数据库操作
    - DataInquire: 数据查询接口
    - AllEventsHandler: 文件监控
    - ExcelProcessor: Excel文件处理
    - ConfigValidator: 配置文件验证
    - logger: 日志系统
"""

from .AllEventsHandler import AllEventsHandler
from .log import logger

# 导出所有可用的符号
__all__ = [
    'AllEventsHandler',
    'logger',
]

# 版本信息
__version__ = '1.0.0'

