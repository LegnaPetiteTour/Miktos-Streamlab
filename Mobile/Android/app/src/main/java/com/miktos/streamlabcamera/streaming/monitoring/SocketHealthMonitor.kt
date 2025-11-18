package com.miktos.streamlabcamera.streaming.monitoring

import android.util.Log
import java.io.IOException
import java.net.Socket
import java.util.concurrent.Executors
import java.util.concurrent.ScheduledExecutorService
import java.util.concurrent.TimeUnit

/**
 * Active Socket Health Monitor
 * 
 * The CRITICAL missing piece: actively probes the socket to verify it's truly alive.
 * TCP doesn't immediately know when the remote end dies - we force a check by writing.
 * 
 * Checks every 2 seconds:
 * - Basic state (isClosed, isConnected) - can be misleading
 * - Active probe: writes a test byte to force OS to verify connection
 * 
 * If the receiver is dead, the write will throw IOException immediately.
 */
class SocketHealthMonitor(
    private val onDisconnected: (String) -> Unit
) {
    private val TAG = "SocketHealthMonitor"
    private var executor: ScheduledExecutorService? = null
    private var socket: Socket? = null
    private var isMonitoring = false
    
    /**
     * Start monitoring the given socket
     * Checks health every 2 seconds
     */
    fun startMonitoring(socket: Socket) {
        this.socket = socket
        isMonitoring = true
        
        executor = Executors.newSingleThreadScheduledExecutor()
        executor?.scheduleAtFixedRate({
            if (!checkSocketHealth()) {
                onDisconnected("Socket health check failed")
                stopMonitoring()
            }
        }, 1, 2, TimeUnit.SECONDS)
        
        Log.i(TAG, "✅ Socket health monitoring started (2s interval)")
    }
    
    /**
     * Active socket health check
     * 
     * @return true if socket is healthy, false if dead
     */
    private fun checkSocketHealth(): Boolean {
        val sock = socket ?: return false
        
        // Basic checks (these can lie - socket might report connected when it's dead!)
        if (sock.isClosed || !sock.isConnected) {
            Log.e(TAG, "❌ Socket reports closed/disconnected")
            return false
        }
        
        // ACTIVE PROBE - This is the critical check!
        // Try to actually write to the socket.
        // If the connection is dead, this will throw IOException
        try {
            val output = sock.getOutputStream()
            
            // Write a single null byte as a heartbeat
            // If socket is dead, this will fail immediately
            output.write(0x00)
            output.flush()
            
            // Socket is truly alive
            return true
            
        } catch (e: IOException) {
            Log.e(TAG, "❌ Active probe failed - socket is DEAD: ${e.message}")
            return false
        }
    }
    
    /**
     * Stop monitoring
     */
    fun stopMonitoring() {
        isMonitoring = false
        executor?.shutdown()
        executor = null
        Log.i(TAG, "Socket health monitoring stopped")
    }
    
    /**
     * Check if currently monitoring
     */
    fun isActive(): Boolean = isMonitoring
}
