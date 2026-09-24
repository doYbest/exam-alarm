package com.example.exambrief.feature.briefing

import com.example.exambrief.core.network.BriefingItemDto
import org.junit.Assert.assertEquals
import org.junit.Test

class BriefingContentTest {
    private val items = listOf(
        BriefingItemDto(2, "b", "第二条", "第二条内容。", 4),
        BriefingItemDto(1, "a", "第一条", "第一条内容。", 4),
    )

    @Test
    fun speechParts_ordersItemsBetweenIntroAndOutro() {
        val content = BriefingContent("2026-09-24", "早上好。", items, "播报结束。")

        assertEquals(
            listOf("早上好。", "第一条内容。", "第二条内容。", "播报结束。"),
            content.speechParts(),
        )
    }

    @Test
    fun speechParts_announcesFallbackCache() {
        val content = BriefingContent(
            "2026-09-23", "早上好。", items.take(1), "播报结束。", isFallback = true
        )

        assertEquals("以下为最近缓存内容。", content.speechParts().first())
    }
}
