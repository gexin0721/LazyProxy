#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP 服务端模块
基于 FastAPI 的纯 HTTP 服务端封装，提供 REST API 能力
通过回调函数机制让外部注入业务逻辑
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import Response
from fastapi.responses import RedirectResponse
from fastapi.responses import FileResponse
import uvicorn

class HTTPServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        """
        初始化 HTTP 服务器
        :param host: 监听地址
        :param port: 监听端口
        """
        self.host = host
        self.port = port
        self.app = FastAPI()

    # ==================== 路由管理 ====================
    def add_route(self, path: str, method: str, handler):
        """
        添加路由
        :param path: 路由路径
        :param method: HTTP 方法 (GET, POST, PUT, DELETE 等)
        :param handler: 处理函数
        """
        method = method.upper()
        if method == "GET":
            self.app.get(path)(handler)
        elif method == "POST":
            self.app.post(path)(handler)
        elif method == "PUT":
            self.app.put(path)(handler)
        elif method == "DELETE":
            self.app.delete(path)(handler)
        elif method == "PATCH":
            self.app.patch(path)(handler)

    # ==================== 中间件管理 ====================
    def add_middleware(self, middleware_class, **kwargs):
        """
        添加中间件
        :param middleware_class: 中间件类
        :param kwargs: 中间件参数
        """
        self.app.add_middleware(middleware_class, **kwargs)

    def enable_cors(self, origins: list = None):
        """
        启用 CORS 跨域支持
        :param origins: 允许的源列表，默认允许所有
        """
        if origins is None:
            origins = ["*"]
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # ==================== 静态文件 ====================
    def set_static(self, path: str, directory: str):
        """
        设置静态文件目录
        :param path: URL 路径
        :param directory: 本地目录路径
        """
        self.app.mount(path, StaticFiles(directory=directory), name="static")

    # ==================== 启动服务器 ====================
    def start(self):
        """启动 HTTP 服务器"""
        uvicorn.run(self.app, host=self.host, port=self.port)
