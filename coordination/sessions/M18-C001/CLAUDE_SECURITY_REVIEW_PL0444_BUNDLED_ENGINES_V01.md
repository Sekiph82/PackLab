# CLAUDE security/license + code review: PL-0444 bundled engines (PR #11) V01

- Reviewer: independent Claude security/license reviewer (did not author the change; no source edits)
- Subject: `origin/feat/bundled-engines` head `12594510`, diffed against `origin/main` (16 files, +1519/-12)
- CI: `PackLab Windows Python Quality` run 44806278481, `pull_request`, head `1259451029d5…`, conclusion **success** (checked with `gh run view`)
- Verdict: **PASS_WITH_NOTES** for the engineering change. Public/factory redistribution stays **EXTERNAL_PENDING_REVIEW** (legal); this review does not clear it.

## Evidence I checked myself
- No binaries in the diff (`git diff --numstat` shows no binary entries). Grepping for secrets found only the AGPL text's "password or key" wording. `/engines/` is gitignored.
- License texts are byte-identical to the upstream tags. Their sha256 matches the values fetched with `gh api` at `colmap@4.2.1 COPYING.txt` (`ab30dabb…9233`), `openMVS@v2.4.0 LICENSE` (`0f072d4a…c55f`) and `COPYRIGHT.md` (`87663661…2123`).
- The archive pins match GitHub's release-asset digest and size: COLMAP `c493d88c…86ae` / 127731595 and OpenMVS `0c31660c…2167` / 22363227.
- I re-ran the implementer's frozen probe (`scratchpad/frozen/dist/PackLabEngineProbe/PackLabEngineProbe.exe`): all 6 engines reported `source: bundled`, and bundled `colmap.exe help` exited 0.
- Path logic: `parents[4]` of `apps/windows-studio/src/packlab_studio/engine_config.py` is the runtime root. The launcher runs `OwnerDev/current`, which is a plain copy and not a junction (verified), so `runtime_root.parent/engines` resolves to `OwnerDev/engines`, where the refresh script stages engines. In the frozen build, engines are found beside `sys.executable`. Precedence in `_resolve` is explicit > env (including `PACKLAB_OPENMVS_ROOT`) > bundled > PATH, and tests cover it.
- Hash verification: both the `.partial` download and every cached archive are verified before extraction, and a bad partial download is deleted. Each license text is digest-checked before it is copied.
- Zip-slip: absolute paths, `..`, `:` (drive/ADS) and backslash-normalised names are all rejected, and a test covers this. The content is also hash-pinned, so it is trusted.
- Download guard: if `ipconfig` shows `172.20.10.` the download is refused (fail-closed if `ipconfig` errors). Seeded or cached archives skip the network.
- AGPL/distribution: OpenMVS runs only as a separate, unmodified process, and `SOURCE_OFFER.txt` includes a 3-year written offer. Both registry records carry `native_unresolved_reason`, so `unresolved_count != 0` and the `clearance` step blocks the installer. The new workflow step is `workflow_dispatch`-only and runs after the smoke-diagnostics upload. No artifact path includes `engines/`, and only scanned text pre-clearance evidence is uploaded. This complies with the rule against public binary artifacts while legal review is pending.

## Findings
HIGH: none.

MEDIUM
- M1 (legal, external): the third-party DLLs in both archives (Qt 6, Boost, OpenCV, CGAL/GMP, OpenEXR/OIIO, Python 3.12) have no per-file license texts. OpenMVS `COPYRIGHT.md` lists `ibfs` as "research purposes only", which may conflict with commercial factory use even when the software is only run locally. The PR records both issues correctly as blockers, so this is not a code defect, but owner/legal sign-off is required before any distribution or commercial production use. Status: EXTERNAL_PENDING_REVIEW.

LOW
- L1: `fetch_archive` streams the download without a size cap and does not check `archive_size`, so a hostile or redirected response could fill the disk before the hash check fails. Adding a cap at `archive_size` would fix this.
- L2: `stage_bundle` will `rmtree` any `dest` that contains a `packlab-engine-bundle.json` (and any `<dest>.staging` folder). Files the user adds inside a staged `engines/` folder are lost on restage. This is acceptable because the folder is tool-owned, but it should be documented.
- L3: the bundled lookup is still used when `allow_path_lookup=False`. This is defensible (it is not a PATH scan) but is undocumented.
- L4: running Studio directly from `OwnerDev/releases/<id>` (not `current`) would look for `OwnerDev/releases/engines` and report the engines as missing. The supported launcher is not affected.
- L5: the hotspot guard detects only that one subnet, not other metered links.
