"""
Quick script to clear Python cache folders
Run this before restarting the backend
"""
import os
import shutil
from pathlib import Path

def clear_cache():
    """Delete __pycache__ folders"""
    base_path = Path(__file__).parent
    
    folders_to_clear = [
        base_path / 'agents' / '__pycache__',
        base_path / 'api' / '__pycache__',
        base_path / 'utils' / '__pycache__',
    ]
    
    print("\n" + "="*80)
    print("CLEARING PYTHON CACHE")
    print("="*80 + "\n")
    
    for folder in folders_to_clear:
        if folder.exists():
            try:
                shutil.rmtree(folder)
                print(f"✓ Deleted: {folder}")
            except Exception as e:
                print(f"✗ Failed to delete {folder}: {e}")
        else:
            print(f"  {folder} (not found)")
    
    print("\n" + "="*80)
    print("CACHE CLEARED SUCCESSFULLY!")
    print("="*80)
    print("\nNow restart your backend:")
    print("  py -3.10 api/main_unified_chromadb.py")
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    clear_cache()

