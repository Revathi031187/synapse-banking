# Hybrid Segmentation: Clustering + ChromaDB

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CUSTOMER DATA                             │
│  (Demographics, Behavior, Purchases, Interactions)           │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐         ┌──────────────────┐
│  CLUSTERING  │         │    CHROMADB      │
│  (K-Prototypes)│       │   (Embeddings)   │
└──────┬───────┘         └────────┬─────────┘
       │                          │
       ▼                          ▼
┌──────────────┐         ┌──────────────────┐
│ Macro Segments│        │ Customer Vectors │
│   (4-5)      │        │  (Semantic)      │
└──────┬───────┘         └────────┬─────────┘
       │                          │
       │      ┌───────────────────┘
       │      │
       ▼      ▼
┌──────────────────────┐
│  MICRO SEGMENTS      │
│  (Clustering +       │
│   Vector Refinement) │
└──────────────────────┘
```

## Implementation Plan

### Phase 1: Current (Pure Clustering) ✅
**What you have now:**
- Macro: K-Prototypes with business constraints
- Micro: K-Means on loyalty/expertise/LTV
- Pros: Fast, interpretable, enforces business rules

### Phase 2: Add ChromaDB for Product Recommendations ✅ (Planned)
**Add to your implementation:**
```python
# Store products in ChromaDB
product_collection = chromadb.get_collection('academy_products')
product_collection.add(
    documents=[product_description],
    embeddings=together_ai.embed(product_description),
    metadatas=[product_metadata]
)

# Search for recommendations
results = product_collection.query(
    query_embeddings=customer_embedding,
    n_results=10,
    where={'price': {'$gte': min_price, '$lte': max_price}}
)
```

### Phase 3: Hybrid Segmentation (Advanced) 🚀
**Enhance clustering with vector search:**

#### 3A. Store Customer Embeddings
```python
# After macro segmentation, store customers in ChromaDB
customer_collection = chromadb.get_collection('academy_customers')

for customer in customers_df.itertuples():
    # Create rich customer profile
    profile_text = f"""
    Customer {customer.customer_id}:
    - Purchase history: {customer.purchase_categories}
    - Spending: ${customer.total_spend_12mo}/year
    - Frequency: {customer.purchase_frequency} purchases
    - Preferences: {customer.dominant_category}
    - Behavior: Search specificity {customer.search_specificity}/5
    """
    
    embedding = together_ai.embed(profile_text)
    
    customer_collection.add(
        ids=[customer.customer_id],
        embeddings=[embedding],
        metadatas={
            'macro_segment': customer.cluster,
            'total_spend': customer.total_spend_12mo,
            'persona': customer.persona_name
        }
    )
```

#### 3B. Refine Micro Segments with Similarity
```python
def hybrid_micro_segmentation(macro_segment_id, customer_ids):
    # Step 1: Traditional K-Means clustering
    kmeans = KMeans(n_clusters=4)
    initial_clusters = kmeans.fit_predict(features)
    
    # Step 2: Refine boundaries using ChromaDB
    customer_collection = chromadb.get_collection('academy_customers')
    
    for customer_id, cluster_id in zip(customer_ids, initial_clusters):
        # Find similar customers
        results = customer_collection.query(
            query_embeddings=[customer_embeddings[customer_id]],
            n_results=20,
            where={'macro_segment': macro_segment_id}
        )
        
        # If most similar customers are in a different micro cluster,
        # consider reassigning (with confidence threshold)
        similar_clusters = [r['metadata']['micro_cluster'] for r in results]
        most_common = Counter(similar_clusters).most_common(1)[0]
        
        if most_common[1] > 15:  # 15/20 similar customers
            refined_clusters[customer_id] = most_common[0]
    
    return refined_clusters
```

#### 3C. Enable Semantic Queries
```python
# Find customers matching natural language description
results = customer_collection.query(
    query_texts=["outdoor enthusiasts who prefer premium brands"],
    n_results=100,
    where={'total_spend': {'$gte': 500}}
)

# Find "lookalike" customers for targeting
seed_customer_id = "CUST_00123"
lookalikes = customer_collection.query(
    query_embeddings=[customer_embeddings[seed_customer_id]],
    n_results=50,
    where={'macro_segment': {'$ne': customer_macro_segment}}  # Cross-segment
)
```

## Benefits of Hybrid Approach

| Feature | Pure Clustering | + ChromaDB | Benefit |
|---------|----------------|------------|---------|
| **Business Constraints** | ✅ Built-in | ✅ Built-in | Enforced via algorithm |
| **Interpretability** | ✅ High | ⚠️ Medium | Feature importance clear |
| **Scalability** | ⚠️ O(n²) | ✅ O(log n) | ChromaDB faster for large n |
| **Similar Customers** | ❌ Manual | ✅ Instant | Vector similarity search |
| **New Customer Assignment** | ⚠️ Refit model | ✅ Instant | Query nearest neighbors |
| **Cross-Segment Discovery** | ❌ Complex | ✅ Easy | Semantic search |
| **Product Matching** | ⚠️ Manual | ✅ Built-in | Same vector space |
| **Natural Language Queries** | ❌ No | ✅ Yes | Business users can query |

## When to Use Each Approach

### Use Pure Clustering When:
- ✅ Dataset < 100K customers
- ✅ Weekly/monthly batch refresh is acceptable
- ✅ Interpretability is critical (business reporting)
- ✅ You have clear business constraints
- ✅ Features are well-defined and structured

### Add ChromaDB When:
- ✅ Need real-time "similar customer" lookups
- ✅ Frequent new customer onboarding
- ✅ Want semantic product recommendations
- ✅ Dataset > 100K customers
- ✅ Need natural language segment queries
- ✅ Want to discover "hidden" sub-segments

## Recommended Implementation for Academy Sports

### Keep Current (Don't Change):
```python
# Macro Segmentation - K-Prototypes
# ✓ Handles mixed data types
# ✓ Enforces business constraints
# ✓ Interpretable for stakeholders

# Micro Segmentation - K-Means  
# ✓ Fast and deterministic
# ✓ Clear LTV tiers
# ✓ Works well for your features
```

### Add ChromaDB (Enhance):
```python
# 1. Product Recommendations (High Priority)
# - Semantic search for products
# - "You might like" based on segment
# - Dynamic search matching

# 2. Customer Similarity (Medium Priority)
# - Find lookalike customers
# - Cross-segment discovery
# - New customer assignment

# 3. Segment Search (Low Priority)
# - Natural language queries
# - Ad-hoc analysis
# - Marketing use cases
```

## Cost-Benefit Analysis

### Pure Clustering:
- **Cost**: Low (scikit-learn is free, fast)
- **Maintenance**: Low (stable algorithms)
- **Benefit**: High (interpretable, proven)
- **Verdict**: ✅ Keep for core segmentation

### + ChromaDB:
- **Cost**: Medium (embedding API calls, storage)
- **Maintenance**: Medium (manage collections, embeddings)
- **Benefit**: High (semantic search, recommendations)
- **Verdict**: ✅ Add for recommendations & discovery

## Next Steps

1. **Immediate** ✅: Use ChromaDB for product recommendations (already planned)
2. **Short-term** (1-2 weeks): Add customer embeddings to ChromaDB for similarity search
3. **Medium-term** (1 month): Implement hybrid micro-segmentation with vector refinement
4. **Long-term** (3 months): Enable natural language segment queries for business users

## Code Example: Hybrid Micro Segmentation

```python
class HybridMicroSegmentation:
    def __init__(self, chromadb_client, together_ai_service):
        self.chromadb = chromadb_client
        self.together_ai = together_ai_service
        self.customer_collection = None
    
    def initialize_embeddings(self, customers_df):
        """Store customer embeddings in ChromaDB"""
        self.customer_collection = self.chromadb.get_or_create_collection(
            name='academy_customers_embedded'
        )
        
        for _, customer in customers_df.iterrows():
            profile = self._create_customer_profile(customer)
            embedding = self.together_ai.embed(profile)
            
            self.customer_collection.add(
                ids=[customer.customer_id],
                embeddings=[embedding],
                metadatas={
                    'macro_segment': int(customer.cluster),
                    'total_spend': float(customer.total_spend_12mo),
                    'purchase_frequency': int(customer.purchase_frequency)
                }
            )
    
    def create_micro_segments(self, macro_segment_id, customer_ids, n_clusters=4):
        """Hybrid approach: K-Means + Vector refinement"""
        
        # Step 1: Traditional K-Means
        macro_customers = customers_df[customers_df.customer_id.isin(customer_ids)]
        features = self._extract_features(macro_customers)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        initial_clusters = kmeans.fit_predict(features)
        
        # Step 2: Refine with vector similarity
        refined_clusters = initial_clusters.copy()
        
        for idx, customer_id in enumerate(customer_ids):
            # Find similar customers
            results = self.customer_collection.query(
                ids=[customer_id],
                n_results=10,
                where={'macro_segment': macro_segment_id}
            )
            
            # Check if similar customers agree on cluster
            similar_ids = results['ids'][0]
            similar_clusters = [
                initial_clusters[customer_ids.index(sid)] 
                for sid in similar_ids if sid in customer_ids
            ]
            
            # If strong consensus, refine assignment
            from collections import Counter
            consensus = Counter(similar_clusters).most_common(1)
            if consensus and consensus[0][1] >= 7:  # 7/10 agreement
                refined_clusters[idx] = consensus[0][0]
        
        return refined_clusters
    
    def find_similar_customers(self, customer_id, n_results=10):
        """Find lookalike customers across all segments"""
        results = self.customer_collection.query(
            ids=[customer_id],
            n_results=n_results
        )
        return results
    
    def semantic_segment_search(self, query: str, filters: dict = None):
        """Natural language search for customer segments"""
        results = self.customer_collection.query(
            query_texts=[query],
            n_results=100,
            where=filters
        )
        return results
```

## Conclusion

**Short Answer**: Yes, ChromaDB can benefit segmentation, but use it **strategically**:

1. ✅ **Keep** K-Prototypes/K-Means for core clustering (interpretable, business constraints)
2. ✅ **Add** ChromaDB for product recommendations (semantic search, high value)
3. ⚠️ **Consider** ChromaDB for customer similarity (useful but not critical)
4. 🔮 **Future** Hybrid segmentation for large-scale systems (>100K customers)

For your current 5K customer dataset, the pure clustering approach is excellent. Add ChromaDB primarily for product recommendations (which you're already planning). As you scale or need more advanced features, gradually incorporate vector search for customer similarity.

