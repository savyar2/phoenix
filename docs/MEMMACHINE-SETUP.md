# 🧠 MemMachine Setup Guide

This guide will help you set up MemMachine, an open-source memory layer for AI agents, and integrate it with the Phoenix Protocol.

## What is MemMachine?

MemMachine enables AI-powered applications to **learn**, **store**, and **recall** data and preferences from past sessions to enrich future interactions. It provides a persistent memory layer that works across multiple sessions, agents, and large language models.

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API Key (required for MemMachine's language models and embeddings)

## Step 1: Install MemMachine Server

### Option A: Using Docker (Recommended)

1. **Download the latest MemMachine release:**

```bash
# Get the latest release URL
TARBALL_URL=$(curl -s https://api.github.com/repos/MemMachine/MemMachine/releases/latest \
  | grep '"tarball_url"' \
  | head -n 1 \
  | sed -E 's/.*"tarball_url": "(.*)",/\1/')

# Download the tarball
curl -L "$TARBALL_URL" -o MemMachine-latest.tar.gz

# Extract the archive
tar -xzf MemMachine-latest.tar.gz

# Move into the extracted directory (GitHub adds a commit hash to the folder name)
cd MemMachine-MemMachine-*/

# Start the MemMachine installation
./memmachine-compose.sh
```

2. **Follow the setup prompts:**
   - The script will guide you through the setup process
   - You'll be prompted to enter your OpenAI API key
   - The server will start automatically

### Option B: Using PIP

```bash
pip install memmachine
```

## Step 2: Verify Installation

Once MemMachine is running, verify it's working:

```bash
curl http://localhost:8080/health
```

You should receive a response indicating the server is healthy.

## Step 3: Get Your API Key and Endpoint

### API Endpoint

By default, MemMachine runs on:
- **Base URL:** `http://localhost:8080`

If you're running MemMachine in a different location or port, update the `MEMMACHINE_BASE_URL` in your `.env` file.

### API Key

MemMachine may require an API key depending on your configuration:

1. **Check your MemMachine configuration file** (`cfg.yml` in the MemMachine directory)
2. **If authentication is enabled**, you'll need to:
   - Generate an API key from your MemMachine dashboard/configuration
   - Or use the default key if provided during setup

For local development, MemMachine often works without an API key when running on localhost.

## Step 4: Configure Phoenix Protocol

1. **Add MemMachine configuration to your `.env` file:**

```bash
# MemMachine Configuration
MEMMACHINE_ENABLED=true
MEMMACHINE_BASE_URL=http://localhost:8080
MEMMACHINE_API_KEY=  # Leave empty if not required for localhost
```

2. **Install the MemMachine Python client:**

```bash
cd router
pip install memmachine-client
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

## Step 5: Test the Integration

1. **Start the Phoenix Router:**

```bash
cd router
uvicorn app.main:app --reload --host 127.0.0.1 --port 8787
```

2. **Check MemMachine health:**

```bash
curl http://localhost:8787/api/memmachine/health
```

3. **Store a test memory:**

```bash
curl -X POST http://localhost:8787/api/memmachine/store \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "memory_type": "episodic",
    "content": "User prefers vegetarian restaurants",
    "metadata": {"domain": "food"}
  }'
```

4. **Recall memories:**

```bash
curl -X POST http://localhost:8787/api/memmachine/recall \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "query": "restaurant preferences",
    "limit": 5
  }'
```

## Available API Endpoints

Once integrated, you can use these endpoints:

- `POST /api/memmachine/store` - Store a memory
- `POST /api/memmachine/recall` - Recall relevant memories
- `POST /api/memmachine/profile/update` - Update user profile
- `GET /api/memmachine/profile/{user_id}` - Get user profile
- `GET /api/memmachine/health` - Check MemMachine health

## Troubleshooting

### MemMachine server not starting

- Check Docker is running: `docker ps`
- Check logs: `docker-compose logs` (if using Docker)
- Verify port 8080 is not in use: `lsof -i :8080`

### Connection errors

- Verify MemMachine is running: `curl http://localhost:8080/health`
- Check `MEMMACHINE_BASE_URL` in your `.env` file
- Ensure firewall isn't blocking the connection

### API key issues

- For localhost, API key is often optional
- Check your MemMachine `cfg.yml` configuration
- Verify the API key format matches what MemMachine expects

## Next Steps

- Read the [MemMachine Documentation](https://docs.memmachine.ai/)
- Explore the [Python Client API](https://docs.memmachine.ai/api_reference/python/client_api)
- Integrate MemMachine into your agent workflows

## Resources

- [MemMachine Documentation](https://docs.memmachine.ai/)
- [MemMachine GitHub](https://github.com/MemMachine/MemMachine)
- [Quickstart Guide](https://docs.memmachine.ai/getting_started/quickstart)
- [Configuration Guide](https://docs.memmachine.ai/open_source/configuration)

