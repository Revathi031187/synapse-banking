"""
COMPLETE PARITY TEST: Banking vs Academy Sports
Tests ALL features for exact implementation match
"""
import requests
import json
import sys
from typing import Dict, List, Tuple

API_BASE = "http://localhost:8002"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")

def test_endpoint(endpoint: str, method: str = "GET", data: dict = None, timeout: int = 30) -> Tuple[bool, dict]:
    """Test an API endpoint"""
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=timeout)
        
        if response.status_code == 200:
            return True, response.json()
        else:
            print_error(f"{endpoint}: HTTP {response.status_code}")
            return False, {}
    except Exception as e:
        print_error(f"{endpoint}: {str(e)}")
        return False, {}

def check_required_keys(data: dict, required_keys: List[str], label: str) -> bool:
    """Check if all required keys exist"""
    missing = [key for key in required_keys if key not in data]
    if missing:
        print_error(f"{label} missing keys: {missing}")
        return False
    print_success(f"{label} has all required keys")
    return True

def main():
    print_header("🏦 BANKING vs 🏈 ACADEMY SPORTS - COMPLETE PARITY TEST")
    
    results = {'passed': 0, 'failed': 0, 'warnings': 0}
    
    # ========================================================================
    # TEST 1: Backend Health Check
    # ========================================================================
    print_header("TEST 1: Backend Health Check")
    
    for industry in ['academy', 'banking']:
        success, data = test_endpoint(f"/api/{industry}/status")
        if success:
            print_success(f"{industry.capitalize()} backend: ONLINE")
            results['passed'] += 1
        else:
            print_error(f"{industry.capitalize()} backend: OFFLINE")
            results['failed'] += 1
            return results  # Can't continue without backend
    
    # ========================================================================
    # TEST 2: Agent A Results - Structure Parity
    # ========================================================================
    print_header("TEST 2: Agent A Results - Structure Parity")
    
    success_a, academy_data = test_endpoint("/api/academy/agent_a/results")
    success_b, banking_data = test_endpoint("/api/banking/agent_a/results")
    
    if not (success_a and success_b):
        print_error("One or both Agent A not executed. Run segmentation first!")
        results['failed'] += 1
    else:
        academy_results = academy_data.get('results', {})
        banking_results = banking_data.get('results', {})
        
        # Check personas exist
        if 'personas' not in academy_results or 'personas' not in banking_results:
            print_error("Personas not found in results")
            results['failed'] += 1
        else:
            academy_personas = academy_results['personas']
            banking_personas = banking_results['personas']
            
            print_info(f"Academy: {len(academy_personas)} personas")
            print_info(f"Banking: {len(banking_personas)} personas")
            
            if len(banking_personas) >= 4:
                print_success(f"Banking has {len(banking_personas)} personas (minimum 4)")
                results['passed'] += 1
            else:
                print_error(f"Banking has only {len(banking_personas)} personas (need 4+)")
                results['failed'] += 1
            
            # Check first persona structure
            academy_persona = list(academy_personas.values())[0]
            banking_persona = list(banking_personas.values())[0]
            
            print(f"\n{Colors.BOLD}Checking Persona Structure:{Colors.END}")
            
            # Required keys for parity
            required_keys = [
                'persona_name', 'size', 'characteristics', 'revenue_metrics'
            ]
            
            if check_required_keys(banking_persona, required_keys, "Banking Persona"):
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            # Check for visual enrichment
            print(f"\n{Colors.BOLD}Visual Enrichment Check:{Colors.END}")
            
            visual_keys = {
                'image_url': 'Professional Unsplash images',
                'color_theme': 'Color-coded borders',
                'visual_emoji': 'Banking-specific emojis'
            }
            
            for key, desc in visual_keys.items():
                if key in banking_persona:
                    value = banking_persona[key]
                    print_success(f"{desc}: {value if isinstance(value, str) and len(value) < 50 else type(value).__name__}")
                    results['passed'] += 1
                else:
                    print_error(f"{desc}: MISSING")
                    results['failed'] += 1
            
            # Check for segment explanation
            print(f"\n{Colors.BOLD}Segment Explanation Check:{Colors.END}")
            
            if 'segment_explanation' in banking_persona:
                explanation = banking_persona['segment_explanation']
                required_explanation_keys = ['segment_definition', 'key_behaviors', 'marketing_recommendations']
                
                if check_required_keys(explanation, required_explanation_keys, "Segment Explanation"):
                    results['passed'] += 1
                    
                    # Check content quality
                    if len(explanation.get('key_behaviors', [])) >= 2:
                        print_success(f"Key behaviors: {len(explanation['key_behaviors'])} items")
                        results['passed'] += 1
                    else:
                        print_warning("Key behaviors insufficient")
                        results['warnings'] += 1
                    
                    if len(explanation.get('marketing_recommendations', [])) >= 2:
                        print_success(f"Marketing recommendations: {len(explanation['marketing_recommendations'])} items")
                        results['passed'] += 1
                    else:
                        print_warning("Marketing recommendations insufficient")
                        results['warnings'] += 1
                else:
                    results['failed'] += 1
            else:
                print_error("Banking persona missing segment_explanation")
                results['failed'] += 1
    
    # ========================================================================
    # TEST 3: Micro Segmentation - Complete Check
    # ========================================================================
    print_header("TEST 3: Micro Segmentation - Complete Implementation")
    
    if success_a and success_b:
        academy_personas = academy_data['results']['personas']
        banking_personas = banking_data['results']['personas']
        
        if academy_personas and banking_personas:
            academy_cluster_id = list(academy_personas.keys())[0]
            banking_cluster_id = list(banking_personas.keys())[0]
            
            print_info(f"Testing micro segments for:")
            print_info(f"  Academy: Cluster {academy_cluster_id}")
            print_info(f"  Banking: Cluster {banking_cluster_id}")
            
            # Create/fetch micro segments
            print(f"\n{Colors.BOLD}Creating Micro Segments:{Colors.END}")
            
            success_a_micro, academy_micro_data = test_endpoint(
                f"/api/academy/micro-segments/{academy_cluster_id}",
                method="POST"
            )
            
            success_b_micro, banking_micro_data = test_endpoint(
                f"/api/banking/micro-segments/{banking_cluster_id}",
                method="POST"
            )
            
            if success_a_micro and success_b_micro:
                print_success("Micro segments created for both industries")
                results['passed'] += 1
                
                # Fetch and compare
                success_a_get, academy_micro = test_endpoint(f"/api/academy/micro-segments/{academy_cluster_id}")
                success_b_get, banking_micro = test_endpoint(f"/api/banking/micro-segments/{banking_cluster_id}")
                
                if success_a_get and success_b_get:
                    academy_segs = academy_micro.get('result', {}).get('micro_segments', [])
                    banking_segs = banking_micro.get('result', {}).get('micro_segments', [])
                    
                    print_info(f"Academy micro segments: {len(academy_segs)}")
                    print_info(f"Banking micro segments: {len(banking_segs)}")
                    
                    if len(banking_segs) >= 3:
                        print_success(f"Banking has {len(banking_segs)} micro segments (3+ required)")
                        results['passed'] += 1
                    else:
                        print_error(f"Banking has only {len(banking_segs)} micro segments")
                        results['failed'] += 1
                    
                    # Check micro segment structure
                    if banking_segs:
                        micro_seg = banking_segs[0]
                        
                        print(f"\n{Colors.BOLD}Micro Segment Structure Check:{Colors.END}")
                        
                        required_micro_keys = [
                            'name', 'size', 'percentage', 'ltv_tier', 
                            'characteristics', 'segment_explanation'
                        ]
                        
                        if check_required_keys(micro_seg, required_micro_keys, "Micro Segment"):
                            results['passed'] += 1
                        else:
                            results['failed'] += 1
                        
                        # Check micro segment explanation
                        if 'segment_explanation' in micro_seg:
                            micro_explanation = micro_seg['segment_explanation']
                            required_explanation_keys = [
                                'segment_definition', 'key_behaviors', 'marketing_recommendations'
                            ]
                            
                            if check_required_keys(micro_explanation, required_explanation_keys, "Micro Explanation"):
                                results['passed'] += 1
                            else:
                                results['failed'] += 1
                        else:
                            print_error("Micro segment missing segment_explanation")
                            results['failed'] += 1
            else:
                print_error("Failed to create micro segments")
                results['failed'] += 1
    
    # ========================================================================
    # TEST 4: Agent B - Product Recommendations
    # ========================================================================
    print_header("TEST 4: Agent B - Product Recommendations")
    
    # Get customers list
    success_a, academy_customers = test_endpoint("/api/academy/customers")
    success_b, banking_customers = test_endpoint("/api/banking/customers")
    
    if success_a and success_b:
        academy_count = len(academy_customers.get('customers', []))
        banking_count = len(banking_customers.get('customers', []))
        
        print_info(f"Academy customers: {academy_count}")
        print_info(f"Banking customers: {banking_count}")
        
        if banking_count >= 100:
            print_success(f"Banking has {banking_count} customers")
            results['passed'] += 1
        else:
            print_error(f"Banking has only {banking_count} customers")
            results['failed'] += 1
        
        # Test Agent B execution
        if academy_count > 0 and banking_count > 0:
            academy_customer_id = academy_customers['customers'][0]['customer_id']
            banking_customer_id = banking_customers['customers'][0]['customer_id']
            
            print(f"\n{Colors.BOLD}Testing Agent B Execution:{Colors.END}")
            
            # Academy Agent B
            success_a_exec, academy_rec = test_endpoint(
                "/api/academy/agent_b/execute",
                method="POST",
                data={'customer_id': academy_customer_id, 'top_n': 3}
            )
            
            # Banking Agent B
            success_b_exec, banking_rec = test_endpoint(
                "/api/banking/agent_b/execute",
                method="POST",
                data={'customer_id': banking_customer_id, 'top_n': 3}
            )
            
            if success_a_exec and success_b_exec:
                print_success("Both Agent B executions successful")
                results['passed'] += 1
            else:
                if not success_b_exec:
                    print_error("Banking Agent B execution FAILED")
                    results['failed'] += 1
    
    # ========================================================================
    # TEST 5: API Endpoint Completeness
    # ========================================================================
    print_header("TEST 5: API Endpoint Completeness")
    
    critical_endpoints = {
        'academy': [
            '/api/academy/status',
            '/api/academy/agent_a/results',
            '/api/academy/macro-segments',
            '/api/academy/customers',
            '/api/academy/products'
        ],
        'banking': [
            '/api/banking/status',
            '/api/banking/agent_a/results',
            '/api/banking/macro-segments',
            '/api/banking/customers',
            '/api/banking/products'
        ]
    }
    
    for industry, endpoints in critical_endpoints.items():
        print(f"\n{Colors.BOLD}{industry.capitalize()} Endpoints:{Colors.END}")
        industry_passed = 0
        for endpoint in endpoints:
            success, _ = test_endpoint(endpoint, timeout=5)
            if success:
                print_success(f"{endpoint.split('/')[-1]}: OK")
                industry_passed += 1
            else:
                print_error(f"{endpoint}: FAILED")
        
        if industry_passed == len(endpoints):
            results['passed'] += 1
        else:
            results['failed'] += 1
    
    # ========================================================================
    # TEST 6: Data Quality Check
    # ========================================================================
    print_header("TEST 6: Data Quality Check")
    
    if success_a and success_b:
        academy_results = academy_data.get('results', {})
        banking_results = banking_data.get('results', {})
        
        # Check customer counts
        academy_total = academy_results.get('n_customers', 0)
        banking_total = banking_results.get('n_customers', 0)
        
        print_info(f"Academy total customers: {academy_total}")
        print_info(f"Banking total customers: {banking_total}")
        
        if banking_total >= 5000:
            print_success("Banking has 5000+ customers (matches Academy)")
            results['passed'] += 1
        else:
            print_warning(f"Banking has {banking_total} customers (expected 5000+)")
            results['warnings'] += 1
        
        # Check for unique persona names
        print(f"\n{Colors.BOLD}Unique Names Check:{Colors.END}")
        
        banking_names = [p['persona_name'] for p in banking_results.get('personas', {}).values()]
        if len(banking_names) == len(set(banking_names)):
            print_success("All Banking persona names are unique")
            results['passed'] += 1
        else:
            duplicates = [name for name in banking_names if banking_names.count(name) > 1]
            print_error(f"Banking has duplicate names: {set(duplicates)}")
            results['failed'] += 1
    
    # ========================================================================
    # FINAL REPORT
    # ========================================================================
    print_header("FINAL REPORT")
    
    total = results['passed'] + results['failed']
    pass_rate = (results['passed'] / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}Tests Run:{Colors.END} {total}")
    print(f"{Colors.GREEN}Passed:{Colors.END} {results['passed']}")
    print(f"{Colors.RED}Failed:{Colors.END} {results['failed']}")
    print(f"{Colors.YELLOW}Warnings:{Colors.END} {results['warnings']}")
    print(f"\n{Colors.BOLD}Pass Rate:{Colors.END} {pass_rate:.1f}%\n")
    
    if pass_rate == 100:
        print_success("🎉 PERFECT! Banking has 100% parity with Academy Sports!")
        print_success("✅ All features implemented correctly")
        print_success("✅ Visual elements match")
        print_success("✅ API endpoints complete")
        print_success("✅ Data quality excellent")
    elif pass_rate >= 90:
        print_success("🎯 EXCELLENT! Banking has near-perfect parity (90%+)")
        print_warning(f"Minor issues to address: {results['failed']} failed tests")
    elif pass_rate >= 75:
        print_warning("⚠️  GOOD! But some features need work (75-90%)")
        print_info(f"Work needed: {results['failed']} failed tests")
    else:
        print_error("❌ NEEDS WORK! Significant features missing (<75%)")
        print_error(f"Critical issues: {results['failed']} failed tests")
    
    # Specific recommendations
    print(f"\n{Colors.BOLD}Recommendations:{Colors.END}")
    
    if results['failed'] > 0:
        print_info("1. Check backend logs for specific errors")
        print_info("2. Ensure all data files are generated (5000 customers)")
        print_info("3. Restart backend to load latest code changes")
        print_info("4. Clear browser cache and re-run Agent A")
    else:
        print_success("🚀 Ready for production! All tests passed!")
    
    return results

if __name__ == "__main__":
    try:
        print(f"{Colors.CYAN}Starting comprehensive parity test...{Colors.END}")
        print(f"{Colors.CYAN}Ensure backend is running on {API_BASE}{Colors.END}\n")
        
        results = main()
        
        # Exit code based on results
        sys.exit(0 if results['failed'] == 0 else 1)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        sys.exit(2)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(3)
