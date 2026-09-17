package com.example.exambrief.feature.alarm

import java.time.DayOfWeek
import java.time.Instant
import java.time.LocalDate
import java.time.LocalTime
import java.time.ZoneId

object AlarmTime {
    fun days(mask: Int): Set<DayOfWeek> = DayOfWeek.values().filterTo(mutableSetOf()) {
        mask and (1 shl (it.value - 1)) != 0
    }

    fun mask(days: Set<DayOfWeek>): Int = days.fold(0) { value, day ->
        value or (1 shl (day.value - 1))
    }

    fun nextTrigger(alarm: AlarmEntity, after: Instant, zone: ZoneId): Instant? {
        if (!alarm.enabled) return null
        require(alarm.hour in 0..23 && alarm.minute in 0..59)
        require(alarm.repeatDaysMask in 0..127)
        val time = LocalTime.of(alarm.hour, alarm.minute)
        if (alarm.repeatDaysMask == 0) {
            val date = alarm.oneShotDate?.let { LocalDate.parse(it) } ?: return null
            return date.atTime(time).atZone(zone).toInstant().takeIf { it.isAfter(after) }
        }
        val start = after.atZone(zone).toLocalDate()
        for (offset in 0..7) {
            val date = start.plusDays(offset.toLong())
            if (date.dayOfWeek !in days(alarm.repeatDaysMask)) continue
            val candidate = date.atTime(time).atZone(zone).toInstant()
            if (candidate.isAfter(after)) return candidate
        }
        return null
    }
}
