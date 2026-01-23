"""
Force restart backend with clean Python cache
This ensures the new enhanced agent code is loaded
"""

import os
import sys
import subprocess
import time

# Find and remove __pycache__ directories to force module reload
print("Clearing Python cache...")
for root, dirs, files in os.walk('.'):
    if '__pycache__' in dirs:
        cache_dir = os.path.join(root, '__pycache__')
        print(f"Removing: {cache_dir}")
        try:
            import shutil
            shutil.rmtree(cache_dir)
        except Exception as e:
            print(f"Warning: Could not remove {cache_dir}: {e}")

# Remove .pyc files
print("\nRemoving .pyc files...")
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.pyc'):
            pyc_file = os.path.join(root, file)
            print(f"Removing: {pyc_file}")
            try:
                os.remove(pyc_file)
            except Exception as e:
                print(f"Warning: Could not remove {pyc_file}: {e}")

print("\n" + "="*70)
print("✅ Cache cleared!")
print("="*70)
print("\nNow restart your backend:")
print("  1. Press Ctrl+C in the backend terminal")
print("  2. Run: py -3.10 api/main_unified_chromadb.py")
print("="*70)

