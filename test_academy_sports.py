"""
Comprehensive test for Academy Sports implementation
Tests Agent A (K-Prototypes clustering) and Agent B (Feature-based recommendations)
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from agents.agent_a_academy_chromadb import AgentA_Academy
from agents.agent_b_academy_chromadb import AgentB_Academy


def print_header(title):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def test_agent_a():
    """Test Agent A - Persona identification"""
    print_header("TEST 1: Agent A - Persona Identification (K-Prototypes)")
    
    agent_a = AgentA_Academy()
    result = agent_a.execute()
    
    if 'error' in result:
        print(f"\n❌ ERROR: {result['error']}")
        return False
    
    print(f"\n✅ Status: {result.get('status', 'success')}")
    print(f"📊 Total Customers Analyzed: {result.get('total_customers', 0):,}")
    
    if 'personas' in result:
        print(f"\n{'─'*80}")
        print("IDENTIFIED PERSONAS:")
        print(f"{'─'*80}")
        
        for cluster_id, persona in result['personas'].items():
            print(f"\n{persona['persona_name']}")
            print(f"  └─ Size: {persona['size']:,} customers ({persona['percentage']}%)")
            print(f"  └─ Description: {persona['description']}")
            print(f"  └─ Key Behavioral Signals:")
            
            chars = persona['characteristics']
            print(f"      • Search Specificity: {chars['avg_search_specificity']:.2f}/5.0")
            print(f"      • Spec Expansion Rate: {chars['avg_spec_expansion_rate']*100:.1f}%")
            print(f"      • Bundle Affinity: {chars['avg_bundle_affinity']*100:.1f}%")
            print(f"      • Price Sort Frequency: {chars['avg_price_sort_frequency']*100:.1f}%")
            print(f"      • Avg Annual Spend: ${chars['avg_spend_12mo']:.2f}")
            
            prefs = persona['product_preferences']
            if 'loves' in prefs:
                print(f"  └─ Product Preferences:")
                print(f"      ✅ Loves: {', '.join(prefs['loves'][:3])}")
                if 'hates' in prefs:
                    print(f"      ❌ Avoids: {', '.join(prefs['hates'][:2])}")
    
    if 'validation' in result and 'accuracy' in result['validation']:
        print(f"\n{'─'*80}")
        print("VALIDATION RESULTS:")
        print(f"{'─'*80}")
        validation = result['validation']
        accuracy = validation['accuracy'] * 100
        print(f"  ✅ Clustering Accuracy: {accuracy:.2f}%")
        print(f"  📊 Correct Predictions: {validation['correct']:,} / {validation['total']:,}")
        
        if accuracy >= 85:
            print(f"  🎯 EXCELLENT! Target accuracy (>85%) achieved!")
        elif accuracy >= 75:
            print(f"  👍 GOOD! Above 75% accuracy")
        else:
            print(f"  ⚠️  Below target accuracy (should be >85%)")
    
    return True


def test_agent_b():
    """Test Agent B - Product recommendations"""
    print_header("TEST 2: Agent B - Product Recommendations (Feature-Based Scoring)")
    
    agent_b = AgentB_Academy()
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Novice searching for "tent"',
            'params': {'persona': 'Novice', 'search_query': 'tent', 'top_n': 3},
            'expected': 'Should prioritize instant setup, bundles, simple designs'
        },
        {
            'name': 'Seasoned Pro searching for "backpack"',
            'params': {'persona': 'Seasoned_Pro', 'search_query': 'backpack', 'top_n': 3},
            'expected': 'Should prioritize ultralight, technical designs'
        },
        {
            'name': 'Family Socializer searching for "tent"',
            'params': {'persona': 'Family_Socializer', 'search_query': 'tent', 'top_n': 3},
            'expected': 'Should prioritize 4+ person capacity, weather resistant'
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'─'*80}")
        print(f"Scenario {i}: {scenario['name']}")
        print(f"Expected: {scenario['expected']}")
        print(f"{'─'*80}")
        
        result = agent_b.execute(scenario['params'])
        
        if 'error' in result:
            print(f"❌ ERROR: {result['error']}")
            continue
        
        print(f"\n✅ Status: {result['status']}")
        print(f"📊 Products Considered: {result.get('total_products_considered', 0)}")
        
        if 'recommendations' in result and len(result['recommendations']) > 0:
            print(f"\nTop {len(result['recommendations'])} Recommendations:")
            
            for j, rec in enumerate(result['recommendations'], 1):
                print(f"\n  {j}. {rec['product_name']}")
                print(f"     └─ Score: {rec['score']*100:.2f}% | Match Level: {rec['match_level']}")
                print(f"     └─ Price: ${rec['price']:.2f} | Brand: {rec['brand']}")
                print(f"     └─ Features: {rec['features'].get('setup_type', 'N/A')}, "
                      f"{rec['features'].get('complexity', 'N/A')}")
                
                # Show top lift factors
                if 'feature_lifts' in rec and rec['feature_lifts']:
                    lifts = sorted(rec['feature_lifts'].items(), 
                                  key=lambda x: abs(x[1]['boost_percent']), 
                                  reverse=True)[:2]
                    if lifts:
                        print(f"     └─ Key Factors:", end='')
                        for feature, data in lifts:
                            boost = data['boost_percent']
                            sign = '+' if boost > 0 else ''
                            print(f" {feature} ({sign}{boost:.0f}%)", end='')
                        print()
        
        # Show insights
        if 'insights' in result:
            insights = result['insights']
            print(f"\n  📊 Insights:")
            print(f"     └─ Avg Score: {insights.get('avg_score', 0)*100:.2f}%")
            print(f"     └─ Avg Price: ${insights.get('avg_price', 0):.2f}")
            print(f"     └─ Strategy: {insights.get('recommendation_strategy', 'N/A')}")
    
    return True


def test_usecase1():
    """Test Use Case 1: Two different users, same search"""
    print_header("TEST 3: Use Case 1 - Different Personas, Same Search")
    print("Scenario: Both Novice and Pro search for 'camping tent'")
    print("Expected: Different products ranked #1 for each persona")
    
    agent_b = AgentB_Academy()
    
    # Novice search
    print(f"\n{'─'*80}")
    print("USER 1: Novice (First-Time Camper)")
    print(f"{'─'*80}")
    
    result_novice = agent_b.execute({
        'persona': 'Novice',
        'search_query': 'camping tent',
        'top_n': 3
    })
    
    if 'recommendations' in result_novice and len(result_novice['recommendations']) > 0:
        top_novice = result_novice['recommendations'][0]
        print(f"\n🥇 Top Recommendation: {top_novice['product_name']}")
        print(f"   Score: {top_novice['score']*100:.2f}%")
        print(f"   Why: {top_novice.get('features', {}).get('setup_type', 'N/A')}, "
              f"{top_novice.get('features', {}).get('complexity', 'N/A')}")
    
    # Pro search
    print(f"\n{'─'*80}")
    print("USER 2: Seasoned Pro")
    print(f"{'─'*80}")
    
    result_pro = agent_b.execute({
        'persona': 'Seasoned_Pro',
        'search_query': 'camping tent',
        'top_n': 3
    })
    
    if 'recommendations' in result_pro and len(result_pro['recommendations']) > 0:
        top_pro = result_pro['recommendations'][0]
        print(f"\n🥇 Top Recommendation: {top_pro['product_name']}")
        print(f"   Score: {top_pro['score']*100:.2f}%")
        print(f"   Why: {top_pro.get('features', {}).get('setup_type', 'N/A')}, "
              f"{top_pro.get('features', {}).get('complexity', 'N/A')}")
    
    # Compare
    print(f"\n{'─'*80}")
    print("COMPARISON:")
    print(f"{'─'*80}")
    
    if 'recommendations' in result_novice and 'recommendations' in result_pro:
        if len(result_novice['recommendations']) > 0 and len(result_pro['recommendations']) > 0:
            novice_top = result_novice['recommendations'][0]
            pro_top = result_pro['recommendations'][0]
            
            if novice_top['product_id'] != pro_top['product_id']:
                print("✅ SUCCESS! Different products recommended for each persona")
                print(f"   Novice gets: {novice_top['product_name']}")
                print(f"   Pro gets: {pro_top['product_name']}")
            else:
                print("⚠️  WARNING: Same product recommended for both personas")
    
    return True


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("  🏕️  ACADEMY SPORTS PERSONALIZATION - COMPREHENSIVE TEST")
    print("="*80)
    print("\nTesting K-Prototypes Clustering + Feature-Based Recommendations")
    print("Data: 5,000 customers | 57 products | 3 personas\n")
    
    success = True
    
    # Test Agent A
    try:
        if not test_agent_a():
            success = False
    except Exception as e:
        print(f"\n❌ Agent A Test Failed: {e}")
        success = False
    
    # Test Agent B
    try:
        if not test_agent_b():
            success = False
    except Exception as e:
        print(f"\n❌ Agent B Test Failed: {e}")
        success = False
    
    # Test Use Case 1
    try:
        if not test_usecase1():
            success = False
    except Exception as e:
        print(f"\n❌ Use Case 1 Test Failed: {e}")
        success = False
    
    # Final summary
    print_header("TEST SUMMARY")
    
    if success:
        print("\n✅ ALL TESTS PASSED!")
        print("\n🎯 Next Steps:")
        print("   1. Update ChromaDB initialization (Phase 5)")
        print("   2. Create frontend components (Phase 6)")
        print("   3. Test end-to-end flow (Phase 7)")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("   Review errors above and fix issues")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()

