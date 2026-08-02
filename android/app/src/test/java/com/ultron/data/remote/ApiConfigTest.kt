package com.ultron.data.remote

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ApiConfigTest {
    @Test
    fun productionEndpointUsesHttps() {
        assertTrue(ApiConfig.DEFAULT_BASE_URL.startsWith("https://"))
        assertFalse(ApiConfig.DEFAULT_BASE_URL.contains("localhost"))
        assertFalse(ApiConfig.DEFAULT_BASE_URL.contains("127.0.0.1"))
    }

    @Test(expected = IllegalArgumentException::class)
    fun cleartextEndpointsAreRejected() {
        ApiConfig.validateBaseUrl("http://example.invalid")
    }
}
