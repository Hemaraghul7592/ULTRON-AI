package com.ultron.data.local

import androidx.room.Room
import androidx.room.testing.MigrationTestHelper
import androidx.sqlite.db.SupportSQLiteDatabase
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class AppDatabaseMigrationTest {
    @get:Rule
    val helper = MigrationTestHelper(
        InstrumentationRegistry.getInstrumentation(),
        AppDatabase::class.java,
    )

    @Test
    fun migrate1To2PreservesTables() {
        val database = helper.createDatabase("migration-test", 1)
        database.execSQL("INSERT INTO conversations (id, title, model, system_prompt, created_at, updated_at) VALUES ('c1', 'Title', NULL, NULL, 0, 0)")
        database.close()

        helper.runMigrationsAndValidate(
            "migration-test",
            2,
            true,
            AppDatabase.MIGRATION_1_2,
        ).close()
    }
}
