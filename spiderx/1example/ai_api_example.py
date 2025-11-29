#!/usr/bin/env python3
"""
AI API 调用示例 - 核心版本
基于 OpenAI 兼容的 v1/chat/completions 接口

核心功能：发送请求 -> 获取响应
AI_API_KEY和AI_BASE_URL就写死在代码里
"""

import requests


# ==================== 配置参数 ====================

# AI API 配置
AI_API_KEY = "sk-qVU4OZNspU5cSTPONFBFD000t2Oy8Tq9U8h74Wm5Phnl8tsB"
AI_BASE_URL = "https://poloai.top/v1/chat/completions"


# ==================== 核心函数 ====================

def call_ai_api(user_message, system_message="你是一个专业的分析助手。", model="gpt-4.1-mini"):
    """
    调用 AI API 获取响应
    
    参数：
        user_message: 用户消息（str）
        system_message: 系统提示词（str）
        model: 模型名称（str）
    
    返回：
        str: AI 返回的文本内容
    """
    # 构建请求
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 5000
    }
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 发送请求并解析响应
    response = requests.post(AI_BASE_URL, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    
    return response.json()["choices"][0]["message"]["content"]


# ==================== 使用示例 ====================

if __name__ == '__main__':
    try:
        # 基础调用
        result = call_ai_api("什么是人工智能？用一句话回答。")
        print(f"AI 回复: {result}")
        
    except Exception as e:
        print(f"错误: {e}")

