# Together AI Setup Guide

To enable AI-powered customer persona explanations, you need to configure your Together AI API key.

## 🔑 Getting Your API Key

1. **Sign up or log in** to [Together AI](https://api.together.xyz/)
2. Navigate to **Settings → API Keys**
3. Click **"Create new API key"**
4. Copy your API key

## ⚙️ Configuration

### Option 1: Environment Variable (Recommended)

#### Windows (PowerShell):
```powershell
# Set for current session
$env:TOGETHER_API_KEY="your_api_key_here"

# Or set permanently
[System.Environment]::SetEnvironmentVariable('TOGETHER_API_KEY', 'your_api_key_here', 'User')
```

#### Windows (CMD):
```cmd
set TOGETHER_API_KEY=your_api_key_here
```

#### Linux/Mac:
```bash
# Add to ~/.bashrc or ~/.zshrc
export TOGETHER_API_KEY="your_api_key_here"

# Then reload
source ~/.bashrc  # or source ~/.zshrc
```

### Option 2: Create .env File

Create a `.env` file in the project root:

```env
TOGETHER_API_KEY=your_api_key_here
```

**Note:** If you use this method, you'll need to install `python-dotenv`:

```bash
pip install python-dotenv
```

And add this to the top of `api/main_unified_chromadb.py`:

```python
from dotenv import load_dotenv
load_dotenv()
```

### Option 3: Manual Entry (No Restart Required)

If you don't want to set environment variables:
1. Go to **Academy Sports → Agent A → Customer Insights**
2. Click any customer's **"View Details"**
3. Click **"Configure API Key"** button
4. Enter your API key manually

## 🚀 Restart Backend

After setting the environment variable, restart your backend server:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
cd api
py -3.10 main_unified_chromadb.py
```

## ✅ Verify Setup

1. Start the backend server
2. Go to: http://localhost:8002/api/config/together-api-key
3. You should see: `{"api_key": "your_key...", "configured": true}`

## 🧪 Test It Out

1. Navigate to **Academy Sports → Agent A: Customer Personas**
2. Click **"Run K-Prototypes Clustering"** (if not already done)
3. Click the **"Customer Insights"** tab
4. Click **"View Details"** on any customer
5. Click **"Generate Explanation"** - it should work automatically!

## 📝 Notes

- The API key is **never exposed** to the browser
- It's fetched from the backend securely
- You only need to enter it manually if the environment variable isn't set
- Free tier includes **1M tokens per day**

## 🔗 Useful Links

- [Together AI Dashboard](https://api.together.xyz/)
- [Together AI Documentation](https://docs.together.ai/)
- [API Keys Management](https://api.together.xyz/settings/api-keys)

---

**Need help?** Check the backend logs for any errors related to Together AI authentication.

