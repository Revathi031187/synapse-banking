# Academy Sports Personalization System - Meeting Feedback & Improvement Plan

**Date:** December 24, 2025  
**Meeting:** SportsAcademy Demo Review  
**Attendees:** Abhay Joshi, Jaison Samuel D, Tusharadri Mukherjee, Revathi Balasubramaniyan, Nikki Kasiraju, Pallavi Bhargava, Mahalakshmi Nageswaran

---

## Executive Summary

Thank you for the valuable feedback during our demo session. This document provides a detailed explanation of our current personalization approach, addresses the feedback received, and outlines our implementation plan for improvements.

**Key Takeaways from Meeting:**
- Price matching logic needs refinement for high-value personas
- Recommendation explanations should be visible to users
- Out-of-stock products should be deprioritized
- Recency and frequency should influence recommendations
- Macro activity-based segmentation should precede micro segmentation

---

## 1. Current Implementation - Detailed Explanation

### 1.1 Agent A: Persona Discovery Engine

**Algorithm: K-Prototypes Clustering**

We use K-Prototypes because it handles mixed data types (both numerical and categorical) which is essential for customer behavior analysis.

**Input Data:**
- 5,000 customers from Academy Sports
- 12 months of behavioral data
- Both online and offline (in-store) transactions

**Clustering Features (18 total):**

**Demographic Features:**
- Age group (categorical)
- Location/Distance to store (numerical)
- Customer tenure (numerical)

**Behavioral Features:**
- Search specificity (1-5 scale): Measures search term precision
- Bundle affinity (0-100%): Preference for package deals vs individual items
- Price sensitivity (0-100%): How often they sort by price or choose cheaper options
- Research depth (0-100%): Frequency of reading product specifications

**Purchase History Features:**
- Total spend (last 12 months)
- Purchase frequency (number of transactions)
- Recency (days since last purchase)
- Average transaction value
- Return rate
- Category diversity (how many product categories purchased)

**Engagement Features:**
- Session duration average
- Pages viewed per session
- Click-through rate on recommendations

**Algorithm Parameters:**
- n_clusters: 3 (First-Time Campers, Family Socializers, Seasoned Pros)
- gamma: Auto-calculated based on feature variance
- init: 'Huang' (initialization method)
- n_init: 5 (number of initialization runs)
- max_iter: 150 (convergence iterations)

**Output:**
- Each customer assigned to 1 of 3 personas
- Confidence score (probability of correct assignment)
- Model accuracy: 78% (indicates good generalization without overfitting)

**Current Persona Definitions:**

**First-Time Campers (40% of customers, 11% of revenue)**
- Search specificity: 1.0-3.0 (basic terms like "tent")
- Bundle affinity: 60-100% (love complete packages)
- Price sensitivity: 70-100% (highly budget-conscious)
- Research depth: 0-25% (rarely read specifications)
- Avg spend: $150-$500/year

**Family Socializers (35% of customers, 29% of revenue)**
- Search specificity: 2.2-3.8 (attribute-based like "4-person tent")
- Bundle affinity: 30-70% (mixed preferences)
- Price sensitivity: 40-80% (balanced approach)
- Research depth: 25-60% (moderate research)
- Avg spend: $300-$1,500/year

**Seasoned Pros (25% of customers, 60% of revenue)**
- Search specificity: 3.8-5.0 (exact model names)
- Bundle affinity: 0-30% (prefer individual items)
- Price sensitivity: 0-40% (price less important)
- Research depth: 60-100% (always read specs)
- Avg spend: $800-$3,000/year

---

### 1.2 Agent B: Product Recommendation Engine

**Algorithm: Logistic Regression with Feature Scoring**

**Current Scoring Formula:**

```
Base Logit = Persona-specific baseline score
Feature Lifts = Sum of compatibility adjustments
Final Probability = 1 / (1 + exp(-(Base Logit + Feature Lifts)))
```

**Compatibility Factors Currently Used:**

1. **Bundle Match** (+0.8 to +1.2 lift)
   - If customer loves bundles and product is a bundle → high lift
   - If customer hates bundles and product is individual → high lift

2. **Category Match** (+0.5 to +1.0 lift)
   - If product is in customer's frequently purchased categories

3. **Technical Complexity Match** (+0.6 to +1.0 lift)
   - Beginners → simple, all-in-one products
   - Experts → technical, specialized products

4. **Brand Affinity** (+0.3 to +0.7 lift)
   - If product brand matches past purchase patterns

5. **Price Bracket Match** (+0.4 to +0.8 lift)
   - Currently uses persona's average spend range
   - **Issue identified:** Range too wide for Seasoned Pros

**Current Limitations (Identified in Demo):**

1. **Price Range Too Wide**
   - Seasoned Pros seeing products from $40 to $1,000
   - Should narrow to typical purchase range

2. **Out-of-Stock Products**
   - Currently not filtered or deprioritized
   - Causes poor user experience

3. **No Explanation Visibility**
   - Users can't see why a product is recommended
   - Reduces trust in recommendations

4. **Recency/Frequency Not Weighted**
   - All purchase history treated equally
   - Recent purchases should have higher weight

5. **No Macro Segmentation**
   - Currently persona-based only
   - Should segment by activity first (camping vs sports vs fitness)

---

## 2. Feedback Received & Our Understanding

### Feedback 1: Wide Price Range for Seasoned Pros
**Issue:** Recommendations showing $40-$1,000 range  
**Root Cause:** Current logic matches "technical complexity" but not typical price behavior  
**Example:** Charles Thomas (Seasoned Pro) spends avg $277/purchase, but sees $40 stoves and $1,000 tents  
**Our Understanding:** Even if a $40 product meets technical specs, it doesn't match the premium positioning expected by high-value customers

### Feedback 2: Out-of-Stock Products in Recommendations
**Issue:** Recommended products showing as unavailable  
**Root Cause:** Inventory status not considered in scoring algorithm  
**Our Understanding:** Should either exclude completely or heavily deprioritize

### Feedback 3: Need Attribute Explanations
**Issue:** Users can't see why products are recommended  
**Root Cause:** Compatibility logic is backend-only, not exposed to frontend  
**Our Understanding:** Tooltips or expandable sections should show "Recommended because: matches your bundle preference, in your price range, technical specs match your expertise"

### Feedback 4: Incorporate Recency and Frequency
**Issue:** All purchases weighted equally regardless of when they occurred  
**Root Cause:** Current model uses aggregate metrics, not time-weighted  
**Our Understanding:** A purchase from last week should influence recommendations more than a purchase from 11 months ago

### Feedback 5: Macro Segmentation First
**Issue:** Currently segmenting at persona level without activity context  
**Root Cause:** Assuming all customers are camping customers  
**Our Understanding:** Should first segment by macro activity (Camping, Water Sports, Team Sports, Fitness) then apply persona logic within each activity

### Feedback 6: Show Top 3 Products Only (Demo)
**Issue:** Showing full list is overwhelming for demo  
**Our Understanding:** For presentation purposes, limit to top 3 most relevant products

---

## 3. Proposed Improvements

### Priority 1: Immediate Fixes (Before Next Interaction)

#### 3.1 Fix Price Matching Logic

**Current Approach:**
- Uses persona's entire spend range ($800-$3,000 for Seasoned Pros)

**New Approach:**
- Calculate customer's typical price per item (total spend / number of purchases)
- Define acceptable range as ±30% of typical price
- Add persona-specific minimum thresholds:
  - First-Time Campers: $10-$200 per item
  - Family Socializers: $30-$500 per item
  - Seasoned Pros: $100-$1,000 per item

**Example Fix:**
- Charles Thomas: Avg $277/purchase
- New range: $194-$360 (±30%)
- Enforced minimum: $100 (Seasoned Pro threshold)
- Final range: $194-$360

#### 3.2 Deprioritize Out-of-Stock Products

**Implementation:**
- Add inventory_status field to product scoring
- If out_of_stock: Apply -2.0 penalty to base logit (massive deprioritization)
- If low_stock: Apply -0.5 penalty
- If in_stock: No penalty

**Result:** Out-of-stock products will only appear if no other alternatives exist

#### 3.3 Add Recommendation Explanations (Tooltip)

**Implementation:**
- Generate human-readable explanation for each recommendation
- Display via tooltip on hover or expandable "Why this product?" section

**Example Explanation Text:**
```
"Recommended for Sarah Williams because:
✓ This is a complete bundle (you view bundles 89% of the time)
✓ Price-optimized for beginners ($253 matches your budget)
✓ Includes everything needed for first camping trip
✓ Highly rated by other first-time campers"
```

#### 3.4 Demo Enhancement: Top 3 Products Only

**Implementation:**
- Frontend: Add toggle for "Demo Mode" showing only top 3
- Sort by compatibility score descending
- Display large compatibility percentage and explanation

---

### Priority 2: Algorithm Enhancements (Next Sprint)

#### 3.5 Add Recency-Frequency Weighting (RFM Model)

**Current Issue:** All purchases treated equally

**New Approach: Time-Decay Weighting**

```
Weight = exp(-λ * days_since_purchase)
λ = 0.005 (decay constant)

Example:
- Purchase from 10 days ago: Weight = 0.95
- Purchase from 100 days ago: Weight = 0.61
- Purchase from 300 days ago: Weight = 0.22
```

**Apply weights to:**
- Category preferences (recent categories matter more)
- Price behavior (recent price points matter more)
- Brand preferences (recent brands matter more)

**Add Frequency Boost:**
- Customers with 5+ purchases in category → +0.3 lift for that category
- Customers with 10+ purchases overall → "loyal customer" boost

#### 3.6 Implement Macro Activity Segmentation

**New Two-Level Segmentation:**

**Level 1: Activity Macro Segments**
- Camping & Outdoor (current focus)
- Water Sports (swimming, kayaking, fishing)
- Team Sports (basketball, soccer, baseball)
- Fitness & Training (gym equipment, running gear)
- Cycling & Action Sports

**Level 2: Persona Micro Segments (within each activity)**
- Beginner / Intermediate / Expert
- Budget-Conscious / Balanced / Premium
- Individual / Family / Professional

**Example:**
- Customer: "Camping Beginner, Budget-Conscious, Individual"
- Maps to: First-Time Camper (current persona)

**Implementation:**
- Add activity classification based on product categories purchased
- If customer spans multiple activities (e.g., camps AND cycles), segment by primary activity (most spend)
- Apply persona logic within activity context

---

### Priority 3: Future Enhancements

#### 3.7 Dynamic Segmentation Based on Search Intent

**Use Case:**
- Seasoned Pro searches "beginner gift tent for nephew"
- Temporarily classify as "Gift Buyer for Beginner"
- Show beginner products for that session
- Revert to Seasoned Pro for next session

**Implementation:**
- Real-time intent detection from search query
- Session-level persona override
- Requires NLP/LLM for intent classification

#### 3.8 One-to-One Personalization at Scale

**Use Case:**
- Move beyond personas to individual-level optimization
- Each customer gets unique recommendation weights

**Challenges:**
- Computationally expensive (5,000 customers × 10,000 products = 50M calculations)
- Requires caching and optimization
- More data needed per customer for accuracy

---

## 4. Technical Implementation Details

### 4.1 Updated Scoring Formula (Priority 1 + 2)

```python
# Base logit by persona
base_logit = {
    'First-Time Camper': -0.5,
    'Family Socializer': 0.0,
    'Seasoned Pro': 0.5
}[customer_persona]

# Feature lifts
lift_sum = 0

# 1. Bundle match (existing)
if (customer.bundle_affinity > 0.7 and product.is_bundle) or \
   (customer.bundle_affinity < 0.3 and not product.is_bundle):
    lift_sum += 1.0

# 2. Price match (UPDATED)
customer_typical_price = customer.total_spend / customer.purchase_count
price_min = max(customer_typical_price * 0.7, persona_min_price)
price_max = customer_typical_price * 1.3

if price_min <= product.price <= price_max:
    lift_sum += 0.8
else:
    lift_sum -= 0.5  # Penalty for out-of-range

# 3. Category match with recency weighting (NEW)
recent_categories = get_recent_categories(customer, days=90)
if product.category in recent_categories:
    recency_weight = calculate_recency_weight(customer, product.category)
    lift_sum += (1.0 * recency_weight)

# 4. Inventory penalty (NEW)
if product.inventory_status == 'out_of_stock':
    lift_sum -= 2.0
elif product.inventory_status == 'low_stock':
    lift_sum -= 0.5

# 5. Frequency boost (NEW)
if customer.purchase_frequency > 5:
    lift_sum += 0.3

# 6. Technical complexity match (existing)
complexity_score = match_complexity(customer.expertise, product.complexity)
lift_sum += complexity_score * 0.6

# Final probability
probability = 1 / (1 + exp(-(base_logit + lift_sum)))
```

### 4.2 Explanation Text Generation

```python
def generate_explanation(customer, product, score):
    reasons = []
    
    # Bundle match
    if customer.bundle_affinity > 0.7 and product.is_bundle:
        reasons.append(f"Complete bundle (you prefer bundles {int(customer.bundle_affinity*100)}% of time)")
    
    # Price match
    if is_price_match(customer, product):
        reasons.append(f"Price matches your typical range (${price_min}-${price_max})")
    
    # Category match
    if product.category in customer.recent_categories:
        reasons.append(f"You recently purchased {product.category} products")
    
    # Expertise match
    if matches_expertise(customer, product):
        reasons.append(f"Complexity level matches your {customer.persona} profile")
    
    # Social proof
    similar_customers = get_similar_customers(customer)
    if product.id in similar_customers.top_purchases:
        reasons.append(f"Popular among other {customer.persona}s")
    
    return "\n".join([f"✓ {r}" for r in reasons])
```

---

## 5. Attribute List & Model Parameters

### 5.1 Complete Feature List for K-Prototypes

**Numerical Features (12):**
1. age
2. distance_to_store
3. customer_tenure_months
4. search_specificity (1-5)
5. bundle_affinity (0-1)
6. price_sensitivity (0-1)
7. research_depth (0-1)
8. total_spend_12mo
9. purchase_frequency
10. recency_days
11. avg_transaction_value
12. return_rate

**Categorical Features (6):**
1. age_group (18-25, 26-35, 36-50, 51+)
2. preferred_shopping_channel (online, in-store, both)
3. primary_product_category (camping, water_sports, team_sports, fitness)
4. bundle_buyer (yes, no)
5. loyalty_tier (new, regular, vip)
6. location_type (urban, suburban, rural)

### 5.2 Product Scoring Parameters

**Current Lift Values:**
- Bundle match: +1.0
- Category match: +1.0
- Price match: +0.8
- Technical complexity match: +0.6
- Brand affinity: +0.7

**Proposed New Lift Values:**
- Bundle match: +1.0 (unchanged)
- Category match with recency: +0.8 to +1.2 (time-weighted)
- Price match: +0.8 (unchanged)
- Price mismatch penalty: -0.5 (NEW)
- Technical complexity match: +0.6 (unchanged)
- Brand affinity: +0.7 (unchanged)
- Inventory out-of-stock: -2.0 (NEW)
- Inventory low-stock: -0.5 (NEW)
- Frequency boost: +0.3 (NEW)

---

## 6. Questions for Clarification

To ensure we implement exactly what you need, please clarify:

**Question 1: Price Bands**
Should we enforce these strict minimum prices per persona?
- First-Time Campers: $10-$200 per item
- Family Socializers: $30-$500 per item
- Seasoned Pros: $100-$1,000 per item

Or should we use dynamic ±30% of customer's typical spend?

**Question 2: Out-of-Stock Products**
- Option A: Completely exclude from recommendations
- Option B: Show at bottom with "Out of Stock" label
- Option C: Heavy deprioritization but allow if no alternatives

Which approach do you prefer?

**Question 3: Macro Activity Segmentation**
What are the primary activity categories we should segment by?
- Our proposal: Camping, Water Sports, Team Sports, Fitness, Cycling
- Should we add/remove any?

**Question 4: Recency Window**
For time-weighted recommendations, what time window is most relevant?
- Last 30 days (very recent behavior)
- Last 90 days (seasonal trends)
- Last 180 days (broader patterns)

**Question 5: Demo Mode**
Should the "Top 3 products only" view be:
- Demo mode only (hidden from production)
- Available as user option ("Show more/less")
- Always top 3 (remove full list view)

**Question 6: Explanation Display**
How should we show recommendation explanations?
- Tooltip on hover
- Expandable "Why this?" section
- Always visible below product
- Modal/popup on click

---

## 7. Next Steps

**Immediate Actions:**
1. Implement Priority 1 fixes (price logic, inventory, explanations, demo mode)
2. Share updated attribute list and model parameters for your review (attached as appendix)
3. Prepare test cases for each persona with expected recommendations

**Week 1:**
4. Implement Priority 2 enhancements (RFM weighting, macro segmentation)
5. Update documentation with new algorithm details

**Week 2:**
6. Internal testing with refined model
7. Prepare comparison: before/after recommendation quality

**Ongoing:**
8. Collect feedback on Priority 3 (dynamic segmentation) feasibility and timeline

---

## 8. Appendix: Sample Recommendation Outputs

### Before Improvements (Current):

**Charles Thomas (Seasoned Pro) searching "sleeping bag"**
```
1. Premium Down Sleeping Bag - $899 (96% match)
2. Budget Camp Sleeping Bag - $42 (87% match) ← Problem: Too cheap
3. Ultra-Lightweight Bag - $567 (91% match)
4. Family 4-Season Bag - $234 (85% match)
5. Kids Sleeping Bag - $38 (OUT OF STOCK) ← Problem: Out of stock + wrong persona
```

### After Improvements (Proposed):

**Charles Thomas (Seasoned Pro) searching "sleeping bag"**
```
1. Ultra-Lightweight Bag - $567 (94% match)
   ✓ Technical specs match your expert profile
   ✓ Price matches your typical range ($200-$400)
   ✓ You recently viewed similar ultralight gear
   ✓ Popular among other Seasoned Pros

2. Premium Down Sleeping Bag - $899 (92% match)
   ✓ Professional-grade materials (850-fill down)
   ✓ Temperature rating matches your expedition needs
   ✓ You purchased this brand 3 times in last 6 months

3. 4-Season Technical Bag - $312 (90% match)
   ✓ Advanced features (compression, weight optimization)
   ✓ Price matches your spending pattern
   ✓ In stock - ready to ship
```

---

**We look forward to your feedback on these proposed improvements and answers to the clarification questions above.**

**Team:** Jaison Samuel D, Revathi Balasubramaniyan  
**Date:** December 24, 2025

