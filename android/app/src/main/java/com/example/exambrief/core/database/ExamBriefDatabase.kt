package com.example.exambrief.core.database

import androidx.room.Database
import androidx.room.RoomDatabase
import com.example.exambrief.feature.alarm.AlarmDao
import com.example.exambrief.feature.alarm.AlarmEntity

@Database(
    entities = [CachedHotspotEntity::class, CachedHotspotDetailEntity::class, SyncStateEntity::class, AlarmEntity::class],
    version = 2,
    exportSchema = true,
)
abstract class ExamBriefDatabase : RoomDatabase() {
    abstract fun hotspotDao(): HotspotDao
    abstract fun alarmDao(): AlarmDao
}
