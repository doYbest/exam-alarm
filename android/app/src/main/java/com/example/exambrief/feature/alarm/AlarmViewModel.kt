package com.example.exambrief.feature.alarm

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

@HiltViewModel
class AlarmViewModel @Inject constructor(
    private val repository: AlarmRepository,
) : ViewModel() {
    val alarms = repository.observeAll()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())
    val canSchedule = MutableStateFlow(repository.canSchedule())
    val message = MutableStateFlow<String?>(null)

    fun save(
        existing: AlarmEntity?, hour: Int, minute: Int, repeatDaysMask: Int,
        label: String, vibrate: Boolean, snoozeMinutes: Int,
        morningBriefEnabled: Boolean, autoPlayBrief: Boolean,
    ) = viewModelScope.launch {
        val scheduled = repository.save(
            existing, hour, minute, repeatDaysMask, label, vibrate, snoozeMinutes,
            morningBriefEnabled, autoPlayBrief,
        )
        message.value = if (scheduled) "闹钟已保存" else "闹钟已保存，请授权精确闹钟后点击刷新权限"
        canSchedule.value = repository.canSchedule()
    }

    fun setEnabled(alarm: AlarmEntity, enabled: Boolean) = viewModelScope.launch {
        val scheduled = repository.setEnabled(alarm, enabled)
        message.value = if (!enabled || scheduled) null else "请授权精确闹钟后点击刷新权限"
    }

    fun delete(alarm: AlarmEntity) = viewModelScope.launch {
        repository.delete(alarm)
        message.value = "闹钟已删除"
    }

    fun refreshPermission() = viewModelScope.launch {
        canSchedule.value = repository.canSchedule()
        if (canSchedule.value) {
            repository.rescheduleAll()
            message.value = "已重新安排闹钟"
        }
    }
}
