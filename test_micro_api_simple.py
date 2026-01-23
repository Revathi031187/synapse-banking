"""Test micro segments API - simple version without unicode"""
import requests
import json

API_BASE = "http://localhost:8002"

print("="*80)
print("GET /api/academy/micro-segments/0")
print("="*80)

response = requests.get(f"{API_BASE}/api/academy/micro-segments/0")
print(f"Status: {response.status_code}\n")

data = response.json()
print("Has 'success':", 'success' in data)
print("Has 'result':", 'result' in data)

if 'result' in data:
    result = data['result']
    print("result type:", type(result).__name__)
    
    if isinstance(result, dict):
        print("result keys:", list(result.keys()))
        
        if 'micro_segments' in result:
            micro_segs = result['micro_segments']
            print("\nmicro_segments type:", type(micro_segs).__name__)
            
            if isinstance(micro_segs, list):
                print("micro_segments length:", len(micro_segs))
                if len(micro_segs) > 0:
                    print("\nFIRST ITEM:")
                    print(json.dumps(micro_segs[0], indent=2))
                else:
                    print("\nERROR: micro_segments is an EMPTY LIST!")
            elif isinstance(micro_segs, dict):
                print("ERROR: micro_segments is a DICT with keys:", list(micro_segs.keys()))
                print("This is the bug - frontend expects an ARRAY!")
            else:
                print("ERROR: micro_segments is", type(micro_segs).__name__)
        else:
            print("\nERROR: No 'micro_segments' in result!")
            print("Available keys:", list(result.keys()))

print("\n" + "="*80)

