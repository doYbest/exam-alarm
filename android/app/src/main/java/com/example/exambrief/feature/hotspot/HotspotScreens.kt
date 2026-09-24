package com.example.exambrief.feature.hotspot

import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import android.content.Context
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import com.example.exambrief.core.database.CachedHotspotEntity
import com.example.exambrief.feature.briefing.BriefingPlaybackService
import java.time.LocalDate
import java.time.YearMonth
import java.time.format.DateTimeFormatter
import java.util.Locale

@Composable
fun HotspotHomeScreen(
    onOpen: (String) -> Unit,
    viewModel: HotspotViewModel = hiltViewModel(),
) {
    val cached by viewModel.items.collectAsState()
    val loading by viewModel.loading.collectAsState()
    val error by viewModel.error.collectAsState()
    val day by viewModel.day.collectAsState()
    val briefing by viewModel.briefing.collectAsState()
    val context = LocalContext.current
    var visibleMonth by androidx.compose.runtime.remember {
        androidx.compose.runtime.mutableStateOf(YearMonth.from(LocalDate.now()))
    }
    LaunchedEffect(viewModel) { viewModel.refresh() }
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Text("公考晨报", style = MaterialTheme.typography.headlineSmall)
                Button(onClick = viewModel::refresh) { Text("刷新") }
            }
        }
        item {
            MonthCalendar(
                month = visibleMonth,
                selected = LocalDate.parse(day),
                onPreviousMonth = { visibleMonth = visibleMonth.minusMonths(1) },
                onNextMonth = {
                    val next = visibleMonth.plusMonths(1)
                    if (!next.isAfter(YearMonth.from(LocalDate.now()))) visibleMonth = next
                },
                onSelect = viewModel::selectDay,
            )
        }
        item {
            val selectedDate = LocalDate.parse(day)
            Text(
                if (selectedDate == LocalDate.now()) "今日推荐" else
                    selectedDate.format(DateTimeFormatter.ofPattern("M月d日", Locale.CHINA)) + "回顾",
                style = MaterialTheme.typography.titleLarge,
            )
            briefing?.let { content ->
                Card(modifier = Modifier.fillMaxWidth().padding(top = 8.dp)) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Text("当日晨报 · ${content.items.size} 条", style = MaterialTheme.typography.titleMedium)
                        Text(content.introText, style = MaterialTheme.typography.bodyMedium)
                        if (selectedDate == LocalDate.now()) {
                            Button(onClick = { context.playBriefing() }) { Text("播放晨报") }
                        }
                    }
                }
            }
        }
        if (loading) item { CircularProgressIndicator() }
        if (error != null) item { Text(error.orEmpty(), color = MaterialTheme.colorScheme.error) }
        if (!loading && cached.isEmpty()) item {
            Text(if (error == null) "所选日期暂无热点" else "暂无缓存内容，请稍后重试")
        }
        val core = cached.filter { it.importance == "core" }
        val other = cached.filter { it.importance != "core" }
        if (core.isNotEmpty()) item { Text("今日重点", style = MaterialTheme.typography.titleLarge) }
        items(core, key = { "core:${it.id}" }) { item -> HotspotCard(item, onOpen) }
        if (other.isNotEmpty()) item { Text("其他值得关注", style = MaterialTheme.typography.titleLarge) }
        items(other, key = { "other:${it.id}" }) { item -> HotspotCard(item, onOpen) }
    }
}

@Composable
private fun MonthCalendar(
    month: YearMonth,
    selected: LocalDate,
    onPreviousMonth: () -> Unit,
    onNextMonth: () -> Unit,
    onSelect: (LocalDate) -> Unit,
) {
    val today = LocalDate.now()
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                OutlinedButton(onClick = onPreviousMonth) { Text("‹") }
                Text(
                    month.atDay(1).format(DateTimeFormatter.ofPattern("yyyy年 M月", Locale.CHINA)),
                    style = MaterialTheme.typography.titleMedium,
                )
                OutlinedButton(
                    onClick = onNextMonth,
                    enabled = month < YearMonth.from(today),
                ) { Text("›") }
            }
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
                listOf("一", "二", "三", "四", "五", "六", "日").forEach {
                    Box(modifier = Modifier.width(40.dp), contentAlignment = Alignment.Center) {
                        Text(it, style = MaterialTheme.typography.labelMedium)
                    }
                }
            }
            val firstOffset = month.atDay(1).dayOfWeek.value - 1
            val cells = firstOffset + month.lengthOfMonth()
            repeat((cells + 6) / 7) { week ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly,
                ) {
                    repeat(7) { weekday ->
                        val dayNumber = week * 7 + weekday - firstOffset + 1
                        if (dayNumber !in 1..month.lengthOfMonth()) {
                            Box(modifier = Modifier.size(40.dp))
                        } else {
                            val date = month.atDay(dayNumber)
                            val enabled = !date.isAfter(today)
                            val chosen = date == selected
                            Box(
                                modifier = Modifier
                                    .size(40.dp)
                                    .clickable(enabled = enabled) { onSelect(date) },
                                contentAlignment = Alignment.Center,
                            ) {
                                Text(
                                    dayNumber.toString(),
                                    color = when {
                                        chosen -> MaterialTheme.colorScheme.primary
                                        enabled -> MaterialTheme.colorScheme.onSurface
                                        else -> MaterialTheme.colorScheme.onSurface.copy(alpha = 0.35f)
                                    },
                                    style = if (chosen) MaterialTheme.typography.titleMedium
                                        else MaterialTheme.typography.bodyMedium,
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

private fun Context.playBriefing() {
    startForegroundService(
        Intent(this, BriefingPlaybackService::class.java)
            .setAction(BriefingPlaybackService.ACTION_PLAY)
    )
}

@Composable
private fun HotspotCard(item: CachedHotspotEntity, onOpen: (String) -> Unit) {
    Card(modifier = Modifier.fillMaxWidth().clickable { onOpen(item.id) }) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(item.title, style = MaterialTheme.typography.titleMedium)
            Text(item.summary, style = MaterialTheme.typography.bodyMedium)
            Text(item.category, style = MaterialTheme.typography.labelMedium)
        }
    }
}

@Composable
fun HotspotDetailScreen(
    id: String,
    viewModel: HotspotViewModel = hiltViewModel(),
) {
    val context = LocalContext.current
    val detail by viewModel.detail.collectAsState()
    val loading by viewModel.detailLoading.collectAsState()
    val error by viewModel.detailError.collectAsState()
    LaunchedEffect(id) { viewModel.openDetail(id) }
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        if (loading) item { CircularProgressIndicator() }
        if (error != null) item { Text(error.orEmpty(), color = MaterialTheme.colorScheme.error) }
        detail?.let { result ->
            val detailDto = result.detail
            if (result.offline) item { Text("离线内容，可能不是最新版本") }
            item { Text(detailDto.title, style = MaterialTheme.typography.headlineSmall) }
            item { Text(detailDto.summary) }
            item { Text("背景与变化", style = MaterialTheme.typography.titleMedium) }
            item { Text(detailDto.deepAnalysis.background) }
            item { Text(detailDto.deepAnalysis.whatChanged) }
            item { Text("为什么值得关注", style = MaterialTheme.typography.titleMedium) }
            item { Text(detailDto.deepAnalysis.whyItMatters) }
            item { Text(detailDto.deepAnalysis.examRelevance) }
            if (detailDto.deepAnalysis.possibleAngles.isNotEmpty()) {
                item { Text("可能考法：${detailDto.deepAnalysis.possibleAngles.joinToString("、")}") }
            }
            item { Text("原始来源", style = MaterialTheme.typography.titleMedium) }
            items(detailDto.sources, key = { it.url }) { source ->
                Button(onClick = {
                    try {
                        context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(source.url)))
                    } catch (_: ActivityNotFoundException) {
                        // No browser is available on this device.
                    }
                }) { Text("${source.name} · 查看原文") }
            }
        }
    }
}
