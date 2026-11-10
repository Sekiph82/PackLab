# PL-0379 — Codex Prompt V02

Task: **Bounded fail-closed `.packscan` import and quarantine**  
Milestone: **M17** · Cycle: **M17-C001**

V02 extends V01 after independent source review found `_load_archive()` materialized every ZIP member in memory without package, entry-count, or decompressed-byte limits. Retain V01 corrupt/truncated/path-hostile/quarantine coverage and close the resource-bound gap at the real import boundary.

## Required implementation

- Enforce documented fixed ceilings: 512 MiB compressed package, 1,024 ZIP entries, 64 MiB per entry, 4 MiB per control entry (`manifest.json`, `checksums.json`, `metadata/photos.json`), and 512 MiB total expanded content.
- Check compressed file size before ZIP parsing. Preflight the ZIP end record's single-disk entry count before `ZipFile` materializes the central directory. Reject ZIP64 layouts outside these bounds.
- Check declared sizes before decompression, then read each member in bounded chunks and enforce actual per-entry and total output ceilings.
- Apply compatible limits to the deterministic PackScan writer so it cannot emit packages the reader rejects.
- Ensure extraction re-reads only through the same bounded loader and verifies the validated entry set/checksum/manifest snapshot before publishing extracted files.
- Bound quarantine preservation and capture-ID inspection. An over-limit file may receive a quarantine diagnostic record with `package_preserved=false`; do not copy or decompress it without a bound.
- Add small, deterministic negative tests by lowering constants with monkeypatch; do not allocate a large zip bomb. Exercise the actual `ImportService` rejection/quarantine boundary for an oversized package.
- Preserve valid small `.packscan` behavior, stable diagnostics, atomic extraction, and existing corrupt/traversal/quarantine tests.

## Test timing

- Do not run tests for this child. The owner requires one or two grouped M17 validation runs at the milestone checkpoint; those runs have already occurred before this remediation. Record new tests as unexecuted and keep PL-0379 open until a new owner-authorized M17 grouped validation decision.
- Write `PL-0379_CODEX_LOG_V02.md` only after implementation and independent review; record that tests remain unrun and no test pass is claimed.
