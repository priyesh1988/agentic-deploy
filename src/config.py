import os

PORT = int(os.getenv("PORT", "8080"))
MODE = os.getenv("MODE", "anthropic")  # anthropic|rules_only

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

AUDIT_PATH = os.getenv("AUDIT_PATH", "/data/audit.jsonl")

# Environment posture (used by the gate)
ENV_POLICY_DEV = os.getenv("ENV_POLICY_DEV", "lenient")    # lenient|balanced|strict
ENV_POLICY_QA = os.getenv("ENV_POLICY_QA", "balanced")
ENV_POLICY_PROD = os.getenv("ENV_POLICY_PROD", "strict")
