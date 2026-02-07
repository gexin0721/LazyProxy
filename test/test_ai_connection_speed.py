"""
AI模型连接速度测试程序

该程序用于测试不同AI模型的连接时间和响应速度。

测试指标:
    1. 连接建立时间: 从调用connect()到模型实例化完成的时间
    2. 首次响应时间: 发送测试消息到收到第一个token的时间
    3. 完整响应时间: 发送测试消息到收到完整响应的时间

使用方法:
    python test_ai_connection_speed.py
"""

import sys
import os
import time
import json
from typing import Dict, List, Tuple

# 添加父目录到系统路径,以便导入AICore模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from module.AICore.AIManager import AIFactory


class AIConnectionSpeedTester:
    """
    AI连接速度测试器

    该类负责测试不同AI模型的连接速度和响应时间。

    属性:
        test_message: 用于测试的消息内容
        test_rounds: 每个模型的测试轮数
        timeout: 超时时间(秒)
        results: 测试结果字典
    """

    def __init__(self, test_message: str = "你好", test_rounds: int = 3, timeout: int = 30):
        """
        初始化测试器

        参数:
            test_message: 测试消息内容,默认为"你好"
            test_rounds: 每个模型测试轮数,默认为3次
            timeout: 超时时间(秒),默认为30秒
        """
        self.test_message = test_message
        self.test_rounds = test_rounds
        self.timeout = timeout
        self.results = {}
        self.factory = AIFactory()

    def load_config(self) -> Dict:
        """
        加载配置文件,获取所有可用的AI模型配置

        返回:
            配置字典,包含所有供应商和模型信息
        """
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(script_dir, "module", "AICore", "role", "config.json")

        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"配置文件未找到: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        return config

    def test_connection_time(self, vendor: str, model_name: str) -> float:
        """
        测试AI模型的连接时间

        参数:
            vendor: 供应商名称
            model_name: 模型名称

        返回:
            连接时间(毫秒)
        """
        start_time = time.time()

        try:
            # 连接模型(使用对话模型进行测试)
            self.factory.connect(
                dialogue_vendor=vendor,
                dialogue_model_name=model_name,
                knowledge_vendor=vendor,
                knowledge_model_name=model_name
            )

            end_time = time.time()
            connection_time = (end_time - start_time) * 1000  # 转换为毫秒

            return connection_time

        except Exception as e:
            print(f"连接失败: {vendor}/{model_name} - {str(e)}")
            return -1

    def test_first_response_time(self) -> Tuple[float, float]:
        """
        测试首次响应时间和完整响应时间

        返回:
            元组 (首次响应时间(毫秒), 完整响应时间(毫秒))
        """
        start_time = time.time()
        first_token_time = None

        try:
            # 发送测试消息并接收流式响应
            for chunk in self.factory.dialogue_callback(self.test_message):
                if first_token_time is None:
                    # 记录首次收到token的时间
                    first_token_time = time.time()

            end_time = time.time()

            # 计算时间(毫秒)
            first_response = (first_token_time - start_time) * 1000 if first_token_time else -1
            total_response = (end_time - start_time) * 1000

            return first_response, total_response

        except Exception as e:
            print(f"响应测试失败: {str(e)}")
            return -1, -1

    def test_model(self, vendor: str, model_name: str) -> Dict:
        """
        测试单个AI模型的性能

        参数:
            vendor: 供应商名称
            model_name: 模型名称

        返回:
            测试结果字典,包含连接时间、首次响应时间、完整响应时间
        """
        print(f"\n正在测试: {vendor}/{model_name}")

        connection_times = []
        first_response_times = []
        total_response_times = []

        # 进行多轮测试
        for round_num in range(self.test_rounds):
            print(f"  第 {round_num + 1}/{self.test_rounds} 轮测试...")

            # 测试连接时间
            connection_time = self.test_connection_time(vendor, model_name)
            if connection_time < 0:
                continue

            connection_times.append(connection_time)

            # 测试响应时间
            first_response, total_response = self.test_first_response_time()
            if first_response < 0 or total_response < 0:
                continue

            first_response_times.append(first_response)
            total_response_times.append(total_response)

            # 断开连接,准备下一轮测试
            self.factory.disconnect()

            # 短暂延迟,避免请求过快
            time.sleep(1)

        # 计算平均值 - 区分三种情况
        if connection_times and first_response_times and total_response_times:
            # 情况1: 完全成功
            avg_connection = sum(connection_times) / len(connection_times)
            avg_first_response = sum(first_response_times) / len(first_response_times)
            avg_total_response = sum(total_response_times) / len(total_response_times)

            return {
                "vendor": vendor,
                "model": model_name,
                "connection_time": round(avg_connection, 2),
                "first_response_time": round(avg_first_response, 2),
                "total_response_time": round(avg_total_response, 2),
                "success": True,
                "status": "完全成功"
            }
        elif connection_times:
            # 情况2: 连接成功但响应失败
            avg_connection = sum(connection_times) / len(connection_times)
            return {
                "vendor": vendor,
                "model": model_name,
                "connection_time": round(avg_connection, 2),
                "first_response_time": -1,
                "total_response_time": -1,
                "success": False,
                "status": "连接成功但响应失败"
            }
        else:
            # 情况3: 完全失败
            return {
                "vendor": vendor,
                "model": model_name,
                "connection_time": -1,
                "first_response_time": -1,
                "total_response_time": -1,
                "success": False,
                "status": "连接失败"
            }

    def run_all_tests(self):
        """
        运行所有AI模型的测试
        """
        print("=" * 80)
        print("AI模型连接速度测试")
        print("=" * 80)
        print(f"测试消息: {self.test_message}")
        print(f"测试轮数: {self.test_rounds}")
        print(f"超时时间: {self.timeout}秒")
        print("=" * 80)

        # 加载配置
        try:
            config = self.load_config()
        except Exception as e:
            print(f"加载配置失败: {str(e)}")
            return

        # 遍历所有供应商和模型
        for vendor, models in config.items():
            if not isinstance(models, dict):
                continue

            for model_name in models.keys():
                # 测试模型
                result = self.test_model(vendor, model_name)

                # 保存结果
                key = f"{vendor}/{model_name}"
                self.results[key] = result

        # 输出测试结果
        self.print_results()

    def print_results(self):
        """
        打印测试结果表格
        """
        print("\n" + "=" * 100)
        print("测试结果报告")
        print("=" * 100)
        print(f"{'模型名称':<35} {'连接时间(ms)':<15} {'首次响应(ms)':<15} {'完整响应(ms)':<15} {'状态':<20}")
        print("-" * 100)

        for key, result in self.results.items():
            status = result.get("status", "未知")
            if result["success"]:
                print(f"{key:<35} {result['connection_time']:<15} "
                      f"{result['first_response_time']:<15} {result['total_response_time']:<15} {status:<20}")
            else:
                conn_time = result['connection_time'] if result['connection_time'] > 0 else '失败'
                print(f"{key:<35} {conn_time:<15} {'失败':<15} {'失败':<15} {status:<20}")

        print("=" * 100)


def main():
    """
    主函数
    """
    # 创建测试器实例
    tester = AIConnectionSpeedTester(
        test_message="你好",
        test_rounds=3,
        timeout=30
    )

    # 运行所有测试
    tester.run_all_tests()


if __name__ == "__main__":
    main()
