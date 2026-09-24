package com.example.exambrief.feature.briefing

import com.example.exambrief.core.database.CachedBriefingEntity
import com.example.exambrief.core.database.HotspotDao
import com.example.exambrief.core.network.BriefingDto
import com.example.exambrief.core.network.BriefingItemDto
import com.example.exambrief.core.network.HotspotApi
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import javax.inject.Inject
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

data class BriefingContent(
    val date: String,
    val introText: String,
    val items: List<BriefingItemDto>,
    val outroText: String,
    val isFallback: Boolean = false,
) {
    fun speechParts(): List<String> = buildList {
        if (isFallback) add("以下为最近缓存内容。")
        add(introText)
        addAll(items.sortedBy { it.position }.map { it.ttsText })
        add(outroText)
    }.filter { it.isNotBlank() }
}

class BriefingRepository @Inject constructor(
    private val dao: HotspotDao,
    private val api: HotspotApi,
    private val json: Json,
) {
    suspend fun get(day: String, timezone: String): BriefingContent? =
        dao.briefing(day, timezone)?.toContent()

    suspend fun refresh(day: String, timezone: String): BriefingContent? {
        val cached = dao.briefing(day, timezone)
        return try {
            val response = api.briefing(day, timezone, etag = cached?.etag)
            when {
                response.code() == 304 -> cached?.toContent()
                response.code() == 404 -> cached?.toContent()
                !response.isSuccessful -> throw IllegalStateException("HTTP ${response.code()}")
                else -> {
                    val body = response.body()?.string() ?: throw IllegalStateException("响应为空")
                    val dto = json.decodeFromString(BriefingDto.serializer(), body)
                    require(dto.date == day && dto.timezone == timezone) { "晨报日期或时区不一致" }
                    val entity = CachedBriefingEntity(
                        date = dto.date,
                        timezone = dto.timezone,
                        id = dto.id,
                        version = dto.version,
                        generatedAt = dto.generatedAt,
                        expiresAtEpochMillis = Instant.parse(dto.expiresAt).toEpochMilli(),
                        introText = dto.introText,
                        itemsJson = json.encodeToString(dto.items),
                        outroText = dto.outroText,
                        etag = response.headers()["ETag"],
                        cachedAtEpochMillis = System.currentTimeMillis(),
                    )
                    dao.upsertBriefing(entity)
                    entity.toContent()
                }
            }
        } catch (error: Exception) {
            cached?.toContent() ?: throw error
        }
    }

    suspend fun selectForPlayback(
        nowMillis: Long = System.currentTimeMillis(),
        zoneId: ZoneId = ZoneId.systemDefault(),
    ): BriefingContent? {
        val timezone = zoneId.id
        val today = LocalDate.now(zoneId).toString()
        val current = dao.briefing(today, timezone)
        if (current != null && current.expiresAtEpochMillis >= nowMillis) return current.toContent()
        return dao.recentBriefing(timezone, nowMillis - 24 * 60 * 60 * 1000L)
            ?.toContent(isFallback = true)
    }

    private fun CachedBriefingEntity.toContent(isFallback: Boolean = false) = BriefingContent(
        date = date,
        introText = introText,
        items = json.decodeFromString(itemsJson),
        outroText = outroText,
        isFallback = isFallback,
    )
}
