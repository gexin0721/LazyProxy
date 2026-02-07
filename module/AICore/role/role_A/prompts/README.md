# 模块化提示词架构

## 📁 目录结构

```
prompts/
├── 01_base_role.txt           # 基础角色和专业知识
├── 02_output_decision.txt     # 输出决策规则（JSON vs 文本）
├── 03_json_format.txt         # JSON格式规范
├── 04_code_structure.txt      # 代码结构要求
├── 05_pid_requirements.txt    # PID控制特殊要求
├── 06_examples_correct.txt    # 正确示例
├── 07_examples_wrong.txt      # 错误示例（禁止项）
├── 08_anti_history_pollution.txt  # 防止历史污染
├── 09_deep_thinking.txt       # 深度思考模式 ⭐⭐新增
├── build_prompt.py            # 整合脚本
└── README.md                   # 本文档
```

## 🎯 设计理念

### 问题
原来的 `Char.JSON` 把所有内容挤在一个文件里（6000+字符），导致：
- ❌ 难以维护
- ❌ 难以调试
- ❌ 难以版本管理
- ❌ 难以复用

### 解决方案
采用**模块化设计**，将提示词分解为7个功能模块：
- ✅ 每个模块职责单一
- ✅ 易于修改和测试
- ✅ 便于版本对比
- ✅ 支持模块复用

## 📝 模块说明

### 1. `01_base_role.txt` - 基础角色
- 定义AI的专业领域（PLC编程）
- 列出专业知识范围
- 定义编程语法规则

### 2. `02_output_decision.txt` - 输出决策 ⭐ 核心
- **最关键模块**：决定何时输出JSON，何时输出文本
- 列出分析关键词（输出文本）
- 列出编辑关键词（输出JSON）
- 提供触发示例

### 3. `03_json_format.txt` - JSON格式
- 定义严格的JSON结构规范
- 列出强制约束条件
- 禁止常见的JSON错误

### 4. `04_code_structure.txt` - 代码结构
- PLC代码结构要求
- 完整性规则
- 续写策略

### 5. `05_pid_requirements.txt` - PID要求
- PID控制的特殊要求
- 强制包含的安全机制
- PID代码模板

### 6. `06_examples_correct.txt` - 正确示例
- 3个完整的正确示例
- 覆盖主要使用场景
- 展示期望的输出格式

### 7. `07_examples_wrong.txt` - 错误示例
- 列出常见错误
- 明确禁止的行为
- 帮助AI理解边界

### 8. `08_anti_history_pollution.txt` - 防止历史污染
- **解决"第二次回复就出错"的问题**
- 防止AI从错误的历史对话中学习
- 特别强调：删除操作必须用JSON的delete字段
- 规定：历史中的错误格式不应被模仿

### 9. `09_deep_thinking.txt` - 深度思考模式 ⭐⭐ 新增
- **Chain-of-Thought (思维链) 技术**
- **解决行号错乱、变量重复等问题**
- 强制AI在输出前进行5步思考：
  1. 理解当前文件状态（重复3次行数）
  2. 识别用户意图
  3. 制定操作计划
  4. 验证检查（4项检查清单）
  5. 构造JSON
- **记忆强化**：关键信息重复2-3次
- 特别强调：删除操作后文件状态会变化

## 🚀 使用方法

### 构建完整提示词

```bash
cd prompts
python build_prompt.py
```

输出：
```
==================================================
开始构建提示词...
==================================================
加载模块: 01_base_role.txt
加载模块: 02_output_decision.txt
加载模块: 03_json_format.txt
加载模块: 04_code_structure.txt
加载模块: 05_pid_requirements.txt
加载模块: 06_examples_correct.txt
加载模块: 07_examples_wrong.txt
==================================================
✓ 构建完成！
✓ 输出文件: ../role/Char.JSON
✓ 总字符数: 6234
✓ 总模块数: 7
==================================================
```

### 修改提示词

**场景1：AI总是输出文本而不是JSON**
- 修改文件：`02_output_decision.txt`
- 添加更多编辑关键词
- 重新构建：`python build_prompt.py`

**场景2：JSON格式经常错误**
- 修改文件：`03_json_format.txt`
- 加强格式约束
- 重新构建

**场景3：PID代码缺少安全保护**
- 修改文件：`05_pid_requirements.txt`
- 强化强制要求
- 重新构建

### 调试单个模块

可以单独测试某个模块：

```bash
# 只测试输出决策模块
cat 02_output_decision.txt
```

## 🔄 维护流程

```
1. 发现问题
   ↓
2. 定位模块（哪个模块负责这个功能？）
   ↓
3. 修改模块文件
   ↓
4. 运行 build_prompt.py
   ↓
5. 测试 AI 程序
   ↓
6. 提交变更（git commit）
```

## 📊 版本管理优势

使用Git可以轻松对比：
```bash
# 查看某个模块的修改历史
git log prompts/02_output_decision.txt

# 对比两个版本的差异
git diff HEAD~1 prompts/02_output_decision.txt
```

## ⚠️ 注意事项

1. **修改后必须重新构建**
   - 修改 `.txt` 文件后，必须运行 `build_prompt.py`
   - 否则 `Char.JSON` 不会更新

2. **模块顺序很重要**
   - 01-07 的顺序是精心设计的
   - 基础规则在前，示例在后

3. **不要直接修改 Char.JSON**
   - `Char.JSON` 是自动生成的
   - 修改会在下次构建时被覆盖

## 🎯 未来扩展

可以轻松添加新模块：
- `08_debug_mode.txt` - 调试模式配置
- `09_multi_language.txt` - 多语言支持
- `10_advanced_features.txt` - 高级功能

只需在 `build_prompt.py` 的 `modules` 列表中添加即可。

## 📈 效果对比

| 项目 | 单文件方式 | 模块化方式 |
|------|----------|----------|
| 可维护性 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 可调试性 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 协作友好 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 版本管理 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 复用性 | ⭐ | ⭐⭐⭐⭐⭐ |

---

**设计者注**：这个架构参考了软件工程的模块化设计思想，让提示词工程更加专业和可维护。

