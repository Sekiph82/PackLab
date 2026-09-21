# PL-0043 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_CRITERIA_V01.md
Builder log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_LOG_V01.md

Audited implementation commit: 06386124d7e9fe7c66ad8d7421ad124e0bc48342
Audited log commit: ed5b2d60adae51782179daa04c921bbee0a3d104

## Blocking finding

The test source uses @testable import PackLabCapture, but the application target's source-controlled build settings do not enable ENABLE_TESTABILITY. Apple's Xcode build-settings contract states that Enable Testability supplies the Swift -enable-testing behavior required for @testable access.

The unit-test target also sets TEST_HOST directly but omits BUNDLE_LOADER. Apple's application unit-test setup documents a hosted app-test configuration with BUNDLE_LOADER pointing to the app executable and TEST_HOST resolving through that bundle loader.

Because native xcodebuild was unavailable, these source-visible target settings are the only durable evidence that the future M16 simulator/macOS runner can execute the tests. The current graph does not provide sufficient hosted-test wiring.

## Criterion disposition

1-7: PASS
8: **FAIL** — the XCTest target exists, but its hosted/@testable build wiring is incomplete.
9: PASS
10: **FAIL** — current source-controlled settings do not yet establish that the target can run on the future simulator/macOS CI runner.
11-12: PASS
13: **FAIL** — static validation missed the missing testability/host-loader configuration.
14-19: PASS
20: **FAIL** — a material test-target configuration defect remains.

Result: **16 / 20 PASS, 4 FAIL**

## Required remediation

Make the XCTest target graph self-consistent for hosted app unit tests. At minimum:
- either enable testability for the app configuration used by tests or remove @testable when only public API is needed;
- configure BUNDLE_LOADER / TEST_HOST according to the hosted application unit-test model;
- preserve no-team/no-signing-secret settings;
- preserve Swift 6 strict-concurrency settings;
- keep the smoke tests hardware-independent.

Add static regression checks for these settings. If a macOS/Xcode runner is not yet authorized in this milestone, do not fabricate xcodebuild results; preserve the explicit future M16 validation boundary.

## Evidence boundary

The PL-0043 Xcode project graph, XCTest source, Apple Xcode build-setting requirements, documentation and child-log topology were independently inspected as E3. No native macOS/Xcode test pass is claimed.

Decision: **CHANGES_REQUIRED**
