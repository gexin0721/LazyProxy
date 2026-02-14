# -*- coding: utf-8 -*-
import json
import time
import threading
import paho.mqtt.client as mqtt


class MQTT:
    """MQTT客户端 - 通过发布/订阅与Django服务器通信"""

    def __init__(self, broker, port=1883, client_id=None,
                 request_topic="agent/request", response_topic="agent/response",
                 callback=None, timeout=30):
        """
        参数:
            broker: MQTT Broker地址
            port: 端口，默认1883
            client_id: 客户端ID
            request_topic: 发送请求的topic
            response_topic: 接收响应的topic
            callback: 流式结束判断回调，接收dict返回bool，True表示结束
            timeout: 等待响应超时时间（秒）
        """
        self.broker = broker
        self.port = port
        self.client_id = client_id
        self.request_topic = request_topic
        self.response_topic = response_topic
        self.callback = callback
        self.timeout = timeout
        self.client = None
        self.messages = []  # 响应消息数组
        self._lock = threading.Lock()

    def _on_message(self, client, userdata, msg):
        """收到消息的回调，存入数组"""
        data = json.loads(msg.payload.decode("utf-8"))
        with self._lock:
            self.messages.append(data)

    def connect(self):
        """连接Broker并订阅响应topic"""
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_message = self._on_message
        self.client.connect(self.broker, self.port)
        self.client.subscribe(self.response_topic)
        self.client.loop_start()

    def send(self, data):
        """
        发布消息并等待响应

        参数:
            data: 要发送的字典数据
        返回:
            无callback: 单条响应dict
            有callback: 收集全部消息的列表
        """
        if self.client is None:
            raise ConnectionError("未连接，请先调用 connect()")

        self.client.publish(
            self.request_topic,
            json.dumps(data, ensure_ascii=False)
        )
        # 轮询数组等待响应
        start = time.time()
        if self.callback is None:
            while True:
                with self._lock:
                    if self.messages:
                        return self.messages.pop(0)
                if time.time() - start > self.timeout:
                    raise TimeoutError("等待MQTT响应超时")
                time.sleep(0.01)

        # 流式接收，直到callback返回True
        results = []
        while True:
            with self._lock:
                if self.messages:
                    msg = self.messages.pop(0)
                    results.append(msg)
                    if self.callback(msg):
                        return results
            if time.time() - start > self.timeout:
                raise TimeoutError("等待MQTT响应超时")
            time.sleep(0.01)

    def close(self):
        """断开MQTT连接"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.client = None
