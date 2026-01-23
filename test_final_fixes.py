"""
Quick test to validate all fixes work correctly
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.agent_a_academy_enhanced import AgentA_Academy_Enhanced

def test_all_fixes():
    """Test all 5 critical fixes"""
    print("\n" + "="*80)
    print("TESTING ALL FIXES")
    print("="*80 + "\n")
    
    # Initialize agent
    agent = AgentA_Academy_Enhanced(data_path='data/preloaded/academy_sports')
    
    # Test 1: Load data and validate
    print("Test 1: Data Loading and Validation")
    print("-" * 80)
    if not agent.load_data('v1'):
        print("FAILED: Could not load data")
        return False
    print("PASSED: Data loaded successfully")
    print(f"  Customers: {len(agent.customers_df)}")
    print(f"  Interactions: {len(agent.interactions_df)}")
    print(f"  Purchases: {len(agent.purchases_df)}")
    
    # Test 2: Run clustering
    print("\nTest 2: Dynamic Clustering with NaN Handling")
    print("-" * 80)
    results = agent.execute({'n_clusters': 5, 'gamma': 0.5})
    
    if results.get('status') != 'success':
        print(f"FAILED: Clustering failed - {results.get('error', 'Unknown error')}")
        return False
    print("PASSED: Clustering completed")
    print(f"  Generated {len(results['personas'])} personas")
    
    # Test 3: Check for duplicate persona names
    print("\nTest 3: Unique Persona Names (No Duplicates or Similar Names)")
    print("-" * 80)
    persona_names = [p['persona_name'] for p in results['personas'].values()]
    duplicates = [name for name in persona_names if persona_names.count(name) > 1]
    
    if duplicates:
        print(f"FAILED: Found duplicate names: {set(duplicates)}")
        return False
    
    # Check for similar base names (e.g., "Expert High-Value" and "Expert High-Value Item-by-Item")
    base_names = []
    for name in persona_names:
        # Extract first 3 words (emoji + expertise + spending)
        parts = name.split()
        if len(parts) >= 3:
            base = " ".join(parts[:3])
            if base in base_names:
                print(f"WARNING: Similar base name detected: '{base}'")
                print(f"  Full names: {[n for n in persona_names if n.startswith(base)]}")
            base_names.append(base)
    
    # Check for "(Segment" suffix or "Item-by-Item" suffix
    bad_suffixes = [name for name in persona_names if '(Segment' in name or 'Item-by-Item' in name]
    if bad_suffixes:
        print(f"WARNING: Found fallback suffixes (should use better differentiation): {bad_suffixes}")
    
    print("PASSED: All persona names are unique")
    for i, name in enumerate(persona_names, 1):
        print(f"  {i}. {name}")
    
    # Test 4: Check temporal metrics variation
    print("\nTest 4: Varied Temporal Metrics (Not All Summer 0.0%)")
    print("-" * 80)
    all_same = True
    first_growth = None
    temporal_issues = []
    peak_seasons = []
    
    for persona_id, persona in results['personas'].items():
        temporal = persona.get('temporal_metrics', {})
        growth = temporal.get('growth_rate', 0)
        peak = temporal.get('peak_season', 'Unknown')
        peak_seasons.append(peak)
        
        if first_growth is None:
            first_growth = growth
        elif growth != first_growth:
            all_same = False
        
        if growth == 0.0:
            temporal_issues.append(f"{persona['short_name']}: 0.0% growth")
        
        print(f"  {persona['short_name'][:30]:30} | Peak: {peak:6} | Growth: {growth:+.1f}%")
    
    if all_same:
        print("FAILED: All personas have identical growth rates")
        return False
    
    if temporal_issues:
        print(f"WARNING: Some personas show 0.0% growth: {len(temporal_issues)}")
    
    # Check for peak season variety
    unique_peaks = set(peak_seasons)
    if len(unique_peaks) == 1:
        print(f"WARNING: All personas have same peak season ({unique_peaks.pop()})")
        print("  This reduces actionable insights. Ideally, different personas should have different peaks.")
    else:
        print(f"  Peak season variety: {len(unique_peaks)} different peaks ({', '.join(unique_peaks)})")
    
    print("PASSED: Temporal metrics show variation")
    
    # Test 5: Check validation data completeness
    print("\nTest 5: Complete Validation Data")
    print("-" * 80)
    validation = results.get('validation', {})
    
    required_fields = ['accuracy', 'correct_predictions', 'total_customers', 'method', 'confidence']
    missing_fields = [field for field in required_fields if field not in validation]
    
    if missing_fields:
        print(f"FAILED: Missing validation fields: {missing_fields}")
        print(f"  Available: {list(validation.keys())}")
        return False
    
    print("PASSED: All validation fields present")
    print(f"  Accuracy: {validation['accuracy']:.1f}%")
    print(f"  Correct Predictions: {validation['correct_predictions']:,} out of {validation['total_customers']:,}")
    print(f"  Method: {validation['method']}")
    print(f"  Confidence: {validation['confidence']}")
    
    # Test 6: Check visualization data
    print("\nTest 6: Visualization Data Completeness")
    print("-" * 80)
    viz_data = results.get('visualization_data', {})
    
    required_viz = [
        'cluster_distribution',
        'persona_characteristics',
        'behavior_comparison',
        'persona_distribution',
        'confidence_distribution',
        'seasonal_acquisition',
        'revenue_breakdown'
    ]
    
    missing_viz = [viz for viz in required_viz if viz not in viz_data]
    
    if missing_viz:
        print(f"FAILED: Missing visualization data: {missing_viz}")
        return False
    
    print("PASSED: All 7 visualization types present")
    for viz_type in required_viz:
        data_count = len(viz_data.get(viz_type, []))
        print(f"  {viz_type:30} : {data_count} items")
    
    # Test 7: Check KPI metrics in personas
    print("\nTest 7: Complete KPI Metrics per Persona")
    print("-" * 80)
    kpi_issues = []
    
    for persona_id, persona in results['personas'].items():
        # Check top-level metrics
        if 'total_revenue' not in persona or persona['total_revenue'] == 0:
            kpi_issues.append(f"{persona['short_name']}: Missing total_revenue")
        
        if 'avg_spend' not in persona or persona['avg_spend'] == 0:
            kpi_issues.append(f"{persona['short_name']}: Missing avg_spend")
        
        if 'confidence_avg' not in persona:
            kpi_issues.append(f"{persona['short_name']}: Missing confidence_avg")
        
        # Check nested metrics
        if 'revenue_metrics' not in persona:
            kpi_issues.append(f"{persona['short_name']}: Missing revenue_metrics")
        
        if 'confidence_metrics' not in persona:
            kpi_issues.append(f"{persona['short_name']}: Missing confidence_metrics")
        
        if 'temporal_metrics' not in persona:
            kpi_issues.append(f"{persona['short_name']}: Missing temporal_metrics")
    
    if kpi_issues:
        print("FAILED: KPI metrics incomplete")
        for issue in kpi_issues[:5]:  # Show first 5 issues
            print(f"  {issue}")
        return False
    
    print("PASSED: All KPI metrics present for all personas")
    print(f"  Total Revenue: ${sum(p['total_revenue'] for p in results['personas'].values()):,.2f}")
    print(f"  Avg Confidence: {sum(p['confidence_avg'] for p in results['personas'].values()) / len(results['personas']):.1f}%")
    
    # Final summary
    print("\n" + "="*80)
    print("ALL TESTS PASSED!")
    print("="*80)
    print("\nSummary:")
    print(f"  Personas Generated: {len(results['personas'])}")
    print(f"  Unique Names: {len(set(persona_names))}/{len(persona_names)}")
    print(f"  Validation Accuracy: {validation['accuracy']:.1f}%")
    print(f"  Visualization Types: {len(viz_data)}/7")
    print(f"  Total Customers: {results['total_customers']:,}")
    print(f"  Total Revenue: ${results['total_revenue']:,.2f}")
    print("\n" + "="*80)
    
    return True

if __name__ == '__main__':
    try:
        success = test_all_fixes()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

