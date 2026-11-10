# PL-0436 Validation Criteria V06 — Lazy Resource-Gated Engine

1. Checkpoint metadata and available physical RAM are validated before any injected engine factory can run.
2. Capability probing checks the resource gate and injected prerequisites without constructing the engine.
3. A canceled inference, failed resource admission, unavailable prerequisite, or prerequisite exception does not invoke the factory.
4. A passing gate constructs one valid fake engine once, reuses it, and delegates inputs/results without altering order.
5. Invalid factory results and factory failures fail closed without leaking filesystem paths or exception details in public messages.
6. Synthetic tests do not import VGGT/PyTorch or read checkpoint content; no checkpoint/model is loaded or executed.
7. Focused tests, targeted Ruff, job JSON/log SHA validation, and `git diff --check` pass.
8. Zero Actions/paid CI, no PR, no source push to `main`, no native/Installer build, and no release claim. Owner VGGT access/local-use approval remains complete.
