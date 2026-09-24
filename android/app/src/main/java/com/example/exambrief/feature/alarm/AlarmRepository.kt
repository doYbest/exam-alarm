package com.example.exambrief.feature.alarm

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import com.example.exambrief.MainActivity
import dagger.hilt.android.qualifiers.ApplicationContext
import java.time.Instant
import java.time.LocalDate
import java.time.LocalTime
import java.time.ZoneId
import java.util.UUID
import javax.inject.Inject
import kotlinx.coroutines.flow.Flow

class AlarmRepository @Inject constructor(
    private val dao: AlarmDao,
    @ApplicationContext private val context: Context,
) {
    private val manager: AlarmManager
        get() = context.getSystemService(AlarmManager::class.java)

    fun observeAll(): Flow<List<AlarmEntity>> = dao.observeAll()

    fun canSchedule(): Boolean =
        Build.VERSION.SDK_INT < 31 || manager.canScheduleExactAlarms()

    suspend fun save(
        existing: AlarmEntity?,
        hour: Int,
        minute: Int,
        repeatDaysMask: Int,
        label: String,
        vibrate: Boolean,
        snoozeMinutes: Int,
    ): Boolean {
        require(hour in 0..23 && minute in 0..59)
        val now = System.currentTimeMillis()
        val alarm = AlarmEntity(
            id = existing?.id ?: UUID.randomUUID().toString(),
            hour = hour,
            minute = minute,
            repeatDaysMask = repeatDaysMask,
            oneShotDate = if (repeatDaysMask == 0) upcomingDate(hour, minute) else null,
            enabled = true,
            label = label.trim().ifEmpty { "闹钟" },
            soundUri = existing?.soundUri,
            vibrate = vibrate,
            snoozeMinutes = snoozeMinutes.coerceIn(1, 30),
            morningBriefEnabled = existing?.morningBriefEnabled ?: false,
            autoPlayBrief = existing?.autoPlayBrief ?: false,
            nextTriggerAtEpochMillis = null,
            createdAtEpochMillis = existing?.createdAtEpochMillis ?: now,
            updatedAtEpochMillis = now,
        )
        dao.upsert(alarm)
        return schedule(alarm)
    }

    suspend fun setEnabled(alarm: AlarmEntity, enabled: Boolean): Boolean {
        val updated = alarm.copy(
            enabled = enabled,
            oneShotDate = if (enabled && alarm.repeatDaysMask == 0) {
                upcomingDate(alarm.hour, alarm.minute)
            } else alarm.oneShotDate,
            updatedAtEpochMillis = System.currentTimeMillis(),
        )
        dao.upsert(updated)
        if (!enabled) cancelSnooze(alarm.id)
        return schedule(updated)
    }

    suspend fun delete(alarm: AlarmEntity) {
        cancel(alarm.id, false)
        cancelSnooze(alarm.id)
        dao.delete(alarm.id)
    }

    suspend fun rescheduleAll() {
        dao.enabled().forEach { schedule(it) }
    }

    suspend fun onFire(id: String, snoozed: Boolean): AlarmEntity? {
        val alarm = dao.find(id) ?: return null
        if (!alarm.enabled && !snoozed) return null
        if (!snoozed) {
            if (alarm.repeatDaysMask == 0) {
                dao.setSchedule(id, null, false, System.currentTimeMillis())
            } else {
                schedule(alarm)
            }
        }
        return alarm
    }

    suspend fun snooze(id: String) {
        val alarm = dao.find(id) ?: return
        if (!canSchedule()) return
        register(id, System.currentTimeMillis() + alarm.snoozeMinutes * 60_000L, true)
    }

    private suspend fun schedule(alarm: AlarmEntity): Boolean {
        cancel(alarm.id, false)
        val next = AlarmTime.nextTrigger(alarm, Instant.now(), ZoneId.systemDefault())
        if (next == null || !canSchedule()) {
            dao.setSchedule(alarm.id, null, alarm.enabled && next != null, System.currentTimeMillis())
            return next == null || !alarm.enabled
        }
        return try {
            register(alarm.id, next.toEpochMilli(), false)
            dao.setSchedule(alarm.id, next.toEpochMilli(), true, System.currentTimeMillis())
            true
        } catch (_: SecurityException) {
            dao.setSchedule(alarm.id, null, true, System.currentTimeMillis())
            false
        }
    }

    private fun register(id: String, at: Long, snoozed: Boolean) {
        val show = PendingIntent.getActivity(
            context, 0,
            Intent(context, MainActivity::class.java).apply {
                data = Uri.parse("exambrief://alarm/show/$id")
                putExtra(EXTRA_ALARM_ID, id)
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        manager.setAlarmClock(AlarmManager.AlarmClockInfo(at, show), fireIntent(id, snoozed))
    }

    private fun cancel(id: String, snoozed: Boolean) {
        val pending = PendingIntent.getBroadcast(
            context, 0, fireReceiverIntent(id, snoozed),
            PendingIntent.FLAG_NO_CREATE or PendingIntent.FLAG_IMMUTABLE,
        ) ?: return
        manager.cancel(pending)
        pending.cancel()
    }

    private fun cancelSnooze(id: String) = cancel(id, true)

    private fun fireIntent(id: String, snoozed: Boolean): PendingIntent = PendingIntent.getBroadcast(
        context, 0, fireReceiverIntent(id, snoozed),
        PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
    )

    private fun fireReceiverIntent(id: String, snoozed: Boolean) =
        Intent(context, AlarmReceiver::class.java).apply {
            action = ACTION_FIRE
            data = Uri.parse("exambrief://alarm/${if (snoozed) "snooze" else "regular"}/$id")
            putExtra(EXTRA_ALARM_ID, id)
            putExtra(EXTRA_SNOOZED, snoozed)
        }

    private fun upcomingDate(hour: Int, minute: Int): String {
        val now = java.time.ZonedDateTime.now()
        val today = LocalDate.now()
        return (if (LocalTime.of(hour, minute).isAfter(now.toLocalTime())) today else today.plusDays(1))
            .toString()
    }

    companion object {
        const val ACTION_FIRE = "com.example.exambrief.alarm.FIRE"
        const val EXTRA_ALARM_ID = "alarm_id"
        const val EXTRA_SNOOZED = "snoozed"
    }
}
