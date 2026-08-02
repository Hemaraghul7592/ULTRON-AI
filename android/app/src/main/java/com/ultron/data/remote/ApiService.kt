package com.ultron.data.remote

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.PATCH
import retrofit2.http.Path
import retrofit2.http.Query

data class AuthRequest(
    val username: String,
    val password: String,
)

data class AuthResponse(
    val access_token: String,
    val token_type: String = "bearer",
    val expires_in: Int,
)

data class ChatRequest(
    val message: String,
    val conversation_id: String? = null,
    val system_prompt: String? = null,
    val model: String? = null,
    val provider: String? = null,
    val temperature: Double = 0.7,
    val max_tokens: Int = 4096,
    val stream: Boolean = false,
    val use_memory: Boolean = true,
    val use_tools: Boolean = true,
)

data class ChatResponse(
    val message: String,
    val conversation_id: String,
    val message_id: String,
    val model: String,
    val provider: String,
    val tokens_used: Int,
    val prompt_tokens: Int,
    val completion_tokens: Int,
    val latency_ms: Double,
    val finish_reason: String,
)

data class ConversationResponse(
    val id: String,
    val title: String?,
    val model: String?,
    val created_at: String,
    val updated_at: String,
    val message_count: Int = 0,
)

data class ConversationDetailResponse(
    val id: String,
    val title: String?,
    val model: String?,
    val created_at: String,
    val updated_at: String,
    val message_count: Int = 0,
    val messages: List<MessageResponse> = emptyList(),
)

data class MessageResponse(
    val id: String,
    val role: String,
    val content: String,
    val model: String?,
    val tokens_used: Int?,
    val created_at: String,
)

data class ConversationListResponse(
    val conversations: List<ConversationResponse>,
    val total: Int,
    val page: Int,
    val page_size: Int,
)

data class MemoryResponse(
    val id: String,
    val content: String,
    val summary: String?,
    val memory_type: String,
    val importance: Float,
    val source: String?,
    val created_at: String,
    val updated_at: String,
)

data class MemoryListResponse(
    val memories: List<MemoryResponse>,
    val total: Int,
    val page: Int,
    val page_size: Int,
)

data class MemoryCreateRequest(
    val content: String,
    val memory_type: String = "short_term",
    val importance: Float = 0.5f,
    val source: String? = null,
    val tags: List<String> = emptyList(),
)

data class MemorySearchRequest(
    val query: String,
    val limit: Int = 10,
)

data class MemorySearchResponse(
    val memories: List<MemoryResponse>,
    val scores: List<Double>,
    val query: String,
)

data class TaskResponse(
    val id: String,
    val title: String,
    val description: String?,
    val status: String,
    val priority: Int,
    val due_date: String?,
    val created_at: String,
)

data class TaskListResponse(
    val tasks: List<TaskResponse>,
    val total: Int,
    val page: Int,
    val page_size: Int,
)

data class TaskCreateRequest(
    val title: String,
    val description: String? = null,
    val priority: Int = 0,
    val due_date: String? = null,
)

data class HealthResponse(
    val status: String,
    val version: String,
)

data class DashboardResponse(
    val total_conversations: Int,
    val total_messages: Int,
    val total_memories: Int,
    val total_tasks: Int,
    val total_tokens_used: Int,
    val total_cost_usd: Double,
    val active_tasks: Int,
    val latency_p50: Double,
    val latency_p95: Double,
    val latency_p99: Double,
    val uptime_seconds: Double,
)

interface ApiService {
    @POST("auth/login")
    suspend fun login(@Body request: AuthRequest): Response<AuthResponse>

    @POST("auth/register")
    suspend fun register(@Body request: AuthRequest): Response<AuthResponse>

    @POST("chat")
    suspend fun chat(@Body request: ChatRequest): Response<ChatResponse>

    @GET("conversations")
    suspend fun getConversations(
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 20,
    ): Response<ConversationListResponse>

    @POST("conversations")
    suspend fun createConversation(): Response<ConversationResponse>

    @GET("conversations/{id}")
    suspend fun getConversation(@Path("id") id: String): Response<ConversationDetailResponse>

    @DELETE("conversations/{id}")
    suspend fun deleteConversation(@Path("id") id: String): Response<Unit>

    @GET("memory")
    suspend fun getMemories(
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 20,
    ): Response<MemoryListResponse>

    @POST("memory")
    suspend fun createMemory(@Body request: MemoryCreateRequest): Response<MemoryResponse>

    @POST("memory/search")
    suspend fun searchMemory(@Body request: MemorySearchRequest): Response<MemorySearchResponse>

    @GET("tasks")
    suspend fun getTasks(
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 20,
    ): Response<TaskListResponse>

    @POST("tasks")
    suspend fun createTask(@Body request: TaskCreateRequest): Response<TaskResponse>

    @PATCH("tasks/{id}/complete")
    suspend fun completeTask(@Path("id") id: String): Response<TaskResponse>

    @DELETE("tasks/{id}")
    suspend fun deleteTask(@Path("id") id: String): Response<Unit>

    @GET("observability/health")
    suspend fun health(): Response<HealthResponse>

    @GET("observability/dashboard")
    suspend fun getDashboard(): Response<DashboardResponse>
}
