#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI对话接口主程序
使用 AIManager.py 中的 AIFactory 进行双AI协同对话
基于 MCP 工具的简化架构
"""

import os
import sys
import json

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from module.AICore.AIManager import AIFactory
from module.Agent.Agent import Agent
from module.MCP.client.MCPClient import MCPClient
import time

