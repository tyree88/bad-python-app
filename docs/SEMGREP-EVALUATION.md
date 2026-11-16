# Semgrep CI evaluation

This is an intentionally vulnerable Flask application. Keep the existing examples as a backlog for evaluating detection and PR behavior. This setup scans source without installing or running the app. It does not deploy the application.

## Repository review

Reviewed upstream commit `d78a9cd` on November 15, 2026:

- The original remote is `r2c-CSE/bad-python-app`; use a writable fork for evaluation.
- SQL injection, shell execution, unsafe file handling, weak password hashing, and other vulnerable examples are deliberate. A full scan should find issues.
- `.circleci/config.yml` is legacy configuration, not the evaluation path. Its PR branch does not write the `findings.json` consumed by the next step. Exports appended to `$BASH_ENV` do not apply to the already-running shell; the baseline assignment also contains invalid spacing. Its reachability check treats nonempty strings such as `false` as true. Reachability is not itself a blocking-policy flag.
- The Dockerfile uses Python 3.7 and dependencies are old. This change does not establish container build or app startup compatibility.
- `vulns/sql_injection/sql_injection_login.py` references `flask.render_template_string` without importing `flask`. This runtime defect is retained with the training examples; static scanning does not prove the login route works.
- There was no application test suite or GitHub Actions workflow. Custom-rule fixtures added here validate the scanner policy, not Flask behavior.

## Pipeline behavior

`.github/workflows/semgrep.yml` pins Semgrep 1.183.0 by container digest and GitHub actions by commit SHA. Registry `p/default` rules can still change; saved reports identify the rules used. `.semgrep/rules/` is versioned with this repository.

| Trigger | Community scan | Expected gate behavior |
| --- | --- | --- |
| Push to `main` | Full baseline | Findings are reported in audit mode; scan errors still fail. |
| Pull request | Findings new relative to its base | New findings fail the `Semgrep gate` check. |
| Manual dispatch | Full baseline | Findings are reported in audit mode; scan errors still fail. |

Rule fixtures must pass on every run. JSON and SARIF reports are retained for seven days, including failed scans. Test fixtures and vendored browser assets are excluded from application scans. Application templates and all original Python/Java examples remain eligible for scanning.

`--no-suppress-errors` prevents a scanner failure from silently becoming a passing check. A green baseline means the scan completed without a blocking error; it does not mean this app is secure. Repository rules must require the **Semgrep gate** check before it can prevent merging. This document does not establish that branch protection is enabled.

## Run locally

Use Semgrep **1.183.0**, matching CI. App dependencies and a running Flask server are unnecessary.

```sh
semgrep --version
semgrep --test --config .semgrep/rules .semgrep/tests

# Full baseline: reports findings, but findings alone do not fail this command.
semgrep scan --config p/default --config .semgrep/rules --metrics=off \
  --exclude=.semgrep/tests --exclude=static/assets \
  --json-output=semgrep-results.json --sarif-output=semgrep-results.sarif .

# PR-style gate: start from a clean, committed branch with origin/main available.
SEMGREP_RULES='p/default .semgrep/rules' SEMGREP_SEND_METRICS=off \
  semgrep ci --no-suppress-errors \
  --baseline-commit="$(git merge-base HEAD origin/main)" \
  --exclude=.semgrep/tests --exclude=static/assets
```

The local commands above assume no Semgrep login/token. An authenticated CLI must use the platform path or a separate logged-out environment; do not combine `SEMGREP_RULES` with `SEMGREP_APP_TOKEN`.

## Prove the PR fails and recovers

1. Put the workflow, custom rule, and fixtures on the fork's `main` branch. Run the baseline and inspect its report.
2. Create an evaluation branch from that baseline. Add `ci_demo.py` containing the following function. **Do not call it.**

   ```python
   import os

   def demonstrate_policy():
       os.system("echo Semgrep evaluation")
   ```

3. Commit, push, and open a PR. Confirm `python-no-os-system` appears as a new finding and **Semgrep gate** fails.
4. Replace the body with `return "Semgrep evaluation"` and remove the unused import. Commit and push again. Confirm the check passes.
5. Save both run URLs, commit IDs, reports, and conclusions. Check repository rules separately before claiming the red check prevented a merge.

This custom rule forbids every `os.system` call, including literal commands. It is a clear organization-policy example, not a claim that every matched line is exploitable. The fixture covers dynamic calls, constant calls, an import alias, and allowed alternatives. Existing shell calls stay in the baseline.

## Connect Semgrep AppSec Platform

The no-account community gate works independently. The separate **Semgrep AppSec Platform** job is disabled until configured; a skipped job does not prove dashboard integration.

1. In your Semgrep organization, connect the writable GitHub repository and choose CI-based scanning. Enable only the products intended for this evaluation.
2. Configure the project's detection and remediation policies. Start baseline findings in monitor/audit behavior and select the PR rules you want to enforce. The local custom rule always runs in the community gate; publish and enable it in platform policy if you also want it in the dashboard.
3. Add the Semgrep CI token as the repository Actions secret **`SEMGREP_APP_TOKEN`**. Never commit it or paste it into a report.
4. Add the repository Actions variable **`SEMGREP_PLATFORM_ENABLED=true`**. Dispatch the workflow, then verify the project, scanned commit, products, and findings in the dashboard.
5. Repeat the PR exercise and verify the intended platform comments and blocking policy. Fork and Dependabot PRs skip this token-bearing job; the community gate still runs.

The two jobs deliberately keep platform tokens and local rule configuration separate. SARIF is saved as an artifact; uploading to GitHub code scanning is not configured. This does not imply GitHub Security-tab integration.

## Local validation receipt

Validated on November 15, 2026, with Semgrep 1.183.0 against upstream `d78a9cd` plus this setup:

- The full community scan reported **34 findings across 55 files**, with **0 scan errors**: 5 ERROR and 29 WARNING severity results. These include audit and policy matches; they are not 34 confirmed exploitable vulnerabilities.
- The custom-rule test passed all expected matches and negative examples. Actionlint 1.7.12 accepted the workflow; ShellCheck was not run.
- A temporary Git clone exercised the actual `semgrep ci` command with `p/default` and the custom rule. No application code was executed.

| Local check | Findings | Exit code | Result |
| --- | ---: | ---: | --- |
| Simulated main push, audit mode | 34 | 0 | Existing findings recorded |
| Simulated manual dispatch, audit mode | 34 | 0 | Existing findings recorded |
| Clean PR against committed baseline | 0 | 0 | Passed |
| PR introducing one `os.system` call | 1 | 1 | Blocked by custom rule |
| PR after removing the call | 0 | 0 | Passed |
| Missing rule configuration, audit mode | 0 | 7 | Scanner error failed the check |

These are local CLI results, not hosted GitHub Actions runs. Container execution, artifact upload, GitHub's automatic PR baseline selection, branch protection, and Semgrep dashboard integration still need live validation. Local JSON/SARIF reports are ignored by Git.

## Official references

- [GitHub Actions configuration](https://docs.semgrep.dev/semgrep-ci/sample-ci-configs)
- [CI variables and baseline selection](https://docs.semgrep.dev/semgrep-ci/ci-environment-variables)
- [Blocking findings and internal errors](https://docs.semgrep.dev/semgrep-ci/configuring-blocking-and-errors-in-ci)
- [Testing custom rules](https://docs.semgrep.dev/writing-rules/testing-rules)
- [Unified Policies](https://docs.semgrep.dev/semgrep-appsec-platform/unified-policies/overview)
