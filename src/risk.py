from dataclasses import dataclass
from typing import Any, Dict, List
from .config import ENV_POLICY_DEV, ENV_POLICY_QA, ENV_POLICY_PROD

@dataclass
class Risk:
    score: int
    level: str
    reasons: List[str]

def _posture(env: str) -> str:
    return {"dev": ENV_POLICY_DEV, "qa": ENV_POLICY_QA, "prod": ENV_POLICY_PROD}.get(env, "balanced")

def score(req: Dict[str, Any]) -> Risk:
    reasons: List[str] = []
    s = 0
    env = req.get("env", "dev")
    posture = _posture(env)

    # Base by env
    if env == "prod":
        s += 25; reasons.append("prod_target")
    elif env == "qa":
        s += 10; reasons.append("qa_target")
    else:
        s += 2; reasons.append("dev_target")

    diff = (req.get("diff_summary") or "").lower()
    if any(k in diff for k in ["secret", "token", "key", "password"]):
        s += 25; reasons.append("sensitive_config_change")
    if any(k in diff for k in ["migration", "schema", "ddl"]):
        s += 20; reasons.append("data_migration")
    if any(k in diff for k in ["hpa", "replica", "autoscale"]):
        s += 10; reasons.append("scaling_change")
    if any(k in diff for k in ["networkpolicy", "ingress", "gateway"]):
        s += 12; reasons.append("network_surface_change")

    m = req.get("metrics_snapshot") or {}
    if float(m.get("error_rate", 0)) > 0.01:
        s += 20; reasons.append("elevated_error_rate")
    if float(m.get("p95_ms", 0)) > 500:
        s += 15; reasons.append("latency_regression_risk")

    # Posture modifies threshold perception
    if posture == "strict":
        s += 8; reasons.append("strict_env_posture")
    elif posture == "lenient":
        s -= 5; reasons.append("lenient_env_posture")

    level = "low" if s < 25 else "medium" if s < 55 else "high"
    return Risk(score=max(0, s), level=level, reasons=reasons)
