package com.ultron.data.local

import androidx.room.Database
import androidx.room.migration.Migration
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import androidx.sqlite.db.SupportSQLiteDatabase

@Database(
    entities = [
        ConversationEntity::class,
        MessageEntity::class,
        MemoryEntity::class,
    ],
    version = 2,
    exportSchema = true,
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun conversationDao(): ConversationDao
    abstract fun messageDao(): MessageDao
    abstract fun memoryDao(): MemoryDao

    companion object {
        val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(database: SupportSQLiteDatabase) {
                database.execSQL("CREATE INDEX IF NOT EXISTS index_messages_conversation_id_created_at ON messages(conversation_id, created_at)")
                database.execSQL("CREATE INDEX IF NOT EXISTS index_memories_memory_type_updated_at ON memories(memory_type, updated_at)")
            }
        }
    }
}
