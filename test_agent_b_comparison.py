"""
Agent B Implementation Comparison Test
Tests Banking Agent B vs Academy Sports Agent B to ensure structural match
"""

import requests
import json
from typing import Dict, List
from colorama import init, Fore, Style
import pandas as pd

init(autoreset=True)

API_BASE_URL = 'http://localhost:8002'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{'='*80}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{text}")
    print(f"{'='*80}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Fore.GREEN}✅ {text}")

def print_error(text: str):
    """Print error message"""
    print(f"{Fore.RED}❌ {text}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Fore.YELLOW}⚠️  {text}")

def print_info(text: str):
    """Print info message"""
    print(f"{Fore.BLUE}ℹ️  {text}")

def check_response_structure(response: Dict, expected_keys: List[str], label: str) -> bool:
    """Check if response has expected keys"""
    print(f"\n{Fore.CYAN}Checking {label} Response Structure:")
    
    all_present = True
    for key in expected_keys:
        if key in response:
            print_success(f"Has '{key}': {type(response[key]).__name__}")
            if isinstance(response[key], list):
                print(f"   └─ Count: {len(response[key])}")
        else:
            print_error(f"Missing '{key}'")
            all_present = False
    
    return all_present

def analyze_recommendations(recommendations: List[Dict], label: str):
    """Analyze recommendation structure"""
    print(f"\n{Fore.CYAN}Analyzing {label} Recommendations:")
    
    if not recommendations:
        print_warning("No recommendations found")
        return
    
    print_info(f"Total recommendations: {len(recommendations)}")
    
    # Check first recommendation structure
    first_rec = recommendations[0]
    print(f"\n{Fore.YELLOW}First recommendation keys:")
    for key, value in first_rec.items():
        if isinstance(value, dict):
            print(f"  - {key}: {type(value).__name__} (nested)")
        elif isinstance(value, list):
            print(f"  - {key}: {type(value).__name__} (length: {len(value)})")
        else:
            print(f"  - {key}: {type(value).__name__}")
    
    # Check for required fields
    required_fields = ['product_id', 'product_name', 'propensity_score', 'reasoning']
    print(f"\n{Fore.YELLOW}Required fields check:")
    for field in required_fields:
        if field in first_rec:
            print_success(f"Has '{field}'")
        else:
            print_error(f"Missing '{field}'")

def test_academy_agent_b():
    """Test Academy Sports Agent B"""
    print_header("ACADEMY SPORTS AGENT B TEST")
    
    try:
        # Get customers first
        customers_response = requests.get(f"{API_BASE_URL}/api/academy/agent_a/customers?limit=1")
        customers_data = customers_response.json()
        
        if not customers_data.get('customers'):
            print_error("No Academy customers found")
            print_warning("Skipping Academy test - execute Academy Agent A first")
            print_info("To execute: POST to /api/academy/agent_a/execute")
            return None
        
        customer_id = customers_data['customers'][0]['customer_id']
        print_info(f"Testing with customer: {customer_id}")
        
        # Execute Agent B
        request_body = {
            'customer_id': customer_id,
            'search_query': '',
            'category': None,
            'top_n': 3,
            'persona': None,
            'explain': True
        }
        
        print(f"\n{Fore.YELLOW}Request body:")
        print(json.dumps(request_body, indent=2))
        
        response = requests.post(
            f"{API_BASE_URL}/api/academy/agent_b/execute",
            json=request_body
        )
        
        if response.status_code != 200:
            print_error(f"Request failed: {response.status_code}")
            print(response.text)
            return None
        
        data = response.json()
        
        # Check structure
        expected_keys = [
            'customer_id',
            'tailored_recommendations',
            'similar_products',
            'segment_recommendations',
            'you_might_like',
            'customer_info',
            'recommendation_metadata'
        ]
        
        structure_ok = check_response_structure(data, expected_keys, "Academy Sports")
        
        # Analyze recommendations
        if 'tailored_recommendations' in data:
            analyze_recommendations(data['tailored_recommendations'], "Academy Tailored")
        
        if 'segment_recommendations' in data:
            analyze_recommendations(data['segment_recommendations'], "Academy Segment")
        
        # Check metadata
        if 'recommendation_metadata' in data:
            print(f"\n{Fore.CYAN}Recommendation Metadata:")
            print(json.dumps(data['recommendation_metadata'], indent=2))
        
        return data
        
    except Exception as e:
        print_error(f"Academy test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_banking_agent_b():
    """Test Banking Agent B"""
    print_header("BANKING AGENT B TEST")
    
    try:
        # Get customers first
        customers_response = requests.get(f"{API_BASE_URL}/api/banking/customers?limit=1")
        customers_data = customers_response.json()
        
        if not customers_data.get('customers'):
            print_error("No Banking customers found - Agent A must be executed first!")
            print_warning("Attempting to auto-execute Banking Agent A...")
            
            # Try to execute Agent A automatically
            try:
                agent_a_response = requests.post(
                    f"{API_BASE_URL}/api/banking/agent_a/execute",
                    json={"n_personas": 5},
                    timeout=120  # 2 minute timeout for Agent A
                )
                
                if agent_a_response.status_code == 200:
                    print_success("Banking Agent A executed successfully!")
                    print_info("Waiting 3 seconds for data to be ready...")
                    import time
                    time.sleep(3)
                    
                    # Retry getting customers
                    customers_response = requests.get(f"{API_BASE_URL}/api/banking/customers?limit=1")
                    customers_data = customers_response.json()
                    
                    if not customers_data.get('customers'):
                        print_error("Still no customers after Agent A execution")
                        return None
                else:
                    print_error(f"Agent A execution failed: {agent_a_response.status_code}")
                    print(agent_a_response.text)
                    return None
            except Exception as e:
                print_error(f"Failed to auto-execute Agent A: {e}")
                print_info("Please manually execute: POST to /api/banking/agent_a/execute")
                return None
        
        customer_id = customers_data['customers'][0]['customer_id']
        print_info(f"Testing with customer: {customer_id}")
        
        # Execute Agent B
        request_body = {
            'customer_id': customer_id,
            'use_persona_aligned': True
        }
        
        print(f"\n{Fore.YELLOW}Request body:")
        print(json.dumps(request_body, indent=2))
        
        response = requests.post(
            f"{API_BASE_URL}/api/banking/agent_b/execute",
            json=request_body
        )
        
        if response.status_code != 200:
            print_error(f"Request failed: {response.status_code}")
            print(response.text)
            return None
        
        data = response.json()
        
        # Check structure
        expected_keys = [
            'success',
            'customer_id',
            'tailored_recommendations',
            'similar_products',
            'segment_recommendations',
            'you_might_like',
            'customer_info',
            'recommendation_metadata'
        ]
        
        structure_ok = check_response_structure(data, expected_keys, "Banking")
        
        # Analyze recommendations
        if 'tailored_recommendations' in data:
            analyze_recommendations(data['tailored_recommendations'], "Banking Tailored")
        
        if 'segment_recommendations' in data:
            analyze_recommendations(data['segment_recommendations'], "Banking Segment")
        
        # Check metadata
        if 'recommendation_metadata' in data:
            print(f"\n{Fore.CYAN}Recommendation Metadata:")
            print(json.dumps(data['recommendation_metadata'], indent=2))
        
        # Banking-specific checks
        print(f"\n{Fore.CYAN}Banking-Specific Checks:")
        
        if 'tailored_recommendations' in data and data['tailored_recommendations']:
            first_rec = data['tailored_recommendations'][0]
            
            # Check for banking-specific fields
            banking_fields = ['category', 'annual_fee', 'min_balance', 'interest_rate', 'eligibility_status']
            print(f"\n{Fore.YELLOW}Banking-specific fields:")
            for field in banking_fields:
                if field in first_rec:
                    print_success(f"Has '{field}': {first_rec[field]}")
                else:
                    print_warning(f"Missing optional field '{field}'")
            
            # Check for score_breakdown (12-factor scoring)
            if 'score_breakdown' in first_rec:
                print_success("Has 'score_breakdown' (12-factor scoring)")
                breakdown = first_rec['score_breakdown']
                print(f"\n{Fore.YELLOW}12-Factor Score Breakdown:")
                for factor, score in breakdown.items():
                    print(f"  - {factor}: {score:.3f}")
            else:
                print_warning("Missing 'score_breakdown'")
        
        return data
        
    except Exception as e:
        print_error(f"Banking test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_implementations(academy_data: Dict, banking_data: Dict):
    """Compare Academy and Banking implementations"""
    print_header("IMPLEMENTATION COMPARISON")
    
    if not academy_data or not banking_data:
        print_error("Cannot compare - one or both tests failed")
        return
    
    # Structure comparison
    print(f"{Fore.CYAN}Structure Match:")
    
    academy_keys = set(academy_data.keys())
    banking_keys = set(banking_data.keys()) - {'success'}  # Remove banking-specific 'success'
    
    common_keys = academy_keys.intersection(banking_keys)
    academy_only = academy_keys - banking_keys
    banking_only = banking_keys - academy_keys
    
    print_info(f"Common keys: {len(common_keys)}")
    for key in sorted(common_keys):
        print(f"  ✓ {key}")
    
    if academy_only:
        print_warning(f"\nAcademy-only keys: {academy_only}")
    
    if banking_only:
        print_warning(f"\nBanking-only keys: {banking_only}")
    
    # Count comparison
    print(f"\n{Fore.CYAN}Recommendation Counts:")
    
    comparison_table = []
    
    for key in ['tailored_recommendations', 'segment_recommendations']:
        academy_count = len(academy_data.get(key, []))
        banking_count = len(banking_data.get(key, []))
        
        match = "✅" if academy_count > 0 and banking_count > 0 else "⚠️"
        
        comparison_table.append({
            'Section': key.replace('_', ' ').title(),
            'Academy': academy_count,
            'Banking': banking_count,
            'Match': match
        })
    
    df = pd.DataFrame(comparison_table)
    print(df.to_string(index=False))
    
    # Metadata comparison
    print(f"\n{Fore.CYAN}Metadata Comparison:")
    
    academy_meta = academy_data.get('recommendation_metadata', {})
    banking_meta = banking_data.get('recommendation_metadata', {})
    
    print(f"\n{Fore.YELLOW}Academy Metadata:")
    print(json.dumps(academy_meta, indent=2))
    
    print(f"\n{Fore.YELLOW}Banking Metadata:")
    print(json.dumps(banking_meta, indent=2))
    
    # Recommendation field comparison
    print(f"\n{Fore.CYAN}Recommendation Fields Comparison:")
    
    academy_rec = academy_data.get('tailored_recommendations', [{}])[0] if academy_data.get('tailored_recommendations') else {}
    banking_rec = banking_data.get('tailored_recommendations', [{}])[0] if banking_data.get('tailored_recommendations') else {}
    
    academy_fields = set(academy_rec.keys())
    banking_fields = set(banking_rec.keys())
    
    common_fields = academy_fields.intersection(banking_fields)
    academy_only_fields = academy_fields - banking_fields
    banking_only_fields = banking_fields - academy_fields
    
    print(f"\n{Fore.GREEN}Common fields ({len(common_fields)}):")
    for field in sorted(common_fields):
        print(f"  ✓ {field}")
    
    if academy_only_fields:
        print(f"\n{Fore.YELLOW}Academy-only fields: {sorted(academy_only_fields)}")
    
    if banking_only_fields:
        print(f"\n{Fore.BLUE}Banking-only fields (domain-specific): {sorted(banking_only_fields)}")

def test_ai_explanation():
    """Test AI explanation endpoint"""
    print_header("AI EXPLANATION TEST")
    
    try:
        # Get customers
        customers_response = requests.get(f"{API_BASE_URL}/api/banking/customers?limit=1")
        customers_data = customers_response.json()
        
        if not customers_data.get('customers'):
            print_error("No customers found")
            return
        
        customer_id = customers_data['customers'][0]['customer_id']
        
        # Execute Agent B first to get recommendations
        execute_response = requests.post(
            f"{API_BASE_URL}/api/banking/agent_b/execute",
            json={'customer_id': customer_id, 'use_persona_aligned': True}
        )
        
        if execute_response.status_code != 200:
            print_error("Failed to execute Agent B")
            return
        
        data = execute_response.json()
        
        if not data.get('tailored_recommendations'):
            print_error("No recommendations to test")
            return
        
        # Get first product
        first_product = data['tailored_recommendations'][0]
        product_id = first_product['product_id']
        
        print_info(f"Testing AI explanation for product: {product_id}")
        
        # Request AI explanation
        explain_request = {
            'customer_id': customer_id,
            'product_id': product_id
        }
        
        print(f"\n{Fore.YELLOW}Request body:")
        print(json.dumps(explain_request, indent=2))
        
        explain_response = requests.post(
            f"{API_BASE_URL}/api/banking/agent_b/explain",
            json=explain_request
        )
        
        if explain_response.status_code != 200:
            print_error(f"AI explanation failed: {explain_response.status_code}")
            print(explain_response.text)
            return
        
        explain_data = explain_response.json()
        
        print(f"\n{Fore.GREEN}AI Explanation Response:")
        print(json.dumps(explain_data, indent=2))
        
        if 'explanation' in explain_data:
            print_success(f"AI Explanation generated: {len(explain_data['explanation'])} characters")
            print(f"\n{Fore.CYAN}Explanation:")
            print(f"{Style.BRIGHT}{explain_data['explanation']}")
        else:
            print_error("No explanation field in response")
        
    except Exception as e:
        print_error(f"AI explanation test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test runner"""
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}{'='*80}")
    print(f"AGENT B IMPLEMENTATION COMPARISON TEST")
    print(f"{'='*80}\n")
    
    print(f"{Fore.CYAN}Testing against: {API_BASE_URL}")
    print(f"{Fore.CYAN}Comparing Banking Agent B vs Academy Sports Agent B\n")
    
    # Test Academy Sports (optional - may not be set up)
    academy_data = test_academy_agent_b()
    
    # Test Banking (REQUIRED - auto-executes Agent A if needed)
    banking_data = test_banking_agent_b()
    
    # Compare implementations if both available
    if academy_data and banking_data:
        compare_implementations(academy_data, banking_data)
    elif banking_data:
        print_header("BANKING-ONLY VALIDATION")
        print_info("Academy Sports not available - validating Banking structure only")
        
        # Validate Banking has the expected Academy Sports structure
        required_keys = ['customer_id', 'tailored_recommendations', 'segment_recommendations', 'recommendation_metadata']
        all_present = True
        for key in required_keys:
            if key in banking_data:
                print_success(f"Banking has '{key}'")
            else:
                print_error(f"Banking missing '{key}'")
                all_present = False
        
        if all_present:
            print_success("\n✅ Banking has all required Academy Sports structure keys!")
        else:
            print_error("\n❌ Banking missing some required structure keys")
    
    # Test AI explanation (Banking-specific)
    if banking_data:
        test_ai_explanation()
    
    # Final summary
    print_header("FINAL SUMMARY")
    
    if academy_data and banking_data:
        # Full comparison (both domains available)
        checks = [
            ("Both have 'tailored_recommendations'", 
             'tailored_recommendations' in academy_data and 'tailored_recommendations' in banking_data),
            ("Both have 'segment_recommendations'", 
             'segment_recommendations' in academy_data and 'segment_recommendations' in banking_data),
            ("Both have 'recommendation_metadata'", 
             'recommendation_metadata' in academy_data and 'recommendation_metadata' in banking_data),
            ("Banking has recommendations", 
             len(banking_data.get('tailored_recommendations', [])) > 0 or 
             len(banking_data.get('segment_recommendations', [])) > 0),
            ("Banking has score_breakdown (12-factor)", 
             'tailored_recommendations' in banking_data and 
             len(banking_data['tailored_recommendations']) > 0 and
             'score_breakdown' in banking_data['tailored_recommendations'][0])
        ]
        
        passed = sum(1 for _, result in checks if result)
        total = len(checks)
        
        print(f"\n{Fore.CYAN}Compatibility Checks: {passed}/{total}")
        for check_name, result in checks:
            if result:
                print_success(check_name)
            else:
                print_error(check_name)
        
        if passed == total:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}🎉 ALL CHECKS PASSED!")
            print(f"{Fore.GREEN}Banking Agent B successfully matches Academy Sports structure!")
        else:
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}⚠️  SOME CHECKS FAILED")
            print(f"{Fore.YELLOW}Review the comparison above for details")
    
    elif banking_data:
        # Banking-only validation
        print_info("Academy Sports not tested - validating Banking structure only")
        
        checks = [
            ("Banking has 'tailored_recommendations'", 
             'tailored_recommendations' in banking_data),
            ("Banking has 'segment_recommendations'", 
             'segment_recommendations' in banking_data),
            ("Banking has 'recommendation_metadata'", 
             'recommendation_metadata' in banking_data),
            ("Banking has recommendations", 
             len(banking_data.get('tailored_recommendations', [])) > 0 or 
             len(banking_data.get('segment_recommendations', [])) > 0),
            ("Banking has score_breakdown (12-factor)", 
             'tailored_recommendations' in banking_data and 
             len(banking_data['tailored_recommendations']) > 0 and
             'score_breakdown' in banking_data['tailored_recommendations'][0])
        ]
        
        passed = sum(1 for _, result in checks if result)
        total = len(checks)
        
        print(f"\n{Fore.CYAN}Banking Structure Checks: {passed}/{total}")
        for check_name, result in checks:
            if result:
                print_success(check_name)
            else:
                print_error(check_name)
        
        if passed == total:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}✅ BANKING AGENT B STRUCTURE VALIDATED!")
            print(f"{Fore.GREEN}All Academy Sports structure requirements met!")
            print(f"\n{Fore.CYAN}Note: Run Academy Agent A to enable full comparison")
        else:
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}⚠️  SOME CHECKS FAILED")
            print(f"{Fore.YELLOW}Review the output above for details")
    
    else:
        print_error("Banking test failed - cannot provide summary")
        print_warning("\nTroubleshooting:")
        print("  1. Is the backend running? Check: http://localhost:8002/health")
        print("  2. Try restarting: RESTART_ACADEMY_MATCH.bat")
        print("  3. Check backend logs for errors")
    
    print(f"\n{Fore.MAGENTA}{'='*80}\n")

if __name__ == '__main__':
    main()
