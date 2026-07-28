"""
Optimal Cluster Selection
Uses Elbow Method and Silhouette Score to find best K
"""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from utils.logger import get_logger

logger = get_logger("OptimalClusters")


def find_optimal_clusters(data: np.ndarray, max_k: int = 10, min_k: int = 3) -> dict:
    """
    Find optimal number of clusters using multiple methods.
    
    Args:
        data: Feature matrix (n_samples, n_features)
        max_k: Maximum clusters to test
        min_k: Minimum clusters to test
        
    Returns:
        dict with optimal_k, scores, and method used
    """
    logger.info(f"🔍 Finding optimal clusters (testing {min_k} to {max_k})...")
    
    # Limit data size for speed (sample if too large)
    if len(data) > 1000:
        logger.info(f"   Sampling 1000 points from {len(data)} for faster computation")
        indices = np.random.choice(len(data), 1000, replace=False)
        sample_data = data[indices]
    else:
        sample_data = data
    
    inertias = []
    silhouettes = []
    k_range = range(min_k, max_k + 1)
    
    for k in k_range:
        # Use faster initialization and fewer iterations for speed
        kmeans = KMeans(
            n_clusters=k,
            init='k-means++',
            n_init=3,  # Reduced from default 10 for speed
            max_iter=100,  # Reduced from default 300 for speed
            random_state=42
        )
        labels = kmeans.fit_predict(sample_data)
        
        # Elbow method: inertia (within-cluster sum of squares)
        inertias.append(kmeans.inertia_)
        
        # Silhouette score (-1 to 1, higher is better)
        if k > 1:  # Silhouette needs at least 2 clusters
            score = silhouette_score(sample_data, labels)
            silhouettes.append(score)
        else:
            silhouettes.append(0)
    
    # Find elbow point (point of maximum curvature)
    optimal_k_elbow = find_elbow_point(inertias, k_range)
    
    # Find best silhouette score
    optimal_k_silhouette = k_range[np.argmax(silhouettes)]
    
    # Use silhouette as primary method (more reliable)
    optimal_k = optimal_k_silhouette
    
    logger.info(f"   ✓ Optimal K by Elbow: {optimal_k_elbow}")
    logger.info(f"   ✓ Optimal K by Silhouette: {optimal_k_silhouette}")
    logger.info(f"   ✅ Recommended K: {optimal_k}")
    
    return {
        'optimal_k': int(optimal_k),
        'elbow_k': int(optimal_k_elbow),
        'silhouette_k': int(optimal_k_silhouette),
        'inertias': [float(x) for x in inertias],
        'silhouettes': [float(x) for x in silhouettes],
        'k_range': list(k_range),
        'best_silhouette_score': float(max(silhouettes))
    }


def find_elbow_point(inertias: list, k_range: range) -> int:
    """
    Find elbow point using point of maximum curvature.
    
    Args:
        inertias: List of inertia values
        k_range: Range of K values tested
        
    Returns:
        Optimal K value
    """
    # Normalize inertias to 0-1 range
    inertias = np.array(inertias)
    norm_inertias = (inertias - inertias.min()) / (inertias.max() - inertias.min())
    
    # Calculate distances from line connecting first and last point
    n_points = len(norm_inertias)
    all_coords = np.vstack((range(n_points), norm_inertias)).T
    first_point = all_coords[0]
    last_point = all_coords[-1]
    line_vec = last_point - first_point
    line_vec_norm = line_vec / np.linalg.norm(line_vec)
    
    # Calculate distances
    vec_from_first = all_coords - first_point
    scalar_product = np.dot(vec_from_first, line_vec_norm)
    vec_to_line = vec_from_first - np.outer(scalar_product, line_vec_norm)
    distances = np.linalg.norm(vec_to_line, axis=1)
    
    # Point with maximum distance is the elbow
    elbow_idx = np.argmax(distances)
    
    return list(k_range)[elbow_idx]


def calculate_cluster_quality(data: np.ndarray, labels: np.ndarray) -> dict:
    """
    Calculate multiple quality metrics for clustering.
    
    Args:
        data: Feature matrix
        labels: Cluster labels
        
    Returns:
        dict with quality metrics
    """
    from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score
    
    n_clusters = len(np.unique(labels))
    
    metrics = {
        'n_clusters': int(n_clusters),
        'n_samples': int(len(data))
    }
    
    if n_clusters > 1:
        # Silhouette Score: -1 to 1 (higher is better)
        # Measures how similar objects are to their own cluster vs other clusters
        metrics['silhouette_score'] = float(silhouette_score(data, labels))
        
        # Calinski-Harabasz Index: Higher is better
        # Ratio of between-cluster to within-cluster dispersion
        metrics['calinski_harabasz_score'] = float(calinski_harabasz_score(data, labels))
        
        # Davies-Bouldin Index: Lower is better (0 is perfect)
        # Average similarity between each cluster and its most similar one
        metrics['davies_bouldin_score'] = float(davies_bouldin_score(data, labels))
        
        # Quality interpretation
        if metrics['silhouette_score'] > 0.5:
            metrics['quality'] = 'Excellent'
        elif metrics['silhouette_score'] > 0.3:
            metrics['quality'] = 'Good'
        elif metrics['silhouette_score'] > 0.1:
            metrics['quality'] = 'Fair'
        else:
            metrics['quality'] = 'Poor'
    else:
        metrics['silhouette_score'] = 0
        metrics['quality'] = 'Single Cluster'
    
    return metrics

