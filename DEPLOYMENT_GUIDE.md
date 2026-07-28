# Dynamic Segmentation & Product Recommendations - Deployment Guide

## Implementation Summary

This document provides a comprehensive guide for deploying the enhanced Academy Sports segmentation and recommendation system.

## What Was Implemented

### Backend Components

#### 1. Enhanced Macro Segmentation (`agents/agent_a_academy_chromadb.py`)
- **Business Constraints Enforcement**
  - Forces 4-5 macro segments (previously allowed any number)
  - Minimum segment size: 10% of total customers
  - Minimum revenue per customer: $50
  - Automated validation with detailed reporting
  
- **Enhanced Metadata**
  - Revenue potential per segment
  - Special flags (high_value, price_sensitive, brand_loyal, expert_level, etc.)
  - Last refreshed timestamp
  - Constraint validation status

#### 2. Micro Segmentation Agent (`agents/agent_a_academy_micro.py`)
- Creates 3-4 sub-segments within each macro persona
- **Segmentation Features:**
  - Brand loyalty score (0-1)
  - Expertise level (based on search specificity + spec expansion)
  - LTV tiers (Bronze, Silver, Gold, Platinum)
  - Category focus score
  
- **Output:**
  - Micro segment names (e.g., "Expert Brand Loyal - Platinum Tier")
  - Size and revenue metrics
  - Top 5 customers per segment

#### 3. Enhanced Recommendation Engine (`agents/agent_b_academy_enhanced.py`)
Three types of recommendations:

**a) Similar Products**
- Based on purchase history
- Category and brand matching
- Price range filtering (±50%)
- Scoring: 40% category + 30% brand + 30% rating

**b) You Might Like (Segment-Based)**
- Popular products in same micro segment
- Collaborative filtering approach
- Excludes already purchased items

**c) Dynamic Search**
- Semantic search with ChromaDB (when available)
- Keyword fallback
- Personalized to customer's price range

#### 4. New Visitor Support
- Generic recommendations for users without purchase history
- Best-selling products
- Top-rated products
- Trending products (last 30 days)

### API Endpoints

#### Macro Segmentation
- `GET /api/academy/macro-segments` - Get all macro segments with constraints
- `GET /api/academy/agent_a/results` - Get full Agent A results

#### Micro Segmentation
- `POST /api/academy/micro-segments/{macro_segment_id}` - Create micro segments
- `GET /api/academy/micro-segments/{macro_segment_id}` - Retrieve micro segments

#### Recommendations
- `GET /api/academy/recommendations/{customer_id}/similar` - Similar products
- `GET /api/academy/recommendations/{customer_id}/you-might-like` - Segment-based
- `POST /api/academy/recommendations/{customer_id}/search` - Search-based
- `GET /api/academy/recommendations/{customer_id}/all` - All three types
- `GET /api/academy/recommendations/new-visitor` - For new visitors

### Frontend Components

#### 1. Enhanced Macro Segment Display (`frontend/src/pages/academy/AcademyAgentA.tsx`)
- **Clickable persona cards** - Navigate to micro segments
- **Business constraints badges** - Visual indicators of segment flags
- **Revenue potential display** - Prominent per-customer value
- **Last refreshed indicator** - Shows weekly refresh schedule
- **Constraint validation status** - Green/yellow banner
- **Special flags** - Badges for high_value, price_sensitive, etc.

#### 2. Micro Segmentation Viewer (`frontend/src/pages/academy/AcademyMicroSegments.tsx`)
- **Route:** `/academy/macro-segment/:id/micro`
- **Features:**
  - Pie chart showing micro segment size distribution
  - Bar chart showing revenue by micro segment
  - Expandable cards with LTV tier badges
  - Key characteristics (expertise, brand loyalty, category focus)
  - Top 5 customers per segment (clickable to recommendations)
  - Navigation back to macro segments

#### 3. Product Recommendations Dashboard (`frontend/src/pages/academy/AcademyRecommendations.tsx`)
- **Route:** `/academy/customer/:customerId/recommendations`
- **Three Tabs:**
  1. **Similar Products** - Based on purchase history
  2. **You Might Like** - Segment-based recommendations
  3. **Search & Discover** - Live search with results
  
- **Features:**
  - Customer summary card (spend, frequency, avg order value)
  - Price range indicator
  - Product cards with ratings, price, and reason
  - Search functionality with semantic matching

### Automation

#### Weekly Refresh Script (`scripts/refresh_segmentation.py`)
- Runs every Sunday at 2 AM
- **Steps:**
  1. Re-execute macro segmentation (K-Prototypes)
  2. Re-calculate micro segments for each macro
  3. Save results to JSON files
  4. Export CSV for marketing
  5. Update "latest" results for API

- **Logging:**
  - Timestamped log files in `/logs`
  - Console output for monitoring
  - Error handling with exit codes

### Testing

#### Unit Tests (`tests/test_micro_segmentation.py`)
- Micro segmentation logic
- Recommendation algorithms
- Business constraint validation
- Data structure validation

---

## Deployment Steps

### Step 1: Local Development & Testing

#### 1.1 Install Dependencies
```bash
# Ensure you're in the project root with venv activated
cd /path/to/personalization-agent
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install any new dependencies (if needed)
pip install scikit-learn pandas numpy
```

#### 1.2 Test Backend Locally
```bash
# Test macro segmentation with constraints
python -c "from agents.agent_a_academy_chromadb import AgentA_Academy; agent = AgentA_Academy(); result = agent.execute({'n_clusters': 4}); print(f'Status: {result[\"status\"]}, Constraints Met: {result.get(\"constraints_validation\", {}).get(\"all_constraints_met\", \"N/A\")}')"

# Test micro segmentation
python -c "from agents.agent_a_academy_micro import AgentA_Academy_Micro; print('Micro agent imported successfully')"

# Test recommendations
python -c "from agents.agent_b_academy_enhanced import AgentB_Academy_Enhanced; print('Recommendations agent imported successfully')"
```

#### 1.3 Test API Endpoints
```bash
# Start backend (in one terminal)
cd /path/to/personalization-agent
python api/main_unified_chromadb.py

# Test endpoints (in another terminal)
curl http://localhost:8002/api/academy/macro-segments
curl http://localhost:8002/api/academy/agent_a/execute -X POST -H "Content-Type: application/json" -d '{"n_clusters": 4}'
curl http://localhost:8002/api/academy/recommendations/new-visitor
```

#### 1.4 Build Frontend
```bash
cd frontend

# Update API base URL in .env.production (already set to /nba-api)
# Verify vite.config.ts has base: '/nba-platform/'

# Build
npm run build

# Verify build output
ls -la dist/
```

#### 1.5 Test Refresh Script
```bash
# Test the weekly refresh script
python scripts/refresh_segmentation.py --dataset-version v1 --n-clusters 4

# Check logs
tail -f logs/refresh_segmentation_*.log
```

### Step 2: Git Push

```bash
# Create feature branch (if not already)
git checkout -b feature/dynamic-segmentation-recommendations

# Add all new files
git add agents/agent_a_academy_micro.py
git add agents/agent_b_academy_enhanced.py
git add frontend/src/pages/academy/AcademyMicroSegments.tsx
git add frontend/src/pages/academy/AcademyRecommendations.tsx
git add scripts/refresh_segmentation.py
git add tests/test_micro_segmentation.py

# Add modified files
git add agents/agent_a_academy_chromadb.py
git add api/main_unified_chromadb.py
git add frontend/src/pages/academy/AcademyAgentA.tsx
git add frontend/src/App.tsx

# Commit
git commit -m "feat: Add dynamic segmentation and product recommendations

- Macro segmentation with business constraints (4-5 segments, min size, min revenue)
- Micro segmentation (brand loyalty, expertise, LTV tiers)
- Three types of product recommendations (similar, segment, search)
- New visitor support with generic recommendations
- Weekly automated refresh script
- Enhanced frontend UI with clickable cards and navigation
- Comprehensive API endpoints for all features
- Unit tests for core functionality"

# Push to remote
git push origin feature/dynamic-segmentation-recommendations
```

### Step 3: Production Deployment on AWS (penpal.latentview.com)

#### 3.1 SSH to Server
```bash
ssh aipenpaladm@54.160.147.118
```

#### 3.2 Pull Latest Code
```bash
cd /home/aipenpaladm/personalization-agent

# Pull latest changes
git pull origin feature/dynamic-segmentation-recommendations

# Or if merged to main:
git pull origin main
```

#### 3.3 Install Backend Dependencies (if new)
```bash
# Activate venv
source venv/bin/activate

# Install any new packages
pip install -r requirements.txt

# Or manually if needed:
# pip install scikit-learn pandas numpy
```

#### 3.4 Rebuild Frontend
```bash
cd /home/aipenpaladm/personalization-agent/frontend

# Build production bundle
npm run build

# Verify build
ls -la dist/
```

#### 3.5 Deploy Frontend to Nginx
```bash
# Copy built files to web directory
sudo cp -r /home/aipenpaladm/personalization-agent/frontend/dist/* /var/www/html/nba-platform/

# Verify files
ls -la /var/www/html/nba-platform/

# Set permissions
sudo chown -R www-data:www-data /var/www/html/nba-platform/
sudo chmod -R 755 /var/www/html/nba-platform/
```

#### 3.6 Restart Backend Service
```bash
# If using systemd service (nba-platform.service)
sudo systemctl restart nba-platform
sudo systemctl status nba-platform

# Or if running with nohup
pkill -f "python.*main_unified_chromadb"
cd /home/aipenpaladm/personalization-agent
nohup python api/main_unified_chromadb.py > logs/nba-platform.log 2>&1 &

# Verify it's running
sleep 3
curl http://localhost:8002/api/academy/macro-segments
```

#### 3.7 Test API Endpoints
```bash
# Test macro segments
curl http://localhost/nba-api/macro-segments

# Test micro segments (after running Agent A)
curl http://localhost/nba-api/micro-segments/0

# Test recommendations
curl http://localhost/nba-api/recommendations/new-visitor

# Test from external URL
curl https://penpal.latentview.com/nba-api/macro-segments
```

#### 3.8 Verify Nginx Configuration
The routes should already be in `/etc/nginx/nginx.conf` from previous deployment:
```nginx
# NBA Platform API
location /nba-api/ {
    proxy_pass http://localhost:8002/api/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
}

# NBA Platform Frontend
location /nba-platform {
    root /var/www/html;
    try_files $uri $uri/ /nba-platform/index.html;
}
```

If not present, add them and reload:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

#### 3.9 Set Up Weekly Refresh Cron Job
```bash
# Make script executable
chmod +x /home/aipenpaladm/personalization-agent/scripts/refresh_segmentation.py

# Edit crontab
crontab -e

# Add this line (runs every Sunday at 2 AM)
0 2 * * 0 /home/aipenpaladm/personalization-agent/venv/bin/python /home/aipenpaladm/personalization-agent/scripts/refresh_segmentation.py --n-clusters 4 --n-micro 4

# Verify cron job
crontab -l
```

#### 3.10 Create Required Directories
```bash
cd /home/aipenpaladm/personalization-agent

# Create results directory for refresh script
mkdir -p data/results

# Ensure logs directory exists
mkdir -p logs

# Set permissions
chmod 755 data/results logs
```

### Step 4: Verification & Testing

#### 4.1 Test Frontend Access
Open in browser:
- **Main Page:** `https://penpal.latentview.com/nba-platform/`
- **Agent A:** `https://penpal.latentview.com/nba-platform/academy` (click Agent A tab)
- **Execute Agent A** - Click "Run K-Prototypes Clustering" button
- **Verify Enhanced Display:**
  - See special flags badges (high_value, price_sensitive, etc.)
  - See revenue potential per customer
  - See "Last Refreshed" timestamp
  - See business constraints status (green banner)

#### 4.2 Test Micro Segmentation
1. Click on any macro segment card (they should be clickable)
2. Should navigate to `/nba-platform/academy/macro-segment/0/micro`
3. Verify:
   - Pie chart shows micro segment distribution
   - Bar chart shows revenue by micro segment
   - 3-4 micro segment cards with LTV tiers
   - Can expand cards to see top customers

#### 4.3 Test Recommendations
1. From micro segments page, click on a customer name
2. Should navigate to `/nba-platform/academy/customer/CUST_XXXXX/recommendations`
3. Test all three tabs:
   - **Similar Products** - Should show 3 products based on history
   - **You Might Like** - Should show 3 products from segment
   - **Search & Discover** - Enter "tent" and search, should see results

#### 4.4 Test New Visitor Flow
```bash
curl https://penpal.latentview.com/nba-api/recommendations/new-visitor
```
Should return:
- Best-selling products (3)
- Top-rated products (3)
- Trending products (3)

#### 4.5 Monitor Logs
```bash
# Backend logs
tail -f /home/aipenpaladm/personalization-agent/logs/nba-platform.log

# Nginx access logs
sudo tail -f /var/log/nginx/access.log | grep nba

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

#### 4.6 Test Weekly Refresh (Manual Run)
```bash
cd /home/aipenpaladm/personalization-agent
source venv/bin/activate

# Run refresh script manually
python scripts/refresh_segmentation.py --n-clusters 4 --n-micro 4

# Check output
tail -f logs/refresh_segmentation_*.log

# Verify results saved
ls -la data/results/
```

### Step 5: Post-Deployment Checklist

- [ ] Backend API responding on all new endpoints
- [ ] Frontend loads at https://penpal.latentview.com/nba-platform/
- [ ] Agent A executes and shows enhanced macro segments
- [ ] Macro segment cards are clickable
- [ ] Micro segmentation page loads and displays charts
- [ ] Recommendations page loads for individual customers
- [ ] Search functionality works in recommendations
- [ ] New visitor recommendations endpoint works
- [ ] Weekly refresh cron job is scheduled
- [ ] Logs are being generated correctly
- [ ] Nginx routes are working (no 404s)
- [ ] No console errors in browser
- [ ] All three recommendation types return data

---

## Rollback Plan

If issues arise, follow these steps:

### 1. Rollback Frontend
```bash
# Restore previous frontend build (if you backed it up)
sudo rm -rf /var/www/html/nba-platform/*
sudo cp -r /var/www/html/nba-platform.backup/* /var/www/html/nba-platform/
```

### 2. Rollback Backend
```bash
# Stop current service
sudo systemctl stop nba-platform
# Or: pkill -f "python.*main_unified_chromadb"

# Checkout previous version
cd /home/aipenpaladm/personalization-agent
git checkout <previous-commit-hash>

# Restart service
sudo systemctl start nba-platform
```

### 3. Disable Cron Job
```bash
crontab -e
# Comment out the refresh line with #
```

---

## Troubleshooting

### Issue: Macro segments not showing constraints
**Solution:** Check that Agent A was executed with the updated code. Re-run Agent A.

### Issue: Micro segments API returns 404
**Solution:** Micro segments are created on-demand. Execute Agent A first, then access micro segments.

### Issue: Recommendations return empty
**Solution:** Ensure customer has purchase history. For testing, use customers with purchases. For new visitors, use `/recommendations/new-visitor` endpoint.

### Issue: Frontend shows "Network Error"
**Solution:** Check API base URL in frontend. Should be `/nba-api` (relative). Verify Nginx proxy is working: `curl http://localhost/nba-api/macro-segments`

### Issue: Cron job not running
**Solution:** 
```bash
# Check cron logs
sudo grep CRON /var/log/syslog

# Test script manually
/home/aipenpaladm/personalization-agent/venv/bin/python /home/aipenpaladm/personalization-agent/scripts/refresh_segmentation.py

# Ensure script is executable
chmod +x scripts/refresh_segmentation.py
```

### Issue: 504 Gateway Timeout on clustering
**Solution:** Already configured in Nginx with 300s timeout. If still happening, increase further in `/etc/nginx/nginx.conf`:
```nginx
proxy_connect_timeout 600;
proxy_send_timeout 600;
proxy_read_timeout 600;
```

---

## Monitoring & Maintenance

### Daily Checks
- Monitor backend logs for errors: `tail -f logs/nba-platform.log`
- Check Nginx error logs: `sudo tail -f /var/log/nginx/error.log`
- Verify API health: `curl http://localhost/nba-api/macro-segments`

### Weekly Checks (After Sunday 2 AM Refresh)
- Check refresh logs: `ls -lt logs/refresh_segmentation_*.log | head -1 | xargs cat`
- Verify new results: `ls -lt data/results/`
- Test macro segments in UI: https://penpal.latentview.com/nba-platform/academy

### Monthly Maintenance
- Review and archive old log files
- Clean up old result files in `data/results/`
- Review constraint validation - adjust thresholds if needed
- Analyze micro segment quality - adjust n_micro_segments if needed

---

## Performance Optimization

### If Response Times Are Slow:
1. **Add Redis caching** for frequently accessed endpoints
2. **Implement pagination** for large customer lists
3. **Use background jobs** for heavy computations
4. **Add database indexing** if using persistent storage
5. **Optimize ChromaDB queries** for semantic search

### If Memory Usage Is High:
1. **Limit DataFrame sizes** - process in batches
2. **Clear unused variables** after processing
3. **Use generators** instead of loading all data at once
4. **Monitor with:** `htop` or `free -h`

---

## Contact & Support

For issues or questions:
- **Backend/API Issues:** Check `logs/nba-platform.log`
- **Frontend Issues:** Browser console (F12)
- **Nginx Issues:** `/var/log/nginx/error.log`
- **Cron Issues:** `/var/log/syslog` (search for CRON)

---

## Summary

**What was deployed:**
- ✅ Enhanced macro segmentation with business constraints
- ✅ Micro segmentation with brand loyalty, expertise, LTV
- ✅ Three types of product recommendations
- ✅ New visitor support
- ✅ Weekly automated refresh
- ✅ Enhanced frontend UI with navigation
- ✅ Comprehensive API endpoints
- ✅ Unit tests

**Access Points:**
- **Frontend:** https://penpal.latentview.com/nba-platform/
- **API Base:** https://penpal.latentview.com/nba-api/
- **Server:** 54.160.147.118 (SSH: aipenpaladm@54.160.147.118)

**Key Files:**
- Backend: `api/main_unified_chromadb.py`
- Agents: `agents/agent_a_academy_*.py`, `agents/agent_b_academy_enhanced.py`
- Frontend: `frontend/src/pages/academy/Academy*.tsx`
- Scripts: `scripts/refresh_segmentation.py`
- Nginx: `/etc/nginx/nginx.conf`

---

**Deployment Complete! 🎉**
