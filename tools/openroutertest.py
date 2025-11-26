# 导入 OpenAI 客户端库
from openai import OpenAI
import json

# 创建 OpenAI 客户端，配置为使用 OpenRouter 服务
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",  # OpenRouter API 基础地址
  api_key="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",  # API 密钥
)

# 调用 API - 启用推理功能
response = client.chat.completions.create(
  model="google/gemini-3-pro-preview",  # 使用 Google Gemini 3 Pro 预览版模型
  messages=[
          {
            "role": "user",
            "content": "你好，请介绍一下你自己"  # 用户问题
          }
        ],
  extra_body={"reasoning": {"enabled": True}}  # 启用推理模式，让模型展示思考过程
)

# 提取助手的回复消息
message = response.choices[0].message

# 准备保存的数据
result = {
  "content": message.content,  # 回答内容
  "reasoning_details": message.reasoning_details if hasattr(message, 'reasoning_details') else None,  # 推理详情
  "model": response.model,  # 使用的模型
  "usage": {  # token 使用情况
    "prompt_tokens": response.usage.prompt_tokens,
    "completion_tokens": response.usage.completion_tokens,
    "total_tokens": response.usage.total_tokens
  } if hasattr(response, 'usage') else None
}

# 将结果保存到文件
output_file = "openrouter_response.json"
with open(output_file, 'w', encoding='utf-8') as f:
  json.dump(result, f, ensure_ascii=False, indent=2)

print(f"响应已保存到文件: {output_file}")
print(f"回答内容: {message.content}")