package com.example.exambrief.feature.hotspot

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.exambrief.core.database.CachedHotspotEntity
import com.example.exambrief.feature.briefing.BriefingContent
import com.example.exambrief.feature.briefing.BriefingRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import java.time.LocalDate
import java.time.ZoneId
import javax.inject.Inject
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

@HiltViewModel
@OptIn(ExperimentalCoroutinesApi::class)
class HotspotViewModel @Inject constructor(
    private val repository: HotspotRepository,
    private val briefingRepository: BriefingRepository,
) : ViewModel() {
    private val today = LocalDate.now().toString()
    val day = MutableStateFlow(today)
    val timezone: String = ZoneId.systemDefault().id
    val items: StateFlow<List<CachedHotspotEntity>> = day.flatMapLatest { selectedDay ->
        repository.observe(selectedDay, timezone)
    }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    val loading = MutableStateFlow(false)
    val error = MutableStateFlow<String?>(null)
    val detail = MutableStateFlow<DetailResult?>(null)
    val detailLoading = MutableStateFlow(false)
    val detailError = MutableStateFlow<String?>(null)
    val briefing = MutableStateFlow<BriefingContent?>(null)

    fun selectDay(selected: LocalDate) {
        if (selected.isAfter(LocalDate.now())) return
        day.value = selected.toString()
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            val selectedDay = day.value
            loading.value = true
            error.value = null
            try {
                repository.refresh(selectedDay, timezone)
            } catch (cause: Exception) {
                if (cause is CancellationException) throw cause
                error.value = "同步失败，正在显示已缓存内容"
            } finally {
                loading.value = false
            }
            val selectedBriefing = try {
                briefingRepository.refresh(selectedDay, timezone)
            } catch (cause: Exception) {
                if (cause is CancellationException) throw cause
                briefingRepository.get(selectedDay, timezone)
            }
            if (day.value == selectedDay) briefing.value = selectedBriefing
        }
    }

    fun openDetail(id: String) {
        viewModelScope.launch {
            detailLoading.value = true
            detailError.value = null
            detail.value = null
            try {
                detail.value = repository.detail(id)
                if (detail.value == null) detailError.value = "热点不存在或尚未缓存"
            } catch (cause: Exception) {
                if (cause is CancellationException) throw cause
                detailError.value = "热点详情暂时不可用"
            } finally {
                detailLoading.value = false
            }
        }
    }
}
