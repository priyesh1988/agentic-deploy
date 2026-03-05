from typing import Any, Dict
from .risk import score
from .policy import eval_policies

def decide(req: Dict[str, Any]) -> Dict[str, Any]:
    env = req.get("env", "dev")
    manifests = req.get("manifests_raw") or req.get("manifests") or []
    policy_allowed, policy_denies = eval_policies(env, manifests, req.get("policy_rules"))

    r = score(req)

    # Hard deny if policy fails
    if not policy_allowed:
        return {
            "decision": "deny",
            "risk": r,
            "policy": {"allowed": False, "deny_reasons": policy_denies},
        }

    if r.level == "high":
        return {"decision": "requires_approval", "risk": r, "policy": {"allowed": True, "deny_reasons": []}}
    if r.level == "medium":
        return {"decision": "approve_with_canary", "risk": r, "policy": {"allowed": True, "deny_reasons": []}}
    return {"decision": "approve", "risk": r, "policy": {"allowed": True, "deny_reasons": []}}

def plan(decision: str, pref: str = "canary") -> Dict[str, Any]:
    if decision in ("approve_with_canary",) or pref == "canary":
        return {"type":"canary","steps":["10% 5m","25% 10m","50% 15m","100%"],"rollback":"auto_on_slo_breach"}
    if pref == "blue_green":
        return {"type":"blue_green","steps":["deploy_green","smoke_test","switch_traffic"],"rollback":"switch_back"}
    return {"type":"rolling","steps":["rollingUpdate"],"rollback":"manual"}
