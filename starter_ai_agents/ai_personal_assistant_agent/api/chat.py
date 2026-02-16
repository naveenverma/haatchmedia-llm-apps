"""Vercel serverless API for the AI Personal Assistant. POST /api/chat with JSON body."""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Ensure app is importable (project root = agent directory for Vercel)
_AGENT_ROOT = Path(__file__).resolve().parent.parent
if str(_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_AGENT_ROOT))
os.chdir(_AGENT_ROOT)

# Lazy-initialized agent (reused across warm invocations)
_agent = None


def _get_agent():
    global _agent
    if _agent is None:
        from app.agent import build_agent_executor
        from app.config import get_settings
        from app.model_factory import build_chat_model
        from app.storage import StateStore
        from app.tools import build_tools

        settings = get_settings()
        # Use /tmp on Vercel for ephemeral state (or ASSISTANT_DATA_FILE env)
        data_file = os.getenv("ASSISTANT_DATA_FILE", "/tmp/assistant_state.json")
        store = StateStore(data_file)
        tools = build_tools(store)
        llm, _, _ = build_chat_model(
            provider=settings.llm_provider,
            explicit_model_name=settings.model_name,
            enable_web_refresh=False,  # Skip web refresh on serverless
            nvidia_base_url=settings.nvidia_base_url if settings.llm_provider == "nvidia" else None,
            nvidia_api_key=settings.nvidia_api_key if settings.llm_provider == "nvidia" else None,
        )
        # Code evolution disabled on Vercel (read-only filesystem)
        _agent = build_agent_executor(llm=llm, tools=tools, controller_mode=False)
    return _agent


def _invoke_agent(message: str, chat_history: list) -> str:
    from langchain_core.messages import AIMessage, HumanMessage
    from langchain_core.messages.base import BaseMessage

    agent = _get_agent()
    messages: list[BaseMessage] = []
    for h in chat_history:
        if h.get("role") == "user":
            messages.append(HumanMessage(content=h.get("content", "")))
        elif h.get("role") == "assistant":
            messages.append(AIMessage(content=h.get("content", "")))
    messages.append(HumanMessage(content=message))

    result = agent.invoke({"messages": messages})
    out_messages = result["messages"]
    output = ""
    for m in reversed(out_messages):
        if isinstance(m, AIMessage) and m.content:
            output = m.content
            break
    return output or (str(out_messages[-1]) if out_messages else "No response.")


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
            data = json.loads(body) if body.strip() else {}
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        message = data.get("message", "").strip()
        if not message:
            self._send_json(400, {"error": "message is required"})
            return

        chat_history = data.get("chat_history", [])

        try:
            response = _invoke_agent(message, chat_history)
            self._send_json(200, {"response": response})
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status: int, data: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))
