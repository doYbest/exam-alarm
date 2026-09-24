package com.example.exambrief

import android.app.Application
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import com.example.exambrief.feature.hotspot.HotspotSyncWorker
import com.example.exambrief.feature.alarm.AlarmRepository
import dagger.hilt.android.HiltAndroidApp
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

@HiltAndroidApp
class ExamBriefApplication : Application() {
    @Inject lateinit var alarms: AlarmRepository

    override fun onCreate() {
        super.onCreate()
        CoroutineScope(Dispatchers.IO).launch { alarms.rescheduleAll() }
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()
        WorkManager.getInstance(this).enqueueUniqueWork(
            "hotspots-startup",
            ExistingWorkPolicy.KEEP,
            OneTimeWorkRequestBuilder<HotspotSyncWorker>().setConstraints(constraints).build(),
        )
        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            "hotspots-daily",
            ExistingPeriodicWorkPolicy.KEEP,
            PeriodicWorkRequestBuilder<HotspotSyncWorker>(1, TimeUnit.DAYS)
                .setConstraints(constraints)
                .build(),
        )
    }
}
