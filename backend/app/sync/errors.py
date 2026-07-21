class SyncError(Exception):
    def __init__(
        self, message: str = "", provider: str = "", original_error: Exception | None = None,
    ) -> None:
        self.provider = provider
        self.original_error = original_error
        super().__init__(message)


class ProviderUnavailableError(SyncError):
    pass


class ConflictError(SyncError):
    def __init__(self, message: str = "", provider: str = "", conflict: dict | None = None) -> None:
        self.conflict = conflict or {}
        super().__init__(message, provider)


class RetryExceededError(SyncError):
    pass


class AuthenticationError(SyncError):
    pass


class QueueError(SyncError):
    pass
