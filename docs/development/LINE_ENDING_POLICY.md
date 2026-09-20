# PackLab line-ending policy

PackLab stores repository text as UTF-8 with LF (`\n`) line endings. Every maintained text file should end with one final newline and should not contain trailing whitespace. `.editorconfig` provides the editor-facing defaults for Python, Swift, JSON/YAML/TOML, Markdown, PowerShell, and Xcode project files.

## Windows and macOS collaboration

Editors on Windows, macOS, and Linux may display or consume LF text normally. A tool that defaults to CRLF can create noisy whole-file diffs, so contributors should use an EditorConfig-aware editor and inspect `git diff --check` before committing. The policy applies to new or deliberately edited files; it does not authorize normalizing unrelated historical files.

Git checkout behavior remains a repository/user choice. PackLab does not modify user-global Git configuration. Contributors should inspect the repository attributes and their local Git settings when diagnosing churn, use a clean working tree before changing conversion settings, and verify the resulting diff rather than assuming a conversion is harmless. Do not use line-ending conversion as a synchronization shortcut.

## File-specific defaults

- UTF-8, LF, final newline, and trailing-whitespace trimming are the baseline.
- Python, Swift, PowerShell, and Xcode project files use four-space indentation.
- JSON, YAML, TOML, and Markdown use two-space indentation where indentation is meaningful.
- Existing files are not batch-rewritten solely to apply this policy; changes remain scoped to the authorized task.

Validation for changes is `git diff --check` plus an exact changed-file review. A future task may add `.gitattributes` if repository-wide Git normalization needs a separate audited decision; this policy does not silently modify global configuration.
