# Rollback Playbook

- If canary fails SLO, auto-rollback triggers.
- If manual rollback needed: `kubectl rollout undo deployment/<name> -n <ns>`.
