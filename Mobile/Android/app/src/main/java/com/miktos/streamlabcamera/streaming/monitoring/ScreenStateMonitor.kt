package com.miktos.streamlabcamera.streaming.monitoring

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.util.Log

/**
 * Screen State Monitor
 * 
 * Detects phone lock/unlock events and triggers connection verification.
 * 
 * Critical for detecting the "phone locked for 60+ minutes" bug:
 * - When phone locks, we log it and monitor closely
 * - When phone unlocks, we IMMEDIATELY verify the connection is still alive
 * - If connection died during lock, we catch it and trigger reconnection
 * 
 * This catches the case where the connection died during lock but
 * wasn't detected by the other monitors yet.
 */
class ScreenStateMonitor(
    private val context: Context,
    private val onScreenUnlocked: () -> Unit
) {
    private val TAG = "ScreenStateMonitor"
    private var isMonitoring = false
    
    private val screenReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            when (intent.action) {
                Intent.ACTION_SCREEN_OFF -> {
                    Log.d(TAG, "📵 Screen locked - monitoring closely")
                }
                Intent.ACTION_USER_PRESENT -> {
                    Log.d(TAG, "🔓 Screen unlocked - verifying connection")
                    onScreenUnlocked()
                }
            }
        }
    }
    
    /**
     * Start monitoring screen state
     */
    fun startMonitoring() {
        if (isMonitoring) {
            Log.w(TAG, "Already monitoring screen state")
            return
        }
        
        val filter = IntentFilter().apply {
            addAction(Intent.ACTION_SCREEN_OFF)
            addAction(Intent.ACTION_USER_PRESENT)
        }
        context.registerReceiver(screenReceiver, filter)
        isMonitoring = true
        Log.i(TAG, "✅ Screen state monitoring started")
    }
    
    /**
     * Stop monitoring screen state
     */
    fun stopMonitoring() {
        if (!isMonitoring) {
            return
        }
        
        try {
            context.unregisterReceiver(screenReceiver)
            isMonitoring = false
            Log.i(TAG, "Screen state monitoring stopped")
        } catch (e: IllegalArgumentException) {
            // Already unregistered
            Log.w(TAG, "Receiver already unregistered")
        }
    }
    
    /**
     * Check if currently monitoring
     */
    fun isActive(): Boolean = isMonitoring
}
