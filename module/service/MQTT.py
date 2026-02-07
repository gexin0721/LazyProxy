#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT 服务端模块
基于 paho-mqtt 的 MQTT 客户端封装，提供消息订阅接收能力
通过回调函数机制让外部注入业务逻辑
"""
import paho.mqtt.client as mqtt

class MQTTServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 1883, client_id: str = None):
        """
        初始化 MQTT 服务
        :param host: Broker 地址
        :param port: Broker 端口
        :param client_id: 客户端 ID
        """
        self.host = host
        self.port = port
        self.client = mqtt.Client(client_id=client_id)

        # 绑定内部回调
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        # 外部回调函数
        self._on_connect_callback = None
        self._on_message_callback = None
        self._on_disconnect_callback = None

    # ==================== 内部回调 ====================
    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if self._on_connect_callback:
            self._on_connect_callback(client, userdata, flags, rc)

    def _on_message(self, client, userdata, msg):
        """消息回调"""
        if self._on_message_callback:
            self._on_message_callback(client, userdata, msg)

    def _on_disconnect(self, client, userdata, rc):
        """断开回调"""
        if self._on_disconnect_callback:
            self._on_disconnect_callback(client, userdata, rc)

    # ==================== 设置回调 ====================
    def set_on_connect(self, callback):
        """
        设置连接回调
        :param callback: 回调函数 (client, userdata, flags, rc)
        """
        self._on_connect_callback = callback

    def set_on_message(self, callback):
        """
        设置消息接收回调
        :param callback: 回调函数 (client, userdata, msg)
        """
        self._on_message_callback = callback

    def set_on_disconnect(self, callback):
        """
        设置断开回调
        :param callback: 回调函数 (client, userdata, rc)
        """
        self._on_disconnect_callback = callback

    # ==================== 连接管理 ====================
    def connect(self, username: str = None, password: str = None):
        """
        连接到 Broker
        :param username: 用户名
        :param password: 密码
        """
        if username and password:
            self.client.username_pw_set(username, password)
        self.client.connect(self.host, self.port)

    def subscribe(self, topic: str, qos: int = 0):
        """
        订阅主题
        :param topic: 主题名称
        :param qos: 服务质量等级
        """
        self.client.subscribe(topic, qos)

    # ==================== 启动服务 ====================
    def start(self):
        """启动 MQTT 消息循环"""
        self.client.loop_forever()
