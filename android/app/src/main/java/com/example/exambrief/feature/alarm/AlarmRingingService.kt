package com.example.exambrief.feature.alarm

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.media.AudioAttributes
import android.media.Ringtone
import android.media.RingtoneManager
import android.net.Uri
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import com.example.exambrief.feature.briefing.BriefingPlaybackService
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch

@AndroidEntryPoint
class AlarmRingingService : Service() {
    @Inject lateinit var repository: AlarmRepository
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var ringtone: Ringtone? = null
    private var wakeLock: PowerManager.WakeLock? = null
    private var currentId: String? = null
    private var morningBriefEnabled = false
    private var autoPlayBrief = false

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_STOP -> stopRinging(playBrief = autoPlayBrief)
            ACTION_STOP_AND_PLAY -> stopRinging(playBrief = morningBriefEnabled)
            ACTION_SNOOZE -> {
                val id = currentId ?: intent.getStringExtra(AlarmRepository.EXTRA_ALARM_ID)
                scope.launch {
                    try {
                        if (id != null) repository.snooze(id)
                    } finally {
                        stopRinging()
                    }
                }
            }
            ACTION_RING -> {
                val id = intent.getStringExtra(AlarmRepository.EXTRA_ALARM_ID) ?: return START_NOT_STICKY
                if (currentId == id) return START_NOT_STICKY
                stopSound()
                currentId = id
                morningBriefEnabled = intent.getBooleanExtra(EXTRA_MORNING_BRIEF_ENABLED, false)
                autoPlayBrief = intent.getBooleanExtra(EXTRA_AUTO_PLAY_BRIEF, false)
                createChannel()
                val label = intent.getStringExtra(EXTRA_LABEL).orEmpty().ifEmpty { "闹钟" }
                startForeground(NOTIFICATION_ID, notification(id, label))
                wakeLock = getSystemService(PowerManager::class.java)
                    .newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "exambrief:alarm")
                    .apply { acquire(10 * 60_000L) }
                val uri = RingtoneManager.getActualDefaultRingtoneUri(this, RingtoneManager.TYPE_ALARM)
                    ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
                ringtone = RingtoneManager.getRingtone(this, uri)?.apply {
                    audioAttributes = AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_ALARM)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                        .build()
                    isLooping = true
                    play()
                }
                if (intent.getBooleanExtra(EXTRA_VIBRATE, true)) {
                    val vibrator = if (Build.VERSION.SDK_INT >= 31) {
                        getSystemService(VibratorManager::class.java).defaultVibrator
                    } else {
                        @Suppress("DEPRECATION")
                        getSystemService(Vibrator::class.java)
                    }
                    vibrator.vibrate(VibrationEffect.createWaveform(longArrayOf(0, 500, 500), 0))
                }
            }
            else -> stopSelf(startId)
        }
        return START_NOT_STICKY
    }

    private fun notification(id: String, label: String): Notification {
        val show = PendingIntent.getActivity(
            this, 0,
            Intent(this, AlarmRingingActivity::class.java).apply {
                data = Uri.parse("exambrief://alarm/ringing/$id")
                putExtra(AlarmRepository.EXTRA_ALARM_ID, id)
                putExtra(EXTRA_LABEL, label)
                putExtra(EXTRA_MORNING_BRIEF_ENABLED, morningBriefEnabled)
                putExtra(EXTRA_AUTO_PLAY_BRIEF, autoPlayBrief)
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        return Notification.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
            .setContentTitle(label)
            .setContentText("闹钟正在响铃")
            .setCategory(Notification.CATEGORY_ALARM)
            .setVisibility(Notification.VISIBILITY_PUBLIC)
            .setOngoing(true)
            .setContentIntent(show)
            .setFullScreenIntent(show, true)
            .addAction(0, "停止", actionIntent(id, ACTION_STOP))
            .apply {
                if (morningBriefEnabled && !autoPlayBrief) {
                    addAction(0, "停止并播报", actionIntent(id, ACTION_STOP_AND_PLAY))
                }
            }
            .addAction(0, "稍后提醒", actionIntent(id, ACTION_SNOOZE))
            .build()
    }

    private fun actionIntent(id: String, actionName: String): PendingIntent = PendingIntent.getService(
        this, 0,
        Intent(this, AlarmRingingService::class.java).apply {
            action = actionName
            data = Uri.parse("exambrief://alarm/$actionName/$id")
            putExtra(AlarmRepository.EXTRA_ALARM_ID, id)
        },
        PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
    )

    private fun createChannel() {
        val attributes = AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ALARM).build()
        val channel = NotificationChannel(
            CHANNEL_ID, "闹钟响铃", NotificationManager.IMPORTANCE_HIGH
        ).apply {
            setSound(null, attributes)
            enableVibration(false)
            lockscreenVisibility = Notification.VISIBILITY_PUBLIC
        }
        getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }

    private fun stopSound() {
        ringtone?.stop()
        ringtone = null
        getSystemService(Vibrator::class.java)?.cancel()
        wakeLock?.let { if (it.isHeld) it.release() }
        wakeLock = null
    }

    private fun stopRinging(playBrief: Boolean = false) {
        stopSound()
        currentId = null
        stopForeground(STOP_FOREGROUND_REMOVE)
        if (playBrief) {
            startForegroundService(
                Intent(this, BriefingPlaybackService::class.java)
                    .setAction(BriefingPlaybackService.ACTION_PLAY)
            )
        }
        stopSelf()
    }

    override fun onDestroy() {
        stopSound()
        scope.cancel()
        super.onDestroy()
    }

    companion object {
        const val ACTION_RING = "com.example.exambrief.alarm.RING"
        const val ACTION_STOP = "com.example.exambrief.alarm.STOP"
        const val ACTION_SNOOZE = "com.example.exambrief.alarm.SNOOZE"
        const val ACTION_STOP_AND_PLAY = "com.example.exambrief.alarm.STOP_AND_PLAY"
        const val EXTRA_LABEL = "label"
        const val EXTRA_VIBRATE = "vibrate"
        const val EXTRA_MORNING_BRIEF_ENABLED = "morning_brief_enabled"
        const val EXTRA_AUTO_PLAY_BRIEF = "auto_play_brief"
        private const val CHANNEL_ID = "alarm_ringing"
        private const val NOTIFICATION_ID = 201
    }
}
