# 🔥 The Phoenix Protocol

> **Magic Context Injection: Your AI Never Forgets Who You Are**

[![Neo4j](https://img.shields.io/badge/Neo4j-4581C3?style=flat&logo=neo4j&logoColor=white)](https://neo4j.com/)
[![MemVerge](https://img.shields.io/badge/MemVerge-FF6B35?style=flat)](https://memverge.com/)
[![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-4285F4?style=flat&logo=googlechrome&logoColor=white)](https://chrome.google.com/webstore)

The Phoenix Protocol delivers a **visibly magical experience** where users type normally in ChatGPT/Claude/Gemini, and the system automatically injects the 2–5 most relevant constraints/preferences from their "Context Wallet" with conflict resolution (Neo4j) and crash-resumable agent demo (MemVerge).

## 🎯 The Problem

Every AI chatbot today has the memory of a goldfish:
- Tell it your budget on Monday, it forgets by Tuesday
- You have to repeat your constraints every conversation
- It can't resolve conflicts between your preferences and constraints
- When an agent crashes mid-task, you start over

## 💡 The Solution

**Magic Injection Architecture:**

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Chrome Extension** | Content Scripts | Intercepts prompts, injects context |
| **Context Router** | FastAPI (localhost:8787) | Generates Context Packs from Memory Cards |
| **Context Wallet** | Encrypted SQLite | Local-first storage for Memory Cards |
| **Neo4j** | Graph Database | Conflict resolution, relationship reasoning |
| **MemVerge** | Memory Machine Cloud | Agent state persistence (demo) |

## ✨ Key Features

### 🪄 Magic Context Injection
- Type normally in ChatGPT/Claude/Gemini
- Extension automatically prepends your constraints/preferences
- No need to repeat yourself—ever
- UI chip shows exactly what context was used

### 🧠 Graph-Powered Conflict Resolution (Neo4j)
- Stores Memory Cards as a knowledge graph
- Resolves conflicts using graph traversal (not just vector similarity)
- "You like Steakhouse X, but your No Red Meat diet (hard constraint) overrides that"

### 💾 Immortal Agent Execution (MemVerge - Demo)
- Checkpoints agent RAM every 30 seconds
- On crash: restore to the exact step mid-reasoning
- "The agent was at step 25 of 50. It's back at step 25."

### 🔥 The Phoenix Demo
1. Type "Book me a dinner reservation" in ChatGPT
2. Extension injects: "Hard: No red meat | Soft: Budget $50/month"
3. ChatGPT responds perfectly—no repetition needed
4. (Optional) Start long agent task → crash → restore

## 🏗️ Architecture

```
User types in ChatGPT: "Book me a dinner reservation"
         │
         ▼
Chrome Extension intercepts
         │
         ▼
Calls Context Router (localhost:8787)
         │
         ├─→ Retrieves Memory Cards from Wallet
         ├─→ Queries Neo4j for conflict resolution
         └─→ Returns Context Pack
         │
         ▼
Extension prepends: "CONTEXT: Hard: No red meat | Soft: Budget $50"
         │
         ▼
Message sent to ChatGPT with context injected
         │
         ▼
ChatGPT responds perfectly aligned with constraints
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Architecture Overview](./docs/00-ARCHITECTURE-OVERVIEW.md) | System design and data flow |
| [Phase 1: Foundation](./docs/01-BUILD-PHASE-1-FOUNDATION.md) | Project setup, FastAPI skeleton |
| [Phase 2: Neo4j](./docs/02-BUILD-PHASE-2-GRAPH.md) | Graph integration, Cypher queries |
| [Phase 3: Agent](./docs/03-BUILD-PHASE-3-AGENT.md) | LangGraph agent implementation |
| [Phase 4: MemVerge](./docs/04-BUILD-PHASE-4-MEMVERGE.md) | Checkpoint/restore system |
| [Phase 5: Frontend](./docs/05-BUILD-PHASE-5-FRONTEND.md) | React dashboard |
| [Demo Script](./docs/06-DEMO-SCRIPT.md) | Hackathon presentation guide |
| [Timeline](./docs/07-TIMELINE.md) | Build schedule and sprint plan |

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Neo4j AuraDB account (free tier)
- OpenAI API key
- Ollama installed locally

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/phoenix-protocol.git
cd phoenix-protocol

# Copy environment template
cp .env.example .env
# Edit .env with your credentials

# Start all services
docker-compose up --build

# In another terminal, seed demo data
python scripts/seed_graph.py
```

### Access

- **Context Router**: http://127.0.0.1:8787
- **Router Health**: http://127.0.0.1:8787/health
- **Chrome Extension**: Load `extension/` folder as unpacked extension

## 🎬 Demo Scenarios

### Scenario 1: Magic Context Injection
1. Install Chrome Extension
2. Add Memory Cards: "No red meat (hard)", "Budget $50/month (soft)"
3. Open ChatGPT and type: "Book me a dinner reservation"
4. Extension automatically injects context
5. ChatGPT responds: "I've booked Sushi Place Y (respects your no red meat diet and budget)"

### Scenario 2: Conflict Resolution (Neo4j)
- User has: Preference "Likes Steakhouse X" + Constraint "No red meat (hard)"
- Neo4j detects conflict → Constraint wins
- Context Pack includes: "Hard: No red meat | Preference suppressed: Steakhouse X"

### Scenario 3: Crash & Restore (MemVerge - Demo)
```bash
# Start a long agent task
curl -X POST http://localhost:8787/api/agent/start \
  -d '{"task": "Plan a 7-step trip itinerary"}'

# Wait for step 3-4, then crash
curl -X POST http://localhost:8787/api/agent/crash

# Restore from checkpoint
curl -X POST http://localhost:8787/api/agent/restore
```
→ Agent resumes at the exact step it was on

## 🛠️ Tech Stack

- **Chrome Extension**: Manifest V3, Content Scripts
- **Context Router**: FastAPI (Python 3.11) on localhost:8787
- **Context Wallet**: Encrypted SQLite (local-first)
- **Graph DB**: Neo4j AuraDB (conflict resolution)
- **Agent Orchestrator**: LangGraph (optional, for long tasks)
- **State Persistence**: MemVerge MMC (demo capability)

## 📁 Project Structure

```
phoenix/
├── extension/         # Chrome Extension (PRIMARY)
│   ├── manifest.json
│   ├── content.js    # Intercepts chat prompts
│   └── popup/         # Wallet management UI
├── router/            # Context Router (localhost:8787)
│   └── app/
│       ├── api/       # Context Pack generation
│       └── services/  # Intent classification, conflict resolution
├── wallet/            # Context Wallet Store
│   └── store/         # Encrypted local storage
├── backend/           # Neo4j graph services
│   └── app/
│       └── graph/     # Cypher queries
├── agent/             # Agent Orchestrator (optional)
│   └── src/           # LangGraph agent
├── scripts/           # Utility scripts
└── docs/              # Documentation
```

## 🏆 Hackathon Strategy

This architecture is designed to win by hitting sponsor judging criteria:

### Neo4j Judges Want:
- ✅ Graph relationships for conflict resolution
- ✅ "Winning rules" computation when constraints conflict with preferences
- ✅ Explainability traces ("why" this constraint won)

### MemVerge Judges Want:
- ✅ State persistence beyond just data (RAM checkpointing)
- ✅ Instant recovery from crash (agent demo)
- ✅ "Big Memory" use case (long-running agent tasks)

## 🙏 Acknowledgments

- **Neo4j** for graph database technology
- **MemVerge** for Memory Machine Cloud
- **LangChain/LangGraph** for agent framework
- **Ollama** for local LLM inference

## 📄 License

MIT License - see [LICENSE](./LICENSE) for details.

---

<p align="center">
  <b>🔥 The Phoenix rises from the ashes. Every time. 🔥</b>
</p>

