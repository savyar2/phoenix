# 🔑 API Keys Guide: MemVerge vs MemMachine

This guide clarifies the difference between **MemVerge** and **MemMachine** and where to get API keys for each.

## ⚠️ Important: Two Different Products

The Phoenix Protocol uses **two different memory-related products**:

1. **MemVerge** (Memory Machine Cloud) - Agent checkpointing/restore
2. **MemMachine** - Persistent memory layer for AI agents

---

## 🧠 MemMachine API Key

### What is MemMachine?

MemMachine is an **open-source memory layer** for AI agents that enables learning, storing, and recalling data across sessions.

### Do I Need an API Key?

**For Local Development (localhost):**
- ✅ **NO API KEY REQUIRED** - Leave `MEMMACHINE_API_KEY` empty in `.env`
- MemMachine runs locally and doesn't require authentication

**For Cloud/Remote Deployment:**
- Check your MemMachine configuration file (`cfg.yml`)
- If authentication is enabled, you'll get a key during setup
- Or check your MemMachine dashboard/configuration

### How to Get Started Without an API Key

1. **Install MemMachine server locally:**
   ```bash
   bash scripts/setup_memmachine.sh
   ```

2. **Configure in `.env`:**
   ```bash
   MEMMACHINE_ENABLED=true
   MEMMACHINE_BASE_URL=http://localhost:8080
   MEMMACHINE_API_KEY=  # Leave empty - not needed for localhost
   ```

3. **That's it!** MemMachine will work without an API key for local development.

### If You Need an API Key

- Check the `cfg.yml` file in your MemMachine installation directory
- Look for authentication settings in the MemMachine configuration
- The setup script (`memmachine-compose.sh`) will guide you through this

---

## 💾 MemVerge API Key

### What is MemVerge?

MemVerge (Memory Machine Cloud) is a **commercial product** for checkpointing and restoring agent state. It's used for the "Immortal Agent" demo capability.

### Do I Need an API Key?

**Yes, if you want to use MemVerge:**
- MemVerge is a commercial cloud service
- You need to sign up and get an API key from MemVerge

### How to Get a MemVerge API Key

1. **Sign up for MemVerge Memory Machine Cloud:**
   - Visit: https://memverge.com/
   - Contact MemVerge for access to Memory Machine Cloud (MMC)
   - This is typically a commercial/enterprise product

2. **Get your API credentials:**
   - Once you have access, log into the MemVerge dashboard
   - Navigate to API keys/settings
   - Generate an API key

3. **Configure in `.env`:**
   ```bash
   MEMVERGE_API_ENDPOINT=https://mmc.memverge.com/api
   MEMVERGE_API_KEY=your-memverge-api-key-here
   MEMVERGE_PROJECT_ID=phoenix-agent
   ```

### Note About MemVerge

- MemVerge is **optional** - the system works without it
- It's used for the agent checkpoint/restore demo
- If you don't have access, the system will still function
- The code includes MemVerge integration but it's not required for basic operation

---

## 📋 Quick Reference

| Product | Type | API Key Needed? | Where to Get |
|---------|------|----------------|--------------|
| **MemMachine** | Open-source | ❌ No (for localhost) | N/A - runs locally |
| **MemVerge** | Commercial | ✅ Yes | https://memverge.com/ (contact for access) |

---

## 🎯 Recommended Setup

### For Development/Testing:

1. **Use MemMachine (no API key needed):**
   ```bash
   MEMMACHINE_ENABLED=true
   MEMMACHINE_BASE_URL=http://localhost:8080
   MEMMACHINE_API_KEY=  # Empty - not needed
   ```

2. **Skip MemVerge (optional):**
   - Don't configure MemVerge settings
   - The system will work fine without it
   - Agent checkpointing will be simulated instead

### For Production:

1. **MemMachine:** Same as development (or configure cloud instance if needed)
2. **MemVerge:** Contact MemVerge for enterprise access and API keys

---

## 🔍 Current Configuration Status

Check your `.env` file:

```bash
# MemMachine (Open-source, local)
MEMMACHINE_ENABLED=true
MEMMACHINE_BASE_URL=http://localhost:8080
MEMMACHINE_API_KEY=  # ✅ Can be empty for localhost

# MemVerge (Commercial, optional)
MEMVERGE_API_ENDPOINT=https://mmc.memverge.com/api
MEMVERGE_API_KEY=  # ⚠️ Only if you have MemVerge access
MEMVERGE_PROJECT_ID=phoenix-agent
```

---

## ❓ FAQ

### Q: Do I need both?

**A:** No! MemMachine is for persistent memory. MemVerge is for agent checkpointing. You can use one, both, or neither.

### Q: Can I use Phoenix Protocol without either?

**A:** Yes! The core functionality (Context Wallet, Neo4j, Chrome Extension) works without MemMachine or MemVerge.

### Q: Which one should I set up first?

**A:** 
- **MemMachine** - Easy to set up locally, no API key needed
- **MemVerge** - Requires commercial access, skip if you don't have it

### Q: I'm getting errors about missing API keys

**A:** 
- **MemMachine:** Make sure `MEMMACHINE_ENABLED=false` if you're not using it
- **MemVerge:** The code handles missing MemVerge gracefully - it's optional

---

## 📚 More Information

- **MemMachine Setup:** See `docs/MEMMACHINE-SETUP.md`
- **MemVerge Integration:** See `docs/04-BUILD-PHASE-4-MEMVERGE.md`
- **Running Guide:** See `RUNNING.md`

