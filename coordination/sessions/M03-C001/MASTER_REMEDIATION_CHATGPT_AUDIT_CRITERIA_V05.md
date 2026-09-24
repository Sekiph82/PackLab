# M03-BATCH-006 — Master Remediation Audit Criteria V05

All criteria mandatory.

1. TASKS.md authorizes M03-BATCH-006 / READY / CODEX before material work.
2. Authorized child set is exactly PL-0073, PL-0074 and PL-0075.
3. PL-0068 remains OWNER_REQUIRED.
4. The other 22 M03 children remain accepted and unregressed.
5. Codex never edits TASKS.md or ChatGPT audit artifacts.
6. No M04 work starts.
7. No secrets/signing/provisioning/private assets/caches enter public Git.
8. Existing production camera architecture is preserved.
9. One production-used injectable camera-device-control seam is shared by real AVCaptureDevice wrappers and deterministic tests.
10. PL-0073 proves wrong-device, adjusting/stable focus, lock timing and runtime propagation.
11. PL-0074 proves wrong-device, clamp/metering/lock, serialized configuration, runtime propagation and persisted exposure/ISO.
12. PL-0075 proves wrong-device, adjusting/stable white balance, lock timing, observed temperature, runtime propagation and persisted WB.
13. Synthetic driver values are clearly test fixtures and never represented as physical evidence.
14. Each child has a distinct implementation commit and a separate log-only commit.
15. Child logs end READY_FOR_INDEPENDENT_AUDIT.
16. Relevant regression/project/static checks pass truthfully.
17. git diff --check/protected-file/privacy checks are clean.
18. All user-facing repository links are full GitHub URLs.
19. Master log indexes all three children accurately.
20. Master log ends AWAITING_MILESTONE_AUDIT.

If all three children independently pass, M03 may close while PL-0068 remains OWNER_REQUIRED under the existing owner-authorized exception.
