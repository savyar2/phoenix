"""
Phoenix Protocol - Crash and Restore Demo

This script demonstrates the MemVerge integration:
1. Starts a long-running agent task
2. Waits until it's partway through
3. Simulates a crash
4. Restores from checkpoint
5. Shows the agent continuing from where it left off
"""
import asyncio
import httpx
from datetime import datetime

API_BASE = "http://localhost:8787"  # Router port


async def run_demo():
    """Run the crash and restore demo."""
    
    print("\n" + "="*70)
    print("🔥 PHOENIX PROTOCOL - IMMORTAL AGENT DEMO")
    print("="*70)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Step 1: Start a long-running task
        print("\n📝 Step 1: Starting a complex agent task...")
        print("   Task: 'Analyze 50 transactions and create a spending report'")
        
        # First, create some checkpoints to simulate progress
        print("\n   Creating initial checkpoints to simulate agent progress...")
        
        for step in range(1, 6):
            try:
                response = await client.post(
                    f"{API_BASE}/api/memverge/checkpoint",
                    json={
                        "container_id": "phoenix-agent",
                        "step_number": step,
                        "total_steps": 10,
                        "task_description": "Analyze 50 transactions and create a spending report with trends"
                    }
                )
                if response.status_code == 200:
                    checkpoint = response.json()
                    print(f"   ✅ Checkpoint {step}/10 created: {checkpoint['checkpoint']['checkpoint_id']}")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"   ⚠️  Checkpoint creation failed: {e}")
        
        # Step 2: Let it run and checkpoint
        print("\n⏳ Step 2: Agent is working... (checkpoints every 30s)")
        
        # Check status
        try:
            ckpt_resp = await client.get(f"{API_BASE}/api/memverge/checkpoints")
            checkpoints = ckpt_resp.json()["checkpoints"]
            
            print(f"   Progress: {len(checkpoints)} checkpoints created")
            if checkpoints:
                latest = checkpoints[0]
                print(f"   Latest: Step {latest['step_number']}/{latest['total_steps']}")
                print(f"   Task: {latest['task_description']}")
        except Exception as e:
            print(f"   ⚠️  Status check failed: {e}")
        
        # Step 3: Simulate crash
        print("\n💥 Step 3: SIMULATING CRASH!")
        print("   (In production, this would kill the Docker container)")
        
        try:
            crash_resp = await client.post(
                f"{API_BASE}/api/memverge/simulate-crash",
                json={"container_id": "phoenix-agent"}
            )
            crash_result = crash_resp.json()
            print(f"   {crash_result['message']}")
        except Exception as e:
            print(f"   ⚠️  Crash simulation failed: {e}")
        
        # Dramatic pause
        print("\n   ☠️  Agent is DOWN")
        await asyncio.sleep(2)
        
        # Step 4: Show available checkpoints
        print("\n📸 Step 4: Available checkpoints:")
        try:
            ckpt_resp = await client.get(f"{API_BASE}/api/memverge/checkpoints")
            checkpoints = ckpt_resp.json()["checkpoints"]
            
            for ckpt in checkpoints:
                print(f"   - {ckpt['checkpoint_id']}")
                print(f"     Step: {ckpt['step_number']}/{ckpt['total_steps']}")
                print(f"     Time: {ckpt['timestamp']}")
            
            if not checkpoints:
                print("   ⚠️  No checkpoints found (demo may have run too fast)")
                return
        except Exception as e:
            print(f"   ⚠️  Failed to list checkpoints: {e}")
            return
        
        # Step 5: Restore from latest checkpoint
        print("\n🔄 Step 5: RESTORING FROM CHECKPOINT...")
        print("   Using MemVerge to restore agent state...")
        
        try:
            restore_resp = await client.post(
                f"{API_BASE}/api/memverge/restore",
                json={"checkpoint_id": None}  # Latest
            )
            restore_result = restore_resp.json()
            
            print(f"\n   ✅ AGENT RESTORED!")
            print(f"   Restored to step: {restore_result['restored_step']}/{restore_result['total_steps']}")
            print(f"   Task: {restore_result['task']}")
            print(f"\n   🔥 The agent is IMMORTAL! It continued exactly where it left off.")
        except Exception as e:
            print(f"   ⚠️  Restore failed: {e}")
            return
        
        # Step 6: Show agent continuing
        print("\n⏩ Step 6: Agent continues working...")
        print("   (In a real scenario, the agent would resume execution)")
        
        # Create a few more checkpoints to show continuation
        for step in range(6, 11):
            try:
                await asyncio.sleep(1)
                response = await client.post(
                    f"{API_BASE}/api/memverge/checkpoint",
                    json={
                        "container_id": "phoenix-agent",
                        "step_number": step,
                        "total_steps": 10,
                        "task_description": "Analyze 50 transactions and create a spending report with trends"
                    }
                )
                if response.status_code == 200:
                    print(f"   Progress: Step {step}/10 completed")
            except Exception as e:
                print(f"   ⚠️  Checkpoint failed: {e}")
        
        print("\n   ✅ Task completed!")
        
        print("\n" + "="*70)
        print("🎉 DEMO COMPLETE - The Phoenix has risen!")
        print("="*70)


if __name__ == "__main__":
    print("\nThis demo shows MemVerge checkpoint/restore capabilities.")
    print("Make sure the API server is running on localhost:8787\n")
    
    try:
        input("Press Enter to start the demo...")
    except KeyboardInterrupt:
        print("\nDemo cancelled.")
        exit(0)
    
    asyncio.run(run_demo())

