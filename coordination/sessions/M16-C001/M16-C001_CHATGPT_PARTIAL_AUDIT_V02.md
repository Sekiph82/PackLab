# M16-C001 - ChatGPT Partial Audit V02

Date: 2026-10-06
Decision: **AUDITED_PARTIAL_CHANGES_REQUIRED**
Independently accepted frontier: **PL-0347 V02 through PL-0349**
Current blocked child: **PL-0350 V01**
PL-0351 through PL-0367: **NOT_STARTED**
PL-0368: **DEFERRED_POST_M17**

## Accepted children

- PL-0347 V02 — `AUDITED_PASS`
- PL-0348 V01 — `AUDITED_PASS`
- PL-0349 V01 — `AUDITED_PASS`

Individual audits are published in this M16 session directory.

## PL-0350 V01 blocker

The builder stop is **VALID**.

The frozen PL-0350 criteria require a reviewable file-level inventory of the **actual current staged Windows bundle** and complete required redistribution notices/license evidence before any release-ready installer claim.

Independent GitHub Actions inspection confirms:

- hosted production build/smoke run `37424680100` succeeded;
- its job built and smoke-tested the current production staging tree;
- the run has **zero uploaded artifacts**;
- therefore the exact staging tree is no longer available for independent file-level inspection after runner teardown.

The only local staging tree described by the builder predates PL-0349 and is not valid evidence for the current production bundle.

The current dependency/license register also truthfully keeps unresolved redistribution work for actual shipped PySide6/Qt, OCP/OCCT/OCP-proxy, Open3D/native and other bundled runtime contents.

No installer or release-ready claim was produced. That is the correct behavior.

## Remediation ruling

Do **not** solve this by uploading the unresolved application bundle publicly.

PL-0350 V02 must instead extend the hosted Windows build into a deterministic compliance-evidence pipeline:

1. inspect the exact current staging tree **on the hosted runner before teardown**;
2. generate a path-free machine-readable file inventory;
3. map every staged file to PackLab, CPython, PyInstaller, an installed Python distribution/native component, or an explicitly reviewed system-runtime category;
4. collect/package required license/notice texts into the staging tree from exact reviewed distribution/upstream evidence;
5. fail closed on any unmapped or unresolved redistributed file/component;
6. upload only a small text/JSON compliance evidence artifact for independent review before binary publication;
7. build the versioned Inno Setup installer only if the compliance validator reports zero unresolved items.

The public evidence artifact must not contain PackLabStudio.exe, DLLs, private data, project/library state or signing material.

A binary installer artifact remains unauthorized until the compliance gate is green.

## Compliance evidence requirements

The inventory must bind at minimum:

- exact build revision and Studio semantic version;
- relative staged path;
- SHA-256 and byte length for every staged file;
- file category and owning component/distribution;
- package/component version where available;
- PE metadata for EXE/DLL/PYD where available;
- mapping evidence source;
- license identifier/status;
- required notice/license file references;
- unresolved reason, if any.

Use PyInstaller build metadata/TOC plus the locked installed environment to map staged files. Strip all runner/workspace absolute paths from canonical evidence.

For installed Python distributions, collect declared/packaged LICENSE, COPYING, NOTICE and dist-info license files where present.

For components whose wheel omits required evidence, use an explicit reviewed supplemental registry pinned to exact upstream component/version and checked-in license/exception text. The registry must not guess.

The current repository has no evidence of a commercial Qt license. V02 must not pretend a commercial route exists. If the open-source Qt/PySide redistribution route cannot be documented sufficiently for the actual staged modules/plugins, stop truthfully with that unresolved item.

Likewise, if exact OCP/OCCT or Open3D/native staged contents cannot be mapped to complete reviewed notice/license evidence, stop. Do not paper over the gap with a generic dependency list.

## Installer rule

Only after the hosted compliance validator reports:

`unresolved_count = 0`

may V02:

- generate `THIRD_PARTY_NOTICES.txt`;
- package required license/exception texts;
- build a versioned Inno Setup installer;
- smoke/inspect the installer output.

No GitHub Release or V0.1 release is authorized.

## Verdict

`AUDITED_PARTIAL_CHANGES_REQUIRED`

PL-0350 V01 stop is independently accepted. Resume at PL-0350 V02. PL-0351 through PL-0367 remain unauthorized until V02 is builder-green. PL-0368 remains `DEFERRED_POST_M17`.
