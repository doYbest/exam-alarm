package com.example.exambrief.core.database

import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL(
            """CREATE TABLE IF NOT EXISTS alarms (
                id TEXT NOT NULL PRIMARY KEY,
                hour INTEGER NOT NULL,
                minute INTEGER NOT NULL,
                repeatDaysMask INTEGER NOT NULL,
                oneShotDate TEXT,
                enabled INTEGER NOT NULL,
                label TEXT NOT NULL,
                soundUri TEXT,
                vibrate INTEGER NOT NULL,
                snoozeMinutes INTEGER NOT NULL,
                morningBriefEnabled INTEGER NOT NULL,
                autoPlayBrief INTEGER NOT NULL,
                nextTriggerAtEpochMillis INTEGER,
                createdAtEpochMillis INTEGER NOT NULL,
                updatedAtEpochMillis INTEGER NOT NULL
            )""".trimIndent()
        )
    }
}

val MIGRATION_2_3 = object : Migration(2, 3) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL(
            """CREATE TABLE IF NOT EXISTS cached_briefings (
                date TEXT NOT NULL,
                timezone TEXT NOT NULL,
                id TEXT NOT NULL,
                version INTEGER NOT NULL,
                generatedAt TEXT NOT NULL,
                expiresAtEpochMillis INTEGER NOT NULL,
                introText TEXT NOT NULL,
                itemsJson TEXT NOT NULL,
                outroText TEXT NOT NULL,
                etag TEXT,
                cachedAtEpochMillis INTEGER NOT NULL,
                PRIMARY KEY(date, timezone)
            )""".trimIndent()
        )
    }
}
