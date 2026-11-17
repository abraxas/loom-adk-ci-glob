#!/usr/bin/env python3
"""In-process oracle for the v1.9.0 ADK code-interpreter name miss.

Imports product ApprovalPolicyMatcher. Reads FunctionTool names from the
product file. Does not import code_interpreter.py (that module pulls the
sandbox client). Matching is only find_matching_policy.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import logging
import os
import sys
import types
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

LABEL = "LOOM-190-ADK-CI-GLOB"
BIND = os.environ.get("LAB_BIND", "0.0.0.0")
PORT = int(os.environ.get("LAB_PORT", "18750"))
ADK_ROOT = Path(os.environ.get("ADK_ROOT", "/opt/adk_agent"))
STRANDS_ROOT = Path(os.environ.get("STRANDS_ROOT", "/opt/strands_agent"))
APPROVAL_PY = ADK_ROOT / "src" / "integrations" / "approval.py"
CI_PY = ADK_ROOT / "src" / "integrations" / "code_interpreter.py"
STRANDS_AGENT_PY = STRANDS_ROOT / "src" / "agent.py"
MATCHER_ID = "src.integrations.approval.ApprovalPolicyMatcher"
MAX_BODY = 4096

logger = logging.getLogger(LABEL)


def _install_adk_stubs() -> None:
    """approval.py imports these two types and does not need google-adk."""
    google = types.ModuleType("google")
    adk = types.ModuleType("google.adk")
    tools = types.ModuleType("google.adk.tools")
    base_tool = types.ModuleType("google.adk.tools.base_tool")
    tool_context = types.ModuleType("google.adk.tools.tool_context")

    class BaseTool:
        name = ""

    class ToolContext:
        def __init__(self) -> None:
            self.state: dict[str, Any] = {}
            self.tool_confirmation = None

    base_tool.BaseTool = BaseTool
    tool_context.ToolContext = ToolContext
    sys.modules["google"] = google
    sys.modules["google.adk"] = adk
    sys.modules["google.adk.tools"] = tools
    sys.modules["google.adk.tools.base_tool"] = base_tool
    sys.modules["google.adk.tools.tool_context"] = tool_context


def function_tool_names(source: str) -> list[str]:
    tree = ast.parse(source)
    names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Name) or func.id != "FunctionTool":
            continue
        if not node.args or not isinstance(node.args[0], ast.Name):
            continue
        names.append(node.args[0].id)
    return names


def strands_ci_tools(source: str) -> list[str]:
    tree = ast.parse(source)
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "append":
            continue
        if not isinstance(func.value, ast.Name) or func.value.id != "tools":
            continue
        if not node.args or not isinstance(node.args[0], ast.Attribute):
            continue
        arg = node.args[0]
        if isinstance(arg.value, ast.Name) and arg.value.id == "ci":
            found.append(arg.attr)
    return found


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _method1(rules: list[str]) -> dict[str, Any]:
    return {
        "name": "method-1",
        "enabled": True,
        "policy_type": "loop_hook",
        "approval_mode": "require_approval",
        "tool_match_rules": list(rules),
        "agent_scope": {"type": "all"},
    }


_install_adk_stubs()
sys.path.insert(0, str(ADK_ROOT))

from src.integrations.approval import ApprovalPolicyMatcher  # noqa: E402

_MATCHER_FILE = inspect.getsourcefile(ApprovalPolicyMatcher) or ""
if not _MATCHER_FILE.endswith("/src/integrations/approval.py"):
    raise SystemExit(f"{LABEL} matcher-file-unexpected")
if f"{ApprovalPolicyMatcher.__module__}.{ApprovalPolicyMatcher.__qualname__}" != MATCHER_ID:
    raise SystemExit(f"{LABEL} matcher-id-unexpected")

_APPROVAL_SHA = _sha256(APPROVAL_PY)
_CI_SHA = _sha256(CI_PY)
_STRANDS_SHA = _sha256(STRANDS_AGENT_PY)
_CI_SOURCE = CI_PY.read_text(encoding="utf-8")
_STRANDS_SOURCE = STRANDS_AGENT_PY.read_text(encoding="utf-8")
_APPROVAL_SOURCE = APPROVAL_PY.read_text(encoding="utf-8")
_FUNCTION_TOOLS = function_tool_names(_CI_SOURCE)
_STRANDS_TOOLS = strands_ci_tools(_STRANDS_SOURCE)


def health() -> dict[str, Any]:
    return {
        "ok": True,
        "matcher": MATCHER_ID,
        "matcher_file": "src/integrations/approval.py",
        "product_fnmatch": "fnmatch.fnmatch" in _APPROVAL_SOURCE,
        "approval_sha256": _APPROVAL_SHA,
        "code_interpreter_sha256": _CI_SHA,
        "strands_agent_sha256": _STRANDS_SHA,
        "function_tools": _FUNCTION_TOOLS,
        "strands_tools": _STRANDS_TOOLS,
    }


def match_tool(tool_name: str, rules: list[str]) -> bool:
    policy = _method1(rules)
    found = ApprovalPolicyMatcher(policies=[policy]).find_matching_policy(tool_name)
    return found is not None


def _parse_match(body: dict[str, Any]) -> tuple[str, list[str]] | None:
    tool_name = body.get("tool_name")
    rules = body.get("tool_match_rules")
    if not isinstance(tool_name, str) or not tool_name or len(tool_name) > 200:
        return None
    if not isinstance(rules, list) or len(rules) > 8:
        return None
    if any(not isinstance(item, str) or len(item) > 200 for item in rules):
        return None
    return tool_name, rules


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "loom-lab"

    def log_message(self, fmt: str, *args: object) -> None:
        logger.info("%s %s", self.address_string(), fmt % args)

    def _send(self, code: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            self._send(200, health())
            return
        self._send(404, {"ok": False, "error": "not-found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/match":
            self._send(404, {"ok": False, "error": "not-found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send(400, {"ok": False, "error": "bad-length"})
            return
        if length <= 0 or length > MAX_BODY:
            self._send(400, {"ok": False, "error": "bad-length"})
            return
        try:
            body = json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            self._send(400, {"ok": False, "error": "bad-json"})
            return
        if not isinstance(body, dict):
            self._send(400, {"ok": False, "error": "bad-json"})
            return
        parsed = _parse_match(body)
        if parsed is None:
            self._send(400, {"ok": False, "error": "bad-match"})
            return
        tool_name, rules = parsed
        matched = match_tool(tool_name, rules)
        logger.info("match tool=%s rules=%s matched=%s", tool_name, rules, matched)
        self._send(
            200,
            {
                "ok": True,
                "matched": matched,
                "tool_name": tool_name,
                "tool_match_rules": rules,
                "policy_type": "loop_hook",
                "approval_mode": "require_approval",
                "matcher": MATCHER_ID,
            },
        )


class ReuseServer(ThreadingHTTPServer):
    allow_reuse_address = True


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    server = ReuseServer((BIND, PORT), Handler)
    logger.info("listening %s:%s matcher=%s tools=%s", BIND, PORT, MATCHER_ID, _FUNCTION_TOOLS)
    server.serve_forever()


if __name__ == "__main__":
    main()
