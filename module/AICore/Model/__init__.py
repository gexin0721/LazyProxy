"""
AI 模型模块
提供各种大语言模型的接口封装
"""

# 导入已实现的模型
# from .xinhuo import Xinhuo  # 暂时封闭，等待接口统一化
from .Kiimi import Kimi  # 注意：文件名是 Kiimi.py (两个i)
from .deepseek import DeepSeek
from .doubao import Doubao
from .qwen import Qwen

# 预留其他模型的导入（待实现）
# from .claude import Claude
# from .Gemini import Gemini
# from .CharGPT import CharGPT

# 导出所有可用的类
__all__ = [
    # 'Xinhuo',  # 暂时封闭，等待接口统一化
    'Kimi',
    'DeepSeek',
    'Doubao',
    'Qwen',
    # 'CharGPT',  # 待实现
    # 'Claude',   # 待实现
    # 'Gemini',   # 待实现
]

# 版本信息
__version__ = '1.0.0'

