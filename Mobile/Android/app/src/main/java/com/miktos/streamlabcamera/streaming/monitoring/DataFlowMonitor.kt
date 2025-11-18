package com.miktos.streamlabcamera.streaming.monitoring

import android.util.Log
import java.util.concurrent.Executors
import java.util.concurrent.ScheduledExecutorService
import java.util.concurrent.TimeUnit

/**
 * Data Flow Monitor
 * 
 * Verifies that actual data is flowing, not just that the encoder is running.
 * Tracks confirmed successful writes and detects when data stops flowing.
 * 
 * If no successful write happens within DATA_FLOW_TIMEOUT (10 seconds),
 * triggers disconnect detection.
 * 
 * This catches cases where:
 * - Encoder is running but socket writes are failing silently
 * - Network buffer is full and writes are blocking
 * - Connection is dead but encoder hasn't detected it yet
 */
class DataFlowMonitor(
    private val onDataFlowStopped: (String) -> Unit
) {
    private val TAG = "DataFlowMonitor"
    private var executor: ScheduledExecutorService? = null
    private var lastSuccessfulWrite: Long = 0
    private val DATA_FLOW_TIMEOUT = 30_000L // 30 seconds no data = problem (allows 1 fps PAUSE mode)
    
    /**
     * Start monitoring data flow
     * Checks every 3 seconds
     */
    fun startMonitoring() {
        lastSuccessfulWrite = System.currentTimeMillis()
        
        executor = Executors.newSingleThreadScheduledExecutor()
        executor?.scheduleAtFixedRate({
            checkDataFlow()
        }, 3, 3, TimeUnit.SECONDS)
        
        Log.i(TAG, "✅ Data flow monitoring started (30s timeout for PAUSE mode compatibility)")
    }
    
    /**
     * Record a successful write
     * Call this AFTER each successful socket write
     */
    fun recordSuccessfulWrite() {
        lastSuccessfulWrite = System.currentTimeMillis()
    }
    
    /**
     * Check if data is flowing
     */
    private fun checkDataFlow() {
        val timeSinceLastWrite = System.currentTimeMillis() - lastSuccessfulWrite
        
        if (timeSinceLastWrite > DATA_FLOW_TIMEOUT) {
            Log.e(TAG, "❌ Data flow stopped - ${timeSinceLastWrite/1000}s since last successful write")
            onDataFlowStopped("No data sent for ${timeSinceLastWrite/1000}s")
            stopMonitoring()
        } else {
            Log.d(TAG, "✓ Data flowing - last write ${timeSinceLastWrite/1000}s ago")
        }
    }
    
    /**
     * Stop monitoring
     */
    fun stopMonitoring() {
        executor?.shutdown()
        executor = null
        Log.i(TAG, "Data flow monitoring stopped")
    }
    
    /**
     * Check if currently monitoring
     */
    fun isActive(): Boolean = executor != null && !executor!!.isShutdown
}
