# iOS diagnostics boundary

`DiagnosticsLogger` is a local actor with bounded retention. It stores structured level/category/code/message entries up to a configured capacity and supports explicit clearing. It does not accept image data, capture payloads, credentials, account identifiers, file paths, or device identifiers as part of its structured model.

`DiagnosticsEnvironment` is intentionally limited to app version, build number, and a sorted capability summary. Callers must provide non-sensitive event codes and messages. `DiagnosticsExporter.prepareUserInitiatedExport` snapshots the bounded buffer and prepares local JSON data for a user-controlled share/save action. It never performs silent upload or network transfer.

Actual transfer, server endpoints, authentication, retention beyond the in-memory bound, and user-facing share-sheet wiring are deferred to later approved work. Native Swift/Xcode compilation and UI integration require the authorized macOS boundary; Windows validation is limited to static source/project checks.
