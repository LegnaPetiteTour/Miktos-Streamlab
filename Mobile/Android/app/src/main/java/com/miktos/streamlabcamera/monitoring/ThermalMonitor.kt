package com.miktos.streamlabcamera.monitoring

import android.content.Context
import android.content.Intent
import android.os.PowerManager
import android.os.Build
import android.util.Log
import java.util.concurrent.Executors
import java.util.concurrent.ScheduledExecutorService
import java.util.concurrent.TimeUnit

class ThermalMonitor(
    private val context: Context,
    private val onThermalStateChanged: (ThermalState) -> Unit
) {
    private val TAG = "ThermalMonitor"
    private var executor: ScheduledExecutorService? = null
    private var currentState: ThermalState = ThermalState.OK
    
    enum class ThermalState {
        OK,      // Normal operation
        WARM,    // Reduce quality
        HOT,     // Force lower bitrate
        CRITICAL // Consider stopping
    }
    
    fun startMonitoring() {
        executor = Executors.newSingleThreadScheduledExecutor()
        
        executor?.scheduleAtFixedRate({
            checkThermalState()
        }, 0, 5, TimeUnit.SECONDS)
        
        Log.i(TAG, "🌡️ Thermal monitoring started")
    }
    
    private fun checkThermalState() {
        val newState = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val powerManager = context.getSystemService(Context.POWER_SERVICE) as PowerManager
            
            when (powerManager.currentThermalStatus) {
                PowerManager.THERMAL_STATUS_NONE,
                PowerManager.THERMAL_STATUS_LIGHT -> ThermalState.OK
                
                PowerManager.THERMAL_STATUS_MODERATE -> ThermalState.WARM
                
                PowerManager.THERMAL_STATUS_SEVERE,
                PowerManager.THERMAL_STATUS_CRITICAL -> ThermalState.HOT
                
                PowerManager.THERMAL_STATUS_EMERGENCY,
                PowerManager.THERMAL_STATUS_SHUTDOWN -> ThermalState.CRITICAL
                
                else -> ThermalState.OK
            }
        } else {
            // For older Android versions, use heuristics or always return OK
            ThermalState.OK
        }
        
        if (newState != currentState) {
            currentState = newState
            Log.w(TAG, "🌡️ Thermal state changed: $newState")
            onThermalStateChanged(newState)
            
            // Broadcast to Studio Mode
            val intent = Intent("com.miktos.STUDIO_UPDATE")
            intent.putExtra("thermal", newState.name)
            context.sendBroadcast(intent)
        }
    }
    
    fun getCurrentState(): ThermalState = currentState
    
    fun stopMonitoring() {
        executor?.shutdown()
        executor = null
        Log.i(TAG, "🌡️ Thermal monitoring stopped")
    }
}
