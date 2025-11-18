package com.miktos.streamlabcamera.streaming

/**
 * Streaming State Machine
 * Represents all possible states of the streaming system
 */
sealed class StreamingState {
    object Stopped : StreamingState()
    object Starting : StreamingState()
    data class Running(val connectionInfo: ConnectionInfo) : StreamingState()
    data class Paused(val connectionInfo: ConnectionInfo, val pausedAt: Long = System.currentTimeMillis()) : StreamingState()
    data class Disconnected(val reason: String, val detectedAt: Long) : StreamingState()
    data class Reconnecting(
        val attempt: Int,
        val maxAttempts: Int,
        val nextAttemptTime: Long
    ) : StreamingState()
    data class Error(val reason: String, val errorType: ErrorType) : StreamingState()
    object Stopping : StreamingState()
}

/**
 * Connection metadata
 */
data class ConnectionInfo(
    val serverIp: String,
    val serverPort: Int,
    val networkType: NetworkType,
    val connectedAt: Long = System.currentTimeMillis()
)

/**
 * Network type classification
 */
enum class NetworkType {
    UNKNOWN,        // Network type not determined
    LAN_WIFI,       // WiFi on local network (no internet)
    INET_WIFI,      // WiFi with internet access
    LTE_CELLULAR,   // Cellular/mobile data
    OFFLINE         // No network connection
}

/**
 * Error type classification for better error handling
 */
enum class ErrorType {
    UNKNOWN,        // Unknown error type
    CAMERA,         // Camera access/initialization error
    ENCODER,        // Video encoder error
    NETWORK,        // Network/connection error
    THERMAL,        // Device thermal throttling
    PERMISSION,     // Missing permissions
    TIMEOUT         // Operation timeout
}
