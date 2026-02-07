# """
# 星火大模型API封装类

# 使用示例:

# 使用字典数据初始化:
#     config = {
#         "key": "your_api_key",
#         "params": {
#             "appid": "your_appid",
#             "api_secret": "your_api_secret",
#             "domain": "generalv3.5",
#             "Spark_url": "wss://spark-api.xf-yun.com/v3.5/chat",
#             "temperature": 0.8,  # 可选
#             "max_tokens": 2048,  # 可选
#             "top_k": 5,  # 可选
#             "auditing": "default",  # 可选
#             "uid": "1234",  # 可选
#             "history": "chat_history.json"  # 可选
#         }
#     }
#     xinhuo = Xinhuo(config)
#     answer = xinhuo.ask("你好")
#     print(answer)

# 常用方法:
#     - ask(question, timeout=30.0): 提问并获取回答
#     - clear_history(): 清除对话历史
#     - get_history(): 获取对话历史列表

# 注意:
#     - ask()方法会自动处理WebSocket连接的建立和关闭
#     - 每次调用ask()都会重新建立连接（这是星火API的特性）
#     - 对话历史会自动保存到指定的历史文件（默认为chat_history.json）
# """

# import json
# import requests
# import websocket
# import threading
# import time
# import base64
# import datetime
# import hashlib
# import hmac
# import ssl
# import os
# import _thread as thread
# from typing import Callable, Optional, Dict, Any, Union, overload
# from urllib.parse import urlparse, urlencode
# from wsgiref.handlers import format_date_time

# # 最大 token
# MAX_TOKENS = 8096

# class Xinhuo:

#     def __init__(self, message: dict):
#         """
#         初始化星火大模型
        
#         参数:
#             message: 包含配置信息的字典，格式为:
#             {
#                 "key": "api_key",
#                 "params": {
#                     "appid": "应用ID",
#                     "api_secret": "API密钥secret",
#                     "domain": "模型版本",
#                     "Spark_url": "API服务地址",
#                     "temperature": 0.8,  # 可选
#                     "max_tokens": 2048,  # 可选
#                     "top_k": 5,  # 可选
#                     "auditing": "default",  # 可选
#                     "uid": "1234",  # 可选
#                     "history": "历史文件路径"  # 可选
#                 }
#             }
#         """
#         params = message.get("params", {})
        
#         # 星火API必需参数
#         self.appid = params.get("appid", "")
#         self.api_secret = params.get("api_secret", "")
#         self.api_key = message.get("key", "")
#         self.domain = params.get("domain", "")
#         self.Spark_url = params.get("Spark_url", "")
        
#         # 可选参数
#         self.temperature = params.get("temperature", 0.8)
#         self.max_tokens = params.get("max_tokens", 2048)
#         self.top_k = params.get("top_k", 5)
#         self.auditing = params.get("auditing", "default")
#         self.uid = params.get("uid", "1234")
        
#         # 对话历史文件路径
#         if params.get("history"):
#             self.history = params.get("history")
#         else:
#             # 默认在当前目录创建历史文件
#             self.history = os.path.join(os.getcwd(), "chat_history.json")
        
#         # 解析URL获取主机名和路径
#         if self.Spark_url:
#             parsed_url = urlparse(self.Spark_url)
#             self.host = parsed_url.netloc
#             self.path = parsed_url.path
#         else:
#             self.host = ""
#             self.path = ""
        
#         # 实例变量（运行时状态）
#         self.full_answer = ""
#         self.answer_event = threading.Event()
#         self.error_msg = None

#     #  ============ 生成请求参数 ============
#     def gen_params(self, question):

#         # 读取对话历史
#         try:
#             with open(self.history, "r", encoding="utf-8") as f:
#                 text_list = json.load(f)  # 读取为列表
#         except (FileNotFoundError, json.JSONDecodeError):
#             text_list = []  # 如果文件不存在或格式错误，初始化为空列表
        
#         # 添加新的用户问题
#         text_list.append({"role": "user", "content": question})
        
#         # 保存更新后的对话历史
#         with open(self.history, "w", encoding="utf-8") as f:
#             json.dump(text_list, f, ensure_ascii=False, indent=2)
        

#         # 生成请求参数
#         return {
#             "header": {"app_id": self.appid, "uid": self.uid},  # 请求头，包含应用ID和用户ID
#             "parameter": {
#                 "chat": {
#                     "domain": self.domain,  # 模型版本/领域
#                     "temperature": self.temperature,  # 温度参数，控制生成文本的随机性，越大越随机
#                     "max_tokens": self.max_tokens,  # 生成文本的最大长度
#                     "top_k": self.top_k,  # 从k个候选中随机选择一个
#                     "auditing": self.auditing  # 审核设置
#                 }
#             },
#             "payload": {"message": {"text": text_list}}  # 消息内容，包含对话历史
#         }

#     #  ============ 创建带认证信息的WebSocket URL ============
#     def create_url(self):
#         """
#         创建带认证信息的WebSocket URL
        
#         返回:
#             str: 完整的带认证参数的WebSocket URL
#         """
#         # 生成RFC1123格式的时间戳
#         now = datetime.datetime.now()
#         date = format_date_time(time.mktime(now.timetuple()))
        
#         # 构建签名原文
#         signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.path} HTTP/1.1"
        
#         # 使用HMAC-SHA256算法结合APISecret对签名原文进行加密
#         signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
#         signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')
        
#         # 构建授权原文并进行base64编码
#         authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
#         authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        
#         # 将认证信息添加到URL参数中
#         v = {"authorization": authorization, "date": date, "host": self.host}
#         return self.Spark_url + '?' + urlencode(v)

#     #  ============ 接受数据回调函数 ============
#     def on_message(self, ws, message):
#         """
#         处理从WebSocket接收到的消息
        
#         参数:
#             ws: WebSocket实例
#             message: 接收到的消息内容
#         """

#         # 解析JSON消息
#         data = json.loads(message)
#         code = data['header']['code']

#         # 如果返回错误码，关闭连接
#         if code != 0:
#             print(f'请求错误: {code}, {data}')
#             ws.close()
#         else:
#             # 获取会话ID (sid)
#             global sid
#             sid = data["header"]["sid"]
            
#             # 从返回数据中提取内容
#             choices = data["payload"]["choices"]
#             status = choices["status"]  # 状态：0-开始，1-继续，2-结束
#             content = choices["text"][0]["content"]  # 实际内容
            
#             # 拼接收到的每一部分内容（大模型回答可能分多次返回）
#             self.full_answer += content
            
#             # 如果status为2，表示回答完成，发布到ROS话题并关闭连接
#             if status == 2:
#                 # 把完整回答写入历史文件
#                 try:
#                     # 读取现有历史
#                     with open(self.history, "r", encoding="utf-8") as f:
#                         text_list = json.load(f)
#                 except (FileNotFoundError, json.JSONDecodeError):
#                     text_list = []
#                 # 存储AI回答
#                 text_list.append({"role": "assistant", "content": self.full_answer})
#                 with open(self.history, "w", encoding="utf-8") as f:
#                     json.dump(text_list, f, ensure_ascii=False, indent=2)
                
#                 # 设置事件，表示回答已完成
#                 self.answer_event.set()
#                 ws.close()
    
#     #  ============ WebSocket错误回调 ============
#     def on_error(self, ws, error):
#         """
#         处理WebSocket错误
        
#         参数:
#             ws: WebSocket实例
#             error: 错误信息
#         """
#         print(f"WebSocket错误: {error}")
#         self.error_msg = str(error)
#         self.answer_event.set()
    
#     #  ============ WebSocket关闭回调 ============
#     def on_close(self, ws, close_status_code, close_msg):
#         """
#         处理WebSocket关闭
        
#         参数:
#             ws: WebSocket实例
#             close_status_code: 关闭状态码
#             close_msg: 关闭消息
#         """
#         pass
    
#     #  ============ WebSocket打开回调 ============
#     def on_open(self, ws):
#         """
#         WebSocket连接建立时的回调，用于发送请求
        
#         参数:
#             ws: WebSocket实例
#         """
#         def run():
#             # 发送请求数据
#             data = json.dumps(self.current_params)
#             ws.send(data)
        
#         # 在新线程中发送数据
#         thread.start_new_thread(run, ())
    
#     #  ============ 封装的提问方法 ============
#     def ask(self, question: str, timeout: float = 30.0) -> Optional[str]:
#         """
#         向星火大模型提问并获取回答（封装方法，自动处理WebSocket连接）
        
#         参数:
#             question: 要提问的问题
#             timeout: 超时时间（秒），默认30秒
            
#         返回:
#             str: 星火大模型的回答，如果出错则返回None
#         """
#         # 重置状态
#         self.full_answer = ""
#         self.error_msg = None
#         self.answer_event.clear()
        
#         # 生成请求参数
#         self.current_params = self.gen_params(question)
        
#         # 创建WebSocket URL
#         ws_url = self.create_url()
        
#         # 创建WebSocket连接
#         ws = websocket.WebSocketApp(
#             ws_url,
#             on_message=self.on_message,
#             on_error=self.on_error,
#             on_close=self.on_close,
#             on_open=self.on_open
#         )
        
#         # 在新线程中运行WebSocket
#         ws_thread = threading.Thread(target=ws.run_forever, kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}})
#         ws_thread.daemon = True
#         ws_thread.start()
        
#         # 等待回答完成或超时
#         if self.answer_event.wait(timeout):
#             if self.error_msg:
#                 print(f"请求失败: {self.error_msg}")
#                 return None
#             answer = self.full_answer
#             self.full_answer = ""  # 重置
#             return answer
#         else:
#             print(f"请求超时（{timeout}秒）")
#             ws.close()
#             return None
    
#     #  ============ 清除对话历史 ============
#     def clear_history(self) -> None:
#         """
#         清除对话历史文件，开始新的对话
#         """
#         if os.path.exists(self.history):
#             os.remove(self.history)
#             print("对话历史已清除")
    
#     #  ============ 获取对话历史 ============
#     def get_history(self) -> list:
#         """
#         获取当前的对话历史
        
#         返回:
#             list: 对话历史列表
#         """
#         try:
#             with open(self.history, "r", encoding="utf-8") as f:
#                 return json.load(f)
#         except (FileNotFoundError, json.JSONDecodeError):
#             return []

