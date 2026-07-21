from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.entities import router as entities_router
from app.api.v1.google_auth import router as google_auth_router
from app.api.v1.memory import router as memory_router
from app.api.v1.observability import router as observability_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.tools import router as tools_router
from app.api.v1.voice import router as voice_router
from app.core.config import get_settings
from app.core.database import Base, close_db, init_db
from app.core.health import check_database, get_health
from app.core.logging import get_logger, setup_logging
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.request_logger import RequestLoggerMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

settings = get_settings()
_logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    await init_db()

    if settings.DEBUG:
        from app.core.database import engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    api_keys = settings.get_configured_api_keys()
    missing = [name for name, configured in api_keys.items() if not configured]
    if missing:
        _logger.warning(
            "missing_api_keys",
            count=len(missing),
            keys=missing,
            message="The following API keys are not configured. "
            "Set them in .env to enable the corresponding features.",
        )

    from app.agent.service import AgentService
    from app.automation.reminders import ReminderEngine
    from app.automation.scheduler import SchedulerService as SchedService
    from app.file_engine.service import FileService
    from app.file_engine.storage.local import LocalStorage
    from app.plugins.manager import PluginManager
    from app.search import init_search_service
    from app.search.cache import SearchCache
    from app.search.providers import TavilyProvider
    from app.search.service import SearchService
    from app.sync.service import SyncService
    from app.tools.plugin_loader import PluginLoader
    from app.tools.router import ToolRouter
    from app.voice.providers.groq import GroqSTTProvider, GroqTTSProvider
    from app.voice.providers.gemini import GeminiSTTProvider, GeminiTTSProvider
    from app.voice.providers.mock import MockSTTProvider, MockTTSProvider
    from app.voice.service import VoiceService
    from app.voice.pipeline import VoicePipeline
    from app.voice.session import VoiceSessionManager

    search_cache = SearchCache(default_ttl=300)
    tavily_provider = TavilyProvider()
    search_service = SearchService(provider=tavily_provider, cache=search_cache, timeout=25.0)
    init_search_service(search_service)

    file_storage = LocalStorage()
    file_service = FileService(storage=file_storage, max_size=50 * 1024 * 1024, deduplicate=True)

    if settings.GROQ_API_KEY:
        stt_provider = GroqSTTProvider()
        tts_provider = GroqTTSProvider()
    elif settings.GEMINI_API_KEY:
        stt_provider = GeminiSTTProvider()
        tts_provider = GeminiTTSProvider()
    else:
        stt_provider = MockSTTProvider()
        tts_provider = MockTTSProvider()

    voice_service = VoiceService(stt_provider=stt_provider, tts_provider=tts_provider)
    voice_service.set_chat_handler(None)

    sync_service = SyncService()

    agent_service = AgentService()

    plugin_manager = PluginManager()
    await plugin_manager.initialize()

    scheduler = SchedService()
    reminders = ReminderEngine()

    application.state.search_service = search_service
    application.state.file_service = file_service
    application.state.voice_service = voice_service
    application.state.sync_service = sync_service
    application.state.agent_service = agent_service
    application.state.plugin_manager = plugin_manager
    application.state.scheduler = scheduler
    application.state.reminders = reminders

    _logger.info("ultron_started", version=settings.APP_VERSION)

    yield

    if hasattr(application.state, "scheduler"):
        await application.state.scheduler.stop()
    if hasattr(application.state, "plugin_manager"):
        await application.state.plugin_manager.shutdown()

    await close_db()
    _logger.info("ultron_stopped")


app = FastAPI(
    title="ULTRON API",
    description="Personal AI Assistant Backend",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(ErrorHandlerMiddleware)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(memory_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(entities_router, prefix="/api/v1")
app.include_router(google_auth_router, prefix="/api/v1")
app.include_router(voice_router, prefix="/api/v1")
app.include_router(tools_router, prefix="/api/v1")
app.include_router(observability_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict:
    return {
        "name": "ULTRON",
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health() -> dict:
    return await get_health()


@app.get("/livez")
async def liveness() -> dict:
    return {"status": "alive"}


@app.get("/readyz")
async def readiness() -> dict:
    db = await check_database()
    if db["status"] != "healthy":
        return {"status": "not_ready", "checks": {"database": db}}
    return {"status": "ready", "checks": {"database": db}}
