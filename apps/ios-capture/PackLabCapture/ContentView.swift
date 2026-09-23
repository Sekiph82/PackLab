import SwiftUI

struct ContentView: View {
    @State private var showPoseDebug = false

    var body: some View {
        NavigationStack {
            ZStack {
                #if targetEnvironment(simulator)
                VStack(spacing: 12) {
                    Image(systemName: "camera.slash")
                        .font(.largeTitle)
                    Text("Camera unavailable in Simulator")
                        .font(.headline)
                    Text("No synthetic camera image is shown. Use an iPhone to preview a capture.")
                        .multilineTextAlignment(.center)
                        .foregroundStyle(.secondary)
                }
                .padding()
                #else
                NextLevelPreviewBridge()
                    .ignoresSafeArea()
                VStack {
                    Spacer()
                    Text("PackLab Capture")
                        .font(.headline)
                        .padding(8)
                        .background(.black.opacity(0.65), in: Capsule())
                        .foregroundStyle(.white)
                        .padding()
                }
                #endif
                if showPoseDebug {
                    VStack(alignment: .leading, spacing: 4) {
                        ForEach(PoseOverlayModel.make(visible: true, tracking: TrackingSnapshot(quality: .unavailable, poseEvidenceEligible: false), epoch: 0, pose: nil).lines, id: \.self) { line in
                            Text(line).font(.caption.monospaced()).foregroundStyle(.white)
                        }
                    }
                    .padding(8)
                    .background(.black.opacity(0.7), in: RoundedRectangle(cornerRadius: 8))
                    .padding()
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topTrailing)
                    .allowsHitTesting(false)
                }
            }
            .navigationTitle("PackLab")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button(showPoseDebug ? "Hide Debug" : "Show Debug") { showPoseDebug.toggle() }
                }
            }
        }
    }
}

#Preview {
    ContentView()
}
