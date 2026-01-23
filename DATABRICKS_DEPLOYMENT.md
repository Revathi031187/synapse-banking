# Databricks Deployment Guide for Streamlit App

## Overview

This guide explains how to deploy the Academy Sports Personalization Agent as a Streamlit app on Databricks.

## Prerequisites

1. ✅ Databricks Workspace access (Workspace Contributor role)
2. ✅ GitHub repository connected to Databricks
3. ✅ Data files uploaded to DBFS (`/dbfs/FileStore/academy_sports/`)
4. ✅ Cluster with required libraries installed

## Deployment Steps

### Step 1: Ensure Code is in Databricks Repos

Your GitHub repository (`Revathi031187/NBA`) should already be connected to Databricks workspace.

1. Go to **Databricks Workspace**
2. Navigate to **Workspace** → **Repos**
3. Verify you see your **NBA** repository

If not connected, add it:
1. Click **Repos** → **Add Repo**
2. **Git repository URL:** https://github.com/Revathi031187/NBA
3. **Git provider:** GitHub
4. Authorize if needed
5. Click **Create**

### Step 2: Verify Data Files

Ensure data files exist in DBFS:

```python
# Run this in a Databricks notebook
import os

data_dir = "/dbfs/FileStore/academy_sports/"
required_files = [
    "customers.csv",
    "products.csv",
    "interactions.csv",
    "purchases.csv",
    "feature_affinity.csv",
    "customers_v2.csv",
    "products_v2.csv",
    "interactions_v2.csv",
    "purchases_v2.csv",
    "feature_affinity_v2.csv"
]

for file in required_files:
    path = os.path.join(data_dir, file)
    exists = os.path.exists(path)
    status = "✅" if exists else "❌"
    print(f"{status} {file}")
```

### Step 3: Install Libraries on Cluster

Ensure your cluster has all required libraries:

1. Go to **Compute** → Your cluster
2. Click **Libraries** tab
3. Click **Install new**
4. Select **PyPI**
5. Install these packages:
   ```
   streamlit
   plotly
   kmodes
   scikit-learn
   pandas
   numpy
   chromadb
   loguru
   requests
   faker
   pydantic
   python-dotenv
   ```

### Step 4: Configure Environment Variables

Set up Together AI API key (optional, for AI explanations):

**Option A: Using Databricks Secrets (Recommended)**

```python
# Create secret scope (one-time, run in notebook)
dbutils.secrets.createScope("api-keys")

# Add secret (run once)
dbutils.secrets.put(scope="api-keys", key="together-api-key", value="YOUR_API_KEY")
```

**Option B: Environment Variable**

In cluster configuration, add:
```
TOGETHER_API_KEY=your_api_key_here
```

### Step 5: Create Databricks App

**Method 1: Using Databricks Apps (If Available)**

1. Go to **Apps** in Databricks sidebar
2. Click **Create App**
3. Fill in:
   - **Name:** personalization-agent
   - **Description:** Academy Sports AI Personalization
   - **Source:** Python file
   - **Path:** `/Workspace/Repos/<your-email>/NBA/streamlit_app/app.py`
   - **Cluster:** Select your cluster
4. Click **Create**
5. Wait for app to deploy (2-3 minutes)
6. You'll get a public URL like:
   ```
   https://adb-3750626659891863.3.azuredatabricks.net/apps/personalization-agent
   ```

**Method 2: Run Streamlit Manually (Alternative)**

If Databricks Apps is not available, run Streamlit on your cluster:

1. Create a new notebook in your repo
2. Add this code:
   ```python
   import subprocess
   import os
   
   # Set working directory
   os.chdir('/Workspace/Repos/<your-email>/NBA')
   
   # Run Streamlit
   subprocess.run([
       "streamlit", "run",
       "streamlit_app/app.py",
       "--server.port=8501",
       "--server.address=0.0.0.0"
   ])
   ```
3. Run the notebook
4. Access via cluster driver URL:
   ```
   https://<workspace>.azuredatabricks.net/driver-proxy/o/0/<cluster-id>/8501/
   ```

### Step 6: Test the Deployment

1. Open the app URL
2. Test each page:
   - ✅ Home page loads
   - ✅ Data Loader can load V1 and V2 datasets
   - ✅ Agent A runs clustering successfully
   - ✅ Agent B generates recommendations
   - ✅ Customer Insights displays customer details

### Step 7: Share with Team

Once deployed and tested:

1. Share the app URL with your team
2. Grant Databricks workspace access to team members:
   - Go to **Settings** → **User Management**
   - Add users with "Can View" or "Can Run" permissions
3. Provide quick start guide:
   - Load data from Data Loader
   - Run Agent A for personas
   - Use Agent B for recommendations

## Updating the App

When you make code changes:

1. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update Streamlit app"
   git push origin master
   ```

2. In Databricks:
   - Go to **Repos** → Your repo
   - Click **Update** or the refresh icon
   - Pull latest changes

3. Restart the app:
   - If using Databricks Apps: Click **Restart**
   - If running manually: Stop and restart the notebook

## Troubleshooting

### Issue: "Module not found" errors

**Solution:** Install missing libraries on your cluster

```python
# In a notebook, run:
%pip install streamlit plotly kmodes
```

### Issue: "Cannot connect to database"

**Solution:** Verify DBFS paths are correct

```python
# Check data directory
import os
print(os.listdir("/dbfs/FileStore/academy_sports/"))
```

### Issue: "Together AI API error"

**Solution:** Check API key configuration

```python
# Verify API key
import os
print("API Key set:", bool(os.getenv('TOGETHER_API_KEY')))
```

### Issue: App is slow

**Solution:** 
- Ensure cluster has sufficient resources
- Use caching in Streamlit (`@st.cache_data`)
- Reduce data preview sizes

## Architecture

### Streamlit App Structure

```
streamlit_app/
├── app.py                      # Main entry point
├── pages/
│   ├── home.py                # Home/landing page
│   ├── data_loader.py         # Dataset selection and loading
│   ├── agent_a.py             # Persona discovery
│   ├── agent_b.py             # Product recommendations
│   └── customer_insights.py   # Customer-level analysis
├── components/
│   ├── charts.py              # Plotly visualizations
│   ├── metrics.py             # Metric displays
│   └── tables.py              # Table components
└── utils/
    ├── session.py             # Session state management
    └── styling.py             # Custom CSS/styling

.streamlit/
└── config.toml                # Streamlit configuration

agents/                        # Reused from existing codebase
├── agent_a_academy_chromadb.py
└── agent_b_academy_chromadb.py

utils/                         # Reused from existing codebase
└── (feature engineering, scoring, etc.)
```

### Data Flow

```
User → Streamlit UI → Direct Python Function Calls → Agent Modules → DBFS Data
```

No API layer needed - Streamlit directly imports and calls agent functions.

## Benefits Over React + FastAPI

1. **No Azure permissions needed** - Deploys within Databricks
2. **Simpler architecture** - No API layer, direct function calls
3. **Faster development** - Single language (Python)
4. **Better integration** - Native Databricks authentication and access control
5. **Easier maintenance** - One codebase instead of two

## Next Steps

After successful deployment:

1. Collect user feedback
2. Monitor app usage and performance
3. Add additional features as needed
4. Consider adding more visualizations
5. Optimize for larger datasets

## Support

For issues or questions:
- Check Databricks cluster logs
- Review Streamlit error messages
- Verify all dependencies are installed
- Ensure data files are accessible in DBFS

