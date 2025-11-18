package com.miktos.streamlabcamera

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Build
import android.util.Log
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.view.PreviewView
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import androidx.appcompat.widget.SwitchCompat
import com.miktos.streamlabcamera.ui.StudioModeActivity

class MainActivity : AppCompatActivity() {
    
    private lateinit var previewView: PreviewView
    private lateinit var ipInput: EditText
    private lateinit var portInput: EditText
    private lateinit var startButton: Button
    private lateinit var pauseResumeButton: Button
    private lateinit var studioModeButton: Button
    private lateinit var statusText: TextView
    private lateinit var lteFailoverSwitch: SwitchCompat
    private lateinit var lteWarning: TextView
    private lateinit var remoteControlSwitch: SwitchCompat
    private lateinit var remoteServerIp: EditText
    private lateinit var remoteServerPort: EditText
    private lateinit var remoteStatusIndicator: View
    private lateinit var remoteStatusText: TextView
    
    private var isStreaming = false
    private var isRemoteControlEnabled = false

    // Disconnect handling
    private val disconnectReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            when (intent?.action) {
                "com.miktos.STREAM_DISCONNECTED" -> {
                    val attempts = intent.getIntExtra("reconnect_attempts", 0)
                    val maxAttempts = intent.getIntExtra("max_attempts", 5)
                    val backoffMs = intent.getLongExtra("backoff_delay_ms", 0)
                    
                    runOnUiThread {
                        statusText.text = "🔄 Connection lost - Reconnecting...\n\n" +
                            "Attempt $attempts/$maxAttempts (${backoffMs/1000}s delay)\n\n" +
                            "⚠️ NOT streaming - auto-reconnect in progress"
                        startButton.text = "RECONNECTING ($attempts/$maxAttempts)"
                        startButton.isEnabled = false
                        startButton.backgroundTintList = getColorStateList(android.R.color.holo_orange_dark)
                        isStreaming = false  // Critical: UI knows we're NOT streaming
                        studioModeButton.isEnabled = false  // Disable Studio Mode during reconnection
                    }
                }
                "com.miktos.STREAM_RECONNECTED" -> {
                    runOnUiThread {
                        val ip = ipInput.text.toString()
                        val port = portInput.text.toString()
                        statusText.text = "✅ LIVE: Streaming to $ip:$port\n\n📺 Reconnected successfully!"
                        startButton.text = "STOP"
                        startButton.isEnabled = true
                        startButton.backgroundTintList = getColorStateList(android.R.color.holo_red_dark)
                        isStreaming = true  // Now we're actually streaming
                        studioModeButton.isEnabled = true  // Re-enable Studio Mode
                        Toast.makeText(this@MainActivity, "✅ Reconnected!", Toast.LENGTH_SHORT).show()
                    }
                }
                "com.miktos.STREAM_FAILED" -> {
                    runOnUiThread {
                        statusText.text = "❌ Connection Failed\n\n" +
                            "Auto-reconnect gave up after multiple attempts.\n\n" +
                            "Please check network and tap RETRY"
                        startButton.text = "RETRY"
                        startButton.isEnabled = true
                        startButton.backgroundTintList = getColorStateList(android.R.color.holo_green_dark)
                        isStreaming = false
                        studioModeButton.isEnabled = false  // Keep Studio Mode disabled
                        Toast.makeText(this@MainActivity, "❌ Reconnection failed", Toast.LENGTH_LONG).show()
                    }
                }
                "com.miktos.NETWORK_TYPE_CHANGED" -> {
                    val networkType = intent.getStringExtra("network_type")
                    val warning = intent.getStringExtra("warning")
                    
                    runOnUiThread {
                        if (networkType == "LTE") {
                            Toast.makeText(this@MainActivity, 
                                "📱 Using LTE (Cellular)\n$warning", 
                                Toast.LENGTH_LONG).show()
                            statusText.append("\n\n📱 Network: LTE (Reduced bitrate)")
                        } else if (networkType == "WIFI") {
                            Toast.makeText(this@MainActivity, 
                                "📶 Back on WiFi (Full quality)", 
                                Toast.LENGTH_SHORT).show()
                        }
                    }
                }
                "com.miktos.REMOTE_CONTROL_CONNECTED" -> {
                    Log.d("MainActivity", "📡 Received REMOTE_CONTROL_CONNECTED broadcast")
                    runOnUiThread {
                        Log.d("MainActivity", "📡 Updating UI to show connected state")
                        remoteStatusIndicator.setBackgroundResource(android.R.drawable.presence_online)
                        remoteStatusText.text = "Connected"
                        remoteStatusText.setTextColor(getColor(android.R.color.holo_green_light))
                        Toast.makeText(this@MainActivity, "✅ Remote control connected", Toast.LENGTH_SHORT).show()
                    }
                }
                "com.miktos.REMOTE_CONTROL_DISCONNECTED" -> {
                    Log.d("MainActivity", "📡 Received REMOTE_CONTROL_DISCONNECTED broadcast")
                    runOnUiThread {
                        remoteStatusIndicator.setBackgroundResource(R.drawable.red_dot)
                        remoteStatusText.text = "Disconnected"
                        remoteStatusText.setTextColor(getColor(android.R.color.darker_gray))
                    }
                }
                "com.miktos.STREAMING_STOPPED" -> {
                    Log.d("MainActivity", "📡 Received STREAMING_STOPPED broadcast")
                    runOnUiThread {
                        isStreaming = false
                        startButton.text = "Start Streaming"
                        startButton.backgroundTintList = getColorStateList(android.R.color.holo_green_dark)
                        pauseResumeButton.visibility = android.view.View.GONE
                        studioModeButton.isEnabled = false
                        statusText.text = "Streaming stopped"
                        Log.d("MainActivity", "✅ UI updated - button shows 'Start Streaming'")
                    }
                }
                "com.miktos.STREAMING_STARTED" -> {
                    Log.d("MainActivity", "📡 Received STREAMING_STARTED broadcast")
                    runOnUiThread {
                        isStreaming = true
                        startButton.text = "STOP"
                        startButton.backgroundTintList = getColorStateList(android.R.color.holo_red_dark)
                        pauseResumeButton.text = "⏸️ PAUSE"
                        pauseResumeButton.visibility = android.view.View.VISIBLE
                        pauseResumeButton.backgroundTintList = getColorStateList(android.R.color.holo_orange_dark)
                        studioModeButton.isEnabled = true
                        statusText.text = "Streaming..."
                        Log.d("MainActivity", "✅ UI updated - button shows 'STOP'")
                    }
                }
            }
        }
    }
    
    companion object {
        private const val REQUEST_CAMERA_PERMISSION = 200
        private const val PREFS_NAME = "StreamlabPrefs"
        private const val PREF_SERVER_IP = "server_ip"
        private const val PREF_SERVER_PORT = "server_port"
        private const val PREF_LTE_FAILOVER = "lte_failover_enabled"
        private const val PREF_REMOTE_CONTROL = "remote_control_enabled"
        private const val PREF_REMOTE_IP = "remote_server_ip"
        private const val PREF_REMOTE_PORT = "remote_server_port"
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Keep screen on during streaming to prevent camera disconnect
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        
        // Enable immersive mode to hide navigation bar
        enableImmersiveMode()
        
        // Register disconnect receiver
        val filter = IntentFilter().apply {
            addAction("com.miktos.STREAM_DISCONNECTED")
            addAction("com.miktos.STREAM_RECONNECTED")
            addAction("com.miktos.STREAM_FAILED")
            addAction("com.miktos.NETWORK_TYPE_CHANGED")
            addAction("com.miktos.REMOTE_CONTROL_CONNECTED")
            addAction("com.miktos.REMOTE_CONTROL_DISCONNECTED")
            addAction("com.miktos.STREAMING_STOPPED")
            addAction("com.miktos.STREAMING_STARTED")
            addAction("com.miktos.STREAMING_PAUSED")
            addAction("com.miktos.STREAMING_RESUMED")
        }
        registerReceiver(disconnectReceiver, filter, RECEIVER_NOT_EXPORTED)
        
        // Initialize views
        previewView = findViewById(R.id.previewView)
        ipInput = findViewById(R.id.ipInput)
        portInput = findViewById(R.id.portInput)
        startButton = findViewById(R.id.startButton)
        pauseResumeButton = findViewById(R.id.pauseResumeButton)
        studioModeButton = findViewById(R.id.studioModeButton)
        statusText = findViewById(R.id.statusText)
        lteFailoverSwitch = findViewById(R.id.lteFailoverSwitch)
        lteWarning = findViewById(R.id.lteWarning)
        remoteControlSwitch = findViewById(R.id.remoteControlSwitch)
        remoteServerIp = findViewById(R.id.remoteServerIp)
        remoteServerPort = findViewById(R.id.remoteServerPort)
        remoteStatusIndicator = findViewById(R.id.remoteStatusIndicator)
        remoteStatusText = findViewById(R.id.remoteStatusText)
        
        // Load saved settings
        loadSavedSettings()
        
        // Set up LTE failover switch listener
        lteFailoverSwitch.setOnCheckedChangeListener { _, isChecked ->
            // Update service if running
            CameraStreamService.streamer?.setLteFailoverEnabled(isChecked)
            
            // Show/hide warning text
            lteWarning.visibility = if (isChecked) View.VISIBLE else View.GONE
            
            // Save preference
            getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE).edit()
                .putBoolean(PREF_LTE_FAILOVER, isChecked)
                .apply()
            
            // Show toast to confirm
            val message = if (isChecked) {
                "✅ LTE Backup Enabled\nWill use cellular if WiFi fails"
            } else {
                "⚠️ LTE Backup Disabled\nWiFi-only mode"
            }
            Toast.makeText(this, message, Toast.LENGTH_SHORT).show()
        }
        
        // Set up remote control switch listener
        remoteControlSwitch.setOnCheckedChangeListener { _, isChecked ->
            isRemoteControlEnabled = isChecked
            
            // Enable/disable input fields
            remoteServerIp.isEnabled = isChecked
            remoteServerPort.isEnabled = isChecked
            
            // Save preference
            getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE).edit()
                .putBoolean(PREF_REMOTE_CONTROL, isChecked)
                .apply()
            
            // Enable or disable remote control immediately (even if not streaming)
            if (isChecked) {
                val serverIp = remoteServerIp.text.toString()
                val serverPort = remoteServerPort.text.toString().toIntOrNull() ?: 9000
                
                if (serverIp.isNotEmpty()) {
                    // Save server settings
                    getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE).edit()
                        .putString(PREF_REMOTE_IP, serverIp)
                        .putInt(PREF_REMOTE_PORT, serverPort)
                        .apply()
                    
                    // Start the service if not already running (just for remote control)
                    if (!isStreaming) {
                        // Start a minimal service instance just for remote control
                        CameraStreamService.startForRemoteControl(this, serverIp, serverPort)
                    } else {
                        // Service already running, just enable remote control
                        CameraStreamService.streamer?.enableRemoteControl(serverIp, serverPort)
                    }
                    Toast.makeText(this, "🎮 Connecting to remote control server...", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(this, "⚠️ Enter server IP first", Toast.LENGTH_SHORT).show()
                    remoteControlSwitch.isChecked = false
                }
            } else {
                CameraStreamService.streamer?.disableRemoteControl()
                remoteStatusIndicator.setBackgroundResource(R.drawable.red_dot)
                remoteStatusText.text = "Disconnected"
                remoteStatusText.setTextColor(getColor(android.R.color.darker_gray))
                Toast.makeText(this, "🎮 Remote control disabled", Toast.LENGTH_SHORT).show()
            }
        }
        
        // Request permissions
        if (!hasRequiredPermissions()) {
            requestPermissions()
        }
        
        startButton.setOnClickListener {
            if (!isStreaming) {
                startStreaming()
            } else {
                stopStreaming()
            }
        }
        
        // Pause/Resume button - only visible when streaming
        pauseResumeButton.setOnClickListener {
            CameraStreamService.streamer?.let { streamer ->
                if (streamer.isPaused) {
                    streamer.resumeStreaming()
                } else {
                    streamer.pauseStreaming()
                }
            }
        }
        
        // Studio Mode button - only enabled when streaming
        studioModeButton.setOnClickListener {
            if (isStreaming) {
                StudioModeActivity.start(this)
            } else {
                Toast.makeText(this, "⚠️ Start streaming first", Toast.LENGTH_SHORT).show()
            }
        }
    }
    
    private fun hasRequiredPermissions(): Boolean {
        return ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.CAMERA
        ) == PackageManager.PERMISSION_GRANTED &&
        ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.RECORD_AUDIO
        ) == PackageManager.PERMISSION_GRANTED
    }
    
    private fun requestPermissions() {
        val permissions = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            arrayOf(
                Manifest.permission.CAMERA,
                Manifest.permission.RECORD_AUDIO,
                Manifest.permission.POST_NOTIFICATIONS
            )
        } else {
            arrayOf(
                Manifest.permission.CAMERA,
                Manifest.permission.RECORD_AUDIO
            )
        }
        
        ActivityCompat.requestPermissions(
            this,
            permissions,
            REQUEST_CAMERA_PERMISSION
        )
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        
        if (requestCode == REQUEST_CAMERA_PERMISSION) {
            if (grantResults.all { it == PackageManager.PERMISSION_GRANTED }) {
                Toast.makeText(this, "Permissions granted!", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(
                    this,
                    "Camera and audio permissions are required",
                    Toast.LENGTH_LONG
                ).show()
                finish()
            }
        }
    }
    
    private fun startStreaming() {
        val ip = ipInput.text.toString()
        val port = portInput.text.toString().toIntOrNull() ?: 8554
        
        if (ip.isEmpty()) {
            Toast.makeText(this, "Please enter Mac IP address", Toast.LENGTH_SHORT).show()
            return
        }
        
        if (!hasRequiredPermissions()) {
            requestPermissions()
            return
        }
        
        // Save settings for next time
        saveSettings(ip, port)
        
        // Start the foreground service with LTE failover preference
        CameraStreamService.start(this, ip, port)
        
        // Apply LTE failover setting to the streamer (service will handle it)
        val lteEnabled = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getBoolean(PREF_LTE_FAILOVER, false)
        // The service will pick up this preference when it creates the streamer
        
        // Enable remote control if enabled
        if (isRemoteControlEnabled) {
            val serverIp = remoteServerIp.text.toString()
            val serverPort = remoteServerPort.text.toString().toIntOrNull() ?: 9000
            
            if (serverIp.isNotEmpty()) {
                // Wait a moment for service to start, then enable remote control
                startButton.postDelayed({
                    CameraStreamService.streamer?.enableRemoteControl(serverIp, serverPort)
                }, 500)
            }
        }
        
        // Update UI
        isStreaming = true
        startButton.text = "STOP"
        statusText.text = "✅ LIVE: Streaming to $ip:$port\n\n📺 Check notification and Mac screen!"
        startButton.backgroundTintList = getColorStateList(android.R.color.holo_red_dark)
        studioModeButton.isEnabled = true  // Enable Studio Mode when streaming
        
        val networkMode = if (lteEnabled) "WiFi + LTE backup" else "WiFi only"
        Toast.makeText(this, "Service started ($networkMode) - check notification!", Toast.LENGTH_LONG).show()
    }
    
    private fun stopStreaming() {
        // Stop the foreground service
        CameraStreamService.stop(this)
        
        // Update UI
        isStreaming = false
        startButton.text = "START"
        statusText.text = "Stopped"
        startButton.backgroundTintList = getColorStateList(android.R.color.holo_green_dark)
        studioModeButton.isEnabled = false  // Disable Studio Mode when stopped
    }
    
    private fun loadSavedSettings() {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val savedIp = prefs.getString(PREF_SERVER_IP, "")
        val savedPort = prefs.getInt(PREF_SERVER_PORT, 8554)
        val lteFailoverEnabled = prefs.getBoolean(PREF_LTE_FAILOVER, false)
        val remoteControlEnabled = prefs.getBoolean(PREF_REMOTE_CONTROL, false)
        val remoteIp = prefs.getString(PREF_REMOTE_IP, "192.168.2.36")  // Default to current desktop IP
        val remotePort = prefs.getInt(PREF_REMOTE_PORT, 9000)
        
        if (!savedIp.isNullOrEmpty()) {
            ipInput.setText(savedIp)
        }
        portInput.setText(savedPort.toString())
        
        // Restore LTE failover setting
        lteFailoverSwitch.isChecked = lteFailoverEnabled
        lteWarning.visibility = if (lteFailoverEnabled) View.VISIBLE else View.GONE
        
        // Restore remote control settings
        remoteControlSwitch.isChecked = remoteControlEnabled
        isRemoteControlEnabled = remoteControlEnabled
        remoteServerIp.isEnabled = remoteControlEnabled
        remoteServerPort.isEnabled = remoteControlEnabled
        
        // Always set the remote IP (with default if empty)
        remoteServerIp.setText(remoteIp ?: "192.168.2.36")
        remoteServerPort.setText(remotePort.toString())
        
        // AUTO-CONNECT: If remote control was enabled, reconnect automatically
        if (remoteControlEnabled && !remoteIp.isNullOrEmpty()) {
            Log.i("MainActivity", "🔄 Auto-connecting to remote control server...")
            // Start service for remote control if not already running
            if (!isStreaming) {
                CameraStreamService.startForRemoteControl(this, remoteIp, remotePort)
            } else {
                // Service already running, just enable remote control
                CameraStreamService.streamer?.enableRemoteControl(remoteIp, remotePort)
            }
            Toast.makeText(this, "🎮 Auto-connecting to remote control...", Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun saveSettings(ip: String, port: Int) {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().apply {
            putString(PREF_SERVER_IP, ip)
            putInt(PREF_SERVER_PORT, port)
            apply()
        }
    }
    
    private fun enableImmersiveMode() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            // Android 11+ (API 30+)
            window.setDecorFitsSystemWindows(false)
            window.insetsController?.let { controller ->
                controller.hide(android.view.WindowInsets.Type.navigationBars())
                controller.systemBarsBehavior = android.view.WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
            }
        } else {
            // Android 10 and below
            @Suppress("DEPRECATION")
            window.decorView.systemUiVisibility = (
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                or View.SYSTEM_UI_FLAG_FULLSCREEN
            )
        }
    }
    
    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) {
            enableImmersiveMode()
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        
        // Unregister disconnect receiver
        unregisterReceiver(disconnectReceiver)
        if (isStreaming) {
            stopStreaming()
        }
    }
}
