# DeepSeek API 指南

本文档介绍 DeepSeek API 的高级用法，包括思考模式、多轮对话、JSON 输出、工具调用与上下文缓存等。

---

## 思考模式

DeepSeek 模型支持思考模式：在输出最终回答之前，模型会先输出一段思维链内容，以提升最终答案的准确性。

### 思考模式开关与思考强度控制

| 控制项 | OpenAI 格式 | Anthropic 格式 |
| --- | --- | --- |
| 思考模式开关 (1) | `{"thinking": {"type": "enabled/disabled"}}` | — |
| 思考强度控制 (2)(3) | `{"reasoning_effort": "high/max"}` | `{"output_config": {"effort": "high/max"}}` |

> (1) 默认思考开关为 `enabled`  
> (2) 思考模式下，对普通请求，默认 effort 为 `high`；对一些复杂 Agent 类请求（如 Claude Code、OpenCode），effort 自动设置为 `max`  
> (3) 思考模式下，出于兼容考虑 `low`、`medium` 会映射为 `high`，`xhigh` 会映射为 `max`

使用 OpenAI SDK 设置 `thinking` 参数时，需将 `thinking` 传入 `extra_body`：

```python
response = client.chat.completions.create(
    model="deepseek-v4-pro",
    # ...
    reasoning_effort="high",
    extra_body={"thinking": {"type": "enabled"}},
)
```

### 输入输出参数

思考模式**不支持** `temperature`、`top_p`、`presence_penalty`、`frequency_penalty` 参数。为兼容已有软件，设置这些参数不会报错，但也不会生效。

在思考模式下，思维链内容通过 `reasoning_content` 参数返回，与 `content` 同级。在后续轮次的拼接中，可以选择性地将 `reasoning_content` 回传给 API：

- 在两个 user 消息之间，若模型**未**进行工具调用，则中间 assistant 的 `reasoning_content` **无需**参与上下文拼接；在后续轮次中传入 API 会被忽略。详见 [多轮对话拼接](#多轮对话拼接)。
- 在两个 user 消息之间，若模型**进行了**工具调用，则中间 assistant 的 `reasoning_content` **必须**参与上下文拼接，在后续所有 user 交互轮次中必须回传给 API。详见 [工具调用](#工具调用)。

### 多轮对话拼接

在每一轮对话过程中，模型会输出思维链内容（`reasoning_content`）和最终回答（`content`）。如果没有工具调用，则在下一轮对话中，之前轮输出的思维链内容不会被拼接到上下文中。

### 样例代码

以下以 Python 为例，展示如何访问思维链和最终回答，以及如何在多轮对话中进行上下文拼接。

#### 非流式

```python
from openai import OpenAI

client = OpenAI(api_key="<DEEPSEEK_API_KEY>", base_url="https://api.deepseek.com")

# Turn 1
messages = [{"role": "user", "content": "9.11 and 9.8, which is greater?"}]
response = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=messages,
    reasoning_effort="high",
    extra_body={"thinking": {"type": "enabled"}},
)

reasoning_content = response.choices[0].message.reasoning_content
content = response.choices[0].message.content

# Turn 2
# The reasoning_content will be ignored by the API
messages.append(response.choices[0].message)
messages.append({"role": "user", "content": "How many Rs are there in the word 'strawberry'?"})
response = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=messages,
    reasoning_effort="high",
    extra_body={"thinking": {"type": "enabled"}},
)
# ...
```

> 流式输出的写法与上述类似，将 `stream=True` 即可；详见官方文档。

### 工具调用

DeepSeek 模型的思考模式支持工具调用。模型在输出最终答案之前，可以进行多轮的思考与工具调用，以提升答案质量。

> **注意**：区别于思考模式下未进行工具调用的轮次，**进行了工具调用的轮次**，在后续所有请求中，必须完整回传 `reasoning_content` 给 API。若未正确回传，API 会返回 400 报错。

#### 样例代码

下面是在思考模式下进行工具调用的样例：

```python
import os
import json
from openai import OpenAI
from datetime import datetime

# The definition of the tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_date",
            "description": "Get the current date",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather of a location, the user should supply the location and date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "The city name"},
                    "date": {"type": "string", "description": "The date in format YYYY-mm-dd"},
                },
                "required": ["location", "date"],
            },
        },
    },
]

# The mocked version of the tool calls
def get_date_mock():
    return datetime.now().strftime("%Y-%m-%d")

def get_weather_mock(location, date):
    return "Cloudy 7~13°C"

TOOL_CALL_MAP = {
    "get_date": get_date_mock,
    "get_weather": get_weather_mock,
}

def run_turn(turn, messages):
    sub_turn = 1
    while True:
        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=messages,
            tools=tools,
            reasoning_effort="high",
            extra_body={"thinking": {"type": "enabled"}},
        )
        messages.append(response.choices[0].message)
        reasoning_content = response.choices[0].message.reasoning_content
        content = response.choices[0].message.content
        tool_calls = response.choices[0].message.tool_calls
        print(f"Turn {turn}.{sub_turn}\n{reasoning_content=}\n{content=}\n{tool_calls=}")
        if tool_calls is None:
            break
        for tool in tool_calls:
            tool_function = TOOL_CALL_MAP[tool.function.name]
            tool_result = tool_function(**json.loads(tool.function.arguments))
            print(f"tool result for {tool.function.name}: {tool_result}\n")
            messages.append({
                "role": "tool",
                "tool_call_id": tool.id,
                "content": tool_result,
            })
        sub_turn += 1
    print()

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url=os.environ.get("DEEPSEEK_BASE_URL"),
)

# Turn 1
turn = 1
messages = [{"role": "user", "content": "How's the weather in Hangzhou Tomorrow"}]
run_turn(turn, messages)

# Turn 2
turn = 2
messages.append({"role": "user", "content": "How's the weather in Guangzhou Tomorrow"})
run_turn(turn, messages)
```

在 Turn 1 的每个子请求中，都携带了该 Turn 下产生的 `reasoning_content` 给 API，从而让模型继续之前的思考。`response.choices[0].message` 携带了 assistant 消息的所有必要字段，包括 `content`、`reasoning_content`、`tool_calls`。简单起见，可以直接：

```python
messages.append(response.choices[0].message)
```

等价于：

```python
messages.append({
    "role": "assistant",
    "content": response.choices[0].message.content,
    "reasoning_content": response.choices[0].message.reasoning_content,
    "tool_calls": response.choices[0].message.tool_calls,
})
```

且在 Turn 2 的请求中，仍然携带着 Turn 1 所产生的 `reasoning_content` 给 API。

#### 样例输出

```
Turn 1.1
reasoning_content="The user is asking about the weather in Hangzhou tomorrow. I need to get tomorrow's date first, then call the weather function."
content="Let me check tomorrow's weather in Hangzhou for you. First, let me get tomorrow's date."
tool_calls=[ChatCompletionMessageFunctionToolCall(...)]
tool result for get_date: 2026-04-19

Turn 1.2
reasoning_content="Today is 2026-04-19, so tomorrow is 2026-04-20. Now I'll call the weather function for Hangzhou."
content=''
tool_calls=[ChatCompletionMessageFunctionToolCall(...)]
tool result for get_weather: Cloudy 7~13°C

Turn 1.3
reasoning_content='The weather result is in. Let me share this with the user.'
content="Here's the weather forecast for **Hangzhou tomorrow (April 20, 2026)**: ..."
tool_calls=None
```

---

## 多轮对话

本指南介绍如何使用 DeepSeek `/chat/completions` API 进行多轮对话。

DeepSeek `/chat/completions` API 是**无状态**的：服务端不记录用户请求的上下文，每次请求需将之前所有对话历史拼接后传给 API。

下面的代码以 Python 为例，展示如何进行上下文拼接：

```python
from openai import OpenAI

client = OpenAI(api_key="<DEEPSEEK_API_KEY>", base_url="https://api.deepseek.com")

# Round 1
messages = [{"role": "user", "content": "What's the highest mountain in the world?"}]
response = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=messages,
)

messages.append(response.choices[0].message)
print(f"Messages Round 1: {messages}")

# Round 2
messages.append({"role": "user", "content": "What is the second?"})
response = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=messages,
)

messages.append(response.choices[0].message)
print(f"Messages Round 2: {messages}")
```

**第一轮**请求时，传递给 API 的 `messages` 为：

```json
[
    {"role": "user", "content": "What's the highest mountain in the world?"}
]
```

**第二轮**请求时：

1. 将第一轮中模型的输出添加到 `messages` 末尾
2. 将新的提问添加到 `messages` 末尾

最终传递给 API 的 `messages` 为：

```json
[
    {"role": "user", "content": "What's the highest mountain in the world?"},
    {"role": "assistant", "content": "The highest mountain in the world is Mount Everest."},
    {"role": "user", "content": "What is the second?"}
]
```

---

## 对话前缀续写（Beta）

对话前缀续写沿用 Chat Completion API：用户提供以 assistant 开头的消息，让模型补全其余内容。

### 注意事项

- 使用对话前缀续写时，需确保 `messages` 列表里**最后一条**消息的 `role` 为 `assistant`，并设置 `prefix` 参数为 `True`。
- 需设置 `base_url="https://api.deepseek.com/beta"` 以开启 Beta 功能。

### 样例代码

下面给出完整 Python 样例。本例将 assistant 开头的消息设为 `"```python\n"` 以强制模型输出 Python 代码，并设置 `stop` 参数为 `['```']` 以避免额外解释：

```python
from openai import OpenAI

client = OpenAI(
    api_key="<DEEPSEEK_API_KEY>",
    base_url="https://api.deepseek.com/beta",
)

messages = [
    {"role": "user", "content": "Please write quick sort code"},
    {"role": "assistant", "content": "```python\n", "prefix": True},
]
response = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=messages,
    stop=["```"],
)
print(response.choices[0].message.content)
```

---

## JSON Output

在很多场景下，需要让模型严格按照 JSON 格式输出，以实现结构化，便于后续解析。

DeepSeek 提供 JSON Output 功能，确保模型输出合法的 JSON 字符串。

### 注意事项

- 设置 `response_format` 参数为 `{'type': 'json_object'}`。
- 传入的 system 或 user prompt 中**必须含有 `json` 字样**，并给出希望输出的 JSON 格式样例。
- 合理设置 `max_tokens`，防止 JSON 字符串被中途截断。
- 使用 JSON Output 时，API 有概率返回空的 `content`；可尝试修改 prompt 以缓解。

### 样例代码

```python
import json
from openai import OpenAI

client = OpenAI(
    api_key="<DEEPSEEK_API_KEY>",
    base_url="https://api.deepseek.com",
)

system_prompt = """
The user will provide some exam text. Please parse the "question" and "answer" and output them in JSON format.

EXAMPLE INPUT:
Which is the highest mountain in the world? Mount Everest.

EXAMPLE JSON OUTPUT:
{
    "question": "Which is the highest mountain in the world?",
    "answer": "Mount Everest"
}
"""

user_prompt = "Which is the longest river in the world? The Nile River."

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt},
]

response = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=messages,
    response_format={"type": "json_object"},
)

print(json.loads(response.choices[0].message.content))
```

模型输出示例：

```json
{
    "question": "Which is the longest river in the world?",
    "answer": "The Nile River"
}
```

---

## Tool Calls

Tool Calls 让模型能够调用外部工具，以增强自身能力。

### 非思考模式

#### 样例代码

以下以获取用户当前位置的天气信息为例。Tool Calls 的具体 API 格式请参考[对话补全文档](https://api-docs.deepseek.com/zh-cn/api/create-chat-completion)。

```python
from openai import OpenAI

def send_messages(messages):
    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=messages,
        tools=tools,
    )
    return response.choices[0].message

client = OpenAI(
    api_key="<DEEPSEEK_API_KEY>",
    base_url="https://api.deepseek.com",
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather of a location, the user should supply a location first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                },
                "required": ["location"],
            },
        },
    },
]

messages = [{"role": "user", "content": "How's the weather in Hangzhou, Zhejiang?"}]
message = send_messages(messages)
print(f"User>\t {messages[0]['content']}")

tool = message.tool_calls[0]
messages.append(message)
messages.append({"role": "tool", "tool_call_id": tool.id, "content": "24℃"})
message = send_messages(messages)
print(f"Model>\t {message.content}")
```

执行流程：

1. **用户**：询问现在的天气
2. **模型**：返回 `function get_weather({location: 'Hangzhou'})`
3. **用户**：调用 `get_weather` 并将结果传给模型
4. **模型**：返回自然语言，如 "The current temperature in Hangzhou is 24°C."

> 上述代码中 `get_weather` 函数功能需由用户提供，模型本身不执行具体函数。

### 思考模式

从 DeepSeek-V3.2 开始，API 支持思考模式下的工具调用，详见 [思考模式 · 工具调用](#工具调用)。

### strict 模式（Beta）

在 strict 模式下，模型输出 Function 调用时会严格遵循 Function 的 JSON Schema，确保输出符合用户定义。思考与非思考模式下的工具调用均可使用 strict 模式。

使用 strict 模式需要：

1. 设置 `base_url="https://api.deepseek.com/beta"` 开启 Beta 功能
2. 在传入的 `tools` 列表中，所有 function 均需设置 `strict: true`
3. 服务端会对 Function 的 JSON Schema 进行校验；不符合规范或不支持的类型将返回错误

strict 模式下 tool 定义样例：

```json
{
    "type": "function",
    "function": {
        "name": "get_weather",
        "strict": true,
        "description": "Get weather of a location, the user should supply a location first.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA"
                }
            },
            "required": ["location"],
            "additionalProperties": false
        }
    }
}
```

#### strict 模式支持的 JSON Schema 类型

- `object`
- `string`
- `number`
- `integer`
- `boolean`
- `array`
- `enum`
- `anyOf`

##### object 类型

`object` 定义包含键值对的深层结构，`properties` 定义每个键的 schema。每个 object 的所有属性均需设为 `required`，且 `additionalProperties` 必须为 `false`。

```json
{
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"}
    },
    "required": ["name", "age"],
    "additionalProperties": false
}
```

##### string 类型

**支持的参数：**

| 参数 | 说明 |
| --- | --- |
| `pattern` | 使用正则约束字符串格式 |
| `format` | 预定义格式校验，支持：`email`、`hostname`、`ipv4`、`ipv6`、`uuid` |

**不支持的参数：** `minLength`、`maxLength`

```json
{
    "type": "object",
    "properties": {
        "user_email": {
            "type": "string",
            "description": "The user's email address",
            "format": "email"
        },
        "zip_code": {
            "type": "string",
            "description": "Six digit postal code",
            "pattern": "^\\d{6}$"
        }
    }
}
```

##### number / integer 类型

**支持的参数：** `const`、`default`、`minimum`、`maximum`、`exclusiveMinimum`、`exclusiveMaximum`、`multipleOf`

```json
{
    "type": "object",
    "properties": {
        "score": {
            "type": "integer",
            "description": "A number from 1-5, which represents your rating, the higher, the better",
            "minimum": 1,
            "maximum": 5
        }
    },
    "required": ["score"],
    "additionalProperties": false
}
```

##### array 类型

**不支持的参数：** `minItems`、`maxItems`

```json
{
    "type": "object",
    "properties": {
        "keywords": {
            "type": "array",
            "description": "Five keywords of the article, sorted by importance",
            "items": {
                "type": "string",
                "description": "A concise and accurate keyword or phrase."
            }
        }
    },
    "required": ["keywords"],
    "additionalProperties": false
}
```

##### enum

`enum` 确保输出是预期选项之一，例如订单状态：

```json
{
    "type": "object",
    "properties": {
        "order_status": {
            "type": "string",
            "description": "Ordering status",
            "enum": ["pending", "processing", "shipped", "cancelled"]
        }
    }
}
```

##### anyOf

匹配所提供的多个 schema 中的任意一个，例如账户可以是邮箱或手机号：

```json
{
    "type": "object",
    "properties": {
        "account": {
            "anyOf": [
                {"type": "string", "format": "email", "description": "可以是电子邮件地址"},
                {"type": "string", "pattern": "^\\d{11}$", "description": "或11位手机号码"}
            ]
        }
    }
}
```

##### $ref 和 $def

可使用 `$def` 定义模块，再用 `$ref` 引用以减少重复；也可单独使用 `$ref` 定义递归结构：

```json
{
    "type": "object",
    "properties": {
        "report_date": {
            "type": "string",
            "description": "The date when the report was published"
        },
        "authors": {
            "type": "array",
            "description": "The authors of the report",
            "items": {"$ref": "#/$def/author"}
        }
    },
    "required": ["report_date", "authors"],
    "additionalProperties": false,
    "$def": {
        "author": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "author's name"},
                "institution": {"type": "string", "description": "author's institution"},
                "email": {"type": "string", "format": "email", "description": "author's email"}
            },
            "additionalProperties": false,
            "required": ["name", "institution", "email"]
        }
    }
}
```

---

## 上下文硬盘缓存

DeepSeek API 上下文硬盘缓存技术对所有用户**默认开启**，无需修改代码即可使用。

每个请求都会触发硬盘缓存的构建。若后续请求与之前的请求在前缀上存在重复，则重复部分只需从缓存中拉取，计入「缓存命中」。

### 缓存落盘与命中规则

缓存命中的前提是相应前缀已被「落盘」（写入硬盘缓存）。受 Sliding Window Attention 机制影响，缓存前缀的存取与判别与之前有所不同：每条缓存前缀是一个独立的完整单元，后续请求只有**完整匹配**缓存前缀单元时，才能命中缓存。

**缓存前缀落盘时机：**

| 时机 | 说明 |
| --- | --- |
| 请求结束位置落盘 | 每次请求的用户输入结束位置与模型输出结束位置，各产生一个缓存前缀单元 |
| 公共前缀检测落盘 | 系统检测到多次请求之间存在公共前缀时，将该公共前缀作为独立单元落盘 |
| 按固定 token 间隔落盘 | 在长输入或长输出中，以一定 token 间隔截取缓存前缀单元，避免长前缀迟迟无法被缓存 |

**举例 1：** 第一轮请求内容为 `A + B`，第二轮为 `A + B + C`，则第二轮可完整匹配 `A + B` 缓存前缀单元。详见 [例一：多轮对话](#例一多轮对话)。

**举例 2：** 第一轮为 `A + B`，第二轮为 `A + C`，则第二轮无法命中（`A + C` 不能完整匹配 `A + B`）。但系统会识别公共前缀 `A` 并落盘；第三轮 `A + D` 可命中 `A` 的缓存。详见 [例二：长文本问答](#例二长文本问答)。

### 例一：多轮对话

**第一次请求**

```json
[
    {"role": "system", "content": "你是一位乐于助人的助手"},
    {"role": "user", "content": "中国的首都是哪里？"}
]
```

**第二次请求**

```json
[
    {"role": "system", "content": "你是一位乐于助人的助手"},
    {"role": "user", "content": "中国的首都是哪里？"},
    {"role": "assistant", "content": "中国的首都是北京。"},
    {"role": "user", "content": "美国的首都是哪里？"}
]
```

第二次请求可完整复用第一次请求的缓存前缀单元，这部分会计入「缓存命中」。

### 例二：长文本问答

**第一次请求**

```json
[
    {"role": "system", "content": "你是一位资深的财报分析师..."},
    {"role": "user", "content": "<财报内容>\n\n请总结一下这份财报的关键信息。"}
]
```

**第二次请求**

```json
[
    {"role": "system", "content": "你是一位资深的财报分析师..."},
    {"role": "user", "content": "<财报内容>\n\n请分析一下这份财报的盈利情况。"}
]
```

**第三次请求**

```json
[
    {"role": "system", "content": "你是一位资深的财报分析师..."},
    {"role": "user", "content": "<财报内容>\n\n请分析一下公司收入与支出占比。"}
]
```

前两次请求不会命中缓存。完成后，系统会将 `system` 消息 + user 消息中的 `<财报内容>` 识别为缓存前缀单元并落盘。第三次请求完整匹配该单元后即可命中缓存。

### 查看缓存命中情况

DeepSeek API 在 `usage` 字段中增加了两个字段反映缓存命中情况：

| 字段 | 说明 |
| --- | --- |
| `prompt_cache_hit_tokens` | 本次请求输入中，缓存命中的 tokens 数 |
| `prompt_cache_miss_tokens` | 本次请求输入中，缓存未命中的 tokens 数 |

### 硬盘缓存与输出随机性

硬盘缓存只匹配到用户输入的前缀部分；输出仍通过计算推理得到，仍受 `temperature` 等参数影响。输出效果与不使用硬盘缓存相同。

### 其它说明

- 缓存系统是「尽力而为」，不保证 100% 缓存命中
- 缓存构建耗时为秒级；缓存不再使用后会自动清空，一般为数小时到数天
