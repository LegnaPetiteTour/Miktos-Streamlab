package com.miktos.streamlabcamera.remote

import android.content.Context
import android.provider.Settings
import android.util.Log
import kotlinx.coroutines.*
import okhttp3.*
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class RemoteControlClient(
    private val context: Context,
    private val onCommandReceived: (String, JSONObject) -> Unit,
    private val onConnected: (() -> Unit)? = null
) {
    private val TAG = "RemoteControlClient"
    
    private var webSocket: WebSocket? = null
    private val client = OkHttpClient.Builder()
        .connectTimeout(5, TimeUnit.SECONDS)
        .readTimeout(0, TimeUnit.MINUTES) // No timeout for WebSocket
        .pingInterval(30, TimeUnit.SECONDS) // Keep-alive
        .build()
    
    private var isConnected = false
    private var reconnectJob: Job? = null
    private var cameraId: String = ""
    
    init {
        // Get unique camera ID from device
        cameraId = Settings.Secure.getString(
            context.contentResolver,
            Settings.Secure.ANDROID_ID
        ) ?: "unknown-device"
    }
    
    fun connect(serverIp: String, port: Int = 9000) {
        // Disconnect existing connection first to prevent duplicates
        webSocket?.let {
            Log.w(TAG, "⚠️  Closing existing WebSocket before new connection")
            it.close(1000, "Reconnecting")
            webSocket = null
            isConnected = false
        }
        
        // Cancel any pending reconnection attempts
        reconnectJob?.cancel()
        reconnectJob = null
        
        val request = Request.Builder()
            .url("ws://$serverIp:$port")
            .build()
        
        Log.i(TAG, "🔌 Connecting to WebSocket server at $serverIp:$port...")
        
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                Log.i(TAG, "✅ WebSocket connected to $serverIp:$port")
                isConnected = true
                
                // Broadcast connection status FIRST
                try {
                    Log.d(TAG, "📡 Broadcasting REMOTE_CONTROL_CONNECTED...")
                    val intent = android.content.Intent("com.miktos.REMOTE_CONTROL_CONNECTED").apply {
                        setPackage(context.packageName)  // Explicit package for security
                        addFlags(android.content.Intent.FLAG_INCLUDE_STOPPED_PACKAGES)
                    }
                    context.sendBroadcast(intent)
                    Log.d(TAG, "📡 Broadcast sent successfully to package: ${context.packageName}")
                } catch (e: Exception) {
                    Log.e(TAG, "❌ Failed to send broadcast: ${e.message}", e)
                }
                
                // Send registration
                try {
                    val registration = JSONObject().apply {
                        put("type", "register")
                        put("camera_id", cameraId)
                        put("timestamp", System.currentTimeMillis())
                    }
                    webSocket.send(registration.toString())
                    Log.i(TAG, "📝 Sent registration for camera: $cameraId")
                } catch (e: Exception) {
                    Log.e(TAG, "❌ Failed to send registration: ${e.message}", e)
                }
                
                // Trigger immediate status update callback
                onConnected?.invoke()
            }
            
            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    Log.d(TAG, "📩 Raw message received: $text")
                    val message = JSONObject(text)
                    val type = message.optString("type", "")
                    
                    if (type.isEmpty()) {
                        Log.e(TAG, "❌ Message missing 'type' field: $text")
                        return
                    }
                    
                    when (type) {
                        "registered" -> {
                            Log.i(TAG, "✅ Registration confirmed by server")
                        }
                        "command" -> {
                            val command = message.getString("command")
                            val params = message.optJSONObject("params") ?: JSONObject()
                            Log.i(TAG, "📥 Command received: $command")
                            onCommandReceived(command, params)
                        }
                        else -> {
                            Log.d(TAG, "📨 Received message type: $type")
                        }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "❌ Error parsing message: ${e.message} - Raw: $text")
                }
            }
            
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                Log.e(TAG, "❌ WebSocket failure: ${t.message}")
                isConnected = false
                
                // Broadcast disconnection status
                val intent = android.content.Intent("com.miktos.REMOTE_CONTROL_DISCONNECTED").apply {
                    setPackage(context.packageName)
                    addFlags(android.content.Intent.FLAG_INCLUDE_STOPPED_PACKAGES)
                }
                context.sendBroadcast(intent)
                
                scheduleReconnect(serverIp, port)
            }
            
            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                Log.w(TAG, "⚠️  WebSocket closing: $reason (code: $code)")
                isConnected = false
            }
            
            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                Log.w(TAG, "WebSocket closed: $reason (code: $code)")
                isConnected = false
                
                // Broadcast disconnection status
                val intent = android.content.Intent("com.miktos.REMOTE_CONTROL_DISCONNECTED").apply {
                    setPackage(context.packageName)
                    addFlags(android.content.Intent.FLAG_INCLUDE_STOPPED_PACKAGES)
                }
                context.sendBroadcast(intent)
                
                if (code != 1000) {  // 1000 = normal closure
                    scheduleReconnect(serverIp, port)
                }
            }
        })
    }
    
    private fun scheduleReconnect(serverIp: String, port: Int) {
        reconnectJob?.cancel()
        reconnectJob = CoroutineScope(Dispatchers.IO).launch {
            delay(5000) // Wait 5 seconds before reconnecting
            if (!isConnected) {
                Log.i(TAG, "🔄 Attempting WebSocket reconnection...")
                connect(serverIp, port)
            }
        }
    }
    
    fun sendStatus(status: JSONObject) {
        if (isConnected) {
            val message = JSONObject().apply {
                put("type", "status")
                put("data", status)
                put("timestamp", System.currentTimeMillis())
            }
            val sent = webSocket?.send(message.toString()) ?: false
            if (sent) {
                Log.d(TAG, "📤 Status sent to server")
            } else {
                Log.w(TAG, "⚠️  Failed to send status - not connected")
            }
        } else {
            Log.w(TAG, "⚠️  Cannot send status - WebSocket not connected")
        }
    }
    
    fun isConnected(): Boolean = isConnected
    
    fun getCameraId(): String = cameraId
    
    fun disconnect() {
        Log.i(TAG, "🔌 Disconnecting WebSocket...")
        reconnectJob?.cancel()
        webSocket?.close(1000, "Client disconnect")
        isConnected = false
    }
}
