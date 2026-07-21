from __future__ import annotations


class VoiceError(Exception):
    def __init__(
        self,
        message: str = "",
        provider: str = "",
        original_error: Exception | None = None,
    ) -> None:
        self.provider = provider
        self.original_error = original_error
        super().__init__(message)


class InvalidAudioError(VoiceError):
    pass


class SpeechRecognitionError(VoiceError):
    pass


class SpeechSynthesisError(VoiceError):
    pass


class SessionError(VoiceError):
    pass


class ProviderUnavailableError(VoiceError):
    pass


class ProviderAuthError(VoiceError):
    pass
