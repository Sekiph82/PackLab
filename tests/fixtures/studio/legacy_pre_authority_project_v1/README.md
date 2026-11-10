# Legacy pre-authority project fixture (PL-0384)

Created on 2026-11-10 by running the actual Windows Studio sources from commit `109138a9^` (before the
M06 R01 remediation introduced `working/authority.json`): `ProjectManager.new_project(...)` followed by one
`commit_edit({"notes": ..., "units": "mm"})`. Bytes are unmodified. Empty layout directories are recreated by the
test from `.packlab-layout.json` because Git does not store empty directories. Synthetic content only.
