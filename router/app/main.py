"""
Phoenix Protocol - Context Router Service

Local service (localhost:8787) that generates Context Packs for the Chrome Extension.
"""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import ingest, graph, memory_cards, agent, memverge, memmachine, profile, context_pack
from app.services.graph_service import GraphService
from app.services.memmachine_service import MemMachineService

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info("🔥 Phoenix Protocol starting up...")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Initialize Neo4j
    try:
        await GraphService.get_driver()
        await GraphService.setup_schema()
        logger.info("✅ Neo4j connection established")
    except Exception as e:
        logger.error(f"❌ Neo4j connection failed: {e}")
    
    # Initialize MemMachine
    if settings.memmachine_enabled:
        try:
            client = MemMachineService.get_client()
            if client:
                logger.info("✅ MemMachine client initialized")
            else:
                logger.warning("⚠️ MemMachine client not available (check configuration)")
        except Exception as e:
            logger.error(f"❌ MemMachine initialization failed: {e}")
    else:
        logger.info("ℹ️ MemMachine is disabled")
    
    # TODO: Initialize MemVerge client
    # TODO: Start agent monitoring
    
    yield
    
    # Shutdown
    logger.info("🔥 Phoenix Protocol shutting down...")
    await GraphService.close()


app = FastAPI(
    title="Phoenix Context Router",
    description="Local service for generating Context Packs from Memory Cards",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware (allow Chrome extension, frontend, and AI chat sites)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8787",
        "http://127.0.0.1:8787",
        # AI Chat sites for content script requests
        "https://chatgpt.com",
        "https://chat.openai.com",
        "https://claude.ai",
        "https://gemini.google.com",
    ],
    allow_origin_regex=r"(chrome-extension://.*|https://.*\.openai\.com|https://.*\.anthropic\.com|https://.*\.google\.com)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "alive",
        "service": "Phoenix Context Router",
        "message": "Ready to generate Context Packs 🔥"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    memmachine_health = await MemMachineService.health_check()
    
    return {
        "status": "healthy",
        "components": {
            "router": "up",
            "wallet": "pending",  # TODO: Actual check
            "neo4j": "pending",  # TODO: Actual check
            "memmachine": memmachine_health
        }
    }


# Include routers
app.include_router(ingest.router, prefix="/api/ingest", tags=["Ingestion"])
app.include_router(graph.router, prefix="/api/graph", tags=["Graph"])
app.include_router(memory_cards.router, prefix="/api/memory-cards", tags=["Memory Cards"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(memverge.router, prefix="/api/memverge", tags=["MemVerge"])
app.include_router(memmachine.router, prefix="/api/memmachine", tags=["MemMachine"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(context_pack.router, prefix="/api/context-pack", tags=["Context Pack"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.router_host,
        port=settings.router_port,
        reload=settings.debug
    )

