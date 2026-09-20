# iOS permission inventory

PackLab Capture currently declares only the camera permission required by its capture architecture:

- `NSCameraUsageDescription`: explains that the camera records product views for a capture session.

No photo-library usage description is declared. The current M01 foundation has no photo-library read/write flow; a future share/export API does not by itself require photo-library access. A photo-library permission must be added only if a later approved feature actually reads from or writes to the user’s library.

No local-network permission or Bonjour service declaration is declared. The current app has no network transport or local discovery implementation. Local-network access is a future M05 boundary and must be justified by the approved transfer design before adding a user-facing declaration or service identifier.

The permission strings contain no private service identifiers, account details, credentials, personal paths, or signing information. Native prompt behavior remains subject to macOS/Xcode and device/simulator verification.
