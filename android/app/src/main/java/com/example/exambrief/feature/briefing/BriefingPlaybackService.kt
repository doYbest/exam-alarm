package com.example.exambrief.feature.briefing

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.os.IBinder
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import dagger.hilt.android.AndroidEntryPoint
import java.util.Locale
import javax.inject.Inject
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch

@AndroidEntryPoint
class BriefingPlaybackService : Service(), TextToSpeech.OnInitListener {
    @Inject lateinit var repository: BriefingRepository

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var tts: TextToSpeech? = null
    private var parts: List<String> = emptyList()
    private var currentIndex = 0
    private var initialized = false
    private var paused = false
    private var audioFocusRequest: AudioFocusRequest? = null

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        createChannel()
        tts = TextToSpeech(this, this)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_STOP -> stopPlayback()
            ACTION_PAUSE -> pausePlayback()
            ACTION_RESUME -> resumePlayback()
            ACTION_PLAY -> {
                startForeground(NOTIFICATION_ID, notification("正在准备晨报…", false))
                scope.launch {
                    val content = repository.selectForPlayback()
                    parts = content?.speechParts() ?: listOf("今日晨报暂未准备好。")
                    currentIndex = 0
                    paused = false
                    if (initialized) speakCurrent()
                }
            }
            else -> stopSelf(startId)
        }
        return START_NOT_STICKY
    }

    override fun onInit(status: Int) {
        if (status != TextToSpeech.SUCCESS) {
            showError("系统语音引擎不可用")
            return
        }
        val engine = tts ?: return
        val language = engine.setLanguage(Locale.SIMPLIFIED_CHINESE)
        if (language == TextToSpeech.LANG_MISSING_DATA || language == TextToSpeech.LANG_NOT_SUPPORTED) {
            showError("请安装系统中文语音数据")
            return
        }
        engine.setSpeechRate(1.0f)
        engine.setAudioAttributes(
            AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_ASSISTANCE_ACCESSIBILITY)
                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                .build()
        )
        engine.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
            override fun onStart(utteranceId: String?) = Unit
            override fun onError(utteranceId: String?) = advance(utteranceId)
            override fun onDone(utteranceId: String?) = advance(utteranceId)
        })
        initialized = true
        if (parts.isNotEmpty() && !paused) speakCurrent()
    }

    private fun advance(utteranceId: String?) {
        val finishedIndex = utteranceId?.substringAfterLast('-')?.toIntOrNull() ?: return
        if (finishedIndex != currentIndex || paused) return
        currentIndex++
        if (currentIndex >= parts.size) stopPlayback() else speakCurrent()
    }

    private fun speakCurrent() {
        if (!initialized || paused || currentIndex !in parts.indices) return
        requestAudioFocus()
        val title = if (currentIndex == 0) "正在播报晨报" else "晨报 ${currentIndex + 1}/${parts.size}"
        getSystemService(NotificationManager::class.java).notify(
            NOTIFICATION_ID, notification(title, true)
        )
        tts?.speak(parts[currentIndex], TextToSpeech.QUEUE_FLUSH, null, "briefing-$currentIndex")
    }

    private fun pausePlayback() {
        if (!initialized || currentIndex !in parts.indices) return
        paused = true
        tts?.stop()
        getSystemService(NotificationManager::class.java).notify(
            NOTIFICATION_ID, notification("晨报已暂停", false)
        )
    }

    private fun resumePlayback() {
        if (!paused) return
        paused = false
        speakCurrent()
    }

    private fun requestAudioFocus() {
        val manager = getSystemService(AudioManager::class.java)
        if (audioFocusRequest != null) return
        val request = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ASSISTANCE_ACCESSIBILITY)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                    .build()
            )
            .setOnAudioFocusChangeListener { change ->
                if (change == AudioManager.AUDIOFOCUS_LOSS ||
                    change == AudioManager.AUDIOFOCUS_LOSS_TRANSIENT
                ) pausePlayback()
            }
            .build()
        audioFocusRequest = request
        manager.requestAudioFocus(request)
    }

    private fun abandonAudioFocus() {
        val request = audioFocusRequest ?: return
        getSystemService(AudioManager::class.java).abandonAudioFocusRequest(request)
        audioFocusRequest = null
    }

    private fun showError(message: String) {
        getSystemService(NotificationManager::class.java).notify(
            NOTIFICATION_ID, notification(message, false, canResume = false)
        )
    }

    private fun notification(
        text: String,
        playing: Boolean,
        canResume: Boolean = true,
    ): Notification {
        val builder = Notification.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .setContentTitle("公考晨报")
            .setContentText(text)
            .setOngoing(playing)
            .addAction(0, "停止", actionIntent(ACTION_STOP, 1))
        if (playing) builder.addAction(0, "暂停", actionIntent(ACTION_PAUSE, 2))
        else if (canResume) builder.addAction(0, "继续", actionIntent(ACTION_RESUME, 3))
        return builder.build()
    }

    private fun actionIntent(actionName: String, requestCode: Int): PendingIntent =
        PendingIntent.getService(
            this,
            requestCode,
            Intent(this, BriefingPlaybackService::class.java).setAction(actionName),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )

    private fun createChannel() {
        getSystemService(NotificationManager::class.java).createNotificationChannel(
            NotificationChannel(CHANNEL_ID, "晨报播报", NotificationManager.IMPORTANCE_LOW)
        )
    }

    private fun stopPlayback() {
        tts?.stop()
        abandonAudioFocus()
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    override fun onDestroy() {
        tts?.stop()
        tts?.shutdown()
        abandonAudioFocus()
        scope.cancel()
        super.onDestroy()
    }

    companion object {
        const val ACTION_PLAY = "com.example.exambrief.briefing.PLAY"
        const val ACTION_PAUSE = "com.example.exambrief.briefing.PAUSE"
        const val ACTION_RESUME = "com.example.exambrief.briefing.RESUME"
        const val ACTION_STOP = "com.example.exambrief.briefing.STOP"
        private const val CHANNEL_ID = "briefing_playback"
        private const val NOTIFICATION_ID = 301
    }
}
