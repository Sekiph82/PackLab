import SwiftUI

struct ContentView: View {
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
            }
            .navigationTitle("PackLab")
        }
    }
}

#Preview {
    ContentView()
}
