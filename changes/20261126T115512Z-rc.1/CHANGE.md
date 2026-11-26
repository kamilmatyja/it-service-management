---
lab6_change:
  id: "change-1795694133"
  candidate: "itsmlab.local/lab6-candidate:f16e6700e6e0"
  stable: "ghcr.io/swasik/svcdesk-v2-seeded:2.0.0"
  strategy: "canary"
  change_type: "normal"
  risk: "medium"
  rollback_plan: "Reset Caddy upstream weights to 100% stable and 0% canary, then stop the canary container."
  started: "2026-11-26T11:55:12Z"
  finished: "2026-11-26T11:55:33Z"
  outcome: "rolled-back"
  reason: "Rollback triggered by automated analysis gate: Hang detected: HANG: Canary completed only 0.0 requests while stable completed 363.75 requests"
  actions:
    - at: "2026-11-26T11:55:12Z"
      action: "Read deployment configuration and pre-approved release plan"
      autonomy: "approve-then-act"
      approval: "CAB pre-approval CAB-2026-L6-CANARY"
    - at: "2026-11-26T11:55:13Z"
      action: "Start svcdesk-canary container with candidate image"
      autonomy: "closed-loop"
    - at: "2026-11-26T11:55:13Z"
      action: "Set canary routing weight to 10% (stable: 90%)"
      autonomy: "closed-loop"
    - at: "2026-11-26T11:55:18Z"
      action: "Read Prometheus metrics for canary track at step weight 10%"
      autonomy: "read-only"
    - at: "2026-11-26T11:55:23Z"
      action: "Read Prometheus metrics for canary track at step weight 10%"
      autonomy: "read-only"
    - at: "2026-11-26T11:55:28Z"
      action: "Read Prometheus metrics for canary track at step weight 10%"
      autonomy: "read-only"
    - at: "2026-11-26T11:55:33Z"
      action: "Read Prometheus metrics for canary track at step weight 10%"
      autonomy: "read-only"
    - at: "2026-11-26T11:55:33Z"
      action: "Gate check failed: rollback weights to 100% stable, 0% canary"
      autonomy: "closed-loop"
---
# Change Record: Canary Deployment of itsmlab.local/lab6-candidate:f16e6700e6e0

## Outcome: rolled-back
Reason: Rollback triggered by automated analysis gate: Hang detected: HANG: Canary completed only 0.0 requests while stable completed 363.75 requests

## Autonomy & Execution
This change was executed by an automated deployment gate following the progressive delivery schedule.
