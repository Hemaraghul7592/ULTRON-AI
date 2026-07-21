package com.ultron.data.repository

import com.ultron.data.local.ConversationDao
import com.ultron.data.local.ConversationEntity
import com.ultron.data.local.MessageDao
import com.ultron.data.local.MessageEntity
import com.ultron.data.remote.ApiService
import com.ultron.data.remote.ChatRequest
import com.ultron.data.remote.ConversationDetailResponse
import com.ultron.domain.model.ChatMessage
import com.ultron.domain.model.Conversation
import com.ultron.domain.model.Message
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withContext
import java.util.Date
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ChatRepository @Inject constructor(
    private val apiService: ApiService,
    private val conversationDao: ConversationDao,
    private val messageDao: MessageDao,
) {
    suspend fun sendMessage(
        message: String,
        conversationId: String? = null,
        provider: String? = null,
        model: String? = null,
        useMemory: Boolean = true,
    ): Result<Pair<String, String>> = withContext(Dispatchers.IO) {
        try {
            val actualConversationId = conversationId ?: run {
                val newConv = ConversationEntity()
                conversationDao.insert(newConv)
                newConv.id
            }

            messageDao.insert(
                MessageEntity(
                    conversationId = actualConversationId,
                    role = "user",
                    content = message,
                )
            )

            val response = apiService.chat(
                ChatRequest(
                    message = message,
                    conversation_id = actualConversationId,
                    provider = provider,
                    model = model,
                    use_memory = useMemory,
                )
            )

            if (response.isSuccessful) {
                val body = response.body()!!
                val convId = body.conversation_id.ifEmpty { actualConversationId }

                messageDao.insert(
                    MessageEntity(
                        conversationId = convId,
                        role = "assistant",
                        content = body.message,
                        model = body.model,
                        tokensUsed = body.tokens_used,
                    )
                )

                val conv = conversationDao.getById(convId)
                if (conv != null) {
                    conversationDao.update(conv.copy(updatedAt = Date()))
                }

                Result.success(Pair(body.message, convId))
            } else {
                Result.failure(Exception("API error: ${response.code()} ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    fun getConversations(): Flow<List<Conversation>> {
        return conversationDao.getAll().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    suspend fun getConversation(id: String): Conversation? {
        return conversationDao.getById(id)?.toDomain()
    }

    suspend fun getConversationDetail(id: String): Result<ConversationDetailResponse> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getConversation(id)
            if (response.isSuccessful) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Failed to load conversation"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    fun getMessages(conversationId: String): Flow<List<Message>> {
        return messageDao.getByConversationId(conversationId).map { entities ->
            entities.map { it.toDomain() }
        }
    }

    suspend fun createConversation(): String {
        val entity = ConversationEntity()
        conversationDao.insert(entity)
        return entity.id
    }

    suspend fun deleteConversation(id: String) {
        messageDao.deleteByConversationId(id)
        conversationDao.deleteById(id)
    }

    suspend fun deleteAllLocal() {
        conversationDao.getAll().collect { conversations ->
            conversations.forEach { conv ->
                messageDao.deleteByConversationId(conv.id)
                conversationDao.delete(conv)
            }
        }
    }

    private fun ConversationEntity.toDomain() = Conversation(
        id = id,
        title = title,
        model = model,
        systemPrompt = systemPrompt,
        createdAt = createdAt.time,
        updatedAt = updatedAt.time,
        messageCount = 0,
    )

    private fun MessageEntity.toDomain() = Message(
        id = id,
        conversationId = conversationId,
        role = role,
        content = content,
        model = model,
        tokensUsed = tokensUsed,
        createdAt = createdAt.time,
    )
}
