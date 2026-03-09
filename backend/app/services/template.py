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
        matches = TOKEN_RE.findall(value)
        if not matches:
            return value

        if len(matches) == 1 and value.strip() == f"{{{{{matches[0]}}}}}":
            resolved = resolve_path(context, matches[0].strip())
            return value if resolved is None else resolved

        rendered = value
        for token in matches:
            resolved = resolve_path(context, token.strip())
            replacement = "" if resolved is None else str(resolved)
            rendered = rendered.replace(f"{{{{{token}}}}}", replacement)
        return rendered

    if isinstance(value, list):
        return [render_value(item, context) for item in value]
    if isinstance(value, dict):
        return {key: render_value(item, context) for key, item in value.items()}
    return value
