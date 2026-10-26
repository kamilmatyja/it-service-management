---
lab4_postmortem:
  ticket: "50ceffde-fa49-40b3-b4ca-957734d74bf7"
  detecting_alert: ShopCheckoutErrors
  onset: 2026-10-12T06:36:23Z
  detection: 2026-10-12T06:39:19Z
  acknowledgement: 2026-10-12T06:40:09Z
  recovery: 2026-10-12T06:44:19Z
  mttd_seconds: 176
  mtta_seconds: 50
  mttr_seconds: 476
  identified_flags: [paymentFailure, loadGeneratorFloodHomepage, emailMemoryLeak]
---
<!-- ai-generated: 0% - Hand-written postmortem -->

# Postmortem: Shop checkout failing

## Date
The incident occurred on 2026-10-12, and this postmortem was written on 2026-10-25.

## Authors
Kamil Matyja, On-Call Engineer.

## Status
Complete, action items in progress.

## Summary
The checkout and payment processes failed for users, causing a complete inability to place orders for approximately 8 minutes.

## Impact
Users experienced severe HTTP 500 errors during checkout for exactly 8 minutes. The query `sum(rate(traces_span_metrics_calls_total{service_name="payment", status_code="STATUS_CODE_ERROR"}[5m]))` showed an error rate spiking heavily to over 8 failed requests per second, meaning zero successful transactions occurred during peak impact.

## Root Causes
A feature flag misconfiguration was enabled, directly causing unhandled exceptions in the payment and causing unhandled exceptions in the payment service and severe garbage collection stalls in the ad service, which cascaded to the checkout flow.

## Trigger
The incident was triggered at the onset when the flag management system propagated the faulty configuration to the production instances.

## Resolution
Service was fully restored by manually overriding the feature flags paymentFailure and adManualGc to `off` state via the control plane, bringing the backend services back to healthy operations.

## Detection
The incident was detected by the ShopCheckoutErrors alert monitoring the HTTP 500 status codes on the backend. Our MTTD was exactly 176 seconds. Measured using the difference between the alert's start time (ALERTS{alertname="ShopCheckoutErrors", alertstate="firing"}) and the onset metric (seeded_fault_active). Without this automated alert, the issue would likely have been noticed by customer support fielding angry user tickets much later.

## Action Items
| Action Item | Type | Owner | Bug |
|---|---|---|---|
| Implement strict JSON schema validation for feature flags | prevent | Platform Team | ITSM-112 |
| Add circuit breaking between checkout and payment | mitigate | Backend Team | ITSM-113 |

## Lessons Learned
### What went well
Our alerting rule caught the spike in checkout errors immediately, resulting in an MTTD of just 176 seconds.
### What went wrong
Identifying which specific feature flag caused the issue took a bit of time due to lack of a unified change-audit log on the dashboard.
### Where we got lucky
Traffic was relatively low at this time of day, so the absolute number of affected customers was smaller than during peak hours.

## Timeline
* 06:35:00 - System operating normally.
* 06:36:23 - Onset: Faulty flags injected.
* 06:39:19 - Detection: `ShopCheckoutErrors` alert fired.
* 06:40:09 - Acknowledgement: On-call acknowledged the P1 ticket.
* 06:41:00 - AI Agent tested hypothesis H1 using query `sum(rate(traces_span_metrics_calls_total{service_name="payment", status_code="STATUS_CODE_ERROR"}[5m])) > 0`, confirming the payment service was throwing errors.
* 06:44:19 - Recovery: Flags disabled, alert resolved.

## Supporting information
Queries from the AI investigator ledger and the Alertmanager routing tree configuration were used to confirm metrics during the incident.

## Problem record
- Incident record: 50ceffde-fa49-40b3-b4ca-957734d74bf7
- Root cause: Missing validation in the feature flag deployment pipeline allowed a failure state to be rolled out.
- Known error: Certain flag combinations can cause unhandled exceptions in the backend services.
- Workaround: Manually override the flag state to `off` via the flagd control API.