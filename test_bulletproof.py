"""Bulletproof test - writes to both console and log file"""
import sys
import os
from datetime import datetime

# Create log file
log_file = open('test_output.log', 'w', encoding='utf-8')

def log(msg):
    """Write to both console and log file"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    sys.stdout.flush()
    log_file.write(full_msg + "\n")
    log_file.flush()

try:
    log("="*70)
    log("BULLETPROOF TEST - Logs to test_output.log")
    log("="*70)
    
    log("")
    log("Step 1/7: Importing pandas...")
    import pandas as pd
    log("✓ Pandas imported successfully")
    log(f"  Version: {pd.__version__}")
    
    log("")
    log("Step 2/7: Loading CSV file...")
    csv_path = 'data/preloaded/fmb_bank/customers.csv'
    log(f"  Path: {csv_path}")
    df = pd.read_csv(csv_path, engine='python')
    log(f"✓ CSV loaded: {len(df)} rows, {len(df.columns)} columns")
    
    log("")
    log("Step 3/7: Checking monthly_transaction_volume column...")
    if 'monthly_transaction_volume' in df.columns:
        min_val = df['monthly_transaction_volume'].min()
        max_val = df['monthly_transaction_volume'].max()
        avg_val = df['monthly_transaction_volume'].mean()
        log(f"✓ Column exists!")
        log(f"  Min: {min_val:.0f}")
        log(f"  Max: {max_val:.0f}")
        log(f"  Avg: {avg_val:.1f}")
    else:
        log("❌ Column NOT FOUND!")
        log(f"  Available: {list(df.columns[:10])}")
        raise ValueError("monthly_transaction_volume not found")
    
    log("")
    log("Step 4/7: Importing agent class...")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced
    log("✓ Agent class imported successfully")
    
    log("")
    log("Step 5/7: Initializing agent...")
    agent = AgentA_Banking_Enhanced(data_path='data/preloaded/fmb_bank')
    log("✓ Agent initialized with correct data path")
    
    log("")
    log("Step 6/7: Running segmentation...")
    log("  This will take 30-60 seconds, please wait...")
    params = {'n_clusters': 5}
    result = agent.execute(params)
    
    if 'error' in result:
        log(f"❌ Agent error: {result['error']}")
        raise RuntimeError(result['error'])
    
    log(f"✓ Segmentation completed successfully!")
    log(f"  Generated {len(result['personas'])} personas")
    
    log("")
    log("Step 7/7: Validating results...")
    log("")
    log("Segment Details:")
    log("-" * 70)
    
    all_valid = True
    for cluster_id, persona in result['personas'].items():
        name = persona['persona_name']
        word_count = len(name.split())
        size = persona['size']
        monthly_txn = persona['characteristics'].get('avg_monthly_transaction_volume', 0)
        
        valid = word_count <= 2 and 10 <= monthly_txn <= 800
        status = "✅" if valid else "❌"
        
        log(f"{cluster_id}. {name}")
        log(f"   Words: {word_count} | Size: {size} | Txns/mo: {monthly_txn:.1f} {status}")
        
        if not valid:
            all_valid = False
    
    log("-" * 70)
    log("")
    
    if all_valid:
        log("="*70)
        log("🎉 ALL TESTS PASSED!")
        log("="*70)
        log("")
        log("✅ All segment names are short (≤2 words)")
        log("✅ All transaction volumes in range (10-800/month)")
        log("✅ Segmentation working correctly")
    else:
        log("="*70)
        log("❌ SOME TESTS FAILED")
        log("="*70)
        log("Check details above")
    
    log("")
    log("Test completed. Check test_output.log for full details.")
    
except Exception as e:
    log("")
    log("="*70)
    log(f"❌ ERROR: {type(e).__name__}: {e}")
    log("="*70)
    import traceback
    for line in traceback.format_exc().split('\n'):
        log(line)
    
finally:
    log_file.close()
    print("\n" + "="*70)
    print("Test output saved to: test_output.log")
    print("="*70)
    input("\nPress Enter to exit...")
