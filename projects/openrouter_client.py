"""Compatibility import for callers of the previous tutor transport.

All requests now use DeepSeek and DEEPSEEK_API_KEY, never OpenRouter.
New code should import ask_deepseek_stream from projects.deepseek_client.
"""

from projects.deepseek_client import ask_deepseek_stream

# Preserve the former callable without retaining the former service or key.
ask_openrouter_stream = ask_deepseek_stream
