# iOS diagnostics boundary

`DiagnosticsLogger` is a local actor with bounded retention and an enforced sanitization boundary. It stores structured level/category/code/message entries up to a configured capacity and redacts common secret-bearing values and private user/home paths before retention. It does not accept image data, capture payloads, credentials, account identifiers, file paths, or device identifiers as part of its structured model.

`DiagnosticsEnvironment` is intentionally limited to sanitized app version, build number, and a constrained sorted capability summary. Diagnostic strings are sanitized in the model initializers, so caller discipline is not the privacy boundary. `DiagnosticsExporter.prepareUserInitiatedExport` snapshots the bounded buffer and prepares local JSON data for a user-controlled share/save action. It never performs silent upload or network transfer.

Actual transfer, server endpoints, authentication, retention beyond the in-memory bound, and user-facing share-sheet wiring are deferred to later approved work. Native Swift/Xcode compilation and UI integration require the authorized macOS boundary; Windows validation is limited to static source/project checks.
