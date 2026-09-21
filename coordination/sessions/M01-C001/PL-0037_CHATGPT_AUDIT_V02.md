# PL-0037 — ChatGPT Independent Re-Audit V02

Decision: **CHANGES_REQUIRED**

Reason for re-audit: new independent Xcode project-graph evidence materially affects the prior V01 verdict.

Repository: https://github.com/Sekiph82/PackLab
V01 audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0037_CHATGPT_AUDIT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0037_CHATGPT_AUDIT_CRITERIA_V01.md

## New blocking evidence

The PackLab Xcode project contains the remote package reference and an XCSwiftPackageProductDependency for NextLevel, and the native target lists that product in packageProductDependencies.

However, there is no PBXBuildFile whose productRef points to the NextLevel product, and the application target Frameworks build phase remains empty.

Normal Xcode Swift-package product wiring includes both the target package-product dependency and the productRef build-file entry in the Frameworks phase. Without the latter, the package product is referenced/resolved but not actually linked as a target framework/library dependency. A future source import can therefore resolve metadata yet fail to link/use the product as intended.

## Updated criterion disposition

1-7: PASS
8: **FAIL** — the exact package is referenced and pinned, but target product linking is incomplete.
9-10: PASS
11: **FAIL** — static project-graph validation missed the missing Frameworks/productRef wiring.
12-19: PASS
20: **FAIL** — a material SPM target-integration defect remains.

Updated result: **17 / 20 PASS, 3 FAIL**

## Required remediation

Preserve the exact NextLevel 0.19.1 canonical package pin and add the missing target-link wiring:
- create the PBXBuildFile entry whose productRef is the NextLevel XCSwiftPackageProductDependency;
- add that build file to the PackLabCapture Frameworks build phase;
- keep NextLevel behind PackLab-owned service boundaries;
- add no unrelated package;
- retain truthful Windows/macOS evidence limits.

Add static regression checks proving package URL, exact version, product dependency, PBXBuildFile productRef and Frameworks-phase membership are all present.

Prior V01 audit remains historical evidence but is superseded by this V02 re-audit because new independent project-graph evidence invalidated that verdict.

Decision: **CHANGES_REQUIRED**
