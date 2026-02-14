# -*- coding: utf-8 -*-
import httpx
from typing import Callable
import json

class HTTP:
    """HTTP客户端 - 向Django服务器发送请求并接收响应"""

    def __init__(self, ended: Callable[[dict], bool],
                        base_url:str ,
                        endpoint:str,
                        timeout:int=30):
        """
        参数:
            ended: 判断流式输出是否结束的回调函数
            base_url: 服务器地址，如 "http://127.0.0.1:8000"
            endpoint：发送地址
            timeout: 请求超时时间（秒）
        """
        if  base_url == None: # 服务器地址必须是存在的
            raise TypeError("服务器地址不能为空")
        if timeout <= 0: # 超时时间，必须是非零的正整数
            raise ValueError("超时时间必须是非零的正整数")

        self.base_url = base_url
        self.timeout = timeout
        self.endpoint = endpoint
        self.ended = ended

        self.client = None

    def connect(self):
        """创建HTTP客户端"""
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={"Content-Type": "application/json"}
        )

    def send(self, data:dict):
        """
        发送数据并等待响应

        参数:
            data: 要发送的字典数据
            endpoint: 请求路径，默认 "/"
        返回:
            服务器响应的字典数据
        """
        if self.client is None:
            raise ConnectionError("未连接，请先调用 connect()")

        try:
            with self.client.stream("POST", self.endpoint, json=data) as e:
                e.raise_for_status()
                for line in e.iter_lines():
                    if not line:
                        continue
                    msg = json.loads(line)
                    yield msg
                    if self.ended(msg):
                        break
        except httpx.ConnectError:
            raise ConnectionError("无法连接到服务器: " + self.base_url)
        except httpx.TimeoutException:
            raise TimeoutError("请求超时，超时时间: " + str(self.timeout) + "秒")

    def close(self):
        """关闭HTTP客户端"""
        if self.client:
            self.client.close()
            self.client = None
