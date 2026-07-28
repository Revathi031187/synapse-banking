"""
Advanced Clustering Module
Implements K-Means, DBSCAN, and Hierarchical clustering with evaluation metrics
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from scipy.cluster.hierarchy import dendrogram, linkage
from typing import Dict, Any, Tuple, Optional
import json

from utils.logger import get_logger

logger = get_logger("Clustering")


class AdvancedClustering:
    """Advanced clustering with multiple algorithms and evaluation."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.pca = None
        self.tsne = None
        logger.info("🔬 Advanced Clustering module initialized")
    
    def prepare_features(self, df: pd.DataFrame, feature_columns: list) -> np.ndarray:
        """
        Prepare and scale features for clustering.
        
        Args:
            df: DataFrame with features
            feature_columns: List of column names to use
            
        Returns:
            Scaled feature matrix
        """
        logger.info(f"📊 Preparing {len(feature_columns)} features for clustering...")
        
        # Extract features
        X = df[feature_columns].values
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0.0)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        logger.info(f"✅ Features prepared: shape {X_scaled.shape}")
        return X_scaled
    
    def find_optimal_k(self, X: np.ndarray, k_range: range = range(2, 11)) -> Dict[str, Any]:
        """
        Find optimal number of clusters using elbow method and silhouette analysis.
        
        Args:
            X: Feature matrix
            k_range: Range of K values to test
            
        Returns:
            Dictionary with elbow curve data and optimal K
        """
        logger.info(f"🔍 Finding optimal K in range {k_range.start}-{k_range.stop-1}...")
        
        inertias = []
        silhouette_scores = []
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X)
            
            inertias.append(kmeans.inertia_)
            
            if k > 1:
                sil_score = silhouette_score(X, labels)
                silhouette_scores.append(sil_score)
            else:
                silhouette_scores.append(0)
        
        # Find elbow (simple method: max second derivative)
        inertias_arr = np.array(inertias)
        second_deriv = np.diff(inertias_arr, n=2)
        optimal_k_elbow = k_range.start + np.argmax(second_deriv) + 1
        
        # Find best silhouette score
        optimal_k_silhouette = k_range.start + np.argmax(silhouette_scores)
        
        # Prefer silhouette if reasonable, else use elbow
        optimal_k = optimal_k_silhouette if silhouette_scores[optimal_k_silhouette - k_range.start] > 0.3 else optimal_k_elbow
        
        logger.info(f"✅ Optimal K: {optimal_k} (elbow: {optimal_k_elbow}, silhouette: {optimal_k_silhouette})")
        
        return {
            "k_values": list(k_range),
            "inertias": inertias,
            "silhouette_scores": silhouette_scores,
            "optimal_k": optimal_k,
            "optimal_k_elbow": optimal_k_elbow,
            "optimal_k_silhouette": optimal_k_silhouette
        }
    
    def kmeans_clustering(self, X: np.ndarray, n_clusters: int) -> Dict[str, Any]:
        """
        Perform K-Means clustering.
        
        Args:
            X: Feature matrix
            n_clusters: Number of clusters
            
        Returns:
            Clustering results with labels and metrics
        """
        logger.info(f"🎯 Performing K-Means clustering with K={n_clusters}...")
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        
        # Calculate metrics
        silhouette = silhouette_score(X, labels)
        davies_bouldin = davies_bouldin_score(X, labels)
        calinski_harabasz = calinski_harabasz_score(X, labels)
        
        logger.info(f"✅ K-Means complete - Silhouette: {silhouette:.3f}")
        
        return {
            "algorithm": "K-Means",
            "labels": labels.tolist(),
            "n_clusters": n_clusters,
            "cluster_centers": kmeans.cluster_centers_.tolist(),
            "inertia": float(kmeans.inertia_),
            "metrics": {
                "silhouette_score": float(silhouette),
                "davies_bouldin_score": float(davies_bouldin),
                "calinski_harabasz_score": float(calinski_harabasz)
            }
        }
    
    def dbscan_clustering(self, X: np.ndarray, eps: float = 0.5, min_samples: int = 5) -> Dict[str, Any]:
        """
        Perform DBSCAN clustering.
        
        Args:
            X: Feature matrix
            eps: Maximum distance between samples
            min_samples: Minimum samples in a neighborhood
            
        Returns:
            Clustering results
        """
        logger.info(f"🎯 Performing DBSCAN clustering (eps={eps}, min_samples={min_samples})...")
        
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        labels = dbscan.fit_predict(X)
        
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        # Calculate metrics (excluding noise points)
        if n_clusters > 1:
            mask = labels != -1
            silhouette = silhouette_score(X[mask], labels[mask]) if sum(mask) > 0 else 0
        else:
            silhouette = 0
        
        logger.info(f"✅ DBSCAN complete - {n_clusters} clusters, {n_noise} noise points")
        
        return {
            "algorithm": "DBSCAN",
            "labels": labels.tolist(),
            "n_clusters": n_clusters,
            "n_noise": n_noise,
            "metrics": {
                "silhouette_score": float(silhouette)
            }
        }
    
    def hierarchical_clustering(self, X: np.ndarray, n_clusters: int) -> Dict[str, Any]:
        """
        Perform Hierarchical clustering.
        
        Args:
            X: Feature matrix
            n_clusters: Number of clusters
            
        Returns:
            Clustering results with linkage matrix
        """
        logger.info(f"🎯 Performing Hierarchical clustering with K={n_clusters}...")
        
        # Agglomerative clustering
        hierarchical = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
        labels = hierarchical.fit_predict(X)
        
        # Calculate linkage for dendrogram
        linkage_matrix = linkage(X, method='ward')
        
        # Calculate metrics
        silhouette = silhouette_score(X, labels)
        davies_bouldin = davies_bouldin_score(X, labels)
        calinski_harabasz = calinski_harabasz_score(X, labels)
        
        logger.info(f"✅ Hierarchical complete - Silhouette: {silhouette:.3f}")
        
        return {
            "algorithm": "Hierarchical",
            "labels": labels.tolist(),
            "n_clusters": n_clusters,
            "linkage_matrix": linkage_matrix.tolist(),
            "metrics": {
                "silhouette_score": float(silhouette),
                "davies_bouldin_score": float(davies_bouldin),
                "calinski_harabasz_score": float(calinski_harabasz)
            }
        }
    
    def reduce_dimensions_for_viz(self, X: np.ndarray, method: str = 'pca') -> np.ndarray:
        """
        Reduce dimensions to 2D for visualization.
        
        Args:
            X: Feature matrix
            method: 'pca' or 'tsne'
            
        Returns:
            2D coordinates
        """
        logger.info(f"📉 Reducing dimensions using {method.upper()}...")
        
        if method == 'pca':
            if self.pca is None:
                self.pca = PCA(n_components=2, random_state=42)
            coords = self.pca.fit_transform(X)
        elif method == 'tsne':
            if self.tsne is None:
                self.tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, X.shape[0]-1))
            coords = self.tsne.fit_transform(X)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        logger.info(f"✅ Dimensions reduced to 2D")
        return coords
    
    def get_cluster_summary(self, df: pd.DataFrame, labels: np.ndarray, feature_columns: list) -> Dict[int, Dict[str, Any]]:
        """
        Get summary statistics for each cluster.
        
        Args:
            df: Original DataFrame
            labels: Cluster labels
            feature_columns: List of feature columns
            
        Returns:
            Dictionary with cluster summaries
        """
        logger.info("📊 Calculating cluster summaries...")
        
        df_with_labels = df.copy()
        df_with_labels['cluster'] = labels
        
        summaries = {}
        
        for cluster_id in sorted(set(labels)):
            if cluster_id == -1:  # Skip noise in DBSCAN
                continue
                
            cluster_data = df_with_labels[df_with_labels['cluster'] == cluster_id]
            
            summary = {
                "size": len(cluster_data),
                "percentage": len(cluster_data) / len(df) * 100,
                "feature_means": cluster_data[feature_columns].mean().to_dict(),
                "feature_medians": cluster_data[feature_columns].median().to_dict(),
                "feature_stds": cluster_data[feature_columns].std().to_dict()
            }
            
            summaries[int(cluster_id)] = summary
        
        logger.info(f"✅ Summaries calculated for {len(summaries)} clusters")
        return summaries


# Global instance
clustering = AdvancedClustering()

