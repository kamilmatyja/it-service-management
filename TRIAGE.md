---
lab5_triage:
  image: ghcr.io/kamilmatyja/it-service-management@sha256:ea76bdbe6ac8e83af86a8fe350de6c757b5bd84bbfa52c965a73c05aff9ea1d3
  sarif_receipt: 376
---
<!-- ai-generated: 100% - drafted from this repository's receipted SARIF and bake-off results -->
# Triage

These are the findings on the repository's own files in the receipted SARIF. The scanner reports are evidence, not
proof that a code path is exploitable; each disposition below records the context reviewed.

| Tool | Rule | Decision | Reason |
|---|---|---|---|
| semgrep | dockerfile.security.missing-user.missing-user | accept | The image currently runs as root. The service does not execute user-supplied code, but this increases impact if the app is compromised; retain as a tracked hardening item and add a non-root runtime user before production deployment. |
| semgrep | python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected | false-positive | `agent/prom_mcp.py:34` opens a request built from the operator-configured Prometheus URL; the URL is not supplied by an end user, and dynamic path components are URL-quoted. |
| trivy | no finding in repository files | accept | Trivy reported no finding on the repository's own files in the receipted SARIF; its canary matches are included only in the measured bake-off. |

## Bake-off

The eight labelled defects produce a deliberately small, seeded sample, so these scores describe this set and not
general scanner quality. Gitleaks found two secrets with one false positive (precision 0.667, recall 0.250); it
matched C03 and C06 but missed C05. Grype and OSV-Scanner each found both vulnerable dependency pins with no false
positives (precision 1.000, recall 0.250). Semgrep found A02, A14 and C06, but also made three false-positive
matches (precision 0.500, recall 0.375). Trivy found C03 and both dependency defects with one false positive
(precision 0.750, recall 0.375). I would keep Trivy and gitleaks as gates because the course rules define their
blocking conditions and the canary confirms those gates fire; Grype, OSV-Scanner and Semgrep provide complementary
reporting rather than additional blocking gates. A03, the path-traversal defect, and C05, a secret, were not found
by any of the five detectors, showing that a clean scan cannot establish absence of defects. Every recall here is
an upper bound for real maintenance work: detectors were measured against a small set of deliberately seeded,
labelled examples, not a representative sample of the service's future defects.

The local AI reviewer matched all eight labelled defects (TP 8, FP 0, FN 0; precision, recall and F1 are 1.000).
This review was run after the canary labels had been revealed, so it is a post-reveal consistency check, not a
blinded estimate of an AI detector's expected performance. Its raw answer is preserved in
`bakeoff/transcript.md`; `tools/ai-to-sarif.py` converted it to the `ai-reviewer` run in `bakeoff.json`. The
perfect score should therefore not be compared as if it were an independent prospective bake-off.
