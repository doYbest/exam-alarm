package com.example.exambrief.feature.alarm

import java.time.DayOfWeek
import java.time.Instant
import java.time.ZoneId
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class AlarmTimeTest {
    private fun alarm(
        repeatDaysMask: Int,
        oneShotDate: String? = null,
        hour: Int = 7,
        minute: Int = 0,
    ) = AlarmEntity(
        id = "test",
        hour = hour,
        minute = minute,
        repeatDaysMask = repeatDaysMask,
        oneShotDate = oneShotDate,
        enabled = true,
        label = "",
        soundUri = null,
        vibrate = false,
        snoozeMinutes = 5,
        morningBriefEnabled = false,
        autoPlayBrief = false,
        nextTriggerAtEpochMillis = null,
        createdAtEpochMillis = 0,
        updatedAtEpochMillis = 0,
    )

    @Test
    fun repeatedAlarmSkipsPastOccurrenceAndCrossesWeek() {
        val monday = AlarmTime.mask(setOf(DayOfWeek.MONDAY))
        val next = AlarmTime.nextTrigger(
            alarm(monday),
            Instant.parse("2026-09-21T00:00:00Z"),
            ZoneId.of("Asia/Shanghai"),
        )
        assertEquals(Instant.parse("2026-09-27T23:00:00Z"), next)
        assertEquals(setOf(DayOfWeek.MONDAY), AlarmTime.days(monday))
    }

    @Test
    fun oneShotAlarmDoesNotRollToNextDay() {
        val once = alarm(0, oneShotDate = "2026-09-21")
        val zone = ZoneId.of("Asia/Shanghai")
        assertEquals(
            Instant.parse("2026-09-20T23:00:00Z"),
            AlarmTime.nextTrigger(once, Instant.parse("2026-09-20T22:00:00Z"), zone),
        )
        assertNull(AlarmTime.nextTrigger(once, Instant.parse("2026-09-20T23:00:00Z"), zone))
    }

    @Test
    fun springDstGapMovesToNextValidLocalTime() {
        val sunday = AlarmTime.mask(setOf(DayOfWeek.SUNDAY))
        val next = AlarmTime.nextTrigger(
            alarm(sunday, hour = 2, minute = 30),
            Instant.parse("2026-03-08T05:00:00Z"),
            ZoneId.of("America/New_York"),
        )
        assertEquals(Instant.parse("2026-03-08T07:30:00Z"), next)
    }
}
