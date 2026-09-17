package com.example.exambrief.core.database

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import kotlinx.coroutines.flow.Flow

@Dao
abstract class HotspotDao {
    @Query("SELECT * FROM cached_hotspots WHERE date = :date AND timezone = :timezone ORDER BY CASE importance WHEN 'core' THEN 0 ELSE 1 END, publishedAt DESC")
    abstract fun observeByDate(date: String, timezone: String): Flow<List<CachedHotspotEntity>>

    @Query("SELECT * FROM cached_hotspot_details WHERE id = :id")
    abstract suspend fun detail(id: String): CachedHotspotDetailEntity?

    @Query("SELECT * FROM sync_states WHERE resource = :resource")
    abstract suspend fun syncState(resource: String): SyncStateEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    abstract suspend fun upsertHotspots(items: List<CachedHotspotEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    abstract suspend fun upsertDetail(item: CachedHotspotDetailEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    abstract suspend fun upsertSyncState(state: SyncStateEntity)

    @Query("DELETE FROM cached_hotspots WHERE date = :date AND timezone = :timezone AND id NOT IN (:ids)")
    abstract suspend fun removeMissing(date: String, timezone: String, ids: List<String>)

    @Transaction
    open suspend fun replaceDate(
        date: String,
        timezone: String,
        items: List<CachedHotspotEntity>,
        etag: String?,
    ) {
        upsertHotspots(items)
        removeMissing(date, timezone, items.map { it.id })
        upsertSyncState(
            SyncStateEntity("hotspots:$date:$timezone", etag, System.currentTimeMillis(), null)
        )
    }
}
