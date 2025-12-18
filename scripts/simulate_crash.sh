#!/bin/bash
# Simulate a crash by killing the agent container

echo "💥 Simulating agent crash..."
echo ""

# Option 1: Use API
curl -X POST http://localhost:8787/api/memverge/simulate-crash \
  -H "Content-Type: application/json" \
  -d '{"container_id": "phoenix-agent", "delay_seconds": 0}'

# Option 2: Direct Docker kill (uncomment if needed)
# docker kill phoenix-agent

echo ""
echo "Agent crashed. Run restore to bring it back:"
echo "  curl -X POST http://localhost:8787/api/memverge/restore -H 'Content-Type: application/json' -d '{}'"

