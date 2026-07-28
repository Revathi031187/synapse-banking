"""Absolutely minimal test"""
print("START", flush=True)

try:
    print("Importing pandas...", flush=True)
    import pandas as pd
    print(f"OK - pandas {pd.__version__}", flush=True)
    
    print("Loading CSV...", flush=True)
    df = pd.read_csv('data/preloaded/fmb_bank/customers.csv', engine='python')
    print(f"OK - {len(df)} rows, {len(df.columns)} columns", flush=True)
    
    print("Checking column...", flush=True)
    if 'monthly_transaction_volume' in df.columns:
        print(f"OK - column exists, range {df['monthly_transaction_volume'].min():.0f}-{df['monthly_transaction_volume'].max():.0f}", flush=True)
    else:
        print("ERROR - column not found", flush=True)
    
    print("ALL BASIC CHECKS PASSED", flush=True)
    
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()

print("END", flush=True)
input("Press Enter...")
