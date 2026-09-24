package com.example.exambrief.feature.hotspot

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import dagger.hilt.EntryPoint
import dagger.hilt.InstallIn
import dagger.hilt.android.EntryPointAccessors
import dagger.hilt.components.SingletonComponent
import com.example.exambrief.feature.briefing.BriefingRepository
import java.time.LocalDate
import java.time.ZoneId
import kotlinx.coroutines.CancellationException

@EntryPoint
@InstallIn(SingletonComponent::class)
interface HotspotWorkerEntryPoint {
    fun hotspotRepository(): HotspotRepository
    fun briefingRepository(): BriefingRepository
}

class HotspotSyncWorker(context: Context, parameters: WorkerParameters) :
    CoroutineWorker(context, parameters) {
    override suspend fun doWork(): Result {
        val entryPoint = EntryPointAccessors.fromApplication(
            applicationContext,
            HotspotWorkerEntryPoint::class.java,
        )
        val hotspotRepository = entryPoint.hotspotRepository()
        val briefingRepository = entryPoint.briefingRepository()
        return try {
            val day = LocalDate.now().toString()
            val timezone = ZoneId.systemDefault().id
            hotspotRepository.refresh(day, timezone)
            briefingRepository.refresh(day, timezone)
            Result.success()
        } catch (error: Exception) {
            if (error is CancellationException) throw error
            Result.retry()
        }
    }
}
