# 📋 Agent B Test Script Guide

## 🎯 What This Script Tests

The `test_agent_b_complete.py` script performs **comprehensive validation** of both Agent B approaches with detailed debugging.

---

## 🧪 Test Coverage

### 1. **Weight Validation** ✓
- Verifies all 13 factors sum to exactly 100%
- Shows tier breakdowns (TIER 1: 55%, TIER 2: 28%, etc.)
- Displays each factor's weight

### 2. **Data Loading** ✓
- Loads customers, products, transactions
- Validates column names
- Analyzes product attribute diversity:
  - Unique fee values
  - Min balance ranges
  - Interest rate ranges
  - Categories and subcategories

### 3. **Agent A Personas** ✓
- Runs customer segmentation
- Creates 5 personas
- Shows persona names, sizes, emojis

### 4. **Rule-Based Agent B** ✓
- **TEST 1**: Persona mode (Personal Banking)
- **TEST 2**: Customer mode (Specific customer)
- **TEST 3**: Category filter (Checking only)
- **TEST 4**: Search query ('savings')

### 5. **Hybrid ML Agent B** ✓
- **TEST 5**: Persona mode with ML
- **TEST 6**: Customer mode with ML
- **TEST 7**: Category filter (Savings) - CRITICAL TEST!
- **TEST 8**: Search query ('checking')
- Validates 50% ML + 50% Rules calculation

### 6. **13-Factor Scorer Direct Test** ✓
- **TEST 9**: Scores 3 different products for same customer
- Shows detailed factor breakdowns
- Validates Product Value factor (NEW!)
- Checks score differentiation

### 7. **Product Value Factor Theory** ✓
- Tests expected scores for different product types
- Validates fee/rate/balance/ROI scoring logic
- Shows expected differentiation spread

---

## 🚀 How to Run

### Method 1: Batch File (Easy)
```bash
RUN_AGENT_B_TEST.bat
```

### Method 2: Direct Python
```bash
py -3.10 test_agent_b_complete.py
```

---

## 📊 What to Look For

### ✅ PASS Indicators

#### 1. Weight Validation
```
📊 13-Factor Weight Distribution:
  GRAND TOTAL: 100.00%
  ✅ PASS: Weights sum to 100%
```

#### 2. Score Differentiation
```
📊 Top 5 Product Scores:
  1. FREE Business Checking    | Score: 0.8234 (82.3%)
  2. Business Savings          | Score: 0.7912 (79.1%)
  3. Ultimate Business Check   | Score: 0.7456 (74.6%)
  4. Business Money Market     | Score: 0.7289 (72.9%)
  5. Business Credit Cards     | Score: 0.7134 (71.3%)

  ✅ PASS: 5 unique scores (good differentiation!)
```

#### 3. Product Value Factor
```
Key Factor Breakdowns:
  - product_value:           11.5% (weight: 12%)
    └─ No annual fee (excellent) | No minimum balance | Free checking - great value

  ✅ Product Value factor exists!
```

#### 4. Hybrid ML Validation
```
🔍 Hybrid Scoring Validation:
  ML Contribution:   0.3421 × 0.5 = 0.1710
  Rule Contribution: 0.6789 × 0.5 = 0.3394
  Expected Final:    0.5104
  Actual Final:      0.5104
  ✅ PASS: Hybrid calculation correct!
```

#### 5. Category Filter
```
TEST 7: Hybrid ML - Category Filter (Savings)
  ✅ Returned 4 recommendations
  ✅ PASS: Category filter working
```

---

### ❌ FAIL Indicators

#### Weight Sum Error
```
GRAND TOTAL: 104.00%
❌ FAIL: Weights sum to 104% (should be 100%)
Error margin: 4.00%
```
**Fix**: Adjust TIER 3 weights down by 4%

#### Identical Scores
```
Top 5 Product Scores:
  1. Product A | Score: 0.6217 (62.2%)
  2. Product B | Score: 0.6217 (62.2%)  ← IDENTICAL
  3. Product C | Score: 0.6217 (62.2%)  ← IDENTICAL

  ⚠️ WARNING: All scores are IDENTICAL (0.6217)
  Product Value factor may not be working properly!
```
**Fix**: Check if `_calculate_product_value` method exists and is called

#### Missing Product Value
```
🔍 13-Factor Scoring Validation:
  ✅ detailed_calculation exists
  Factors present: 12
  ❌ FAIL: Product Value factor missing!
```
**Fix**: Add Factor 4 (product_value) to scorer

#### Category Filter Broken
```
TEST 7: Hybrid ML - Category Filter (Savings)
  ✅ Returned 0 recommendations
  ❌ FAIL: Category filter returned 0 products!
  This is the bug user reported - category filtering broke!
```
**Fix**: Check category filtering logic in `agent_b_banking_logit_enhanced.py`

---

## 📋 Detailed Test Breakdown

### TEST 1: Persona Mode - Personal Banking
- Selects Persona 1 (Growth Builders)
- Gets 10 recommendations
- **Validates**: Score differentiation, 13-factor scoring, Product Value factor

### TEST 2: Customer Mode
- Uses first customer from dataset
- Gets personalized recommendations
- **Validates**: Customer-specific scoring

### TEST 3: Category Filter - Checking
- Filters to Checking accounts only
- **Validates**: All returned products are Checking subcategory

### TEST 4: Search Query - 'savings'
- Searches for products matching 'savings'
- **Validates**: Relevant products returned

### TEST 5: Hybrid ML - Persona Mode
- Tests ML-based recommendations
- **Validates**: ML probability, rule score, hybrid calculation

### TEST 6: Hybrid ML - Customer Mode
- Tests ML with specific customer
- **Validates**: Customer-level predictions

### TEST 7: Hybrid ML - Category Filter (CRITICAL)
- Tests category filtering in ML approach
- **This was broken before!**
- **Validates**: Non-zero results, correct category

### TEST 8: Hybrid ML - Search Query
- Tests search with ML approach
- **Validates**: Search functionality

### TEST 9: 13-Factor Scorer Direct
- Scores 3 different products for same customer
- **Validates**: 
  - Score differentiation
  - Product Value factor working
  - Factor breakdowns correct

---

## 🔍 Debugging Output

The script includes extensive debugging:

### Product-Level Debugging
```
Product 1: Worry-FREE Checking®
  - Annual Fee: $0
  - Min Balance: $0
  - Interest Rate: 0.00%
  - Subcategory: Checking

  🎯 TOTAL SCORE: 0.6823 (68.2%)

  Key Factor Breakdowns:
    - eligibility_score:      22.0% (weight: 22%)
    - financial_need_match:   17.8% (weight: 18%)
    - product_value:          11.5% (weight: 12%)
      └─ No annual fee (excellent) | No minimum balance
    - product_pairing:         4.5% (weight: 9%)
```

### Score Differentiation Analysis
```
🔍 Score Differentiation Analysis:
  - Product 1 (Worry-FREE):     0.6823
  - Product 2 (High Yield):     0.7145
  - Product 3 (Money Market):   0.6734
  
  ✅ PASS: All 3 products have DIFFERENT scores!
  Score range: 0.0411 (4.1% spread)
```

---

## 📄 Output Files

### 1. Console Output
- Detailed test results
- Pass/fail status for each test
- Debugging information

### 2. JSON Results (`test_agent_b_results.json`)
```json
{
  "test_results": {
    "weight_validation": true,
    "data_loading": true,
    "agent_a": true,
    "rule_based": true,
    "hybrid_ml": true,
    "13_factor_scorer": true,
    "product_value_test": true
  },
  "summary": {
    "total_tests": 7,
    "passed": 7,
    "failed": 0,
    "pass_rate": "100.0%"
  }
}
```

---

## 🎯 Success Criteria

### Minimum Requirements
- ✅ Weights sum to 100%
- ✅ Data loads without errors
- ✅ Agent A creates 5 personas
- ✅ Rule-Based returns recommendations
- ✅ Hybrid ML returns recommendations

### Quality Requirements
- ✅ Scores are differentiated (not all identical)
- ✅ Product Value factor exists
- ✅ Category filters work
- ✅ Search queries work
- ✅ Hybrid calculation correct (50/50 split)

### Excellence Requirements
- ✅ Score spread > 5% (significant differentiation)
- ✅ Product Value factor shows detailed breakdown
- ✅ All 13 factors present in breakdown
- ✅ Zero errors or warnings

---

## 🐛 Common Issues & Fixes

### Issue: "Weights must sum to 1.0, got 1.04"
**Fix**: TIER 3 weights too high - reduce by 4%

### Issue: All scores identical
**Fix**: Add Product Value factor (12%) to differentiate products

### Issue: Category filter returns 0 products
**Fix**: Use proper column checking and boolean masking

### Issue: "Objects are not valid as React child"
**Fix**: Extract scalar values before rendering in frontend

---

## 📞 Next Steps

1. **Run the test**: `RUN_AGENT_B_TEST.bat`
2. **Review output**: Look for PASS/FAIL indicators
3. **Share results**: Copy the console output or send `test_agent_b_results.json`
4. **Fix issues**: If any tests fail, output shows exactly what's wrong

---

🎯 **This script catches ALL issues before you see them in the UI!**
