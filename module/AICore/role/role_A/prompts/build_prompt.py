#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词构建脚本
将模块化的提示词文件整合成完整的 Char.JSON
"""

import os
import json

def load_module(filename):
    """加载单个模块文件"""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"警告：找不到文件 {filename}")
        return ""

def build_prompt():
    """构建完整提示词"""
    modules = [
        '01_base_role.txt',

    ]
    
    print("=" * 50)
    print("开始构建提示词...")
    print("=" * 50)
    
    content_parts = []
    for module in modules:
        print(f"加载模块: {module}")
        content = load_module(module)
        if content:
            content_parts.append(content)
    
    # 整合所有模块
    full_content = "\n\n".join(content_parts)
    
    # 构建JSON结构
    char_json = {
        "role": "system",
        "content": full_content
    }
    
    # 写入 assistant.json
    output_path = os.path.join(os.path.dirname(__file__), '..', 'assistant.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(char_json, f, ensure_ascii=False, indent=2)
    
    print("=" * 50)
    print(f"✓ 构建完成！")
    print(f"✓ 输出文件: {output_path}")
    print(f"✓ 总字符数: {len(full_content)}")
    print(f"✓ 总模块数: {len(modules)}")
    print("=" * 50)
    
    return char_json

if __name__ == "__main__":
    build_prompt()

