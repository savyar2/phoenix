"""
Phoenix Protocol - Demo Scenario Runner

This script runs the key demo scenarios for the hackathon presentation.
"""
import asyncio
import httpx
from datetime import datetime

API_BASE = "http://localhost:8787"


async def demo_conflict_resolution():
    """
    Demo 1: Show Neo4j conflict resolution
    
    Scenario: User asks for dinner reservation
    - User historically likes Steakhouse X
    - User recently started a "No Red Meat" diet
    - Graph should detect conflict and suggest alternative
    """
    print("\n" + "="*60)
    print("🥩 DEMO 1: Conflict Resolution (Neo4j Showcase)")
    print("="*60)
    
    # Start the task
    print("\n📝 Task: 'Book me a dinner reservation for tonight'")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/api/agent/start",
            json={
                "task": "Book me a dinner reservation for tonight",
                "user_id": "demo_user"
            }
        )
        session = response.json()
        session_id = session["session_id"]
        print(f"   Session started: {session_id}")
        
        # Poll for completion
        while True:
            await asyncio.sleep(2)
            status_response = await client.get(f"{API_BASE}/api/agent/status/{session_id}")
            status = status_response.json()
            
            print(f"   Status: {status['status']} - Step {status['current_step']}/{status['total_steps']}")
            
            if status["conflict_detected"]:
                print("\n🔴 CONFLICT DETECTED!")
                print(f"   {status['conflict_detected']}")
            
            if status["status"] in ["completed", "failed"]:
                break
        
        print("\n✅ Final Response:")
        print(f"   {status.get('final_response', 'No response')}")


async def demo_long_running_task():
    """
    Demo 2: Prepare for MemVerge crash/restore demo
    
    Scenario: Start a long-running task that will be "crashed"
    """
    print("\n" + "="*60)
    print("📊 DEMO 2: Long-Running Task (MemVerge Showcase Prep)")
    print("="*60)
    
    task = "Analyze my last 100 purchases and create a spending report with trends"
    
    print(f"\n📝 Task: '{task}'")
    print("   This task will take multiple steps...")
    print("   (We'll 'crash' the agent mid-way to demo MemVerge)")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/api/agent/start",
            json={
                "task": task,
                "user_id": "demo_user"
            }
        )
        session = response.json()
        session_id = session["session_id"]
        print(f"   Session started: {session_id}")
        
        # Show a few steps, then we'll "crash" it
        for i in range(5):
            await asyncio.sleep(3)
            status_response = await client.get(f"{API_BASE}/api/agent/status/{session_id}")
            status = status_response.json()
            
            print(f"   Step {status['current_step']}/{status['total_steps']}: {status['status']}")
            
            if i == 2:
                print("\n💥 SIMULATING CRASH... (Ctrl+C or kill the container)")
                print("   The agent is at step 3. MemVerge has checkpoints.")
                print("   Run the restore demo to bring it back!")
                break


if __name__ == "__main__":
    print("🔥 PHOENIX PROTOCOL - DEMO SCENARIOS")
    print("Choose a demo:")
    print("1. Conflict Resolution (Neo4j)")
    print("2. Long-Running Task (MemVerge prep)")
    
    choice = input("\nEnter 1 or 2: ").strip()
    
    if choice == "1":
        asyncio.run(demo_conflict_resolution())
    elif choice == "2":
        asyncio.run(demo_long_running_task())
    else:
        print("Invalid choice")

