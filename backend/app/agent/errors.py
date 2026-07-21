class AgentError(Exception):
    def __init__(
        self, message: str = "", task_id: str = "", original_error: Exception | None = None,
    ) -> None:
        self.task_id = task_id
        self.original_error = original_error
        if original_error is not None:
            self.__cause__ = original_error
        super().__init__(message)


class PlanningError(AgentError):
    pass


class ExecutionError(AgentError):
    pass


class DependencyError(AgentError):
    pass


class TaskTimeoutError(AgentError):
    pass


class RecoveryError(AgentError):
    pass
