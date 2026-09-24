package com.example.exambrief.core.network

import android.content.Context
import androidx.room.Room
import com.example.exambrief.BuildConfig
import com.example.exambrief.core.database.ExamBriefDatabase
import com.example.exambrief.core.database.HotspotDao
import com.example.exambrief.core.database.MIGRATION_1_2
import com.example.exambrief.core.database.MIGRATION_2_3
import com.example.exambrief.feature.alarm.AlarmDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import retrofit2.Retrofit

@Module
@InstallIn(SingletonComponent::class)
object DataModule {
    @Provides
    @Singleton
    fun database(@ApplicationContext context: Context): ExamBriefDatabase =
        Room.databaseBuilder(context, ExamBriefDatabase::class.java, "exambrief.db")
            .addMigrations(MIGRATION_1_2, MIGRATION_2_3)
            .build()

    @Provides
    fun hotspotDao(database: ExamBriefDatabase): HotspotDao = database.hotspotDao()

    @Provides
    fun alarmDao(database: ExamBriefDatabase): AlarmDao = database.alarmDao()

    @Provides
    @Singleton
    fun json(): Json = Json { ignoreUnknownKeys = true }

    @Provides
    @Singleton
    fun okHttpClient(): OkHttpClient = OkHttpClient.Builder()
        .addInterceptor { chain ->
            val request = chain.request().newBuilder()
                .header("X-Client-Token", BuildConfig.CLIENT_TOKEN)
                .build()
            chain.proceed(request)
        }
        .build()

    @Provides
    @Singleton
    fun retrofit(client: OkHttpClient): Retrofit = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .client(client)
        .build()

    @Provides
    fun hotspotApi(retrofit: Retrofit): HotspotApi = retrofit.create(HotspotApi::class.java)
}
