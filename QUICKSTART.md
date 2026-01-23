# 🚀 Quick Start Guide

## Get Started in 3 Minutes!

### Option 1: Automated Script (Recommended)

#### Windows
```cmd
run.bat
```

#### Linux/Mac
```bash
chmod +x run.sh
./run.sh
```

Then select:
1. Generate Synthetic Data (first time only)
2. Run Streamlit UI

### Option 2: Manual Commands

```bash
# Step 1: Install dependencies
pip install -r requirements.txt

# Step 2: Generate data (first time only)
python main.py generate-data

# Step 3: Run the UI
streamlit run app.py
```

### Option 3: Docker (Production)

```bash
# Build and run
docker-compose up --build

# Access:
# - UI: http://localhost:8501
# - API: http://localhost:8000
```

---

## 🎯 First Steps in the UI

1. **Click "Generate Synthetic Data"** (if not done already)
   - Generates 10,000 customers, 100 products, 50,000 transactions

2. **Click "Initialize System"**
   - Trains all 5 AI agents
   - Takes ~2-3 minutes

3. **Go to "NBA Generator"**
   - Select any customer
   - Click "Generate Next Best Actions"
   - See personalized recommendations!

---

## 📍 Key Pages

### 📊 Overview
- System metrics and health
- Persona & intent distribution
- Performance trends

### 🎯 NBA Generator
- Select customer
- Configure context
- Generate personalized offers
- See all 5 agents in action

### 🤖 Agent Insights
- Deep dive into each agent
- Persona analysis
- Product performance
- RL metrics
- Marketing mix optimization

### 📈 Analytics
- Revenue trends
- Channel performance
- Customer lifetime value

---

## 💡 Pro Tips

1. **Use the sidebar** to check system status
2. **Watch the progress bar** when generating NBA
3. **Hover over charts** for interactive details
4. **Try different customers** to see varying personas
5. **Explore Agent Insights** to understand how decisions are made

---

## 🆘 Troubleshooting

**System not initializing?**
- Make sure you generated synthetic data first
- Check logs in `logs/` folder

**Missing dependencies?**
- Run: `pip install -r requirements.txt`

**Port already in use?**
- Change port: `streamlit run app.py --server.port=8502`

---

## 🎓 Learn More

- See `README.md` for detailed architecture
- Check `config/agents.yaml` for configuration
- Browse code in `agents/` folder to understand each agent

---

**Enjoy exploring the Agentic AI system! 🚀**

