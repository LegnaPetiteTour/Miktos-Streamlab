//
//  ContentView.swift
//  Miktos Streamlab - Mobile Camera Native
//
//  Main UI for camera streaming
//

import SwiftUI
import AVFoundation

struct ContentView: View {
    @StateObject private var cameraManager = CameraManager()
    @StateObject private var streamer = SRTStreamer()
    
    @State private var serverIP: String = ""
    @State private var serverPort: String = "9001"
    @State private var isStreaming: Bool = false
    @State private var showError: Bool = false
    @State private var errorMessage: String = ""
    
    var body: some View {
        ZStack {
            // Camera Preview (background)
            if cameraManager.isAuthorized {
                CameraPreviewView(session: cameraManager.captureSession)
                    .edgesIgnoringSafeArea(.all)
            }
            
            // Overlay UI
            VStack {
                // Top bar - Status
                HStack {
                    Circle()
                        .fill(isStreaming ? Color.red : Color.gray)
                        .frame(width: 12, height: 12)
                    Text(isStreaming ? "STREAMING" : "READY")
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(.white)
                    
                    Spacer()
                    
                    if isStreaming {
                        Text(streamer.statistics)
                            .font(.system(size: 12, design: .monospaced))
                            .foregroundColor(.white)
                    }
                }
                .padding()
                .background(Color.black.opacity(0.7))
                
                Spacer()
                
                // Bottom controls
                VStack(spacing: 20) {
                    if !isStreaming {
                        // Server configuration
                        VStack(spacing: 15) {
                            TextField("Server IP (e.g. 192.168.1.100)", text: $serverIP)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .keyboardType(.decimalPad)
                                .autocapitalization(.none)
                            
                            TextField("Port", text: $serverPort)
                                .textFieldStyle(RoundedBorderTextFieldStyle())
                                .keyboardType(.numberPad)
                        }
                        .padding(.horizontal)
                    }
                    
                    // Start/Stop button
                    Button(action: {
                        if isStreaming {
                            stopStreaming()
                        } else {
                            startStreaming()
                        }
                    }) {
                        Text(isStreaming ? "STOP STREAMING" : "START STREAMING")
                            .font(.system(size: 18, weight: .bold))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(isStreaming ? Color.red : Color.green)
                            .cornerRadius(10)
                    }
                    .padding(.horizontal)
                    .disabled(!cameraManager.isAuthorized || serverIP.isEmpty)
                }
                .padding(.bottom, 40)
                .background(
                    LinearGradient(
                        gradient: Gradient(colors: [Color.clear, Color.black.opacity(0.8)]),
                        startPoint: .top,
                        endPoint: .bottom
                    )
                )
            }
        }
        .alert("Error", isPresented: $showError) {
            Button("OK", role: .cancel) { }
        } message: {
            Text(errorMessage)
        }
        .onAppear {
            cameraManager.requestAuthorization()
            
            // Try to load saved server IP
            if let savedIP = UserDefaults.standard.string(forKey: "serverIP") {
                serverIP = savedIP
            }
        }
    }
    
    private func startStreaming() {
        // Save server IP for next time
        UserDefaults.standard.set(serverIP, forKey: "serverIP")
        
        // Validate inputs
        guard !serverIP.isEmpty else {
            showError(message: "Please enter server IP address")
            return
        }
        
        guard let port = Int(serverPort), port > 0, port < 65536 else {
            showError(message: "Invalid port number")
            return
        }
        
        // Start camera
        cameraManager.startCapture()
        
        // Start streaming
        let srtURL = "srt://\(serverIP):\(port)?mode=caller&latency=80"
        streamer.connect(to: srtURL, cameraManager: cameraManager) { success, error in
            if success {
                isStreaming = true
            } else {
                cameraManager.stopCapture()
                showError(message: error ?? "Failed to start streaming")
            }
        }
    }
    
    private func stopStreaming() {
        streamer.disconnect()
        cameraManager.stopCapture()
        isStreaming = false
    }
    
    private func showError(message: String) {
        errorMessage = message
        showError = true
    }
}

// Camera Preview using UIViewRepresentable
struct CameraPreviewView: UIViewRepresentable {
    let session: AVCaptureSession
    
    func makeUIView(context: Context) -> UIView {
        let view = UIView(frame: .zero)
        let previewLayer = AVCaptureVideoPreviewLayer(session: session)
        previewLayer.videoGravity = .resizeAspectFill
        view.layer.addSublayer(previewLayer)
        context.coordinator.previewLayer = previewLayer
        return view
    }
    
    func updateUIView(_ uiView: UIView, context: Context) {
        if let previewLayer = context.coordinator.previewLayer {
            DispatchQueue.main.async {
                previewLayer.frame = uiView.bounds
            }
        }
    }
    
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }
    
    class Coordinator {
        var previewLayer: AVCaptureVideoPreviewLayer?
    }
}

// Preview for SwiftUI canvas
struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
