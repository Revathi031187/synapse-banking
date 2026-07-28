"""Test agent import only - no execution"""
import sys
import os

print("="*70, flush=True)
print("TEST: Import Agent Only (No Execution)", flush=True)
print("="*70, flush=True)

try:
    print("\nStep 1: Adding project to path...", flush=True)
    project_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_dir)
    print(f"✓ Added: {project_dir}", flush=True)
    
    print("\nStep 2: Importing agent module...", flush=True)
    from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced
    print("✓ Agent module imported successfully!", flush=True)
    
    print("\nStep 3: Creating agent instance...", flush=True)
    agent = AgentA_Banking_Enhanced(data_path='data/preloaded/fmb_bank')
    print("✓ Agent instance created successfully!", flush=True)
    
    print("\n" + "="*70, flush=True)
    print("🎉 AGENT IMPORT TEST PASSED!", flush=True)
    print("="*70, flush=True)
    print("\nAgent is ready. Next: Run full segmentation test.", flush=True)
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}", flush=True)
    import traceback
    print("\nFull traceback:", flush=True)
    traceback.print_exc()

input("\nPress Enter to exit...")
