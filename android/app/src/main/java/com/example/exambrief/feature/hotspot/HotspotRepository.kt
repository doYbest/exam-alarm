package com.example.exambrief.feature.hotspot

import com.example.exambrief.core.database.CachedHotspotDetailEntity
import com.example.exambrief.core.database.CachedHotspotEntity
import com.example.exambrief.core.database.HotspotDao
import com.example.exambrief.core.database.SyncStateEntity
import com.example.exambrief.core.network.HotspotApi
import com.example.exambrief.core.network.HotspotDetailDto
import com.example.exambrief.core.network.HotspotItemDto
import com.example.exambrief.core.network.HotspotListDto
import javax.inject.Inject
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.Flow
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

data class DetailResult(val detail: HotspotDetailDto, val offline: Boolean)

class HotspotRepository @Inject constructor(
    private val dao: HotspotDao,
    private val api: HotspotApi,
    private val json: Json,
) {
    fun observe(day: String, timezone: String): Flow<List<CachedHotspotEntity>> =
        dao.observeByDate(day, timezone)

    suspend fun refresh(day: String, timezone: String) {
        val resource = "hotspots:$day:$timezone"
        val previous = dao.syncState(resource)
        try {
            val first = api.list(day, timezone, etag = previous?.etag)
            if (first.code() == 304) {
                dao.upsertSyncState(
                    SyncStateEntity(resource, previous?.etag, System.currentTimeMillis(), null)
                )
                return
            }
            if (!first.isSuccessful) throw IllegalStateException("HTTP ${first.code()}")
            val firstBody = first.body()?.string() ?: throw IllegalStateException("响应为空")
            val firstPage = json.decodeFromString(HotspotListDto.serializer(), firstBody)
            if (firstPage.date != day) throw IllegalStateException("响应日期不一致")
            val items = firstPage.items.toMutableList()
            var cursor = firstPage.nextCursor
            val seenCursors = mutableSetOf<String>()
            while (cursor != null) {
                if (!seenCursors.add(cursor) || seenCursors.size > 100) {
                    throw IllegalStateException("分页游标重复或过多")
                }
                val response = api.list(day, timezone, cursor = cursor)
                if (!response.isSuccessful) throw IllegalStateException("HTTP ${response.code()}")
                val body = response.body()?.string() ?: throw IllegalStateException("响应为空")
                val page = json.decodeFromString(HotspotListDto.serializer(), body)
                if (page.date != day) throw IllegalStateException("响应日期不一致")
                items.addAll(page.items)
                cursor = page.nextCursor
            }
            val now = System.currentTimeMillis()
            dao.replaceDate(
                day,
                timezone,
                items.distinctBy(HotspotItemDto::id).map { item ->
                    CachedHotspotEntity(
                        id = item.id,
                        date = day,
                        timezone = timezone,
                        title = item.title,
                        summary = item.summary,
                        category = item.category,
                        importance = item.importance,
                        publishedAt = item.publishedAt,
                        sourceNamesJson = json.encodeToString(item.sourceNames),
                        contentVersion = item.contentVersion,
                        cachedAtEpochMillis = now,
                    )
                },
                first.headers()["ETag"],
            )
        } catch (error: Exception) {
            if (error is CancellationException) throw error
            dao.upsertSyncState(
                SyncStateEntity(resource, previous?.etag, previous?.lastSuccessEpochMillis, error.message)
            )
            throw error
        }
    }

    suspend fun detail(id: String): DetailResult? {
        val cached = dao.detail(id)
        try {
            val response = api.detail(id, cached?.etag)
            if (response.code() == 404) return null
            if (response.code() == 304 && cached != null) {
                return DetailResult(json.decodeFromString(HotspotDetailDto.serializer(), cached.json), false)
            }
            if (!response.isSuccessful) throw IllegalStateException("HTTP ${response.code()}")
            val body = response.body()?.string() ?: throw IllegalStateException("响应为空")
            val item = json.decodeFromString(HotspotDetailDto.serializer(), body)
            dao.upsertDetail(
                CachedHotspotDetailEntity(
                    id = id,
                    json = body,
                    contentVersion = item.contentVersion,
                    etag = response.headers()["ETag"],
                    cachedAtEpochMillis = System.currentTimeMillis(),
                )
            )
            return DetailResult(item, false)
        } catch (error: Exception) {
            if (error is CancellationException) throw error
            return cached?.let {
                DetailResult(json.decodeFromString(HotspotDetailDto.serializer(), it.json), true)
            }
        }
    }
}
