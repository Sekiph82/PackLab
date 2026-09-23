# PL-0069 — ChatGPT Strict Audit Criteria V01

Task: **PL-0069 — Integrate NextLevel preview into SwiftUI using a controlled UIKit bridge**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0069_CODEX_PROMPT_V01.md

All **20 criteria** are mandatory.

1. TASKS.md authorizes M03 / PL-0069 / READY / CODEX before material work.
2. PL-0068 remains unchecked and explicitly OWNER_REQUIRED; PL-0069 work does not fabricate or close the physical benchmark.
3. Repository synchronization is safe and no destructive Git operation is used.
4. Codex does not edit TASKS.md or any ChatGPT audit artifact.
5. PL-0070 and later M03 tasks are not started.
6. No secret, signing credential, provisioning profile/private key, private Kenya asset, private scan or cache artifact enters public Git.
7. Changed files stay within the authorized iOS preview-integration scope plus only justified minimal adjacent project/test files.
8. The pinned NextLevel dependency remains version 0.19.1 unless an explicit blocking compatibility defect is proven; no opportunistic dependency upgrade occurs.
9. A dedicated UIKit-backed preview component is introduced and bridged into SwiftUI through a controlled representable/container boundary rather than scattering camera framework ownership through SwiftUI views.
10. The preview surface uses the real NextLevel preview contract on physical-device builds and has an explicit simulator-safe unavailable/fallback path.
11. Camera/session lifecycle ownership is explicit: starting, stopping, attaching/detaching preview, repeated appearance/disappearance, and deinitialization cannot create duplicate sessions or obvious retain cycles.
12. Camera authorization states are represented truthfully and denied/restricted/unavailable states fail closed with visible non-camera UI rather than fabricated preview evidence.
13. Existing Swift 6 strict-concurrency constraints are respected; unsafe global/shared mutable state is not introduced merely to satisfy NextLevel integration.
14. Existing CameraService and simulator-fallback seams are preserved or evolved coherently; no conflicting second camera architecture is created without justification.
15. ContentView or the appropriate capture root actually presents the new preview surface and a usable status/placeholder state.
16. Tests or deterministic validation cover at least bridge state/lifecycle decisions and simulator/unavailable behavior where executable testing is practical.
17. Project-file/source membership remains coherent and NextLevel stays linked only where required.
18. Available build/test/static validation is run truthfully. If xcodebuild/device execution is unavailable in the builder environment, that limitation is explicitly reported and no native-device success is claimed.
19. git diff --check passes, git diff -- TASKS.md is empty, and exact changed-file/privacy review is recorded.
20. PL-0069_CODEX_LOG_V01.md links prompt/criteria, records implementation commit, exact files, commands/results/limitations, remote visibility, and ends exactly READY_FOR_INDEPENDENT_AUDIT.

## Closure

Builder validation never self-closes PL-0069. ChatGPT independently audits the actual GitHub source/diff/evidence before the task may be checked complete or PL-0070 may start.
