# AI 助手模块 - 项目目录结构

## 📁 完整目录树

```
ai_assistant/
├── ai_assistant.py                  # 主程序入口（AIAssistant类）
├── README_USAGE.md                  # 使用说明文档
├── PROJECT_STRUCTURE.md             # 本文档
├── debug.log                        # 调试日志
│
├── module/                          # 核心模块目录
│   │
│   ├── Agent/                       # AI代理模块
│   │   ├── __init__.py
│   │   ├── ConversationHandler.py  # 对话处理器（三阶段流程编排）
│   │   ├── _Search.py               # 知识检索处理（TODO生成与执行）
│   │   └── _Dialogue.py             # 对话生成处理（最终回答生成）
│   │
│   ├── AICore/                      # AI核心模块
│   │   ├── __init__.py
│   │   ├── AIManager.py             # AI工厂类（双AI协同管理）
│   │   │
│   │   ├── Model/                   # 多模型支持
│   │   │   ├── __init__.py
│   │   │   ├── deepseek.py          # DeepSeek模型 ✓
│   │   │   ├── qwen.py              # 通义千问模型 ✓
│   │   │   ├── Kiimi.py             # Kimi模型 ✓
│   │   │   ├── doubao.py            # 豆包模型 ✓
│   │   │   ├── claude.py            # Claude模型（待实现）
│   │   │   ├── Gemini.py            # Gemini模型（待实现）
│   │   │   ├── CharGPT.py           # ChatGPT模型（待实现）
│   │   │   └── xinhuo.py            # 讯飞星火模型（待实现）
│   │   │
│   │   ├── Tool/                    # AI工具类
│   │   │   ├── __init__.py
│   │   │   ├── OPEN_AI.py           # OpenAI标准接口封装
│   │   │   ├── HistoryManager.py    # 历史记录管理器（token裁剪）
│   │   │   └── ConfigValidator.py   # 配置验证器
│   │   │
│   │   └── role/                    # 角色配置目录
│   │       ├── config.json          # 模型配置文件
│   │       ├── secret_key.json      # API密钥配置（重要）
│   │       ├── system.json          # 系统配置
│   │       ├── user.JSON            # 用户配置
│   │       │
│   │       ├── role_A/              # 角色A配置（对话AI）
│   │       │   ├── assistant.json   # 助手配置
│   │       │   ├── history.JSON     # 对话历史
│   │       │   └── prompts/         # 提示词模板
│   │       │       ├── 01_base_role.txt
│   │       │       ├── 02_output_decision.txt
│   │       │       ├── 03_json_format.txt
│   │       │       ├── 04_code_structure.txt
│   │       │       ├── 05_pid_requirements.txt
│   │       │       ├── 06_examples_correct.txt
│   │       │       ├── 07_examples_wrong.txt
│   │       │       ├── 08_anti_history_pollution.txt
│   │       │       ├── 09_deep_thinking.txt
│   │       │       ├── build_prompt.py
│   │       │       └── README.md
│   │       │
│   │       └── role_B/              # 角色B配置（知识AI）
│   │           ├── assistant.json   # 助手配置
│   │           ├── history.json     # 对话历史
│   │           └── prompts/         # 提示词模板
│   │               ├── 01_base_role.txt
│   │               ├── 02_search_decision.txt
│   │               ├── 03_todo_generation.txt
│   │               ├── 04_search_execution.txt
│   │               ├── 05_json_format.txt
│   │               └── build_prompt.py
│   │
│   └── MCP/                         # MCP服务器模块
│       ├── __init__.py
│       │
│       ├── server/                  # MCP服务端
│       │   ├── __init__.py
│       │   ├── MCPServer.py         # MCP服务器（基于FastMCP）
│       │   └── Tools/               # MCP工具集（30+工具）
│       │       ├── __init__.py
│       │       ├── DatabaseEditor.py    # 数据库编辑工具
│       │       ├── DataInquire.py       # 数据查询工具
│       │       └── FileEditor.py        # 文件编辑工具
│       │
│       └── client/                  # MCP客户端
│           ├── __init__.py
│           └── MCPClient.py         # MCP客户端（异步任务队列）
│
├── tools/                           # 通用工具模块
│   ├── __init__.py
│   ├── log.py                       # 日志工具
│   └── AllEventsHandler.py          # 文件监控器（基于watchdog）
│
├── window/                          # Web配置管理界面
│   ├── app.py                       # Flask应用
│   ├── requirements.txt             # 依赖列表
│   ├── README.md                    # 说明文档
│   ├── 启动配置管理.bat             # 启动脚本
│   └── templates/
│       └── index.html               # 前端页面
│
├── Data/                            # 数据存储目录
│   ├── plc_program.st               # 示例数据文件
│   └── plc_program_toggle.st        # 示例数据文件
│
└── test/                            # 测试目录
    ├── mcp_complete.py              # MCP完整测试
    └── use_external_mcp.py          # 外部MCP测试
```

## 📦 模块说明

### 1. Agent 模块（AI代理）

**位置**: `module/Agent/`

**核心文件**:
- **ConversationHandler.py** - 对话处理器
  - 三阶段对话流程编排
  - 阶段1：生成TODO搜索规划
  - 阶段2：执行TODO列表查询
  - 阶段3：生成最终回答
  - 集成文件监控功能

- **_Search.py** - 知识检索处理
  - TODO计划生成
  - 文件上下文扫描和注入
  - 文件变化监控和更新
  - JSON指令执行

- **_Dialogue.py** - 对话生成处理
  - 对话模型调用
  - 查询结果注入
  - 历史记录简化

### 2. AICore 模块（AI核心）

**位置**: `module/AICore/`

**核心文件**:
- **AIManager.py** - AI工厂类
  - 双AI协同架构（对话模型 + 知识模型）
  - 支持多供应商模型切换
  - 配置文件管理
  - 流式输出回调函数

**子模块**:

#### 2.1 Model（多模型支持）
- ✓ **deepseek.py** - DeepSeek模型（已实现）
- ✓ **qwen.py** - 通义千问模型（已实现）
- ✓ **Kiimi.py** - Kimi模型（已实现）
- ✓ **doubao.py** - 豆包模型（已实现）
- ⏳ **claude.py** - Claude模型（待实现）
- ⏳ **Gemini.py** - Gemini模型（待实现）
- ⏳ **CharGPT.py** - ChatGPT模型（待实现）
- ⏳ **xinhuo.py** - 讯飞星火模型（待实现）

#### 2.2 Tool（AI工具类）
- **OPEN_AI.py** - OpenAI标准接口封装
  - 支持流式和非流式输出
  - 文件上传功能
  - 历史记录管理集成
  - 回调函数机制

- **HistoryManager.py** - 历史记录管理器
  - 对话历史管理（增删改查）
  - Token自动裁剪（保留最新对话）
  - 永久保留第一条system消息
  - 支持role_path区分不同模型的历史

- **ConfigValidator.py** - 配置验证器

#### 2.3 role（角色配置）
- **config.json** - 模型配置文件
- **secret_key.json** - API密钥配置（重要）
- **system.json** - 系统配置
- **user.JSON** - 用户配置
- **role_A/** - 对话AI配置和提示词
- **role_B/** - 知识AI配置和提示词

### 3. MCP 模块（工具调用系统）

**位置**: `module/MCP/`

#### 3.1 MCP Server（服务端）
- **MCPServer.py** - 基于FastMCP的服务器实现
  - 注册30+工具函数
  - 支持数据库、文件、数据查询操作

#### 3.2 MCP Tools（工具集）
- **DatabaseEditor.py** - 数据库编辑工具
  - SQLite数据库操作（连接、创建表、增删改查等）

- **DataInquire.py** - 数据查询工具
  - 文件查询（目录、内容、行数、模糊搜索）
  - 数据库查询（表列表、表内容、数据存在性、模糊搜索、统计、批量查询、条件筛选）

- **FileEditor.py** - 文件编辑工具
  - 文件编辑操作（读取、更新、删除、插入、追加行，JSON操作等）

#### 3.3 MCP Client（客户端）
- **MCPClient.py** - MCP客户端
  - 异步MCP客户端
  - 线程化运行
  - 任务队列管理
  - 支持暂停/恢复/关闭

### 4. tools 模块（通用工具）

**位置**: `tools/`

- **log.py** - 日志工具
- **AllEventsHandler.py** - 文件监控器
  - 基于watchdog的文件系统监控
  - 监控文件创建、删除、修改、移动事件
  - 事件队列管理
  - 支持递归监控子目录

### 5. window 模块（Web界面）

**位置**: `window/`

- **app.py** - Flask应用
- **templates/index.html** - 前端页面
- 用于配置管理的Web界面

### 6. 配置与数据

- **Data/** - 数据存储目录
- **test/** - 测试文件目录

---

## 🎯 核心特性

### ✅ 已实现功能

1. **双AI协同架构**
   - 对话AI（role_A）：负责理解用户需求、规划任务、生成回答
   - 知识AI（role_B）：负责数据收集、文件搜索、简单处理

2. **三阶段对话流程**
   - 阶段1：对话AI生成TODO搜索规划
   - 阶段2：知识AI执行TODO列表（调用MCP工具/扫描文件）
   - 阶段3：对话AI生成最终回答

3. **MCP工具调用系统**
   - 30+工具函数
   - 支持文件操作、数据库操作、数据查询
   - 异步任务队列管理

4. **文件监控系统**
   - 实时监控工作区文件变化
   - 事件队列存储
   - 集成到对话流程中

5. **多模型支持**
   - 已支持：DeepSeek、Qwen、Kimi、Doubao
   - 待支持：Claude、Gemini、ChatGPT、Xinhuo

6. **历史管理系统**
   - Token自动裁剪
   - 保留system消息
   - 支持多角色历史分离

### ⏳ 待实现功能

1. **AuthCore模块**（登录/注册/权限系统）
2. **独立的权限管理系统**
3. **WorkspaceIndex**（持久化工作空间索引）
4. **更多AI模型支持**（Claude、Gemini等）

---

## 📝 主要文件说明

| 文件路径 | 说明 | 状态 |
|---------|------|------|
| `ai_assistant.py` | 程序主入口（AIAssistant类） | ✓ |
| `module/AICore/AIManager.py` | AI工厂类（双模型管理） | ✓ |
| `module/Agent/ConversationHandler.py` | 对话处理器（三阶段流程） | ✓ |
| `module/Agent/_Search.py` | 知识检索处理 | ✓ |
| `module/Agent/_Dialogue.py` | 对话生成处理 | ✓ |
| `module/AICore/Tool/OPEN_AI.py` | OpenAI标准接口封装 | ✓ |
| `module/AICore/Tool/HistoryManager.py` | 历史记录管理器 | ✓ |
| `module/MCP/server/MCPServer.py` | MCP服务器 | ✓ |
| `module/MCP/client/MCPClient.py` | MCP客户端 | ✓ |
| `tools/AllEventsHandler.py` | 文件监控器 | ✓ |
| `window/app.py` | 配置管理Web界面 | ✓ |
| `module/AICore/role/config.json` | 模型配置文件 | ✓ |
| `module/AICore/role/secret_key.json` | API密钥配置（重要） | ✓ |

---

## 🔧 数据流说明

### 单轮对话的数据流

```
用户输入
  ↓
ConversationHandler（对话处理器）
  ↓
阶段1：对话AI生成TODO规划
  ↓
阶段2：知识AI执行TODO
  ├─ 扫描文件结构（_Search._scan_files）
  ├─ 调用MCP工具（通过JSON指令）
  └─ 监控文件变化（AllEventsHandler）
  ↓
阶段3：对话AI生成最终回答
  ↓
返回给用户
```

### 文件监控数据流

```
文件系统变化
  ↓
AllEventsHandler（watchdog监听）
  ↓
事件队列存储
  ↓
_Search读取事件
  ↓
更新文件上下文
  ↓
注入到知识AI
```

---

## ⚠️ 已知问题

1. **导入路径错误**
   - 文件：`ai_assistant.py:16`
   - 错误：`from module.Agent.AIManager import AIFactory`
   - 应为：`from module.AICore.AIManager import AIFactory`

2. **缺失模块**
   - JSONProcessor（被多处引用但未找到实现文件）

3. **部分模型未实现**
   - Claude、Gemini、ChatGPT、Xinhuo模型文件存在但未实现

---

## 📌 备注

- 所有API密钥统一在 `module/AICore/role/secret_key.json` 中管理
- 支持双AI协作：role_A（对话AI）和 role_B（知识AI）
- MCP工具调用通过JSON指令格式进行
- 文件监控基于watchdog库实现
- 历史管理支持token自动裁剪机制

