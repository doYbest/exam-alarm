package com.example.exambrief.feature.alarm

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

@AndroidEntryPoint
class AlarmReceiver : BroadcastReceiver() {
    @Inject lateinit var repository: AlarmRepository

    override fun onReceive(context: Context, intent: Intent) {
        val pending = goAsync()
        CoroutineScope(Dispatchers.IO).launch {
            try {
                if (intent.action == AlarmRepository.ACTION_FIRE) {
                    val id = intent.getStringExtra(AlarmRepository.EXTRA_ALARM_ID)
                    val alarm = id?.let {
                        repository.onFire(it, intent.getBooleanExtra(AlarmRepository.EXTRA_SNOOZED, false))
                    }
                    if (alarm != null) {
                        context.startForegroundService(
                            Intent(context, AlarmRingingService::class.java).apply {
                                action = AlarmRingingService.ACTION_RING
                                putExtra(AlarmRepository.EXTRA_ALARM_ID, alarm.id)
                                putExtra(AlarmRingingService.EXTRA_LABEL, alarm.label)
                                putExtra(AlarmRingingService.EXTRA_VIBRATE, alarm.vibrate)
                            }
                        )
                    }
                } else {
                    repository.rescheduleAll()
                }
            } catch (error: Exception) {
                Log.e("AlarmReceiver", "Unable to handle alarm event", error)
            } finally {
                pending.finish()
            }
        }
    }
}
