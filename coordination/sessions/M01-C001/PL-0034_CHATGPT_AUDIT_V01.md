# PL-0034 — ChatGPT Strict Independent Audit V01

Decision: **CHANGES_REQUIRED**

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0034_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0034_CHATGPT_AUDIT_CRITERIA_V01.md
Builder log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0034_CODEX_LOG_V01.md

Audited implementation commit: `a7a6d9cbad2884f8fa98b0be179907e1cb2d576a`
Audited log commit: `00c96974461d3644cbdf2b654c5807d59b7bca58`

## Blocking finding

The registry currently models the `cuda` capability using only:

`("nvidia-smi", "--version")`

and marks the capability `AVAILABLE` whenever that executable returns successfully and any generic version-shaped token is parseable.

That is not sufficient evidence that CUDA runtime/toolkit capability is actually available. `nvidia-smi` is NVIDIA driver/NVML tooling, and its version output is not the same semantic fact as an installed/usable CUDA runtime or toolkit. The generic regex may also capture the NVIDIA-SMI/driver version rather than a CUDA version.

This violates the requirement to represent capabilities with accurate provenance and to separate executable discovery/version evidence from assumptions. It is the same class of error that the M00 host baseline explicitly guards against: hardware/driver metadata must not be promoted into a stronger CUDA capability claim.

The remaining registry behavior is sound: missing executables do not crash unrelated features, probe errors/malformed versions become UNKNOWN, OpenCascade stays unselected, and GPU brand/memory is not used.

## Criterion disposition

1-7: PASS  
8: **FAIL** — CUDA AVAILABLE is overstated from NVIDIA-SMI evidence.  
9: **FAIL** — executable evidence is promoted into a stronger capability assumption.  
10-19: PASS  
20: **FAIL** — a material capability-semantics defect remains.

Result: **17 / 20 PASS, 3 FAIL**

## Required remediation

Separate NVIDIA driver/NVML discovery from CUDA capability truth, or make the CUDA record conservative:

- NVIDIA-SMI presence/version may be recorded as driver/NVIDIA evidence;
- CUDA must become AVAILABLE only from a probe that directly establishes the intended CUDA capability;
- when only NVIDIA-SMI evidence exists, CUDA should remain UNKNOWN unless the frozen design explicitly defines that evidence as sufficient;
- never infer CUDA from GPU name, memory size, AdapterRAM, or generic version parsing.

Add tests proving:
- NVIDIA-SMI available by itself does not falsely establish CUDA runtime/toolkit availability;
- direct CUDA evidence can produce AVAILABLE with explicit provenance;
- missing and probe-error behavior remains conservative;
- OpenCascade binding remains unselected.

## Evidence boundary

GitHub source, tests, capability/provenance semantics and commit topology were independently inspected as E3. Builder-run local commands remain E1/E2 where not independently rerun.

Decision: **CHANGES_REQUIRED**
