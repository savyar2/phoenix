# 🚀 How to Run The Phoenix Protocol

This guide covers all the ways to run the Phoenix Protocol system.

## 📋 Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** installed
- **Node.js 18+** and npm installed
- **Docker & Docker Compose** installed
- **Neo4j AuraDB account** (free tier) - [Sign up here](https://neo4j.com/cloud/aura/)
- **OpenAI API key** (or Anthropic/Claude API key) - Optional, for LLM features
- **Ollama** installed locally (optional, for local LLM fallback)
- **MemMachine** (optional) - For persistent memory layer - [Setup Guide](docs/MEMMACHINE-SETUP.md)

---

## 🎯 Option 1: Run Everything with Docker Compose (Recommended)

This is the easiest way to run all services together.

### Step 1: Create Environment File

```bash
# Navigate to project root
cd /Users/savyar/Desktop/Code/phoenix

# Run the setup script (creates .env and generates encryption key)
bash scripts/setup_env.sh
```

Or manually create `.env` file:

```bash
# Create .env file
cat > .env << 'EOF'
# Context Router
ROUTER_HOST=127.0.0.1
ROUTER_PORT=8787

# Neo4j Configuration
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password-here

# Wallet Store
WALLET_STORE_PATH=./wallet/data/wallet.db
WALLET_ENCRYPTION_KEY=your-encryption-key-here
WALLET_DEFAULT_PERSONA=Personal

# LLM Providers (Optional)
PHOENIX_OPENAI_API_KEY=your-openai-key
PHOENIX_ANTHROPIC_API_KEY=your-anthropic-key
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
LLM_PROVIDER_PREFERENCE=openai

# MemMachine (Optional - for persistent memory layer)
MEMMACHINE_ENABLED=true
MEMMACHINE_BASE_URL=http://localhost:8080
MEMMACHINE_API_KEY=  # Leave empty for localhost
EOF
```

**Important:** Replace the placeholder values with your actual credentials:
- Get Neo4j URI and credentials from your AuraDB dashboard
- Generate encryption key: `python3 scripts/generate_encryption_key.py`
- Add your OpenAI/Anthropic API keys if you have them
- **MemMachine (Optional)**: If you want persistent memory, install MemMachine server (see [Setup Guide](docs/MEMMACHINE-SETUP.md)) or set `MEMMACHINE_ENABLED=false` to disable

### Step 2: Start MemMachine (Optional)

If you want to use MemMachine for persistent memory:

```bash
# Option A: Use the setup script (requires Docker)
bash scripts/setup_memmachine.sh

# Option B: Manual installation (see docs/MEMMACHINE-SETUP.md)
```

MemMachine will run on `http://localhost:8080` by default.

**Note:** If you don't want to use MemMachine, set `MEMMACHINE_ENABLED=false` in your `.env` file.

### Step 3: Start All Services

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up --build -d
```

This will start:
- **Context Router** on `http://127.0.0.1:8787`
- **Frontend Dashboard** on `http://localhost:5173`
- **MemMachine** (if enabled) on `http://localhost:8080`

### Step 4: Seed Demo Data

In a new terminal:

```bash
cd /Users/savyar/Desktop/Code/phoenix

# Seed Neo4j with demo Memory Cards
python3 scripts/seed_graph.py
```

### Step 5: Verify Services

```bash
# Check router health
curl http://127.0.0.1:8787/health

# Check router API docs
open http://127.0.0.1:8787/docs

# Open frontend dashboard
open http://localhost:5173
```

### Step 6: Load Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `extension/` folder from this project
5. The extension icon should appear in your toolbar

---

## 🛠️ Option 2: Run Services Manually (For Development)

If you want to run services individually for development/debugging:

### A. Run Context Router Manually

```bash
# Navigate to router directory
cd router

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Run the router
uvicorn app.main:app --reload --host 127.0.0.1 --port 8787
```

The router will be available at `http://127.0.0.1:8787`

### B. Run Frontend Manually

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

### C. Run Agent (Optional)

If you want to run the agent separately:

```bash
cd agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run agent (check agent/src/graph.py for entry point)
python -m src.graph
```

---

## 🧪 Testing the System

### Test 1: Health Check

```bash
curl http://127.0.0.1:8787/health
```

Expected response: `{"status": "healthy"}`

### Test 2: Context Pack Generation

```bash
curl -X POST http://127.0.0.1:8787/api/context-pack \
  -H "Content-Type: application/json" \
  -d '{
    "draft_prompt": "Book me a dinner reservation",
    "site_id": "chatgpt",
    "persona": "Personal"
  }'
```

This should return a Context Pack with relevant Memory Cards.

### Test 3: Graph Query

```bash
curl http://127.0.0.1:8787/api/graph/memory-cards
```

This should return all Memory Cards from Neo4j.

### Test 4: MemMachine Health (if enabled)

```bash
curl http://127.0.0.1:8787/api/memmachine/health
```

This should return MemMachine health status.

### Test 5: Store Memory in MemMachine (if enabled)

```bash
curl -X POST http://127.0.0.1:8787/api/memmachine/store \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "memory_type": "episodic",
    "content": "User prefers vegetarian restaurants",
    "metadata": {"domain": "food"}
  }'
```

### Test 6: Chrome Extension

1. Open ChatGPT, Claude, or Gemini in your browser
2. Type a message like "Book me a dinner reservation"
3. The extension should intercept and inject context
4. Check the extension popup to see what context was used

---

## 🎬 Running Demo Scenarios

### Demo 1: Magic Context Injection

1. Make sure router is running
2. Load Chrome extension
3. Add Memory Cards via extension popup or API
4. Open ChatGPT and type: "Book me a dinner reservation"
5. Extension automatically injects context

### Demo 2: Agent Crash & Restore

```bash
# Start a long agent task
curl -X POST http://localhost:8787/api/agent/start \
  -H "Content-Type: application/json" \
  -d '{"task": "Plan a 7-step trip itinerary"}'

# Wait for step 3-4, then simulate crash
curl -X POST http://localhost:8787/api/agent/crash

# Restore from checkpoint
curl -X POST http://localhost:8787/api/agent/restore
```

Or use the frontend dashboard at `http://localhost:5173` for a visual interface.

---

## 🔧 Troubleshooting

### Router won't start

- Check that `.env` file exists and has correct Neo4j credentials
- Verify Neo4j URI is accessible: `curl -v <NEO4J_URI>`
- Check logs: `docker-compose logs router`

### Frontend won't connect to router

- Verify router is running: `curl http://127.0.0.1:8787/health`
- Check `VITE_API_URL` in frontend (should be `http://localhost:8787`)
- Check browser console for CORS errors

### Chrome Extension not working

- Check that router is running on `localhost:8787`
- Open extension popup and check for errors
- Check browser console (F12) for content script errors
- Verify extension is loaded: `chrome://extensions/`

### Neo4j connection issues

- Verify credentials in `.env`
- Check Neo4j AuraDB instance is running
- Test connection: `curl -u neo4j:password <NEO4J_URI>`
- Check firewall/network settings

### Wallet encryption errors

- Regenerate encryption key: `python3 scripts/generate_encryption_key.py`
- Update `WALLET_ENCRYPTION_KEY` in `.env`
- Delete old wallet database: `rm wallet/data/wallet.db`

### MemMachine connection issues

- Verify MemMachine server is running: `curl http://localhost:8080/health`
- Check `MEMMACHINE_BASE_URL` in `.env` matches your MemMachine server URL
- If not using MemMachine, set `MEMMACHINE_ENABLED=false` in `.env`
- See [MemMachine Setup Guide](docs/MEMMACHINE-SETUP.md) for detailed troubleshooting

---

## 📊 Service URLs

Once everything is running:

| Service | URL | Description |
|---------|-----|-------------|
| Context Router | http://127.0.0.1:8787 | Main API server |
| Router API Docs | http://127.0.0.1:8787/docs | Interactive API documentation |
| Router Health | http://127.0.0.1:8787/health | Health check endpoint |
| Frontend Dashboard | http://localhost:5173 | React dashboard UI |
| MemMachine Server | http://localhost:8080 | Persistent memory layer (optional) |
| MemMachine API | http://127.0.0.1:8787/api/memmachine/* | MemMachine endpoints via router |

---

## 🛑 Stopping Services

### Docker Compose

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clears data)
docker-compose down -v
```

### Manual Services

- Press `Ctrl+C` in each terminal running a service
- Or kill processes by port:
  ```bash
  # Kill router
  lsof -ti:8787 | xargs kill
  
  # Kill frontend
  lsof -ti:5173 | xargs kill
  ```

---

## 📝 Next Steps

1. **Read the docs**: Check `docs/` folder for architecture details
2. **Run the demo script**: Follow `docs/06-DEMO-SCRIPT.md` for presentation
3. **Customize Memory Cards**: Add your own constraints/preferences
4. **Explore the API**: Use `http://127.0.0.1:8787/docs` for interactive testing
5. **Set up MemMachine** (optional): Follow `docs/MEMMACHINE-SETUP.md` for persistent memory capabilities

---

## 🆘 Need Help?

- Check the documentation in `docs/` folder
- Review the architecture overview: `docs/00-ARCHITECTURE-OVERVIEW.md`
- Check service logs: `docker-compose logs <service-name>`

