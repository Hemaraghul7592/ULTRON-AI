package com.ultron.ui.screens.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ultron.data.local.SettingsDataStore
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class SettingsUiState(
    val serverUrl: String = "http://10.0.2.2:8000",
    val defaultProvider: String = "groq",
    val defaultModel: String = "llama-3.3-70b-versatile",
    val ttsEnabled: Boolean = true,
    val sttEnabled: Boolean = true,
    val wakeWordEnabled: Boolean = false,
    val darkMode: Boolean = true,
    val voiceId: String = "Arista",
    val onboardingComplete: Boolean = false,
)

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val settingsDataStore: SettingsDataStore,
) : ViewModel() {

    private val _uiState = MutableStateFlow(SettingsUiState())
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    init {
        loadSettings()
    }

    private fun loadSettings() {
        viewModelScope.launch {
            settingsDataStore.serverUrl.collect { _uiState.value = _uiState.value.copy(serverUrl = it) }
        }
        viewModelScope.launch {
            settingsDataStore.defaultProvider.collect { _uiState.value = _uiState.value.copy(defaultProvider = it) }
        }
        viewModelScope.launch {
            settingsDataStore.defaultModel.collect { _uiState.value = _uiState.value.copy(defaultModel = it) }
        }
        viewModelScope.launch {
            settingsDataStore.ttsEnabled.collect { _uiState.value = _uiState.value.copy(ttsEnabled = it) }
        }
        viewModelScope.launch {
            settingsDataStore.sttEnabled.collect { _uiState.value = _uiState.value.copy(sttEnabled = it) }
        }
        viewModelScope.launch {
            settingsDataStore.wakeWordEnabled.collect { _uiState.value = _uiState.value.copy(wakeWordEnabled = it) }
        }
        viewModelScope.launch {
            settingsDataStore.darkMode.collect { _uiState.value = _uiState.value.copy(darkMode = it) }
        }
        viewModelScope.launch {
            settingsDataStore.onboardingComplete.collect { _uiState.value = _uiState.value.copy(onboardingComplete = it) }
        }
    }

    fun setServerUrl(url: String) {
        viewModelScope.launch { settingsDataStore.setServerUrl(url) }
    }

    fun setDefaultProvider(provider: String) {
        viewModelScope.launch { settingsDataStore.setDefaultProvider(provider) }
    }

    fun setDefaultModel(model: String) {
        viewModelScope.launch { settingsDataStore.setDefaultModel(model) }
    }

    fun setTtsEnabled(enabled: Boolean) {
        viewModelScope.launch { settingsDataStore.setTtsEnabled(enabled) }
    }

    fun setSttEnabled(enabled: Boolean) {
        viewModelScope.launch { settingsDataStore.setSttEnabled(enabled) }
    }

    fun setWakeWordEnabled(enabled: Boolean) {
        viewModelScope.launch { settingsDataStore.setWakeWordEnabled(enabled) }
    }

    fun setDarkMode(enabled: Boolean) {
        viewModelScope.launch { settingsDataStore.setDarkMode(enabled) }
    }

    fun setOnboardingComplete(complete: Boolean) {
        viewModelScope.launch { settingsDataStore.setOnboardingComplete(complete) }
    }
}
