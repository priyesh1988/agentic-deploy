from typing import Dict, Any

# Starter in-memory approvals (replace with DB/Slack/Jira)
_APPROVALS: Dict[str, Dict[str, Any]] = {}

def set_decision(audit_id: str, approver: str, decision: str):
    _APPROVALS[audit_id] = {"approver": approver, "decision": decision}

def get_decision(audit_id: str):
    return _APPROVALS.get(audit_id)
