from __future__ import annotations

import pytest

from app.ai.tool_executor import ToolExecutor
from app.plugins.base import PluginInterface, PluginStatus
from app.plugins.errors import (
    PluginAuthError,
    PluginError,
    PluginExecutionError,
    PluginNotFoundError,
    PluginRateLimitError,
    PluginUnavailableError,
    error_response,
    normalize_error,
    success_response,
)
from app.plugins.manager import PluginManager
from app.tools.base import BaseTool


class FakeTool(BaseTool):
    def __init__(self, name: str, should_fail: bool = False) -> None:
        self._name = name
        self._should_fail = should_fail

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"Tool {self._name}"

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}}

    async def execute(self, **kwargs: str) -> str:
        if self._should_fail:
            raise ValueError("execution failed")
        return f"{self._name} executed with {kwargs}"


class FakePlugin(PluginInterface):
    def __init__(
        self, name: str = "fake", version: str = "1.0.0", desc: str = "Fake plugin",
    ) -> None:
        self._name = name
        self._version = version
        self._desc = desc
        self._tools: list[BaseTool] = [FakeTool(f"{name}_tool1"), FakeTool(f"{name}_tool2")]
        self._enabled = True

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def description(self) -> str:
        return self._desc

    @property
    def required_credentials(self) -> list[str]:
        return ["FAKE_API_KEY"]

    def get_tools(self) -> list[BaseTool]:
        return self._tools

    async def health_check(self) -> dict:
        if not self._enabled:
            return {"status": PluginStatus.DISABLED, "message": "disabled"}
        return {"status": PluginStatus.AVAILABLE, "message": "ok"}

    async def validate(self) -> bool:
        return True


class FailingPlugin(FakePlugin):
    def __init__(self) -> None:
        super().__init__(name="failing", version="1.0.0")
        self._tools = [FakeTool("failing_tool", should_fail=True)]

    async def health_check(self) -> dict:
        return {"status": PluginStatus.UNAVAILABLE, "message": "unavailable"}

    async def validate(self) -> bool:
        return False


class TestPluginInterface:
    def test_required_credentials_abstract(self) -> None:
        with pytest.raises(TypeError):

            class IncompletePlugin(PluginInterface):  # type: ignore
                @property
                def name(self) -> str:
                    return "test"

                @property
                def version(self) -> str:
                    return "1.0.0"

                @property
                def description(self) -> str:
                    return "test"

                def get_tools(self) -> list:
                    return []

            IncompletePlugin()

    def test_get_metadata(self) -> None:
        p = FakePlugin()
        meta = p.get_metadata()
        assert meta["name"] == "fake"
        assert meta["version"] == "1.0.0"
        assert meta["description"] == "Fake plugin"

    def test_get_permission_scope(self) -> None:
        p = FakePlugin()
        scope = p.get_permission_scope()
        assert scope["name"] == "fake"
        assert "FAKE_API_KEY" in scope["required_credentials"]
        assert "fake_tool1" in scope["actions"]
        assert "fake_tool2" in scope["actions"]

    @pytest.mark.asyncio
    async def test_health_check_default(self) -> None:
        p = FakePlugin()
        hc = await p.health_check()
        assert hc["status"] == PluginStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_validate_default(self) -> None:
        p = FakePlugin()
        v = await p.validate()
        assert v is True

    @pytest.mark.asyncio
    async def test_execute_tool(self) -> None:
        p = FakePlugin()
        result = await p.execute_tool("fake_tool1", key="val")
        assert "fake_tool1 executed" in result

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self) -> None:
        p = FakePlugin()
        with pytest.raises(ValueError, match="Tool 'nonexistent' not found"):
            await p.execute_tool("nonexistent")


class TestPluginErrors:
    def test_normalize_error_keeps_plugin_error(self) -> None:
        e = PluginAuthError(message="auth failed")
        result = normalize_error(e)
        assert result is e

    def test_normalize_error_from_http_401(self) -> None:
        e = ValueError("401 Unauthorized")
        result = normalize_error(e, "test")
        assert isinstance(result, PluginAuthError)

    def test_normalize_error_from_rate_limit(self) -> None:
        e = ValueError("429 Too Many Requests")
        result = normalize_error(e, "test")
        assert isinstance(result, PluginRateLimitError)

    def test_normalize_error_from_auth_message(self) -> None:
        e = ValueError("authentication failed")
        result = normalize_error(e, "test")
        assert isinstance(result, PluginAuthError)

    def test_normalize_error_generic(self) -> None:
        e = ValueError("something broke")
        result = normalize_error(e, "test")
        assert isinstance(result, PluginExecutionError)

    def test_success_response(self) -> None:
        r = success_response("ok", tool_name="t1", plugin_name="p1")
        assert r["success"] is True
        assert r["result"] == "ok"
        assert r["tool"] == "t1"
        assert r["plugin"] == "p1"

    def test_error_response(self) -> None:
        r = error_response(PluginNotFoundError("not found"), plugin_name="p1", tool_name="t1")
        assert r["success"] is False
        assert r["error"] == "not found"
        assert r["error_type"] == "PluginNotFoundError"
        assert r["plugin"] == "p1"
        assert r["tool"] == "t1"

    def test_error_response_hierarchy(self) -> None:
        classes = [
            PluginNotFoundError,
            PluginAuthError,
            PluginRateLimitError,
            PluginUnavailableError,
            PluginExecutionError,
        ]
        for cls in classes:
            e = cls("test")
            assert isinstance(e, cls)
            assert issubclass(cls, PluginError)


class TestPluginManager:
    @pytest.fixture
    def manager(self) -> PluginManager:
        pm = PluginManager()
        return pm

    @pytest.mark.asyncio
    async def test_initial_state(self, manager: PluginManager) -> None:
        assert manager.is_initialized() is False
        assert manager.plugin_count() == 0
        assert manager.tool_count() == 0

    @pytest.mark.asyncio
    async def test_register_and_unregister(self, manager: PluginManager) -> None:
        plugin = FakePlugin()
        manager._router.register_plugin(plugin)
        assert manager.plugin_count() == 1
        assert manager.tool_count() == 2

        plugin2 = FakePlugin(name="another", version="2.0.0")
        manager._router.register_plugin(plugin2)
        assert manager.plugin_count() == 2
        assert manager.tool_count() == 4

        manager._router.unregister_plugin("fake")
        assert manager.plugin_count() == 1
        assert manager.tool_count() == 2

    @pytest.mark.asyncio
    async def test_get_plugin(self, manager: PluginManager) -> None:
        plugin = FakePlugin()
        manager._router.register_plugin(plugin)
        found = manager.get_plugin("fake")
        assert found is plugin
        assert manager.get_plugin("nonexistent") is None

    @pytest.mark.asyncio
    async def test_get_all_plugins(self, manager: PluginManager) -> None:
        p1 = FakePlugin("alpha")
        p2 = FakePlugin("beta")
        manager._router.register_plugin(p1)
        manager._router.register_plugin(p2)
        plugins = manager.get_all_plugins()
        assert len(plugins) == 2
        names = {p.name for p in plugins}
        assert names == {"alpha", "beta"}

    @pytest.mark.asyncio
    async def test_get_all_tools(self, manager: PluginManager) -> None:
        p1 = FakePlugin("alpha")
        p2 = FakePlugin("beta")
        manager._router.register_plugin(p1)
        manager._router.register_plugin(p2)
        tools = manager.get_all_tools()
        assert len(tools) == 4
        tool_names = {t["name"] for t in tools}
        assert tool_names == {"alpha_tool1", "alpha_tool2", "beta_tool1", "beta_tool2"}
        for t in tools:
            assert "plugin" in t
            assert t["plugin"] in ("alpha", "beta")

    @pytest.mark.asyncio
    async def test_get_tool_definitions(self, manager: PluginManager) -> None:
        p1 = FakePlugin("alpha")
        manager._router.register_plugin(p1)
        defs = manager.get_tool_definitions()
        assert len(defs) == 2
        for d in defs:
            assert d["type"] == "function"
            assert "function" in d

    @pytest.mark.asyncio
    async def test_health_check_all(self, manager: PluginManager) -> None:
        p1 = FakePlugin("alpha")
        p2 = FailingPlugin()
        manager._router.register_plugin(p1)
        manager._router.register_plugin(p2)
        result = await manager.health_check()
        assert result["healthy"] >= 1
        assert result["unavailable"] >= 1
        assert "alpha" in result["plugins"]
        assert "failing" in result["plugins"]

    @pytest.mark.asyncio
    async def test_health_check_specific(self, manager: PluginManager) -> None:
        p1 = FakePlugin("alpha")
        manager._router.register_plugin(p1)
        result = await manager.health_check("alpha")
        assert result["plugin"] == "alpha"
        assert result["status"] == PluginStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_health_check_not_found(self, manager: PluginManager) -> None:
        result = await manager.health_check("nonexistent")
        assert result["status"] == PluginStatus.UNAVAILABLE
        assert result["error"] == "not_found"

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, manager: PluginManager) -> None:
        plugin = FakePlugin("alpha")
        manager._router.register_plugin(plugin)
        manager.set_status("alpha", PluginStatus.AVAILABLE)
        result = await manager.execute_tool("alpha_tool1", param="value")
        assert result["success"] is True
        assert "alpha_tool1 executed" in result["result"]
        assert result["tool"] == "alpha_tool1"

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, manager: PluginManager) -> None:
        with pytest.raises(PluginNotFoundError):
            await manager.execute_tool("nonexistent")

    @pytest.mark.asyncio
    async def test_execute_tool_plugin_unavailable(self, manager: PluginManager) -> None:
        plugin = FakePlugin("alpha")
        manager._router.register_plugin(plugin)
        manager.set_status("alpha", PluginStatus.DISABLED)
        with pytest.raises(PluginUnavailableError):
            await manager.execute_tool("alpha_tool1")

    @pytest.mark.asyncio
    async def test_execute_tool_auth_failed_status(self, manager: PluginManager) -> None:
        plugin = FakePlugin("alpha")
        manager._router.register_plugin(plugin)
        manager.set_status("alpha", PluginStatus.AUTH_FAILED)
        with pytest.raises(PluginUnavailableError):
            await manager.execute_tool("alpha_tool1")

    @pytest.mark.asyncio
    async def test_execute_tool_safe_success(self, manager: PluginManager) -> None:
        plugin = FakePlugin("alpha")
        manager._router.register_plugin(plugin)
        manager.set_status("alpha", PluginStatus.AVAILABLE)
        result = await manager.execute_tool_safe("alpha_tool1")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_tool_safe_not_found(self, manager: PluginManager) -> None:
        result = await manager.execute_tool_safe("nonexistent")
        assert result["success"] is False
        assert result["error_type"] == "PluginNotFoundError"

    @pytest.mark.asyncio
    async def test_get_set_status(self, manager: PluginManager) -> None:
        plugin = FakePlugin("alpha")
        manager._router.register_plugin(plugin)
        assert manager.get_status("alpha") is None
        manager.set_status("alpha", PluginStatus.INITIALIZED)
        assert manager.get_status("alpha") == PluginStatus.INITIALIZED

    @pytest.mark.asyncio
    async def test_get_all_statuses(self, manager: PluginManager) -> None:
        p1 = FakePlugin("alpha")
        p2 = FakePlugin("beta")
        manager._router.register_plugin(p1)
        manager._router.register_plugin(p2)
        manager.set_status("alpha", PluginStatus.AVAILABLE)
        manager.set_status("beta", PluginStatus.DISABLED)
        statuses = manager.get_all_statuses()
        assert statuses["alpha"] == PluginStatus.AVAILABLE
        assert statuses["beta"] == PluginStatus.DISABLED

    @pytest.mark.asyncio
    async def test_get_stats(self, manager: PluginManager) -> None:
        p1 = FakePlugin("alpha")
        manager._router.register_plugin(p1)
        manager.set_status("alpha", PluginStatus.AVAILABLE)
        stats = manager.get_stats()
        assert stats["total_plugins"] == 1
        assert stats["total_tools"] == 2
        assert "alpha" in stats["plugins"]
        assert stats["plugins"]["alpha"]["status"] == PluginStatus.AVAILABLE

    @pytest.mark.asyncio
    async def test_get_plugin_metadata(self, manager: PluginManager) -> None:
        plugin = FakePlugin("alpha")
        manager._router.register_plugin(plugin)
        manager._health_cache["alpha"] = plugin.get_metadata()
        meta = manager.get_plugin_metadata("alpha")
        assert meta is not None
        assert meta["name"] == "alpha"

        assert manager.get_plugin_metadata("nonexistent") is None

    @pytest.mark.asyncio
    async def test_get_all_plugin_metadata(self, manager: PluginManager) -> None:
        p1 = FakePlugin("alpha")
        p2 = FakePlugin("beta")
        manager._router.register_plugin(p1)
        manager._router.register_plugin(p2)
        manager._health_cache["alpha"] = p1.get_metadata()
        manager._health_cache["beta"] = p2.get_metadata()
        metas = manager.get_all_plugin_metadata()
        assert len(metas) == 2

    @pytest.mark.asyncio
    async def test_shutdown(self, manager: PluginManager) -> None:
        p1 = FakePlugin("alpha")
        manager._router.register_plugin(p1)
        manager.set_status("alpha", PluginStatus.AVAILABLE)
        await manager.shutdown()
        assert manager.plugin_count() == 0
        assert manager.is_initialized() is False


class TestToolExecutorSync:
    @pytest.mark.asyncio
    async def test_sync_from_plugin_manager(self) -> None:
        pm = PluginManager()
        plugin = FakePlugin("alpha")
        pm._router.register_plugin(plugin)
        pm.set_status("alpha", PluginStatus.AVAILABLE)

        executor = ToolExecutor()
        executor.sync_from_plugin_manager(pm)

        assert executor.has_tools() is True
        assert len(executor.get_tool_names()) == 2
        assert "alpha_tool1" in executor.get_tool_names()
        assert "alpha_tool2" in executor.get_tool_names()

        defs = executor.get_tool_definitions()
        assert len(defs) == 2
        for d in defs:
            assert d["type"] == "function"
            assert d["function"]["name"] in ("alpha_tool1", "alpha_tool2")

    @pytest.mark.asyncio
    async def test_execute_through_executor(self) -> None:
        pm = PluginManager()
        plugin = FakePlugin("alpha")
        pm._router.register_plugin(plugin)
        pm.set_status("alpha", PluginStatus.AVAILABLE)

        executor = ToolExecutor()
        executor.sync_from_plugin_manager(pm)

        result = await executor.execute(
            {"id": "call_1", "name": "alpha_tool1", "arguments": {"x": "y"}},
        )
        assert result["success"] is True
        assert "alpha_tool1 executed" in result["result"]
        assert result["tool_call_id"] == "call_1"

    @pytest.mark.asyncio
    async def test_execute_multiple(self) -> None:
        pm = PluginManager()
        plugin = FakePlugin("alpha")
        pm._router.register_plugin(plugin)
        pm.set_status("alpha", PluginStatus.AVAILABLE)

        executor = ToolExecutor()
        executor.sync_from_plugin_manager(pm)

        calls = [
            {"id": "c1", "name": "alpha_tool1", "arguments": {}},
            {"id": "c2", "name": "alpha_tool2", "arguments": {}},
        ]
        results = await executor.execute_multiple(calls)
        assert len(results) == 2
        assert all(r["success"] for r in results)

    @pytest.mark.asyncio
    async def test_sync_clears_previous(self) -> None:
        pm = PluginManager()
        plugin = FakePlugin("alpha")
        pm._router.register_plugin(plugin)
        pm.set_status("alpha", PluginStatus.AVAILABLE)

        executor = ToolExecutor()
        executor.register_tool("old_tool", lambda: "old", description="old")
        assert executor.has_tools() is True

        executor.sync_from_plugin_manager(pm)
        assert "old_tool" not in executor.get_tool_names()


class TestPluginStatusLabel:
    def test_labels(self) -> None:
        assert PluginStatus.label(PluginStatus.AVAILABLE) == "Available"
        assert PluginStatus.label(PluginStatus.DISABLED) == "Disabled"
        assert PluginStatus.label(PluginStatus.AUTH_FAILED) == "Auth Failed"
        assert PluginStatus.label(PluginStatus.UNAVAILABLE) == "Unavailable"
        assert PluginStatus.label("unknown_status") == "unknown_status"
