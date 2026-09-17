package com.example.exambrief.feature.hotspot

import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import com.example.exambrief.core.database.CachedHotspotEntity

@Composable
fun HotspotHomeScreen(
    onOpen: (String) -> Unit,
    viewModel: HotspotViewModel = hiltViewModel(),
) {
    val cached by viewModel.items.collectAsState()
    val loading by viewModel.loading.collectAsState()
    val error by viewModel.error.collectAsState()
    LaunchedEffect(viewModel) { viewModel.refresh() }
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Text("今日热点", style = MaterialTheme.typography.headlineSmall)
                Button(onClick = viewModel::refresh) { Text("刷新") }
            }
            Text(viewModel.day, style = MaterialTheme.typography.bodySmall)
        }
        if (loading) item { CircularProgressIndicator() }
        if (error != null) item { Text(error.orEmpty(), color = MaterialTheme.colorScheme.error) }
        if (!loading && cached.isEmpty()) item { Text("今日暂无热点。联网后可重试。") }
        val core = cached.filter { it.importance == "core" }
        val other = cached.filter { it.importance != "core" }
        if (core.isNotEmpty()) item { Text("今日重点", style = MaterialTheme.typography.titleLarge) }
        items(core, key = { "core:${it.id}" }) { item -> HotspotCard(item, onOpen) }
        if (other.isNotEmpty()) item { Text("其他值得关注", style = MaterialTheme.typography.titleLarge) }
        items(other, key = { "other:${it.id}" }) { item -> HotspotCard(item, onOpen) }
    }
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
