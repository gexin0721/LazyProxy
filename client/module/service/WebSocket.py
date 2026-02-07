#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket 服务端模块
基于 websockets 的 WebSocket 服务端封装，提供实时双向通信能力
通过回调函数机制让外部注入业务逻辑
"""
import asyncio
import websockets

class WebSocketServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        """
        初始化 WebSocket 服务器
        :param host: 监听地址
        :param port: 监听端口
        """
        self.host = host
        self.port = port
        self.clients = set()

        # 外部回调函数
        self._on_connect_callback = None
        self._on_message_callback = None
        self._on_disconnect_callback = None

    # ==================== 设置回调 ====================
    def set_on_connect(self, callback):
        """
        设置客户端连接回调
        :param callback: 回调函数 (websocket)
        """
        self._on_connect_callback = callback

    def set_on_message(self, callback):
        """
        设置消息接收回调
        :param callback: 回调函数 (websocket, message)
        """
        self._on_message_callback = callback

    def set_on_disconnect(self, callback):
        """
        设置客户端断开回调
        :param callback: 回调函数 (websocket)
        """
        self._on_disconnect_callback = callback

    # ==================== 连接处理 ====================
    async def _handler(self, websocket):
        """处理客户端连接"""
        self.clients.add(websocket)
        try:
            if self._on_connect_callback:
                await self._on_connect_callback(websocket)
            async for message in websocket:
                if self._on_message_callback:
                    await self._on_message_callback(websocket, message)
        finally:
            self.clients.discard(websocket)
            if self._on_disconnect_callback:
                await self._on_disconnect_callback(websocket)

    # ==================== 启动服务器 ====================
    def start(self):
        """启动 WebSocket 服务器"""
        async def _run():
            async with websockets.serve(self._handler, self.host, self.port):
                await asyncio.Future()
        asyncio.run(_run())
