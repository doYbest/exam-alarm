package com.example.exambrief.feature.alarm

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface AlarmDao {
    @Query("SELECT * FROM alarms ORDER BY hour, minute, id")
    fun observeAll(): Flow<List<AlarmEntity>>

    @Query("SELECT * FROM alarms WHERE enabled = 1")
    suspend fun enabled(): List<AlarmEntity>

    @Query("SELECT * FROM alarms WHERE id = :id")
    suspend fun find(id: String): AlarmEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(alarm: AlarmEntity)

    @Query("UPDATE alarms SET nextTriggerAtEpochMillis = :next, enabled = :enabled, updatedAtEpochMillis = :updated WHERE id = :id")
    suspend fun setSchedule(id: String, next: Long?, enabled: Boolean, updated: Long)

    @Query("DELETE FROM alarms WHERE id = :id")
    suspend fun delete(id: String)
}
