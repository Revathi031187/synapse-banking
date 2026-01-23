"""Initialize ChromaDB for Academy Sports products"""
from utils.chromadb_academy_init import initialize_academy_chromadb

print("Starting ChromaDB initialization...")
print("This may take 30-60 seconds...\n")

result = initialize_academy_chromadb(force_recreate=True)

product_init = result['product_initialization']

print(f"\n{'='*60}")
print(f"Status: {product_init['status']}")
print(f"Products: {product_init.get('product_count', 0)}")
print(f"Time: {product_init.get('elapsed_time', 0)}s")
print(f"Model: {product_init.get('embedding_model', 'N/A')}")
print(f"{'='*60}\n")

if product_init['status'] == 'success':
    print("SUCCESS! ChromaDB is ready for semantic search!")
    print("\nNext steps:")
    print("1. Run: py -3.10 test_phase1_phase2.py")
    print("2. Or open: http://localhost:5173/academy")
else:
    print(f"ERROR: {product_init.get('error', 'Unknown error')}")

