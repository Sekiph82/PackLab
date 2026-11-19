"""PL-0358 static safety contract for the optional signed IPA workflow."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
SIGNED = WORKFLOWS / "packlab-capture-signed-ipa.yml"
UNSIGNED = WORKFLOWS / "packlab-capture-macos.yml"
CONFIGURED = "steps.signing-inputs.outputs.configured == 'true'"
SECRET_REF = re.compile(r"secrets\.([A-Za-z0-9_]+)")
SIGNING_SUFFIXES = (".p12", ".pfx", ".cer", ".mobileprovision", ".keychain", ".keychain-db")


def _load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    # PyYAML (YAML 1.1) parses the bare `on` key as boolean True.
    data["on"] = data.pop(True)
    return data


def _job() -> dict[str, Any]:
    jobs = _load(SIGNED)["jobs"]
    assert list(jobs) == ["capture-signed-ipa"]
    return jobs["capture-signed-ipa"]


def _step(job: dict[str, Any], name: str) -> dict[str, Any]:
    matches = [step for step in job["steps"] if step.get("name") == name]
    assert len(matches) == 1, name
    return matches[0]


def test_unsigned_path_stays_default_and_secret_free() -> None:
    text = UNSIGNED.read_text(encoding="utf-8")
    workflow = _load(UNSIGNED)
    assert {"push", "pull_request"} <= set(workflow["on"])
    assert "secrets." not in text
    assert all("environment" not in job for job in workflow["jobs"].values())
    assert text.count("CODE_SIGNING_ALLOWED=NO") >= 2
    assert "PACKLAB_SIGNING_STATE: UNSIGNED" in text
    assert "SIGNED" not in text.replace("UNSIGNED", "")


def test_signed_workflow_is_manual_main_only_and_environment_gated() -> None:
    workflow = _load(SIGNED)
    assert set(workflow["on"]) == {"workflow_dispatch"}
    assert workflow["permissions"] == {"contents": "read"}
    inputs = workflow["on"]["workflow_dispatch"]["inputs"]
    assert inputs["upload_signed_ipa"]["default"] is False
    job = _job()
    assert job["environment"] == "ios-signing"
    assert job["permissions"] == {"contents": "read"}
    assert "github.event_name == 'workflow_dispatch'" in job["if"]
    assert "github.ref == 'refs/heads/main'" in job["if"]
    assert job["timeout-minutes"] <= 60


def test_no_pull_request_event_can_reach_any_secret() -> None:
    for path in sorted(WORKFLOWS.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        if "secrets." not in text:
            continue
        triggers = set(_load(path)["on"])
        assert not triggers & {"pull_request", "pull_request_target", "workflow_run"}, path.name


def test_secrets_only_enter_through_step_env_and_never_through_run() -> None:
    text = SIGNED.read_text(encoding="utf-8")
    workflow = _load(SIGNED)
    job = _job()
    assert "secrets" not in str(workflow.get("env", "")) + str(job.get("env", ""))
    env_refs: list[str] = []
    secret_env_names: set[str] = set()
    for step in job["steps"]:
        run = step.get("run", "")
        assert "${{" not in run, step["name"]
        assert not re.search(r"set\s+-[a-wyz]*x|set\s+-o\s+xtrace|bash\s+-x", run), step["name"]
        for key, value in (step.get("env") or {}).items():
            refs = SECRET_REF.findall(str(value))
            env_refs.extend(refs)
            if refs and "!=" not in str(value):
                secret_env_names.add(key)
        assert "secrets." not in str(step.get("with", "")), step["name"]
        if any(SECRET_REF.search(str(value)) for value in (step.get("env") or {}).values()):
            assert CONFIGURED in step.get("if", "") or step["name"].startswith("Check signing")
            assert "uses" not in step, "secrets must not be handed to third-party actions"
    # Every textual secret reference is one of the audited step-env mappings.
    assert len(SECRET_REF.findall(text)) == len(env_refs)
    assert set(env_refs) == {
        "PACKLAB_IOS_CERTIFICATE_P12_BASE64",
        "PACKLAB_IOS_CERTIFICATE_PASSWORD",
        "PACKLAB_IOS_PROVISIONING_PROFILE_BASE64",
    }
    allowed_uses = (
        re.compile(r"""printf '%s' "\$(\w+)" \| base64 --decode > "\$signing_dir/[\w.]+"$"""),
        re.compile(r"""-P "\$(PACKLAB_IOS_CERTIFICATE_PASSWORD)" -T /usr/bin/codesign"""),
    )
    for step in job["steps"]:
        for line in step.get("run", "").splitlines():
            for name in secret_env_names:
                if name in line:
                    assert any(p.search(line.strip()) for p in allowed_uses), line
                    assert "echo" not in line and "tee" not in line, line


def test_absent_credentials_skip_and_partial_credentials_fail() -> None:
    check = _job()["steps"][0]
    assert check["name"] == "Check signing inputs without reading their values"
    assert all(str(value).endswith("!= '' }}") for value in check["env"].values())
    assert "configured=false" in check["run"] and "SKIPPED_CREDENTIALS_ABSENT" in check["run"]
    assert "partially configured" in check["run"] and "exit 1" in check["run"]
    for step in _job()["steps"][1:-1]:
        assert CONFIGURED in step["if"], step["name"]


def test_keychain_and_signing_material_are_always_cleaned_up() -> None:
    job = _job()
    cleanup = job["steps"][-1]
    assert cleanup["name"] == "Delete temporary keychain and signing material"
    assert "always()" in cleanup["if"]
    assert "security delete-keychain" in cleanup["run"]
    assert 'rm -rf "$signing_dir"' in cleanup["run"]
    assert "Provisioning Profiles/$profile_uuid.mobileprovision" in cleanup["run"]
    install = _step(job, "Install signing material into a temporary keychain")["run"]
    assert "umask 077" in install
    assert 'keychain="$signing_dir/packlab-signing.keychain-db"' in install
    assert 'keychain_password="$(openssl rand -hex 32)"' in install
    assert "-T /usr/bin/codesign" in install and " -A " not in install


def test_no_signing_material_is_uploaded() -> None:
    uploads = [
        step
        for step in _job()["steps"]
        if str(step.get("uses", "")).startswith("actions/upload-artifact@")
    ]
    assert len(uploads) == 2
    for step in uploads:
        assert re.fullmatch(r"actions/upload-artifact@[0-9a-f]{40}", step["uses"])
        assert step["with"]["retention-days"] == 1
        paths = [p.strip() for p in str(step["with"]["path"]).splitlines() if p.strip()]
        assert len(paths) == 1
        path = paths[0]
        assert path.endswith(("PackLabCapture.ipa", "packlab-capture-signed-ipa-provenance.json"))
        assert "packlab-signing" not in path and not path.endswith(SIGNING_SUFFIXES)
    ipa_upload = _step(_job(), "Preserve signed IPA for one day (owner opt-in)")
    assert "inputs.upload_signed_ipa" in ipa_upload["if"]


def test_signed_ipa_is_verified_and_labelled_signed() -> None:
    job = _job()
    verify = _step(job, "Verify exported IPA signature and identity")["run"]
    lines = [line.strip() for line in verify.splitlines()]
    assert lines[0] == "set -euo pipefail"
    command = '/usr/bin/codesign --verify --deep --strict "$app_path" > /dev/null 2>&1'
    assert lines.count(command) == 1
    assert not any("codesign --verify" in line and "||" in line for line in lines)
    summary = next(i for i, line in enumerate(lines) if "Signing state: SIGNED" in line)
    assert lines.index(command) < summary
    assert "embedded.mobileprovision" in verify
    provenance = _step(job, "Prepare signed IPA provenance sidecar")
    assert provenance["env"]["PACKLAB_ARTIFACT_TYPE"] == "ios_signed_ipa"
    assert provenance["env"]["PACKLAB_SIGNING_STATE"] == "SIGNED"
    assert "ios_artifact_provenance.py verify" in provenance["run"]
    patch = _step(job, "Apply runner-local manual signing to the app target only")["run"]
    assert "'PRODUCT_BUNDLE_IDENTIFIER = com.packlab.capture;'" in patch
    assert "len(hits) != 1" in patch


def test_actions_are_pinned_and_nextlevel_resolution_matches_unsigned_archive() -> None:
    for step in _job()["steps"]:
        if "uses" in step:
            assert re.fullmatch(r"[\w./-]+@[0-9a-f]{40}", step["uses"]), step["uses"]
    name = "Resolve and validate the exact NextLevel package pin"
    archive_job = _load(UNSIGNED)["jobs"]["capture-unsigned-device-archive"]
    assert _step(_job(), name)["run"] == _step(archive_job, name)["run"]


# PL-0358 security review V01 (P2-1, P3-1..P3-4): Actions logs on this public repo are
# world-readable, so nothing derived from the certificate or profile may be printed.
RUN_DENYLIST = (
    re.compile(r"\bprintenv\b"),
    re.compile(r"(?:^|[|;&]\s*)env(?:\s|$)"),
    re.compile(
        r"\b(?:cat|tail|head|less|more|xxd|od)\b[^|\n]*\.(?:plist|mobileprovision|log|p12|json)"
    ),
    re.compile(r"\bcms -D\b(?![^\n]*-o )"),
    re.compile(r"\bcms\b[^\n]*-o\s+(?:/dev/stdout|-)(?:\s|$)"),
    re.compile(r"\bplutil\s+-p\b"),
    re.compile(r"\bsecurity\s+(?:find-certificate|dump-keychain)\b"),
    re.compile(r"python3?\s+-m\s+json\.tool"),
    # Python one-liners may read signing.json only into a shell variable.
    re.compile(r"^(?!\s*\w+=\"\$\(python3 -c ).*\bpython3?\s+-c\b.*signing\.json"),
    re.compile(r"set\s+-[a-wyz]*x|set\s+-o\s+xtrace|bash\s+-x"),
    re.compile(r"\bbase64\b(?![^\n]*--decode >)"),
)


def _runs() -> list[tuple[str, str]]:
    return [(step["name"], step["run"]) for step in _job()["steps"] if "run" in step]


def test_run_blocks_never_dump_signing_derived_material() -> None:
    for name, run in _runs():
        for line in run.splitlines():
            for pattern in RUN_DENYLIST:
                assert not pattern.search(line), (name, line)
            if "find-identity" in line:
                assert "grep -Eq" in line, line
            if "$team_id" in line or "$profile_uuid" in line:
                assert (
                    "::add-mask::" in line
                    or re.match(r"\s*(?:team_id|profile_uuid)=\"\$\(python3 ", line)
                    or '/$profile_uuid.mobileprovision"' in line
                    or line.strip() == 'if [[ -n "$profile_uuid" ]]; then'
                ), (name, line)
            if "GITHUB_STEP_SUMMARY" in line:
                assert not re.search(r"team|profile_uuid|identity|signing\.json", line), line


def test_profile_derived_values_are_masked_and_validated() -> None:
    install = _step(_job(), "Install signing material into a temporary keychain")["run"]
    assert 'echo "::add-mask::$team_id"' in install
    assert 'echo "::add-mask::$profile_uuid"' in install
    assert install.index("::add-mask::$profile_uuid") < install.index("Provisioning Profiles")
    for message in (
        "Provisioning profile is expired or has no expiration date.",
        "Provisioning profile team identifier is missing or invalid.",
        "Provisioning profile does not cover com.packlab.capture.",
        "Provisioning profile type does not match the selected export method.",
        "Export method is not in the reviewed allow-list.",
    ):
        assert f"raise SystemExit('{message}')" in install, message
    assert "if method not in {'release-testing', 'debugging'}:" in install
    assert 'rm -f "$signing_dir/certificate.p12"' in install
    assert install.index("security import") < install.index('rm -f "$signing_dir/certificate.p12"')


def test_xcodebuild_failure_never_prints_the_log() -> None:
    archive = _step(_job(), "Archive and export signed PackLabCapture IPA")["run"]
    assert archive.count('> "$signing_dir/archive.log" 2>&1') == 1
    assert archive.count('> "$signing_dir/export.log" 2>&1') == 1
    assert archive.count("report_failure ") == 2
    assert "| tee" not in archive.split("report_failure()")[1].split("echo '- Signed")[0]
    body = archive.split("report_failure() {", 1)[1].split("\n}\n", 1)[0]
    assert len(body.splitlines()) == 5, body
    greps = re.findall(r"\bgrep\b[^\n;]*", body)
    assert greps == ['grep -ciE "$1" "$log" 2>/dev/null || echo 0'], greps
    # Every output line is an echo of counts produced by the counting helper only.
    for line in body.splitlines()[1:]:
        stripped = line.strip()
        assert stripped.startswith(("local log=", "_n() {", "echo ")), stripped
        if stripped.startswith("echo "):
            assert "$log" not in stripped and "$2" not in stripped, stripped
    assert not re.search(r"\b(?:cat|tail|head|sed|awk)\b", body)


def test_failure_report_emits_only_a_count(tmp_path: Path) -> None:
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash unavailable")
    archive = _step(_job(), "Archive and export signed PackLabCapture IPA")["run"]
    function = (
        "report_failure() {"
        + archive.split("report_failure() {", 1)[1].split("\n}\n", 1)[0]
        + "\n}\n"
    )
    log = tmp_path / "archive.log"
    log.write_text(
        'error: Provisioning profile "Secret Owner Profile" does not include signing '
        'certificate "Apple Distribution: Jane Private (ABCDE12345)".\n'
        "ERROR: team ABCDE12345 mismatch\nnote: Signing Identity: Jane Private\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [bash, "-c", function + 'report_failure archive "$1"', "_", log.as_posix()],
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    assert "failed with 2 error line(s); log kept on the runner only." in output
    assert "profile=1 certificate=1 entitlement=0 team=0 compile=0" in output
    for leaked in ("Jane", "ABCDE12345", "Secret Owner", "Apple Distribution"):
        assert leaked not in output


def test_keychain_is_deleted_before_uploads_and_cleanup_covers_outputs() -> None:
    names = [step["name"] for step in _job()["steps"]]
    early = names.index("Delete temporary keychain once signing is verified")
    assert names.index("Verify exported IPA signature and identity") < early
    assert early < names.index("Preserve signed IPA provenance sidecar for one day")
    run = _job()["steps"][early]["run"]
    assert 'security delete-keychain "$signing_dir/packlab-signing.keychain-db"' in run
    cleanup = _job()["steps"][-1]["run"]
    assert '"$RUNNER_TEMP/packlab-signed-export"' in cleanup
    assert '"$RUNNER_TEMP/packlab-capture-archive-derived-data"' in cleanup


def test_profile_is_installed_and_removed_in_both_xcode_profile_directories() -> None:
    job = _job()
    old = "$HOME/Library/MobileDevice/Provisioning Profiles"
    new = "$HOME/Library/Developer/Xcode/UserData/Provisioning Profiles"
    install = _step(job, "Install signing material into a temporary keychain")["run"]
    early = _step(job, "Delete temporary keychain once signing is verified")["run"]
    cleanup = _step(job, "Delete temporary keychain and signing material")["run"]
    for script in (install, early, cleanup):
        assert old in script and new in script
