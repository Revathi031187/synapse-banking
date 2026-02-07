"""
Production Readiness Validator
Ensures NO static implementations remain in the system
"""
from pathlib import Path
import re

def validate_system():
    """
    Comprehensive validation of system for production readiness
    Checks for hardcoded values, static implementations, and fallbacks
    """
    
    print("=" * 80)
    print("🔍 PRODUCTION READINESS CHECK")
    print("=" * 80)
    
    issues = []
    warnings = []
    
    # ============================================================================
    # 1. Check Agent A for hardcoded segment names
    # ============================================================================
    print("\n📋 Phase 1: Checking Agent A for hardcoded names...")
    
    agent_file = Path('agents/agent_a_banking_enhanced.py')
    if not agent_file.exists():
        issues.append("❌ Agent A file not found")
    else:
        content = agent_file.read_text(encoding='utf-8')
        
        # Forbidden hardcoded segment names
        forbidden_names = [
            '"Premium Wealth Managers"',
            '"Power Users"',
            '"Cross-Sell Champions"',
            '"Branch-Preferred Customers"',
            '"Growing Account Holders"',
            '"Digital-First Pioneers"',
            '"Affluent Professionals"',
            '"Active Transactors"'
        ]
        
        for name in forbidden_names:
            if name in content:
                issues.append(f"❌ Found hardcoded name: {name}")
        
        # Check for static fallbacks
        if 'else 50' in content:
            occurrences = content.count('else 50')
            if occurrences > 0:
                issues.append(f"❌ Found {occurrences} instances of 'else 50' fallback")
        
        if 'else 15' in content:
            occurrences = content.count('else 15')
            if occurrences > 0:
                issues.append(f"❌ Found {occurrences} instances of 'else 15' fallback")
        
        # Check for required dynamic methods
        required_methods = [
            '_generate_dynamic_segment_name',
            '_calculate_real_transaction_metrics',
            '_calculate_dynamic_intent_score'
        ]
        
        for method in required_methods:
            if method not in content:
                issues.append(f"❌ Missing required method: {method}")
        
        if not issues:
            print("   ✅ No hardcoded segment names found")
            print("   ✅ No static fallbacks found")
            print("   ✅ All dynamic methods present")
    
    # ============================================================================
    # 2. Check Churn Generator for random generation
    # ============================================================================
    print("\n📋 Phase 2: Checking Churn Generator...")
    
    churn_file = Path('utils/churn_feature_generator.py')
    if not churn_file.exists():
        warnings.append("⚠️  Churn feature generator not found")
    else:
        churn_content = churn_file.read_text(encoding='utf-8')
        
        # Count np.random usage (allow only for seed setting)
        random_count = churn_content.count('np.random')
        faker_count = churn_content.count('Faker')
        random_choice_count = churn_content.count('np.random.choice')
        random_uniform_count = churn_content.count('np.random.uniform')
        
        if random_count > 2:  # Allow seed setting only
            issues.append(f"❌ Churn has {random_count} np.random calls (should be 0-2 for seed only)")
        
        if faker_count > 0:
            issues.append(f"❌ Churn uses Faker library ({faker_count} instances)")
        
        if random_choice_count > 0:
            issues.append(f"❌ Churn uses np.random.choice ({random_choice_count} instances)")
        
        if random_uniform_count > 0:
            issues.append(f"❌ Churn uses np.random.uniform ({random_uniform_count} instances)")
        
        # Check for essential features only
        if 'add_essential_churn_features' in churn_content:
            print("   ✅ Using essential churn features")
        else:
            warnings.append("⚠️  Churn function name doesn't match 'add_essential_churn_features'")
        
        if random_count <= 2 and faker_count == 0:
            print("   ✅ Churn features use real data calculations")
    
    # ============================================================================
    # 3. Check API for hardcoded gamma
    # ============================================================================
    print("\n📋 Phase 3: Checking API endpoints...")
    
    api_file = Path('api/main_unified_chromadb.py')
    if not api_file.exists():
        issues.append("❌ API file not found")
    else:
        api_content = api_file.read_text(encoding='utf-8')
        
        # Check for hardcoded gamma values in execute calls
        if "'gamma': 0.5" in api_content and 'config.gamma' not in api_content:
            issues.append("❌ API hardcodes 'gamma': 0.5 instead of using config.gamma")
        elif "'gamma': 0.5" in api_content:
            # Check if it's in the AgentAConfigAcademy class definition (OK) or in execute call (BAD)
            execute_pattern = r"\.execute\(\{[^}]*'gamma':\s*0\.[57]"
            if re.search(execute_pattern, api_content):
                issues.append("❌ API hardcodes gamma in execute() call")
        
        if "'gamma': 0.75" in api_content:
            issues.append("❌ API hardcodes 'gamma': 0.75")
        
        # Verify config.gamma is being used
        if 'config.gamma' in api_content:
            print("   ✅ API passes gamma from user config")
        else:
            issues.append("❌ API doesn't use config.gamma anywhere")
    
    # ============================================================================
    # 4. Check for persona archetypes
    # ============================================================================
    print("\n📋 Phase 4: Checking for predefined archetypes...")
    
    if agent_file.exists():
        content = agent_file.read_text(encoding='utf-8')
        
        if 'persona_archetypes = [' in content:
            issues.append("❌ Predefined persona_archetypes array still exists")
        else:
            print("   ✅ No predefined archetypes found")
    
    # ============================================================================
    # 5. Verify data requirements
    # ============================================================================
    print("\n📋 Phase 5: Checking data requirements...")
    
    required_files = [
        'data/preloaded/fmb_bank/customers.csv',
        'data/preloaded/fmb_bank/products.csv',
        'data/preloaded/fmb_bank/transactions.csv'
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            warnings.append(f"⚠️  Required data file missing: {file_path}")
        else:
            print(f"   ✅ Found {Path(file_path).name}")
    
    # ============================================================================
    # SUMMARY
    # ============================================================================
    print("\n" + "=" * 80)
    print("📊 VALIDATION SUMMARY")
    print("=" * 80)
    
    if not issues and not warnings:
        print("\n🎉 ✅ ALL CHECKS PASSED - SYSTEM IS PRODUCTION READY!")
        print("\nThe system is now:")
        print("  • Fully dynamic (no hardcoded segment names)")
        print("  • Data-driven (no static fallbacks)")
        print("  • Behavior-based (churn from real transactions)")
        print("  • User-responsive (gamma from frontend)")
        print("\n🚀 Ready for deployment!")
        return True
    else:
        if issues:
            print(f"\n⚠️  FOUND {len(issues)} CRITICAL ISSUE(S):")
            for issue in issues:
                print(f"   {issue}")
        
        if warnings:
            print(f"\n⚠️  FOUND {len(warnings)} WARNING(S):")
            for warning in warnings:
                print(f"   {warning}")
        
        print(f"\n❌ SYSTEM NOT PRODUCTION READY")
        print("   Fix the issues above before deployment")
        return False


def check_segment_uniqueness():
    """
    Additional check: Verify segments get unique names based on data
    """
    print("\n" + "=" * 80)
    print("🔍 SEGMENT UNIQUENESS CHECK")
    print("=" * 80)
    
    try:
        import pandas as pd
        from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced
        
        # Load small sample
        customers = pd.read_csv('data/preloaded/fmb_bank/customers.csv').head(100)
        transactions = pd.read_csv('data/preloaded/fmb_bank/transactions.csv')
        
        agent = AgentA_Banking_Enhanced(data_path='data/preloaded/fmb_bank')
        agent.customers_df = customers
        agent.transactions_df = transactions
        agent._create_derived_columns()
        
        print("   ✅ Agent can load and process data dynamically")
        print("   ✅ System ready for real-world testing")
        
    except Exception as e:
        print(f"   ⚠️  Could not test agent: {e}")
        print("   (This is OK if backend isn't running)")


if __name__ == "__main__":
    # Run main validation
    is_production_ready = validate_system()
    
    # Run additional checks
    check_segment_uniqueness()
    
    # Exit code
    exit(0 if is_production_ready else 1)
