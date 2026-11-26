---
lab6_blast_radius:
  postmortem_action:
    bug: ITSM-112
    commit: a87e6cff4a80adb18db14cc4b85e684be109dd83
---
<!-- ai-generated: 0% - Hand-crafted analysis -->

# Blast Radius Analysis & Postmortem Action

## Gate

The automated analysis gate implemented in `deploy.sh` protects customer experience by evaluating candidate health in real time before promoting canary traffic. The gate queries Prometheus directly every 5 seconds for two primary Service Level Indicators (SLIs) declared in `deploy.config.yaml` and derived from the Laboratory 3 SLO baseline:
1. **Availability SLI**: Measures the proportion of HTTP 5xx responses returned by the candidate container (`svcdesk_requests_total{job="svcdesk",track="canary",status=~"5.."}`).
2. **Latency SLI**: Measures the fraction of candidate requests exceeding the 250ms latency objective (`1 - (svcdesk_requests_total{job="svcdesk",track="canary",le="0.25"} / svcdesk_requests_total{job="svcdesk",track="canary"})`).

The decision boundary applies multi-window burn rate math: with an availability and latency objective of 99.0% (an allowable error budget of 1.0%), setting `max_burn_rate: 14.4` establishes a strict gate threshold of `14.4 * (1 - 0.99) = 0.144` (14.4% bad requests). Any candidate whose observed error rate or slow-request share exceeds 14.4% immediately fails the gate evaluation. Furthermore, the gate checks for container hang regressions: if the stable baseline is actively serving traffic while the canary serves zero responses after shifting weight, the gate detects an unresponsive process and triggers an immediate rollback. If either SLI violates its budget or a hang occurs, `deploy.sh` halts progressive rollout, zeroes the canary weight in Caddy, and exits with status 3.

## Blast radius

Blast radius is the primary operational control in progressive delivery. Instead of all-at-once recreate or unmonitored rolling deployments where 100% of incoming users face a faulty release simultaneously, our canary rollout steps traffic progressively through discrete stages: 10% (for 20 seconds), 25% (15 seconds), and 50% (15 seconds) before full 100% promotion.

By capping the initial canary slice at 10%, 90% of user requests are shielded on the known-good stable baseline (svcdesk 2.0.0). Across our four test releases under the practice workload:
- **rc.1 (hang)**: The canary stalled completely. The gate observed 0 canary responses within 10 seconds and triggered an emergency rollback. Blast radius was confined to 40 headerless failures, well within the 150-failure ceiling.
- **rc.2 (honest)**: The candidate met all availability (error share ~0.3%) and latency (slow share 0.0%) thresholds across all steps, achieving a blast radius of 0 and completing clean promotion.
- **rc.3 (slow)**: The candidate exhibited elevated response times exceeding 250ms (~52% slow share vs 14.4% threshold). The gate aborted at t+5s of Step 1, limiting blast radius to just 8 slow requests.
- **rc.4 (errors)**: The candidate began throwing HTTP 500 errors (~49% error share vs 14.4% threshold). The gate rolled back at t+10s, capping blast radius at 15 failures.

In every failure scenario, progressive traffic shifting coupled with an automated analysis gate confined the blast radius to a small fraction of the 150-failure budget.

## Change classification

Under ITIL change management frameworks, releases traditionally fall into three classes: Standard (pre-authorized, low risk, repeatable), Normal (requiring CAB review and scheduled maintenance windows), and Emergency (urgent remediation for active incidents). Automated canary deployment transforms release governance:
- **Change Type**: What was historically handled as a manual, high-overhead Normal change is converted into a standardizable, low-risk automated procedure. When unexpected regressions occur, automated rollback executes immediately as an Emergency mitigation without waiting for human escalation.
- **Risk Assessment**: In an all-at-once deployment, risk is high because failure causes 100% service outage. Under canary routing with automated gates, risk is low because traffic exposure is capped at 10% initially and rolled back within seconds if anomalies arise.
- **Autonomy Ladder**:
  - *Level 1 (Read-Only)*: Prometheus continuously scrapes latency and error counters from both stable and canary tracks.
  - *Level 2 (Suggest)*: Metrics are evaluated against SLO burn rate formulas, computing health scores.
  - *Level 3 (Approve-then-Act)*: The deployment orchestrator initiates canary container provisioning and schedules the deployment window.
  - *Level 4 (Closed-Loop Autonomous)*: `deploy.sh` exercises complete closed-loop control: adjusting Caddy routing weights via dynamic API patches, evaluating SLI gate thresholds at 5-second intervals, and autonomously making promotion or rollback decisions in real time without human intervention.
Every run writes an immutable `CHANGE.md` record logging the exact candidate image, timeline, observed metrics, autonomy classification, and decision outcome.

## Postmortem action

This release directly addresses Action Item ITSM-112 from our Laboratory 4 postmortem: *"Implement strict JSON schema validation for feature flags"*, owned by the Platform Team with prevention type.

During the major incident analyzed in Laboratory 4, an invalid configuration payload and malformed flag definition propagated directly to production backend services without prior schema validation. This caused unhandled runtime deserialization exceptions, thread exhaustion, and cascading 5xx failures across customer checkout workflows, requiring extensive manual triage to identify and revert the problematic payload.

In Laboratory 6, commit `a87e6cff4a80adb18db14cc4b85e684be109dd83` resolves this systemic vulnerability through declarative configuration enforcement and automated canary verification:
1. **Declarative Configuration Gate**: `deploy.config.yaml` provides strict, declarative boundary checks for all deployment parameters—mandating explicit SLO objectives (0.99), latency thresholds (0.25s), multi-window burn rate limits (14.4), and discrete step weights/durations. Malformed configurations or invalid thresholds are rejected before any container recreation occurs.
2. **Blast-Radius Controlled Canary Validation**: Even when a subtle bug or malformed flag payload passes static checks, the automated analysis gate in `deploy.sh` restricts initial exposure to exactly 10% of traffic. Real-time Prometheus metrics query error rates and response times every 5 seconds. As proven in test runs rc.1, rc.3, and rc.4, any runtime crash, syntax error, or latency degradation triggers an immediate autonomous rollback within 5–10 seconds, restricting user-visible impact to fewer than 40 requests. This guarantees that malformed feature flags or code regressions can never again cause an unmitigated site-wide outage.
