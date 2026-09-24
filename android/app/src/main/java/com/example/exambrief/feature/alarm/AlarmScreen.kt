package com.example.exambrief.feature.alarm

import android.Manifest
import android.app.NotificationManager
import android.app.TimePickerDialog
import android.content.Intent
import android.os.Build
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

@Composable
fun AlarmScreen(viewModel: AlarmViewModel = hiltViewModel()) {
    val context = LocalContext.current
    val alarms by viewModel.alarms.collectAsState()
    val canSchedule by viewModel.canSchedule.collectAsState()
    val message by viewModel.message.collectAsState()
    var editing by remember { mutableStateOf<AlarmEntity?>(null) }
    var showEditor by remember { mutableStateOf(false) }
    val notificationPermission = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { }
    LazyColumn(
        modifier = Modifier.padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item { Text("闹钟", style = MaterialTheme.typography.headlineMedium) }
        item {
            Button(onClick = { editing = null; showEditor = true }) { Text("添加闹钟") }
        }
        if (!canSchedule) item {
            Text("需要精确闹钟权限才能按时响铃。")
            Button(onClick = {
                context.startActivity(Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM).apply {
                    data = android.net.Uri.parse("package:${context.packageName}")
                })
            }) { Text("授权精确闹钟") }
            OutlinedButton(onClick = { viewModel.refreshPermission() }) { Text("授权后刷新") }
        }
        if (Build.VERSION.SDK_INT >= 33 &&
            context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) !=
            android.content.pm.PackageManager.PERMISSION_GRANTED
        ) item {
            Text("允许通知后，响铃时才能显示操作按钮。")
            Button(onClick = { notificationPermission.launch(Manifest.permission.POST_NOTIFICATIONS) }) {
                Text("允许通知")
            }
        }
        if (Build.VERSION.SDK_INT >= 34 &&
            !context.getSystemService(NotificationManager::class.java).canUseFullScreenIntent()
        ) item {
            Text("未允许全屏响铃时，请从通知打开响铃界面。")
            Button(onClick = {
                context.startActivity(Intent(Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT).apply {
                    data = android.net.Uri.parse("package:${context.packageName}")
                })
            }) { Text("允许全屏响铃") }
        }
        if (message != null) item { Text(message.orEmpty()) }
        if (alarms.isEmpty()) item { Text("还没有闹钟") }
        items(alarms, key = { it.id }) { alarm ->
            Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("%02d:%02d".format(alarm.hour, alarm.minute),
                        style = MaterialTheme.typography.headlineSmall)
                    Switch(checked = alarm.enabled, onCheckedChange = { viewModel.setEnabled(alarm, it) })
                }
                Text(alarm.label)
                Text(if (alarm.repeatDaysMask == 0) "单次" else "每周 ${repeatLabel(alarm.repeatDaysMask)}")
                alarm.nextTriggerAtEpochMillis?.let {
                    Text("下次响铃：${Instant.ofEpochMilli(it).atZone(ZoneId.systemDefault()).format(
                        DateTimeFormatter.ofPattern("M月d日 HH:mm")
                    )}")
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(onClick = { editing = alarm; showEditor = true }) { Text("编辑") }
                    OutlinedButton(onClick = { viewModel.delete(alarm) }) { Text("删除") }
                }
            }
        }
    }
    if (showEditor) AlarmEditor(
        initial = editing,
        onDismiss = { showEditor = false },
        onSave = { hour, minute, mask, label, vibrate, snooze, brief, autoPlay ->
            viewModel.save(editing, hour, minute, mask, label, vibrate, snooze, brief, autoPlay)
            showEditor = false
        },
    )
}

@Composable
private fun AlarmEditor(
    initial: AlarmEntity?,
    onDismiss: () -> Unit,
    onSave: (Int, Int, Int, String, Boolean, Int, Boolean, Boolean) -> Unit,
) {
    val context = LocalContext.current
    val now = java.time.LocalTime.now()
    var hour by remember(initial) { mutableIntStateOf(initial?.hour ?: now.hour) }
    var minute by remember(initial) { mutableIntStateOf(initial?.minute ?: now.minute) }
    var mask by remember(initial) { mutableIntStateOf(initial?.repeatDaysMask ?: 0) }
    var label by remember(initial) { mutableStateOf(initial?.label.orEmpty()) }
    var vibrate by remember(initial) { mutableStateOf(initial?.vibrate ?: true) }
    var snooze by remember(initial) { mutableIntStateOf(initial?.snoozeMinutes ?: 5) }
    var morningBrief by remember(initial) { mutableStateOf(initial?.morningBriefEnabled ?: true) }
    var autoPlay by remember(initial) { mutableStateOf(initial?.autoPlayBrief ?: true) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (initial == null) "添加闹钟" else "编辑闹钟") },
        text = {
            Column(
                modifier = Modifier.heightIn(max = 520.dp).verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Button(onClick = {
                    TimePickerDialog(context, { _, h, m -> hour = h; minute = m }, hour, minute, true).show()
                }) { Text("时间：%02d:%02d".format(hour, minute)) }
                OutlinedTextField(value = label, onValueChange = { label = it }, label = { Text("名称") })
                Text("重复：不选星期为单次")
                val names = listOf("一", "二", "三", "四", "五", "六", "日")
                for (row in 0..1) {
                    Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                        val range = if (row == 0) 0..3 else 4..6
                        for (index in range) {
                            val bit = 1 shl index
                            FilterChip(
                                selected = mask and bit != 0,
                                onClick = { mask = mask xor bit },
                                label = { Text(names[index]) },
                            )
                        }
                    }
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("震动")
                    Switch(checked = vibrate, onCheckedChange = { vibrate = it })
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("响铃后播放晨报")
                    Switch(
                        checked = morningBrief,
                        onCheckedChange = {
                            morningBrief = it
                            if (!it) autoPlay = false
                        },
                    )
                }
                if (morningBrief) {
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("停止闹钟后自动播放")
                        Switch(checked = autoPlay, onCheckedChange = { autoPlay = it })
                    }
                }
                Text("稍后提醒")
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf(5, 10, 15).forEach { minutes ->
                        FilterChip(
                            selected = snooze == minutes,
                            onClick = { snooze = minutes },
                            label = { Text("${minutes}分钟") },
                        )
                    }
                }
            }
        },
        confirmButton = {
            Button(onClick = {
                onSave(hour, minute, mask, label, vibrate, snooze, morningBrief, autoPlay)
            }) {
                Text("保存")
            }
        },
        dismissButton = { OutlinedButton(onClick = onDismiss) { Text("取消") } },
    )
}

private fun repeatLabel(mask: Int): String = listOf("周一", "周二", "周三", "周四", "周五", "周六", "周日")
    .filterIndexed { index, _ -> mask and (1 shl index) != 0 }
    .joinToString("、")
