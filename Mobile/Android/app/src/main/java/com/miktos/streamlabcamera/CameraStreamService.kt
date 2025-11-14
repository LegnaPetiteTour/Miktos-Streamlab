package com.miktos.streamlabcamera

import android.app.*
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat

class CameraStreamService : Service() {
    
    companion object {
        private const val NOTIFICATION_ID = 1001
        private const val CHANNEL_ID = "camera_stream_channel"
        
        fun start(context: Context, ip: String, port: Int) {
            val intent = Intent(context, CameraStreamService::class.java).apply {
                putExtra("ip", ip)
                putExtra("port", port)
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }
        
        fun stop(context: Context) {
            context.stopService(Intent(context, CameraStreamService::class.java))
        }
    }
    
    private var cameraStreamer: CameraStreamer? = null
    
    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val ip = intent?.getStringExtra("ip") ?: return START_NOT_STICKY
        val port = intent.getIntExtra("port", 8554)
        
        // Start foreground IMMEDIATELY
        val notification = createNotification("Connecting to $ip:$port...")
        startForeground(NOTIFICATION_ID, notification)
        
        // Initialize camera streamer
        cameraStreamer = CameraStreamer(this) { isStreaming ->
            if (isStreaming) {
                updateNotification("📹 LIVE: Streaming to $ip:$port")
            } else {
                updateNotification("⏸ Stream stopped")
                stopSelf()
            }
        }
        
        // Start streaming
        cameraStreamer?.startStreaming(ip, port)
        
        return START_STICKY
    }
    
    override fun onDestroy() {
        super.onDestroy()
        cameraStreamer?.stopStreaming()
        cameraStreamer = null
    }
    
    override fun onBind(intent: Intent?): IBinder? = null
    
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Camera Streaming",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Keeps camera streaming active"
                setShowBadge(false)
            }
            
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }
    
    private fun createNotification(text: String): Notification {
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE
        )
        
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Miktos Camera")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_menu_camera)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }
    
    private fun updateNotification(text: String) {
        val notification = createNotification(text)
        val manager = getSystemService(NotificationManager::class.java)
        manager.notify(NOTIFICATION_ID, notification)
    }
}
