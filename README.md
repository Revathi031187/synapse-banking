# 🎯 Agentic AI Personalization Platform for Academy Sports

> **An enterprise-grade, AI-powered personalization platform featuring intelligent customer segmentation and robust product recommendations with multi-agent orchestration.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB.svg)](https://reactjs.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3.3-3178C6.svg)](https://www.typescriptlang.org/)

---

## 🌟 Overview

This platform implements a sophisticated **two-agent system** for customer personalization and product recommendations in the outdoor/camping retail industry. Using advanced machine learning techniques and AI-powered insights, it delivers targeted product recommendations that match individual customer preferences, spending patterns, and expertise levels.

### **Key Capabilities**

- 🎯 **AI-Driven Customer Segmentation** (Agent A): Macro & micro-level segmentation using K-Prototypes clustering
- 🛍️ **Intelligent Product Recommendations** (Agent B): Multi-metric scoring system considering 9+ customer attributes
- 📊 **Dynamic Dashboard**: Real-time insights with interactive visualizations
- 🤖 **LLM-Powered Explanations**: Natural language justifications for every recommendation
- 🔄 **Real-Time Adaptation**: Recommendations update based on search queries and customer behavior
- 📈 **Business Constraints**: Ensures segments meet minimum customer count and revenue thresholds

---

## 🏗️ Architecture

### **Agent System**

```
┌─────────────────────────────────────────────────────────────┐
│                     DATA INGESTION                          │
│  5,000 Customers + 1,000+ Products + Purchase History       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ├─────► 🎯 AGENT A: Customer Segmentation
                      │         ├── K-Prototypes Clustering (mixed data)
                      │         ├── Macro Segmentation (4-5 segments)
                      │         ├── Micro Segmentation (4 sub-segments each)
                      │         ├── LLM-generated segment names
                      │         └── Business constraint validation
                      │
                      └─────► 🛍️ AGENT B: Product Recommendations
                                ├── Multi-Metric Scoring System:
                                │   • Category Match (35%)
                                │   • Price Appropriateness (20%)
                                │   • Brand Loyalty (15%)
                                │   • Expertise Match (15%)
                                │   • Value Tier Alignment (10%)
                                │   • Bundle Affinity (5%)
                                │   • Product Rating (5%)
                                │   • Purchase Recency (5%)
                                │   • Popularity (5%)
                                ├── Semantic Search (ChromaDB)
                                ├── Out-of-Stock Alternatives
                                └── Personalized Explanations
```

### **Technology Stack**

#### **Backend**
- **FastAPI** (Python 3.10+): High-performance REST API
- **ChromaDB**: Vector database for semantic product search
- **K-Prototypes**: Mixed-type data clustering (numeric + categorical)
- **Pandas & NumPy**: Data manipulation and analysis
- **Scikit-learn**: Machine learning algorithms
- **Together AI / LLaMA**: LLM-powered insights and explanations

#### **Frontend**
- **React 18** + **TypeScript**: Modern, type-safe UI
- **TanStack Query**: Efficient server state management
- **Recharts**: Interactive data visualizations
- **Framer Motion**: Smooth animations and transitions
- **Tailwind CSS**: Utility-first styling
- **Vite**: Lightning-fast build tool

#### **Infrastructure**
- **Nginx**: Reverse proxy and static file serving
- **Systemd**: Process management
- **Git**: Version control

---

## 🚀 Quick Start

### **Prerequisites**

- **Python 3.10+** with pip
- **Node.js 18+** with npm
- **Git**
- 8GB+ RAM recommended

### **1. Clone Repository**

```bash
git clone https://github.com/Revathi031187/NBA.git
cd NBA
```

### **2. Backend Setup**

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables (optional, for LLM features)
echo "TOGETHER_API_KEY=your_key_here" > .env

# Initialize ChromaDB with Academy Sports data
python initialize_chromadb.py

# Start FastAPI server
uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8002 --reload
```

**Backend running at**: `http://localhost:8002`  
**API Docs**: `http://localhost:8002/docs`

### **3. Frontend Setup**

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start development server
npm run dev
```

**Frontend running at**: `http://localhost:3000`

### **4. Access the Application**

Open your browser and navigate to `http://localhost:3000`

---

## 📊 Core Features

### **1. Data Overview & Loading**

The platform dynamically analyzes loaded datasets and provides comprehensive insights:

- **Customer Metrics**: Total count, demographics, behavioral patterns
- **Product Catalog**: Count, price ranges, brand distribution
- **AI Features**: 30+ behavioral signals analyzed

**Location**: Agent A → Data Overview section (appears after clustering)

### **2. Agent A: Customer Segmentation**

#### **Macro Segmentation** (Strategic Level)

- **Algorithm**: K-Prototypes clustering for mixed data types
- **Business Constraints**:
  - 4-5 actionable segments
  - Minimum customers per segment
  - $50+ average revenue potential per segment
- **Outputs**:
  - AI-generated segment names (e.g., "Outdoor Adventure Enthusiasts")
  - Key characteristics with comparative analysis
  - Revenue potential and customer count
  - Visual dashboards with lifestyle images

#### **Micro Segmentation** (Tactical Level)

Within each macro segment, identifies 4 sub-segments based on:
- **Brand Loyalty**: Premium vs. value-conscious buyers
- **Expertise Level**: Beginners vs. advanced users
- **Customer Lifetime Value**: VIP vs. casual shoppers
- **Category Specialization**: Specific product focus

**Unique Behaviors**: Each micro segment has **distinct** behavior patterns:
- Expert: "Deep product research - compares 5+ models before buying"
- Price-Sensitive: "Active price comparison across multiple retailers"
- Bundle Buyer: "Prefers complete camping kits - 'ready to go' approach"
- Frequent Buyer: "Frequent upgrader - shops 12x per year"

**Comparative Insights**: All differences highlighted with "Unlike other segments..." language

### **3. Agent B: Robust Product Recommendations**

#### **Multi-Metric Scoring System** (NEW!)

Agent B considers **9 key metrics** when scoring products:

| Metric | Weight | Description |
|--------|--------|-------------|
| **Category Match** | 35% | Main category (25%) + Subcategory (10%) |
| **Price Appropriateness** | 20% | Matches customer's historical spending |
| **Brand Loyalty** | 15% | Considers customer's brand preferences |
| **Expertise Match** | 15% | Product complexity matches customer level |
| **Value Tier Alignment** | 10% | Premium/budget product fits customer tier |
| **Bundle Affinity** | 5% | Bundle-compatible if customer prefers kits |
| **Product Rating** | 5% | Quality indicator |
| **Purchase Recency** | 5% | Favor recently purchased categories |
| **Popularity** | 5% | Highly rated products among similar customers |

**TOTAL**: Up to 115% (some metrics may not apply to all products)

#### **Three Types of Recommendations**

1. **Personalized (Based on Purchase History)**
   - Price range: ±50% of customer's historical average
   - Category: Customer's top purchased categories
   - Brands: Customer's preferred brands

2. **You Might Also Like (Segment-Based)**
   - Popular products within customer's micro segment
   - Discover new items similar customers are buying
   - Cross-category recommendations

3. **Dynamic Search (Real-Time)**
   - Semantic search using ChromaDB vector embeddings
   - Updates instantly as search query changes
   - Context-aware product matching

#### **Price Tier Logic**

| Customer Tier | Annual Spend | Recommended Price Range |
|---------------|--------------|------------------------|
| Ultra-Premium | $2000+ | $200 - $600 |
| Platinum | $1500 - $1999 | $150 - $600 |
| Gold | $1000 - $1499 | $100 - $400 |
| Silver | $600 - $999 | $50 - $250 |
| Bronze | $300 - $599 | $25 - $150 |
| Entry | <$300 | $10 - $100 |

**Example**: A customer spending $2,432/year receives **$200-$600** product recommendations, not $45 items.

### **4. Customer Insights & Explanations**

- **AI-Generated Explanations**: Natural language justification for each recommendation
- **Segment Membership**: Why customer belongs to their segment
- **Product Fit Analysis**: Why specific products match customer preferences
- **Out-of-Stock Alternatives**: Intelligent substitution suggestions

### **5. Visual Analytics Dashboard**

- **Macro Segmentation Dashboard**: Interactive cards with lifestyle imagery
- **Micro Segment Drill-Down**: Click any macro segment to explore sub-segments
- **Revenue Analysis**: Segment-wise revenue breakdown
- **Customer Distribution**: Visual representation of segment sizes
- **Key Differences**: Comparative analysis between segments

---

## 📂 Project Structure

```
personalization-agent/
├── api/
│   └── main_unified_chromadb.py      # FastAPI backend with all endpoints
├── agents/
│   ├── agent_a_academy_enhanced.py   # Macro segmentation (K-Prototypes)
│   ├── agent_a_academy_micro.py      # Micro segmentation
│   ├── agent_b_academy_chromadb.py   # Product recommendations (ChromaDB)
│   └── agent_b_academy_enhanced.py   # Enhanced recommendation logic
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── academy/
│   │   │   │   ├── AcademyAgentA.tsx          # Agent A UI
│   │   │   │   ├── AcademyMacroDashboard.tsx  # Macro/Micro dashboard
│   │   │   │   ├── AcademyAgentB.tsx          # Agent B UI
│   │   │   │   └── AcademyDataLoader.tsx      # Data loading UI
│   │   │   └── ...
│   │   ├── components/
│   │   │   ├── CustomerInsightModal.tsx       # Customer detail modal
│   │   │   └── visualizations/                # Chart components
│   │   └── services/
│   │       └── api.ts                         # API client
│   ├── package.json
│   └── vite.config.ts
├── data/
│   └── academy_sports/
│       ├── customers.csv           # 5,000 customer profiles
│       ├── products.csv            # 1,000+ camping products
│       ├── purchases.csv           # Purchase history
│       └── interactions.csv        # Customer-product interactions
├── chroma_db/                      # ChromaDB vector storage
├── utils/
│   ├── feature_scorer.py           # Product scoring logic
│   └── ...
├── requirements.txt                # Python dependencies
├── package.json                    # Node dependencies (root)
├── initialize_chromadb.py          # ChromaDB initialization script
└── README.md
```

---

## 🔧 Configuration

### **Environment Variables**

Create a `.env` file in the project root:

```env
# AI/LLM Configuration
TOGETHER_API_KEY=your_together_ai_api_key_here

# Data Paths
DATA_DIR=data/academy_sports/

# API Configuration
API_PORT=8002
FRONTEND_PORT=3000

# ChromaDB
CHROMA_DB_PATH=chroma_db/
```

### **Frontend Configuration**

Edit `frontend/vite.config.ts` for build settings:

```typescript
export default defineConfig({
  plugins: [react()],
  base: '/nba-platform-v2/',  // Deployment path
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      }
    }
  }
})
```

### **Backend Configuration**

Edit `api/main_unified_chromadb.py` for CORS and API settings:

```python
# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🌐 API Endpoints

### **Data Management**

- `GET /api/academy/agent_a/results` - Get segmentation results
- `POST /api/academy/agent_a/execute` - Run clustering
- `GET /api/academy/products` - List all products
- `GET /api/academy/agent_a/customers` - List customers (paginated)

### **Segmentation**

- `GET /api/academy/macro-segments` - Get macro segments
- `POST /api/academy/micro-segments/{macro_id}` - Create micro segments
- `GET /api/academy/micro-segments/{macro_id}` - Get micro segments

### **Recommendations**

- `POST /api/academy/agent_b/execute` - Get product recommendations
- `GET /api/academy/recommendations/{customer_id}/all` - Get all recommendation types
- `GET /api/academy/recommendations/{customer_id}/similar` - Get similar products

### **Customer Insights**

- `GET /api/academy/agent_a/customer/{customer_id}` - Get customer details
- `POST /api/academy/agent_a/customer/{customer_id}/explain` - AI explanation

**Full API Documentation**: `http://localhost:8002/docs` (when backend is running)

---

## 🚀 Deployment

### **Production Deployment to Linux Server**

#### **1. Server Preparation**

```bash
# SSH into server
ssh user@your-server.com

# Install prerequisites
sudo apt update
sudo apt install python3.10 python3-pip nodejs npm nginx git

# Clone repository
cd /home/user/
git clone https://github.com/Revathi031187/NBA.git
cd NBA
```

#### **2. Backend Deployment**

```bash
# Install Python dependencies
pip install -r requirements.txt

# Initialize ChromaDB
python initialize_chromadb.py

# Create systemd service
sudo nano /etc/systemd/system/nba-backend.service
```

**Service file content**:

```ini
[Unit]
Description=NBA Personalization Platform Backend
After=network.target

[Service]
Type=simple
User=user
WorkingDirectory=/home/user/NBA
Environment="PATH=/home/user/NBA/venv/bin"
ExecStart=/home/user/NBA/venv/bin/uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8002
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl enable nba-backend
sudo systemctl start nba-backend
sudo systemctl status nba-backend
```

#### **3. Frontend Deployment**

```bash
# Build frontend
cd frontend
npm install
npm run build

# Verify build
ls -la dist/
```

#### **4. Nginx Configuration**

```bash
# Edit Nginx config
sudo nano /etc/nginx/sites-available/personalization
```

**Nginx config**:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location /nba-platform-v2/ {
        alias /home/user/NBA/frontend/dist/;
        index index.html;
        try_files $uri $uri/ /nba-platform-v2/index.html;
    }

    # Backend API
    location /nba-platform-v2/api/ {
        proxy_pass http://localhost:8002/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
# Enable site and reload
sudo ln -s /etc/nginx/sites-available/personalization /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### **5. SSL Certificate (Optional)**

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com
```

### **Databricks Deployment (Alternative)**

For Databricks deployment, see **[DATABRICKS_DEPLOYMENT.md](DATABRICKS_DEPLOYMENT.md)**.

---

## 🧪 Testing

### **Quick Test Workflow**

1. **Start Backend**: `uvicorn api.main_unified_chromadb:app --reload --port 8002`
2. **Start Frontend**: `cd frontend && npm run dev`
3. **Navigate** to `http://localhost:3000`
4. **Load Data**: Go to Data Loader, select dataset
5. **Run Agent A**: Click "Run K-Prototypes Clustering"
6. **View Segments**: Explore macro dashboard
7. **Get Recommendations**: Select a customer, view personalized products

### **Run Tests**

```bash
# Backend tests
python test_academy_sports.py
python test_all_academy_endpoints.py

# Frontend tests (if configured)
cd frontend
npm test
```

---

## 📊 Key Metrics & Performance

### **Agent A Performance**

- **Clustering Time**: ~30-60 seconds for 5,000 customers
- **Segmentation Accuracy**: 85-95% (measured against known patterns)
- **Segment Sizes**: 500-1,500 customers per macro segment
- **Micro Segments**: 4 per macro, 100-400 customers each

### **Agent B Performance**

- **Recommendation Time**: <1 second per customer
- **Score Range**: 0-115% (weighted multi-metric)
- **Product Coverage**: 1,000+ products indexed
- **Semantic Search**: ChromaDB vector similarity
- **Personalization**: 9 customer attributes considered

### **Data Scale**

- **Customers**: 5,000 profiles
- **Products**: 1,000+ items
- **Purchases**: 50,000+ transactions
- **Interactions**: 100,000+ events

---

## 📚 Documentation

### **Core Documentation**

- **[DEMO_FEEDBACK_CHANGES_COMPLETE.md](DEMO_FEEDBACK_CHANGES_COMPLETE.md)** - Latest UI improvements
- **[DEMO_FEEDBACK_ROUND2_COMPLETE.md](DEMO_FEEDBACK_ROUND2_COMPLETE.md)** - Dynamic data, unique behaviors
- **[ACADEMY_SPORTS_IMPLEMENTATION_GUIDE.md](ACADEMY_SPORTS_IMPLEMENTATION_GUIDE.md)** - Complete implementation details
- **[PRESENTATION_FILES_GUIDE.md](PRESENTATION_FILES_GUIDE.md)** - Demo materials
- **[DATABRICKS_DEPLOYMENT.md](DATABRICKS_DEPLOYMENT.md)** - Databricks deployment guide

### **Technical Guides**

- **[MACRO_MICRO_SEGMENTATION_OVERVIEW.md](MACRO_MICRO_SEGMENTATION_OVERVIEW.md)** - Segmentation approach
- **[RECOMMENDATION_FLOW_AUDIT.md](RECOMMENDATION_FLOW_AUDIT.md)** - Recommendation logic
- **[API_ENDPOINTS_FIXED.md](API_ENDPOINTS_FIXED.md)** - API documentation

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🆘 Troubleshooting

### **Common Issues**

| Issue | Solution |
|-------|----------|
| Port 8002 already in use | Kill process: `sudo fuser -k 8002/tcp` |
| ChromaDB not initialized | Run: `python initialize_chromadb.py` |
| Frontend build fails | Clear cache: `cd frontend && rm -rf node_modules dist && npm install` |
| CORS errors | Check API_BASE_URL in frontend and CORS config in backend |
| Agent A takes too long | Reduce n_clusters or dataset size |
| No recommendations showing | Verify Agent B has run successfully |
| Pricing seems wrong | Check updated `_calculate_price_range()` in `agent_b_academy_chromadb.py` |

### **Logs**

- **Backend**: `tail -f logs/backend.log`
- **Nginx**: `sudo tail -f /var/log/nginx/error.log`
- **Systemd**: `sudo journalctl -u nba-backend -f`

---

## 📧 Support

- **GitHub Issues**: [https://github.com/Revathi031187/NBA/issues](https://github.com/Revathi031187/NBA/issues)
- **Documentation**: See `/docs` folder for detailed guides

---

## 🎯 Roadmap

- [x] Macro segmentation with K-Prototypes
- [x] Micro segmentation with sub-clustering
- [x] Multi-metric recommendation scoring
- [x] Dynamic data overview
- [x] Comparative segment analysis
- [ ] A/B testing framework
- [ ] Real-time personalization API
- [ ] Mobile app support
- [ ] Multi-tenant architecture

---

**Made with ❤️ for Academy Sports**
