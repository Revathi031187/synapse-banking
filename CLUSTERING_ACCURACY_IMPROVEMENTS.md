# K-Prototypes Clustering Accuracy Improvements

## 🎯 **Goal: Increase Model Accuracy from 66% to 75%+**

## 📊 **What Was Changed:**

### 1. **Enhanced Feature Engineering** (Most Impactful)

#### RFM Composite Scores:
- `recency_score`: Inverse recency (1 / (recency_days + 1))
- `frequency_score`: Normalized purchase frequency
- `monetary_score`: Normalized spend
- `rfm_score`: Combined RFM metric

#### Behavioral Engagement Metrics:
- `engagement_score`: Search specificity + bundle affinity
- `experience_level`: Expertise indicator (specificity × (1 - expansion))
- `value_seeker_score`: Price sensitivity × low bundle affinity
- `premium_buyer_score`: High AOV × low price sensitivity

#### Purchase Behavior Patterns:
- `loyalty_index`: Purchase frequency × (1 - return rate)
- `spend_per_purchase`: Total spend / purchases
- `exploration_score`: Expansion rate × specificity

#### Demographic-Behavior Interactions:
- `income_spend_ratio`: Spend as % of income
- `age_experience_match`: Age-weighted expertise

### 2. **Feature Scaling & Normalization**
- Added **StandardScaler** to normalize all numeric features
- Ensures all features contribute equally to distance calculations
- Prevents features with large ranges from dominating

### 3. **Better Initialization Algorithm**
- Changed from **'Huang'** to **'Cao'** initialization
- Cao method selects better initial centroids
- Results in better convergence and cluster separation

### 4. **Multiple Random Restarts**
- Increased from **5 to 10** initialization runs
- Keeps the model with the **lowest cost** (best fit)
- Reduces risk of local optima

### 5. **Increased Feature Count**
- Original: **11 numeric + 5 categorical = 16 features**
- Enhanced: **23 numeric + 5 categorical = 28 features**
- More features = better persona separation

### 6. **Improved Distance Metric**
- Scaled features ensure proper distance calculations
- Gamma parameter now more effective
- Better balance between numeric and categorical features

---

## 🧪 **How to Test the Improvements:**

### Step 1: Restart Backend
```bash
cd api
py -3.10 main_unified_chromadb.py
```

### Step 2: Run Clustering
1. Go to **Academy Sports → Agent A: Customer Personas**
2. Keep default settings (n_clusters=3, gamma=0.5)
3. Click **"Run K-Prototypes Clustering"**
4. Wait for results (~20-45 seconds)

### Step 3: Check Accuracy
Look at the **"Model Validation"** section:
- **Before**: ~66.3% accuracy
- **Expected After**: **75-85% accuracy**

---

## 📈 **Expected Results:**

### Accuracy Improvement:
```
Before: 66.3% (1,327 / 2,000 correct)
After:  75-85% (1,500-1,700 / 2,000 correct)
```

### Better Persona Separation:
- More distinct behavioral patterns per persona
- Clearer customer segmentation
- Higher confidence scores

### More Actionable Insights:
- Enhanced features reveal hidden patterns
- Better understanding of customer motivations
- More targeted recommendations

---

## 🔧 **Technical Details:**

### Feature Engineering Rationale:

1. **RFM Score** - Classic marketing segmentation metric
   - Combines recency, frequency, monetary value
   - Proven to improve customer segmentation

2. **Engagement Score** - Measures customer involvement
   - Higher engagement = more specific searches
   - Higher bundle affinity = more exploration

3. **Experience Level** - Identifies expertise
   - High specificity + low expansion = expert
   - Low specificity + high expansion = beginner

4. **Value Seeker vs Premium Buyer**
   - Separates price-sensitive from quality-focused
   - Key differentiator for camping gear personas

5. **Loyalty Index** - Predicts retention
   - High frequency + low returns = loyal
   - Important for persona stability

### Scaling Benefits:

Without scaling:
```
search_specificity: 1-5
total_spend_12mo: 50-2000
```
Features with larger ranges dominate distance calculations.

With scaling:
```
All features: mean=0, std=1
Equal contribution to clustering
```

### Initialization Improvements:

**Huang Method** (old):
- Random selection of initial centroids
- Can lead to poor local optima
- Higher variance in results

**Cao Method** (new):
- Selects most distant points as centroids
- Better initial separation
- More consistent results
- Lower final cost

---

## 🎯 **Why This Works:**

### 1. More Discriminative Features
The synthetic data has hidden patterns that basic features don't capture:
- A customer with high spend + low frequency might be a "big trip" buyer
- A customer with high specificity + low expansion is experienced
- A customer with low price sensitivity + high AOV values premium gear

### 2. Proper Feature Scaling
Original implementation:
```python
X = df[cols].values  # Raw values, unscaled
```

Enhanced implementation:
```python
X_scaled = StandardScaler().fit_transform(X[numeric_cols])
```

This ensures:
- All features contribute equally
- Distance calculations are meaningful
- Gamma parameter is effective

### 3. Better Global Optimum
With 10 restarts and Cao initialization:
- Higher chance of finding global optimum
- More stable cluster assignments
- Lower final cost = better fit

---

## 📊 **Performance Metrics to Monitor:**

1. **Overall Accuracy**: Should increase to 75-85%
2. **Correct Predictions**: Should increase to 1,500-1,700
3. **Clustering Cost**: Should decrease significantly
4. **Confidence Scores**: Should be higher on average
5. **Silhouette Score**: Better cluster separation (can add this metric)

---

## 🔄 **If Accuracy Is Still Below Target:**

### Option 1: Tune Gamma Parameter
```python
# Try these values:
gamma = 0.3  # Favor numeric features more
gamma = 0.7  # Favor categorical features more
gamma = 1.0  # Equal weight
```

### Option 2: Adjust Number of Clusters
```python
# Try 4 clusters for finer segmentation
n_clusters = 4
```

### Option 3: Add More Features
- Seasonal patterns
- Product category preferences
- Review sentiment
- Social media engagement

### Option 4: Use Ensemble Methods
- Run multiple clusterings with different parameters
- Combine results through voting
- More robust but slower

---

## 📝 **Code Changes Summary:**

**File**: `agents/agent_a_academy_chromadb.py`

**Lines Changed**: ~140-265

**Key Additions**:
1. Feature engineering section (13 new features)
2. StandardScaler for normalization
3. Multiple initialization loop (10 runs)
4. Cao initialization method
5. Cost-based model selection

**Dependencies**: None (StandardScaler from sklearn already imported)

---

## ✅ **Testing Checklist:**

- [ ] Backend restarted successfully
- [ ] Clustering runs without errors
- [ ] Accuracy improved from 66% baseline
- [ ] Personas are still interpretable
- [ ] Customer Insights tab works
- [ ] All visualizations render correctly
- [ ] Export to CSV works
- [ ] AI explanations work

---

## 🎓 **Learning Points:**

1. **Feature engineering is crucial** - Often more important than algorithm tuning
2. **Scaling matters** - Don't forget to normalize features
3. **Multiple restarts help** - Avoid local optima
4. **Domain knowledge** - RFM, engagement, loyalty indices are proven marketing metrics
5. **Composite features** - Combining features can reveal hidden patterns

---

## 🚀 **Next Steps After Testing:**

1. Monitor accuracy on new data
2. A/B test recommendations based on new clusters
3. Collect business feedback on persona quality
4. Consider adding more domain-specific features
5. Experiment with other clustering algorithms (DBSCAN, Hierarchical)

---

**Expected Improvement**: **+9% to +19% accuracy** (66% → 75-85%)

**Implementation Time**: Immediate (code already deployed)

**Testing Time**: 2-3 minutes per clustering run

**Risk Level**: Low (fallback to rule-based if fails)


