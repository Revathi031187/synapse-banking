"""
Initialize ChromaDB with Pre-computed Data
This script loads, clusters, and stores all data for instant retrieval
Run this once during deployment or when data needs to be refreshed
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

from utils.chromadb_client import get_chroma_client, COLLECTIONS
from utils.embedding_service import EmbeddingService
from utils.logger import get_logger
from utils.cluster_naming import cluster_namer
from ml_models.clustering import AdvancedClustering
from sklearn.preprocessing import StandardScaler

logger = get_logger(__name__)


class ChromaDBInitializer:
    """Handles data initialization and pre-computation"""
    
    def __init__(self):
        self.chroma = get_chroma_client()
        self.embedding_service = EmbeddingService()
        self.clustering = AdvancedClustering()
        logger.info("🚀 Initializer ready")
    
    def initialize_banking(self, dataset_path: str = "data/preloaded/banking_nba", n_clusters: int = 5):
        """
        Initialize banking data in ChromaDB
        
        Args:
            dataset_path: Path to banking dataset
            n_clusters: Number of clusters for segmentation
        """
        logger.info(f"🏦 Initializing Banking Data from {dataset_path}")
        
        # 1. Load customer data
        customers_df = pd.read_csv(Path(dataset_path) / "customers.csv")
        logger.info(f"📊 Loaded {len(customers_df)} customers")
        
        # 2. Load products
        products_df = pd.read_csv(Path(dataset_path) / "products.csv")
        logger.info(f"📦 Loaded {len(products_df)} products")
        
        # 3. Perform clustering
        logger.info("🔬 Performing clustering analysis...")
        feature_matrix, feature_df = self._build_banking_features(customers_df)
        
        # Find optimal clusters if auto
        if n_clusters == 0:
            metrics = self.clustering.find_optimal_k(feature_matrix, k_range=range(2, 11))
            n_clusters = metrics['optimal_k']
            logger.info(f"✅ Auto-selected {n_clusters} clusters")
        
        # Perform clustering
        clustering_result = self.clustering.kmeans_clustering(feature_matrix, n_clusters=n_clusters)
        cluster_labels = clustering_result['labels']
        cluster_metrics = {
            **clustering_result['metrics'],
            'inertia': clustering_result['inertia']
        }
        
        # Add cluster labels to customers
        customers_df['cluster_id'] = cluster_labels
        
        # 4. Generate personas
        personas = self._generate_banking_personas(customers_df, feature_df)
        logger.info(f"✅ Generated {len(personas)} personas")
        
        # 5. Store customers in ChromaDB
        self._store_banking_customers(customers_df)
        
        # 6. Store personas in ChromaDB
        self._store_banking_personas(personas, cluster_metrics)
        
        # 7. Store products in ChromaDB
        self._store_banking_products(products_df)
        
        logger.info("✅ Banking data initialization complete!")
        return {
            "customers": len(customers_df),
            "personas": len(personas),
            "products": len(products_df),
            "n_clusters": n_clusters,
            "cluster_metrics": cluster_metrics
        }
    
    def initialize_retail(self, dataset_path: str = "data/preloaded/retail_nba", n_clusters: int = 5):
        """
        Initialize retail data in ChromaDB
        
        Args:
            dataset_path: Path to retail dataset
            n_clusters: Number of clusters for segmentation
        """
        logger.info(f"🛒 Initializing Retail Data from {dataset_path}")
        
        # 1. Load customer data
        customers_df = pd.read_csv(Path(dataset_path) / "customers.csv")
        logger.info(f"📊 Loaded {len(customers_df)} customers")
        
        # 2. Load products
        products_df = pd.read_csv(Path(dataset_path) / "products.csv")
        logger.info(f"📦 Loaded {len(products_df)} products")
        
        # 3. Perform clustering
        logger.info("🔬 Performing clustering analysis...")
        feature_matrix, feature_df = self._build_retail_features(customers_df)
        
        # Find optimal clusters if auto
        if n_clusters == 0:
            metrics = self.clustering.find_optimal_k(feature_matrix, k_range=range(2, 11))
            n_clusters = metrics['optimal_k']
            logger.info(f"✅ Auto-selected {n_clusters} clusters")
        
        # Perform clustering
        clustering_result = self.clustering.kmeans_clustering(feature_matrix, n_clusters=n_clusters)
        cluster_labels = clustering_result['labels']
        cluster_metrics = {
            **clustering_result['metrics'],
            'inertia': clustering_result['inertia']
        }
        
        # Add cluster labels to customers
        customers_df['cluster_id'] = cluster_labels
        
        # 4. Generate personas
        personas = self._generate_retail_personas(customers_df, feature_df)
        logger.info(f"✅ Generated {len(personas)} personas")
        
        # 5. Store customers in ChromaDB
        self._store_retail_customers(customers_df)
        
        # 6. Store personas in ChromaDB
        self._store_retail_personas(personas, cluster_metrics)
        
        # 7. Store products in ChromaDB
        self._store_retail_products(products_df)
        
        logger.info("✅ Retail data initialization complete!")
        return {
            "customers": len(customers_df),
            "personas": len(personas),
            "products": len(products_df),
            "n_clusters": n_clusters,
            "cluster_metrics": cluster_metrics
        }
    
    def _build_banking_features(self, customers_df: pd.DataFrame):
        """Build feature matrix for banking clustering"""
        feature_columns = [
            'age', 'income', 'credit_score', 'tenure_months',
            'login_frequency_30d', 'transaction_volume_30d',
            'avg_transaction_amount', 'intent_score'
        ]
        
        feature_df = customers_df[feature_columns].fillna(0)
        scaler = StandardScaler()
        feature_matrix = scaler.fit_transform(feature_df)
        
        return feature_matrix, feature_df
    
    def _build_retail_features(self, customers_df: pd.DataFrame):
        """Build feature matrix for retail clustering"""
        feature_columns = [
            'age', 'income', 'recency_score', 'frequency_score',
            'monetary_score', 'avg_order_value', 'web_visits_30d',
            'app_engagement_score', 'intent_score'
        ]
        
        feature_df = customers_df[feature_columns].fillna(0)
        scaler = StandardScaler()
        feature_matrix = scaler.fit_transform(feature_df)
        
        return feature_matrix, feature_df
    
    def _generate_banking_personas(self, customers_df: pd.DataFrame, feature_df: pd.DataFrame):
        """Generate persona summaries for banking"""
        personas = []
        
        for cluster_id in sorted(customers_df['cluster_id'].unique()):
            cluster_customers = customers_df[customers_df['cluster_id'] == cluster_id]
            
            persona = {
                'cluster_id': int(cluster_id),
                'size': len(cluster_customers),
                'percentage': len(cluster_customers) / len(customers_df) * 100,
                
                # Demographics
                'avg_age': float(cluster_customers['age'].mean()),
                'avg_income': float(cluster_customers['income'].mean()),
                'avg_credit_score': float(cluster_customers['credit_score'].mean()),
                
                # Engagement
                'avg_tenure': float(cluster_customers['tenure_months'].mean()),
                'avg_login_frequency': float(cluster_customers['login_frequency_30d'].mean()),
                'avg_engagement': float(cluster_customers['login_frequency_30d'].mean()),
                
                # Intent
                'avg_intent': float(cluster_customers['intent_score'].mean()),
                
                # Channel preference
                'dominant_channel': cluster_customers['channel_preference'].mode()[0] if len(cluster_customers['channel_preference'].mode()) > 0 else 'mobile',
            }
            
            # Generate meaningful cluster name
            persona['cluster_name'] = cluster_namer.name_banking_cluster(persona)
            
            personas.append(persona)
        
        logger.info(f"   ✓ Named Cluster {cluster_id}: '{persona['cluster_name']}'")
        
        return personas
    
    def _generate_retail_personas(self, customers_df: pd.DataFrame, feature_df: pd.DataFrame):
        """Generate persona summaries for retail"""
        personas = []
        
        for cluster_id in sorted(customers_df['cluster_id'].unique()):
            cluster_customers = customers_df[customers_df['cluster_id'] == cluster_id]
            
            persona = {
                'cluster_id': int(cluster_id),
                'size': len(cluster_customers),
                'percentage': len(cluster_customers) / len(customers_df) * 100,
                
                # Demographics
                'avg_age': float(cluster_customers['age'].mean()),
                'avg_income': float(cluster_customers['income'].mean()),
                
                # RFM
                'avg_recency': float(cluster_customers['recency_score'].mean()),
                'avg_frequency': float(cluster_customers['frequency_score'].mean()),
                'avg_monetary': float(cluster_customers['monetary_score'].mean()),
                
                # Engagement
                'avg_engagement': float(cluster_customers['web_visits_30d'].mean()),
                'avg_aov': float(cluster_customers['avg_order_value'].mean()),
                
                # Intent
                'avg_intent': float(cluster_customers['intent_score'].mean()),
                
                # Category preference
                'dominant_category': cluster_customers['preferred_category'].mode()[0] if len(cluster_customers['preferred_category'].mode()) > 0 else 'Unknown',
            }
            
            # Generate meaningful cluster name
            persona['cluster_name'] = cluster_namer.name_retail_cluster(persona)
            
            personas.append(persona)
        
        logger.info(f"   ✓ Named Cluster {cluster_id}: '{persona['cluster_name']}'")
        
        return personas
    
    def _store_banking_customers(self, customers_df: pd.DataFrame):
        """Store banking customers in ChromaDB"""
        logger.info("💾 Storing banking customers...")
        
        # Delete existing collection
        self.chroma.delete_collection(COLLECTIONS['banking_customers'])
        
        # Convert to documents
        documents, metadatas, ids = self.embedding_service.dataframe_to_documents(
            customers_df,
            self.embedding_service.customer_to_text_banking,
            id_column='customer_id'
        )
        
        # Store in ChromaDB
        self.chroma.add_documents(
            collection_name=COLLECTIONS['banking_customers'],
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def _store_retail_customers(self, customers_df: pd.DataFrame):
        """Store retail customers in ChromaDB"""
        logger.info("💾 Storing retail customers...")
        
        # Delete existing collection
        self.chroma.delete_collection(COLLECTIONS['retail_customers'])
        
        # Convert to documents
        documents, metadatas, ids = self.embedding_service.dataframe_to_documents(
            customers_df,
            self.embedding_service.customer_to_text_retail,
            id_column='customer_id'
        )
        
        # Store in ChromaDB
        self.chroma.add_documents(
            collection_name=COLLECTIONS['retail_customers'],
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def _store_banking_personas(self, personas: list, cluster_metrics: dict):
        """Store banking personas in ChromaDB"""
        logger.info("💾 Storing banking personas...")
        
        # Delete existing collection
        self.chroma.delete_collection(COLLECTIONS['banking_personas'])
        
        # Prepare documents
        documents = []
        metadatas = []
        ids = []
        
        for persona in personas:
            # Add cluster metrics
            persona_with_metrics = {**persona, **cluster_metrics}
            
            # Generate text
            text = self.embedding_service.persona_to_text(persona_with_metrics, 'banking')
            documents.append(text)
            
            # Metadata - filter out None values and complex types
            metadata = {}
            for k, v in persona_with_metrics.items():
                if isinstance(v, (dict, list)):
                    continue  # Skip complex types
                if v is None or (isinstance(v, float) and (pd.isna(v) or v != v)):  # None or NaN
                    continue  # Skip None/NaN values
                metadata[k] = v
            metadatas.append(metadata)
            
            # ID
            ids.append(f"persona_{persona['cluster_id']}")
        
        # Store in ChromaDB
        self.chroma.add_documents(
            collection_name=COLLECTIONS['banking_personas'],
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def _store_retail_personas(self, personas: list, cluster_metrics: dict):
        """Store retail personas in ChromaDB"""
        logger.info("💾 Storing retail personas...")
        
        # Delete existing collection
        self.chroma.delete_collection(COLLECTIONS['retail_personas'])
        
        # Prepare documents
        documents = []
        metadatas = []
        ids = []
        
        for persona in personas:
            # Add cluster metrics
            persona_with_metrics = {**persona, **cluster_metrics}
            
            # Generate text
            text = self.embedding_service.persona_to_text(persona_with_metrics, 'retail')
            documents.append(text)
            
            # Metadata - filter out None values and complex types
            metadata = {}
            for k, v in persona_with_metrics.items():
                if isinstance(v, (dict, list)):
                    continue  # Skip complex types
                if v is None or (isinstance(v, float) and (pd.isna(v) or v != v)):  # None or NaN
                    continue  # Skip None/NaN values
                metadata[k] = v
            metadatas.append(metadata)
            
            # ID
            ids.append(f"persona_{persona['cluster_id']}")
        
        # Store in ChromaDB
        self.chroma.add_documents(
            collection_name=COLLECTIONS['retail_personas'],
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def _store_banking_products(self, products_df: pd.DataFrame):
        """Store banking products in ChromaDB"""
        logger.info("💾 Storing banking products...")
        
        # Delete existing collection
        self.chroma.delete_collection(COLLECTIONS['banking_products'])
        
        # Convert to documents
        documents, metadatas, ids = self.embedding_service.dataframe_to_documents(
            products_df,
            self.embedding_service.product_to_text_banking,
            id_column='product_id'
        )
        
        # Store in ChromaDB
        self.chroma.add_documents(
            collection_name=COLLECTIONS['banking_products'],
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def _store_retail_products(self, products_df: pd.DataFrame):
        """Store retail products in ChromaDB"""
        logger.info("💾 Storing retail products...")
        
        # Delete existing collection
        self.chroma.delete_collection(COLLECTIONS['retail_products'])
        
        # Convert to documents
        documents, metadatas, ids = self.embedding_service.dataframe_to_documents(
            products_df,
            self.embedding_service.product_to_text_retail,
            id_column='product_id'
        )
        
        # Store in ChromaDB
        self.chroma.add_documents(
            collection_name=COLLECTIONS['retail_products'],
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def show_stats(self):
        """Display ChromaDB statistics"""
        logger.info("\n" + "="*80)
        logger.info("📊 CHROMADB STATISTICS")
        logger.info("="*80)
        
        for collection_name in self.chroma.list_collections():
            stats = self.chroma.collection_stats(collection_name)
            logger.info(f"  📦 {collection_name}: {stats['count']} documents")
        
        logger.info("="*80 + "\n")


def main():
    """Main initialization function"""
    logger.info("="*80)
    logger.info("🚀 CHROMADB INITIALIZATION")
    logger.info("="*80)
    
    initializer = ChromaDBInitializer()
    
    # Initialize banking data
    try:
        banking_stats = initializer.initialize_banking(n_clusters=5)
        logger.info(f"✅ Banking: {banking_stats}")
    except Exception as e:
        logger.error(f"❌ Banking initialization failed: {e}")
    
    # Initialize retail data
    try:
        retail_stats = initializer.initialize_retail(n_clusters=5)
        logger.info(f"✅ Retail: {retail_stats}")
    except Exception as e:
        logger.error(f"❌ Retail initialization failed: {e}")
    
    # Show final stats
    initializer.show_stats()
    
    logger.info("="*80)
    logger.info("✅ INITIALIZATION COMPLETE")
    logger.info("="*80)


if __name__ == "__main__":
    main()

