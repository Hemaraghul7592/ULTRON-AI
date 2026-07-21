package com.ultron.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "ultron_settings")

class SettingsDataStore @Inject constructor(
    private val context: Context,
) {
    private object Keys {
        val SERVER_URL = stringPreferencesKey("server_url")
        val THEME = stringPreferencesKey("theme")
        val DARK_MODE = booleanPreferencesKey("dark_mode")
        val TTS_ENABLED = booleanPreferencesKey("tts_enabled")
        val STT_ENABLED = booleanPreferencesKey("stt_enabled")
        val WAKE_WORD_ENABLED = booleanPreferencesKey("wake_word_enabled")
        val VOICE_ID = stringPreferencesKey("voice_id")
        val DEFAULT_MODEL = stringPreferencesKey("default_model")
        val DEFAULT_PROVIDER = stringPreferencesKey("default_provider")
        val ONBOARDING_COMPLETE = booleanPreferencesKey("onboarding_complete")
        val ACCESS_TOKEN = stringPreferencesKey("access_token")
    }

    val serverUrl: Flow<String> = context.dataStore.data.map { it[Keys.SERVER_URL] ?: "http://127.0.0.1:8000" }
    val theme: Flow<String> = context.dataStore.data.map { it[Keys.THEME] ?: "system" }
    val darkMode: Flow<Boolean> = context.dataStore.data.map { it[Keys.DARK_MODE] ?: true }
    val ttsEnabled: Flow<Boolean> = context.dataStore.data.map { it[Keys.TTS_ENABLED] ?: true }
    val sttEnabled: Flow<Boolean> = context.dataStore.data.map { it[Keys.STT_ENABLED] ?: true }
    val wakeWordEnabled: Flow<Boolean> = context.dataStore.data.map { it[Keys.WAKE_WORD_ENABLED] ?: false }
    val voiceId: Flow<String> = context.dataStore.data.map { it[Keys.VOICE_ID] ?: "Arista" }
    val defaultModel: Flow<String> = context.dataStore.data.map { it[Keys.DEFAULT_MODEL] ?: "llama-3.3-70b-versatile" }
    val defaultProvider: Flow<String> = context.dataStore.data.map { it[Keys.DEFAULT_PROVIDER] ?: "groq" }
    val onboardingComplete: Flow<Boolean> = context.dataStore.data.map { it[Keys.ONBOARDING_COMPLETE] ?: false }
    val accessToken: Flow<String> = context.dataStore.data.map { it[Keys.ACCESS_TOKEN] ?: "" }

    suspend fun setServerUrl(url: String) {
        context.dataStore.edit { it[Keys.SERVER_URL] = url }
    }

    suspend fun setTheme(theme: String) {
        context.dataStore.edit { it[Keys.THEME] = theme }
    }

    suspend fun setDarkMode(enabled: Boolean) {
        context.dataStore.edit { it[Keys.DARK_MODE] = enabled }
    }

    suspend fun setTtsEnabled(enabled: Boolean) {
        context.dataStore.edit { it[Keys.TTS_ENABLED] = enabled }
    }

    suspend fun setSttEnabled(enabled: Boolean) {
        context.dataStore.edit { it[Keys.STT_ENABLED] = enabled }
    }

    suspend fun setWakeWordEnabled(enabled: Boolean) {
        context.dataStore.edit { it[Keys.WAKE_WORD_ENABLED] = enabled }
    }

    suspend fun setVoiceId(id: String) {
        context.dataStore.edit { it[Keys.VOICE_ID] = id }
    }

    suspend fun setDefaultModel(model: String) {
        context.dataStore.edit { it[Keys.DEFAULT_MODEL] = model }
    }

    suspend fun setDefaultProvider(provider: String) {
        context.dataStore.edit { it[Keys.DEFAULT_PROVIDER] = provider }
    }

    suspend fun setOnboardingComplete(complete: Boolean) {
        context.dataStore.edit { it[Keys.ONBOARDING_COMPLETE] = complete }
    }

    suspend fun setAccessToken(token: String) {
        context.dataStore.edit { it[Keys.ACCESS_TOKEN] = token }
    }
}
