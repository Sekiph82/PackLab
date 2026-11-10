# PackLab Evidence Log Contract | Claude Code Active / Codex Historical (2026-11-10)

Earlier `CODEX_LOG_*.md`, `CODEX_PEER_REVIEW_*.md` and `CHATGPT_AUDIT_*.md` are **read-only historical evidence**. The previous Codex-required `AWAITING_AUDIT` stop is NOT an active work order. Claude is sole new execution/acceptance coordinator.

For each new PL task record append-only evidence under `coordination/sessions/<cycle>/`, naming files `CLAUDE_IMPLEMENTATION_LOG_VNN.md`, `CLAUDE_PEER_REVIEW_VNN.md`, optional `CLAUDE_TEST_EVIDENCE_VNN.md` and milestone consolidated review. Never forge historic author identities or overwrite an earlier audit.

A log must identify: PL ID; acceptance criteria and technical pre-reads; start/implementation/review/final Git SHAs; actual files added/changed; expected/failure/observed results for commands; focused/negative/regression coverage; hosted Windows/macOS GitHub Actions run IDs and verified conclusions; separate reviewer identity and exact diff findings; security/license/data provenance review; limitations and real external/physical/owner gates; `TASKS.md` status decision; remote push verification; Desktop fast-forward/parity or `LOCAL_SYNC_PENDING`; OwnerDev refresh outcome and disk/worktree safety.

Do not predeclare a commit SHA that does not yet exist or claim a task PASS from implementation alone. Only after actual mandatory tests and non-implementing peer/security review may the Claude coordinator update `[x] CLAUDE_PEER_AUDITED_PASS` in the single live tracker and choose the next task.
