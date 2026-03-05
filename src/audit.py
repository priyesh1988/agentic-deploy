import json, time, uuid
from typing import Any, Dict
from .config import AUDIT_PATH

def write(event: Dict[str, Any]) -> str:
    audit_id = f"audit_{uuid.uuid4().hex[:18]}"
    record = {"audit_id": audit_id, "ts": int(time.time()), **event}
    # Ensure directory exists
    import os
    os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return audit_id

def read_last(n: int = 200):
    try:
        with open(AUDIT_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()[-n:]
        return [json.loads(x) for x in lines]
    except FileNotFoundError:
        return []
