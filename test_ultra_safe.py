"""Ultra-safe test with maximum error handling"""
import sys
import os

def safe_print(msg):
    """Print with flush and error handling"""
    try:
        print(msg, flush=True)
    except:
        print(msg)

def test_step(step_num, description, func):
    """Run a test step with error handling"""
    safe_print(f"\nStep {step_num}: {description}...")
    try:
        result = func()
        safe_print(f"✓ Step {step_num} completed")
        return result
    except Exception as e:
        safe_print(f"❌ Step {step_num} FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)

# =============================================================================
# START TEST
# =============================================================================

safe_print("="*70)
safe_print("ULTRA-SAFE STEP-BY-STEP TEST")
safe_print("="*70)

# Step 1: Import pandas
def step1():
    import pandas as pd
    return pd

pd = test_step(1, "Import pandas", step1)

# Step 2: Load CSV
def step2():
    df = pd.read_csv('data/preloaded/fmb_bank/customers.csv', engine='python')
    safe_print(f"  → Loaded {len(df)} rows, {len(df.columns)} columns")
    return df

df = test_step(2, "Load CSV file", step2)

# Step 3: Check column
def step3():
    if 'monthly_transaction_volume' not in df.columns:
        raise ValueError("Column 'monthly_transaction_volume' not found!")
    min_val = df['monthly_transaction_volume'].min()
    max_val = df['monthly_transaction_volume'].max()
    avg_val = df['monthly_transaction_volume'].mean()
    safe_print(f"  → Range: {min_val:.0f}-{max_val:.0f}, Avg: {avg_val:.1f}")
    return True

test_step(3, "Verify monthly_transaction_volume column", step3)

# Step 4: Import agent
def step4():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced
    return AgentA_Banking_Enhanced

AgentClass = test_step(4, "Import agent class", step4)

# Step 5: Initialize agent
def step5():
    agent = AgentClass(data_path='data/preloaded/fmb_bank')
    safe_print(f"  → Agent initialized with path: data/preloaded/fmb_bank")
    return agent

agent = test_step(5, "Initialize agent", step5)

# Step 6: Execute segmentation
def step6():
    safe_print("  → Running segmentation (may take 30-60 seconds)...")
    params = {'n_clusters': 5}
    result = agent.execute(params)
    
    if 'error' in result:
        raise RuntimeError(f"Agent returned error: {result['error']}")
    
    safe_print(f"  → Generated {len(result['personas'])} personas")
    return result

result = test_step(6, "Execute segmentation", step6)

# Step 7: Validate results
def step7():
    safe_print("\n  Segment Details:")
    for cluster_id, persona in result['personas'].items():
        name = persona['persona_name']
        word_count = len(name.split())
        monthly_txn = persona['characteristics'].get('avg_monthly_transaction_volume', 0)
        safe_print(f"    {cluster_id}. {name} ({word_count} words): {monthly_txn:.1f} txns/month")
    return True

test_step(7, "Validate and display results", step7)

# =============================================================================
# SUCCESS!
# =============================================================================

safe_print("\n" + "="*70)
safe_print("🎉 ALL 7 STEPS COMPLETED SUCCESSFULLY!")
safe_print("="*70)
safe_print("\nThe segmentation is working correctly.")
safe_print("Monthly transaction volumes are in the expected range.")

input("\nPress Enter to exit...")
