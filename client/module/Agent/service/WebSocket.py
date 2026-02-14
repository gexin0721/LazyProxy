# -*- coding: utf-8 -*-
import json
from websockets.sync.client import connect


class WebSocket:
    """WebSocket客户端 - 与Django服务器建立长连接"""

    def __init__(self, url, callback=None):
        """
        参数:
            url: WebSocket地址，如 "ws://127.0.0.1:8000/ws"
            callback: 流式结束判断回调，接收dict返回bool，True表示结束
        """
        self.url = url
        self.ws = None
        self.callback = callback

    def connect(self):
        """建立WebSocket连接"""
        self.ws = connect(self.url)

    def send(self, data):
        """
        发送数据并等待响应

        参数:
            data: 要发送的字典数据
        返回:
            无callback: 单条响应dict
            有callback: 收集全部消息的列表
        """
        if self.ws is None:
            raise ConnectionError("未连接，请先调用 connect()")

        self.ws.send(json.dumps(data, ensure_ascii=False))

        if self.callback is None:
            response = self.ws.recv()
            return json.loads(response)

        # 流式接收，直到callback返回True
        results = []
        while True:
            response = json.loads(self.ws.recv())
            results.append(response)
            if self.callback(response):
                return results

    def close(self):
        """断开WebSocket连接"""
        if self.ws:
            self.ws.close()
            self.ws = None
