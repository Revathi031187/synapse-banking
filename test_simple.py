"""
Simple diagnostic test - no complex libraries
"""
import sys
print(f"Python version: {sys.version}")
print("Basic imports test...")

try:
    import json
    print("✓ json")
except Exception as e:
    print(f"✗ json: {e}")

try:
    import requests
    print("✓ requests")
except Exception as e:
    print(f"✗ requests: {e}")

try:
    import pandas
    print("✓ pandas")
except Exception as e:
    print(f"✗ pandas: {e}")

try:
    import numpy
    print("✓ numpy")
except Exception as e:
    print(f"✗ numpy: {e}")

try:
    import colorama
    print("✓ colorama")
except Exception as e:
    print(f"✗ colorama: {e}")

print("\nAll imports successful!")
print("\nTesting API connection...")

try:
    import requests
    response = requests.get("http://localhost:8002/health", timeout=5)
    print(f"✓ Backend is accessible: {response.status_code}")
except Exception as e:
    print(f"✗ Backend connection failed: {e}")

print("\n" + "="*60)
print("DIAGNOSTIC COMPLETE")
print("="*60)

input("\nPress Enter to exit...")
