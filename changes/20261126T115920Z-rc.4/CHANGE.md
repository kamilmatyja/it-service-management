---
lab6_change:
  id: "change-1795694372"
  candidate: "itsmlab.local/lab6-candidate:c58b65121406"
  stable: "ghcr.io/swasik/svcdesk-v2-seeded:2.0.0"
  strategy: "canary"
  change_type: "normal"
  risk: "medium"
  rollback_plan: "Reset Caddy upstream weights to 100% stable and 0% canary, then stop the canary container."
  started: "2026-11-26T11:59:20Z"
  finished: "2026-11-26T11:59:32Z"
  outcome: "rolled-back"
  reason: "Rollback triggered by automated analysis gate: Availability SLI violated: ERR_SLI: Error share 0.3476 exceeded threshold 0.144"
  actions:
    - at: "2026-11-26T11:59:20Z"
      action: "Read deployment configuration and pre-approved release plan"
      autonomy: "approve-then-act"
      approval: "CAB pre-approval CAB-2026-L6-CANARY"
    - at: "2026-11-26T11:59:21Z"
      action: "Start svcdesk-canary container with candidate image"
      autonomy: "closed-loop"
    - at: "2026-11-26T11:59:21Z"
      action: "Set canary routing weight to 10% (stable: 90%)"
      autonomy: "closed-loop"
    - at: "2026-11-26T11:59:26Z"
      action: "Read Prometheus metrics for canary track at step weight 10%"
      autonomy: "read-only"
    - at: "2026-11-26T11:59:32Z"
      action: "Read Prometheus metrics for canary track at step weight 10%"
      autonomy: "read-only"
    - at: "2026-11-26T11:59:32Z"
      action: "Gate check failed: rollback weights to 100% stable, 0% canary"
      autonomy: "closed-loop"
---
# Change Record: Canary Deployment of itsmlab.local/lab6-candidate:c58b65121406

## Outcome: rolled-back
Reason: Rollback triggered by automated analysis gate: Availability SLI violated: ERR_SLI: Error share 0.3476 exceeded threshold 0.144

## Autonomy & Execution
This change was executed by an automated deployment gate following the progressive delivery schedule.
