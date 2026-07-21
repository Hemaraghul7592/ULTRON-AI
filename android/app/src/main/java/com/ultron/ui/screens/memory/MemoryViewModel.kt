package com.ultron.ui.screens.memory

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ultron.data.repository.MemoryRepository
import com.ultron.domain.model.Memory
import com.ultron.domain.model.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class MemoryUiState(
    val memories: List<Memory> = emptyList(),
    val searchResults: List<Memory> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
    val searchQuery: String = "",
    val selectedType: String? = null,
)

@HiltViewModel
class MemoryViewModel @Inject constructor(
    private val memoryRepository: MemoryRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(MemoryUiState())
    val uiState: StateFlow<MemoryUiState> = _uiState.asStateFlow()

    init {
        loadMemories()
    }

    fun loadMemories() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            memoryRepository.getAll().collect { memories ->
                _uiState.value = _uiState.value.copy(
                    memories = memories,
                    isLoading = false,
                )
            }
        }
    }

    fun search(query: String) {
        _uiState.value = _uiState.value.copy(searchQuery = query)
        if (query.isBlank()) {
            _uiState.value = _uiState.value.copy(searchResults = emptyList())
            return
        }
        viewModelScope.launch {
            val results = memoryRepository.search(query)
            _uiState.value = _uiState.value.copy(searchResults = results)
        }
    }

    fun addMemory(content: String, type: String = "short_term", importance: Float = 0.5f) {
        viewModelScope.launch {
            memoryRepository.store(
                content = content,
                memoryType = type,
                importance = importance,
            )
            loadMemories()
        }
    }

    fun deleteMemory(id: String) {
        viewModelScope.launch {
            memoryRepository.delete(id)
            loadMemories()
        }
    }

    fun syncFromServer() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            val result = memoryRepository.syncFromServer()
            result.fold(
                onSuccess = { count ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = if (count > 0) "Synced $count memories" else null,
                    )
                    loadMemories()
                },
                onFailure = { error ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = error.message,
                    )
                },
            )
        }
    }
}
