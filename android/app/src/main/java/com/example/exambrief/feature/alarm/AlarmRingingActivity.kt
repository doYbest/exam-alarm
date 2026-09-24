package com.example.exambrief.feature.alarm

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

class AlarmRingingActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setShowWhenLocked(true)
        setTurnScreenOn(true)
        val id = intent.getStringExtra(AlarmRepository.EXTRA_ALARM_ID).orEmpty()
        val label = intent.getStringExtra(AlarmRingingService.EXTRA_LABEL).orEmpty().ifEmpty { "闹钟" }
        val morningBriefEnabled = intent.getBooleanExtra(
            AlarmRingingService.EXTRA_MORNING_BRIEF_ENABLED, false
        )
        setContent {
            MaterialTheme {
                RingingScreen(
                    label,
                    morningBriefEnabled,
                    onStop = { act(id, AlarmRingingService.ACTION_STOP) },
                    onStopAndPlay = { act(id, AlarmRingingService.ACTION_STOP_AND_PLAY) },
                    onSnooze = { act(id, AlarmRingingService.ACTION_SNOOZE) },
                )
            }
        }
    }

    private fun act(id: String, actionName: String) {
        startService(Intent(this, AlarmRingingService::class.java).apply {
            action = actionName
            putExtra(AlarmRepository.EXTRA_ALARM_ID, id)
        })
        finish()
    }
}

@Composable
private fun RingingScreen(
    label: String,
    morningBriefEnabled: Boolean,
    onStop: () -> Unit,
    onStopAndPlay: () -> Unit,
    onSnooze: () -> Unit,
) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.spacedBy(24.dp, Alignment.CenterVertically),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(label, style = MaterialTheme.typography.headlineLarge)
        Button(onClick = onStop) { Text("停止") }
        if (morningBriefEnabled) {
            Button(onClick = onStopAndPlay) { Text("停止并播放晨报") }
        }
        Button(onClick = onSnooze) { Text("稍后提醒") }
    }
}
