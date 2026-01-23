# 🏷️ Cluster Naming System - User Guide

## Overview

The NBA Personalization Platform now uses **meaningful, business-friendly names** for customer clusters instead of generic "Cluster 1", "Cluster 2", etc. This makes it much easier for non-technical users to understand customer segments.

---

## What Changed?

### Before ❌
- Clusters were named: **"Cluster 0", "Cluster 1", "Cluster 2"**, etc.
- Non-technical users couldn't understand what each cluster represented
- Required technical knowledge to interpret results

### After ✅
- Clusters have meaningful names like:
  - **💎 Premium Active Clients**
  - **🔥 Active Prospects**
  - **💤 Dormant Accounts**
  - **👑 VIP Elite Shoppers**
  - **🎯 Ready-to-Buy Prospects**

---

## Banking Cluster Names

Cluster names are automatically generated based on customer characteristics:

### High-Value Segments
- **💎 Premium Active Clients** - High income, high credit, high engagement
- **🌟 Affluent Banking Clients** - High income and credit score
- **🏆 Loyal Active Members** - Long tenure with high engagement
- **⭐ Prime Credit Prospects** - High credit score with high intent

### Engaged Segments
- **🔥 Active Prospects** - High intent and high engagement
- **👤 Engaged Explorers** - High engagement, moderate intent
- **📱 Digital Browsers** - High engagement but low intent
- **💰 Ready-to-Convert Prospects** - High intent, moderate engagement

### At-Risk Segments
- **💤 Dormant Accounts** - Low engagement and low intent
- **⚠️ At-Risk Low Engagement** - Low engagement, moderate intent
- **🔄 Periodic Users** - Moderate engagement, low intent

### New Customers
- **✨ New Active Customers** - Recent customers with high engagement
- **🌟 Fresh Onboardees** - Recently joined with moderate engagement

---

## Retail Cluster Names

Retail clusters are based on RFM (Recency, Frequency, Monetary), engagement, and intent:

### VIP Segments
- **👑 VIP Elite Shoppers** - High RFM, high engagement, high AOV
- **💎 Loyal Champions** - High RFM with high engagement
- **🌟 High-Value Active Buyers** - High RFM and high intent
- **🏆 Best Customers** - High RFM with moderate engagement

### Active Shoppers
- **🔥 Hot Leads** - High engagement and high intent
- **🛍️ Frequent Browsers** - High engagement, moderate intent
- **🎯 Ready-to-Buy Prospects** - High intent, moderate engagement
- **💰 High-Ticket Buyers** - High average order value with high intent

### Growing Segments
- **📈 Growing Regulars** - Moderate RFM with high engagement
- **🤝 Steady Shoppers** - Moderate RFM and engagement
- **🌱 Casual Shoppers** - Moderate intent and engagement

### At-Risk Segments
- **💤 Dormant Customers** - Low recency, low engagement
- **⚠️ Inactive Accounts** - Low engagement and low intent
- **🔔 Re-Engagement Opportunity** - Low engagement, moderate intent

### New/Occasional
- **🆕 Recently Active** - High recency with high engagement
- **✨ New Shoppers** - High recency, moderate engagement
- **🌊 Occasional Visitors** - Moderate engagement, low intent

---

## How It Works

The system analyzes multiple customer characteristics to generate names:

### Banking Metrics
1. **Intent Score** (0-1) - Likelihood to purchase
2. **Engagement** (logins per month)
3. **Income Level** (annual income)
4. **Credit Score** (300-850)
5. **Tenure** (months as customer)
6. **Channel Preference** (mobile, web, branch)

### Retail Metrics
1. **Intent Score** (0-1) - Purchase likelihood
2. **Engagement** (website visits per month)
3. **RFM Scores** (Recency, Frequency, Monetary - each 1-5)
4. **Average Order Value** (AOV in dollars)
5. **Income Level**
6. **Preferred Category** (Electronics, Fashion, etc.)

---

## Implementation Details

### Files Modified

1. **`utils/cluster_naming.py`** (NEW)
   - Contains `ClusterNamer` class
   - `name_banking_cluster()` - Generates banking cluster names
   - `name_retail_cluster()` - Generates retail cluster names

2. **`scripts/initialize_chromadb.py`**
   - Added cluster name generation during initialization
   - Calls `cluster_namer.name_banking_cluster()` and `cluster_namer.name_retail_cluster()`
   - Stores `cluster_name` in persona metadata

3. **`agents/agent_a_banking_chromadb.py`**
   - Updated `_prepare_visualization_data()` to include cluster names
   - Cluster names now flow through to visualizations

4. **`agents/agent_a_retail_chromadb.py`**
   - Updated `_prepare_visualization_data()` to include cluster names
   - Consistent with banking implementation

5. **`frontend/src/pages/banking/BankingAgentA.tsx`**
   - Updated UI to display `persona.cluster_name` instead of "Cluster {id}"
   - Scatter plot legend now shows meaningful names

6. **`frontend/src/pages/retail/RetailAgentA.tsx`**
   - Updated UI to display `persona.cluster_name` instead of "Cluster {id}"
   - Consistent user experience across both industries

---

## Using the New System

### For Administrators

**Re-initialize the database to generate cluster names:**

```bash
# Windows
py -3.10 scripts\initialize_chromadb.py

# Linux/Mac
python3.10 scripts/initialize_chromadb.py
```

The initialization script will:
1. Perform K-means clustering (default: 5 clusters)
2. Analyze each cluster's characteristics
3. Generate meaningful names automatically
4. Store names in ChromaDB

### For Users

**No action needed!** Simply use the application as before:

1. Navigate to **Banking Dashboard** or **Retail Dashboard**
2. Click **"Agent A: Persona Builder"**
3. Click **"Execute"**
4. View results with meaningful cluster names

---

## Customizing Cluster Names

### Adding New Naming Rules

Edit `utils/cluster_naming.py` to add your own naming logic:

```python
# Example: Add a new banking segment
if high_engagement and new_customer and high_credit:
    return "🚀 Fast-Track VIP Onboarding"
```

### Changing Thresholds

Adjust thresholds in `cluster_naming.py`:

```python
# Current thresholds
high_intent = avg_intent > 0.6        # > 60%
high_engagement = avg_engagement >= 7  # >= 7 logins/month
high_income = avg_income >= 120000    # >= $120k

# Modify as needed for your business
```

---

## Benefits

### For Business Users
✅ **Instant Understanding** - Know what each segment represents immediately
✅ **Better Decision Making** - Make informed decisions based on clear segments
✅ **Easier Communication** - Share results with stakeholders using business language
✅ **No Technical Knowledge Required** - Anyone can understand the segments

### For Technical Users
✅ **Automated** - No manual labeling needed
✅ **Consistent** - Same logic applied across all clusters
✅ **Customizable** - Easy to modify naming rules
✅ **Scalable** - Works with any number of clusters

---

## Examples in Action

### Banking Example

**Before:**
```
Cluster 0: 1,250 customers (25.0%)
Cluster 1: 890 customers (17.8%)
Cluster 2: 1,100 customers (22.0%)
```

**After:**
```
💎 Premium Active Clients: 1,250 customers (25.0%)
🔥 Active Prospects: 890 customers (17.8%)
🏆 Loyal Active Members: 1,100 customers (22.0%)
```

### Retail Example

**Before:**
```
Cluster 0: 2,100 customers (21.0%)
Cluster 1: 1,800 customers (18.0%)
Cluster 2: 1,500 customers (15.0%)
```

**After:**
```
👑 VIP Elite Shoppers: 2,100 customers (21.0%)
🔥 Hot Leads: 1,800 customers (18.0%)
🤝 Steady Shoppers: 1,500 customers (15.0%)
```

---

## Troubleshooting

### Issue: Cluster names not showing

**Solution:**
1. Re-run the initialization script: `py -3.10 scripts\initialize_chromadb.py`
2. Restart the backend: `py -3.10 api\main_unified_chromadb.py`
3. Refresh the frontend in your browser

### Issue: Cluster names are generic

**Solution:**
- Check that ChromaDB was initialized after adding the cluster naming utility
- Verify `cluster_name` field exists in persona metadata
- Re-initialize if needed

### Issue: Want to change cluster names

**Solution:**
1. Edit `utils/cluster_naming.py`
2. Modify the naming logic in `name_banking_cluster()` or `name_retail_cluster()`
3. Re-run initialization script
4. Restart backend

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   K-Means Clustering                         │
│             (groups similar customers)                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Cluster Characteristics Analysis                │
│     (intent, engagement, RFM, income, etc.)                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              ClusterNamer.name_*_cluster()                  │
│        (generates business-friendly names)                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   ChromaDB Storage                           │
│           (persists cluster_name with personas)              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Agent A Retrieval & Display                     │
│          (shows meaningful names to users)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Future Enhancements

Potential improvements for the cluster naming system:

1. **AI-Powered Names** - Use LLM to generate creative, context-aware names
2. **Industry Templates** - Pre-built naming rules for different industries
3. **Multi-Language Support** - Translate cluster names to different languages
4. **Custom Naming Rules UI** - Allow admins to define naming rules via web interface
5. **A/B Testing Names** - Test different naming strategies for user comprehension

---

## Support

For questions or issues related to cluster naming:
- Check `TERMINAL_COMMANDS.md` for setup help
- Review `README.md` for general documentation
- Open a GitHub issue at: https://github.com/Revathi031187/NBA/issues

---

**Last Updated:** December 16, 2025
**Version:** 1.0
**Author:** NBA Development Team

