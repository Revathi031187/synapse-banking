"""
Quick update: Add cluster names to existing ChromaDB personas
WITHOUT re-clustering (faster than full reinitialization)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.chromadb_client import get_chroma_client, COLLECTIONS
from utils.cluster_naming import cluster_namer
from utils.logger import get_logger

logger = get_logger(__name__)

def update_banking_cluster_names():
    """Update banking persona cluster names in-place"""
    print("=" * 70)
    print("🏦 UPDATING BANKING CLUSTER NAMES")
    print("=" * 70)
    
    chroma = get_chroma_client()
    
    # Get all banking personas
    personas_data = chroma.get_all(COLLECTIONS['banking_personas'])
    
    if not personas_data['ids']:
        print("❌ No banking personas found. Please run full initialization first.")
        return False
    
    print(f"📊 Found {len(personas_data['ids'])} banking personas")
    
    # Update each persona with cluster name
    for i, persona_id in enumerate(personas_data['ids']):
        metadata = personas_data['metadatas'][i]
        
        # Generate cluster name
        cluster_name = cluster_namer.name_banking_cluster(metadata)
        
        # Update metadata
        metadata['cluster_name'] = cluster_name
        
        # Update in ChromaDB
        chroma.update_documents(
            collection_name=COLLECTIONS['banking_personas'],
            ids=[persona_id],
            metadatas=[metadata]
        )
        
        print(f"  ✓ Cluster {metadata.get('cluster_id')}: '{cluster_name}'")
    
    print(f"✅ Updated {len(personas_data['ids'])} banking personas")
    return True

def update_retail_cluster_names():
    """Update retail persona cluster names in-place"""
    print("\n" + "=" * 70)
    print("🛒 UPDATING RETAIL CLUSTER NAMES")
    print("=" * 70)
    
    chroma = get_chroma_client()
    
    # Get all retail personas
    personas_data = chroma.get_all(COLLECTIONS['retail_personas'])
    
    if not personas_data['ids']:
        print("❌ No retail personas found. Please run full initialization first.")
        return False
    
    print(f"📊 Found {len(personas_data['ids'])} retail personas")
    
    # Update each persona with cluster name
    for i, persona_id in enumerate(personas_data['ids']):
        metadata = personas_data['metadatas'][i]
        
        # Generate cluster name
        cluster_name = cluster_namer.name_retail_cluster(metadata)
        
        # Update metadata
        metadata['cluster_name'] = cluster_name
        
        # Update in ChromaDB
        chroma.update_documents(
            collection_name=COLLECTIONS['retail_personas'],
            ids=[persona_id],
            metadatas=[metadata]
        )
        
        print(f"  ✓ Cluster {metadata.get('cluster_id')}: '{cluster_name}'")
    
    print(f"✅ Updated {len(personas_data['ids'])} retail personas")
    return True

def main():
    print("\n" + "=" * 70)
    print("🏷️  QUICK CLUSTER NAME UPDATE")
    print("=" * 70)
    print("This script updates cluster names WITHOUT re-clustering")
    print("Time: ~5-10 seconds")
    print("=" * 70 + "\n")
    
    try:
        # Update banking
        banking_success = update_banking_cluster_names()
        
        # Update retail
        retail_success = update_retail_cluster_names()
        
        if banking_success and retail_success:
            print("\n" + "=" * 70)
            print("✅ ALL CLUSTER NAMES UPDATED SUCCESSFULLY!")
            print("=" * 70)
            print("\n📌 NEXT STEPS:")
            print("1. Restart your backend: py -3.10 api\\main_unified_chromadb.py")
            print("2. Refresh your browser at http://localhost:5173")
            print("3. You should now see meaningful cluster names!")
            print("=" * 70 + "\n")
        else:
            print("\n❌ Some updates failed. Consider running full initialization.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 If this fails, run full initialization:")
        print("   py -3.10 scripts\\initialize_chromadb.py")

if __name__ == "__main__":
    main()

