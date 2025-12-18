# 🏗️ Phase 1: Foundation Setup

**Estimated Time: 3-4 hours**

This phase establishes:
- Local Context Router (localhost:8787) - the service that generates Context Packs
- Context Wallet Store - local-first encrypted storage for Memory Cards
- Chrome Extension skeleton - the magic injection interface
- Basic project structure and environment configuration

---

## 1.1 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.11+ installed
- [ ] Node.js 18+ and npm/pnpm installed
- [ ] Docker and Docker Compose installed
- [ ] Git configured
- [ ] Neo4j AuraDB account created (free tier)
- [ ] OpenAI API key (or Claude API key)
- [ ] Ollama installed locally (for distiller)
- [ ] MemVerge MMC access (coordinate with sponsor)

---

## 1.2 Environment Setup

### Step 1: Create Project Structure

```bash
# Create main directories
mkdir -p phoenix/{extension,router/app,wallet/store,backend/app,agent/src,scripts,docs}

# Navigate to project root
cd phoenix

# Initialize git
git init
echo "# 🔥 The Phoenix Protocol" > README.md
```

### Step 2: Create Environment Configuration

Create `.env.example` in project root:

```bash
# .env.example

# ============================================
# CONTEXT ROUTER CONFIGURATION
# ============================================
ROUTER_HOST=127.0.0.1
ROUTER_PORT=8787

# ============================================
# NEO4J CONFIGURATION
# ============================================
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password-here

# ============================================
# WALLET STORE CONFIGURATION
# ============================================
WALLET_STORE_PATH=./wallet/data/wallet.db
WALLET_ENCRYPTION_KEY=your-encryption-key-here  # Generate a secure key
WALLET_DEFAULT_PERSONA=Personal

# ============================================
# MEMVERGE CONFIGURATION (for agent demo)
# ============================================
MEMVERGE_API_ENDPOINT=https://mmc.memverge.com/api
MEMVERGE_API_KEY=your-memverge-key
MEMVERGE_PROJECT_ID=phoenix-agent

# ============================================
# APPLICATION CONFIGURATION
# ============================================
DEBUG=true
```

Copy to `.env`:
```bash
cp .env.example .env
# Edit .env with your actual values
```

---

## 1.3 Context Router Setup

### Step 1: Create Context Router Service

```bash
cd router

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create requirements.txt
cat > requirements.txt << 'EOF'
# Core Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0

# Neo4j
neo4j==5.16.0

# Utilities
httpx==0.26.0
structlog==24.1.0

# Encryption (for wallet)
cryptography==41.0.7

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
EOF

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Create Core Configuration Module

Create `router/app/config.py`:

```python
"""
Phoenix Protocol - Configuration Management
"""
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Context Router settings loaded from environment variables."""
    
    # Router
    router_host: str = Field(default="127.0.0.1", env="ROUTER_HOST")
    router_port: int = Field(default=8787, env="ROUTER_PORT")
    
    # Neo4j
    neo4j_uri: str = Field(..., env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(..., env="NEO4J_PASSWORD")
    
    # Wallet Store
    wallet_store_path: str = Field(default="./wallet/data/wallet.db", env="WALLET_STORE_PATH")
    wallet_encryption_key: str = Field(..., env="WALLET_ENCRYPTION_KEY")
    wallet_default_persona: str = Field(default="Personal", env="WALLET_DEFAULT_PERSONA")
    
    # Application
    debug: bool = Field(default=False, env="DEBUG")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

### Step 3: Create Context Router Application Entry

Create `router/app/main.py`:

```python
"""
Phoenix Protocol - Context Router Service

Local service (localhost:8787) that generates Context Packs for the Chrome Extension.
"""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

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
    
    # TODO: Initialize Neo4j connection pool
    # TODO: Initialize MemVerge client
    # TODO: Start agent monitoring
    
    yield
    
    # Shutdown
    logger.info("🔥 Phoenix Protocol shutting down...")
    # TODO: Close connections gracefully


app = FastAPI(
    title="Phoenix Context Router",
    description="Local service for generating Context Packs from Memory Cards",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware (allow Chrome extension)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*", "http://localhost:*", "http://127.0.0.1:*"],
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
    return {
        "status": "healthy",
        "components": {
            "router": "up",
            "wallet": "pending",  # TODO: Actual check
            "neo4j": "pending"  # TODO: Actual check
        }
    }


# Import and include routers (will be created in Phase 2+)
# from app.api.routes import ingest, graph, agent, memverge
# app.include_router(ingest.router, prefix="/api/ingest", tags=["Ingestion"])
# app.include_router(graph.router, prefix="/api/graph", tags=["Graph"])
# app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
# app.include_router(memverge.router, prefix="/api/memverge", tags=["MemVerge"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.router_host,
        port=settings.router_port,
        reload=settings.debug
    )
```

### Step 4: Create Memory Card Models

Create directory structure:

```bash
mkdir -p router/app/api/routes
mkdir -p router/app/services
mkdir -p router/app/models
```

Create `router/app/models/memory_card.py`:

```python
"""
Pydantic models for Memory Cards and Context Packs.
"""
from pydantic import BaseModel, Field
from typing import Literal, List
from datetime import datetime
import uuid


class MemoryCard(BaseModel):
    """An atomic memory card stored in the Context Wallet."""
    
    id: str = Field(default_factory=lambda: f"card_{uuid.uuid4().hex[:8]}")
    type: Literal["constraint", "preference", "goal", "capability"] = Field(..., description="Type of memory card")
    domain: List[str] = Field(default_factory=list, description="Domains this applies to (food, shopping, coding, etc.)")
    priority: Literal["hard", "soft"] = Field(default="soft", description="Hard constraints override preferences")
    text: str = Field(..., description="The actual constraint/preference/goal text")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    persona: str = Field(default="Personal", description="Persona this belongs to (Work/Personal/Travel)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None


class ContextPackRequest(BaseModel):
    """Request to generate a Context Pack for a draft prompt."""
    
    draft_prompt: str = Field(..., description="The user's draft prompt")
    site_id: str = Field(..., description="Which site (chatgpt, claude, gemini)")
    persona: str = Field(default="Personal", description="Which persona to use")
    sensitivity_mode: Literal["quiet", "normal", "verbose"] = Field(default="quiet", description="How much context to include")


class ContextPack(BaseModel):
    """The Context Pack returned to the extension."""
    
    pack_text: str = Field(..., description="Formatted context text to prepend to prompt")
    used_cards: List[str] = Field(default_factory=list, description="IDs of Memory Cards used")
    conflicts: List[dict] = Field(default_factory=list, description="Detected conflicts and resolutions")
    explain: List[str] = Field(default_factory=list, description="Human-readable explanations")


class ContextPackResponse(BaseModel):
    """Response containing the Context Pack."""
    
    success: bool
    pack: ContextPack
    message: str | None = None
```

Create `router/app/models/context_pack.py`:

```python
# Re-export for convenience
from .memory_card import MemoryCard, ContextPackRequest, ContextPack, ContextPackResponse

__all__ = ["MemoryCard", "ContextPackRequest", "ContextPack", "ContextPackResponse"]

---

## 1.4 Context Wallet Store Setup

### Step 1: Create Wallet Store Service

Create `wallet/store/wallet_store.py`:

```python
"""
Phoenix Protocol - Context Wallet Store

Local-first encrypted storage for Memory Cards.
"""
import sqlite3
import json
from typing import List, Optional
from datetime import datetime
from cryptography.fernet import Fernet
import os

from router.app.models.memory_card import MemoryCard


class WalletStore:
    """Encrypted local storage for Memory Cards."""
    
    def __init__(self, db_path: str, encryption_key: str):
        self.db_path = db_path
        self.cipher = Fernet(encryption_key.encode())
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize the wallet database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_cards (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                domain TEXT NOT NULL,
                priority TEXT NOT NULL,
                text_encrypted TEXT NOT NULL,
                tags TEXT NOT NULL,
                persona TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_card(self, card: MemoryCard) -> MemoryCard:
        """Add a memory card to the wallet."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Encrypt the text
        encrypted_text = self.cipher.encrypt(card.text.encode()).decode()
        
        cursor.execute("""
            INSERT OR REPLACE INTO memory_cards 
            (id, type, domain, priority, text_encrypted, tags, persona, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            card.id,
            card.type,
            json.dumps(card.domain),
            card.priority,
            encrypted_text,
            json.dumps(card.tags),
            card.persona,
            card.created_at.isoformat(),
            datetime.utcnow().isoformat() if card.updated_at else None
        ))
        
        conn.commit()
        conn.close()
        return card
    
    def get_cards(self, persona: str = "Personal", domain: Optional[str] = None) -> List[MemoryCard]:
        """Retrieve memory cards, optionally filtered by persona and domain."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM memory_cards WHERE persona = ?"
        params = [persona]
        
        if domain:
            query += " AND domain LIKE ?"
            params.append(f'%"{domain}"%')
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        cards = []
        for row in rows:
            # Decrypt text
            decrypted_text = self.cipher.decrypt(row[4].encode()).decode()
            
            cards.append(MemoryCard(
                id=row[0],
                type=row[1],
                domain=json.loads(row[2]),
                priority=row[3],
                text=decrypted_text,
                tags=json.loads(row[5]),
                persona=row[6],
                created_at=datetime.fromisoformat(row[7]),
                updated_at=datetime.fromisoformat(row[8]) if row[8] else None
            ))
        
        return cards
    
    def delete_card(self, card_id: str) -> bool:
        """Delete a memory card."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM memory_cards WHERE id = ?", (card_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return deleted
```

## 1.5 Chrome Extension Skeleton

### Step 1: Create Extension Manifest

Create `extension/manifest.json`:

```json
{
  "manifest_version": 3,
  "name": "Phoenix Protocol - Context Wallet",
  "version": "0.1.0",
  "description": "Magic context injection for ChatGPT, Claude, and Gemini",
  
  "permissions": [
    "storage",
    "activeTab"
  ],
  
  "host_permissions": [
    "https://chat.openai.com/*",
    "https://claude.ai/*",
    "https://gemini.google.com/*",
    "http://127.0.0.1:8787/*",
    "http://localhost:8787/*"
  ],
  
  "background": {
    "service_worker": "background.js"
  },
  
  "content_scripts": [
    {
      "matches": [
        "https://chat.openai.com/*",
        "https://claude.ai/*",
        "https://gemini.google.com/*"
      ],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ],
  
  "action": {
    "default_popup": "popup/popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  }
}
```

### Step 2: Create Content Script

Create `extension/content.js`:

```javascript
/**
 * Phoenix Protocol - Content Script
 * 
 * Detects chat textboxes and intercepts send events to inject context.
 */

const ROUTER_URL = 'http://127.0.0.1:8787';

// Detect which site we're on
function detectSite() {
  if (window.location.hostname.includes('openai.com')) return 'chatgpt';
  if (window.location.hostname.includes('claude.ai')) return 'claude';
  if (window.location.hostname.includes('gemini.google.com')) return 'gemini';
  return null;
}

// Find the textbox (site-specific selectors)
function findTextbox() {
  const site = detectSite();
  if (!site) return null;
  
  // ChatGPT selector
  if (site === 'chatgpt') {
    return document.querySelector('textarea[data-id="root"]') || 
           document.querySelector('textarea');
  }
  
  // Claude selector
  if (site === 'claude') {
    return document.querySelector('div[contenteditable="true"]') ||
           document.querySelector('textarea');
  }
  
  // Gemini selector
  if (site === 'gemini') {
    return document.querySelector('textarea') ||
           document.querySelector('div[contenteditable="true"]');
  }
  
  return null;
}

// Get context pack from router
async function getContextPack(draftPrompt) {
  try {
    const response = await fetch(`${ROUTER_URL}/api/context-pack`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        draft_prompt: draftPrompt,
        site_id: detectSite(),
        persona: 'Personal', // TODO: Get from storage
        sensitivity_mode: 'quiet'
      })
    });
    
    const data = await response.json();
    return data.pack;
  } catch (error) {
    console.error('Failed to get context pack:', error);
    return null;
  }
}

// Inject context into prompt
function injectContext(textbox, contextPack) {
  const originalText = textbox.value || textbox.textContent;
  const finalText = `${contextPack.pack_text}\n\n${originalText}`;
  
  if (textbox.value !== undefined) {
    textbox.value = finalText;
    textbox.dispatchEvent(new Event('input', { bubbles: true }));
  } else {
    textbox.textContent = finalText;
    textbox.dispatchEvent(new Event('input', { bubbles: true }));
  }
  
  // Show UI chip
  showContextChip(contextPack);
}

// Show "Context Used" UI chip
function showContextChip(contextPack) {
  // TODO: Create and inject chip element
  console.log('Context used:', contextPack.used_cards);
}

// Main: Intercept send events
function setupInterception() {
  const textbox = findTextbox();
  if (!textbox) return;
  
  // Listen for Enter key or Send button
  textbox.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      
      const draftPrompt = textbox.value || textbox.textContent;
      const contextPack = await getContextPack(draftPrompt);
      
      if (contextPack) {
        injectContext(textbox, contextPack);
      }
      
      // Trigger send (site-specific)
      // TODO: Find and click send button
    }
  });
}

// Initialize when page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', setupInterception);
} else {
  setupInterception();
}
```

## 1.6 Docker Configuration

Create `router/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8787

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8787"]
```

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  # Context Router (localhost:8787)
  router:
    build:
      context: ./router
      dockerfile: Dockerfile
    ports:
      - "8787:8787"
    env_file:
      - .env
    volumes:
      - ./router/app:/app/app  # Hot reload in development
      - ./wallet/data:/app/wallet/data  # Wallet database
    networks:
      - phoenix-network

  # Neo4j connection (via backend service in Phase 2)
  # Will be added in Phase 2

networks:
  phoenix-network:
    driver: bridge
```

---

## 1.5 Verification Steps

After completing Phase 1, verify:

### Test 1: Context Router Starts Successfully

```bash
cd router
source venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8787
```

Visit `http://127.0.0.1:8787` - should see:
```json
{
  "status": "alive",
  "service": "Phoenix Context Router",
  "message": "Ready to generate Context Packs 🔥"
}
```

### Test 2: Health Check Works

Visit `http://127.0.0.1:8787/health` - should return health status

### Test 3: Wallet Store Works

```bash
cd ../wallet
python -c "
from store.wallet_store import WalletStore
from router.app.models.memory_card import MemoryCard

store = WalletStore('./data/wallet.db', 'test-key-12345678901234567890123456789012')
card = MemoryCard(type='constraint', text='No red meat', domain=['food'], priority='hard')
store.add_card(card)
print('✅ Wallet store works!')
"
```

### Test 4: Docker Compose Builds

```bash
cd ..  # Back to project root
docker-compose build router
```

Should complete without errors.

---

## 1.7 Phase 1 Deliverables Checklist

- [ ] Project directory structure created
- [ ] `.env.example` and `.env` configured
- [ ] Context Router service running on localhost:8787
- [ ] Wallet Store with encrypted storage working
- [ ] Memory Card models defined
- [ ] Context Pack models defined
- [ ] Chrome Extension manifest and skeleton created
- [ ] Content script detects chat textboxes
- [ ] Docker configuration ready
- [ ] Basic health check endpoints working

---

## Next: [Phase 2 - Neo4j Graph Integration](./02-BUILD-PHASE-2-GRAPH.md)

