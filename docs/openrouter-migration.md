# Historical: OpenRouter migration and verification

Superseded by `deepseek-migration.md`. This records the previous transport only; current tutors use DeepSeek.

## Design

- Keep the original notebook and `%run projects/problem_ai_helper.py <id>` workflow unchanged.
- Both tutor modules share `projects/openrouter_client.py`; no Ollama endpoint or dependency remains.
- Read `OPENROUTER_API_KEY` and optional `OPENROUTER_MODEL` at request time. Default model: `openrouter/auto`.
- Use the existing requests dependency with OpenRouter Chat Completions streaming. Ignore SSE comments and content-free accounting frames; terminate on `[DONE]`. Surface malformed, empty, interrupted, and upstream-error streams rather than silently reporting success.
- Do not retry billable requests automatically. Close response connections on completion/cancellation. Never show upstream error bodies or raw exception strings that might contain sensitive data.
- Preserve course prompts, history, Markdown rendering, and local logs. Resolve tutor resources relative to their module rather than the working directory. Imports do not launch widgets; `%run` still does.
- The original coding tutor references resources not included in this course. Do not invent homework content. Its transport is migrated and its workflow is tested using temporary fixture resources.

## Verification (2026-10-15, Windows)

- `uv sync`: installed 98 packages with CPython 3.14.7. `uv lock --check` succeeded; the universal lock also includes platform-specific alternatives.
- `uv run pytest -q`: 19 tests cover actual local HTTP requests, bearer header, model selection, Unicode streaming, missing credentials, seven HTTP error statuses, broken/empty/error streams, attendance, all three discussion exercises, and the coding tutor using fixture resources.
- `uv run ruff check .`: passed.
- Live minimal OpenRouter request using the saved Windows user key returned a successful Chinese connection confirmation. No key was printed or saved.
- Executed every code cell in the unchanged `fa.ipynb` using nbclient and the project kernel. Submitted a real question to the final exercise tutor, received a contextual Chinese follow-up question, and verified the rendered chat. Test script and any generated scratch data remain ignored under `.temp`; the source notebook retains no outputs.
- Known inherited compatibility warnings: ipywidgets `Text.on_submit` deprecation, attendance Layout `gap`, and Windows Jupyter/ZMQ event-loop warning. They did not prevent either full notebook execution or tutor interaction; Enter submission behavior was retained rather than changed during this transport migration.

## Operational notes

Windows user environment variables are inherited only when processes start. The desktop process did not initially contain the key, but the Windows user environment did. Load that value into the current PowerShell process before launching Jupyter (README), or restart the parent app/terminal. The application itself reads ordinary process environment variables only.

The repository was initially private and subsequently made public at the user's explicit request. Local study logs, virtual environments, secrets, and scratch data are excluded from version control.

## References

- https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request
- https://openrouter.ai/docs/api/reference/streaming
- https://docs.astral.sh/uv/concepts/projects/sync/
