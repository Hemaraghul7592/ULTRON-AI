from __future__ import annotations

import pytest

from app.agent.context import AgentContext
from app.agent.errors import (
    AgentError,
    DependencyError,
    ExecutionError,
    PlanningError,
    RecoveryError,
    TimeoutError,
)
from app.agent.executor import Executor
from app.agent.models import Task, TaskGraph
from app.agent.planner import Planner
from app.agent.service import AgentService


class TestTask:
    def test_create_task(self) -> None:
        t = Task(name="test", service="search", action="search", args={"query": "test"})
        assert t.name == "test"
        assert t.service == "search"
        assert t.status == "pending"
        assert t.id

    def test_task_to_dict(self) -> None:
        t = Task(name="t", service="s", action="a", args={"x": 1}, priority=5, max_retries=3, depends_on=["dep1"])
        d = t.to_dict()
        assert d["name"] == "t"
        assert d["priority"] == 5
        assert d["depends_on"] == ["dep1"]
        assert d["status"] == "pending"

    def test_is_ready(self) -> None:
        t = Task(name="t", service="s", action="a", depends_on=["a", "b"])
        assert t.is_ready({"a"}) is False
        assert t.is_ready({"a", "b"}) is True

    def test_is_ready_when_completed(self) -> None:
        t = Task(name="t", service="s", action="a")
        t.status = "completed"
        assert t.is_ready(set()) is False

    def test_can_retry(self) -> None:
        t = Task(name="t", service="s", action="a", max_retries=2)
        assert t.can_retry() is True
        t.attempts = 2
        assert t.can_retry() is False


class TestTaskGraph:
    def test_add_task(self) -> None:
        g = TaskGraph("test graph")
        t = Task(name="t1", service="s", action="a")
        g.add_task(t)
        assert g.size() == 1

    def test_add_tasks(self) -> None:
        g = TaskGraph("test")
        tasks = [
            Task(name="t1", service="s", action="a"),
            Task(name="t2", service="s", action="b"),
        ]
        g.add_tasks(tasks)
        assert g.size() == 2

    def test_get_ready_tasks(self) -> None:
        g = TaskGraph("test")
        t1 = Task(name="t1", service="s", action="a")
        t2 = Task(name="t2", service="s", action="b", depends_on=[t1.id])
        g.add_tasks([t1, t2])
        ready = g.get_ready_tasks(set())
        assert len(ready) == 1
        assert ready[0].id == t1.id

    def test_get_ready_after_completion(self) -> None:
        g = TaskGraph("test")
        t1 = Task(name="t1", service="s", action="a")
        t2 = Task(name="t2", service="s", action="b", depends_on=[t1.id])
        g.add_tasks([t1, t2])
        g.mark_completed(t1.id)
        ready = g.get_ready_tasks({t1.id})
        assert len(ready) == 1
        assert ready[0].id == t2.id

    def test_get_next_ready(self) -> None:
        g = TaskGraph("test")
        t1 = Task(name="t1", service="s", action="a", priority=0)
        t2 = Task(name="t2", service="s", action="b", priority=1)
        g.add_tasks([t1, t2])
        next_task = g.get_next_ready(set())
        assert next_task is not None
        assert next_task.name == "t2"

    def test_is_complete(self) -> None:
        g = TaskGraph("test")
        t1 = Task(name="t1", service="s", action="a")
        g.add_task(t1)
        assert g.is_complete() is False
        g.mark_completed(t1.id)
        assert g.is_complete() is True

    def test_all_succeeded(self) -> None:
        g = TaskGraph("test")
        t1 = Task(name="t1", service="s", action="a")
        t2 = Task(name="t2", service="s", action="b")
        g.add_tasks([t1, t2])
        g.mark_completed(t1.id)
        g.mark_completed(t2.id)
        assert g.all_succeeded() is True

    def test_mark_failed(self) -> None:
        g = TaskGraph("test")
        t = Task(name="t", service="s", action="a")
        g.add_task(t)
        g.mark_failed(t.id, "error msg")
        assert t.status == "failed"
        assert t.error == "error msg"

    def test_mark_retry(self) -> None:
        g = TaskGraph("test")
        t = Task(name="t", service="s", action="a")
        g.add_task(t)
        t.status = "failed"
        g.mark_retry(t.id)
        assert t.status == "pending"
        assert t.attempts == 1

    def test_to_dict(self) -> None:
        g = TaskGraph("desc")
        g.add_task(Task(name="t1", service="s", action="a"))
        d = g.to_dict()
        assert d["description"] == "desc"
        assert len(d["tasks"]) == 1


class TestAgentContext:
    def test_create_context(self) -> None:
        ctx = AgentContext("req_1")
        assert ctx.request_id == "req_1"

    def test_log_execution(self) -> None:
        ctx = AgentContext()
        t = Task(name="t", service="s", action="a")
        t.status = "completed"
        ctx.log(t, result="ok", duration_ms=100.0)
        assert len(ctx.execution_log) == 1
        assert ctx.execution_log[0]["status"] == "completed"

    def test_execution_summary(self) -> None:
        ctx = AgentContext()
        t = Task(name="t1", service="s", action="a")
        t.status = "completed"
        ctx.log(t, result="ok", duration_ms=50)
        t2 = Task(name="t2", service="s", action="b")
        t2.status = "failed"
        ctx.log(t2, error="fail", duration_ms=10)
        summary = ctx.get_execution_summary()
        assert summary["total_tasks"] == 2
        assert summary["completed"] == 1
        assert summary["failed"] == 1

    def test_to_dict(self) -> None:
        ctx = AgentContext("r1")
        ctx.conversation_id = "conv_1"
        ctx.user_id = "user_1"
        d = ctx.to_dict()
        assert d["conversation_id"] == "conv_1"
        assert d["user_id"] == "user_1"


class TestPlanner:
    def test_plan_search_intent(self) -> None:
        planner = Planner()
        graph = planner.plan("what is artificial intelligence?", "user_1")
        assert graph.size() >= 2
        task_names = {t.name for t in graph.tasks.values()}
        assert "web_search" in task_names
        assert "ai_response" in task_names

    def test_plan_deep_research(self) -> None:
        planner = Planner()
        graph = planner.plan("do a deep research on climate change", "user_1")
        task_names = {t.name for t in graph.tasks.values()}
        assert "deep_research" in task_names

    def test_plan_memory_intent(self) -> None:
        planner = Planner()
        graph = planner.plan("remember that my favorite color is blue", "user_1")
        task_names = {t.name for t in graph.tasks.values()}
        assert "recall_memories" in task_names or "save_to_memory" in task_names
        assert "ai_response" in task_names

    def test_plan_plugin_intent(self) -> None:
        planner = Planner()
        graph = planner.plan("show my github repositories", "user_1")
        task_names = {t.name for t in graph.tasks.values()}
        assert "plugin_operation" in task_names

    def test_plan_file_intent(self) -> None:
        planner = Planner()
        graph = planner.plan("extract text from this document", "user_1")
        task_names = {t.name for t in graph.tasks.values()}
        assert "file_operation" in task_names

    def test_plan_multiple_intents(self) -> None:
        planner = Planner()
        graph = planner.plan("search for python tutorials and save them to my notes", "user_1")
        task_names = {t.name for t in graph.tasks.values()}
        assert "web_search" in task_names
        assert any(n in task_names for n in ["save_to_memory", "recall_memories"])

    def test_plan_ai_response_has_deps(self) -> None:
        planner = Planner()
        graph = planner.plan("search for latest ai news", "user_1")
        ai_tasks = [t for t in graph.tasks.values() if t.service == "ai"]
        assert len(ai_tasks) == 1
        assert len(ai_tasks[0].depends_on) > 0


class TestExecutor:
    @pytest.fixture
    def executor(self) -> Executor:
        return Executor(timeout=5.0, max_retries=1)

    @pytest.mark.asyncio
    async def test_execute_single_task(self, executor: Executor) -> None:
        async def handler(task: Task, context: AgentContext) -> str:
            return "done"

        executor.register_handler("test_service", handler)
        g = TaskGraph()
        t = Task(name="t1", service="test_service", action="test", args={"x": 1})
        g.add_task(t)
        ctx = AgentContext()
        await executor.execute(g, ctx)
        assert t.status == "completed"
        assert t.result == "done"

    @pytest.mark.asyncio
    async def test_execute_sequential_tasks(self, executor: Executor) -> None:
        results = []

        async def handler(task: Task, context: AgentContext) -> str:
            results.append(task.name)
            return task.name

        executor.register_handler("s", handler)
        g = TaskGraph()
        t1 = Task(name="step1", service="s", action="a")
        t2 = Task(name="step2", service="s", action="b", depends_on=[t1.id])
        g.add_tasks([t1, t2])
        ctx = AgentContext()
        await executor.execute(g, ctx)
        assert results == ["step1", "step2"]
        assert t1.status == "completed"
        assert t2.status == "completed"

    @pytest.mark.asyncio
    async def test_task_retry(self, executor: Executor) -> None:
        call_count = []

        async def handler(task: Task, context: AgentContext) -> str:
            call_count.append(1)
            if len(call_count) < 2:
                raise ValueError("transient error")
            return "ok"

        executor.register_handler("s", handler)
        g = TaskGraph()
        t = Task(name="t", service="s", action="a", max_retries=2)
        g.add_task(t)
        ctx = AgentContext()
        await executor.execute(g, ctx)
        assert t.status == "completed"
        assert t.result == "ok"
        assert t.attempts == 1

    @pytest.mark.asyncio
    async def test_task_fails_without_retries(self, executor: Executor) -> None:
        async def handler(task: Task, context: AgentContext) -> str:
            raise ValueError("permanent error")

        executor.register_handler("s", handler)
        g = TaskGraph()
        t = Task(name="t", service="s", action="a", max_retries=0)
        g.add_task(t)
        ctx = AgentContext()
        await executor.execute(g, ctx)
        assert t.status == "failed"
        assert "permanent error" in t.error

    @pytest.mark.asyncio
    async def test_no_handler_raises(self, executor: Executor) -> None:
        g = TaskGraph()
        t = Task(name="t", service="unknown", action="a", max_retries=0)
        g.add_task(t)
        ctx = AgentContext()
        await executor.execute(g, ctx)
        assert t.status == "failed"

    @pytest.mark.asyncio
    async def test_context_propagation(self, executor: Executor) -> None:
        async def handler(task: Task, context: AgentContext) -> str:
            context.memory_refs.append("mem_1")
            return "ok"

        executor.register_handler("s", handler)
        g = TaskGraph()
        t = Task(name="t", service="s", action="a")
        g.add_task(t)
        ctx = AgentContext("req_1")
        ctx.user_message = "test"
        await executor.execute(g, ctx)
        assert "mem_1" in ctx.memory_refs

    @pytest.mark.asyncio
    async def test_execution_logging(self, executor: Executor) -> None:
        async def handler(task: Task, context: AgentContext) -> str:
            return "result"

        executor.register_handler("s", handler)
        g = TaskGraph()
        t = Task(name="t", service="s", action="a")
        g.add_task(t)
        ctx = AgentContext()
        await executor.execute(g, ctx)
        assert len(ctx.execution_log) >= 1

    @pytest.mark.asyncio
    async def test_recover_retry(self, executor: Executor) -> None:
        g = TaskGraph()
        t = Task(name="t", service="s", action="a", max_retries=2)
        t.status = "failed"
        t.attempts = 2
        g.add_task(t)
        await executor.recover(t, g, "retry")
        assert t.status == "pending"
        assert t.attempts == 1

    @pytest.mark.asyncio
    async def test_recover_skip(self, executor: Executor) -> None:
        g = TaskGraph()
        t = Task(name="t", service="s", action="a")
        t.status = "failed"
        g.add_task(t)
        await executor.recover(t, g, "skip")
        assert t.status == "completed"

    @pytest.mark.asyncio
    async def test_recover_unknown_raises(self, executor: Executor) -> None:
        g = TaskGraph()
        t = Task(name="t", service="s", action="a")
        t.status = "failed"
        g.add_task(t)
        with pytest.raises(RecoveryError):
            await executor.recover(t, g, "unknown")

    @pytest.mark.asyncio
    async def test_deadlock_detection(self, executor: Executor) -> None:
        g = TaskGraph()
        t1 = Task(name="t1", service="s1", action="a", depends_on=["t2"])
        t2 = Task(name="t2", service="s2", action="b", depends_on=["t1"])
        g.add_tasks([t1, t2])
        ctx = AgentContext()
        with pytest.raises(DependencyError, match="Deadlock"):
            await executor.execute(g, ctx)


class TestAgentService:
    @pytest.fixture
    def service(self) -> AgentService:
        return AgentService()

    @pytest.mark.asyncio
    async def test_process_with_mock_handlers(self, service: AgentService) -> None:
        async def ai_handler(task: Task, context: AgentContext) -> str:
            return "AI response"

        async def search_handler(task: Task, context: AgentContext) -> dict:
            return {"results": ["result1"]}

        async def memory_handler(task: Task, context: AgentContext) -> dict:
            return {"memories": []}

        service.register_service("ai", ai_handler)
        service.register_service("search", search_handler)
        service.register_service("memory", memory_handler)
        service.register_service("file", lambda t, c: {})
        service.register_service("plugin", lambda t, c: {})
        service.register_service("voice", lambda t, c: {})
        service.register_service("sync", lambda t, c: {})

        result = await service.process("what is python?", "user_1")
        assert result["success"] is True
        assert result["total_tasks"] > 0

    @pytest.mark.asyncio
    async def test_process_memory_intent(self, service: AgentService) -> None:
        memories = []

        async def ai_handler(task: Task, context: AgentContext) -> str:
            return "ok"

        async def memory_save_handler(task: Task, context: AgentContext) -> dict:
            memories.append(task.args)
            return {"memory": "saved"}

        service.register_service("ai", ai_handler)
        service.register_service("memory", memory_save_handler)
        service.register_service("search", lambda t, c: {})
        service.register_service("file", lambda t, c: {})
        service.register_service("plugin", lambda t, c: {})
        service.register_service("voice", lambda t, c: {})
        service.register_service("sync", lambda t, c: {})

        await service.process("remember this: python is my favorite language", "user_1")
        assert len(memories) >= 1

    @pytest.mark.asyncio
    async def test_health_check(self, service: AgentService) -> None:
        service.register_service("ai", lambda t, c: "ok")
        health = await service.health_check()
        assert health["status"] == "healthy"
        assert "ai" in health["registered_services"]

    @pytest.mark.asyncio
    async def test_process_failed_tasks(self, service: AgentService) -> None:
        async def failing_handler(task: Task, context: AgentContext) -> str:
            raise ValueError("failed")

        async def ai_handler(task: Task, context: AgentContext) -> str:
            return "still works"

        service.register_service("ai", ai_handler)
        service.register_service("search", failing_handler)
        service.register_service("memory", lambda t, c: {})
        service.register_service("file", lambda t, c: {})
        service.register_service("plugin", lambda t, c: {})
        service.register_service("voice", lambda t, c: {})
        service.register_service("sync", lambda t, c: {})

        result = await service.process("what is the weather?", "user_1")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_context_passes_through(self, service: AgentService) -> None:
        async def ai_handler(task: Task, context: AgentContext) -> str:
            context.conversation_id = "conv_1"
            return "hi"

        service.register_service("ai", ai_handler)
        service.register_service("search", lambda t, c: {})
        service.register_service("memory", lambda t, c: {})
        service.register_service("file", lambda t, c: {})
        service.register_service("plugin", lambda t, c: {})
        service.register_service("voice", lambda t, c: {})
        service.register_service("sync", lambda t, c: {})

        ctx = AgentContext("r1")
        await service.process("hello", "user_1", context=ctx)
        assert ctx.conversation_id == "conv_1"


class TestAgentErrors:
    def test_error_hierarchy(self) -> None:
        e1 = PlanningError("plan failed")
        assert isinstance(e1, AgentError)
        e2 = ExecutionError("exec failed", task_id="t1")
        assert e2.task_id == "t1"
        e3 = DependencyError("dep failed")
        assert isinstance(e3, AgentError)
        e4 = TimeoutError("timeout")
        assert isinstance(e4, AgentError)
        e5 = RecoveryError("recovery failed")
        assert isinstance(e5, AgentError)

    def test_execution_error_carries_task_id(self) -> None:
        e = ExecutionError("msg", task_id="task_abc")
        assert e.task_id == "task_abc"


class TestAgentIntegration:
    @pytest.mark.asyncio
    async def test_full_pipeline(self) -> None:
        planner = Planner()
        executor = Executor(timeout=10.0, max_retries=0)
        results = []

        async def make_handler(name: str):
            async def handler(task: Task, context: AgentContext) -> str:
                results.append(f"{name}:{task.action}")
                context.search_results.setdefault(name, {})["done"] = True
                return f"{name}_done"
            return handler

        for svc in ["search", "memory", "ai", "file", "plugin", "voice", "sync"]:
            executor.register_handler(svc, await make_handler(svc))

        graph = planner.plan("search for and remember the latest python features", "user_1")
        ctx = AgentContext()
        ctx = await executor.execute(graph, ctx)

        assert len(results) >= 2
        assert len(ctx.execution_log) >= 2
        assert ctx.execution_log[0]["duration_ms"] >= 0
