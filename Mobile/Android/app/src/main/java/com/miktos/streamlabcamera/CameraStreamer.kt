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
import android.os.Looper
import android.os.PowerManager
import android.util.Log
import java.io.IOException
import java.io.OutputStream
import java.net.Socket
import java.net.InetSocketAddress
import java.util.concurrent.Executors
import java.util.concurrent.ScheduledExecutorService
import java.util.concurrent.TimeUnit
import android.content.Intent
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import com.miktos.streamlabcamera.streaming.*
import com.miktos.streamlabcamera.streaming.monitoring.*
import com.miktos.streamlabcamera.remote.RemoteControlClient
import com.miktos.streamlabcamera.monitoring.ThermalMonitor
import com.miktos.streamlabcamera.ui.StudioModeActivity
import org.json.JSONObject
import android.os.BatteryManager

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

    // Connection health monitoring
    private var heartbeatExecutor: ScheduledExecutorService? = null

    // 4-LAYER MONITORING SYSTEM - The complete fix for disconnect detection
    private val socketMonitor = SocketHealthMonitor { reason ->
        Log.e(TAG, "Socket monitor detected disconnect: $reason")
        cameraHandler?.post {
            onDisconnect()
        }
    }
    
    private val dataFlowMonitor = DataFlowMonitor { reason ->
        Log.e(TAG, "Data flow monitor detected problem: $reason")
        cameraHandler?.post {
            onDisconnect()
        }
    }
    
    private val screenMonitor = ScreenStateMonitor(context) {
        // Screen unlocked - verify connection is still alive
        verifyConnectionAfterUnlock()
    }
    
    // State machine
    private var currentState: StreamingState = StreamingState.Stopped

    // Remote Control Integration
    private var remoteControlClient: RemoteControlClient? = null
    private var thermalMonitor: ThermalMonitor? = null
    private var statusUpdateExecutor: ScheduledExecutorService? = null

    // Advanced disconnect detection
    private var lastWriteTime = System.currentTimeMillis()
    private var lastSuccessfulFrameTime = System.currentTimeMillis()
    private val WRITE_TIMEOUT = 8_000 // 8 seconds - trigger reconnect if no successful writes
    private val FRAME_TIMEOUT = 12_000 // 12 seconds - emergency fallback
    private var reconnectAttempts = 0
    private val MAX_RECONNECT_ATTEMPTS = 5  // Increased from 3 to 5
    private var consecutiveWriteFailures = 0
    private val MAX_WRITE_FAILURES = 3  // Trigger reconnect after 3 failed writes
    private var isReconnecting = false  // Guard to prevent overlapping reconnections    
    private var waitingForNetwork = false  // Waiting for WiFi to return

    // Connection parameters for auto-reconnection
    private var storedServerIp: String? = null
    private var storedServerPort: Int? = null
    
    // PAUSE/RESUME functionality for multi-camera switching
    var isPaused = false  // Made public for MainActivity access
        private set
    private var lastFreezeFrame: ByteArray? = null
    private var lastFreezeFrameInfo: MediaCodec.BufferInfo? = null
    private var freezeFrameSendTime = 0L
    private val FREEZE_FRAME_INTERVAL = 1000L  // Send freeze frame every 1 second (1 fps)
    
    // Network monitoring and LTE failover
    private var connectivityManager: ConnectivityManager? = null
    private var networkCallback: ConnectivityManager.NetworkCallback? = null
    private var currentNetworkType: NetworkType = NetworkType.UNKNOWN
    private var allowLteFailover: Boolean = false  // User preference for LTE backup
    private var lteQualityThreshold: Float = 2.0f  // Mbps - switch to LTE if WiFi drops below this
    private var activeNetwork: Network? = null  // Active network for socket binding
    
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
    
    // LTE failover configuration
    fun setLteFailoverEnabled(enabled: Boolean) {
        allowLteFailover = enabled
        Log.i(TAG, "LTE failover ${if (enabled) "enabled" else "disabled"}")
        
        // Re-register network callback to include/exclude cellular
        if (networkCallback != null) {
            unregisterNetworkCallback()
            registerNetworkCallback()
        }
    }
    
    fun setLteQualityThreshold(thresholdMbps: Float) {
        lteQualityThreshold = thresholdMbps
        Log.i(TAG, "LTE quality threshold set to $thresholdMbps Mbps")
    }
    
    fun getCurrentNetworkType(): NetworkType {
        return currentNetworkType
    }
    
    private fun detectNetworkType(network: Network): NetworkType {
        val capabilities = connectivityManager?.getNetworkCapabilities(network) ?: return NetworkType.UNKNOWN
        
        return when {
            capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) -> {
                // Check if it's local WiFi or internet WiFi
                if (capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_VPN) &&
                    capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)) {
                    NetworkType.INET_WIFI
                } else {
                    NetworkType.LAN_WIFI
                }
            }
            capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) -> {
                NetworkType.LTE_CELLULAR
            }
            else -> NetworkType.UNKNOWN
        }
    }
    
    /**
     * Set streaming destination without starting streaming
     * Used to configure the destination for remote START commands
     */
    fun setStreamingDestination(serverIp: String, serverPort: Int) {
        storedServerIp = serverIp
        storedServerPort = serverPort
        Log.i(TAG, "📝 Streaming destination configured: $serverIp:$serverPort")
    }
    
    fun startStreaming(serverIp: String, serverPort: Int) {
        // Store connection parameters for auto-reconnection
        storedServerIp = serverIp
        storedServerPort = serverPort
        Log.d(TAG, "Connection parameters stored: $serverIp:$serverPort")
        
        // Check if using local IP (LTE failover won't work with local IPs)
        val isLocalIp = isLocalNetworkAddress(serverIp)
        if (isLocalIp && allowLteFailover) {
            Log.w(TAG, "⚠️ Server IP $serverIp is local - LTE failover disabled for this stream")
            Log.i(TAG, "💡 For LTE failover to work, use a public IP or domain name")
        }
        
        // Register network callback to detect WiFi restoration
        if (networkCallback == null) {
            registerNetworkCallback()
        }
        
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
                // Update state to Starting
                currentState = StreamingState.Starting
                
                connectToServer(serverIp, serverPort)
                initializeEncoder()
                startCamera2()
                
                // START ALL MONITORS - This is the critical fix!
                socketMonitor.startMonitoring(socket!!)
                dataFlowMonitor.startMonitoring()
                screenMonitor.startMonitoring()
                
                isStreaming = true
                lastWriteTime = System.currentTimeMillis()
                lastSuccessfulFrameTime = System.currentTimeMillis()
                consecutiveWriteFailures = 0  // Reset failure counter
                
                // Update state to Running
                currentState = StreamingState.Running(
                    ConnectionInfo(serverIp, serverPort, currentNetworkType, System.currentTimeMillis())
                )
                
                // If this was a successful reconnection, notify UI (check BEFORE resetting)
                val wasReconnecting = isReconnecting
                val attemptCount = reconnectAttempts
                
                reconnectAttempts = 0 // Reset reconnection counter
                isReconnecting = false // Clear reconnection flag
                
                if (wasReconnecting && attemptCount > 0) {
                    Log.i(TAG, "✅ Reconnection successful after $attemptCount attempts!")
                    val intent = Intent("com.miktos.STREAM_RECONNECTED")
                    intent.setPackage(context.packageName)
                    context.sendBroadcast(intent)
                } else {
                    // Notify MainActivity that streaming started (for remote START command)
                    Intent("com.miktos.STREAMING_STARTED").also { intent ->
                        intent.setPackage(context.packageName)
                        context.sendBroadcast(intent)
                        Log.d(TAG, "📡 Sent STREAMING_STARTED broadcast to MainActivity")
                    }
                }
                statusCallback(true)
                Log.i(TAG, "✅ Streaming started - all 4 monitors active")
                
            } catch (e: Exception) {
                Log.e(TAG, "Error starting stream", e)
                cleanup()
                
                // If this was a reconnection attempt, schedule the next one
                if (reconnectAttempts > 0 && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                    Log.w(TAG, "Reconnection attempt $reconnectAttempts failed - scheduling next attempt")
                    
                    // DON'T call statusCallback(false) during reconnection - keep service alive!
                    
                    // Mark that we're waiting for network if the error suggests network issue
                    if (e is IOException || e.message?.contains("Network") == true || e.message?.contains("Connection") == true) {
                        waitingForNetwork = true
                        Log.i(TAG, "📵 Network issue detected - will retry immediately when WiFi returns")
                    }
                    
                    // Increment counter BEFORE scheduling the delay
                    reconnectAttempts++
                    
                    // Update UI immediately with new attempt number
                    val intent = Intent("com.miktos.STREAM_DISCONNECTED")
                    intent.setPackage(context.packageName)
                    intent.putExtra("reconnect_attempts", reconnectAttempts)
                    intent.putExtra("max_attempts", MAX_RECONNECT_ATTEMPTS)
                    context.sendBroadcast(intent)
                    
                    // Calculate exponential backoff for retry
                    val retryDelay = Math.min(
                        (Math.pow(2.0, reconnectAttempts.toDouble()) * 1000).toLong(),
                        30000  // Cap at 30 seconds
                    )
                    
                    Log.i(TAG, "🔄 Scheduling retry reconnection in ${retryDelay/1000}s (attempt $reconnectAttempts/$MAX_RECONNECT_ATTEMPTS)")
                    
                    Handler(Looper.getMainLooper()).postDelayed({
                        try {
                            Log.i(TAG, "🚀 Attempting reconnection $reconnectAttempts/$MAX_RECONNECT_ATTEMPTS")
                            
                            if (storedServerIp != null && storedServerPort != null) {
                                startStreaming(storedServerIp!!, storedServerPort!!)
                            } else {
                                onReconnectionFailed()
                            }
                        } catch (ex: Exception) {
                            Log.e(TAG, "Retry scheduling failed: ${ex.message}")
                            onReconnectionFailed()
                        }
                    }, retryDelay)
                } else if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
                    Log.e(TAG, "❌ Max reconnection attempts reached after connection failure")
                    onReconnectionFailed()
                } else {
                    // This was NOT a reconnection attempt - initial connection failed
                    statusCallback(false)
                }
            }
        }
    }
    
    private fun connectToServer(serverIp: String, serverPort: Int) {
        val isLocalIp = isLocalNetworkAddress(serverIp)
        Log.d(TAG, "Connecting to $serverIp:$serverPort via ${if (activeNetwork != null && !isLocalIp) "bound network (${currentNetworkType})" else "default routing"}")
        
        // Only bind to LTE network if:
        // 1. We have an active network
        // 2. It's LTE
        // 3. Server is NOT a local IP (local IPs can't be reached over LTE)
        socket = if (activeNetwork != null && currentNetworkType == NetworkType.LTE_CELLULAR && !isLocalIp) {
            // Create socket bound to LTE network for cellular failover
            Log.i(TAG, "📱 Creating LTE-bound socket for cellular failover to $serverIp")
            val lteSock = Socket()
            activeNetwork!!.bindSocket(lteSock)
            lteSock
        } else {
            if (isLocalIp && currentNetworkType == NetworkType.LTE_CELLULAR) {
                Log.w(TAG, "⚠️ Can't use LTE for local IP $serverIp - using WiFi-only reconnection")
            }
            // Use default routing (WiFi preferred)
            Socket()
        }
        
        socket?.tcpNoDelay = true
        socket?.keepAlive = true
        socket?.soTimeout = 3000  // 3 second socket timeout
        socket?.connect(InetSocketAddress(serverIp, serverPort), 5000)  // 5 second connect timeout
        
        // Verify connection is actually established
        if (socket?.isConnected != true || socket?.isClosed == true) {
            throw IOException("Socket connection failed verification")
        }
        
        Log.d(TAG, "Connected successfully via ${currentNetworkType}")
        
        outputStream = socket?.getOutputStream()
        Log.d(TAG, "✅ Connected to server successfully")
        startConnectionHealthCheck()
    }

    private fun startConnectionHealthCheck() {
        heartbeatExecutor = Executors.newSingleThreadScheduledExecutor()
        
        heartbeatExecutor?.scheduleAtFixedRate({
            try {
                val currentTime = System.currentTimeMillis()
                
                // Check 1: Basic socket health
                if (socket?.isConnected == false || socket?.isClosed == true) {
                    Log.e(TAG, "❌ Socket disconnected - basic check failed")
                    cameraHandler?.post {
                        onDisconnect()
                    }
                    return@scheduleAtFixedRate
                }
                
                // Check 2: Output stream health
                if (outputStream == null) {
                    Log.e(TAG, "❌ Output stream is null")
                    cameraHandler?.post {
                        onDisconnect()
                    }
                    return@scheduleAtFixedRate
                }
                
                // Check 3: Write timeout (no successful writes for WRITE_TIMEOUT)
                if (isStreaming && currentTime - lastWriteTime > WRITE_TIMEOUT) {
                    Log.e(TAG, "❌ Write timeout - no successful writes for ${(currentTime - lastWriteTime)/1000}s")
                    cameraHandler?.post {
                        onDisconnect()
                    }
                    return@scheduleAtFixedRate
                }
                
                // Check 4: Frame generation timeout (emergency fallback)
                if (isStreaming && currentTime - lastSuccessfulFrameTime > FRAME_TIMEOUT) {
                    Log.e(TAG, "❌ Frame timeout - no frames processed for ${(currentTime - lastSuccessfulFrameTime)/1000}s")
                    cameraHandler?.post {
                        onDisconnect()
                    }
                    return@scheduleAtFixedRate
                }
                
                // Check 5: Consecutive write failures
                if (consecutiveWriteFailures >= MAX_WRITE_FAILURES) {
                    Log.e(TAG, "❌ Too many consecutive write failures ($consecutiveWriteFailures)")
                    cameraHandler?.post {
                        onDisconnect()
                    }
                    return@scheduleAtFixedRate
                }
                
                // All checks passed
                if (currentTime % 10000 < 2000) {  // Log every ~10 seconds
                    Log.d(TAG, "💚 Health check passed - streaming healthy")
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "Heartbeat check failed: ${e.message}")
                cameraHandler?.post {
                    onDisconnect()
                }
            }
        }, 1, 2, TimeUnit.SECONDS) // Check every 2 seconds
    }

    private fun onDisconnect() {
        // Guard against overlapping reconnection attempts
        if (isReconnecting) {
            Log.w(TAG, "Already reconnecting - ignoring duplicate disconnect event")
            return
        }
        
        if (currentState is StreamingState.Reconnecting) {
            Log.w(TAG, "Already in reconnecting state - ignoring duplicate disconnect")
            return
        }
        
        Log.w(TAG, "Connection lost - attempting recovery (attempt ${reconnectAttempts + 1}/${MAX_RECONNECT_ATTEMPTS})")
        
        // Update state
        currentState = StreamingState.Disconnected("Connection lost", System.currentTimeMillis())
        
        // Mark as reconnecting
        isReconnecting = true
        
        // Update internal state FIRST
        isStreaming = false
        
        // Stop socket and data flow monitors (but keep screen monitor to detect unlock)
        socketMonitor.stopMonitoring()
        dataFlowMonitor.stopMonitoring()
        // Keep screen monitor running to detect unlock and trigger verification
        
        // Clean up current resources
        cleanup()
        // DON'T call statusCallback(false) during reconnection - it triggers service destruction!
        
        // Attempt auto-reconnection if within limits
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++
            
            // Calculate exponential backoff: 2^attempt * 1000ms (1s, 2s, 4s, 8s, 16s)
            val backoffDelay = Math.min(
                (Math.pow(2.0, reconnectAttempts.toDouble()) * 1000).toLong(),
                30000  // Cap at 30 seconds
            )
            
            // Update state to Reconnecting
            currentState = StreamingState.Reconnecting(
                reconnectAttempts,
                MAX_RECONNECT_ATTEMPTS,
                System.currentTimeMillis() + backoffDelay
            )
            
            Log.i(TAG, "🔄 Auto-reconnecting in ${backoffDelay/1000}s... (attempt $reconnectAttempts/$MAX_RECONNECT_ATTEMPTS)")
            
            // Notify MainActivity via broadcast with reconnection status (AFTER incrementing)
            val intent = Intent("com.miktos.STREAM_DISCONNECTED")
            intent.setPackage(context.packageName)
            intent.putExtra("reconnect_attempts", reconnectAttempts)
            intent.putExtra("max_attempts", MAX_RECONNECT_ATTEMPTS)
            intent.putExtra("backoff_delay_ms", backoffDelay)
            context.sendBroadcast(intent)
            
            // Schedule reconnection with exponential backoff
            Handler(Looper.getMainLooper()).postDelayed({
                try {
                    Log.i(TAG, "🚀 Attempting auto-reconnection $reconnectAttempts/$MAX_RECONNECT_ATTEMPTS...")
                    
                    // Implement actual reconnection logic using stored parameters
                    if (storedServerIp != null && storedServerPort != null) {
                        Log.i(TAG, "Reconnecting to ${storedServerIp}:${storedServerPort}")
                        startStreaming(storedServerIp!!, storedServerPort!!)
                    } else {
                        Log.e(TAG, "Cannot auto-reconnect: connection parameters not stored")
                        onReconnectionFailed()
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Auto-reconnection scheduling failed: ${e.message}")
                    onReconnectionFailed()
                }
            }, backoffDelay)
        } else {
            Log.e(TAG, "❌ Max reconnection attempts ($MAX_RECONNECT_ATTEMPTS) reached")
            
            // If waiting for network, keep the door open for when WiFi returns
            if (waitingForNetwork) {
                Log.i(TAG, "⏳ Max attempts reached but waiting for network - will retry when WiFi is back")
                // Don't reset reconnectAttempts - keep current state
                // Network callback will trigger immediate reconnection when WiFi returns
            } else {
                // No network issue detected - truly failed
                reconnectAttempts = 0
                isReconnecting = false
                val failIntent = Intent("com.miktos.STREAM_FAILED")
                failIntent.setPackage(context.packageName)
                context.sendBroadcast(failIntent)
            }
        }
    }

    private fun onReconnectionFailed() {
        Log.w(TAG, "All reconnection attempts exhausted")
        
        // If we're waiting for network, keep waiting - don't fail yet
        if (waitingForNetwork) {
            Log.i(TAG, "⏳ Still waiting for network to return - will retry when WiFi is back")
            // Keep isReconnecting = true and reconnectAttempts as-is
            // The network callback will trigger reconnection when WiFi returns
        } else {
            // No hope of reconnection - give up
            currentState = StreamingState.Error("Max reconnection attempts reached", ErrorType.NETWORK)
            isReconnecting = false
            reconnectAttempts = 0
            waitingForNetwork = false
            
            val failIntent = Intent("com.miktos.STREAM_FAILED")
            failIntent.setPackage(context.packageName)
            context.sendBroadcast(failIntent)
        }
    }
    
    private fun stopHeartbeat() {
        heartbeatExecutor?.shutdown()
        heartbeatExecutor = null
    }
    
    private fun initializeEncoder() {
        Log.d(TAG, "Initializing H.264 encoder")
        
        // Adjust bitrate based on network type
        val adaptiveBitrate = when (currentNetworkType) {
            NetworkType.LTE_CELLULAR -> {
                // Reduce bitrate for LTE: 6 Mbps → 4 Mbps
                val lteBitrate = (VIDEO_BITRATE * 0.67).toInt() // ~4 Mbps
                Log.i(TAG, "🎚️ LTE mode: Reduced bitrate to ${lteBitrate / 1_000_000} Mbps")
                lteBitrate
            }
            NetworkType.LAN_WIFI, NetworkType.INET_WIFI -> {
                Log.i(TAG, "🎚️ WiFi mode: Full bitrate ${VIDEO_BITRATE / 1_000_000} Mbps")
                VIDEO_BITRATE
            }
            else -> {
                Log.w(TAG, "🎚️ Unknown network: Using standard bitrate")
                VIDEO_BITRATE
            }
        }
        
        val format = MediaFormat.createVideoFormat(
            MediaFormat.MIMETYPE_VIDEO_AVC,
            VIDEO_WIDTH,
            VIDEO_HEIGHT
        )
        
        format.setInteger(
            MediaFormat.KEY_COLOR_FORMAT,
            MediaCodecInfo.CodecCapabilities.COLOR_FormatSurface
        )
        format.setInteger(MediaFormat.KEY_BIT_RATE, adaptiveBitrate)
        format.setInteger(MediaFormat.KEY_FRAME_RATE, VIDEO_FPS)
        format.setInteger(MediaFormat.KEY_I_FRAME_INTERVAL, VIDEO_I_FRAME_INTERVAL)
        format.setInteger(MediaFormat.KEY_PROFILE, MediaCodecInfo.CodecProfileLevel.AVCProfileHigh)
        format.setInteger(MediaFormat.KEY_LEVEL, MediaCodecInfo.CodecProfileLevel.AVCLevel4)
        
        encoder = MediaCodec.createEncoderByType(MediaFormat.MIMETYPE_VIDEO_AVC)
        encoder?.configure(format, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
        
        // Log network type for debugging
        Log.i(TAG, "📡 Encoding configured for network type: $currentNetworkType")
        
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
                        // Note: createCaptureSession is deprecated but SessionConfiguration requires API 28+
                        // Since minSdk is 26, we keep the working deprecated method
                        @Suppress("DEPRECATION")
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
                    Log.w(TAG, "Camera disconnected by system (likely screen lock/unlock)")
                    // This is expected during lock/unlock - auto-reconnect will handle it
                    onDisconnect()
                }
                
                override fun onError(camera: CameraDevice, error: Int) {
                    Log.e(TAG, "Camera error: $error - triggering auto-reconnect")
                    onDisconnect()
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
                // Check if we're in PAUSED state - send freeze frame instead
                if (isPaused) {
                    handlePausedFrame(codec, index, info, encodedData)
                    return
                }
                
                // Normal streaming mode - send all frames
                // Check if this is codec configuration (SPS/PPS)
                val isConfig = (info.flags and MediaCodec.BUFFER_FLAG_CODEC_CONFIG) != 0
                
                val data = ByteArray(info.size)
                encodedData.position(info.offset)
                encodedData.limit(info.offset + info.size)
                encodedData.get(data)
                
                // Capture keyframes as potential freeze frames for future PAUSE
                if ((info.flags and MediaCodec.BUFFER_FLAG_KEY_FRAME) != 0) {
                    lastFreezeFrame = data.copyOf()
                    lastFreezeFrameInfo = MediaCodec.BufferInfo().apply {
                        set(0, data.size, info.presentationTimeUs, info.flags)
                    }
                }
                
                // ALWAYS send codec config, and send keyframes + regular frames
                if (isConfig || (info.flags and MediaCodec.BUFFER_FLAG_KEY_FRAME) != 0 || info.flags == 0) {
                    try {
                        outputStream?.write(data)
                        outputStream?.flush()
                        
                        // CRITICAL: Tell monitor we successfully wrote data
                        dataFlowMonitor.recordSuccessfulWrite()
                        
                        // Track successful transmission
                        lastWriteTime = System.currentTimeMillis()
                        lastSuccessfulFrameTime = System.currentTimeMillis()
                        consecutiveWriteFailures = 0  // Reset failure counter on success
                        
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
                    } catch (e: Exception) {
                        consecutiveWriteFailures++
                        Log.e(TAG, "❌ Write error #$consecutiveWriteFailures - network issue: ${e.message}")
                        
                        // Trigger immediate disconnect if write fails
                        cameraHandler?.post {
                            onDisconnect()
                        }
                        return
                    }
                }
            }
            
            codec.releaseOutputBuffer(index, false)
            
        } catch (e: IOException) {
            Log.e(TAG, "Error sending frame during ${if (isReconnecting) "reconnection" else "streaming"}", e)
            // Don't call stopStreaming() if we're already reconnecting
            // This would reset reconnection state and break UI synchronization
            if (!isReconnecting) {
                onDisconnect()  // Trigger auto-reconnect flow
            }
        }
    }
    
    /**
     * Handle frame output when in PAUSED state
     * Sends freeze frame at 1 fps to keep session alive with minimal bandwidth
     */
    private fun handlePausedFrame(
        codec: MediaCodec,
        index: Int,
        info: MediaCodec.BufferInfo,
        encodedData: java.nio.ByteBuffer
    ) {
        // Capture new keyframe as freeze frame candidate
        if ((info.flags and MediaCodec.BUFFER_FLAG_KEY_FRAME) != 0) {
            val data = ByteArray(info.size)
            encodedData.position(info.offset)
            encodedData.limit(info.offset + info.size)
            encodedData.get(data)
            
            lastFreezeFrame = data.copyOf()
            lastFreezeFrameInfo = MediaCodec.BufferInfo().apply {
                set(0, data.size, info.presentationTimeUs, info.flags)
            }
            Log.d(TAG, "❄️ Captured new freeze frame: ${data.size} bytes")
        }
        
        // Send freeze frame at 1 fps interval
        val currentTime = System.currentTimeMillis()
        if (lastFreezeFrame != null && currentTime - freezeFrameSendTime >= FREEZE_FRAME_INTERVAL) {
            try {
                outputStream?.write(lastFreezeFrame!!)
                outputStream?.flush()
                
                // Track write for monitoring
                dataFlowMonitor.recordSuccessfulWrite()
                lastWriteTime = currentTime
                freezeFrameSendTime = currentTime
                consecutiveWriteFailures = 0
                
                Log.d(TAG, "❄️ Sent freeze frame (paused mode): ${lastFreezeFrame!!.size} bytes")
                
            } catch (e: Exception) {
                consecutiveWriteFailures++
                Log.e(TAG, "❌ Freeze frame write error: ${e.message}")
                cameraHandler?.post { onDisconnect() }
            }
        }
        
        // Release the buffer even though we didn't send it
        codec.releaseOutputBuffer(index, false)
    }
    
    fun stopStreaming() {
        Log.d(TAG, "Stopping streaming...")
        
        currentState = StreamingState.Stopping
        
        isStreaming = false
        isPaused = false  // Clear pause state
        lastFreezeFrame = null  // Clear freeze frame
        
        // Stop all monitors
        socketMonitor.stopMonitoring()
        dataFlowMonitor.stopMonitoring()
        screenMonitor.stopMonitoring()
        
        // Reset reconnection state to allow manual restart
        isReconnecting = false
        reconnectAttempts = 0
        waitingForNetwork = false
        
        // Unregister network callback
        unregisterNetworkCallback()
        
        cleanup()
        
        currentState = StreamingState.Stopped
        statusCallback(false)
        
        // Notify MainActivity that streaming stopped
        Intent("com.miktos.STREAMING_STOPPED").also { intent ->
            intent.setPackage(context.packageName)
            context.sendBroadcast(intent)
            Log.d(TAG, "📡 Sent STREAMING_STOPPED broadcast to MainActivity")
        }
    }
    
    /**
     * Pause streaming - freeze current frame but keep session alive
     * Perfect for multi-camera switching without startup latency
     */
    fun pauseStreaming() {
        if (currentState !is StreamingState.Running) {
            Log.w(TAG, "⚠️ Cannot pause - not currently running (state: $currentState)")
            return
        }
        
        val runningState = currentState as StreamingState.Running
        
        Log.i(TAG, "⏸️ Pausing stream - entering freeze frame mode")
        isPaused = true
        freezeFrameSendTime = 0L  // Force immediate send of first freeze frame
        
        // Update state to Paused (keeps connection info)
        currentState = StreamingState.Paused(runningState.connectionInfo)
        
        // Notify MainActivity
        Intent("com.miktos.STREAMING_PAUSED").also { intent ->
            intent.setPackage(context.packageName)
            context.sendBroadcast(intent)
        }
        
        // Notify desktop
        sendStatusUpdate()
        
        Log.i(TAG, "✅ Stream paused - will send freeze frame at 1 fps")
    }
    
    /**
     * Resume streaming - return to normal frame rate
     * Instant resume with zero startup latency
     */
    fun resumeStreaming() {
        if (currentState !is StreamingState.Paused) {
            Log.w(TAG, "⚠️ Cannot resume - not currently paused (state: $currentState)")
            return
        }
        
        val pausedState = currentState as StreamingState.Paused
        
        Log.i(TAG, "▶️ Resuming stream - returning to normal frame rate")
        isPaused = false
        lastFreezeFrame = null  // Clear freeze frame to save memory
        lastFreezeFrameInfo = null
        
        // Update state back to Running (restore connection info)
        currentState = StreamingState.Running(pausedState.connectionInfo)
        
        // Notify MainActivity
        Intent("com.miktos.STREAMING_RESUMED").also { intent ->
            intent.setPackage(context.packageName)
            context.sendBroadcast(intent)
        }
        
        // Notify desktop
        sendStatusUpdate()
        
        Log.i(TAG, "✅ Stream resumed - back to 30 fps")
    }
    
    private fun registerNetworkCallback() {
        try {
            connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            
            networkCallback = object : ConnectivityManager.NetworkCallback() {
                override fun onAvailable(network: Network) {
                    val networkType = detectNetworkType(network)
                    val previousType = currentNetworkType
                    currentNetworkType = networkType
                    
                    // Store network reference for socket binding
                    activeNetwork = network
                    
                    Log.i(TAG, "📶 Network available: $networkType (was: $previousType)")
                    
                    // Handle network type transitions
                    when {
                        // WiFi came back - prefer it over LTE
                        networkType == NetworkType.LAN_WIFI || networkType == NetworkType.INET_WIFI -> {
                            if (waitingForNetwork && reconnectAttempts > 0 && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                                Log.i(TAG, "🚀 WiFi restored - attempting immediate reconnection!")
                                waitingForNetwork = false
                                
                                Handler(Looper.getMainLooper()).postDelayed({
                                    if (storedServerIp != null && storedServerPort != null && !isStreaming) {
                                        startStreaming(storedServerIp!!, storedServerPort!!)
                                    }
                                }, 500)
                            } else if (isStreaming && previousType == NetworkType.LTE_CELLULAR) {
                                // Switch back from LTE to WiFi
                                Log.i(TAG, "🔄 Switching from LTE back to WiFi (better quality)")
                                Handler(Looper.getMainLooper()).postDelayed({
                                    if (storedServerIp != null && storedServerPort != null) {
                                        // Trigger reconnection to use WiFi
                                        isReconnecting = true
                                        reconnectAttempts = 1
                                        startStreaming(storedServerIp!!, storedServerPort!!)
                                    }
                                }, 800)
                            }
                        }
                        
                        // LTE available - use if WiFi is lost and failover enabled
                        networkType == NetworkType.LTE_CELLULAR && allowLteFailover -> {
                            // Check if server is reachable over LTE (not a local IP)
                            val canUseLte = storedServerIp != null && !isLocalNetworkAddress(storedServerIp!!)
                            
                            if (!canUseLte) {
                                Log.w(TAG, "⚠️ LTE available but server ${storedServerIp} is local - waiting for WiFi")
                                // Don't attempt LTE reconnection for local IPs
                                return@onAvailable
                            }
                            
                            if (waitingForNetwork && reconnectAttempts > 0 && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                                Log.i(TAG, "📱 LTE available - attempting failover reconnection!")
                                waitingForNetwork = false
                                
                                // Notify UI about LTE usage
                                val intent = Intent("com.miktos.NETWORK_TYPE_CHANGED")
                                intent.setPackage(context.packageName)
                                intent.putExtra("network_type", "LTE")
                                intent.putExtra("warning", "Using cellular data - monitor usage")
                                context.sendBroadcast(intent)
                                
                                Handler(Looper.getMainLooper()).postDelayed({
                                    if (storedServerIp != null && storedServerPort != null && !isStreaming) {
                                        startStreaming(storedServerIp!!, storedServerPort!!)
                                    }
                                }, 1000) // Slightly longer delay for LTE
                            }
                        }
                    }
                }
                
                override fun onLost(network: Network) {
                    val lostType = detectNetworkType(network)
                    Log.w(TAG, "📵 Network lost: $lostType")
                    
                    // If WiFi lost and LTE failover enabled, flag it
                    if ((lostType == NetworkType.LAN_WIFI || lostType == NetworkType.INET_WIFI) && allowLteFailover) {
                        Log.i(TAG, "⚠️ WiFi lost but LTE failover enabled - will try cellular")
                    }
                    
                    // Clear active network if this was the active one
                    if (activeNetwork == network) {
                        activeNetwork = null
                        Log.d(TAG, "Cleared active network reference")
                    }
                    
                    currentNetworkType = NetworkType.OFFLINE
                }
                
                override fun onCapabilitiesChanged(network: Network, capabilities: NetworkCapabilities) {
                    // Monitor link quality for potential LTE switch
                    if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)) {
                        val downstreamKbps = capabilities.linkDownstreamBandwidthKbps
                        val downstreamMbps = downstreamKbps / 1000.0f
                        
                        if (downstreamMbps < lteQualityThreshold && allowLteFailover && isStreaming) {
                            Log.w(TAG, "⚠️ WiFi quality poor (${downstreamMbps} Mbps < ${lteQualityThreshold} Mbps)")
                            Log.i(TAG, "📱 Considering LTE failover due to poor WiFi quality...")
                            // Could trigger proactive switch here if needed
                        }
                    }
                }
            }
            
            // Use default network callback to monitor all network changes (WiFi + LTE)
            connectivityManager?.registerDefaultNetworkCallback(networkCallback!!)
            Log.d(TAG, "Network callback registered for all networks (LTE failover: $allowLteFailover)")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to register network callback: ${e.message}")
        }
    }
    
    private fun unregisterNetworkCallback() {
        try {
            if (networkCallback != null && connectivityManager != null) {
                connectivityManager?.unregisterNetworkCallback(networkCallback!!)
                Log.d(TAG, "Network callback unregistered")
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error unregistering network callback: ${e.message}")
        }
        networkCallback = null
        connectivityManager = null
    }
    
    private fun isLocalNetworkAddress(ip: String): Boolean {
        // Check if IP is in private ranges: 192.168.x.x, 10.x.x.x, 172.16-31.x.x, localhost
        return ip.startsWith("192.168.") ||
               ip.startsWith("10.") ||
               ip.startsWith("172.16.") || ip.startsWith("172.17.") ||
               ip.startsWith("172.18.") || ip.startsWith("172.19.") ||
               ip.startsWith("172.20.") || ip.startsWith("172.21.") ||
               ip.startsWith("172.22.") || ip.startsWith("172.23.") ||
               ip.startsWith("172.24.") || ip.startsWith("172.25.") ||
               ip.startsWith("172.26.") || ip.startsWith("172.27.") ||
               ip.startsWith("172.28.") || ip.startsWith("172.29.") ||
               ip.startsWith("172.30.") || ip.startsWith("172.31.") ||
               ip == "localhost" || ip == "127.0.0.1"
    }
    
    /**
     * Verify connection after screen unlock
     * CRITICAL for fixing the 60+ minute lock bug
     * 
     * When the phone unlocks, actively verify the connection is still alive.
     * If dead, trigger reconnection immediately.
     */
    private fun verifyConnectionAfterUnlock() {
        if (currentState !is StreamingState.Running && currentState !is StreamingState.Paused) {
            Log.d(TAG, "Not streaming - skipping post-unlock verification")
            return  // Not currently streaming or paused
        }
        
        Log.i(TAG, "🔓 Verifying connection after unlock...")
        
        // Active check: Is socket really alive?
        try {
            val testSocket = socket
            if (testSocket == null || testSocket.isClosed || !testSocket.isConnected) {
                Log.e(TAG, "❌ Post-unlock verification FAILED - socket is null/closed")
                onDisconnect()
                return
            }
            
            // Try to write a test byte to force OS to check connection
            testSocket.getOutputStream()?.write(0x00)
            testSocket.getOutputStream()?.flush()
            
            Log.i(TAG, "✅ Post-unlock verification passed - connection is alive")
        } catch (e: IOException) {
            Log.e(TAG, "❌ Post-unlock verification FAILED - socket write error: ${e.message}")
            onDisconnect()
        } catch (e: Exception) {
            Log.e(TAG, "❌ Post-unlock verification error: ${e.message}")
            // Don't trigger disconnect on unexpected errors
        }
    }
    
    private fun cleanup() {
        Log.d(TAG, "Cleaning up resources")
        
        // Stop heartbeat monitoring
        stopHeartbeat()
        
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
        
        // Clear handlers so they can be recreated on next stream
        cameraThread = null
        cameraHandler = null
        encoderThread = null
        encoderHandler = null
        
        Log.d(TAG, "Cleanup complete. Sent $frameCount total frames")
    }
    
    // ==================== REMOTE CONTROL METHODS ====================
    
    /**
     * Enable remote control via WebSocket connection to desktop server
     * @param serverIp IP address of the desktop running websocket_server.py
     * @param port WebSocket port (default 9000 for cameras)
     */
    fun enableRemoteControl(serverIp: String, port: Int = 9000) {
        remoteControlClient = RemoteControlClient(
            context = context,
            onCommandReceived = { command, params ->
                handleRemoteCommand(command, params)
            }
        )
        
        remoteControlClient?.connect(serverIp, port)
        Log.i(TAG, "🎮 Remote control enabled - connecting to $serverIp:$port")
        
        // Start thermal monitoring
        thermalMonitor = ThermalMonitor(context) { thermalState ->
            Log.w(TAG, "🌡️ Thermal state: $thermalState")
            // Send thermal update
            sendStatusUpdate()
        }
        thermalMonitor?.startMonitoring()
        
        // Start periodic status updates (every 5 seconds)
        statusUpdateExecutor = Executors.newSingleThreadScheduledExecutor()
        statusUpdateExecutor?.scheduleAtFixedRate({
            sendStatusUpdate()
        }, 5, 5, TimeUnit.SECONDS)
    }
    
    /**
     * Disable remote control and cleanup
     */
    fun disableRemoteControl() {
        remoteControlClient?.disconnect()
        remoteControlClient = null
        
        thermalMonitor?.stopMonitoring()
        thermalMonitor = null
        
        statusUpdateExecutor?.shutdown()
        statusUpdateExecutor = null
        
        Log.i(TAG, "🎮 Remote control disabled")
    }
    
    /**
     * Handle commands received from desktop controller
     */
    private fun handleRemoteCommand(command: String, params: JSONObject) {
        Log.i(TAG, "📥 Processing remote command: $command")
        
        // Define the command execution logic
        val executeCommand: () -> Unit = {
            when (command) {
                "START" -> {
                    // Get server IP/port from params or use stored values
                    val serverIp = if (params.has("server_ip")) {
                        params.getString("server_ip")
                    } else {
                        storedServerIp
                    }
                    
                    val serverPort = if (params.has("server_port")) {
                        params.getInt("server_port")
                    } else {
                        storedServerPort ?: 8554
                    }
                    
                    if (serverIp != null && serverIp.isNotEmpty()) {
                        Log.i(TAG, "🎬 Starting stream to $serverIp:$serverPort via remote command")
                        startStreaming(serverIp, serverPort)
                    } else {
                        Log.e(TAG, "❌ START command failed - no streaming destination configured")
                        Log.e(TAG, "   Please configure server IP in app settings first")
                    }
                }
                
                "STOP" -> {
                    Log.i(TAG, "⏹️ Stopping stream via remote command")
                    stopStreaming()
                }
                
                "PAUSE" -> {
                    Log.i(TAG, "⏸️ Pausing stream via remote command")
                    pauseStreaming()
                }
                
                "RESUME" -> {
                    Log.i(TAG, "▶️ Resuming stream via remote command")
                    resumeStreaming()
                }
                
                "ENTER_STUDIO_MODE" -> {
                    Log.i(TAG, "📺 Entering Studio Mode via remote command (streaming: $isStreaming)")
                    // Studio Mode can be entered anytime, not just when streaming
                    StudioModeActivity.start(context)
                }
                
                "EXIT_STUDIO_MODE" -> {
                    Log.i(TAG, "📺 Exiting Studio Mode via remote command")
                    // Send broadcast to exit Studio Mode
                    val intent = Intent("com.miktos.EXIT_STUDIO_MODE").apply {
                        setPackage(context.packageName)
                        addFlags(Intent.FLAG_INCLUDE_STOPPED_PACKAGES)
                    }
                    context.sendBroadcast(intent)
                }
                
                "GET_STATUS", "STATUS" -> {
                    Log.d(TAG, "📊 Status requested via remote command")
                    sendStatusUpdate()
                }
                
                "SET_QUALITY" -> {
                    // Future: Adjust bitrate/resolution
                    val quality = params.optString("quality", "high")
                    Log.i(TAG, "🎨 Quality change requested: $quality (not implemented yet)")
                }
                
                else -> {
                    Log.w(TAG, "⚠️  Unknown command: $command")
                }
            }
            Unit  // Explicitly return Unit
        }
        
        // Execute on camera handler thread if available, otherwise run directly
        if (cameraHandler != null) {
            cameraHandler?.post(executeCommand)
        } else {
            // No camera handler yet (remote control only mode), execute directly
            Log.d(TAG, "⚡ Executing command directly (no camera handler yet)")
            executeCommand()
        }
    }
    
    /**
     * Send current status to desktop via WebSocket
     */
    private fun sendStatusUpdate() {
        val status = JSONObject().apply {
            put("state", when (currentState) {
                is StreamingState.Stopped -> "stopped"
                is StreamingState.Starting -> "starting"
                is StreamingState.Running -> "running"
                is StreamingState.Paused -> "paused"
                is StreamingState.Disconnected -> "disconnected"
                is StreamingState.Reconnecting -> "reconnecting"
                is StreamingState.Error -> "error"
                is StreamingState.Stopping -> "stopping"
            })
            
            put("is_streaming", isStreaming)
            put("is_paused", isPaused)
            put("frame_count", frameCount)
            
            // Battery info
            val batteryManager = context.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
            put("battery_level", batteryManager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY))
            
            // Network info
            put("network_type", currentNetworkType.name)
            
            // Thermal info
            put("thermal_state", thermalMonitor?.getCurrentState()?.name ?: "OK")
            
            // Streaming uptime (works for both Running and Paused states)
            if (isStreaming && (currentState is StreamingState.Running || currentState is StreamingState.Paused)) {
                val connectionInfo = when (val state = currentState) {
                    is StreamingState.Running -> state.connectionInfo
                    is StreamingState.Paused -> state.connectionInfo
                    else -> null
                }
                
                if (connectionInfo != null) {
                    val uptimeSeconds = (System.currentTimeMillis() - connectionInfo.connectedAt) / 1000
                    put("uptime_seconds", uptimeSeconds)
                    put("server_ip", connectionInfo.serverIp)
                    put("server_port", connectionInfo.serverPort)
                }
            } else {
                put("uptime_seconds", 0)
            }
            
            // Pause duration (if paused)
            if (currentState is StreamingState.Paused) {
                val pausedState = currentState as StreamingState.Paused
                val pausedSeconds = (System.currentTimeMillis() - pausedState.pausedAt) / 1000
                put("paused_seconds", pausedSeconds)
            }
        }
        
        remoteControlClient?.sendStatus(status)
    }
}
