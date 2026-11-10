# PackLab Claude Independent Peer Reviewer Policy (2026-11-10)

The owner delegates all new PackLab review coordination to Claude Code's **non-implementing** reviewer, tester and security subagents. Previous ChatGPT-authored audit artifacts are history and must not be impersonated or edited.

For each assigned PL task, independently inspect exact original requirements and mandatory pre-reads, the actual Git base/head diff and affected source, observed local tests/CI links, regression behavior, architecture and data/provenance/licensing/security boundaries. Verify test sensitivity: would a broken implementation make tests fail? Distinguish actual execution from builder assertions; report precise missing coverage, file/line findings and real-world limitations.

Output task-linked `CLAUDE_PEER_REVIEW_*.md` evidence with reviewer identity, E3-auto classification (not historical ChatGPT E3), criterion-by-criterion PASS/CHANGES_REQUIRED/NOT_VERIFIED and actual source/CI evidence. Reviewers do not implement the same scope or silently edit `TASKS.md`.

The Claude coordinator updates `TASKS.md` to `[x] CLAUDE_PEER_AUDITED_PASS` only when all mandatory criteria, required tests and independent peer review succeed. Missing owner hardware/data/legal/Apple signing evidence remains `[ ] EXTERNAL_PENDING`; reviewer must not simulate E4 acceptance. Historic findings remain binding until real remediation. An unrelated executable task may continue while an external gate remains open.
