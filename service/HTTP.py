#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP 服务端模块
基于 FastAPI 的纯 HTTP 服务端封装，提供 REST API 能力
通过回调函数机制让外部注入业务逻辑

主要功能：
1. 路由注册：支持 GET/POST/PUT/DELETE/PATCH 等 HTTP 方法
2. 中间件支持：CORS 跨域、自定义中间件
3. 回调机制：请求前/后钩子函数
4. 错误处理：统一的异常处理器
5. 启动控制：支持后台线程启动、优雅停止

使用示例：
    server = HTTPServer(host="0.0.0.0", port=8000)

    @server.get("/hello")
    async def hello():
        return {"message": "Hello World"}

    server.start()
"""

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Callable, Optional, Any, Dict, List, Union
import uvicorn
import threading
import asyncio
import signal
import sys


class HTTPServer:
    """
    HTTP 服务端类

    封装了 FastAPI 的核心功能，提供简洁的 API 用于：
    - 注册路由（支持装饰器和方法调用两种方式）
    - 添加中间件
    - 设置请求钩子
    - 控制服务器生命周期

    属性说明：
        app: FastAPI 实例，可直接访问以使用 FastAPI 的高级功能
        host: 服务器监听的主机地址
        port: 服务器监听的端口号
        is_running: 服务器是否正在运行
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        title: str = "HTTP Server",
        description: str = "",
        version: str = "1.0.0",
        debug: bool = False
    ):
        """
        初始化 HTTP 服务器

        参数说明：
            host: 监听的主机地址，默认 127.0.0.1（仅本机访问）
                  设置为 "0.0.0.0" 可允许外部访问
            port: 监听的端口号，默认 8000
            title: API 文档标题（显示在 Swagger UI 中）
            description: API 文档描述
            version: API 版本号
            debug: 是否开启调试模式（会输出更多日志）
        """
        # 保存配置参数
        self.host = host
        self.port = port
        self.debug = debug

        # 创建 FastAPI 实例
        # FastAPI 是一个现代、快速的 Web 框架，自动生成 API 文档
        self.app = FastAPI(
            title=title,
            description=description,
            version=version,
            debug=debug
        )

        # 服务器运行状态标志
        self.is_running = False

        # uvicorn 服务器实例（用于后台运行时控制）
        self._server: Optional[uvicorn.Server] = None

        # 后台运行线程
        self._thread: Optional[threading.Thread] = None

        # 请求钩子函数存储
        # before_request: 在处理请求前调用，可用于认证、日志等
        # after_request: 在处理请求后调用，可用于修改响应、记录等
        self._before_request_hooks: List[Callable] = []
        self._after_request_hooks: List[Callable] = []

        # 注册默认的中间件来处理钩子
        self._setup_hooks_middleware()

        # 注册默认的异常处理器
        self._setup_exception_handlers()

    # ==================== 路由注册方法 ====================
    # 以下方法用于注册不同 HTTP 方法的路由
    # 可以作为装饰器使用，也可以直接调用

    def get(self, path: str, **kwargs) -> Callable:
        """
        注册 GET 请求路由

        GET 请求通常用于：获取资源、查询数据

        参数说明：
            path: 路由路径，如 "/users" 或 "/users/{user_id}"
            **kwargs: 传递给 FastAPI 的其他参数，如：
                - response_model: 响应数据模型
                - tags: API 文档分组标签
                - summary: 接口简短描述
                - description: 接口详细描述

        使用示例：
            @server.get("/users")
            async def get_users():
                return [{"id": 1, "name": "Alice"}]

            @server.get("/users/{user_id}")
            async def get_user(user_id: int):
                return {"id": user_id, "name": "Alice"}
        """
        return self.app.get(path, **kwargs)

    def post(self, path: str, **kwargs) -> Callable:
        """
        注册 POST 请求路由

        POST 请求通常用于：创建新资源、提交数据

        参数说明：
            path: 路由路径
            **kwargs: 传递给 FastAPI 的其他参数

        使用示例：
            @server.post("/users")
            async def create_user(name: str, email: str):
                return {"id": 1, "name": name, "email": email}
        """
        return self.app.post(path, **kwargs)

    def put(self, path: str, **kwargs) -> Callable:
        """
        注册 PUT 请求路由

        PUT 请求通常用于：完整更新资源（替换整个资源）

        参数说明：
            path: 路由路径
            **kwargs: 传递给 FastAPI 的其他参数

        使用示例：
            @server.put("/users/{user_id}")
            async def update_user(user_id: int, name: str, email: str):
                return {"id": user_id, "name": name, "email": email}
        """
        return self.app.put(path, **kwargs)

    def delete(self, path: str, **kwargs) -> Callable:
        """
        注册 DELETE 请求路由

        DELETE 请求通常用于：删除资源

        参数说明：
            path: 路由路径
            **kwargs: 传递给 FastAPI 的其他参数

        使用示例：
            @server.delete("/users/{user_id}")
            async def delete_user(user_id: int):
                return {"message": f"User {user_id} deleted"}
        """
        return self.app.delete(path, **kwargs)

    def patch(self, path: str, **kwargs) -> Callable:
        """
        注册 PATCH 请求路由

        PATCH 请求通常用于：部分更新资源（只更新指定字段）

        参数说明：
            path: 路由路径
            **kwargs: 传递给 FastAPI 的其他参数

        使用示例：
            @server.patch("/users/{user_id}")
            async def patch_user(user_id: int, name: str = None):
                return {"id": user_id, "name": name}
        """
        return self.app.patch(path, **kwargs)

    def route(self, path: str, methods: List[str], **kwargs) -> Callable:
        """
        注册自定义 HTTP 方法的路由

        当需要同时支持多种 HTTP 方法时使用

        参数说明：
            path: 路由路径
            methods: HTTP 方法列表，如 ["GET", "POST"]
            **kwargs: 传递给 FastAPI 的其他参数

        使用示例：
            @server.route("/resource", methods=["GET", "POST"])
            async def handle_resource(request: Request):
                if request.method == "GET":
                    return {"action": "get"}
                else:
                    return {"action": "create"}
        """
        return self.app.api_route(path, methods=methods, **kwargs)

    # ==================== 中间件配置 ====================

    def enable_cors(
        self,
        allow_origins: List[str] = ["*"],
        allow_credentials: bool = True,
        allow_methods: List[str] = ["*"],
        allow_headers: List[str] = ["*"]
    ) -> None:
        """
        启用 CORS（跨域资源共享）支持

        CORS 是什么：
            当网页从一个域名请求另一个域名的资源时，浏览器会进行跨域检查。
            如果服务器没有正确配置 CORS，浏览器会阻止这个请求。
            启用 CORS 后，服务器会在响应中添加特定的头信息，告诉浏览器允许跨域访问。

        参数说明：
            allow_origins: 允许的来源域名列表
                - ["*"] 表示允许所有域名（开发时方便，生产环境建议指定具体域名）
                - ["http://localhost:3000", "https://example.com"] 指定具体域名
            allow_credentials: 是否允许携带凭证（如 Cookie）
            allow_methods: 允许的 HTTP 方法
            allow_headers: 允许的请求头

        使用示例：
            # 允许所有跨域请求（开发环境）
            server.enable_cors()

            # 只允许特定域名（生产环境）
            server.enable_cors(
                allow_origins=["https://myapp.com"],
                allow_credentials=True
            )
        """
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=allow_credentials,
            allow_methods=allow_methods,
            allow_headers=allow_headers
        )

    def add_middleware(self, middleware_class: type, **kwargs) -> None:
        """
        添加自定义中间件

        中间件是什么：
            中间件是在请求到达路由处理函数之前/之后执行的代码。
            可以用于：日志记录、认证检查、请求修改、响应修改等。

        参数说明：
            middleware_class: 中间件类（需要符合 ASGI 中间件规范）
            **kwargs: 传递给中间件的参数

        使用示例：
            from some_package import SomeMiddleware
            server.add_middleware(SomeMiddleware, option1="value1")
        """
        self.app.add_middleware(middleware_class, **kwargs)

    # ==================== 请求钩子 ====================

    def before_request(self, func: Callable) -> Callable:
        """
        注册请求前钩子函数（装饰器）

        钩子函数会在每个请求处理之前被调用，可以用于：
        - 记录请求日志
        - 验证认证信息
        - 修改请求数据

        参数说明：
            func: 钩子函数，接收 Request 对象作为参数
                  可以是同步函数或异步函数

        使用示例：
            @server.before_request
            async def log_request(request: Request):
                print(f"收到请求: {request.method} {request.url}")

            @server.before_request
            async def check_auth(request: Request):
                token = request.headers.get("Authorization")
                if not token:
                    raise HTTPException(status_code=401, detail="未授权")
        """
        self._before_request_hooks.append(func)
        return func

    def after_request(self, func: Callable) -> Callable:
        """
        注册请求后钩子函数（装饰器）

        钩子函数会在每个请求处理之后被调用，可以用于：
        - 记录响应日志
        - 修改响应头
        - 统计请求耗时

        参数说明：
            func: 钩子函数，接收 Request 和 Response 对象作为参数
                  可以是同步函数或异步函数

        使用示例：
            @server.after_request
            async def log_response(request: Request, response: Response):
                print(f"响应状态: {response.status_code}")
        """
        self._after_request_hooks.append(func)
        return func

    def _setup_hooks_middleware(self) -> None:
        """
        设置钩子中间件（内部方法）

        这个中间件负责在请求处理前后调用注册的钩子函数
        """
        @self.app.middleware("http")
        async def hooks_middleware(request: Request, call_next: Callable) -> Response:
            # 执行所有 before_request 钩子
            for hook in self._before_request_hooks:
                # 判断是否为异步函数
                if asyncio.iscoroutinefunction(hook):
                    await hook(request)
                else:
                    hook(request)

            # 调用实际的请求处理函数
            response = await call_next(request)

            # 执行所有 after_request 钩子
            for hook in self._after_request_hooks:
                if asyncio.iscoroutinefunction(hook):
                    await hook(request, response)
                else:
                    hook(request, response)

            return response

    # ==================== 异常处理 ====================

    def _setup_exception_handlers(self) -> None:
        """
        设置默认的异常处理器（内部方法）

        统一处理各种异常，返回格式化的 JSON 错误响应
        """
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
            """
            处理 HTTP 异常

            HTTPException 是 FastAPI 提供的异常类，用于返回特定的 HTTP 错误
            """
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "success": False,
                    "error": {
                        "code": exc.status_code,
                        "message": exc.detail
                    }
                }
            )

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
            """
            处理所有未捕获的异常

            防止服务器因未处理的异常而崩溃，同时避免泄露敏感的错误信息
            """
            # 在调试模式下返回详细错误信息
            if self.debug:
                error_message = str(exc)
            else:
                error_message = "服务器内部错误"

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": 500,
                        "message": error_message
                    }
                }
            )

    def add_exception_handler(self, exc_class: type, handler: Callable) -> None:
        """
        添加自定义异常处理器

        参数说明：
            exc_class: 要处理的异常类
            handler: 处理函数，接收 (request, exception) 参数

        使用示例：
            class CustomError(Exception):
                pass

            async def handle_custom_error(request, exc):
                return JSONResponse(
                    status_code=400,
                    content={"error": str(exc)}
                )

            server.add_exception_handler(CustomError, handle_custom_error)
        """
        self.app.add_exception_handler(exc_class, handler)

    # ==================== 服务器控制 ====================

    def start(self, block: bool = True) -> None:
        """
        启动 HTTP 服务器

        参数说明：
            block: 是否阻塞当前线程
                - True（默认）：阻塞运行，直到服务器停止
                - False：在后台线程运行，不阻塞当前线程

        使用示例：
            # 阻塞运行（通常用于主程序）
            server.start()

            # 后台运行（用于需要同时执行其他任务的场景）
            server.start(block=False)
            # ... 执行其他任务 ...
            server.stop()
        """
        if self.is_running:
            print("服务器已经在运行中")
            return

        self.is_running = True

        if block:
            # 阻塞模式：直接在当前线程运行
            self._run_server()
        else:
            # 非阻塞模式：在后台线程运行
            self._thread = threading.Thread(target=self._run_server, daemon=True)
            self._thread.start()
            print(f"HTTP 服务器已在后台启动: http://{self.host}:{self.port}")

    def _run_server(self) -> None:
        """
        运行服务器（内部方法）

        使用 uvicorn 作为 ASGI 服务器来运行 FastAPI 应用
        """
        # 创建 uvicorn 配置
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="debug" if self.debug else "info"
        )

        # 创建服务器实例
        self._server = uvicorn.Server(config)

        # 运行服务器
        self._server.run()

        # 服务器停止后更新状态
        self.is_running = False

    def stop(self) -> None:
        """
        停止 HTTP 服务器

        优雅地关闭服务器，等待当前请求处理完成

        使用示例：
            server.start(block=False)
            # ... 一段时间后 ...
            server.stop()
        """
        if not self.is_running:
            print("服务器未在运行")
            return

        if self._server:
            # 设置服务器应该退出的标志
            self._server.should_exit = True
            print("正在停止 HTTP 服务器...")

    # ==================== 实用方法 ====================

    def get_app(self) -> FastAPI:
        """
        获取 FastAPI 应用实例

        当需要使用 FastAPI 的高级功能时，可以直接获取实例进行操作

        返回值：
            FastAPI 实例

        使用示例：
            app = server.get_app()
            # 使用 FastAPI 的原生功能
            app.include_router(some_router)
        """
        return self.app

    def include_router(self, router, **kwargs) -> None:
        """
        包含路由器

        用于模块化组织路由，将不同功能的路由分开管理

        参数说明：
            router: FastAPI 的 APIRouter 实例
            **kwargs: 传递给 include_router 的参数，如：
                - prefix: 路由前缀
                - tags: API 文档标签

        使用示例：
            from fastapi import APIRouter

            user_router = APIRouter()

            @user_router.get("/")
            async def list_users():
                return []

            server.include_router(user_router, prefix="/users", tags=["用户管理"])
        """
        self.app.include_router(router, **kwargs)


# ==================== 测试代码 ====================
# 当直接运行此文件时执行测试
if __name__ == "__main__":
    # 创建服务器实例
    server = HTTPServer(
        host="127.0.0.1",
        port=8000,
        title="测试 HTTP 服务器",
        description="这是一个测试服务器",
        debug=True
    )

    # 启用 CORS
    server.enable_cors()

    # 注册请求前钩子
    @server.before_request
    async def log_request(request: Request):
        print(f"[请求] {request.method} {request.url}")

    # 注册请求后钩子
    @server.after_request
    async def log_response(request: Request, response: Response):
        print(f"[响应] 状态码: {response.status_code}")

    # 注册路由
    @server.get("/")
    async def root():
        """根路径"""
        return {"message": "欢迎使用 HTTP 服务器"}

    @server.get("/hello/{name}")
    async def hello(name: str):
        """问候接口"""
        return {"message": f"你好, {name}!"}

    @server.post("/echo")
    async def echo(data: dict):
        """回显接口"""
        return {"received": data}

    # 启动服务器
    print("启动测试服务器...")
    print("访问 http://127.0.0.1:8000/docs 查看 API 文档")
    server.start()
