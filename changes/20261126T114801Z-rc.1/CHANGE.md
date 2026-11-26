---
lab6_change:
  id: "change-1795693701"
  candidate: "itsmlab.local/lab6-candidate:3d0d0c5b6be5"
  stable: "ghcr.io/swasik/svcdesk-v2-seeded:2.0.0"
  strategy: "canary"
  change_type: "normal"
  risk: "medium"
  rollback_plan: "Reset Caddy upstream weights to 100% stable and 0% canary, then stop the canary container."
  started: "2026-11-26T11:48:01Z"
  finished: "2026-11-26T11:48:21Z"
  outcome: "rolled-back"
  reason: "Rollback triggered by automated analysis gate: Hang detected: HANG: Canary completed only 0.0 requests while stable completed 361.25 requests"
  actions:
    - at: "2026-11-26T11:48:01Z"
      action: "Read deployment configuration and pre-approved release plan"
      autonomy: "approve-then-act"
      approval: "CAB pre-approval CAB-2026-L6-CANARY"
    - at: "2026-11-26T11:48:01Z"
      action: "Start svcdesk-canary container with candidate image"
      autonomy: "closed-loop"
    - at: "2026-11-26T11:48:01Z"
      action: "Set canary routing weight to 10% (stable: 90%)"
      autonomy: "closed-loop"
    - at: "2026-11-26T11:48:06Z"
      action: "Read Prometheus metrics for canary track at step weight 10%"
      autonomy: "read-only"
    - at: "2026-11-26T11:48:11Z"
      action: "Read Prometheus metrics for canary track at step weight 10%"
      autonomy: "read-only"
    - at: "2026-11-26T11:48:16Z"
      action: "Read Prometheus metrics for canary track at step weight 10%"
      autonomy: "read-only"
    - at: "2026-11-26T11:48:21Z"
      action: "Read Prometheus metrics for canary track at step weight 10%"
      autonomy: "read-only"
    - at: "2026-11-26T11:48:21Z"
      action: "Gate check failed: rollback weights to 100% stable, 0% canary"
      autonomy: "closed-loop"
---
# Change Record: Canary Deployment of itsmlab.local/lab6-candidate:3d0d0c5b6be5

## Outcome: rolled-back
Reason: Rollback triggered by automated analysis gate: Hang detected: HANG: Canary completed only 0.0 requests while stable completed 361.25 requests

## Autonomy & Execution
This change was executed by an automated deployment gate following the progressive delivery schedule.
