# Wave 1 verification evidence

Supporting evidence for the submitted [trade-offs](../templates/TRADEOFFS.md).
Local integration, development deployment and GitHub execution are separate observations.

## Observed GitHub execution

On 2026-10-24 I inspected [run 40125062976](https://github.com/JonathanGWesterfield/PressW-Take-Home/actions/runs/40125062976)
through the GitHub API. At commit `31758eac019839c4ef39b17fbf20bad20f83fd44`,
**Direct legacy and modern**, **Direct Encore and modern**, and **Gateway ingress
and mixed routing** all completed successfully, including their verification
and upload steps. Three nonexpired artifacts were listed, named
`verification-{legacy,encore,gateway}-40125062976-1`.
[Recorded metadata](../investigation/evidence/github-actions-20261024.jsonl)
preserves run/job/artifact identities and the observation time.

I verified job and artifact metadata, without downloading/recounting the remote
JUnit payloads. The exact counts below come from local I1 reports. Later local
changes are documentation/IDE files; application, executable tests, fixtures,
runner and workflow code match the CI revision. This does not label later commits
as remotely tested. GitHub reported `main` unprotected and the repo public;
required checks/PRs, private sharing and final-revision publication remain
submission actions. A green push run does not establish branch enforcement.

## Local integrated and live evidence

These are saved I1 local runs of the combined tree, inspected for this writeup;
E2 did not start containers or rerun the stack. Reports are ignored local
artifacts, not remote CI results. Each directory contains `run.txt`,
`exit-code.txt`, `junit.xml` and timestamped `compose.log`. I1 ran
`python3 scripts/verify --backend both` for the first two stages below; the
individual commands reproduce the same target gates.

| Full command | Saved report under `test-results/` | Result |
| --- | --- | --- |
| `python3 scripts/verify --backend legacy` | `showcall-verify-814fd83dd4ff/` | Exit 0; 1,084 pytest test cases; no failures/errors/skips |
| `python3 scripts/verify --backend encore` | `showcall-verify-a4e3b870b5e4/` | Exit 0; same 1,084 test cases; no failures/errors/skips |
| `python3 scripts/verify --backend gateway` | `showcall-verify-66349a73c416/` | Exit 0; 81 test cases; no failures/errors/skips |

The direct JUnit suites report `tests=1097`, but each contains 1,084
`testcase` elements: unittest subtest counters add 13. These are not 13
additional pytest methods. The gateway report has 81 entries and counter 81.
Direct targets run the frozen corpus, properties, units, modern and ingress
checks; gateway mode selects its ingress/mixed suite plus units, smoke and
modern checks. Frozen response files are not changed to accommodate Encore.
See [test instructions](../tests/README.md), [I1](../tasks/I1-integration-rehearsal.md)
for live artifacts and final state, and [R1](../tasks/R1-independent-review.md)
for the independent local acceptance verdict. E2's document review is not R1
approval.

The compact [I1 evidence](../investigation/evidence/i1-integration-20261024.jsonl)
records the failed publication, correction, full gate identities, live routing
phases and final config hash. Raw local evidence is in `test-results/i1-live-final/`:
`summary.json`, `publication.jsonl`, `continuous-ingress.json`, phase responses,
gateway identities and DB comparisons. Crew rows and schema matched before/after;
a temporary legacy notes update was visible through wrapper/v3 list/detail and
was restored exactly. Captured noncrew tables were unchanged in this rehearsal;
that does not mean maintenance is disabled. Only the gateway was recreated for
preparation, before the baseline; its instance/container stayed unchanged during
cutover, rollback and reapply. The active route table selects Encore only for
canonical org `7` on the two read prefixes; all writes/jobs stay legacy. Use the
corrected `publish_d2_routes` procedure in [D2](../tasks/D2-rollout-configuration.md)
to publish `tests/routes/legacy.yaml` for rollback, without restart. Modern
clients remain direct Encore. R1 accepted the bounded local result; remote
enforcement remains pending.
