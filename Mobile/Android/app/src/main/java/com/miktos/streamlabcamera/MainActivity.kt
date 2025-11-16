package com.miktos.streamlabcamera

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Build
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

class MainActivity : AppCompatActivity() {
    
    private lateinit var previewView: PreviewView
    private lateinit var ipInput: EditText
    private lateinit var portInput: EditText
    private lateinit var startButton: Button
    private lateinit var statusText: TextView
    
    private var isStreaming = false

    // Disconnect handling
    private val disconnectReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            when (intent?.action) {
                "com.miktos.STREAM_DISCONNECTED" -> {
                    runOnUiThread {
                        statusText.text = "🔄 Disconnected - Reconnecting..."
                        startButton.text = "RECONNECTING"
                        startButton.isEnabled = false
                        isStreaming = false
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
                        isStreaming = true
                    }
                }
                "com.miktos.STREAM_FAILED" -> {
                    runOnUiThread {
                        statusText.text = "❌ Connection Failed - Please retry"
                        startButton.text = "RETRY"
                        startButton.isEnabled = true
                        isStreaming = false
                    }
                }
            }
        }
    }
    
    companion object {
        private const val REQUEST_CAMERA_PERMISSION = 200
        private const val PREFS_NAME = "StreamLabSettings"
        private const val PREF_SERVER_IP = "server_ip"
        private const val PREF_SERVER_PORT = "server_port"
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
        }
        registerReceiver(disconnectReceiver, filter, RECEIVER_NOT_EXPORTED)
        
        // Initialize views
        previewView = findViewById(R.id.previewView)
        ipInput = findViewById(R.id.ipInput)
        portInput = findViewById(R.id.portInput)
        startButton = findViewById(R.id.startButton)
        statusText = findViewById(R.id.statusText)
        
        // Load saved settings
        loadSavedSettings()
        
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
        
        // Start the foreground service
        CameraStreamService.start(this, ip, port)
        
        // Update UI
        isStreaming = true
        startButton.text = "STOP"
        statusText.text = "✅ LIVE: Streaming to $ip:$port\n\n📺 Check notification and Mac screen!"
        startButton.backgroundTintList = getColorStateList(android.R.color.holo_red_dark)
        
        Toast.makeText(this, "Service started - check notification!", Toast.LENGTH_LONG).show()
    }
    
    private fun stopStreaming() {
        // Stop the foreground service
        CameraStreamService.stop(this)
        
        // Update UI
        isStreaming = false
        startButton.text = "START"
        statusText.text = "Stopped"
        startButton.backgroundTintList = getColorStateList(android.R.color.holo_green_dark)
    }
    
    private fun loadSavedSettings() {
        val prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val savedIp = prefs.getString(PREF_SERVER_IP, "")
        val savedPort = prefs.getInt(PREF_SERVER_PORT, 8554)
        
        if (!savedIp.isNullOrEmpty()) {
            ipInput.setText(savedIp)
        }
        portInput.setText(savedPort.toString())
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
