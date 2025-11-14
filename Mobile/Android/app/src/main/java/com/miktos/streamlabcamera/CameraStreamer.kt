package com.miktos.streamlabcamera

import android.content.Context
import android.hardware.camera2.CameraCaptureSession
import android.hardware.camera2.CameraDevice
import android.hardware.camera2.CameraManager
import android.hardware.camera2.CaptureRequest
import android.media.MediaCodec
import android.media.MediaCodecInfo
import android.media.MediaFormat
import android.os.Handler
import android.os.HandlerThread
import android.os.PowerManager
import android.util.Log
import java.io.IOException
import java.io.OutputStream
import java.net.Socket

class CameraStreamer(
    private val context: Context,
    private val statusCallback: (Boolean) -> Unit  // true = streaming, false = stopped
) {
    private val TAG = "CameraStreamer"
    
    private var cameraDevice: CameraDevice? = null
    private var captureSession: CameraCaptureSession? = null
    private var encoder: MediaCodec? = null
    private var socket: Socket? = null
    private var outputStream: OutputStream? = null
    private var wakeLock: PowerManager.WakeLock? = null
    
    private var cameraThread: HandlerThread? = null
    private var cameraHandler: Handler? = null
    private var encoderThread: HandlerThread? = null
    private var encoderHandler: Handler? = null
    
    private var isStreaming = false
    private var frameCount = 0
    
    // Video configuration
    private val VIDEO_WIDTH = 1920
    private val VIDEO_HEIGHT = 1080
    private val VIDEO_FPS = 30
    private val VIDEO_BITRATE = 6_000_000
    private val VIDEO_I_FRAME_INTERVAL = 2
    
    fun startStreaming(serverIp: String, serverPort: Int) {
        // Acquire wake lock to keep camera alive
        val powerManager = context.getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = powerManager.newWakeLock(
            PowerManager.PARTIAL_WAKE_LOCK,
            "MiktosCamera::StreamingWakeLock"
        )
        wakeLock?.acquire(2 * 60 * 60 * 1000L) // 2 hours max
        Log.d(TAG, "Wake lock acquired")
        
        // Initialize background threads
        encoderThread = HandlerThread("EncoderThread").apply { start() }
        encoderHandler = Handler(encoderThread!!.looper)
        
        cameraThread = HandlerThread("CameraThread").apply { start() }
        cameraHandler = Handler(cameraThread!!.looper)
        
        encoderHandler?.post {
            try {
                connectToServer(serverIp, serverPort)
                initializeEncoder()
                startCamera2()
                isStreaming = true
                statusCallback(true)
                Log.d(TAG, "Streaming pipeline initialized")
                
            } catch (e: Exception) {
                Log.e(TAG, "Error starting stream", e)
                cleanup()
                statusCallback(false)
            }
        }
    }
    
    private fun connectToServer(serverIp: String, serverPort: Int) {
        Log.d(TAG, "Connecting to $serverIp:$serverPort")
        socket = Socket(serverIp, serverPort)
        socket?.tcpNoDelay = true
        socket?.soTimeout = 5000
        socket?.keepAlive = true
        outputStream = socket?.getOutputStream()
        Log.d(TAG, "Connected to server")
    }
    
    private fun initializeEncoder() {
        Log.d(TAG, "Initializing H.264 encoder")
        
        val format = MediaFormat.createVideoFormat(
            MediaFormat.MIMETYPE_VIDEO_AVC,
            VIDEO_WIDTH,
            VIDEO_HEIGHT
        )
        
        format.setInteger(
            MediaFormat.KEY_COLOR_FORMAT,
            MediaCodecInfo.CodecCapabilities.COLOR_FormatSurface
        )
        format.setInteger(MediaFormat.KEY_BIT_RATE, VIDEO_BITRATE)
        format.setInteger(MediaFormat.KEY_FRAME_RATE, VIDEO_FPS)
        format.setInteger(MediaFormat.KEY_I_FRAME_INTERVAL, VIDEO_I_FRAME_INTERVAL)
        format.setInteger(MediaFormat.KEY_PROFILE, MediaCodecInfo.CodecProfileLevel.AVCProfileHigh)
        format.setInteger(MediaFormat.KEY_LEVEL, MediaCodecInfo.CodecProfileLevel.AVCLevel4)
        
        encoder = MediaCodec.createEncoderByType(MediaFormat.MIMETYPE_VIDEO_AVC)
        encoder?.configure(format, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
        
        Log.d(TAG, "Encoder configured")
    }
    
    private fun startCamera2() {
        try {
            val cameraManager = context.getSystemService(Context.CAMERA_SERVICE) as CameraManager
            val cameraId = cameraManager.cameraIdList[0] // Back camera
            
            // Set up encoder callback
            encoder?.setCallback(object : MediaCodec.Callback() {
                override fun onInputBufferAvailable(codec: MediaCodec, index: Int) {}
                
                override fun onOutputBufferAvailable(
                    codec: MediaCodec,
                    index: Int,
                    info: MediaCodec.BufferInfo
                ) {
                    handleEncodedFrame(codec, index, info)
                }
                
                override fun onError(codec: MediaCodec, e: MediaCodec.CodecException) {
                    Log.e(TAG, "Encoder error", e)
                }
                
                override fun onOutputFormatChanged(codec: MediaCodec, format: MediaFormat) {
                    Log.d(TAG, "Encoder format changed: $format")
                }
            }, encoderHandler)
            
            // Get encoder input surface and start
            val encoderSurface = encoder?.createInputSurface()
            encoder?.start()
            Log.d(TAG, "Encoder started")
            
            // Open camera
            cameraManager.openCamera(cameraId, object : CameraDevice.StateCallback() {
                override fun onOpened(camera: CameraDevice) {
                    Log.d(TAG, "Camera opened")
                    cameraDevice = camera
                    
                    try {
                        // Create capture session with encoder surface
                        val surfaces = listOf(encoderSurface!!)
                        
                        camera.createCaptureSession(surfaces, object : CameraCaptureSession.StateCallback() {
                            override fun onConfigured(session: CameraCaptureSession) {
                                Log.d(TAG, "Capture session configured")
                                captureSession = session
                                
                                try {
                                    // Build capture request targeting encoder surface
                                    val requestBuilder = camera.createCaptureRequest(CameraDevice.TEMPLATE_RECORD)
                                    requestBuilder.addTarget(encoderSurface)
                                    
                                    // Set FPS range
                                    requestBuilder.set(
                                        CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE,
                                        android.util.Range(VIDEO_FPS, VIDEO_FPS)
                                    )
                                    
                                    // Start repeating capture
                                    session.setRepeatingRequest(
                                        requestBuilder.build(),
                                        null,
                                        cameraHandler
                                    )
                                    
                                    Log.d(TAG, "Camera streaming to encoder")
                                    
                                } catch (e: Exception) {
                                    Log.e(TAG, "Error starting capture", e)
                                    statusCallback(false)
                                }
                            }
                            
                            override fun onConfigureFailed(session: CameraCaptureSession) {
                                Log.e(TAG, "Capture session configuration failed")
                                statusCallback(false)
                            }
                        }, cameraHandler)
                        
                    } catch (e: Exception) {
                        Log.e(TAG, "Error creating capture session", e)
                        statusCallback(false)
                    }
                }
                
                override fun onDisconnected(camera: CameraDevice) {
                    Log.d(TAG, "Camera disconnected")
                    cleanup()
                    statusCallback(false)
                }
                
                override fun onError(camera: CameraDevice, error: Int) {
                    Log.e(TAG, "Camera error: $error")
                    cleanup()
                    statusCallback(false)
                }
            }, cameraHandler)
            
        } catch (e: SecurityException) {
            Log.e(TAG, "Camera permission denied", e)
            statusCallback(false)
        } catch (e: Exception) {
            Log.e(TAG, "Error opening camera", e)
            statusCallback(false)
        }
    }
    
    private fun handleEncodedFrame(
        codec: MediaCodec,
        index: Int,
        info: MediaCodec.BufferInfo
    ) {
        try {
            val encodedData = codec.getOutputBuffer(index) ?: return
            
            if (info.size > 0 && isStreaming) {
                // Check if this is codec configuration (SPS/PPS)
                val isConfig = (info.flags and MediaCodec.BUFFER_FLAG_CODEC_CONFIG) != 0
                
                val data = ByteArray(info.size)
                encodedData.position(info.offset)
                encodedData.limit(info.offset + info.size)
                encodedData.get(data)
                
                // ALWAYS send codec config, and send keyframes + regular frames
                if (isConfig || (info.flags and MediaCodec.BUFFER_FLAG_KEY_FRAME) != 0 || info.flags == 0) {
                    outputStream?.write(data)
                    outputStream?.flush()
                    
                    when {
                        isConfig -> Log.d(TAG, "✅ Sent codec config (SPS/PPS): ${info.size} bytes")
                        (info.flags and MediaCodec.BUFFER_FLAG_KEY_FRAME) != 0 -> {
                            frameCount++
                            if (frameCount % 60 == 0) {
                                Log.d(TAG, "🔑 Keyframe #$frameCount: ${info.size} bytes")
                            }
                        }
                        else -> {
                            frameCount++
                            if (frameCount % 300 == 0) {
                                Log.d(TAG, "📹 Frame #$frameCount: ${info.size} bytes")
                            }
                        }
                    }
                }
            }
            
            codec.releaseOutputBuffer(index, false)
            
        } catch (e: IOException) {
            Log.e(TAG, "Error sending frame", e)
            stopStreaming()
        }
    }
    
    fun stopStreaming() {
        Log.d(TAG, "Stopping streaming...")
        isStreaming = false
        cleanup()
        statusCallback(false)
    }
    
    private fun cleanup() {
        Log.d(TAG, "Cleaning up resources")
        
        // Release wake lock first
        try {
            if (wakeLock?.isHeld == true) {
                wakeLock?.release()
                Log.d(TAG, "Wake lock released")
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error releasing wake lock", e)
        }
        wakeLock = null
        
        // Stop capture session
        try {
            captureSession?.stopRepeating()
        } catch (e: Exception) {
            // Ignore - camera might already be closed
        }
        
        try {
            captureSession?.close()
        } catch (e: Exception) {
            // Ignore
        }
        captureSession = null
        
        // Close camera device
        try {
            cameraDevice?.close()
        } catch (e: Exception) {
            // Ignore
        }
        cameraDevice = null
        
        // Stop and release encoder
        try {
            encoder?.stop()
        } catch (e: Exception) {
            Log.e(TAG, "Error stopping encoder", e)
        }
        
        try {
            encoder?.release()
        } catch (e: Exception) {
            Log.e(TAG, "Error releasing encoder", e)
        }
        encoder = null
        
        // Close network
        try {
            outputStream?.close()
        } catch (e: Exception) {
            // Ignore
        }
        outputStream = null
        
        try {
            socket?.close()
        } catch (e: Exception) {
            // Ignore
        }
        socket = null
        
        // Quit threads
        cameraThread?.quitSafely()
        encoderThread?.quitSafely()
        
        Log.d(TAG, "Cleanup complete. Sent $frameCount total frames")
    }
}
