from typing import Any, Dict, List
import time

# In real pipelines, collect from: GitHub API, Argo, Prometheus, PagerDuty, etc.
# This starter returns a structured payload to show "impact" across dev/qa/prod.
def collect(service: str, env: str, change_id: str, sources: List[str]) -> Dict[str, Any]:
    evidence: Dict[str, Any] = {
        "service": service,
        "env": env,
        "change_id": change_id,
        "collected_at": int(time.time()),
        "sources": sources,
        "git": {"commit": change_id[:12], "files_changed": 12, "risk_keywords": ["hpa","env"]} if "git" in sources else None,
        "metrics": {"error_rate": 0.002, "p95_ms": 180, "slo_ok": True} if "metrics" in sources else None,
        "incidents": {"open_incidents": 0, "recent_incidents_7d": 1} if "incidents" in sources else None,
    }
    return evidence
