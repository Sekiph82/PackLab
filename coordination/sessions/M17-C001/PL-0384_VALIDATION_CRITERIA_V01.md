# PL-0384 — Validation Criteria V01

1. Supported old schemas migrate deterministically through the public import boundary.
2. Malformed inputs and unknown future schemas fail closed without overwriting source data.
3. Migration fixtures are small and disposable; owner data is untouched.
4. Test execution is deferred to M17 milestone end.
