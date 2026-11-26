# Real PackLab.exe click-through, round 1 (2026-11-22, owner Desktop, maximized, launched via Explorer)

Runtime: OwnerDev/current 8e80d6bf..d85cbcde, pythonw (no console). Screenshots: ~/.claude tool-results blobs referenced in session; key observations below.

## Functional defects
- F1 CRITICAL Measure & Design "Open built model…" -> "Open failed: 'NoneType' object has no attribute 'write'": under pythonw sys.stdout/sys.stderr are None and a library (open3d?) writes to stdout. Any print/progress output crashes features only in the real app. Fix at startup (redirect None streams to a log file / devnull) + find the writer.
- F2 Project open fails ("project cannot be opened") when AppData is redirected (MSIX virtualization seen when launched from the Claude app; same class: junctions/cloud-synced folders): project_layout.path compares Path.resolve() of the file vs the area root inconsistently -> "project path escapes its area". Make the containment check robust (no resolve of non-existing/redirected paths; compare lexically normalized paths after safe_relative_path, or resolve both the same way).
- F3 Two PackLab instances can run; the second silently has no project (lock). Single-instance guard: focus the running window instead.
- F4 Project open failure only appears in the status bar in tiny text; show a clear dialog with the reason and what to do.
- F5 Window restored partly off-screen (title bar above the screen top / right edge with close button off-screen). Clamp restored geometry to the available screen.
- F6 File > Open Recent shows the raw folder path instead of the project name.
- F7 Package Families "Create Design Model" (jerrycan preset) takes ~15 s with no progress indication and the status line kept the stale closure message; jerrycan preview looks like a tapered lampshade with visible wireframe triangles (shape/appearance unconvincing).
- F8 Model Viewer "Fit" does not center/scale the model (stays small, off-centre).
- F9 Mask Correction page is a dead end: no way in the UI to open a correction session; all controls disabled forever.
- F10 Exports page: Format dropdown empty when no source; full-width "Cancel" button with no purpose; jargon text (DEFERRED_OWNER_VALIDATION) without plain explanation.
- F11 Settings: "Build revision: unknown" (should show the deployed commit); only 2 of 6 engines show a version after Re-check.
- F12 Library: Add to library / Create SKU enabled when they cannot work; feedback appears in two different places (top line and bottom status).
- F13 Editor page: two full-width fields + full-width button in a mostly empty page; jargon status line.
- F14 Jobs/Activity dock disappears after visiting Capture Inbox (content overflow) and stays gone.
- F15 File/folder dialogs open in the user home showing hidden dot-folders (.aider, .cargo…); default to Documents/PackLab or the project folder.
- F16 Reconstruction page is empty unless a build is running: no list of scans/builds, no history.

## Visual defects (also in PL-0464)
- V1 navigation labels truncated; V2 empty Scene/Properties docks; V3 Jobs dock too tall when idle; V4 no page headers / unlabeled fields; V5 duplicated window title; V6 stray scrollbar stub; V7 QR huge and pushes content off-screen, list clipped; V8 technical rows (UUID/sha256) instead of human text; V9 English-only.

## Round 2 notes (OwnerDev 902d33e4)
- OK: receiver auto-started at launch for paired iPhone17,3 (listening 0.0.0.0:8443, no pairing code issued) - PL-0480 verified in the real window.
- R2-1 LOW: auto-started receiver line still says "scan the QR code in the iPhone app" while no QR is shown; should read "paired phones can send".
