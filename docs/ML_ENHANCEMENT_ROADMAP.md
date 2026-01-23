# ML Enhancement Roadmap for Product Recommendations

## 🎯 Goal
Improve ML-based recommendations beyond simple Logistic Regression while maintaining system stability.

---

## 📊 Current State Assessment

### What's Working
- ✅ **Rule-Based System**: Solid scoring logic (price, category, expertise, rating)
- ✅ **Hybrid Framework**: Clean separation between ML and rules
- ✅ **Infrastructure**: Training pipeline, model persistence, API endpoints

### Current Limitations (Manager's Feedback)
- ❌ **Simple Logit Model**: IIA assumption doesn't match real shopping behavior
- ❌ **No Substitution Patterns**: Can't capture product similarity within categories
- ❌ **Missing Collaborative Signals**: No "customers like you bought" insights
- ❌ **No Temporal Patterns**: Ignores seasonality, trends, recency

---

## 🚀 Phase 1: Quick Wins (1-2 weeks) - **NO Breaking Changes**

### 1.1 Enhanced Feature Engineering
**Status**: ✅ PARTIALLY IMPLEMENTED
- [x] Hard negative sampling in training
- [x] Price position within category
- [ ] **Brand affinity scoring** (calculate per-customer brand preferences)
- [ ] **Product co-occurrence matrix** (products frequently bought together)
- [ ] **Seasonal/temporal features** (purchase month, days since last purchase)

**Implementation**: Enhance `logit_recommendation_model.py` features only
**Risk**: Low - backward compatible

### 1.2 Collaborative Features (Lite)
Add simple collaborative signals WITHOUT building a full CF system:
- **Customer similarity**: Find top 10 similar customers (by purchase behavior)
- **Persona-level popularity**: "73% of Premium Gear Experts bought this"
- **Category co-purchase rate**: "Customers who bought backpacks also bought tents"

**Implementation**: 
- New module: `agents/collaborative_features.py`
- Integrate into `_extract_features()` method
- Add 3-5 new features to existing logit model

**Risk**: Low - additive features, doesn't break existing model

---

## 🏗️ Phase 2: Advanced ML Models (3-4 weeks) - **Parallel Development**

### 2.1 Nested Logit Model (Addressing Manager's Concern)
**Why**: Captures hierarchical choice structure (choose category → choose brand → choose specific product)

**Structure**:
```
Level 1: Category Choice (Hiking Backpacks vs Tents vs Boots)
   ├─ Level 2: Brand Choice (Osprey vs Big Agnes vs Kelty)
   │    └─ Level 3: Product Choice (specific SKU)
```

**Implementation**:
- New module: `agents/nested_logit_model.py`
- Uses `pylogit` or custom implementation
- Captures product substitution elasticity within nests

**Integration**: Add as a 3rd tab in Agent B UI ("Nested Logit Model")
**Risk**: Medium - new model, needs validation

### 2.2 LightGBM Gradient Boosting (Modern ML Baseline)
**Why**: Handles non-linear interactions, robust to feature scaling, fast inference

**Advantages over Logit**:
- Captures complex interactions automatically
- No IIA assumption
- Better handling of categorical features
- Built-in feature importance

**Implementation**:
- New module: `agents/lightgbm_recommender.py`
- Training script: `scripts/train_lightgbm.py`
- Uses same feature engineering pipeline

**Integration**: Add as a 4th tab in Agent B UI ("Gradient Boosting Model")
**Risk**: Medium - well-established library, production-ready

### 2.3 Collaborative Filtering (Matrix Factorization)
**Why**: Captures latent customer-product affinities, "wisdom of the crowd"

**Approach**: Alternating Least Squares (ALS) or SVD
- Customer embeddings (latent factors)
- Product embeddings (latent factors)
- Prediction: dot product of embeddings

**Implementation**:
- New module: `agents/collaborative_filtering.py`
- Uses `implicit` library (optimized for implicit feedback)
- Hybrid: CF score + content features

**Integration**: Available as ensemble component
**Risk**: Medium-High - needs sufficient data density

---

## 🎓 Phase 3: Production-Grade Hybrid System (6-8 weeks) - **Full Upgrade**

### 3.1 Ensemble Meta-Model
Combine multiple models intelligently:

```
Final Score = w1 × Rule-Based 
            + w2 × Logit 
            + w3 × Nested Logit
            + w4 × LightGBM
            + w5 × Collaborative Filtering
```

**Weights optimized by**:
- Historical A/B test data
- Cross-validation on holdout set
- Business constraints (e.g., ensure category match weighs heavily)

### 3.2 Neural Collaborative Filtering (Optional - If Data Permits)
If we have sufficient data (>100K interactions):
- Use PyTorch or TensorFlow
- Deep learning model: `Neural Collaborative Filtering (NCF)`
- Combines GMF (Generalized Matrix Factorization) + MLP

### 3.3 Real-Time Personalization Layer
- Online learning: Update models incrementally with new purchases
- Session-based recommendations: Track current browsing session
- A/B testing framework: Compare model variants in production

---

## 📈 Evaluation Metrics

### Offline Metrics (Before Deployment)
- **AUC-ROC**: Discrimination ability
- **Precision@K**: Accuracy of top-K recommendations
- **NDCG**: Ranking quality
- **Coverage**: % of products ever recommended
- **Diversity**: Category/brand diversity in recommendations

### Online Metrics (Post-Deployment)
- **Click-Through Rate (CTR)**: % of recommendations clicked
- **Conversion Rate**: % of recommendations purchased
- **Average Order Value**: Revenue per recommendation
- **Revenue Lift**: Incremental revenue vs. baseline

---

## 🛡️ Risk Mitigation Strategy

### Ensuring No Breaking Changes
1. **Parallel Development**: New models run alongside existing system
2. **Feature Flags**: Enable/disable models per persona or customer segment
3. **Gradual Rollout**: Test on 10% → 50% → 100% of traffic
4. **Fallback Mechanism**: If new model fails, automatically use rule-based system
5. **Monitoring**: Track model performance, latency, error rates in real-time

### Rollback Plan
- Keep rule-based system as default
- Store model version metadata with each recommendation
- One-click rollback to previous model version

---

## 💰 Resource Requirements

### Phase 1 (Quick Wins)
- **Time**: 1-2 weeks
- **Effort**: 1 developer
- **Infrastructure**: None (uses existing)

### Phase 2 (Advanced Models)
- **Time**: 3-4 weeks
- **Effort**: 1-2 developers
- **Infrastructure**: None (uses existing)
- **Libraries**: `pylogit`, `lightgbm`, `implicit`

### Phase 3 (Production System)
- **Time**: 6-8 weeks
- **Effort**: 2-3 developers + 1 data scientist
- **Infrastructure**: Model registry (MLflow), A/B testing framework
- **Libraries**: `pytorch`/`tensorflow` (optional)

---

## 🎯 Recommended Immediate Action

### Start with Phase 1, Option 1.2: **Collaborative Features (Lite)**

**Why This First?**
- Addresses manager's "collaborative filtering" concern
- Low risk, high impact
- No infrastructure changes
- Complements existing logit model

**Deliverable (1 week)**:
- Add 5 collaborative features to existing model
- Retrain logit model with enhanced features
- Compare results: old vs. new in Agent B UI

**Expected Improvement**:
- Better differentiation within same category
- Capture "wisdom of the crowd" (popular products for persona)
- More realistic probability distributions (60-95% instead of all 100%)

---

## 📝 Next Steps

1. **Manager Approval**: Share this roadmap, confirm Phase 1 approach
2. **Create Feature Branch**: `feature/ml-enhancement-phase1`
3. **Implement Collaborative Features**: Start with persona-level popularity
4. **A/B Test**: Compare old logit vs. enhanced logit
5. **Document Results**: Share metrics before moving to Phase 2

---

## 🔗 References

- **Nested Logit**: Ben-Akiva & Lerman (1985) - "Discrete Choice Analysis"
- **LightGBM**: Ke et al. (2017) - "LightGBM: A Highly Efficient Gradient Boosting Decision Tree"
- **Collaborative Filtering**: Koren et al. (2009) - "Matrix Factorization Techniques for Recommender Systems"
- **Neural CF**: He et al. (2017) - "Neural Collaborative Filtering"

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-20  
**Author**: AI Agent (Based on Manager Feedback)  
**Status**: Awaiting Approval
