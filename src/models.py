from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional

Env = Literal["dev", "qa", "prod"]

class ManifestRef(BaseModel):
    kind: str
    name: str
    namespace: str

class EvaluateReq(BaseModel):
    service: str
    env: Env
    change_id: str
    diff_summary: str = ""
    manifests: List[ManifestRef] = []
    metrics_snapshot: Dict[str, Any] = {}
    strategy_preference: Literal["canary", "blue_green", "rolling"] = "canary"

class EvidenceReq(BaseModel):
    service: str
    env: Env
    change_id: str
    sources: List[Literal["git", "manifests", "metrics", "incidents"]] = ["git","manifests","metrics"]

class ApprovalReq(BaseModel):
    audit_id: str
    approver: str = Field(min_length=2)
    decision: Literal["approve", "deny"]

class AskReq(BaseModel):
    env: Env
    question: str
    context: Dict[str, Any] = {}

class MetricsIngestReq(BaseModel):
    env: Env
    service: str
    error_rate: float = 0.0
    p95_ms: float = 0.0
    cpu_pct: float = 0.0
    mem_pct: float = 0.0

class PolicyEvalReq(BaseModel):
    env: Env
    rules: List[str] = []
    manifests: List[Dict[str, Any]] = []

class DeployStatusResp(BaseModel):
    env: Env
    posture: str
    gate_open: bool
    notes: List[str] = []
