"""Exercise real HTTP streaming and notebook widget interactions offline."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from projects import deepseek_client as client
from projects.clock_in import create_session_widgets
from projects.problem_ai_helper import ThinkingAIChat, load_problems


@pytest.fixture
def server(monkeypatch):
    """Serve a controlled DeepSeek-compatible endpoint over real HTTP."""
    state = {"status": 200, "events": [": keepalive", 'data: {"choices":[{"delta":{"content":"你好"}}]}', 'data: {"choices":[{"delta":{"content":"，同学"}}]}', "data: [DONE]"], "requests": []}

    class Handler(BaseHTTPRequestHandler):
        """Record request contracts and stream configured UTF-8 responses."""

        def do_POST(self):
            """Accept a chat request and emit the configured SSE payload."""
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state["requests"].append((self.path, self.headers["Authorization"], body))
            self.send_response(state["status"])
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(("\n\n".join(state["events"]) + "\n\n").encode())

        def log_message(self, *args):
            """Keep test HTTP logs quiet and free of request credentials."""

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(client, "API_URL", f"http://127.0.0.1:{httpd.server_port}/chat/completions")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-secret")
    monkeypatch.setenv("DEEPSEEK_MODEL", "test/model")
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    yield state
    httpd.shutdown()
    httpd.server_close()
    thread.join()


def test_stream_and_request_contract(server):
    """Verify endpoint, bearer authentication, selected model, and Unicode."""
    assert "".join(client.ask_deepseek_stream("test prompt")) == "你好，同学"
    path, auth, body = server["requests"][0]
    assert path == "/chat/completions"
    assert auth == "Bearer test-secret"
    assert body == {"model": "test/model", "messages": [{"role": "user", "content": "test prompt"}], "stream": True}


def test_missing_key(monkeypatch):
    """Missing credentials must fail before making a network request."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    assert "DEEPSEEK_API_KEY" in "".join(client.ask_deepseek_stream("test"))


@pytest.mark.parametrize("status", [400, 401, 402, 403, 404, 429, 500])
def test_http_errors_are_safe(server, status):
    """Do not expose an upstream body that could contain credentials."""
    server["status"] = status
    server["events"] = ["test-secret"]
    reply = "".join(client.ask_deepseek_stream("test"))
    assert str(status) in reply
    assert "test-secret" not in reply


@pytest.mark.parametrize("events", [["data: not-json"], ['data: {"error":{"message":"test-secret"}}'], ["data: [DONE]"], ['data: {"choices":[{"delta":{"content":"partial"}}]}']])
def test_bad_or_incomplete_stream(server, events):
    """Malformed, empty, failed, and truncated streams report safe errors."""
    server["events"] = events
    reply = "".join(client.ask_deepseek_stream("test"))
    assert "❌" in reply
    assert "test-secret" not in reply


def test_default_model(server, monkeypatch):
    """Blank configuration selects the documented DeepSeek Flash default."""
    monkeypatch.setenv("DEEPSEEK_MODEL", " ")
    list(client.ask_deepseek_stream("test"))
    assert server["requests"][0][2]["model"] == client.DEFAULT_MODEL


def test_attendance_journey(tmp_path):
    """Click start/end and verify persisted events and button states."""
    log = tmp_path / "attendance.log"
    start, end, label = create_session_widgets(str(log)).children
    assert end.disabled
    start.click()
    assert start.disabled and not end.disabled
    end.click()
    assert end.disabled and "已结束" in label.value
    assert log.read_text(encoding="utf-8").count("Session started") == 1
    assert log.read_text(encoding="utf-8").count("Session ended") == 1


@pytest.mark.parametrize("question", ["2.1", "2.2", "2.3"])
def test_tutor_send_button_journey(server, monkeypatch, tmp_path, question):
    """Open each real exercise, submit input, stream feedback, and log it."""
    import projects.problem_ai_helper as helper

    monkeypatch.setattr(helper, "LOG_FILE", str(tmp_path / "dialog.log"))
    assert set(load_problems()) == {"2.1", "2.2", "2.3"}
    chat = ThinkingAIChat(question)
    chat.input_box.value = "我想先明确每个状态的含义。"
    chat.send_button.click()
    assert chat.input_box.value == ""
    assert chat.messages[-1] == ("assistant", "你好，同学")
    assert "你好，同学" in chat.chat_history.value
    assert "你好，同学" in (tmp_path / "dialog.log").read_text(encoding="utf-8")
    assert "有限自动机" in server["requests"][0][2]["messages"][0]["content"]


def test_code_tutor_journey(server, monkeypatch, tmp_path):
    """Exercise the second tutor with fixture resources absent from this course."""
    import projects.code_ai_helper as helper

    (tmp_path / 'code_problems.md').write_text('''# Exercises

## sample
title: Sample
aux_file: aux.cpp
ex_file: main.cpp
compile_log: compile.log
run_log: run.log
task_desc: Complete the transition.
reference:
  - Track the current state.
''', encoding='utf-8')
    (tmp_path / 'main.cpp').write_text('// TODO: transition', encoding='utf-8')
    monkeypatch.setattr(helper, 'PROJECT_DIR', str(tmp_path))
    chat = helper.AIChat('sample')
    assert chat.messages[-1] == ('assistant', '你好，同学')
    chat.input_box.value = 'Please give a hint.'
    chat.send_button.click()
    assert chat.messages[-1] == ('assistant', '你好，同学')
    assert len(server['requests']) == 2
    assert '// TODO: transition' in server['requests'][-1][2]['messages'][0]['content']
    assert '你好，同学' in (tmp_path / 'fa.log').read_text(encoding='utf-8')


def test_deepseek_endpoint_and_model():
    """Pin the official endpoint and V4.1-Flash API identifier."""
    assert client.API_URL == 'https://api.deepseek.com/chat/completions'
    assert client.DEFAULT_MODEL == 'deepseek-flash'


def test_previous_key_is_not_used(monkeypatch):
    """Do not silently authenticate with the previous provider's key."""
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    monkeypatch.setenv('OPENROUTER_API_KEY', 'old-provider-secret')
    reply = ''.join(client.ask_deepseek_stream('test'))
    assert 'DEEPSEEK_API_KEY' in reply
    assert 'old-provider-secret' not in reply


def test_reasoning_frames_are_not_displayed(server):
    """Render only the final answer, not model reasoning or usage frames."""
    server['events'] = [
        ': keepalive',
        'data: {"choices":[{"delta":{"reasoning_content":"private reasoning"}}]}',
        'data: {"choices":[{"delta":{"content":"你好"}}]}',
        'data: {"choices":[],"usage":{"total_tokens":10}}',
        'data: [DONE]',
    ]
    assert ''.join(client.ask_deepseek_stream('test')) == '你好'


def test_compatibility_import_uses_deepseek(server):
    """The previous Python callable delegates exclusively to DeepSeek."""
    from projects.openrouter_client import ask_openrouter_stream

    assert ask_openrouter_stream is client.ask_deepseek_stream
    assert ''.join(ask_openrouter_stream('test')) == '你好，同学'
