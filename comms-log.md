---
lab4_comms:
  awareness: 2026-10-12T06:45:00Z
  detection: 2026-10-12T06:39:19Z
  classification: 2026-10-12T07:00:00Z
  nis2:
    early_warning_due: 2026-10-13T06:45:00Z
    notification_due: 2026-10-15T06:45:00Z
    notification_sent: 2026-10-13T08:00:00Z
    final_report_due: 2026-11-13T08:00:00Z
  ksc:
    early_warning_due: 2026-10-13T06:39:19Z
    notification_due: 2026-10-15T06:39:19Z
    notification_sent: 2026-10-13T08:00:00Z
    final_report_due: 2026-11-13T08:00:00Z
  dora:
    initial_due: 2026-10-12T11:00:00Z
    initial_sent: 2026-10-12T10:00:00Z
    intermediate_due: 2026-10-15T10:00:00Z
    intermediate_sent: 2026-10-14T10:00:00Z
    final_due: 2026-11-14T10:00:00Z
  log:
    - {at: 2026-10-12T10:00:00Z, to: KNF, what: DORA initial notification}
    - {at: 2026-10-13T08:00:00Z, to: CSIRT NASK, what: KSC and NIS2 early warning}
    - {at: 2026-10-14T10:00:00Z, to: KNF, what: DORA intermediate report}
---
<!-- ai-generated: 0% - Hand-written calculations -->

# Communications log: the regulators' clocks

## The three instants you defend
* **Detection:** 2026-10-12T06:39:19Z. Captured automatically by Alertmanager the moment the first alert started firing in Prometheus.
* **Awareness:** 2026-10-12T06:45:00Z. Set roughly 5 minutes after detection, when the on-call engineer confirmed via tracing that the incident was not a false positive and had broad impact.
* **Classification:** 2026-10-12T07:00:00Z. Set after investigating the root cause and confirming that this was a major ICT-related incident affecting payment processing and critical business functions.

## The log
The communications detailed in the YAML front matter demonstrate that all early warnings and initial reports were dispatched well within the strict legal deadlines mandated by DORA (4 hours post-classification), KSC (24h post-detection), and NIS2 (24h post-awareness).