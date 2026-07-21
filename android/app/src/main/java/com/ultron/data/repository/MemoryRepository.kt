package com.ultron.data.repository

import com.ultron.data.local.MemoryDao
import com.ultron.data.local.MemoryEntity
import com.ultron.data.remote.ApiService
import com.ultron.data.remote.MemoryCreateRequest
import com.ultron.data.remote.MemorySearchRequest
import com.ultron.domain.model.Memory
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withContext
import java.util.Date
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class MemoryRepository @Inject constructor(
    private val apiService: ApiService,
    private val memoryDao: MemoryDao,
) {
    suspend fun store(
        content: String,
        memoryType: String = "short_term",
        importance: Float = 0.5f,
        source: String? = null,
        tags: List<String> = emptyList(),
    ): Result<Memory> = withContext(Dispatchers.IO) {
        try {
            val entity = MemoryEntity(
                content = content,
                memoryType = memoryType,
                importance = importance,
                source = source,
                tags = tags.joinToString(","),
            )
            memoryDao.insert(entity)
            Result.success(entity.toDomain())
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    fun getAll(): Flow<List<Memory>> {
        return memoryDao.getAll().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    fun getByType(type: String): Flow<List<Memory>> {
        return memoryDao.getByType(type).map { entities ->
            entities.map { it.toDomain() }
        }
    }

    suspend fun search(query: String, limit: Int = 10): List<Memory> {
        return memoryDao.search(query, limit).map { it.toDomain() }
    }

    suspend fun syncFromServer(): Result<Int> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getMemories(pageSize = 100)
            if (response.isSuccessful) {
                val memories = response.body()?.memories ?: emptyList()
                for (mem in memories) {
                    memoryDao.insert(
                        MemoryEntity(
                            id = mem.id,
                            content = mem.content,
                            summary = mem.summary,
                            memoryType = mem.memory_type,
                            importance = mem.importance,
                            source = mem.source,
                            createdAt = Date(),
                            updatedAt = Date(),
                        )
                    )
                }
                Result.success(memories.size)
            } else {
                Result.failure(Exception("Failed to sync memories"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun delete(id: String) {
        memoryDao.deleteById(id)
    }

    suspend fun count(): Int = memoryDao.count()

    private fun MemoryEntity.toDomain() = Memory(
        id = id,
        content = content,
        summary = summary,
        memoryType = memoryType,
        importance = importance,
        accessCount = accessCount,
        source = source,
        tags = tags?.split(",")?.filter { it.isNotBlank() } ?: emptyList(),
        createdAt = createdAt.time,
        updatedAt = updatedAt.time,
    )
}
