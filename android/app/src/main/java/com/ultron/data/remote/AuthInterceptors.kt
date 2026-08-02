package com.ultron.data.remote

import com.ultron.data.local.SecureTokenStore
import okhttp3.Authenticator
import okhttp3.Interceptor
import okhttp3.Response
import okhttp3.Route
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthorizationInterceptor @Inject constructor(
    private val tokenStore: SecureTokenStore,
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = tokenStore.get()
        val request = if (token.isBlank()) {
            chain.request()
        } else {
            chain.request().newBuilder()
                .header("Authorization", "Bearer $token")
                .build()
        }
        return chain.proceed(request)
    }
}

@Singleton
class SessionAuthenticator @Inject constructor(
    private val tokenStore: SecureTokenStore,
) : Authenticator {
    override fun authenticate(route: Route?, response: Response): okhttp3.Request? {
        val sentToken = response.request.header("Authorization")
        val currentToken = tokenStore.get()
        if (sentToken == null || sentToken != "Bearer $currentToken") return null
        if (responseCount(response) >= 2) return null
        tokenStore.clear()
        return null
    }

    private fun responseCount(response: Response): Int {
        var count = 1
        var previous = response.priorResponse
        while (previous != null) {
            count++
            previous = previous.priorResponse
        }
        return count
    }
}
