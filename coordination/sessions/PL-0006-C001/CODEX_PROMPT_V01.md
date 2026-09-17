# PL-0006-C001 — Codex Work Order V01

Task: **PL-0006 — Define semantic versioning rules for PackLab Studio, PackLab Capture and PackScan schema.**

Repository: `https://github.com/Sekiph82/PackLab`
Branch: `main`
Local workspace: `C:\Users\sekip\Desktop\PackLab`

## Authority

GitHub `main` is repository truth. Root `TASKS.md` is the only live H!veAI tracker. Do not edit `TASKS.md`.

Before material work, read:

1. `AGENTS.md`
2. `TASKS.md`
3. `IMPLEMENTATION_GUIDE.md`
4. `docs/architecture/REPOSITORY_STRUCTURE.md`
5. `docs/architecture/GLOSSARY.md`
6. `docs/architecture/adr/README.md`
7. `docs/architecture/adr/ADR-0001-monorepo-architecture.md`
8. `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md`
9. `coordination/AUDIT_POLICY.md`
10. `coordination/AUDIT_INDEX.md`
11. `coordination/sessions/PL-0005-C001/CHATGPT_AUDIT_V02.md`
12. this prompt
13. `coordination/sessions/PL-0006-C001/CHATGPT_AUDIT_CRITERIA_V01.md`

## Phase 0 — safe synchronization

Run and record:

```powershell
cd C:\Users\sekip\Desktop\PackLab
git rev-parse --show-toplevel
git remote -v
git status --porcelain
git fetch origin main --prune
git rev-list --left-right --count HEAD...origin/main
```

Rules:

- verify the Git root and origin identify `Sekiph82/PackLab`;
- if tracked local changes exist, STOP;
- if local is ahead or diverged, STOP;
- if local is only behind, use only `git merge --ff-only origin/main`;
- do not use reset, rebase, force-push, destructive checkout, silent stash, or `git clean`;
- before material work, prove local `HEAD == origin/main` and ahead/behind is `0 0`;
- historical untracked `.hiveai/` may remain local but must not be staged or committed.

Root `TASKS.md` must authorize PL-0006 as current task, status `READY`, actor `CODEX`. Otherwise STOP with `TASK_STATE_MISMATCH`.

## Objective

Create one canonical semantic-versioning policy for the three independently versioned public contracts:

- PackLab Studio;
- PackLab Capture;
- PackScan schema.

The policy must prevent accidental coupling between application releases and schema compatibility, and must define deterministic compatibility/migration behavior for future implementation tasks.

## Required artifact

Create:

`docs/architecture/VERSIONING_POLICY.md`

Do not create executable release tooling, manifests, package versions, CI workflows, app source, schema files, tags, or releases in PL-0006.

## Required policy content

### 1. Version domains

Define three independent version domains:

- **StudioVersion**
- **CaptureVersion**
- **PackScanSchemaVersion**

State explicitly that they are related but not numerically locked to each other.

Use SemVer-style `MAJOR.MINOR.PATCH` for Studio and Capture.

For PackScan schema, define an explicit semantic contract using `MAJOR.MINOR.PATCH`, with compatibility rules precise enough for later reader/writer implementation.

### 2. Studio / Capture SemVer rules

Define:

- MAJOR for incompatible public behavior/API/project-format/runtime contract changes;
- MINOR for backward-compatible features/capabilities;
- PATCH for backward-compatible fixes that do not change intended public compatibility contracts.

Clarify that internal refactoring alone does not require a major bump if public contracts remain compatible.

Clarify prerelease identifiers such as `0.1.0-alpha.1`, `0.1.0-beta.1`, `0.1.0-rc.1` are allowed for internal/test releases.

Clarify that `0.y.z` is development-stage and does not waive PackLab's explicit compatibility policy.

### 3. PackScan schema rules

Define exact schema bump semantics:

- **Schema MAJOR**: incompatible structural/semantic change where an older compliant reader cannot safely interpret the new package without explicit migration/support.
- **Schema MINOR**: backward-compatible additive change. New optional fields/files/enums are allowed only when older readers can safely ignore/handle them according to the schema contract.
- **Schema PATCH**: corrections/clarifications that do not change valid serialized meaning or required reader/writer behavior in a compatibility-breaking way.

Do not allow a patch bump to silently change required fields, units, coordinate conventions, checksum semantics, file meaning, or required interpretation.

### 4. Compatibility matrix rules

Define expected behavior for:

- older Studio reading newer PackScan schema;
- newer Studio reading older PackScan schema;
- older Capture writing schema consumed by newer Studio;
- newer Capture writing schema consumed by older Studio;
- unsupported future schema major;
- supported older schema major with migration path;
- same major with higher minor;
- same major/minor with higher patch.

Require explicit capability/version checks rather than guessing.

### 5. Reader/writer behavior contract

Define future reader behavior:

- reject unsupported future MAJOR cleanly;
- accept supported same-MAJOR newer MINOR only when additive/optional compatibility contract is preserved;
- accept PATCH differences within a supported major/minor when semantics remain compatible;
- never silently reinterpret units, coordinate frames, checksum rules, photo orientation, calibration meaning, or required file semantics;
- surface clear diagnostics for unsupported/incomplete/future versions;
- preserve immutable raw input during migration/import.

Define future writer behavior:

- emit one explicit schema version;
- never emit fields/files requiring behavior beyond the declared schema version;
- deterministic output contract belongs to later PackScan tasks;
- migration must produce a new derived representation rather than mutating original capture evidence.

### 6. Migration policy

Define:

- migrations are explicit and versioned;
- migration path identifies source and target schema versions;
- migrations are non-destructive relative to original `.packscan` evidence;
- migration failures are reported and do not partially overwrite source data;
- downgrade is not assumed to be possible;
- lossy migration must be explicit and user/audit visible;
- migration implementations belong to later schema/app tasks.

### 7. Application-to-schema compatibility declaration

Define that each Studio/Capture release must later declare:

- application version;
- PackScan schema versions it can read;
- schema version(s) it can write;
- migration support range;
- known incompatibilities.

Do not create the release manifest now. PL-0363/PL-0364 remain responsible for coordinated release numbering/manifest implementation.

### 8. Release bump examples

Include concrete examples for at least:

- Studio bug fix -> PATCH;
- new backward-compatible Studio tool -> MINOR;
- incompatible Studio project contract -> MAJOR;
- Capture UI-only fix -> PATCH;
- backward-compatible new capture capability -> MINOR;
- incompatible Capture persisted-session/API behavior -> MAJOR;
- optional PackScan metadata field -> schema MINOR;
- required field removal/rename -> schema MAJOR;
- documentation-only clarification with no serialized semantic change -> schema PATCH or no schema bump, with rule explaining which;
- unit/coordinate-system semantic change -> schema MAJOR;
- checksum interpretation change that breaks older readers -> schema MAJOR.

### 9. Git/release relationship

Define policy-level relationship only:

- Git tags/releases come later;
- one repository can contain different Studio/Capture/schema versions;
- task IDs are not versions;
- commit SHA is provenance, not semantic version;
- release artifacts must later record exact versions and commit provenance.

Do not create tags or releases.

### 10. Canonical examples and naming

Use unambiguous examples such as:

```text
StudioVersion: 0.1.0
CaptureVersion: 0.1.0
PackScanSchemaVersion: 1.0.0
```

State that these are examples unless explicitly marked as a frozen release decision. PL-0006 must not falsely declare a production release/version already shipped.

### 11. Boundary preservation

The policy must preserve:

- `.packscan` original input immutability;
- millimetres as canonical engineering units unless a future audited ADR changes that contract;
- explicit coordinate-system semantics;
- Scan Mesh / Scan Master / Design Model separation;
- public-repository safety;
- no release implementation before later release tasks.

### 12. Version source-of-truth hierarchy

Define future source-of-truth precedence:

1. serialized PackScan package declares its own schema version;
2. built Studio/Capture binaries expose their own app versions;
3. release manifest records compatibility/provenance later;
4. Git commit SHA supplements provenance but does not replace semantic versions.

Avoid creating duplicate live project trackers.

## Validation

Before commit, run:

```powershell
git diff --check
git add -N docs/architecture/VERSIONING_POLICY.md
git diff -- docs/architecture/VERSIONING_POLICY.md
```

Run explicit content checks proving the document covers all required domains, bump rules, compatibility cases, migration constraints, examples, and scope exclusions.

Run a scope check proving only the authorized policy file is changed before adding the log.

## Authorized changes

Create only:

1. `docs/architecture/VERSIONING_POLICY.md`
2. `coordination/sessions/PL-0006-C001/CODEX_LOG_V01.md`

Do not modify:

- `TASKS.md`;
- `AGENTS.md`;
- `CLAUDE.md`;
- `IMPLEMENTATION_GUIDE.md`;
- prior session artifacts;
- application/source/schema/runtime files;
- dependency/license register;
- ADRs unless an actual architecture contradiction is discovered. If an ADR is genuinely required, STOP and report `ADR_REQUIRED` rather than creating it opportunistically.

Do not start PL-0007.

## Required Codex log

Create `coordination/sessions/PL-0006-C001/CODEX_LOG_V01.md` containing:

- session metadata;
- starting commit;
- implementation commit;
- exact synchronization evidence;
- files read;
- files changed;
- implementation summary;
- validation commands, expected results, failure conditions and actual results;
- explicit compatibility-rule checks;
- scope/privacy/security checks;
- failures and fixes;
- push and remote visibility evidence;
- residual ambiguities/limitations;
- `AWAITING_AUDIT` handoff.

Do not predeclare the future commit SHA that contains the final log.

## Commit / push

Commit the policy first, then the log as a separate evidence commit if practical. Push safely without force. Verify remote `main` after each push or at minimum after the final push.

## Final response

Return only:

- `PL-0006-C001`;
- GitHub path/URL to `CODEX_LOG_V01.md`;
- `AWAITING_AUDIT`.

Then STOP.