package com.example.exambrief.core.network

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class HotspotListDto(
    val date: String,
    val items: List<HotspotItemDto>,
    @SerialName("next_cursor") val nextCursor: String? = null,
)

@Serializable
data class HotspotItemDto(
    val id: String,
    val title: String,
    val summary: String,
    val category: String,
    val subcategories: List<String> = emptyList(),
    @SerialName("exam_types") val examTypes: List<String> = emptyList(),
    val importance: String,
    @SerialName("published_at") val publishedAt: String,
    @SerialName("source_names") val sourceNames: List<String> = emptyList(),
    @SerialName("content_version") val contentVersion: Int,
)

@Serializable
data class SourceDto(
    val name: String,
    val url: String,
    @SerialName("published_at") val publishedAt: String? = null,
)

@Serializable
data class DeepAnalysisDto(
    val background: String,
    @SerialName("what_changed") val whatChanged: String,
    @SerialName("why_it_matters") val whyItMatters: String,
    @SerialName("exam_relevance") val examRelevance: String,
    @SerialName("possible_angles") val possibleAngles: List<String> = emptyList(),
)

@Serializable
data class HotspotDetailDto(
    val id: String,
    val title: String,
    val category: String,
    val subcategories: List<String> = emptyList(),
    @SerialName("exam_types") val examTypes: List<String> = emptyList(),
    val importance: String,
    val brief: String,
    val summary: String,
    @SerialName("deep_analysis") val deepAnalysis: DeepAnalysisDto,
    @SerialName("key_points") val keyPoints: List<String> = emptyList(),
    @SerialName("knowledge_refs") val knowledgeRefs: List<String> = emptyList(),
    @SerialName("evidence_refs") val evidenceRefs: List<String> = emptyList(),
    @SerialName("insufficient_evidence") val insufficientEvidence: Boolean = false,
    @SerialName("content_version") val contentVersion: Int,
    val sources: List<SourceDto> = emptyList(),
)

@Serializable
data class BriefingItemDto(
    val position: Int,
    @SerialName("hotspot_id") val hotspotId: String,
    val title: String,
    @SerialName("tts_text") val ttsText: String,
    @SerialName("estimated_seconds") val estimatedSeconds: Int,
)

@Serializable
data class BriefingDto(
    val id: String,
    val date: String,
    val timezone: String,
    val version: Int,
    @SerialName("generated_at") val generatedAt: String,
    @SerialName("expires_at") val expiresAt: String,
    @SerialName("intro_text") val introText: String,
    val items: List<BriefingItemDto>,
    @SerialName("outro_text") val outroText: String,
)
