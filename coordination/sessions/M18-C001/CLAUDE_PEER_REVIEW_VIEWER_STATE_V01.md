# CLAUDE_PEER_REVIEW viewer state V01 (PR #46, head 4d0bd98d)

Verdict: PASS (code); owner symptom fix NOT_VERIFIED.

Tests: 53 passed (persist, project_parts, model_viewer, build_model, texture_fallback, visual_polish; offscreen). New tests fail on base (via new attributes; the guard/off-thread asserts are real).

Thread safety OK: worker only parses and decimates (no Qt), queued signal, token drops stale results, no cancellation.

- MEDIUM shell.py:686/833: `_on_build_finished` still navigates to Model Viewer and replaces its view, then scene refresh may re-emit a background load. Likely unaddressed cause of vanishing images.
- MEDIUM shell.py:707: `measure.model is None` silently ignores "Object-only, scale and measure" for a new build. Add a status hint.
- LOW model_viewer.py:45: about 86 MB per cache entry (measured), not 50. Rapid clicks start parallel full reads.
- LOW measure_view.py:462: tests write the last-model key to the real HKCU QSettings.
