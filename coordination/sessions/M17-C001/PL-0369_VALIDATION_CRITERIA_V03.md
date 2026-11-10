# PL-0369 — Validation Criteria V03

V03 supersedes V02's sprint-level test timing after the owner directed that testers and grouped tests run at the end of M17. V01/V02 are retained as history.

1. Manifest indexes the six existing hash-pinned synthetic media assets and five existing PackScan corpus cases, without copying/changing payloads.
2. Every entry binds path, canonical byte length, SHA-256, format, synthetic provenance, intended CI use, and applicable expected outcome.
3. Validator rejects unsafe paths, missing/changed/unapproved payloads, policy mismatch, incorrect corpus outcomes, malformed metadata, and non-boolean authority flags.
4. Dataset README and license match the owner's authorized scope: PackLab development/CI and owner-controlled design-office/Kenya-factory use; no external reuse, sublicense, sale, or marketing permission.
5. Terms are dataset-scoped only; root and dependency licensing are unchanged. Formal legal review and broader reuse rights are not claimed.
6. No private scans or physical/accuracy claims are included.
7. Independent source and security/licensing reviews pass.
8. Tests and Tester review remain deferred to the grouped M17 milestone-end checkpoint after PL-0395 (or once all remaining M17 tasks have reached their evidence-supported implementation/blocked state). PL-0369 remains unchecked until grouped validation passes.
