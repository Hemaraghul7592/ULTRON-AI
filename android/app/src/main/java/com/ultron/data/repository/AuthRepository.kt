package com.ultron.data.repository

import com.ultron.data.local.SecureTokenStore
import com.ultron.data.remote.ApiService
import com.ultron.data.remote.AuthRequest
import com.ultron.data.remote.AuthResponse
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepository @Inject constructor(
    private val apiService: ApiService,
    private val tokenStore: SecureTokenStore,
) {
    suspend fun login(username: String, password: String): Result<AuthResponse> = authenticate {
        apiService.login(AuthRequest(username, password))
    }

    suspend fun register(username: String, password: String): Result<AuthResponse> = authenticate {
        apiService.register(AuthRequest(username, password))
    }

    fun logout() {
        tokenStore.clear()
    }

    fun hasSession(): Boolean = tokenStore.get().isNotBlank()

    private suspend fun authenticate(request: suspend () -> retrofit2.Response<AuthResponse>): Result<AuthResponse> = withContext(Dispatchers.IO) {
        try {
            val response = request()
            val body = response.body()
            if (response.isSuccessful && body != null) {
                tokenStore.set(body.access_token)
                Result.success(body)
            } else {
                Result.failure(IllegalStateException("Authentication failed (${response.code()})"))
            }
        } catch (error: Exception) {
            Result.failure(error)
        }
    }
}
