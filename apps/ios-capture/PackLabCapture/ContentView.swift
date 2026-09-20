import SwiftUI

struct ContentView: View {
    var body: some View {
        NavigationStack {
            VStack(spacing: 12) {
                Text("PackLab Capture")
                    .font(.title)
                Text("Capture foundation ready")
                    .foregroundStyle(.secondary)
            }
            .padding()
            .navigationTitle("PackLab")
        }
    }
}

#Preview {
    ContentView()
}
