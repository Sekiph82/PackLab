# PackLab configuration

PackLab configuration is typed and loaded with deterministic precedence:

```text
defaults < user config < explicit project config < environment overrides
```

The user file is platform-safe (`%APPDATA%/PackLab/config.toml` on Windows, `~/Library/Application Support/PackLab/config.toml` on macOS, and `$XDG_CONFIG_HOME/packlab/config.toml` or `~/.config/packlab/config.toml` on Linux). A project file is used only when the caller supplies its explicit path. Missing files use defaults.

Supported keys are `log_level` (`DEBUG`, `INFO`, `WARNING`, `ERROR`), `telemetry_enabled` (boolean), `diagnostics_retention_days` (integer 1–365), and `cache_root` (path string or null). Unknown keys, malformed TOML, wrong types, invalid levels, and unsafe retention values raise actionable `ConfigError` messages; values are not silently coerced.

Environment overrides are `PACKLAB_LOG_LEVEL`, `PACKLAB_TELEMETRY_ENABLED`, `PACKLAB_DIAGNOSTICS_RETENTION_DAYS`, and `PACKLAB_CACHE_ROOT`. They are configuration controls only, not a secret store. No credentials or secret values belong in persisted config, examples, or logs.

The implementation is a foundation service. It does not own PackScan schema truth, external-engine settings, network transfer, or UI presentation configuration.
