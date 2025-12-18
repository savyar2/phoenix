# 🔥 The Phoenix Protocol - Architecture Overview

> **"Magic Context Injection: Your AI Never Forgets Who You Are"**

## Executive Summary

The Phoenix Protocol delivers a **visibly magical experience** where users type normally in ChatGPT/Claude/Gemini, and the system automatically injects the 2–5 most relevant constraints/preferences from their "Context Wallet" with conflict resolution (Neo4j) and crash-resumable agent demo (MemVerge).

**The Magic**: You type "Book me a dinner reservation" in ChatGPT. The extension silently prepends your dietary constraints and budget preferences. The AI responds perfectly—without you repeating yourself.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           THE PHOENIX PROTOCOL                                   │
│                    (Chrome "Magic Injection" + Neo4j + MemVerge)                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                    🌐 CHROME EXTENSION (Magic Injection)                  │  │
│  │                                                                          │  │
│  │  User types in ChatGPT/Claude/Gemini:                                    │  │
│  │  "Book me a dinner reservation"                                           │  │
│  │                                                                          │  │
│  │  Extension intercepts → Calls Context Router → Gets Context Pack        │  │
│  │                                                                          │  │
│  │  Final message sent:                                                      │  │
│  │  "CONTEXT: Hard: No red meat | Soft: Budget $50/month                    │  │
│  │   ──────────────────────────────────────────────────────                  │  │
│  │   Book me a dinner reservation"                                           │  │
│  │                                                                          │  │
│  │  UI Chip: "Using: Vegan • Budget-first • Concise" [Expand]                │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                             │
│                                    │ POST /context-pack                          │
│                                    ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │              🔄 LOCAL CONTEXT ROUTER (localhost:8787)                     │  │
│  │                                                                          │  │
│  │  1. Intent Classification (cheap heuristic)                              │  │
│  │  2. Retrieve relevant Memory Cards from Wallet                           │  │
│  │  3. Query Neo4j for conflict resolution                                  │  │
│  │  4. Return Context Pack + explanation                                    │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                             │
│                                    │ Query Graph                                 │
│                                    ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                    💎 NEO4J (The "Policy + Relationship Brain")           │  │
│  │                                                                          │  │
│  │  Nodes: Preference, Constraint, Goal, Capability, Persona, Source        │  │
│  │  Edges: CONFLICTS_WITH, OVERRIDES, APPLIES_TO_DOMAIN, HAS_PRIORITY      │  │
│  │                                                                          │  │
│  │  Computes "winning rules" when conflicts occur                           │  │
│  │  Provides "why" traces for explainability                                │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                             │
│                                    │ Store/Retrieve                              │
│                                    ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │              💾 CONTEXT WALLET (Local-First Encrypted Store)              │  │
│  │                                                                          │  │
│  │  Memory Cards (atomic):                                                  │  │
│  │  • Type: constraint | preference | goal | capability                     │  │
│  │  • Domain: ["food", "shopping", "coding", "writing"]                    │  │
│  │  • Priority: hard | soft                                                │  │
│  │  • Personas: Work/Personal/Travel                                        │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │              🧠 AGENT ORCHESTRATOR (Optional, for Long Tasks)             │  │
│  │                                                                          │  │
│  │  LangGraph agent for multi-step tasks                                    │  │
│  │  Uses same Context Pack API                                              │  │
│  │  Demonstrates conflict-aware decisions                                   │  │
│  │                                                                          │  │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │ │
│  │  │              MEMVERGE (Agent State Immortality)                    │  │ │
│  │  │                                                                   │  │ │
│  │  │  Wraps Agent Orchestrator process/container                        │  │ │
│  │  │  Periodically checkpoints RAM/state + execution graph state        │  │ │
│  │  │  Demo: "long task → crash → resume at same step"                  │  │ │
│  │  └──────────────────────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### A) Chrome Extension (Distribution + Magic)
**Responsibilities:**
- Detect supported chat UIs (chatgpt.com, claude.ai, gemini.google.com)
- Capture user's draft prompt (before send)
- Call local Context Router to fetch a Context Pack
- Prepend Context Pack to the prompt (or attach as "system-style header")
- Show "Context Used" UI chip with expand/collapse + quick toggle

**Key Parts:**
- Content script per site (DOM hooks)
- Background service worker (auth/session + local calls)
- UI overlay (Context Used + toggles)

### B) Local Context Router (localhost:8787)
**Responsibilities:**
- Intent classification (cheap heuristic first)
- Retrieve relevant "memory cards" from Context Wallet
- Conflict resolution via Neo4j queries
- Return compact Context Pack + explanation metadata

### C) Neo4j (The "Policy + Relationship Brain")
**Stores structured nodes/edges:**
- Nodes: Preference, Constraint, Goal, Capability, Persona, Source
- Edges: CONFLICTS_WITH, OVERRIDES, APPLIES_TO_DOMAIN, DERIVED_FROM, HAS_PRIORITY

**Responsibilities:**
- Compute "winning rules" when conflicts occur
- Provide "why" traces for explainability

### D) MemVerge (Agent State Immortality Layer)
**Included as demo-capability in MVP:**
- Wrap the Agent Orchestrator process/container with MemVerge checkpoint/restore
- Periodically checkpoint RAM/state + execution graph state (LangGraph state)
- Demo: "long task → crash → resume at same step"

### E) Agent Orchestrator (Optional in MVP, but included)
**A local agent service (LangGraph) used for:**
- Long-running tasks (multi-step) that benefit from checkpointing
- Demonstrating conflict-aware decisions using Neo4j

### F) Local Context Wallet Store (Local-first)
**Encrypted local file (JSON/YAML) OR sqlite**
- "Memory Cards" format (small atomic items)
- Personas: Work/Personal/Travel

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Backend API | FastAPI (Python) | REST API, WebSocket for real-time updates |
| Agent Framework | LangGraph | Stateful agent with graph-based execution |
| LLM (Cloud) | OpenAI GPT-4 / Claude | Main reasoning engine |
| LLM (Local) | Ollama + Llama 3.2 | Privacy-preserving tuple extraction |
| Graph Database | Neo4j AuraDB | Long-term memory, relationships |
| State Persistence | MemVerge MMC | RAM checkpointing, instant recovery |
| Frontend | React + Vite | Dashboard visualization |
| Graph Visualization | Neovis.js / react-force-graph | Live graph display |
| Containerization | Docker | Agent runtime isolation |

---

## Data Flow Summary

### Flow 1: Magic Injection on Chat Website (Core MVP)
```
1. User types in ChatGPT: "Recommend a restaurant tonight near me"
                         │
2. Extension intercepts send event
                         │
3. Extension calls Router: POST /context-pack {draft_prompt, site_id, persona}
                         │
4. Router: Intent classify → Retrieve relevant cards → Neo4j conflict query
                         │
5. Router returns Context Pack:
   "CONTEXT: Hard: No red meat | Soft: Budget $50/month"
                         │
6. Extension prepends to prompt + shows UI chip
                         │
7. Message sent to ChatGPT with context injected
```

### Flow 2: Memory Card Ingestion
```
1. User adds "I'm vegan" into Wallet UI
                         │
2. UI writes card into local encrypted store
                         │
3. Router syncs/upserts into Neo4j:
   (:Constraint {id, text, priority, tags...})
                         │
4. Neo4j runs lightweight linking:
   attach domain nodes, detect obvious conflicts
```

### Flow 3: Agent Crash/Resume Demo (MemVerge)
```
1. User starts long task: "Plan a 7-step trip itinerary"
                         │
2. Agent Orchestrator loads Context Pack from Router
                         │
3. LangGraph steps: Planner → Executor → Verifier → Responder
                         │
4. Every N seconds: MemVerge checkpoints agent process state
                         │
5. User presses "Simulate Crash" → Container killed
                         │
6. MemVerge restore triggered → Agent continues at exact step
```

---

## Repository Structure

```
phoenix/
├── docs/                          # Documentation (you are here)
│   ├── 00-ARCHITECTURE-OVERVIEW.md
│   ├── 01-BUILD-PHASE-1-FOUNDATION.md
│   ├── 02-BUILD-PHASE-2-GRAPH.md
│   ├── 03-BUILD-PHASE-3-AGENT.md
│   ├── 04-BUILD-PHASE-4-MEMVERGE.md
│   ├── 05-BUILD-PHASE-5-FRONTEND.md
│   ├── 06-DEMO-SCRIPT.md
│   └── 07-TIMELINE.md
│
├── extension/                     # Chrome Extension (PRIMARY INTERFACE)
│   ├── manifest.json
│   ├── background.js              # Service worker
│   ├── content.js                 # Content scripts per site
│   ├── popup/                     # Extension popup UI
│   │   ├── popup.html
│   │   ├── popup.js
│   │   └── wallet-ui.js          # Context Wallet management
│   └── injected/                 # Injected UI overlay
│       └── context-chip.js       # "Context Used" chip
│
├── router/                        # Local Context Router (localhost:8787)
│   ├── app/
│   │   ├── main.py               # FastAPI router service
│   │   ├── config.py
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── context_pack.py  # POST /context-pack
│   │   │       ├── cards.py         # POST /cards/upsert
│   │   │       └── persona.py       # POST /persona/set
│   │   ├── services/
│   │   │   ├── intent_classifier.py
│   │   │   ├── card_retriever.py
│   │   │   └── conflict_resolver.py  # Neo4j queries
│   │   └── models/
│   │       ├── memory_card.py
│   │       └── context_pack.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── wallet/                        # Context Wallet Store (Local-first)
│   ├── store/
│   │   ├── wallet_store.py       # Encrypted local storage
│   │   ├── encryption.py
│   │   └── sync.py               # Sync with Neo4j
│   └── data/
│       └── wallet.db             # SQLite (or JSON/YAML)
│
├── backend/                       # Neo4j + Graph Services
│   ├── app/
│   │   ├── services/
│   │   │   └── graph_service.py  # Neo4j operations
│   │   ├── graph/
│   │   │   ├── queries.py        # Cypher query templates
│   │   │   └── schema.py         # Graph schema
│   │   └── models/
│   │       └── memory_card.py
│   └── requirements.txt
│
├── agent/                         # Agent Orchestrator (Optional)
│   ├── src/
│   │   ├── graph.py              # LangGraph definition
│   │   ├── nodes/
│   │   │   ├── planner.py
│   │   │   ├── executor.py
│   │   │   └── verifier.py
│   │   └── tools/
│   │       └── context_tools.py  # Uses Context Router API
│   ├── requirements.txt
│   └── Dockerfile.agent
│
├── scripts/                       # Utility scripts
│   ├── seed_wallet.py            # Seed demo Memory Cards
│   ├── demo_injection.py         # Demo magic injection
│   └── demo_crash_restore.py    # MemVerge demo
│
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## Data Contracts (Minimal)

### Memory Card (atomic)
```json
{
  "id": "card_123",
  "type": "constraint | preference | goal | capability",
  "domain": ["food", "shopping", "coding", "writing"],
  "priority": "hard | soft",
  "text": "No red meat",
  "tags": ["diet", "food"],
  "created_at": "..."
}
```

### Context Pack (returned to extension)
```json
{
  "pack_text": "CONTEXT (apply quietly):\n- Hard: No red meat\n- Soft: Prefer cheapest options\n- Style: Be concise\n",
  "used_cards": ["card_123", "card_88", "card_9"],
  "conflicts": [{"a":"card_77","b":"card_123","winner":"card_123"}],
  "explain": ["No red meat overrides Steakhouse preference due to hard constraint."]
}
```

---

## MVP Success Criteria

- ✅ Users feel: "I stopped repeating myself."
- ✅ Conflicts are resolved consistently (Neo4j actually matters).
- ✅ You can demo "immortal agent" (MemVerge) credibly without it being the core wedge.
- ✅ The system fails gracefully (no broken chat UX).

---

## Next Steps

Proceed to the build phases in order:

1. **[Phase 1: Foundation](./01-BUILD-PHASE-1-FOUNDATION.md)** - Context Router, Wallet Store, Chrome Extension setup
2. **[Phase 2: Graph](./02-BUILD-PHASE-2-GRAPH.md)** - Neo4j integration, conflict resolution queries
3. **[Phase 3: Agent](./03-BUILD-PHASE-3-AGENT.md)** - Agent Orchestrator (optional, for long tasks)
4. **[Phase 4: MemVerge](./04-BUILD-PHASE-4-MEMVERGE.md)** - Checkpoint/restore for agent demo
5. **[Phase 5: Frontend](./05-BUILD-PHASE-5-FRONTEND.md)** - Wallet management UI (optional dashboard)
6. **[Demo Script](./06-DEMO-SCRIPT.md)** - Winning demo choreography
7. **[Timeline](./07-TIMELINE.md)** - Build schedule

