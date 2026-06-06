"""DeepSeek 大模型调用公共方法。

本模块封装了对 DeepSeek 对话 API 的调用，供 spiderx 下其它本地程序直接复用。
API Key 从仓库根目录的 .env 文件中读取（DEEPSEEK_KEY），使用相对路径定位，
因此无论从哪个子目录运行都能正确加载。

典型用法::

    # 1) 把 spiderx 目录加入 sys.path（与其它子模块一致）
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    # 2) 引用公共方法
    from deepseek.main import ask, chat, chat_json, DeepSeekClient

    # 最简单：一问一答
    text = ask("用一句话介绍螺纹钢期货")

    # 带系统提示词
    text = ask("总结这条新闻", system="你是财经分析助手")

    # 要求返回 JSON 并自动解析为 dict
    data = chat_json("请用 JSON 返回 {\\"score\\": 1-10}，对这条新闻评分：...")

    # 需要复用同一份配置/连接时，直接用客户端
    client = DeepSeekClient()
    reply = client.ask("你好")
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests

# ==================== 配置 ====================

# .env 位于仓库根目录：spiderx/deepseek/main.py -> parents[2] == workstation/
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"

# DeepSeek 默认参数（见 spiderx/deepseek/doc/ 下的文档）
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_TIMEOUT = 120
DEFAULT_MAX_RETRIES = 2


def _parse_env_file(env_path: Union[str, Path]) -> Dict[str, str]:
    """解析 .env 文件为字典（与 db/mysql_config.py 保持一致的实现）。"""
    path = Path(env_path)
    if not path.exists():
        raise FileNotFoundError(f"未找到环境变量文件: {path}")

    values: Dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        values[key] = value

    return values


def load_deepseek_key(env_path: Optional[Union[str, Path]] = None) -> str:
    """读取 DeepSeek API Key。

    优先级：进程环境变量 DEEPSEEK_KEY / DEEPSEEK_API_KEY > .env 文件。
    """
    key = os.environ.get("DEEPSEEK_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key

    values = _parse_env_file(env_path or ENV_PATH)
    key = values.get("DEEPSEEK_KEY") or values.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError(
            f"缺少 DeepSeek API Key，请在 {env_path or ENV_PATH} 中配置 DEEPSEEK_KEY"
        )
    return key


# ==================== 客户端 ====================


class DeepSeekClient:
    """DeepSeek 对话客户端（可复用）。"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        self.api_key = api_key or load_deepseek_key()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def chat(
        self,
        messages: List[Dict[str, Any]],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking: bool = False,
        reasoning_effort: Optional[str] = None,
        response_format: Optional[Dict[str, str]] = None,
        return_raw: bool = False,
        **extra: Any,
    ) -> Union[str, Dict[str, Any]]:
        """发起一次对话补全请求。

        Args:
            messages: OpenAI 风格的消息列表，如
                [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
            model: 模型名，默认 self.model（deepseek-v4-flash）。
            temperature: 采样温度（思考模式下无效）。
            max_tokens: 生成 token 上限。
            thinking: 是否开启思考模式。
            reasoning_effort: 思考强度，如 "high" / "max"。
            response_format: 响应格式，如 {"type": "json_object"}。
            return_raw: 为 True 时返回完整响应 JSON，否则返回回答文本。
            extra: 其它透传给 API 的字段（如 tools、tool_choice、stop 等）。

        Returns:
            return_raw=False 时返回 str（content）；否则返回完整响应 dict。
        """
        payload: Dict[str, Any] = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if thinking:
            payload["thinking"] = {"type": "enabled"}
        if reasoning_effort is not None:
            payload["reasoning_effort"] = reasoning_effort
        if response_format is not None:
            payload["response_format"] = response_format
        if extra:
            payload.update(extra)

        url = f"{self.base_url}/chat/completions"
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self._session.post(
                    url,
                    headers=self._headers(),
                    data=json.dumps(payload),
                    timeout=self.timeout + attempt * 30,
                )
                if response.status_code == 200:
                    result = response.json()
                    if return_raw:
                        return result
                    return result["choices"][0]["message"]["content"]

                last_error = RuntimeError(
                    f"DeepSeek 请求失败: HTTP {response.status_code} - {response.text[:200]}"
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc

            if attempt < self.max_retries:
                time.sleep(2 ** attempt)

        raise RuntimeError(f"DeepSeek 调用失败（已重试 {self.max_retries} 次）: {last_error}")

    def ask(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """便捷方法：单轮问答，返回纯文本回答。

        Args:
            prompt: 用户问题/内容。
            system: 可选的系统提示词。
            kwargs: 透传给 chat() 的其它参数。
        """
        messages: List[Dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, **kwargs)

    def ask_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """便捷方法：要求模型返回 JSON，并解析为 dict。

        注意：DeepSeek JSON 模式要求提示词中包含 "json" 字样并给出格式样例。
        """
        kwargs.setdefault("response_format", {"type": "json_object"})
        content = self.ask(prompt, system=system, **kwargs)
        return _safe_json_loads(content)


# ==================== 模块级便捷函数（默认共享单例） ====================

_default_client: Optional[DeepSeekClient] = None


def get_client() -> DeepSeekClient:
    """获取默认共享的 DeepSeekClient 单例。"""
    global _default_client
    if _default_client is None:
        _default_client = DeepSeekClient()
    return _default_client


def ask(prompt: str, system: Optional[str] = None, **kwargs: Any) -> str:
    """单轮问答，返回纯文本。等价于 get_client().ask(...)。"""
    return get_client().ask(prompt, system=system, **kwargs)


def chat(messages: List[Dict[str, Any]], **kwargs: Any) -> Union[str, Dict[str, Any]]:
    """多轮对话。等价于 get_client().chat(...)。"""
    return get_client().chat(messages, **kwargs)


def chat_json(prompt: str, system: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
    """要求返回 JSON 并解析为 dict。等价于 get_client().ask_json(...)。"""
    return get_client().ask_json(prompt, system=system, **kwargs)


def _safe_json_loads(content: str) -> Dict[str, Any]:
    """尽量从模型输出中解析出 JSON 对象（兼容 ```json``` 代码块包裹）。"""
    if content is None:
        raise ValueError("模型返回内容为空，无法解析 JSON")

    text = content.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 去除 markdown 代码块标记后重试
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # 截取第一个 { 到最后一个 } 之间的内容
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])

    raise ValueError(f"无法将模型输出解析为 JSON: {content[:200]}")


if __name__ == "__main__":
    # 简单自测：python main.py "你的问题"
    import sys

    question = sys.argv[1] if len(sys.argv) > 1 else "用一句话介绍你自己"
    print(f"[问] {question}")
    print(f"[答] {ask(question)}")
