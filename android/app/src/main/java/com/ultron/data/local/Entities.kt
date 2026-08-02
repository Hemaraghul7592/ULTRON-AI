package com.ultron.data.local

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import java.util.Date
import java.util.UUID

@Entity(tableName = "conversations")
data class ConversationEntity(
    @PrimaryKey
    val id: String = UUID.randomUUID().toString(),
    val title: String? = null,
    val model: String? = null,
    @ColumnInfo(name = "system_prompt")
    val systemPrompt: String? = null,
    @ColumnInfo(name = "created_at")
    val createdAt: Date = Date(),
    @ColumnInfo(name = "updated_at")
    val updatedAt: Date = Date(),
)

@Entity(tableName = "messages", indices = [Index(value = ["conversation_id", "created_at"])])
data class MessageEntity(
    @PrimaryKey
    val id: String = UUID.randomUUID().toString(),
    @ColumnInfo(name = "conversation_id")
    val conversationId: String,
    val role: String,
    val content: String,
    val model: String? = null,
    @ColumnInfo(name = "tokens_used")
    val tokensUsed: Int? = null,
    @ColumnInfo(name = "created_at")
    val createdAt: Date = Date(),
)

@Entity(tableName = "memories", indices = [Index(value = ["memory_type", "updated_at"])])
data class MemoryEntity(
    @PrimaryKey
    val id: String = UUID.randomUUID().toString(),
    val content: String,
    val summary: String? = null,
    @ColumnInfo(name = "memory_type")
    val memoryType: String = "short_term",
    val importance: Float = 0.5f,
    @ColumnInfo(name = "access_count")
    val accessCount: Int = 0,
    val source: String? = null,
    val tags: String? = null,
    @ColumnInfo(name = "created_at")
    val createdAt: Date = Date(),
    @ColumnInfo(name = "updated_at")
    val updatedAt: Date = Date(),
)
