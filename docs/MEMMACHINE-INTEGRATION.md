# 🧠 MemMachine Integration with Phoenix Protocol

## Overview

MemMachine has been integrated into the Phoenix Protocol as an **optional persistent memory layer** that enhances the system's ability to learn and recall information across sessions.

## How It Fits Into the Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PHOENIX PROTOCOL                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Chrome Extension → Context Router → Neo4j (Graph)         │
│                              ↓                               │
│                    MemMachine (Optional)                     │
│                    Persistent Memory Layer                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Relationship to Existing Components

1. **Context Wallet (Local)**: Stores Memory Cards locally in encrypted SQLite
2. **Neo4j (Graph)**: Stores relationships and conflict resolution rules
3. **MemMachine (New)**: Provides persistent memory across sessions for AI agents

## Integration Points

### 1. Configuration

MemMachine is configured via `.env` file:

```bash
MEMMACHINE_ENABLED=true              # Enable/disable MemMachine
MEMMACHINE_BASE_URL=http://localhost:8080  # MemMachine server URL
MEMMACHINE_API_KEY=                   # Optional API key
```

### 2. API Endpoints

MemMachine is accessible through the Phoenix Router:

- `POST /api/memmachine/store` - Store memories
- `POST /api/memmachine/recall` - Recall relevant memories
- `POST /api/memmachine/profile/update` - Update user profile
- `GET /api/memmachine/profile/{user_id}` - Get user profile
- `GET /api/memmachine/health` - Health check

### 3. Service Layer

The `MemMachineService` class in `router/app/services/memmachine_service.py` handles all MemMachine operations.

## Setup Process

### In RUNNING.md

MemMachine is integrated into the standard setup flow:

1. **Prerequisites**: Listed as optional component
2. **Environment Setup**: MemMachine config added to `.env` template
3. **Step 2**: MemMachine setup instructions added
4. **Testing**: MemMachine health and store tests included
5. **Service URLs**: MemMachine endpoints documented
6. **Troubleshooting**: MemMachine-specific troubleshooting added

### Setup Scripts

- `scripts/setup_env.sh` - Now mentions MemMachine as optional step
- `scripts/setup_memmachine.sh` - Dedicated MemMachine setup script

## Usage Flow

### Without MemMachine (Default)

1. User creates Memory Cards → Stored in Context Wallet (local)
2. Cards synced to Neo4j for conflict resolution
3. Context Router generates Context Packs from Neo4j
4. Extension injects context into chat

### With MemMachine (Optional Enhancement)

1. User creates Memory Cards → Stored in Context Wallet (local)
2. Cards synced to Neo4j for conflict resolution
3. **MemMachine stores episodic memories** from agent interactions
4. **MemMachine recalls relevant context** when needed
5. Context Router combines Neo4j + MemMachine data
6. Extension injects enhanced context into chat

## Benefits

- **Persistent Memory**: AI agents remember past interactions
- **Cross-Session Learning**: Information persists across restarts
- **Enhanced Context**: More relevant context for better responses
- **Optional**: Can be disabled if not needed

## When to Use MemMachine

**Use MemMachine when:**
- You want agents to learn from past conversations
- You need persistent memory across sessions
- You're building long-running agent workflows
- You want to enhance context with historical data

**Skip MemMachine when:**
- You only need local Memory Cards
- You're doing simple context injection
- You want to minimize dependencies
- You don't need cross-session memory

## Disabling MemMachine

To disable MemMachine:

1. Set `MEMMACHINE_ENABLED=false` in `.env`
2. Or simply don't install the MemMachine server
3. The system will work normally without it

## Documentation

- **Setup Guide**: `docs/MEMMACHINE-SETUP.md`
- **Integration Details**: This file
- **Running Guide**: `RUNNING.md` (includes MemMachine steps)
- **Status**: `SETUP-STATUS.md`

## Next Steps

1. Follow `RUNNING.md` for complete setup
2. See `docs/MEMMACHINE-SETUP.md` for MemMachine-specific setup
3. Test integration using the test commands in `RUNNING.md`

