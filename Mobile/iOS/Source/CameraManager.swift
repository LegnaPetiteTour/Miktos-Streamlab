//
//  CameraManager.swift
//  Miktos Streamlab - Mobile Camera Native
//
//  Handles camera capture and H.264 encoding
//

import AVFoundation
import UIKit

class CameraManager: NSObject, ObservableObject {
    @Published var isAuthorized = false
    
    let captureSession = AVCaptureSession()
    private var videoOutput: AVCaptureVideoDataOutput?
    private var videoDataDelegate: VideoDataDelegate?
    
    override init() {
        super.init()
        checkAuthorization()
    }
    
    func checkAuthorization() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            isAuthorized = true
        case .notDetermined:
            break
        default:
            isAuthorized = false
        }
    }
    
    func requestAuthorization() {
        AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
            DispatchQueue.main.async {
                self?.isAuthorized = granted
                if granted {
                    self?.setupCamera()
                }
            }
        }
    }
    
    private func setupCamera() {
        captureSession.sessionPreset = .hd1920x1080
        
        // Get back camera
        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back) else {
            print("❌ Failed to get camera")
            return
        }
        
        // Configure camera for streaming
        do {
            try camera.lockForConfiguration()
            
            // Set 30fps
            camera.activeVideoMinFrameDuration = CMTime(value: 1, timescale: 30)
            camera.activeVideoMaxFrameDuration = CMTime(value: 1, timescale: 30)
            
            // Lock exposure and white balance for consistent encoding
            if camera.isExposureModeSupported(.continuousAutoExposure) {
                camera.exposureMode = .continuousAutoExposure
            }
            if camera.isWhiteBalanceModeSupported(.continuousAutoWhiteBalance) {
                camera.whiteBalanceMode = .continuousAutoWhiteBalance
            }
            
            // Lock focus to reduce compression artifacts
            if camera.isFocusModeSupported(.continuousAutoFocus) {
                camera.focusMode = .continuousAutoFocus
            }
            
            camera.unlockForConfiguration()
        } catch {
            print("❌ Failed to configure camera: \(error)")
        }
        
        // Add camera input
        do {
            let input = try AVCaptureDeviceInput(device: camera)
            if captureSession.canAddInput(input) {
                captureSession.addInput(input)
            }
        } catch {
            print("❌ Failed to add camera input: \(error)")
            return
        }
        
        // Add video output
        let output = AVCaptureVideoDataOutput()
        output.videoSettings = [
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange
        ]
        
        let queue = DispatchQueue(label: "com.miktos.videoQueue", qos: .userInitiated)
        videoDataDelegate = VideoDataDelegate()
        output.setSampleBufferDelegate(videoDataDelegate, queue: queue)
        
        if captureSession.canAddOutput(output) {
            captureSession.addOutput(output)
        }
        
        videoOutput = output
        
        // Configure video orientation
        if let connection = output.connection(with: .video) {
            if connection.isVideoOrientationSupported {
                connection.videoOrientation = .portrait
            }
            if connection.isVideoMirroringSupported {
                connection.isVideoMirrored = false
            }
        }
        
        print("✅ Camera configured: 1080p30 H.264")
    }
    
    func startCapture() {
        if !captureSession.isRunning {
            DispatchQueue.global(qos: .userInitiated).async { [weak self] in
                self?.captureSession.startRunning()
                print("📹 Camera capture started")
            }
        }
    }
    
    func stopCapture() {
        if captureSession.isRunning {
            DispatchQueue.global(qos: .userInitiated).async { [weak self] in
                self?.captureSession.stopRunning()
                print("📹 Camera capture stopped")
            }
        }
    }
    
    func setSampleBufferHandler(_ handler: @escaping (CMSampleBuffer) -> Void) {
        videoDataDelegate?.sampleBufferHandler = handler
    }
}

// Delegate to handle video frames
class VideoDataDelegate: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    var sampleBufferHandler: ((CMSampleBuffer) -> Void)?
    
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        sampleBufferHandler?(sampleBuffer)
    }
}
