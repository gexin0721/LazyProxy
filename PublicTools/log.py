import os
import sys
from loguru import logger as _logger


# 移除默认的 handler
_logger.remove()

# 获取日志目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
record_dir = os.path.join(current_dir, '../Data/record')

# 创建日志目录
if not os.path.exists(record_dir):
    os.makedirs(record_dir)

# 配置控制台输出
_logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="DEBUG",
    colorize=True
)

# 配置文件输出
_logger.add(
    os.path.join(record_dir, "{time:YYYY-MM-DD}.log"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    level="DEBUG",
    rotation="00:00",  # 每天午夜轮转
    retention="30 days",  # 保留30天
    encoding="utf-8",
    enqueue=True,  # 异步写入，线程安全
    compression="zip"  # 旧日志自动压缩
)

# 导出 logger 实例
logger = _logger

# 使用示例
# from tools import logger
# logger.info("程序启动")
# logger.error("发生错误: xxxx")
