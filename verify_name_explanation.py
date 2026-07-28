"""
Verify that name_explanation is returned by backend agents
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced
from agents.agent_a_banking_micro import AgentA_Banking_Micro

print("="*80)
print("VERIFYING NAME EXPLANATION IMPLEMENTATION")
print("="*80)

# Test Macro Agent
print("\n1. Testing Macro Agent (agent_a_banking_enhanced.py)...")
try:
    macro_agent = AgentA_Banking_Enhanced(data_path='data/preloaded/fmb_bank')
    print("   ✅ Agent initialized")
    
    # Check if _generate_macro_name_explanation method exists
    if hasattr(macro_agent, '_generate_macro_name_explanation'):
        print("   ✅ _generate_macro_name_explanation method exists")
    else:
        print("   ❌ _generate_macro_name_explanation method NOT FOUND")
    
    # Run segmentation
    print("   Running segmentation with n_clusters=3...")
    result = macro_agent.segment(n_clusters=3)
    
    if result and 'personas' in result:
        print(f"   ✅ Generated {len(result['personas'])} personas")
        
        # Check first persona for name_explanation
        first_persona = result['personas'][0]
        if 'segment_explanation' in first_persona:
            explanation = first_persona['segment_explanation']
            if 'name_explanation' in explanation:
                print(f"   ✅ name_explanation FOUND in persona 0")
                print(f"\n   Sample:")
                print(f"   Name: {first_persona['name']}")
                print(f"   Explanation: {explanation['name_explanation'][:200]}...")
            else:
                print(f"   ❌ name_explanation NOT in segment_explanation")
                print(f"   Keys found: {list(explanation.keys())}")
        else:
            print(f"   ❌ segment_explanation NOT in persona")
    else:
        print("   ❌ No personas in result")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test Micro Agent
print("\n2. Testing Micro Agent (agent_a_banking_micro.py)...")
try:
    micro_agent = AgentA_Banking_Micro(data_path='data/preloaded/fmb_bank')
    print("   ✅ Agent initialized")
    
    # Check if _generate_name_explanation method exists
    if hasattr(micro_agent, '_generate_name_explanation'):
        print("   ✅ _generate_name_explanation method exists")
    else:
        print("   ❌ _generate_name_explanation method NOT FOUND")
    
    # Run micro segmentation (requires macro results)
    print("   Running micro segmentation...")
    micro_result = micro_agent.generate_micro_segments(
        persona_id=0,
        persona_name="Test Persona",
        customer_ids=result['personas'][0]['top_customers'][:100] if result else []
    )
    
    if micro_result and 'micro_segments' in micro_result:
        print(f"   ✅ Generated {len(micro_result['micro_segments'])} micro segments")
        
        # Check first micro for name_explanation
        first_micro = micro_result['micro_segments'][0]
        if 'segment_explanation' in first_micro:
            explanation = first_micro['segment_explanation']
            if 'name_explanation' in explanation:
                print(f"   ✅ name_explanation FOUND in micro 0")
                print(f"\n   Sample:")
                print(f"   Name: {first_micro['name']}")
                print(f"   Explanation: {explanation['name_explanation'][:200]}...")
            else:
                print(f"   ❌ name_explanation NOT in segment_explanation")
                print(f"   Keys found: {list(explanation.keys())}")
        else:
            print(f"   ❌ segment_explanation NOT in micro")
    else:
        print("   ❌ No micro_segments in result")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)
print("\nIf all ✅, the backend is ready.")
print("Run RESTART_WITH_NAME_EXPLANATIONS.bat to test in UI")
print("="*80)
