
import json, re
from datetime import datetime, timezone

def load_json(path: str):
    with open(path, "r") as f:
        return json.load(f)

def idx_by(items, key):
    return {it[key]: it for it in items}

def parse_iso(s: str):
    try:
        return datetime.fromisoformat(s.replace("Z","+00:00"))
    except Exception:
        return None

def hours_until(now, future_dt):
    if not now or not future_dt:
        return None
    delta = future_dt - now
    return delta.total_seconds() / 3600.0

def deep_get(obj, key_path):
    """
    Very small helper: supports dot-separated paths across dicts.
    """
    cur = obj
    for part in key_path.split("."):
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur

def render_template(tpl: str, data: dict) -> str:
    if not tpl:
        return ""
    out = tpl
    for k, v in data.items():
        out = out.replace("{{"+k+"}}", str(v))
    return out
