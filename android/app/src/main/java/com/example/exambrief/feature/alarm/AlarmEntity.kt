package com.example.exambrief.feature.alarm

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "alarms")
data class AlarmEntity(
    @PrimaryKey val id: String,
    val hour: Int,
    val minute: Int,
    val repeatDaysMask: Int,
    val oneShotDate: String?,
    val enabled: Boolean,
    val label: String,
    val soundUri: String?,
    val vibrate: Boolean,
    val snoozeMinutes: Int,
    val morningBriefEnabled: Boolean,
    val autoPlayBrief: Boolean,
    val nextTriggerAtEpochMillis: Long?,
    val createdAtEpochMillis: Long,
    val updatedAtEpochMillis: Long,
)
