# 🎬 Demo Script: "The Phoenix Protocol"

**Total Demo Time: 5-7 minutes**

This is your choreographed demo script designed to hit both sponsor judging criteria perfectly.

---

## Pre-Demo Checklist

```bash
# 30 minutes before demo:
[ ] Context Router running (localhost:8787)
[ ] Chrome Extension loaded (unpacked)
[ ] Wallet seeded with demo Memory Cards
[ ] Neo4j seeded with demo data
[ ] Browser open to ChatGPT/Claude
[ ] Extension popup accessible
[ ] Terminal ready for dramatic commands

# Test each component:
curl http://127.0.0.1:8787/health
curl -X POST http://127.0.0.1:8787/api/context-pack \
  -d '{"draft_prompt":"Book dinner","site_id":"chatgpt","persona":"Personal"}'
```

---

## Opening Hook (30 seconds)

### What to Say:

> "Every AI chatbot today has the memory of a goldfish. Tell it your budget on Monday, it forgets by Tuesday. You have to repeat your constraints every single conversation."
>
> "We built **Phoenix Protocol**: a Chrome extension that makes your AI remember who you are—automatically, invisibly, magically."

### What to Show:

- Chrome browser open to ChatGPT
- Extension icon visible in toolbar
- Wallet UI showing a few Memory Cards
- Dramatic pause

---

## Act 1: The Magic Injection (Chrome Extension + Neo4j) — 2.5 minutes

**Goal: Demonstrate automatic context injection with conflict resolution**

### Setup Narration:

> "Let me show you the magic. I have a Context Wallet with a few Memory Cards: 'No red meat (hard constraint)' and 'Budget $50/month (soft preference)'. I also have a historical preference: 'Likes Steakhouse X'."

### Action 1: Show the Wallet

1. **Open Extension Popup**
   - "Here's my Context Wallet. These are my Memory Cards—constraints, preferences, goals."
   - Point to: "No red meat (hard)", "Budget $50/month (soft)", "Likes Steakhouse X (preference)"
   - "Notice the conflict: I like Steakhouse X, but I have a hard constraint against red meat."

### Action 2: The Magic Injection

2. **Open ChatGPT in browser**
   - "Now watch. I'm going to type normally in ChatGPT, just like any user would."

3. **Type in ChatGPT textbox:**
   > "Book me a dinner reservation for tonight"

4. **Before sending, point to extension:**
   - "The extension intercepted my prompt. It called the Context Router, which queried Neo4j for conflict resolution..."

5. **Show the injected context** (if visible, or explain):
   - "Look at what was actually sent to ChatGPT:"
   - ```
     CONTEXT (apply quietly):
     - Hard: No red meat
     - Soft: Budget $50/month
     - Preference suppressed: Steakhouse X (conflict with constraint)
     
     Book me a dinner reservation for tonight
     ```

6. **Show the UI chip:**
   - "See this chip? 'Using: No red meat • Budget-first'. The user always knows what context was injected."

7. **ChatGPT responds:**
   - "I've booked Sushi Place Y for tonight. It respects your no red meat diet and fits your $50 budget."

### Key Quote for Neo4j Judges:

> "This isn't just retrieval. This is **reasoning over relationships**. Neo4j detected that the hard constraint 'No red meat' conflicts with the preference 'Likes Steakhouse X', and the constraint wins. The graph computed the 'winning rules' before the prompt even reached ChatGPT."

---

## Transition (15 seconds)

> "So that's the magic injection—you never have to repeat yourself. The extension, the Context Router, and Neo4j work together invisibly. But we also built something else: an immortal agent that can crash and resume mid-thought. Let me show you."

*Pause dramatically*

---

## Act 2: The Immortal Agent (MemVerge) — 2 minutes

**Goal: Demonstrate checkpoint/restore of execution state**

### Setup Narration:

> "For long-running tasks, we have an Agent Orchestrator that uses the same Context Pack API. MemVerge lets us checkpoint its *live thought process* and restore it instantly."

### Action 1: Start a Long Task

1. **Open dashboard or use API:**
   > "Plan a 7-step trip itinerary within my constraints"

2. **Narrate as it runs:**
   > "This is a complex multi-step task. The agent loads context from the same Router, plans steps, executes... notice the checkpoints accumulating."

3. **Point to the Checkpoint Timeline:**
   > "Every 30 seconds, MemVerge snapshots the entire RAM state. Not just the data—the *execution state*."

### Action 2: THE CRASH (Most Important Moment)

4. **Wait until agent is at step 3-4 out of ~7**
   > "The agent is at step 4. It's mid-analysis. And now..."

5. **Click the CRASH button** (or run in terminal):
   ```bash
   curl -X POST http://localhost:8000/api/memverge/simulate-crash
   ```

6. **React dramatically:**
   > "The server just died. In any normal system, that's 10 minutes of work—gone. The user would have to start over."

7. **Point to the dashboard:**
   > "Status: CRASHED. But look at the checkpoints..."

### Action 3: THE RESURRECTION

8. **Click "Restore (Phoenix!)" button**

9. **Narrate the magic:**
   > "MemVerge is restoring the full memory image... and..."

10. **When agent resumes:**
    > "The agent is BACK. Look: Step 4 of 7. It didn't restart—it *continued*. Its train of thought was frozen in time and restored."

### Key Quote for MemVerge Judges:

> "This isn't just saving data. This is **persisting cognition**. The agent's working memory—intermediate calculations, decision trees, everything in RAM—was captured and restored. This is true agent immortality."

---

## Act 3: The Synthesis (30 seconds)

### Bring It Together:

> "Let me show you one more example of the magic."

1. **Type in ChatGPT again:**
   > "Order me vegan protein powder within my budget"

2. **Narrate quickly:**
   > "The extension injects: 'Hard: Vegan | Soft: Budget $50/month'. ChatGPT responds perfectly—no repetition, no reminders. The Context Router used Neo4j to ensure no conflicts."

### Final Visual:

- Point to extension: "This is the magic—invisible, automatic."
- Point to wallet: "This is your memory—local, encrypted, yours."
- Point to Neo4j (if showing): "This is the reasoning—relationships, not just keywords."
- Point to checkpoints (if showing): "And this is immortality—for long-running agents."

---

## Closing (30 seconds)

> "We call this the **Phoenix Protocol** because your context rises from the wallet—every time you chat."
>
> "The Chrome Extension makes it invisible. Neo4j makes it smart—resolving conflicts using relationships, not just keywords."
>
> "And MemVerge makes agents immortal—for when you need long-running tasks that survive crashes."
>
> "Together, they create something new: an AI that truly knows you and never forgets—without you having to remind it."

*Pause*

> "Thank you. Happy to take questions."

---

## Backup Demos (If Time / Questions)

### If Asked About Scale:
> "The graph can hold millions of relationships. Neo4j is web-scale. MemVerge is designed for Big Memory workloads—we're just scratching the surface."

### If Asked About Privacy:
> "The distiller runs locally using Ollama. Your raw data never leaves your machine—only structured tuples go to the graph."

### If Asked About Real Use Cases:
> "Personal AI assistants, customer service bots that remember context across sessions, healthcare agents that must maintain state through interruptions..."

---

## Technical Talking Points

### For Neo4j Questions:
- "We use Cypher queries to traverse relationships"
- "Conflict resolution is graph logic, not LLM guessing"
- "GraphRAG filters options *before* they reach the LLM"
- "The schema enforces semantic structure"

### For MemVerge Questions:
- "Checkpoints are full RAM images, not just serialized state"
- "Restore is sub-second—the process doesn't know it died"
- "This enables agent migration between clouds"
- "In production, checkpoints go to S3 or object storage"

---

## Demo God Principles

1. **Never apologize for bugs.** If something fails, say "Let me show you the recovery..." and restore.

2. **Use the crash deliberately.** The crash IS the demo. Make it dramatic.

3. **Speak to the judges' interests:**
   - Neo4j judges: "relationships," "graph traversal," "conflict resolution"
   - MemVerge judges: "RAM state," "instant recovery," "checkpoint," "Big Memory"

4. **Tell a story, not a feature list.** The user has preferences AND constraints. They conflict. The graph resolves it. The agent thinks about it. It crashes. It rises.

5. **End with emotion.** "Immortal." "Never forgets." "Rises from the ashes."

---

## Emergency Recovery

If the demo breaks:

```bash
# Quick restart
docker-compose restart api agent

# Reseed data
python scripts/seed_graph.py

# Manual checkpoint for recovery demo
curl -X POST http://localhost:8000/api/memverge/checkpoint \
  -d '{"container_id":"phoenix-agent","step_number":5,"total_steps":10,"task_description":"Demo task"}'
```

If all else fails:
> "As you can see, even our demo infrastructure crashed—but with Phoenix Protocol, we'd just restore. That's the whole point."

*Never panic. The crash is your friend.*

