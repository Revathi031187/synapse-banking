# 🔴 URGENT: Python 3.14 Alpha → Python 3.11 Downgrade Guide

## Why You Need to Downgrade

**Your current Python:** 3.14.0a7 (alpha - pre-release)  
**Required Python:** 3.11.x or 3.12.x (stable)

### What's Failing:
- ❌ FastAPI won't start
- ❌ Pydantic import errors
- ❌ pandas crashes
- ❌ Backend server won't run

### Why:
Python 3.14 is **NOT RELEASED YET**. It's an alpha version with breaking changes that libraries haven't adapted to yet.

---

## Step-by-Step Downgrade Instructions

### Step 1: Uninstall Python 3.14 Alpha

1. **Open Windows Settings:**
   - Press `Win + I`
   - Go to "Apps" → "Installed apps"

2. **Find and Uninstall:**
   - Search for "Python 3.14"
   - Click the `...` menu → "Uninstall"
   - Follow the prompts

### Step 2: Download Python 3.11

1. **Go to Python.org:**
   - Visit: https://www.python.org/downloads/
   - Look for "Python 3.11.9" (or latest 3.11.x)
   - Click "Download"

2. **Download the Windows Installer:**
   - Choose: **"Windows installer (64-bit)"**
   - NOT the "embeddable package"
   - NOT any "alpha" or "beta" versions

### Step 3: Install Python 3.11

1. **Run the Installer:**
   - Double-click the downloaded file
   - **IMPORTANT:** ✅ Check **"Add Python 3.11 to PATH"**
   - Click **"Install Now"**

2. **Optional (Recommended):**
   - At the end, click "Disable path length limit" if prompted
   - This prevents path-too-long errors

3. **Wait for Installation:**
   - Should take 1-2 minutes

### Step 4: Verify Installation

1. **Open NEW Command Prompt:**
   - Close any existing terminals
   - Open fresh Command Prompt
   - Press `Win + R`, type `cmd`, press Enter

2. **Check Version:**
   ```bash
   python --version
   ```
   
   **Expected Output:**
   ```
   Python 3.11.9
   ```
   
   **If you still see 3.14:**
   - Close ALL terminals
   - Restart your computer
   - Try again

### Step 5: Reinstall Packages

1. **Navigate to Project:**
   ```bash
   cd C:\Users\jaisonsamuel.d.lv\Desktop\personalization-agent-banking
   ```

2. **Upgrade pip:**
   ```bash
   python -m pip install --upgrade pip
   ```

3. **Install All Requirements:**
   ```bash
   pip install -r requirements.txt
   ```
   
   This will take 2-5 minutes.

### Step 6: Test Everything

1. **Check Python Again:**
   ```bash
   CHECK_PYTHON_VERSION.bat
   ```
   
   Should show Python 3.11.x ✅

2. **Start Backend:**
   ```bash
   RESTART_AND_TEST_FIX.bat
   ```
   
   Should start without import errors ✅

3. **Test Agent B:**
   ```bash
   TEST_API_DIRECT.bat
   ```
   
   Should pass all checks ✅

---

## Troubleshooting

### Problem: Still seeing Python 3.14 after install

**Solution:**
1. Close ALL terminals
2. Restart computer
3. Check again with `python --version`

### Problem: "pip not found"

**Solution:**
```bash
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

### Problem: Multiple Python versions found

**Solution:**
```bash
# Use full path to Python 3.11
C:\Users\jaisonsamuel.d.lv\AppData\Local\Programs\Python\Python311\python.exe --version
```

Then use that full path for all commands.

### Problem: Packages fail to install

**Solution:**
```bash
# Install essential packages first
pip install fastapi uvicorn pandas numpy
pip install -r requirements.txt
```

---

## After Successful Downgrade

You should see:

1. **Python Version:**
   ```
   Python 3.11.9
   ```

2. **Backend Starts Successfully:**
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8002 (Press CTRL+C to quit)
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   ```

3. **No Import Errors!**

4. **All Tests Pass:**
   ```
   [OK] Backend is running
   [OK] Agent A executed
   [OK] Agent B executed
   [OK] All response fields present
   ```

---

## Why Python 3.14 Alpha Doesn't Work

### What is an Alpha Release?

- **Alpha** = Pre-release version for testing NEW Python features
- **Intended for:** Python core developers
- **NOT for:** Regular development, production, or real projects

### The Problem with Alpha Releases:

```python
# Python 3.14 alpha changed this internal API:
from annotationlib import get_annotate_from_class_namespace

# But pydantic (used by FastAPI) still expects the OLD API
# Result: ImportError and backend crash
```

### Libraries Need Time to Adapt:

1. **Python 3.14** releases (officially) → October 2025
2. **Libraries update** → November-December 2025
3. **Safe to use 3.14** → January 2026+

Right now (February 2026), even though 3.14 might be released, libraries are still catching up!

---

## Which Python Version Should You Use?

### ✅ Best Choice: Python 3.11.x
- **Most stable**
- **Best compatibility** with all libraries
- **Recommended for production**
- What most developers use

### ✅ Also Good: Python 3.12.x
- Newer features
- Still stable
- Good library support

### ❌ Avoid: Python 3.14.x
- Too new
- Breaking changes
- Limited library support
- Not for production

---

## Quick Reference Commands

```bash
# 1. Check current version
python --version

# 2. Check where Python is installed
where python

# 3. Navigate to project
cd C:\Users\jaisonsamuel.d.lv\Desktop\personalization-agent-banking

# 4. Install packages
pip install -r requirements.txt

# 5. Start backend
RESTART_AND_TEST_FIX.bat

# 6. Test Agent B
TEST_API_DIRECT.bat
```

---

## Need Help?

If you're stuck:

1. **Check version again:**
   ```bash
   CHECK_PYTHON_VERSION.bat
   ```

2. **Try restarting computer**
   - This refreshes PATH variables

3. **Make sure you checked "Add Python to PATH"**
   - During installation
   - If not, reinstall Python 3.11

4. **Use full Python path:**
   ```bash
   C:\Users\jaisonsamuel.d.lv\AppData\Local\Programs\Python\Python311\python.exe --version
   ```

---

## Summary

| Current State | Required Action | Expected Result |
|---------------|----------------|-----------------|
| Python 3.14 alpha | Install Python 3.11 | Backend starts |
| Import errors | Reinstall packages | No errors |
| Backend crashes | Use stable Python | All tests pass |

**Bottom line:** Python 3.14 alpha is too new. Use Python 3.11 (stable and proven).

---

## Downloads

- **Python 3.11.9:** https://www.python.org/downloads/release/python-3119/
- **Python 3.12.7:** https://www.python.org/downloads/release/python-3127/

Choose the "Windows installer (64-bit)" option.

**DO NOT download:**
- ❌ Pre-release versions
- ❌ Alpha/Beta versions
- ❌ Python 3.14 (too new)
