//
//  SRTStreamer.swift
//  Miktos Streamlab - Mobile Camera Native
//
//  Handles H.264 encoding and SRT streaming
//

import Foundation
import AVFoundation
import VideoToolbox

class SRTStreamer: ObservableObject {
    @Published var statistics: String = "0 Kbps"
    
    private var encoder: VTCompressionSession?
    private var outputStream: OutputStream?
    private var isConnected = false
    
    private var frameCount: Int = 0
    private var bytesSent: Int = 0
    private var lastStatsUpdate = Date()
    
    private let encoderQueue = DispatchQueue(label: "com.miktos.encoder", qos: .userInitiated)
    
    func connect(to urlString: String, cameraManager: CameraManager, completion: @escaping (Bool, String?) -> Void) {
        encoderQueue.async { [weak self] in
            guard let self = self else { return }
            
            // Parse SRT URL
            guard let url = URL(string: urlString) else {
                DispatchQueue.main.async {
                    completion(false, "Invalid URL")
                }
                return
            }
            
            guard let host = url.host, let port = url.port else {
                DispatchQueue.main.async {
                    completion(false, "Invalid host or port")
                }
                return
            }
            
            // Setup H.264 encoder
            guard self.setupEncoder() else {
                DispatchQueue.main.async {
                    completion(false, "Failed to setup encoder")
                }
                return
            }
            
            // Connect to SRT server
            var readStream: Unmanaged<CFReadStream>?
            var writeStream: Unmanaged<CFWriteStream>?
            
            CFStreamCreatePairWithSocketToHost(
                nil,
                host as CFString,
                UInt32(port),
                &readStream,
                &writeStream
            )
            
            guard let outputStream = writeStream?.takeRetainedValue() as OutputStream? else {
                DispatchQueue.main.async {
                    completion(false, "Failed to create output stream")
                }
                return
            }
            
            self.outputStream = outputStream
            outputStream.open()
            
            // Wait for connection
            Thread.sleep(forTimeInterval: 0.5)
            
            if outputStream.streamStatus == .open {
                self.isConnected = true
                
                // Set up frame callback
                cameraManager.setSampleBufferHandler { [weak self] sampleBuffer in
                    self?.encode(sampleBuffer: sampleBuffer)
                }
                
                // Start statistics updates
                self.startStatisticsTimer()
                
                DispatchQueue.main.async {
                    completion(true, nil)
                    print("✅ Connected to SRT server: \(host):\(port)")
                }
            } else {
                DispatchQueue.main.async {
                    completion(false, "Connection failed")
                }
            }
        }
    }
    
    func disconnect() {
        encoderQueue.async { [weak self] in
            guard let self = self else { return }
            
            self.isConnected = false
            
            // Clean up encoder
            if let encoder = self.encoder {
                VTCompressionSessionCompleteFrames(encoder, untilPresentationTimeStamp: .invalid)
                VTCompressionSessionInvalidate(encoder)
                self.encoder = nil
            }
            
            // Close stream
            self.outputStream?.close()
            self.outputStream = nil
            
            print("✅ Disconnected from SRT server")
        }
    }
    
    private func setupEncoder() -> Bool {
        var encoder: VTCompressionSession?
        
        let status = VTCompressionSessionCreate(
            allocator: kCFAllocatorDefault,
            width: 1920,
            height: 1080,
            codecType: kCMVideoCodecType_H264,
            encoderSpecification: nil,
            imageBufferAttributes: nil,
            compressedDataAllocator: nil,
            outputCallback: nil,
            refcon: nil,
            compressionSessionOut: &encoder
        )
        
        guard status == noErr, let encoder = encoder else {
            print("❌ Failed to create encoder: \(status)")
            return false
        }
        
        self.encoder = encoder
        
        // Configure encoder for streaming
        // Target bitrate: 5.5 Mbps (good quality for 1080p30)
        VTSessionSetProperty(encoder, key: kVTCompressionPropertyKey_AverageBitRate, value: 5_500_000 as CFNumber)
        
        // Limit bitrate peaks
        VTSessionSetProperty(encoder, key: kVTCompressionPropertyKey_DataRateLimits, value: [5_500_000, 1] as CFArray)
        
        // Keyframe interval: every 2 seconds (60 frames at 30fps)
        VTSessionSetProperty(encoder, key: kVTCompressionPropertyKey_MaxKeyFrameInterval, value: 60 as CFNumber)
        
        // Real-time encoding
        VTSessionSetProperty(encoder, key: kVTCompressionPropertyKey_RealTime, value: kCFBooleanTrue)
        
        // Profile: High (best quality)
        VTSessionSetProperty(encoder, key: kVTCompressionPropertyKey_ProfileLevel, value: kVTProfileLevel_H264_High_AutoLevel)
        
        // Allow frame reordering (B-frames) for better compression
        VTSessionSetProperty(encoder, key: kVTCompressionPropertyKey_AllowFrameReordering, value: kCFBooleanTrue)
        
        // Prepare encoder
        VTCompressionSessionPrepareToEncodeFrames(encoder)
        
        print("✅ H.264 encoder configured: 1080p30 @ 5.5Mbps")
        return true
    }
    
    private func encode(sampleBuffer: CMSampleBuffer) {
        guard isConnected, let encoder = encoder else { return }
        
        guard let imageBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        
        let presentationTime = CMSampleBufferGetPresentationTimeStamp(sampleBuffer)
        let duration = CMSampleBufferGetDuration(sampleBuffer)
        
        let status = VTCompressionSessionEncodeFrame(
            encoder,
            imageBuffer: imageBuffer,
            presentationTimeStamp: presentationTime,
            duration: duration,
            frameProperties: nil,
            infoFlagsOut: nil
        ) { [weak self] status, _, sampleBuffer in
            guard status == noErr, let sampleBuffer = sampleBuffer else { return }
            self?.send(encodedFrame: sampleBuffer)
        }
        
        if status != noErr {
            print("❌ Encode error: \(status)")
        }
    }
    
    private func send(encodedFrame sampleBuffer: CMSampleBuffer) {
        guard isConnected, let outputStream = outputStream else { return }
        guard outputStream.hasSpaceAvailable else { return }
        
        guard let dataBuffer = CMSampleBufferGetDataBuffer(sampleBuffer) else { return }
        
        // Get encoded data
        var length: Int = 0
        var dataPointer: UnsafeMutablePointer<Int8>?
        
        let status = CMBlockBufferGetDataPointer(
            dataBuffer,
            atOffset: 0,
            lengthAtOffsetOut: nil,
            totalLengthOut: &length,
            dataPointerOut: &dataPointer
        )
        
        guard status == kCMBlockBufferNoErr, let data = dataPointer else { return }
        
        // Send data
        let bytesWritten = outputStream.write(
            UnsafePointer<UInt8>(OpaquePointer(data)),
            maxLength: length
        )
        
        if bytesWritten > 0 {
            frameCount += 1
            bytesSent += bytesWritten
        }
    }
    
    private func startStatisticsTimer() {
        Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            guard let self = self, self.isConnected else { return }
            
            let elapsed = Date().timeIntervalSince(self.lastStatsUpdate)
            let kbps = Double(self.bytesSent * 8) / 1000.0 / elapsed
            let fps = Double(self.frameCount) / elapsed
            
            DispatchQueue.main.async {
                self.statistics = String(format: "%.0f Kbps | %.0f fps", kbps, fps)
            }
            
            self.bytesSent = 0
            self.frameCount = 0
            self.lastStatsUpdate = Date()
        }
    }
}
