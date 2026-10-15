"""Shared OpenRouter transport for both notebook tutors.

Set OPENROUTER_API_KEY before starting Jupyter. Optionally select a model with
OPENROUTER_MODEL. Errors are safe, user-facing chunks, never raw HTTP bodies.
"""

import json
import os
from collections.abc import Iterator

import requests

API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openrouter/auto"


def ask_openrouter_stream(prompt: str) -> Iterator[str]:
    """Yield streamed answer text, or an actionable error without credentials.

    Configuration is read at call time so notebook environment changes take
    effect immediately. Requests are not retried to avoid duplicate billing.
    Connections are closed even when a caller stops consuming the iterator.

    Example:
        answer = "".join(ask_openrouter_stream("Explain DFA states briefly."))
    """
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        yield "❌ 请设置 OPENROUTER_API_KEY 环境变量，然后重启 Jupyter / 内核。"
        return
    model = os.environ.get("OPENROUTER_MODEL", "").strip() or DEFAULT_MODEL
    try:
        with requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "stream": True},
            stream=True,
            timeout=(15, 120),
        ) as response:
            if response.status_code != 200:
                hints = {
                    400: "请检查 OPENROUTER_MODEL 和请求参数。",
                    401: "请检查 OPENROUTER_API_KEY 是否有效。",
                    402: "请检查 OpenRouter 账户余额。",
                    403: "请检查密钥权限和模型访问策略。",
                    404: "请检查 OPENROUTER_MODEL 是否可用。",
                    429: "请求过于频繁，请稍后重试。",
                }
                yield f"❌ OpenRouter 请求失败（HTTP {response.status_code}）。" + hints.get(
                    response.status_code, "服务暂时不可用，请稍后重试。"
                )
                return
            # SSE uses UTF-8 regardless of requests' default text encoding.
            response.encoding = "utf-8"
            received_text = False
            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    if not received_text:
                        yield "❌ OpenRouter 未返回文本，请重试或更换模型。"
                    return
                data = json.loads(payload)
                if data.get("error"):
                    yield "❌ OpenRouter 在生成途中返回错误，请稍后重试或更换模型。"
                    return
                for choice in data.get("choices", []):
                    if choice.get("finish_reason") == "error":
                        yield "❌ OpenRouter 模型生成失败，请稍后重试。"
                        return
                    content = (choice.get("delta") or {}).get("content")
                    if content:
                        received_text = True
                        yield content
            yield "❌ OpenRouter 响应流意外结束，回复可能不完整，请重试。"
    except requests.exceptions.Timeout:
        yield "❌ OpenRouter 请求超时，请检查网络或稍后重试。"
    except requests.exceptions.RequestException:
        yield "❌ 无法连接 OpenRouter，请检查网络和代理设置。"
    except (ValueError, TypeError, AttributeError):
        yield "❌ OpenRouter 响应格式异常，请重试或更换模型。"
