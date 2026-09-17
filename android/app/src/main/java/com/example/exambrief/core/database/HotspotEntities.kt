package com.example.exambrief.core.database

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "cached_hotspots", primaryKeys = ["date", "timezone", "id"])
data class CachedHotspotEntity(
    val id: String,
    val date: String,
    val timezone: String,
    val title: String,
    val summary: String,
    val category: String,
    val importance: String,
    val publishedAt: String,
    val sourceNamesJson: String,
    val contentVersion: Int,
    val cachedAtEpochMillis: Long,
)

@Entity(tableName = "cached_hotspot_details")
data class CachedHotspotDetailEntity(
    @PrimaryKey val id: String,
    val json: String,
    val contentVersion: Int,
    val etag: String?,
    val cachedAtEpochMillis: Long,
)

@Entity(tableName = "sync_states")
data class SyncStateEntity(
    @PrimaryKey val resource: String,
    val etag: String?,
    val lastSuccessEpochMillis: Long?,
    val lastError: String?,
)
