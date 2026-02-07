import math
from typing import Dict, Any

class mathematics:
    """
    数学工具类
    """
    def add(self, a:int, b:int) -> Dict[str, Any]:
        """
        加法
        :param a: 加数
        :param b: 加数
        :return: 和
        """
        result = {
            "task_type": "add",
            "message": a + b,
        }
        return result

    def subtract(self, a:int, b:int) -> Dict[str, Any]:
        """
        减法
        :param a: 被减数
        :param b: 减数
        :return: 差
        """
        result = {
            "task_type": "subtract",
            "message": a - b,
        }
        return result
    def multiply(self, a:int, b:int) -> Dict[str, Any]:
        """
        乘法
        :param a: 乘数
        :param b: 乘数
        :return: 积
        """
        result = {
            "task_type": "multiply",
            "message": a * b,
        }
        return result

    def divide(self, a:int, b:int) -> Dict[str, Any]:
        """
        除法
        :param a: 被除数
        :param b: 除数
        :return: 商
        """
        result = {
            "task_type": "divide",
            "message": a / b,
        }
        return result
        
    def power(self, a:int, b:int) -> Dict[str, Any]:
        """
        幂运算
        :param a: 底数
        :param b: 指数
        :return: 幂
        """
        result = {
            "task_type": "power",
            "message": a ** b,
        }
        return result

    def sqrt(self, a:int) -> float:
        """
        平方根
        :param a: 被开方数
        :return: 平方根
        """
        result = {
            "task_type": "sqrt",
            "message": math.sqrt(a),
        }
        return result