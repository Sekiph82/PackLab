# PL-0383 — Validation Criteria V01

1. Missing and wrong-version engine probes fail closed with actionable stable reason codes.
2. Malformed version output is rejected; the accepted pinned version is recognized.
3. Tests use fake/local fixtures and do not install/download software.
4. Test execution is deferred to M17 milestone end.
