from __future__ import annotations

import re
from typing import Any

TOKEN_RE = re.compile(r"{{\s*([^{}]+?)\s*}}")


def resolve_path(context: dict[str, Any], path: str) -> Any:
    current: Any = context
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def render_value(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, str):
        if not TOKEN_RE.search(value):
            return value

        exact_token = TOKEN_RE.fullmatch(value.strip())
        if exact_token:
            resolved = resolve_path(context, exact_token.group(1).strip())
            return value if resolved is None else resolved

        def _replace_token(match: re.Match[str]) -> str:
            resolved = resolve_path(context, match.group(1).strip())
            return "" if resolved is None else str(resolved)

        return TOKEN_RE.sub(_replace_token, value)

    if isinstance(value, list):
        return [render_value(item, context) for item in value]
    if isinstance(value, dict):
        return {key: render_value(item, context) for key, item in value.items()}
    return value
