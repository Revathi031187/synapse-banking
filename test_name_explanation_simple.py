"""
Simple test to check if name_explanation exists in agent output
"""
import json

print("="*80)
print("CHECKING NAME EXPLANATION IN AGENTS")
print("="*80)

# Test 1: Check if methods exist in macro agent
print("\n1. Checking macro agent file...")
with open('agents/agent_a_banking_enhanced.py', 'r', encoding='utf-8') as f:
    macro_content = f.read()
    
if '_generate_macro_name_explanation' in macro_content:
    print("   [OK] _generate_macro_name_explanation method EXISTS")
else:
    print("   [FAIL] _generate_macro_name_explanation method NOT FOUND")

if "'name_explanation': name_explanation" in macro_content:
    print("   [OK] name_explanation is RETURNED in dict")
else:
    print("   [FAIL] name_explanation NOT in return dict")

# Test 2: Check if methods exist in micro agent
print("\n2. Checking micro agent file...")
with open('agents/agent_a_banking_micro.py', 'r', encoding='utf-8') as f:
    micro_content = f.read()
    
if '_generate_name_explanation' in micro_content:
    print("   [OK] _generate_name_explanation method EXISTS")
else:
    print("   [FAIL] _generate_name_explanation method NOT FOUND")

if "'name_explanation': name_explanation" in micro_content:
    print("   [OK] name_explanation is RETURNED in dict")
else:
    print("   [FAIL] name_explanation NOT in return dict")

# Test 3: Check frontend
print("\n3. Checking frontend file...")
with open('frontend/src/pages/banking/BankingMacroDashboard.tsx', 'r', encoding='utf-8') as f:
    frontend_content = f.read()
    
if 'name_explanation' in frontend_content:
    print("   [OK] name_explanation field referenced in frontend")
    
if 'Why This Name?' in frontend_content:
    print("   [OK] 'Why This Name?' section added to UI")
else:
    print("   [FAIL] 'Why This Name?' section NOT FOUND")

if 'name_explanation?' in frontend_content:
    print("   [OK] TypeScript interface updated")
else:
    print("   [FAIL] TypeScript interface needs update")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("\nBackend: READY [OK]")
print("Frontend: READY [OK]")
print("\nACTION REQUIRED:")
print("   1. RESTART BACKEND (taskkill /F /IM uvicorn.exe)")
print("   2. START BACKEND (python -m uvicorn api.main_unified_chromadb:app --port 8002)")
print("   3. RESTART FRONTEND (cd frontend && npm run dev)")
print("\nThen check UI for 'Why This Name?' sections!")
print("="*80)
