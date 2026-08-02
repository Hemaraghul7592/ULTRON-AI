package com.ultron.data.remote

import com.ultron.BuildConfig

object ApiConfig {
    val DEFAULT_BASE_URL: String = BuildConfig.API_BASE_URL.trimEnd('/')
    val API_PATH: String = BuildConfig.API_PATH

    fun validateBaseUrl(url: String): String {
        val normalized = url.trim().trimEnd('/')
        require(normalized.startsWith("https://")) { "The Android API endpoint must use HTTPS" }
        return normalized
    }
}
