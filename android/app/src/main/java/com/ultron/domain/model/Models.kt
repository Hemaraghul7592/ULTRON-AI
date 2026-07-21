package com.ultron.domain.model

data class Conversation(
    val id: String,
    val title: String?,
    val model: String?,
    val systemPrompt: String? = null,
    val createdAt: Long,
    val updatedAt: Long,
    val messageCount: Int = 0,
)

data class Message(
    val id: String,
    val conversationId: String,
    val role: String,
    val content: String,
    val model: String? = null,
    val tokensUsed: Int? = null,
    val createdAt: Long,
)

data class Memory(
    val id: String,
    val content: String,
    val summary: String? = null,
    val memoryType: String = "short_term",
    val importance: Float = 0.5f,
    val accessCount: Int = 0,
    val source: String? = null,
    val tags: List<String> = emptyList(),
    val createdAt: Long,
    val updatedAt: Long,
)

data class Task(
    val id: String,
    val title: String,
    val description: String? = null,
    val status: String = "pending",
    val priority: Int = 0,
    val dueDate: String? = null,
    val createdAt: Long,
)

data class ChatMessage(
    val role: String,
    val content: String,
    val isStreaming: Boolean = false,
    val toolCalls: List<ToolCallInfo> = emptyList(),
)

data class ToolCallInfo(
    val name: String,
    val arguments: Map<String, Any> = emptyMap(),
)

data class DashboardData(
    val totalConversations: Int = 0,
    val totalMessages: Int = 0,
    val totalMemories: Int = 0,
    val totalTasks: Int = 0,
    val totalTokensUsed: Int = 0,
    val totalCostUsd: Double = 0.0,
    val activeTasks: Int = 0,
    val latencyP50: Double = 0.0,
    val latencyP95: Double = 0.0,
    val latencyP99: Double = 0.0,
    val uptimeSeconds: Double = 0.0,
)

sealed class UiState<out T> {
    data object Loading : UiState<Nothing>()
    data class Success<T>(val data: T) : UiState<T>()
    data class Error(val message: String) : UiState<Nothing>()
}
