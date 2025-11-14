package com.miktos.streamlabcamera

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
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
            if (intent?.action == "com.miktos.STREAM_DISCONNECTED") {
                runOnUiThread {
                    statusText.text = "❌ Disconnected"
                    startButton.text = "RECONNECT"
                    startButton.isEnabled = true
                    isStreaming = false
                }
            }
        }
    }
    
    companion object {
        private const val REQUEST_CAMERA_PERMISSION = 200
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Keep screen on during streaming to prevent camera disconnect
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        
        // Register disconnect receiver
        val filter = IntentFilter("com.miktos.STREAM_DISCONNECTED")
        registerReceiver(disconnectReceiver, filter, RECEIVER_NOT_EXPORTED)
        
        // Initialize views
        previewView = findViewById(R.id.previewView)
        ipInput = findViewById(R.id.ipInput)
        portInput = findViewById(R.id.portInput)
        startButton = findViewById(R.id.startButton)
        statusText = findViewById(R.id.statusText)
        
        // Set default values
        portInput.setText("8554")
        
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
        ActivityCompat.requestPermissions(
            this,
            arrayOf(
                Manifest.permission.CAMERA,
                Manifest.permission.RECORD_AUDIO
            ),
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
        
        // Start the foreground service
        CameraStreamService.start(this, ip, port)
        
        // Update UI
        isStreaming = true
        startButton.text = "STOP STREAMING"
        statusText.text = "✅ LIVE: Streaming to $ip:$port\n\n📺 Check notification and Mac screen!"
        startButton.setBackgroundColor(getColor(android.R.color.holo_red_dark))
        
        Toast.makeText(this, "Service started - check notification!", Toast.LENGTH_LONG).show()
    }
    
    private fun stopStreaming() {
        // Stop the foreground service
        CameraStreamService.stop(this)
        
        // Update UI
        isStreaming = false
        startButton.text = "START STREAMING"
        statusText.text = "Stopped"
        startButton.setBackgroundColor(getColor(android.R.color.holo_green_dark))
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
