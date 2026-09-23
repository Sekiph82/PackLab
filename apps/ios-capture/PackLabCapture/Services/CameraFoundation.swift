import Foundation

public enum PreviewSurfaceState: Sendable, Equatable {
    case loading
    case running
    case denied
    case restricted
    case simulatorUnavailable
    case unavailable
    case error(String)
}

/// Framework-free lifecycle policy used by the preview adapter and its tests.
public struct PreviewLifecyclePolicy: Sendable, Equatable {
    public private(set) var isStarted = false
    public private(set) var attachmentCount = 0

    public init() {}

    @discardableResult
    public mutating func startIfNeeded() -> Bool {
        guard !isStarted else { return false }
        isStarted = true
        return true
    }

    @discardableResult
    public mutating func stopIfNeeded() -> Bool {
        guard isStarted else { return false }
        isStarted = false
        return true
    }

    public mutating func attach() { attachmentCount += 1 }
    public mutating func detach() { attachmentCount = max(0, attachmentCount - 1) }
}

#if canImport(UIKit) && canImport(AVFoundation) && canImport(NextLevel)
import AVFoundation
import NextLevel
import UIKit

/// UIKit owns the actual NextLevel preview layer; SwiftUI only presents it.
@MainActor
public final class NextLevelPreviewViewController: UIViewController {
    private let nextLevel: NextLevel
    private let statusLabel = UILabel()
    private var lifecycle = PreviewLifecyclePolicy()
    private var previewLayer: AVCaptureVideoPreviewLayer?

    public init(nextLevel: NextLevel = .shared) {
        self.nextLevel = nextLevel
        super.init(nibName: nil, bundle: nil)
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) { nil }

    public override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .black
        statusLabel.textColor = .white
        statusLabel.textAlignment = .center
        statusLabel.numberOfLines = 0
        statusLabel.text = "Preparing camera…"
        statusLabel.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(statusLabel)
        NSLayoutConstraint.activate([
            statusLabel.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 16),
            statusLabel.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -16),
            statusLabel.centerYAnchor.constraint(equalTo: view.centerYAnchor)
        ])
        attachPreviewIfPossible()
    }

    public override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        guard lifecycle.startIfNeeded() else { return }
        nextLevel.start()
        statusLabel.text = "Camera preview running"
    }

    public override func viewDidDisappear(_ animated: Bool) {
        super.viewDidDisappear(animated)
        guard lifecycle.stopIfNeeded() else { return }
        nextLevel.stop()
        detachPreview()
    }

    deinit { nextLevel.stop() }

    private func attachPreviewIfPossible() {
        lifecycle.attach()
        let layer = nextLevel.previewLayer
        layer.videoGravity = .resizeAspectFill
        layer.frame = view.bounds
        view.layer.insertSublayer(layer, at: 0)
        previewLayer = layer
        statusLabel.isHidden = true
    }

    private func detachPreview() {
        previewLayer?.removeFromSuperlayer()
        previewLayer = nil
        lifecycle.detach()
    }
}

public struct NextLevelPreviewBridge: UIViewControllerRepresentable {
    public init() {}
    public func makeUIViewController(context: Context) -> NextLevelPreviewViewController { NextLevelPreviewViewController() }
    public func updateUIViewController(_ controller: NextLevelPreviewViewController, context: Context) {}
}
#else
/// Simulator and non-Apple builds never manufacture image data.
public struct NextLevelPreviewBridge: Sendable { public init() {} }
#endif
