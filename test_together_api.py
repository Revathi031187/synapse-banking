"""Test Together AI API directly to see exact error"""
import requests
import os
from dotenv import load_dotenv
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

API_KEY = os.getenv("TOGETHER_API_KEY")
BASE_URL = "https://api.together.xyz/v1"

print(f"Testing Together AI API...")
print(f"API Key: ...{API_KEY[-8:]}")
print(f"Base URL: {BASE_URL}")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Test 1: List available models
print("\n--- Test 1: Listing Models ---")
try:
    response = requests.get(f"{BASE_URL}/models", headers=headers, timeout=10, verify=False)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        models = response.json()
        print(f"Available models: {len(models.get('data', []))}")
        # Find embedding models
        embedding_models = [m for m in models.get('data', []) if 'embed' in m.get('id', '').lower()]
        print(f"\nEmbedding models found: {len(embedding_models)}")
        for m in embedding_models[:5]:
            print(f"  - {m.get('id', 'Unknown')}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Try creating embeddings with different models
models_to_test = [
    "togethercomputer/m2-bert-80M-8k-retrieval",
    "BAAI/bge-large-en-v1.5",
    "WhereIsAI/UAE-Large-V1",
    "togethercomputer/m2-bert-80M-32k-retrieval"
]

print("\n--- Test 2: Testing Embedding Models ---")
for model in models_to_test:
    print(f"\nTrying model: {model}")
    try:
        payload = {
            "model": model,
            "input": ["test text"]
        }
        response = requests.post(
            f"{BASE_URL}/embeddings",
            json=payload,
            headers=headers,
            timeout=10,
            verify=False
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  SUCCESS! Embedding dim: {len(data['data'][0]['embedding'])}")
            break
        else:
            print(f"  Error: {response.text[:200]}")
    except Exception as e:
        print(f"  Exception: {e}")

print("\n--- Test Complete ---")

