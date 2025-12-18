# ⏱️ Build Timeline & Sprint Plan

This document provides realistic time estimates for building the Phoenix Protocol, with both a compressed hackathon schedule and a more relaxed development pace.

---

## Option A: 24-Hour Hackathon Sprint

### Hour-by-Hour Breakdown

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         24-HOUR HACKATHON SPRINT                           │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  HOURS 0-2: Foundation & Setup                                             │
│  ════════════════════════════                                              │
│  [██████████] Project structure, environment, basic FastAPI                │
│                                                                            │
│  HOURS 2-5: Neo4j Integration                                              │
│  ════════════════════════════                                              │
│  [██████████████████████████] Graph service, Cypher queries, API routes   │
│                                                                            │
│  HOURS 5-8: LangGraph Agent                                                │
│  ════════════════════════════                                              │
│  [██████████████████████████] State definition, nodes, graph compilation   │
│                                                                            │
│  HOURS 8-10: MemVerge Integration                                          │
│  ════════════════════════════                                              │
│  [██████████████████] Checkpoint service, restore logic                    │
│                                                                            │
│  HOURS 10-14: Frontend Dashboard                                           │
│  ════════════════════════════                                              │
│  [████████████████████████████████████████] React components, styling      │
│                                                                            │
│  HOURS 14-16: Integration & Bug Fixes                                      │
│  ════════════════════════════                                              │
│  [██████████████████] Connect all pieces, fix issues                       │
│                                                                            │
│  HOURS 16-18: Demo Data & Scenarios                                        │
│  ════════════════════════════                                              │
│  [██████████████████] Seed data, demo scripts                              │
│                                                                            │
│  HOURS 18-22: Polish & Testing                                             │
│  ════════════════════════════                                              │
│  [████████████████████████████████████████] UX polish, edge cases         │
│                                                                            │
│  HOURS 22-24: Demo Practice                                                │
│  ════════════════════════════                                              │
│  [██████████████████] Run demo 5+ times, prepare talking points           │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Sprint Details

#### Hours 0-2: Foundation (Phase 1)
- [ ] Create directory structure
- [ ] Set up `.env` configuration
- [ ] Install Python dependencies
- [ ] Create FastAPI skeleton with health checks
- [ ] Create Pydantic models for tuples and agent state
- [ ] Verify basic API runs

#### Hours 2-5: Neo4j (Phase 2)
- [ ] Set up Neo4j AuraDB instance
- [ ] Create graph schema and indexes
- [ ] Implement GraphService with basic CRUD
- [ ] Create Cypher query templates
- [ ] Implement conflict detection query
- [ ] Create `/api/graph/` routes
- [ ] Test with manual tuple ingestion

#### Hours 5-8: Agent (Phase 3)
- [ ] Define AgentState TypedDict
- [ ] Create neo4j_tools for agent
- [ ] Implement planner_node
- [ ] Implement executor_node
- [ ] Implement verifier_node
- [ ] Implement responder_node
- [ ] Compile LangGraph
- [ ] Create `/api/agent/` routes
- [ ] Test agent on simple task

#### Hours 8-10: MemVerge (Phase 4)
- [ ] Create MemVergeService skeleton
- [ ] Implement checkpoint creation (simulated)
- [ ] Implement restore logic
- [ ] Create `/api/memverge/` routes
- [ ] Add crash simulation endpoint
- [ ] Test checkpoint/restore flow

#### Hours 10-14: Frontend (Phase 5)
- [ ] Set up React + Vite + Tailwind
- [ ] Create API service layer
- [ ] Build GraphViewer component
- [ ] Build AgentBrain component
- [ ] Build CheckpointTimeline component
- [ ] Build DemoControls component
- [ ] Assemble App layout
- [ ] Style with dark theme

#### Hours 14-16: Integration
- [ ] Connect frontend to all APIs
- [ ] Test full flow: ingest → agent → checkpoint → crash → restore
- [ ] Fix CORS issues
- [ ] Fix any API mismatches
- [ ] Verify WebSocket updates (if time)

#### Hours 16-18: Demo Setup
- [ ] Create seed_graph.py with demo data
- [ ] Verify demo scenarios work:
  - Conflict resolution demo
  - Crash and restore demo
- [ ] Create demo_scenario.py scripts
- [ ] Prepare Neo4j visualization (optional)

#### Hours 18-22: Polish
- [ ] Add loading states
- [ ] Add error handling
- [ ] Improve animations
- [ ] Test on projector resolution
- [ ] Fix any visual issues
- [ ] Clean up console logs

#### Hours 22-24: Demo Practice
- [ ] Run full demo 5+ times
- [ ] Time each section
- [ ] Prepare for common questions
- [ ] Set up backup demos
- [ ] Rest before presentation

---

## Option B: 48-Hour Hackathon

### Day 1 (Hours 0-16)

**Morning (0-4)**: Foundation + Neo4j Setup
- Complete Phase 1 fully
- Set up Neo4j AuraDB
- Start Phase 2

**Afternoon (4-10)**: Neo4j + Agent Start
- Complete Phase 2
- Begin Phase 3 (Agent)

**Evening (10-16)**: Agent + MemVerge
- Complete Phase 3
- Complete Phase 4

*Sleep 6-8 hours*

### Day 2 (Hours 16-48)

**Morning (24-30)**: Frontend
- Complete Phase 5 (Frontend)

**Afternoon (30-38)**: Integration + Polish
- Full integration
- Bug fixes
- UI polish

**Evening (38-46)**: Demo Prep
- Demo data
- Demo practice
- Talking points

**Final (46-48)**: Rest + Final Check
- One final run-through
- Rest before presentation

---

## Option C: Week-Long Development

### Day 1-2: Foundation & Architecture
- Complete project setup
- Design all data models
- Set up CI/CD (optional)
- Complete Phase 1

### Day 3: Neo4j Integration
- Complete Phase 2
- Thorough testing
- Document Cypher queries

### Day 4: LangGraph Agent
- Complete Phase 3
- Test various scenarios
- Optimize prompts

### Day 5: MemVerge Integration
- Complete Phase 4
- Test with real MemVerge (if access)
- Document checkpointing behavior

### Day 6: Frontend Development
- Complete Phase 5
- Mobile responsiveness (optional)
- Accessibility check

### Day 7: Polish & Demo
- Integration testing
- Performance optimization
- Demo preparation
- Presentation practice

---

## Critical Path Items

These are the items that MUST work for the demo:

### Absolute Must-Haves (MVP)
1. ✅ Neo4j connection and basic queries
2. ✅ Agent runs and completes tasks
3. ✅ Conflict detection displays in UI
4. ✅ Checkpoint list shows in timeline
5. ✅ Crash button "kills" agent
6. ✅ Restore button "revives" agent
7. ✅ Graph visualization renders
8. ✅ Agent status updates in real-time

### Nice-to-Haves
- [ ] Real MemVerge integration (vs simulated)
- [ ] Chrome extension for ingestion
- [ ] WebSocket real-time updates
- [ ] Neo4j Bloom visualization
- [ ] Agent actually migrates between containers
- [ ] Multiple user profiles

---

## Resource Allocation (2-Person Team)

### Person A: Backend Focus
- Phase 1: Foundation
- Phase 2: Neo4j
- Phase 3: Agent (core logic)
- Phase 4: MemVerge

### Person B: Frontend Focus
- Phase 1: Help with models
- Phase 3: Agent API routes
- Phase 5: Frontend (all)
- Integration: API connections

### Both Together
- Integration testing
- Demo scenarios
- Presentation practice

---

## Risk Mitigation

### If Neo4j Is Slow
- Use local Neo4j Community instead of AuraDB
- Pre-cache common queries
- Reduce graph visualization scope

### If Agent Is Buggy
- Fallback to simpler task flow
- Pre-compute demo responses
- Have manual override ready

### If MemVerge Doesn't Work
- Simulate with local file checkpoints
- Mock the API responses
- Focus demo on the concept

### If Frontend Breaks
- Have Postman/curl demos ready
- Show Neo4j Bloom as backup viz
- Terminal-based demo as last resort

---

## Pre-Submission Checklist

```bash
# 1 hour before submission:
[ ] All services start with docker-compose up
[ ] Demo works end-to-end 3 times in a row
[ ] README is complete
[ ] No hardcoded API keys in code
[ ] Video recording done (if required)
[ ] Submission form ready
[ ] Team members listed

# 10 minutes before presentation:
[ ] Services running
[ ] Browser at dashboard
[ ] Terminal ready
[ ] Backup laptop ready
[ ] Water bottle nearby
[ ] Demo script printed
```

---

## Post-Hackathon Roadmap

If you win (or want to continue):

### Week 1-2: Production Hardening
- Real MemVerge integration
- Proper authentication
- Error handling
- Logging and monitoring

### Week 3-4: Features
- Chrome extension
- MCP server integration
- Multi-user support
- Mobile app

### Month 2: Scale
- Distributed agent architecture
- Multi-cloud deployment
- Enterprise security
- API documentation

---

*Remember: A working demo beats a perfect architecture. Ship something impressive, not something complete.*

