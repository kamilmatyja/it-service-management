---
lab6_change:
  id: "change-1795693935"
  candidate: "itsmlab.local/lab6-candidate:a9083dd357af"
  stable: "ghcr.io/swasik/svcdesk-v2-seeded:2.0.0"
  strategy: "canary"
  change_type: "normal"
  risk: "medium"
  rollback_plan: "Reset Caddy upstream weights to 100% stable and 0% canary, then stop the canary container."
  started: "2026-11-26T11:52:04Z"
  finished: "2026-11-26T11:52:15Z"
  outcome: "rolled-back"
  reason: "Rollback triggered by automated analysis gate: Availability SLI violated: ERR_SLI: Error share 0.4904 exceeded threshold 0.144"
  actions:
    - at: "2026-11-26T11:52:04Z"
      action: "Read deployment configuration and pre-approved release plan"
      autonomy: "approve-then-act"
      approval: "CAB pre-approval CAB-2026-L6-CANARY"
    - at: "2026-11-26T11:52:05Z"
      action: "Start svcdesk-canary container with candidate image"
      autonomy: "closed-loop"
    - at: "2026-11-26T11:52:05Z"
      action: "Set canary routing weight to 10% (stable: 90%)"
      autonomy: "closed-loop"
    - at: "2026-11-26T11:52:10Z"
      action: "Read Prometheus metrics for canary track at step weight 10%"
      autonomy: "read-only"
    - at: "2026-11-26T11:52:15Z"
      action: "Read Prometheus metrics for canary track at step weight 10%"
      autonomy: "read-only"
    - at: "2026-11-26T11:52:15Z"
      action: "Gate check failed: rollback weights to 100% stable, 0% canary"
      autonomy: "closed-loop"
---
# Change Record: Canary Deployment of itsmlab.local/lab6-candidate:a9083dd357af

## Outcome: rolled-back
Reason: Rollback triggered by automated analysis gate: Availability SLI violated: ERR_SLI: Error share 0.4904 exceeded threshold 0.144

## Autonomy & Execution
This change was executed by an automated deployment gate following the progressive delivery schedule.
