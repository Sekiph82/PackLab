# PL-0043 — ChatGPT Strict Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_PROMPT_V02.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_CRITERIA_V02.md
Codex log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_LOG_V02.md
Prior audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_V01.md

Audited implementation commit: `a63601955620e146c1634921fd6e17cbf6ecc328`
Audited log commit: `3770cb1862c28c7cdb4a8353d99d2d98463cfd3b`

## Independent result on the wiring

The hosted XCTest graph defect itself is corrected. The application target enables `ENABLE_TESTABILITY = YES`, which is the Xcode setting that supplies Swift `-enable-testing`. The test target configures:

- `BUNDLE_LOADER = "$(BUILT_PRODUCTS_DIR)/PackLabCapture.app/PackLabCapture"`
- `TEST_HOST = "$(BUNDLE_LOADER)"`

This matches Apple's documented application-unit-test host model. The app target dependency, test source membership, Swift 6 strict-concurrency settings and no-personal-signing boundary are preserved.

## Remaining blocking finding

The frozen V02 work order required **adding static regression checks** for testability, bundle loader, test host and source membership.

The implementation commit changes only:
- `apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj`
- `docs/development/IOS_BASELINE.md`

No durable/repeatable regression test or repository check was added. The Codex log reports one-off PowerShell assertions, but does not add a check that future changes can rerun automatically or through the canonical Python test suite.

Because native Xcode execution is intentionally unavailable until M16, this durable static guard is particularly important for preserving the source-controlled project graph.

## Criterion disposition

1-11: PASS  
12: **FAIL** — no persistent static regression check was added.  
13-15: PASS  
16: **FAIL** — the reported ad-hoc static checks are not preserved as a repeatable regression check that will fail on future reintroduction of the V01 defect.  
17-22: PASS  
23: **FAIL** — one frozen remediation requirement remains unsatisfied.

Result: **20 / 23 PASS, 3 FAIL**

## Required remediation

Do not rewrite the now-correct Xcode graph merely to create a diff.

Add a lightweight, durable static regression test/check, preferably in the existing Python test suite, that reads the source-controlled `project.pbxproj` and asserts:
- PackLabCapture Debug/test-used configuration enables `ENABLE_TESTABILITY = YES`;
- PackLabCaptureTests has the expected `BUNDLE_LOADER`;
- `TEST_HOST = "$(BUNDLE_LOADER)"`;
- test source is present in the test Sources build phase;
- the test target depends on PackLabCapture;
- no personal team/signing/provisioning values are introduced.

The regression must run without Xcode and must fail against the pre-remediation project graph. Native `xcodebuild test` remains an M16/macOS evidence boundary.

## Evidence boundary

GitHub project graph, test source, documentation, implementation/log topology and Apple build-setting/application-unit-test documentation were independently inspected as E3. Native macOS/Xcode execution is not claimed.

Decision: **CHANGES_REQUIRED**
