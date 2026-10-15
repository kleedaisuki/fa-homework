# DeepSeek V4.1-Flash migration

Supersedes the transport described in `openrouter-migration.md`.

## Contract

- Both notebook tutors now import `ask_deepseek_stream` from `projects.deepseek_client`.
- Official endpoint: `https://api.deepseek.com/chat/completions`.
- Default model ID: `deepseek-flash`, which the official documentation and authenticated model listing identify as DeepSeek-V4.1-Flash.
- Read `DEEPSEEK_API_KEY` at request time; `DEEPSEEK_MODEL` is an optional explicit override. Never fall back to `OPENROUTER_API_KEY`, OpenRouter, or Ollama.
- Preserve streaming Markdown, exercise prompts, history, attendance, and local logging. Only answer `content` is displayed; reasoning and usage frames are not shown.
- Retain `projects.openrouter_client.ask_openrouter_stream` as a Python import compatibility alias only. It delegates to DeepSeek, uses the new key, and contains no former-provider request logic.
- Reuse requests and the existing locked environment; no dependency additions are required.
- Keep errors actionable but do not print upstream response bodies, credentials, or raw transport exceptions. Do not automatically retry billable requests.

## Validation (2026-10-15, Windows, CPython 3.14.7)

- Authenticated `GET https://api.deepseek.com/models`: HTTP 200; returned `deepseek-flash` named `DeepSeek-V4.1-Flash` and `deepseek-v4-pro` named `DeepSeek-V4-Pro`. Read the key from the saved Windows user environment into the validation process only; never printed or persisted it.
- Executed all original code cells in `fa.ipynb` with nbclient, then submitted a real student question through the final tutor. DeepSeek returned contextual Chinese guidance, and the final reply was present in the rendered chat. The original notebook remains unchanged and output-free; the validation script is ignored under `.temp`.
- `uv run pytest -q --basetemp=.temp/pytest`: 23 offline tests cover both tutors, all three discussion exercises, attendance, HTTP contracts, default/override models, missing keys, absence of old-key fallback, Unicode streaming, HTTP errors, malformed/truncated streams, hidden reasoning/usage, and the compatibility import.
- `uv run ruff check .` and `uv lock --check`: passed.
- Existing ipywidgets deprecation warnings and Windows ZMQ warnings remain unrelated to this provider change; the real notebook workflow succeeds.

## User operation

Restart Jupyter and rerun tutor cells to load the new imports. If the parent terminal predates creation of the saved Windows user variable, explicitly load `DEEPSEEK_API_KEY` into that terminal before starting Jupyter, as shown in README. No `.env` loading is performed.

Repository visibility remains public as requested. Secrets and personal learning logs remain ignored.

## Primary sources

- https://api-docs.deepseek.com/ — official endpoint, authentication, and Flash model mapping.
- https://api-docs.deepseek.com/api/create-chat-completion — streaming chat completion API.
