# PL-0436 Validation Criteria V05 — Memory Admission

1. Memory budget and snapshot reject booleans, non-integers, zero/negative values, and available memory greater than total.
2. Windows memory reader uses `GlobalMemoryStatusEx` available physical bytes and reports failures without exposing process or owner data.
3. Guarded engine rejects missing/wrong-sized checkpoint, measurement errors, and insufficient available memory before calling the wrapped engine.
4. A passing admission delegates exactly once and preserves image order/result; documentation states that admission is not inference evidence or a guarantee.
5. Synthetic tests inject all memory values and never import/load model weights or read checkpoint contents.
6. Focused tests, targeted Ruff, job/log SHA validation, and `git diff --check` pass.
7. No Actions/paid CI, PR, source push to `main`, native/Installer build, or release claim. Owner access/local-use approval remains complete.
