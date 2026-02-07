"""
网络服务模块
提供 HTTP 和 WebSocket 客户端封装
"""




# 导入 OPEN_AI 客户端
from .OPEN_AI import OPEN_AI
# 导出所有可用的类
__all__ = [
    'OPEN_AI',
]

# 版本信息
__version__ = '1.0.0'

