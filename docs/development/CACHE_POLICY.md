# PackLab cache and local-data policy

PackLab keeps regenerable processing state outside tracked source. The path helpers in `core/src/packlab_core/cache_paths.py` distinguish three concepts:

- **Cache**: dependency/tool metadata and reusable, disposable local state.
- **Temporary workspace**: per-job reconstruction scratch and intermediates that can be regenerated or discarded after a job.
- **Durable project data**: user-owned projects, local scans, source evidence, and other data that must not be deleted automatically.

Default roots are platform-safe: `%LOCALAPPDATA%/PackLab/cache` for cache and `%LOCALAPPDATA%/PackLab/data` for durable project data on Windows, `~/Library/Caches/PackLab` on macOS, and `$XDG_CACHE_HOME/packlab` or `~/.cache/packlab` on Linux. Windows temporary work remains `%LOCALAPPDATA%/PackLab/cache/work`; cache, work, and durable data are sibling concepts under the PackLab parent, and durable data is never beneath the cache root.

`PACKLAB_CACHE_ROOT` and `PACKLAB_DATA_ROOT` provide explicit overrides for tests or advanced users. The public path-resolution flow rejects equal roots and any ancestor/descendant overlap in either direction with an actionable error; only non-overlapping cache/data roots are accepted. The workspace may remain beneath the disposable cache root. They are path controls only, not secret stores; credentials and private values must remain governed by the secrets policy and outside public Git. Tests should point both overrides at separate temporary sibling paths.

Directories are created lazily by `ensure_directories()` with `exist_ok=True`. PackLab never removes existing owner data as part of path resolution or directory creation.
