from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List
from .models import (
    EvaluateReq, EvidenceReq, ApprovalReq, AskReq,
    MetricsIngestReq, PolicyEvalReq, DeployStatusResp
)
from .agent import decide, plan
from .audit import write, read_last
from .evidence import collect
from .approvals import set_decision, get_decision
from .policy import eval_policies
from .llm import AnthropicLLM
from .config import MODE

router = APIRouter()

# --- 1) health ---
@router.get("/health")
def health():
    return {"ok": True}

# --- 2) version ---
@router.get("/version")
def version():
    return {"name": "agentic-deploy-anthropic", "version": "0.2.0", "mode": MODE}

# --- 3) environment status (dev/qa/prod impact) ---
@router.get("/v1/envs/{env}/status", response_model=DeployStatusResp)
def env_status(env: str):
    if env not in ("dev", "qa", "prod"):
        raise HTTPException(400, "env must be dev|qa|prod")
    posture = {"dev": "lenient", "qa": "balanced", "prod": "strict"}[env]
    gate_open = True if env in ("dev", "qa") else True
    notes = [
        f"{env} posture={posture}",
        "prod uses stricter policies (probes/limits) and higher risk sensitivity",
    ]
    return {"env": env, "posture": posture, "gate_open": gate_open, "notes": notes}

# --- 4) evidence collection ---
@router.post("/v1/evidence/collect")
def evidence_collect(req: EvidenceReq):
    ev = collect(req.service, req.env, req.change_id, req.sources)
    audit_id = write({"type": "evidence.collect", "evidence": ev})
    return {
        "evidence": ev,
        "audit_id": audit_id,
        "meaning": "Collected deploy evidence for the agent to reason on.",
    }

# --- 5) metrics ingest ---
@router.post("/v1/metrics/ingest")
def metrics_ingest(req: MetricsIngestReq):
    audit_id = write({"type": "metrics.ingest", **req.model_dump()})
    return {
        "ok": True,
        "audit_id": audit_id,
        "meaning": "Captured a metrics snapshot used for risk scoring.",
    }

# --- 6) policy eval ---
@router.post("/v1/policy/eval")
def policy_eval(req: PolicyEvalReq):
    allowed, denies = eval_policies(req.env, req.manifests, req.rules)
    audit_id = write(
        {"type": "policy.eval", "env": req.env, "allowed": allowed, "deny_reasons": denies}
    )
    return {
        "allowed": allowed,
        "deny_reasons": denies,
        "audit_id": audit_id,
        "meaning": "Policy guardrails for the target environment.",
    }

# --- 7) evaluate (core) ---
@router.post("/v1/evaluate")
def evaluate(req: EvaluateReq):
    # Convert manifest refs into "raw" placeholders (demo)
    req_dict = req.model_dump()
    req_dict["manifests_raw"] = [
        {"kind": m.kind, "metadata": {"name": m.name, "namespace": m.namespace}}
        for m in req.manifests
    ]

    d = decide(req_dict)
    decision = d["decision"]
    p = plan(decision, req.strategy_preference)

    audit_id = write(
        {
            "type": "evaluate",
            "service": req.service,
            "env": req.env,
            "change_id": req.change_id,
            "decision": decision,
            "risk": {"score": d["risk"].score, "level": d["risk"].level, "reasons": d["risk"].reasons},
            "policy": d.get("policy"),
            "plan": p,
        }
    )

    return {
        "decision": decision,
        "risk": {"score": d["risk"].score, "level": d["risk"].level, "reasons": d["risk"].reasons},
        "policy": d.get("policy"),
        "plan": p,
        "audit_id": audit_id,
        "meaning": "Single source of truth: risk + policy + rollout plan for dev/qa/prod.",
    }

# --- 8) plan only ---
@router.post("/v1/plan")
def plan_only(req: EvaluateReq):
    d = decide(req.model_dump())
    p = plan(d["decision"], req.strategy_preference)
    audit_id = write(
        {
            "type": "plan",
            "decision": d["decision"],
            "plan": p,
            "env": req.env,
            "service": req.service,
        }
    )
    return {
        "plan": p,
        "audit_id": audit_id,
        "meaning": "Returns a rollout plan (canary/blue-green/rolling) matched to risk.",
    }

# --- 9) approvals ---
@router.post("/v1/approve")
def approve(req: ApprovalReq):
    set_decision(req.audit_id, req.approver, req.decision)
    audit_id = write(
        {
            "type": "approval",
            "audit_id": req.audit_id,
            "approver": req.approver,
            "decision": req.decision,
        }
    )
    return {
        "ok": True,
        "audit_id": audit_id,
        "meaning": "Records a human approval/denial for high-risk changes.",
    }

# --- 10) decision lookup ---
@router.get("/v1/decisions/{audit_id}")
def decision_lookup(audit_id: str):
    d = get_decision(audit_id)
    if not d:
        raise HTTPException(404, "no approval decision recorded for this audit_id")
    return {
        "audit_id": audit_id,
        "approval": d,
        "meaning": "Fetches the human gate decision used to proceed/rollback.",
    }

# --- 11) audit tail ---
@router.get("/v1/audit/tail")
def audit_tail():
    return {
        "events": read_last(100),
        "meaning": "Last 100 audit events (evidence, policy, evaluate, approvals).",
    }

# --- 12) ChatOps ask (Anthropic everywhere) ---
@router.post("/v1/chatops/ask")
async def chatops_ask(req: AskReq):
    llm = AnthropicLLM()
    schema_hint: Dict[str, Any] = {
        "answer": "(string)",
        "actions": ["(optional list of recommended next actions)"],
        "confidence": 0.7,
    }
    system = "You are an Anthropic-powered deployment assistant. Answer with a single JSON object."
    user = f"""Question: {req.question}
Environment: {req.env}
Context: {req.context}

Return JSON with keys: answer, actions, confidence."""
    out = await llm.complete_json(system=system, user=user, schema_hint=schema_hint)
    audit_id = write({"type": "chatops.ask", "env": req.env, "question": req.question, "result": out})
    return {
        "result": out,
        "audit_id": audit_id,
        "meaning": "Anthropic-assisted guidance for deploy decisions and next steps.",
    }
