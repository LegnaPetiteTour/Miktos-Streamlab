package com.miktos.streamlabcamera.ui

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import android.os.Bundle
import android.os.PowerManager
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.miktos.streamlabcamera.R
import com.miktos.streamlabcamera.MainActivity

class StudioModeActivity : AppCompatActivity() {
    
    private lateinit var redDot: View
    private lateinit var statusText: TextView
    private lateinit var powerManager: PowerManager
    private var wakeLock: PowerManager.WakeLock? = null
    
    // Current status values (cached for battery updates)
    private var currentBattery: Int = 0
    private var currentIsCharging: Boolean = false
    private var currentNetworkType: String = "UNKNOWN"
    private var currentThermal: String = "OK"
    
    private val statusReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            when (intent?.action) {
                "com.miktos.STUDIO_UPDATE" -> {
                    currentBattery = intent.getIntExtra("battery", 0)
                    currentIsCharging = intent.getBooleanExtra("charging", false)
                    currentNetworkType = intent.getStringExtra("network") ?: "UNKNOWN"
                    currentThermal = intent.getStringExtra("thermal") ?: "OK"
                    updateStatusDisplay()
                }
                "com.miktos.EXIT_STUDIO_MODE" -> {
                    android.util.Log.i("StudioModeActivity", "📡 Received EXIT_STUDIO_MODE broadcast")
                    exitStudioMode()
                }
            }
        }
    }
    
    // Battery change receiver for real-time battery updates
    private val batteryReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            if (intent?.action == Intent.ACTION_BATTERY_CHANGED) {
                val level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
                val scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, -1)
                val status = intent.getIntExtra(BatteryManager.EXTRA_STATUS, -1)
                
                if (level >= 0 && scale > 0) {
                    currentBattery = (level * 100 / scale.toFloat()).toInt()
                    currentIsCharging = status == BatteryManager.BATTERY_STATUS_CHARGING || 
                                       status == BatteryManager.BATTERY_STATUS_FULL
                    updateStatusDisplay()
                }
            }
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_studio_mode)
        
        // Initialize views
        redDot = findViewById(R.id.redDot)
        statusText = findViewById(R.id.statusText)
        
        // Setup full-screen immersive mode
        setupImmersiveMode()
        
        // Keep screen on but dimmed
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        
        // Dim screen to minimum (5%)
        val layoutParams = window.attributes
        layoutParams.screenBrightness = 0.05f
        window.attributes = layoutParams
        
        // Acquire wake lock
        powerManager = getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = powerManager.newWakeLock(
            PowerManager.SCREEN_DIM_WAKE_LOCK,
            "MiktosCamera::StudioMode"
        )
        wakeLock?.acquire(24 * 60 * 60 * 1000L) // 24 hours max
        
        // Register status receiver
        val filter = IntentFilter().apply {
            addAction("com.miktos.STUDIO_UPDATE")
            addAction("com.miktos.EXIT_STUDIO_MODE")
        }
        registerReceiver(statusReceiver, filter, RECEIVER_NOT_EXPORTED)
        
        // Register battery receiver for real-time battery updates
        val batteryFilter = IntentFilter(Intent.ACTION_BATTERY_CHANGED)
        registerReceiver(batteryReceiver, batteryFilter)
        
        // Animate red dot (pulse effect)
        startRedDotAnimation()
        
        // Initialize status display
        updateStatusFromSystem()
    }
    
    private fun setupImmersiveMode() {
        window.decorView.systemUiVisibility = (
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
            or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
            or View.SYSTEM_UI_FLAG_FULLSCREEN
            or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
        )
    }
    
    private fun startRedDotAnimation() {
        redDot.animate()
            .alpha(0.3f)
            .setDuration(1000)
            .withEndAction {
                redDot.animate()
                    .alpha(1.0f)
                    .setDuration(1000)
                    .withEndAction {
                        if (!isFinishing) {
                            startRedDotAnimation()
                        }
                    }
            }
    }
    
    private fun updateStatusFromSystem() {
        val batteryManager = getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        val battery = batteryManager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        val batteryStatus = registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        val status = batteryStatus?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) ?: -1
        val isCharging = status == BatteryManager.BATTERY_STATUS_CHARGING || 
                        status == BatteryManager.BATTERY_STATUS_FULL
        
        currentBattery = battery
        currentIsCharging = isCharging
        updateStatusDisplay()
    }
    
    private fun updateStatusDisplay() {
        val chargeIcon = if (currentIsCharging) "⚡" else ""
        val networkIcon = when (currentNetworkType) {
            "LAN_WIFI", "INET_WIFI" -> "📶"
            "LTE_CELLULAR" -> "📱"
            else -> "📵"
        }
        val thermalIcon = when (currentThermal) {
            "OK" -> ""
            "WARM" -> "🌡️"
            "HOT" -> "🔥"
            "CRITICAL" -> "☠️"
            else -> ""
        }
        
        statusText.text = "$networkIcon $chargeIcon$currentBattery% $thermalIcon"
    }
    
    override fun onTouchEvent(event: MotionEvent): Boolean {
        // Block all touch events - no accidental interactions
        return true
    }
    
    private fun exitStudioMode() {
        android.util.Log.i("StudioModeActivity", "🚪 Exiting Studio Mode")
        
        // Restore brightness
        val layoutParams = window.attributes
        layoutParams.screenBrightness = WindowManager.LayoutParams.BRIGHTNESS_OVERRIDE_NONE
        window.attributes = layoutParams
        
        // Release wake lock (only if held)
        wakeLock?.let {
            if (it.isHeld) {
                it.release()
                wakeLock = null  // Set to null so onDestroy doesn't try to release again
                android.util.Log.i("StudioModeActivity", "🔓 Wake lock released")
            }
        }
        
        // Just finish - MainActivity is below us in the stack
        finish()
        
        android.util.Log.i("StudioModeActivity", "✅ Studio Mode finished")
    }
    
    override fun onBackPressed() {
        // Treat back button same as exit
        exitStudioMode()
    }
    
    override fun onDestroy() {
        super.onDestroy()
        unregisterReceiver(statusReceiver)
        unregisterReceiver(batteryReceiver)
        
        // Only release wake lock if it's still held
        wakeLock?.let {
            if (it.isHeld) {
                it.release()
                android.util.Log.i("StudioModeActivity", "🔓 Wake lock released in onDestroy")
            }
        }
        wakeLock = null
    }
    
    companion object {
        fun start(context: Context) {
            val intent = Intent(context, StudioModeActivity::class.java)
            intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK
            context.startActivity(intent)
        }
    }
}
