# DeepSeek API 参考

本文档汇总 DeepSeek 常用 HTTP 端点、请求/响应示例与调用方式。接口格式与 [OpenAI API](https://platform.openai.com/docs/api-reference) 兼容。

| 参数 | 值 |
| --- | --- |
| Base URL | `https://api.deepseek.com` |
| 兼容 Base URL | `https://api.deepseek.com/v1`（旧版客户端） |
| 认证 | `Authorization: Bearer <DEEPSEEK_API_KEY>` |
| 模型 | `deepseek-v4-flash`、`deepseek-v4-pro` 等，见 [列出模型](#列出模型) |

更多入门与高级用法见 [快速开始](./快速开始.md)、[API 指南](./API指南.md)。

---

## 对话补全

`POST` `https://api.deepseek.com/chat/completions`

根据输入的上下文，让模型补全对话内容。

### Python（OpenAI SDK）

```python
from openai import OpenAI

# 兼容旧版客户端时，base_url 也可使用 https://api.deepseek.com/v1
client = OpenAI(api_key="<DEEPSEEK_API_KEY>", base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ],
    max_tokens=1024,
    temperature=0.7,
    stream=False,
)

print(response.choices[0].message.content)
```

### Python（requests）

```python
import json
import requests

url = "https://api.deepseek.com/chat/completions"

payload = {
    "messages": [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hi"},
    ],
    "model": "deepseek-v4-pro",
    "thinking": {"type": "enabled"},
    "reasoning_effort": "high",
    "max_tokens": 4096,
    "response_format": {"type": "text"},
    "stream": False,
    "temperature": 1,
    "top_p": 1,
    "tool_choice": "none",
    "logprobs": False,
}

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": "Bearer <DEEPSEEK_API_KEY>",
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
print(response.text)
```

### 请求体

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `messages` | array | **必填**。对话消息列表 |
| `model` | string | **必填**。模型 ID，如 `deepseek-v4-pro` |
| `thinking` | object | 思考模式开关，如 `{"type": "enabled"}` |
| `reasoning_effort` | string | 思考强度，如 `high`、`max` |
| `max_tokens` | integer | 生成 token 上限 |
| `stream` | boolean | 是否流式输出 |
| `temperature` | number | 采样温度 |
| `top_p` | number | 核采样 |
| `response_format` | object | 响应格式，如 `{"type": "text"}` |
| `tools` | array \| null | 工具定义 |
| `tool_choice` | string | 工具选择策略 |

示例请求体：

```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hi"}
  ],
  "model": "deepseek-v4-pro",
  "thinking": {"type": "enabled"},
  "reasoning_effort": "high",
  "max_tokens": 4096,
  "response_format": {"type": "text"},
  "stream": false,
  "temperature": 1,
  "top_p": 1,
  "tool_choice": "none",
  "logprobs": false
}
```

### 响应示例

```json
{
  "id": "514bc96f-5e9b-45e1-97be-baedbcfd8a54",
  "object": "chat.completion",
  "created": 1779180961,
  "model": "deepseek-v4-pro",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I assist you today?",
        "reasoning_content": "..."
      },
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 64,
    "total_tokens": 74,
    "prompt_tokens_details": {"cached_tokens": 0},
    "completion_tokens_details": {"reasoning_tokens": 54},
    "prompt_cache_hit_tokens": 0,
    "prompt_cache_miss_tokens": 10
  },
  "system_fingerprint": "fp_9954b31ca7_prod0820_fp8_kvcache_20260402"
}
```

思考模式下，思维链通过 `choices[].message.reasoning_content` 返回，详见 [API 指南 · 思考模式](./API指南.md#思考模式)。

---

## 列出模型

`GET` `https://api.deepseek.com/models`

返回当前账号可用的模型列表。

### Python（OpenAI SDK）

```python
from openai import OpenAI

client = OpenAI(api_key="<DEEPSEEK_API_KEY>", base_url="https://api.deepseek.com")
print(client.models.list())
```

### Python（requests）

```python
import requests

url = "https://api.deepseek.com/models"
headers = {
    "Accept": "application/json",
    "Authorization": "Bearer <DEEPSEEK_API_KEY>",
}

response = requests.get(url, headers=headers)
print(response.text)
```

### 响应示例

```json
{
  "object": "list",
  "data": [
    {
      "id": "deepseek-v4-flash",
      "object": "model",
      "owned_by": "deepseek"
    },
    {
      "id": "deepseek-v4-pro",
      "object": "model",
      "owned_by": "deepseek"
    }
  ]
}
```

---

## 查询余额

`GET` `https://api.deepseek.com/user/balance`

查询账号余额。

### Python（requests）

```python
import requests

url = "https://api.deepseek.com/user/balance"
headers = {
    "Accept": "application/json",
    "Authorization": "Bearer <DEEPSEEK_API_KEY>",
}

response = requests.get(url, headers=headers)
print(response.text)
```

### 响应

| 状态码 | 说明 |
| --- | --- |
| `200` | 成功，返回用户余额详情 |

响应示例：

```json
{
  "is_available": true,
  "balance_infos": [
    {
      "currency": "CNY",
      "total_balance": "49.99",
      "granted_balance": "0.00",
      "topped_up_balance": "49.99"
    }
  ]
}
```
