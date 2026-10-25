<!-- ai-generated: 0% - Hand-written -->
# K8sGPT vs AI Agent Comparison

This document compares the diagnostic capabilities of `k8sgpt` with the Prometheus MCP-backed AI agent during a feature flag-induced incident.

`k8sgpt` is heavily optimized for identifying infrastructural state anomalies directly from the Kubernetes API. In simulated tests, it successfully identified Pods that were OOMKilled (due to inadequate resource limits) and reported issues with unused ConfigMaps. However, it completely missed the actual root cause of our incident. Because a feature flag toggle does not crash the pods or change their readiness state, `k8sgpt` reported the core application stack as healthy.

Conversely, the AI agent using the Prometheus MCP server investigated the symptoms via telemetry. It queried the exact `traces_span_metrics_calls_total` metric, which correctly highlighted a severe spike in HTTP 500s (`STATUS_CODE_ERROR`) in the payment service, leading to checkout failures.

Conclusion: `k8sgpt` is a powerful tool for cluster hygiene and infrastructure failure monitoring, but it is blind to logical application errors (like bad feature flags) that do not perturb the Kubernetes state machine. Telemetry-based AI agents remain necessary for full-stack Root Cause Analysis.