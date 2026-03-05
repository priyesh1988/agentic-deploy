from typing import Any, Dict, List, Tuple

# Tiny built-in policy checks (no external OPA dependency in this starter)
# You can replace this with real OPA/Conftest later.
def eval_policies(env: str, manifests: List[Dict[str, Any]], rules: List[str] | None = None) -> Tuple[bool, List[str]]:
    deny_reasons: List[str] = []

    for m in manifests or []:
        kind = (m.get("kind") or "").lower()
        spec = m.get("spec") or {}
        # Example: prod requires probes + resource limits
        if env == "prod" and kind == "deployment":
            tpl = ((spec.get("template") or {}).get("spec") or {})
            containers = tpl.get("containers") or []
            for c in containers:
                if not c.get("readinessProbe"):
                    deny_reasons.append("prod_requires_readinessProbe")
                res = c.get("resources") or {}
                lim = res.get("limits") or {}
                if not lim:
                    deny_reasons.append("prod_requires_resource_limits")

        # Example: deny privileged anywhere
        if kind == "deployment":
            tpl = ((spec.get("template") or {}).get("spec") or {})
            containers = tpl.get("containers") or []
            for c in containers:
                sc = c.get("securityContext") or {}
                if sc.get("privileged") is True:
                    deny_reasons.append("privileged_container_denied")

    # Optional additional rule strings for demo impact
    for r in rules or []:
        if r == "deny_all_prod" and env == "prod":
            deny_reasons.append("rule:deny_all_prod")

    allowed = len(deny_reasons) == 0
    return allowed, deny_reasons
