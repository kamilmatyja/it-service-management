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

The eight labelled defects are a deliberately small, seeded sample; these measurements describe only this canary,
not the scanners' expected production performance. Gitleaks returned TP/FP/FN 2/1/6 (precision 0.667, recall
0.250, F1 0.364): it matched C03 and C06, missed C05, and produced one finding that matched no labelled defect.
Grype and OSV-Scanner each returned 2/0/6 (precision 1.000, recall 0.250, F1 0.400), finding both vulnerable
dependency pins but none of the six other defects. Semgrep returned 3/3/5 (precision 0.500, recall 0.375, F1
0.429): it matched A02, A14 and C06, while three findings matched no defect. Trivy returned 3/1/5 (precision
0.750, recall 0.375, F1 0.500), matching C03 and both dependency defects with one unmatched finding.

The false positives matter operationally even when a detector catches real issues: someone must inspect and
disposition each alert, and repeated noise can consume review capacity or teach maintainers to ignore the gate.
The false negatives are more consequential here: A03 (path traversal) and C05 (a secret) were missed by all five
tools, so even combining their outputs did not provide adequate coverage. These are defect-level counts: repeated
findings on a defect do not inflate TP, and a finding is not credited unless both its location and weakness class
match. The observed precision and recall are therefore useful for comparing these runs, but eight hand-seeded
examples cannot estimate real-world false-positive or false-negative rates.

I would retain Trivy and gitleaks as blocking gates because the published policy requires those gates and the
canary run demonstrates that the vulnerability and secret checks stop the line; this is not a claim that their
measured recall is sufficient. I would keep Grype and OSV-Scanner as complementary dependency reports, since they
confirmed both vulnerable pins but did not broaden coverage in this set. Semgrep's three unmatched findings
against three matches justify reviewing its alerts without making this configuration an additional blocker.
For every detector, reviewers should record a reasoned disposition and re-check the policy rather than treating a
green build as proof of safety. This is precisely where small, complete changes and a visible green/red build
help: a red build pauses merges until the finding is understood, while the matrix makes the limitations of each
detector explicit instead of hiding them behind one aggregate score.
