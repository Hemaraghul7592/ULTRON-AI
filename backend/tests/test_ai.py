import pytest

from app.ai.prompt_builder import PromptBuilder
from app.ai.context_builder import ContextBuilder


class TestPromptBuilder:
    def setup_method(self):
        self.builder = PromptBuilder()

    def test_build_messages(self):
        messages = self.builder.build_messages(
            user_message="Hello",
            system_prompt="You are ULTRON",
        )
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"

    def test_build_with_history(self):
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        messages = self.builder.build_messages(
            user_message="How are you?",
            conversation_history=history,
        )
        assert len(messages) == 4

    def test_build_with_memory(self):
        messages = self.builder.build_messages(
            user_message="What's my schedule?",
            memory_context="User has meeting at 3pm",
        )
        assert len(messages) == 2
        assert "meeting" in messages[0]["content"]

    def test_build_summary_prompt(self):
        prompt = self.builder.build_summary_prompt(["Conversation 1", "Conversation 2"])
        assert "Conversation 1" in prompt
        assert "Conversation 2" in prompt

    def test_build_memory_extraction_prompt(self):
        prompt = self.builder.build_memory_extraction_prompt("I like coffee in the morning")
        assert "coffee" in prompt

    def test_build_entity_extraction_prompt(self):
        prompt = self.builder.build_entity_extraction_prompt("John works at Google")
        assert "John" in prompt
        assert "Google" in prompt


class TestContextBuilder:
    def setup_method(self):
        self.builder = ContextBuilder()

    def test_build_context_empty(self):
        context = self.builder.build_context()
        assert context == ""

    def test_build_context_with_memories(self):
        memories = [
            {"content": "User likes coffee", "importance": 0.8, "tags": ["preference"]},
            {"content": "Meeting at 3pm", "importance": 0.9, "tags": []},
        ]
        context = self.builder.build_context(memories=memories)
        assert "coffee" in context
        assert "Meeting" in context

    def test_estimate_tokens(self):
        tokens = self.builder.estimate_tokens("Hello world")
        assert tokens > 0

    def test_truncate_to_fit(self):
        messages = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "User message " * 100},
            {"role": "assistant", "content": "Response " * 100},
        ]
        truncated = self.builder.truncate_to_fit(messages, max_tokens=50)
        assert len(truncated) <= 3

    def test_format_memory_context(self):
        memories = [
            {"content": "Fact 1", "memory_type": "short_term", "importance": 0.5},
            {"content": "Fact 2", "memory_type": "long_term", "importance": 0.9},
        ]
        context = self.builder.format_memory_context(memories)
        assert "Fact 1" in context
        assert "Fact 2" in context
        assert "short_term" in context
