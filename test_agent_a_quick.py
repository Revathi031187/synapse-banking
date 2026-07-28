"""Quick test of Agent A with num_products fix"""
import sys
sys.path.append('.')

from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced

print("=" * 70)
print("Testing Agent A with num_products fix")
print("=" * 70)

# Initialize agent
agent = AgentA_Banking_Enhanced(data_path='data/preloaded/banking_nba')

# Load data
print("\n1. Loading data...")
success = agent.load_data()
print(f"   Load successful: {success}")

if success:
    print(f"   Loaded {len(agent.customers_df)} customers")
    
    # Check if num_products exists
    if 'num_products' in agent.customers_df.columns:
        print(f"   ✅ num_products column exists!")
        print(f"   Sample values: {agent.customers_df['num_products'].head().tolist()}")
        print(f"   Mean products per customer: {agent.customers_df['num_products'].mean():.2f}")
    else:
        print(f"   ❌ num_products column MISSING!")
    
    # Execute clustering
    print("\n2. Executing clustering...")
    result = agent.execute({'n_clusters': 5})
    
    if 'error' in result:
        print(f"   ❌ ERROR: {result['error']}")
    else:
        print(f"   ✅ SUCCESS!")
        print(f"   Generated {len(result.get('personas', {}))} personas")
        for pid, persona in result.get('personas', {}).items():
            print(f"      - {persona['persona_name']} ({persona['size']} customers)")

print("\n" + "=" * 70)
