# PackLab cache and local-data policy

PackLab keeps regenerable processing state outside tracked source. The path helpers in `core/src/packlab_core/cache_paths.py` distinguish three concepts:

- **Cache**: dependency/tool metadata and reusable, disposable local state.
- **Temporary workspace**: per-job reconstruction scratch and intermediates that can be regenerated or discarded after a job.
- **Durable project data**: user-owned projects, local scans, source evidence, and other data that must not be deleted automatically.

Default roots are platform-safe: `%LOCALAPPDATA%/PackLab` on Windows, `~/Library/Caches/PackLab` on macOS, and `$XDG_CACHE_HOME/packlab` or `~/.cache/packlab` on Linux. Durable data uses platform application-data locations rather than the cache root.

`PACKLAB_CACHE_ROOT` and `PACKLAB_DATA_ROOT` provide explicit overrides for tests or advanced users. They are path controls only, not secret stores; credentials and private values must remain governed by the secrets policy and outside public Git. Tests should point both overrides at a temporary directory.

Directories are created lazily by `ensure_directories()` with `exist_ok=True`. PackLab never removes existing owner data as part of path resolution or directory creation.
