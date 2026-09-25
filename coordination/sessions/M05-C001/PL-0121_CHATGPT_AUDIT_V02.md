# PL-0121 — ChatGPT Remediation Audit V02

Decision: **CHANGES_REQUIRED**

## Independent result

Swift/Python V1 models now cover create, status, control, completion and error envelopes, and Python consumes the shared golden fixture. The frozen cross-language criterion is still not fully met: the Swift test does not consume the authoritative golden fixture; it reconstructs values in code and checks selected encoded fields. The fixture is not a test-bundle resource. Swift decoding also does not enforce protocol-version rejection for status/completion/error models; the current test covers encoding field names, not version rejection/error mapping from the shared fixture.

## Required remediation

Make the same golden fixture available to the Swift test target and decode/compare every create/chunk/status/cancel/resume/completion/error object from it. Add fail-closed Swift decode validation for unsupported protocol versions and stable error envelopes.

PL-0121 remains unchecked.

Decision: **CHANGES_REQUIRED**
