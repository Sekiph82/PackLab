# ADR-0002 — M06 viewport backend

Status: accepted for M06 implementation pending independent audit  
Date: 2026-09-27  
Scope: PL-0151 through PL-0157

## Decision

PackLab Studio M06 uses a PackLab-owned viewport adapter backed by PySide6
`QImage`/`QPainter` software rasterization. Backend-specific calls stay inside
the adapter. No new third-party viewport dependency is added or selected.

## Alternatives compared

| Candidate | Local evidence | Strengths | Limitations |
| --- | --- | --- | --- |
| Qt raster `QImage`/`QPainter` | Executed deterministic 1k/10k/50k point render proxies under the repository's Python 3.12/PySide6 environment | Windows-compatible, headless/offscreen-capable, no added dependency, deterministic image export | Software proxy; large scenes need display budgets; advanced picking/shaders remain PackLab seams |
| Qt OpenGL offscreen context | Executed a `QOffscreenSurface`/`QOpenGLContext` probe | Native OpenGL path is Windows-compatible and could support large GPU scenes | Context/native availability is environment-dependent; this host evidence is not a physical GPU benchmark; more native/shader coupling and harder headless tests |

The reproducible evidence is committed at:

`https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/evidence/M06-viewport-spike-v01.json`

The command is:

```text
QT_QPA_PLATFORM=offscreen uv run --locked python tools/viewport_spike.py --output docs/architecture/evidence/M06-viewport-spike-v01.json
```

## Compatibility and license

Both candidates are PySide6-compatible and Windows-capable. The selected
backend uses the already declared and locked `PySide6>=6.8,<7` dependency and
does not change `pyproject.toml` or `uv.lock`. Qt for Python licensing remains
the existing LGPLv3/GPLv3 or commercial-route review recorded in the
dependency register; this ADR is not a distribution clearance.

## Limitations

The spike measured software/offscreen proxies only. It did not establish
physical GPU throughput, native-driver performance, or calibrated measurement
accuracy. PL-0157 owns the reproducible display-budget benchmark, and M09 owns
physical measurement accuracy. No M07 reconstruction engine is selected here.
