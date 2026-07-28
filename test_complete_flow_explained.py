"""
Complete Test: Macro Segments → Micro Segments → Agent B Recommendations
Shows all classification factors and tests the complete flow
"""
import sys
sys.path.append('.')

print("="*80)
print("🧪 COMPLETE BANKING FLOW TEST")
print("="*80)

# ============================================================================
# PART 1: MACRO SEGMENTATION (Agent A)
# ============================================================================
print("\n📊 PART 1: MACRO SEGMENTATION (Agent A)")
print("-"*80)

from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced

agent_a = AgentA_Banking_Enhanced(data_path='data/preloaded/fmb_bank')
print("✓ Agent A loaded\n")

print("🔄 Running K-Prototypes clustering...")
print("\n📋 CLUSTERING FACTORS (Macro):")
print("   PRIMARY (2x weight):")
print("     • total_deposits (wealth tier)")
print("     • monthly_transaction_volume (activity)")
print("     • cross_sell_receptivity (willingness)")
print("     • num_products (relationship depth)")
print("     • digital_engagement_score (channel)")
print("   SECONDARY:")
print("     • product_adoption_velocity")
print("     • income, credit_score")
print("     • customer_value_score, digital_adoption, financial_health")
print("   CATEGORICAL:")
print("     • risk_tolerance, channel_preference, geographic_region")
print("     • home_ownership, life_stage")

result_a = agent_a.execute({'n_clusters': 5, 'gamma': 0.5})

if 'error' in result_a:
    print(f"❌ Error: {result_a['error']}")
    sys.exit(1)

print(f"\n✅ Generated {len(result_a['personas'])} MACRO segments:\n")

for pid, persona in result_a['personas'].items():
    print(f"{persona['emoji']} {persona['persona_name']}")
    print(f"   {persona['size']:,} customers | ${persona['avg_balance']:,.0f} | {persona['avg_transactions']:.1f} txns | {persona['avg_intent_score']*100:.0f}% intent")
    print()

# ============================================================================
# PART 2: MICRO SEGMENTATION (Agent A Micro)
# ============================================================================
print("\n📊 PART 2: MICRO SEGMENTATION (Agent A Micro)")
print("-"*80)

from agents.agent_a_banking_micro import AgentA_Banking_Micro

# Test on first macro segment
test_macro_id = list(result_a['personas'].keys())[0]
test_persona = result_a['personas'][test_macro_id]

print(f"\n🎯 Creating micro segments for: {test_persona['persona_name']}")
print(f"   ({test_persona['size']} customers)")

print("\n📋 MICRO CLUSTERING FACTORS:")
print("     • digital_engagement (online/mobile usage)")
print("     • portfolio_depth (number of products)")
print("     • credit_utilization (borrowing behavior)")
print("     • transaction_velocity (activity frequency)")
print("     • account_maturity (tenure)")
print("     • cross_sell_receptivity (openness to offers)")

agent_micro = AgentA_Banking_Micro(
    customers_df=result_a['customers_df'],
    macro_personas=result_a['personas']
)

result_micro = agent_micro.execute(test_macro_id, n_micro_segments=4)

if 'error' in result_micro:
    print(f"❌ Error: {result_micro['error']}")
else:
    print(f"\n✅ Generated {len(result_micro['micro_segments'])} MICRO segments:\n")
    for micro in result_micro['micro_segments']:
        print(f"   • {micro['name']}")
        print(f"     {micro['size']} customers | {micro['ltv_tier']} tier | ${micro['avg_balance']:,.0f}")

# ============================================================================
# PART 3: AGENT B RECOMMENDATIONS (Rule-Based + ML)
# ============================================================================
print("\n\n📊 PART 3: AGENT B RECOMMENDATIONS")
print("-"*80)

from agents.agent_b_banking_rule_based import AgentB_Banking_RuleBased

agent_b = AgentB_Banking_RuleBased(
    customers_df=result_a['customers_df'],
    products_df=agent_a.products_df,
    transactions_df=agent_a.transactions_df,
    personas=result_a['personas'],
    data_path='data/preloaded/fmb_bank'
)

# Get test customer
test_customer_id = result_a['customers_df'].iloc[100]['customer_id']  # Pick customer 100
test_customer = result_a['customers_df'].iloc[100]

print(f"\n🧪 Testing recommendations for:")
print(f"   Customer ID: {test_customer_id}")
print(f"   Name: {test_customer.get('customer_name', 'Unknown')}")
print(f"   Deposits: ${test_customer.get('total_deposits', 0):,.0f}")
print(f"   Products: {test_customer.get('num_products', 0)}")
print(f"   Credit Score: {test_customer.get('credit_score', 0):.0f}")
print(f"   Intent: {test_customer.get('intent_score', 0)*100:.0f}%")
print(f"   Cluster: {test_customer.get('cluster', 'Unknown')}")

print("\n📋 AGENT B SCORING FACTORS:")
print("   RULE-BASED (50%):")
print("     • Eligibility (25%): credit score, income, balance requirements")
print("     • Segment Match (20%): Personal/Business/Agricultural")
print("     • Financial Need (20%): product addresses customer need")
print("     • Relationship Depth (15%): existing products, tenure")
print("     • Intent Score (10%): cross-sell receptivity")
print("     • Channel Fit (10%): digital product for digital customer")
print("   ML PROBABILITY (50%):")
print("     • Logit model (if trained, otherwise rule-based 100%)")

print("\n🔄 Generating recommendations...")

recs = agent_b.get_all_recommendations(test_customer_id)

if 'error' in recs:
    print(f"\n❌ Agent B failed: {recs['error']}")
else:
    print(f"\n✅ Agent B Success!\n")
    
    metadata = recs.get('recommendation_metadata', {})
    print(f"📊 Scoring: {metadata.get('scoring_method', 'unknown')}")
    print(f"   Rule Weight: {metadata.get('rule_weight', 0)*100:.0f}%")
    print(f"   ML Weight: {metadata.get('ml_weight', 0)*100:.0f}%")
    print(f"   ML Available: {'✅' if metadata.get('ml_available') else '❌ (using rule-based only)'}")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    print(f"   Tailored: {len(recs['tailored_recommendations'])}")
    print(f"   Similar: {len(recs['similar_products'])}")
    print(f"   Segment: {len(recs['segment_recommendations'])}")
    
    if len(recs['tailored_recommendations']) > 0:
        print(f"\n💎 Top 3 Recommendations:\n")
        for i, rec in enumerate(recs['tailored_recommendations'][:3], 1):
            print(f"   {i}. {rec['product_name']}")
            print(f"      Category: {rec['category']}")
            print(f"      Overall Score: {rec.get('score', 0):.3f}")
            print(f"      • Rule Score: {rec.get('rule_score', 0):.3f}")
            print(f"      • ML Prob: {rec.get('ml_probability', 0):.3f}")
            print(f"      Reason: {rec.get('reason', 'N/A')}")
            print()

# ============================================================================
# SUMMARY
# ============================================================================
print("="*80)
print("📋 SUMMARY")
print("="*80)
print(f"✅ Macro Segments: {len(result_a['personas'])} unique segments generated")
print(f"✅ Micro Segments: {len(result_micro['micro_segments']) if 'error' not in result_micro else 0} segments created")
print(f"✅ Agent B: {'Working' if 'error' not in recs else 'Failed'}")
if 'error' not in recs:
    print(f"   • Generated {len(recs['tailored_recommendations'])} recommendations")
    print(f"   • Scoring: {metadata.get('scoring_method', 'unknown')}")
print("\n🎉 Complete flow tested successfully!")
print("="*80)
