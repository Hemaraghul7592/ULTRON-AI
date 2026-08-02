package com.ultron.data.local

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SecureTokenStore @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    private val file = context.getFileStreamPath(FILE_NAME)
    private val _token = MutableStateFlow(loadToken())
    val token: StateFlow<String> = _token

    @Synchronized
    fun get(): String = _token.value

    @Synchronized
    fun set(value: String) {
        _token.value = value
        if (value.isBlank()) {
            clear()
            return
        }
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, secretKey())
        val payload = cipher.iv + cipher.doFinal(value.toByteArray(Charsets.UTF_8))
        file.writeText(Base64.encodeToString(payload, Base64.NO_WRAP), Charsets.UTF_8)
    }

    @Synchronized
    fun clear() {
        _token.value = ""
        if (file.exists()) file.delete()
    }

    private fun loadToken(): String {
        if (!file.exists()) return ""
        return runCatching {
            val payload = Base64.decode(file.readText(Charsets.UTF_8), Base64.NO_WRAP)
            require(payload.size > IV_LENGTH)
            val cipher = Cipher.getInstance(TRANSFORMATION)
            cipher.init(
                Cipher.DECRYPT_MODE,
                secretKey(),
                GCMParameterSpec(TAG_LENGTH_BITS, payload.copyOf(IV_LENGTH)),
            )
            cipher.doFinal(payload.copyOfRange(IV_LENGTH, payload.size)).toString(Charsets.UTF_8)
        }.getOrDefault("")
    }

    private fun secretKey(): SecretKey {
        val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
        val existing = keyStore.getKey(KEY_ALIAS, null) as? SecretKey
        if (existing != null) return existing
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEYSTORE).apply {
            init(
                KeyGenParameterSpec.Builder(
                    KEY_ALIAS,
                    KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT,
                )
                    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                    .build(),
            )
        }.generateKey()
    }

    private companion object {
        const val FILE_NAME = "ultron_auth_token.bin"
        const val ANDROID_KEYSTORE = "AndroidKeyStore"
        const val KEY_ALIAS = "ultron_auth_token"
        const val TRANSFORMATION = "AES/GCM/NoPadding"
        const val IV_LENGTH = 12
        const val TAG_LENGTH_BITS = 128
    }
}
