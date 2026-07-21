package com.ultron.ui.screens.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.ultron.data.repository.ChatRepository
import com.ultron.domain.model.ChatMessage
import com.ultron.domain.model.Conversation
import com.ultron.domain.model.UiState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class ChatUiState(
    val conversations: List<Conversation> = emptyList(),
    val currentConversationId: String? = null,
    val messages: List<ChatMessage> = emptyList(),
    val isLoading: Boolean = false,
    val isStreaming: Boolean = false,
    val error: String? = null,
    val inputValue: String = "",
)

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val chatRepository: ChatRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    init {
        loadConversations()
    }

    fun loadConversations() {
        viewModelScope.launch {
            chatRepository.getConversations().collect { conversations ->
                _uiState.value = _uiState.value.copy(conversations = conversations)
            }
        }
    }

    fun selectConversation(conversationId: String) {
        _uiState.value = _uiState.value.copy(
            currentConversationId = conversationId,
            messages = emptyList(),
        )
        loadMessages(conversationId)
    }

    private fun loadMessages(conversationId: String) {
        viewModelScope.launch {
            chatRepository.getMessages(conversationId).collect { messages ->
                val chatMessages = messages.map { msg ->
                    ChatMessage(
                        role = msg.role,
                        content = msg.content,
                    )
                }
                _uiState.value = _uiState.value.copy(messages = chatMessages)
            }
        }
    }

    fun updateInput(value: String) {
        _uiState.value = _uiState.value.copy(inputValue = value)
    }

    fun sendMessage() {
        val message = _uiState.value.inputValue.trim()
        if (message.isEmpty() || _uiState.value.isLoading) return

        val userMessage = ChatMessage(role = "user", content = message)
        _uiState.value = _uiState.value.copy(
            messages = _uiState.value.messages + userMessage,
            inputValue = "",
            isLoading = true,
            isStreaming = true,
        )

        viewModelScope.launch {
            val result = chatRepository.sendMessage(
                message = message,
                conversationId = _uiState.value.currentConversationId,
            )
            result.fold(
                onSuccess = { (response, conversationId) ->
                    val assistantMessage = ChatMessage(role = "assistant", content = response)
                    _uiState.value = _uiState.value.copy(
                        messages = _uiState.value.messages + assistantMessage,
                        currentConversationId = conversationId,
                        isLoading = false,
                        isStreaming = false,
                    )
                    loadConversations()
                },
                onFailure = { error ->
                    _uiState.value = _uiState.value.copy(
                        error = error.message,
                        isLoading = false,
                        isStreaming = false,
                    )
                },
            )
        }
    }

    fun newConversation() {
        viewModelScope.launch {
            val id = chatRepository.createConversation()
            _uiState.value = _uiState.value.copy(
                currentConversationId = id,
                messages = emptyList(),
            )
        }
    }

    fun deleteConversation(id: String) {
        viewModelScope.launch {
            chatRepository.deleteConversation(id)
            if (_uiState.value.currentConversationId == id) {
                _uiState.value = _uiState.value.copy(
                    currentConversationId = null,
                    messages = emptyList(),
                )
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
