package com.example.exambrief.feature.hotspot

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import dagger.hilt.EntryPoint
import dagger.hilt.InstallIn
import dagger.hilt.android.EntryPointAccessors
import dagger.hilt.components.SingletonComponent
import java.time.LocalDate
import java.time.ZoneId
import kotlinx.coroutines.CancellationException

@EntryPoint
@InstallIn(SingletonComponent::class)
interface HotspotWorkerEntryPoint {
    fun hotspotRepository(): HotspotRepository
}

class HotspotSyncWorker(context: Context, parameters: WorkerParameters) :
    CoroutineWorker(context, parameters) {
    override suspend fun doWork(): Result {
        val repository = EntryPointAccessors.fromApplication(
            applicationContext,
            HotspotWorkerEntryPoint::class.java,
        ).hotspotRepository()
        return try {
            repository.refresh(LocalDate.now().toString(), ZoneId.systemDefault().id)
            Result.success()
        } catch (error: Exception) {
            if (error is CancellationException) throw error
            Result.retry()
        }
    }
}

