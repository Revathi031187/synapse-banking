"""
Complete Test Script for Banking vs Academy Sports Parity
Tests all Agent A and Agent B functionality to ensure perfect parity
"""
import requests
import json
import time
from typing import Dict, List

API_BASE = "http://localhost:8002"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
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
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def test_api_endpoint(endpoint, method="GET", data=None, expected_keys=None):
    """Test an API endpoint and verify response"""
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            # Check for expected keys
            if expected_keys:
                missing_keys = [key for key in expected_keys if key not in result]
                if missing_keys:
                    print_warning(f"{endpoint}: Missing keys {missing_keys}")
                    return False, result
            
            return True, result
        else:
            print_error(f"{endpoint}: Status {response.status_code}")
            return False, None
    except Exception as e:
        print_error(f"{endpoint}: {str(e)}")
        return False, None

def compare_structures(academy_data, banking_data, label):
    """Compare two data structures for parity"""
    print(f"\n{Colors.BOLD}Comparing {label}:{Colors.END}")
    
    if isinstance(academy_data, dict) and isinstance(banking_data, dict):
        academy_keys = set(academy_data.keys())
        banking_keys = set(banking_data.keys())
        
        missing_in_banking = academy_keys - banking_keys
        extra_in_banking = banking_keys - academy_keys
        
        if missing_in_banking:
            print_error(f"Missing in Banking: {missing_in_banking}")
        if extra_in_banking:
            print_info(f"Extra in Banking: {extra_in_banking}")
        
        # Check common keys
        common_keys = academy_keys & banking_keys
        for key in common_keys:
            if isinstance(academy_data[key], (dict, list)):
                if type(academy_data[key]) != type(banking_data[key]):
                    print_warning(f"Type mismatch for '{key}': Academy={type(academy_data[key])}, Banking={type(banking_data[key])}")
        
        if not missing_in_banking:
            print_success(f"{label}: Structure matches!")
            return True
        return False
    return True

def main():
    print_header("BANKING vs ACADEMY SPORTS PARITY TEST")
    
    results = {
        'passed': 0,
        'failed': 0,
        'warnings': 0
    }
    
    # ========================================================================
    # TEST 1: Check Backend Status
    # ========================================================================
    print_header("TEST 1: Backend Status")
    
    success, academy_status = test_api_endpoint("/api/academy/status")
    if success:
        print_success(f"Academy Status: OK")
        results['passed'] += 1
    else:
        print_error("Academy Status: FAILED")
        results['failed'] += 1
    
    success, banking_status = test_api_endpoint("/api/banking/status")
    if success:
        print_success(f"Banking Status: OK")
        results['passed'] += 1
    else:
        print_error("Banking Status: FAILED")
        results['failed'] += 1
    
    # ========================================================================
    # TEST 2: Agent A Results Structure
    # ========================================================================
    print_header("TEST 2: Agent A Results Structure")
    
    success, academy_agent_a = test_api_endpoint("/api/academy/agent_a/results")
    success2, banking_agent_a = test_api_endpoint("/api/banking/agent_a/results")
    
    if success and success2:
        academy_results = academy_agent_a.get('results', {})
        banking_results = banking_agent_a.get('results', {})
        
        # Check personas structure
        if 'personas' in academy_results and 'personas' in banking_results:
            academy_persona = list(academy_results['personas'].values())[0]
            banking_persona = list(banking_results['personas'].values())[0]
            
            if compare_structures(academy_persona, banking_persona, "Persona Structure"):
                results['passed'] += 1
            else:
                results['failed'] += 1
                
            # Check for image enrichment
            print(f"\n{Colors.BOLD}Image Enrichment Check:{Colors.END}")
            if 'image_url' in banking_persona:
                print_success(f"Banking has image_url: {banking_persona['image_url'][:50]}...")
                results['passed'] += 1
            else:
                print_error("Banking missing image_url")
                results['failed'] += 1
            
            if 'color_theme' in banking_persona:
                print_success(f"Banking has color_theme: {banking_persona['color_theme']}")
                results['passed'] += 1
            else:
                print_error("Banking missing color_theme")
                results['failed'] += 1
            
            if 'visual_emoji' in banking_persona:
                print_success(f"Banking has visual_emoji: {banking_persona['visual_emoji']}")
                results['passed'] += 1
            else:
                print_error("Banking missing visual_emoji")
                results['failed'] += 1
            
            # Check for segment explanation
            print(f"\n{Colors.BOLD}Segment Explanation Check:{Colors.END}")
            if 'segment_explanation' in academy_persona:
                print_info(f"Academy has segment_explanation with keys: {list(academy_persona['segment_explanation'].keys())}")
                
                if 'segment_explanation' in banking_persona:
                    print_success(f"Banking has segment_explanation")
                    compare_structures(
                        academy_persona['segment_explanation'],
                        banking_persona['segment_explanation'],
                        "Segment Explanation"
                    )
                    results['passed'] += 1
                else:
                    print_error("Banking missing segment_explanation")
                    results['failed'] += 1
        else:
            print_error("No personas found in Agent A results")
            results['failed'] += 1
    
    # ========================================================================
    # TEST 3: Micro Segmentation
    # ========================================================================
    print_header("TEST 3: Micro Segmentation")
    
    # Get first persona ID
    if success and success2:
        academy_personas = academy_agent_a.get('results', {}).get('personas', {})
        banking_personas = banking_agent_a.get('results', {}).get('personas', {})
        
        if academy_personas and banking_personas:
            academy_cluster_id = list(academy_personas.keys())[0]
            banking_cluster_id = list(banking_personas.keys())[0]
            
            # Create micro segments
            print_info(f"Creating Academy micro segments for cluster {academy_cluster_id}...")
            success_a, _ = test_api_endpoint(f"/api/academy/micro-segments/{academy_cluster_id}", method="POST")
            
            print_info(f"Creating Banking micro segments for cluster {banking_cluster_id}...")
            success_b, _ = test_api_endpoint(f"/api/banking/micro-segments/{banking_cluster_id}", method="POST")
            
            if success_a and success_b:
                print_success("Micro segments created for both")
                results['passed'] += 1
                
                # Fetch micro segments
                success_a, academy_micro = test_api_endpoint(f"/api/academy/micro-segments/{academy_cluster_id}")
                success_b, banking_micro = test_api_endpoint(f"/api/banking/micro-segments/{banking_cluster_id}")
                
                if success_a and success_b:
                    academy_segs = academy_micro.get('result', {}).get('micro_segments', [])
                    banking_segs = banking_micro.get('result', {}).get('micro_segments', [])
                    
                    print_info(f"Academy micro segments: {len(academy_segs)}")
                    print_info(f"Banking micro segments: {len(banking_segs)}")
                    
                    if academy_segs and banking_segs:
                        # Compare first micro segment structure
                        if compare_structures(academy_segs[0], banking_segs[0], "Micro Segment Structure"):
                            results['passed'] += 1
                        else:
                            results['failed'] += 1
                        
                        # Check for segment explanation in micro
                        print(f"\n{Colors.BOLD}Micro Segment Explanation Check:{Colors.END}")
                        if 'segment_explanation' in academy_segs[0]:
                            print_info(f"Academy micro has segment_explanation")
                            if 'segment_explanation' in banking_segs[0]:
                                print_success(f"Banking micro has segment_explanation")
                                
                                academy_explanation = academy_segs[0]['segment_explanation']
                                banking_explanation = banking_segs[0]['segment_explanation']
                                
                                # Check explanation keys
                                required_keys = ['segment_definition', 'key_behaviors', 'marketing_recommendations']
                                missing = [k for k in required_keys if k not in banking_explanation]
                                if missing:
                                    print_error(f"Banking micro explanation missing: {missing}")
                                    results['failed'] += 1
                                else:
                                    print_success("Banking micro explanation has all required keys")
                                    results['passed'] += 1
                            else:
                                print_error("Banking micro missing segment_explanation")
                                results['failed'] += 1
            else:
                print_error("Failed to create micro segments")
                results['failed'] += 1
    
    # ========================================================================
    # TEST 4: Agent B Endpoints
    # ========================================================================
    print_header("TEST 4: Agent B Endpoints")
    
    # Check if customers endpoint exists
    success_a, academy_customers = test_api_endpoint("/api/academy/customers")
    success_b, banking_customers = test_api_endpoint("/api/banking/customers")
    
    if success_a and success_b:
        print_success("Both have customer endpoints")
        results['passed'] += 1
    else:
        print_error("Customer endpoints missing")
        results['failed'] += 1
    
    # ========================================================================
    # TEST 5: API Endpoint Parity
    # ========================================================================
    print_header("TEST 5: API Endpoint Parity")
    
    academy_endpoints = [
        "/api/academy/status",
        "/api/academy/agent_a/results",
        "/api/academy/customers",
        "/api/academy/products"
    ]
    
    banking_endpoints = [
        "/api/banking/status",
        "/api/banking/agent_a/results",
        "/api/banking/customers",
        "/api/banking/products"
    ]
    
    print(f"\n{Colors.BOLD}Academy Endpoints:{Colors.END}")
    for endpoint in academy_endpoints:
        success, _ = test_api_endpoint(endpoint)
        if success:
            print_success(f"{endpoint}: OK")
        else:
            print_error(f"{endpoint}: FAILED")
    
    print(f"\n{Colors.BOLD}Banking Endpoints:{Colors.END}")
    for endpoint in banking_endpoints:
        success, _ = test_api_endpoint(endpoint)
        if success:
            print_success(f"{endpoint}: OK")
        else:
            print_error(f"{endpoint}: FAILED")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print_header("TEST SUMMARY")
    
    total = results['passed'] + results['failed']
    pass_rate = (results['passed'] / total * 100) if total > 0 else 0
    
    print(f"{Colors.BOLD}Total Tests:{Colors.END} {total}")
    print(f"{Colors.GREEN}Passed:{Colors.END} {results['passed']}")
    print(f"{Colors.RED}Failed:{Colors.END} {results['failed']}")
    print(f"{Colors.YELLOW}Warnings:{Colors.END} {results['warnings']}")
    print(f"{Colors.BOLD}Pass Rate:{Colors.END} {pass_rate:.1f}%\n")
    
    if pass_rate >= 90:
        print_success("🎉 EXCELLENT! Banking has near-perfect parity with Academy Sports!")
    elif pass_rate >= 75:
        print_warning("⚠️  GOOD! But some improvements needed for full parity")
    else:
        print_error("❌ NEEDS WORK! Several features missing for parity")
    
    return results

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}Test failed with error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
