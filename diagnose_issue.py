"""Diagnose why scripts are failing silently"""
import sys
import traceback

print("="*70, flush=True)
print("DIAGNOSTIC SCRIPT - Finding the issue", flush=True)
print("="*70, flush=True)

try:
    print("\n1. Testing pandas import...", flush=True)
    import pandas as pd
    print("   ✓ pandas imported successfully", flush=True)
    
    print("\n2. Testing CSV file existence...", flush=True)
    from pathlib import Path
    csv_path = Path('data/preloaded/fmb_bank/customers.csv')
    print(f"   File exists: {csv_path.exists()}", flush=True)
    print(f"   Absolute path: {csv_path.absolute()}", flush=True)
    
    print("\n3. Testing CSV read with engine='python'...", flush=True)
    df = pd.read_csv(csv_path, engine='python')
    print(f"   ✓ CSV loaded: {len(df)} rows, {len(df.columns)} columns", flush=True)
    print(f"   ✓ 'monthly_transaction_volume' exists: {'monthly_transaction_volume' in df.columns}", flush=True)
    
    print("\n4. Testing agent import...", flush=True)
    sys.path.append('.')
    from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced
    print("   ✓ Agent imported successfully", flush=True)
    
    print("\n5. Testing agent initialization...", flush=True)
    agent = AgentA_Banking_Enhanced()
    print("   ✓ Agent initialized", flush=True)
    
    print("\n" + "="*70, flush=True)
    print("✅ ALL DIAGNOSTICS PASSED!", flush=True)
    print("="*70, flush=True)
    
except Exception as e:
    print(f"\n❌ ERROR FOUND:", flush=True)
    print(f"   {type(e).__name__}: {e}", flush=True)
    print("\nFull traceback:", flush=True)
    traceback.print_exc()
    sys.exit(1)
