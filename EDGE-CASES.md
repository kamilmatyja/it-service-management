---
lab2_edge_cases:
  E1: {rule: R-08, count: 3}
  E2: {rule: R-06, count: 2}
  E3: {rule: R-09, count: 4}
  E4: {rule: R-10, count: 4}
  E5: {rule: R-12, count: 1}
  E6: {rule: R-13, count: 11}
---
<!-- ai-generated: 100% - Gemini CLI generated the explanations for edge cases and gaming -->

# Edge cases in the practice event log

## E1 - clock skew produces a negative lead time

- What the log contains: A commit timestamped after the deployment that shipped it due to clock skew.
- What a default definition would have done: It would produce a negative lead time or drop the pair entirely, skewing the median incorrectly.
- Why the rule is defensible: Dropping the pair would hide a successful deployment from the metrics. Clamping it to zero acknowledges the instant delivery without corrupting the math.

## E2 - a revert of a revert

- What the log contains: A commit that reverts a commit which is itself a revert of an earlier commit.
- What a default definition would have done: It would count them as three separate changes, artificially inflating throughput and changes delivered.
- Why the rule is defensible: A revert of a revert simply restores the original change. Grouping them under the original `change_id` accurately reflects the actual value delivered to the user.

## E3 - a hotfix that never touched `main`

- What the log contains: A commit deployed straight to production from a branch other than `main` (e.g., a hotfix branch).
- What a default definition would have done: It would filter out any commits not on `main`, missing critical, fast emergency fixes from the throughput metrics.
- Why the rule is defensible: Customers don't care which branch a feature came from; they care that it is in production. Ignoring hotfixes punishes teams for resolving emergencies.

## E4 - a deployment with zero linked commits

- What the log contains: A production deployment event with an empty `commits` array (e.g., config changes, restarts).
- What a default definition would have done: It would drop the deployment completely or crash with a division by zero when calculating averages.
- Why the rule is defensible: It's a real deployment that changes the production state. It must count towards deployment frequency and instability metrics even if there's no code change.

## E5 - a deployment that failed and never recovered

- What the log contains: A failed deployment whose covering incident has no `resolved` event inside or outside the window.
- What a default definition would have done: It would close it at the window's end or drop it, producing artificially short recovery times.
- Why the rule is defensible: Unresolved incidents are open failures. Excluding them from the median while keeping them in the fail rate paints an honest picture of instability without making up false recovery times.

## E6 - overlapping incidents

- What the log contains: Unordered pairs of distinct incidents whose active intervals overlap in time.
- What a default definition would have done: It would merge them into one giant incident or sum their durations, double-counting the wall-clock time.
- Why the rule is defensible: Each failed deployment requires its own recovery calculation based on its specific covering incident. Merging them misrepresents the actual recovery time of individual failures.

## Gaming demonstration

We gamed the `deployment_frequency_per_day` metric by exploiting rule `R-11`. We injected 50 fake successful deployments with empty `commits` arrays (which is allowed by R-10). At the same time, we delayed all real, base deployments by 10 days, which harmed the true change lead time and caused some real changes to fall outside the reporting window (dropping the number of delivered changes).

In a real team, this would be incentivized if management set a hard target for "deployments per day" (tokenmaxxing/gaming). A developer or DevOps engineer could automate empty config reloads to hit the target and get a bonus, while actual feature delivery for the customer becomes much slower.