---
lab6_change:
  id: "change-1795694306"
  candidate: "itsmlab.local/lab6-candidate:ac1b80756802"
  stable: "ghcr.io/swasik/svcdesk-v2-seeded:2.0.0"
  strategy: "canary"
  change_type: "normal"
  risk: "medium"
  rollback_plan: "Reset Caddy upstream weights to 100% stable and 0% canary, then stop the canary container."
  started: "2026-11-26T11:58:15Z"
  finished: "2026-11-26T11:58:26Z"
  outcome: "rolled-back"
  reason: "Rollback triggered by automated analysis gate: Latency SLI violated: LAT_SLI: Slow share 0.5762 exceeded threshold 0.144"
  actions:
    - at: "2026-11-26T11:58:15Z"
      action: "Read deployment configuration and pre-approved release plan"
      autonomy: "approve-then-act"
      approval: "CAB pre-approval CAB-2026-L6-CANARY"
    - at: "2026-11-26T11:58:16Z"
      action: "Start svcdesk-canary container with candidate image"
      autonomy: "closed-loop"
    - at: "2026-11-26T11:58:16Z"
      action: "Set canary routing weight to 10% (stable: 90%)"
      autonomy: "closed-loop"
    - at: "2026-11-26T11:58:21Z"
      action: "Read Prometheus metrics for canary track at step weight 10%"
      autonomy: "read-only"
    - at: "2026-11-26T11:58:26Z"
      action: "Read Prometheus metrics for canary track at step weight 10%"
      autonomy: "read-only"
    - at: "2026-11-26T11:58:26Z"
      action: "Gate check failed: rollback weights to 100% stable, 0% canary"
      autonomy: "closed-loop"
---
# Change Record: Canary Deployment of itsmlab.local/lab6-candidate:ac1b80756802

## Outcome: rolled-back
Reason: Rollback triggered by automated analysis gate: Latency SLI violated: LAT_SLI: Slow share 0.5762 exceeded threshold 0.144

## Autonomy & Execution
This change was executed by an automated deployment gate following the progressive delivery schedule.
