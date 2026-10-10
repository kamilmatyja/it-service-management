---
lab3_first_draft:
  source: instructor
  ladder: [0.001, 0.0025, 0.005, 0.0075, 0.01, 0.0125, 0.015, 0.0175, 0.02, 0.025, 0.03, 0.04, 0.5, 2.5]
  verdict: refuted
  evidence: {p99_seconds: 0.208, bucket: [0.04, 0.5], relative_width: 2.212}
lab3_flawed_ladder:
  verdict: refuted
  evidence: {p99_seconds: 0.208, bucket: [0.04, 0.5], relative_width: 2.212}
---
<!-- ai-generated: 0% - Hand-written according to instructor instructions for no-AI path -->

# The assistant's first draft, and two verdicts

## Verdict on the draft ladder
The measured p99 is 0.208 s, falling into the (0.04, 0.5] bucket. Its relative width is (0.5 - 0.04) / 0.208 = 2.212, which is far greater than the 0.20 allowed limit. Consequently, the histogram quantile calculation would be highly inaccurate. The verdict is thus refuted.

## The draft alert rule
The draft alert rule is a generic example using a single window without considering error budgets, multiple burn rates, and without a suitable threshold based on the actual distribution. Therefore, we discarded it in favor of customized rules matching the SLO.

## Verdict on the instructor's flawed ladder
The instructor's flawed ladder resolves poorly at the 0.208 s p99. It places the value within the highly coarse (0.04, 0.5] bucket, offering a relative width of 2.212. This fails the required resolution of a 20% margin, hence the verdict is refuted.
