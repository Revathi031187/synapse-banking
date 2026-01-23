"""
Initialize ChromaDB for Academy Sports data
Creates collections and loads embeddings for fast retrieval
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
from tqdm import tqdm

print("=" * 70)
print("🏕️  Academy Sports ChromaDB Initialization")
print("=" * 70)

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)

# Initialize embedding model
print("\n📦 Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Model loaded")

# Data directory
data_dir = Path('data/preloaded/academy_sports')

def create_customer_embeddings(version='v1'):
    """Create embeddings for customers"""
    print(f"\n{'='*70}")
    print(f"👥 Processing Academy Sports Customers ({version.upper()})")
    print(f"{'='*70}")
    
    suffix = '_v2' if version == 'v2' else ''
    customers_df = pd.read_csv(data_dir / f'customers{suffix}.csv')
    
    print(f"Loaded {len(customers_df)} customers")
    
    # Create collection
    collection_name = f'academy_customers_{version}'
    try:
        chroma_client.delete_collection(collection_name)
    except:
        pass
    
    collection = chroma_client.create_collection(
        name=collection_name,
        metadata={"description": f"Academy Sports customers {version}"}
    )
    
    # Create customer descriptions for embedding
    documents = []
    metadatas = []
    ids = []
    
    for idx, row in tqdm(customers_df.iterrows(), total=len(customers_df), desc="Processing customers"):
        # Create rich description
        doc = f"""
        Customer {row['customer_name']} (ID: {row['customer_id']})
        Age: {row['age']}, Distance: {row['distance_to_store']:.1f} miles
        Total Spend: ${row['total_spend_12mo']:.2f}
        Purchase Frequency: {row['purchase_frequency']}
        Search Specificity: {row['search_specificity']:.2f}
        Bundle Affinity: {row['bundle_affinity']:.2f}
        Price Sort Frequency: {row['price_sort_frequency']:.2f}
        Spec Expansion Rate: {row['spec_expansion_rate']:.2f}
        """
        
        documents.append(doc)
        
        # Store metadata
        metadata = {
            'customer_id': str(row['customer_id']),
            'customer_name': str(row['customer_name']),
            'age': int(row['age']),
            'total_spend_12mo': float(row['total_spend_12mo']),
            'purchase_frequency': int(row['purchase_frequency']),
            'search_specificity': float(row['search_specificity']),
            'bundle_affinity': float(row['bundle_affinity']),
            'price_sort_frequency': float(row['price_sort_frequency']),
            'spec_expansion_rate': float(row['spec_expansion_rate']),
            'distance_to_store': float(row['distance_to_store'])
        }
        
        metadatas.append(metadata)
        ids.append(str(row['customer_id']))
    
    # Generate embeddings
    print("\n🔄 Generating embeddings...")
    embeddings = model.encode(documents, show_progress_bar=True)
    
    # Add to collection in batches
    batch_size = 1000
    for i in tqdm(range(0, len(ids), batch_size), desc="Adding to ChromaDB"):
        end_idx = min(i + batch_size, len(ids))
        collection.add(
            documents=documents[i:end_idx],
            embeddings=embeddings[i:end_idx].tolist(),
            metadatas=metadatas[i:end_idx],
            ids=ids[i:end_idx]
        )
    
    print(f"✅ Added {len(ids)} customers to ChromaDB collection: {collection_name}")
    return collection

def create_product_embeddings(version='v1'):
    """Create embeddings for products"""
    print(f"\n{'='*70}")
    print(f"🛍️  Processing Academy Sports Products ({version.upper()})")
    print(f"{'='*70}")
    
    suffix = '_v2' if version == 'v2' else ''
    products_df = pd.read_csv(data_dir / f'products{suffix}.csv')
    
    print(f"Loaded {len(products_df)} products")
    
    # Create collection
    collection_name = f'academy_products_{version}'
    try:
        chroma_client.delete_collection(collection_name)
    except:
        pass
    
    collection = chroma_client.create_collection(
        name=collection_name,
        metadata={"description": f"Academy Sports products {version}"}
    )
    
    # Create product descriptions
    documents = []
    metadatas = []
    ids = []
    
    for idx, row in tqdm(products_df.iterrows(), total=len(products_df), desc="Processing products"):
        # Create rich description
        doc = f"""
        {row['product_name']} (SKU: {row['product_id']})
        Brand: {row['brand']} ({row['brand_tier']})
        Category: {row['main_category']} - {row['subcategory']}
        Price: ${row['price']:.2f}
        Setup: {row['setup_type']}
        Complexity: {row['complexity']}
        Bundle: {row['bundle_compatible']}
        Capacity: {row['capacity']}
        Weight: {row['weight_class']}
        Weather: {row['weatherproof']}
        Rating: {row['avg_rating']}/5.0
        """
        
        documents.append(doc)
        
        # Store metadata
        metadata = {
            'product_id': str(row['product_id']),
            'product_name': str(row['product_name']),
            'brand': str(row['brand']),
            'main_category': str(row['main_category']),
            'subcategory': str(row['subcategory']),
            'price': float(row['price']),
            'brand_tier': str(row['brand_tier']),
            'setup_type': str(row['setup_type']),
            'complexity': str(row['complexity'])
        }
        
        metadatas.append(metadata)
        ids.append(str(row['product_id']))
    
    # Generate embeddings
    print("\n🔄 Generating embeddings...")
    embeddings = model.encode(documents, show_progress_bar=True)
    
    # Add to collection
    collection.add(
        documents=documents,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"✅ Added {len(ids)} products to ChromaDB collection: {collection_name}")
    return collection

def create_persona_collection():
    """Create persona definitions collection"""
    print(f"\n{'='*70}")
    print("🎯 Creating Persona Definitions Collection")
    print(f"{'='*70}")
    
    collection_name = 'academy_personas'
    try:
        chroma_client.delete_collection(collection_name)
    except:
        pass
    
    collection = chroma_client.create_collection(
        name=collection_name,
        metadata={"description": "Academy Sports persona definitions"}
    )
    
    personas = {
        'First_Time_Camper': {
            'description': 'New to camping, needs simplicity and guidance. Generic search terms, rarely expands specs, loves bundles, always sorts by price. Price-sensitive $50-$300/year.',
            'characteristics': {
                'search_specificity': 2.0,
                'bundle_affinity': 0.85,
                'price_sort_frequency': 0.85,
                'spec_expansion_rate': 0.10
            }
        },
        'Family_Socializer': {
            'description': 'Occasional camper, values comfort and convenience. Attribute-based searches, some research, likes bundles, balanced on price. Moderate spend $300-$1,000/year.',
            'characteristics': {
                'search_specificity': 3.0,
                'bundle_affinity': 0.55,
                'price_sort_frequency': 0.45,
                'spec_expansion_rate': 0.35
            }
        },
        'Seasoned_Pro': {
            'description': 'Expert camper, technical knowledge, brand loyal. Model-specific searches, always expands specs, no bundles, doesn\'t sort by price. High spend $800-$3,000/year.',
            'characteristics': {
                'search_specificity': 4.5,
                'bundle_affinity': 0.10,
                'price_sort_frequency': 0.10,
                'spec_expansion_rate': 0.80
            }
        }
    }
    
    documents = []
    metadatas = []
    ids = []
    
    for persona_name, persona_data in personas.items():
        documents.append(persona_data['description'])
        metadatas.append({
            'persona_name': persona_name,
            **{f'avg_{k}': v for k, v in persona_data['characteristics'].items()}
        })
        ids.append(persona_name)
    
    # Generate embeddings
    embeddings = model.encode(documents)
    
    collection.add(
        documents=documents,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"✅ Added {len(ids)} personas to ChromaDB")
    return collection

# Main execution
if __name__ == "__main__":
    print("\n🚀 Starting ChromaDB initialization for Academy Sports...")
    
    try:
        # V1 Data
        print("\n" + "="*70)
        print("Processing V1 Dataset")
        print("="*70)
        create_customer_embeddings('v1')
        create_product_embeddings('v1')
        
        # V2 Data
        print("\n" + "="*70)
        print("Processing V2 Dataset")
        print("="*70)
        create_customer_embeddings('v2')
        create_product_embeddings('v2')
        
        # Personas
        create_persona_collection()
        
        # Summary
        print("\n" + "="*70)
        print("✅ INITIALIZATION COMPLETE")
        print("="*70)
        
        collections = chroma_client.list_collections()
        print(f"\n📊 Created {len(collections)} ChromaDB collections:")
        for coll in collections:
            count = coll.count()
            print(f"   - {coll.name}: {count} items")
        
        print("\n✅ Academy Sports data loaded into ChromaDB successfully!")
        print("🚀 Ready for fast queries!\n")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
