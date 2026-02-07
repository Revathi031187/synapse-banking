# Agent B Implementation Comparison Test Guide

## Overview

`test_agent_b_comparison.py` is a comprehensive validation script that compares the Banking Agent B implementation against Academy Sports Agent B to ensure they match structurally while maintaining domain-specific logic.

---

## What This Test Does

### 1. **Academy Sports Agent B Test**
- Fetches a customer from Academy Sports
- Executes Agent B with Academy Sports endpoint
- Validates response structure
- Analyzes recommendation fields
- Checks metadata

### 2. **Banking Agent B Test**
- Fetches a customer from Banking domain
- Executes Agent B with Banking endpoint
- Validates response structure matching Academy Sports
- Analyzes recommendation fields
- Checks banking-specific fields (eligibility, annual_fee, etc.)
- Validates 12-factor score breakdown

### 3. **Side-by-Side Comparison**
- Compares response structures
- Identifies common vs domain-specific fields
- Compares recommendation counts
- Validates metadata format
- Checks field-level compatibility

### 4. **AI Explanation Test (Banking-Specific)**
- Tests the `/api/banking/agent_b/explain` endpoint
- Validates Together AI integration
- Checks AI-generated explanation quality

---

## How to Run

### Prerequisites
1. **Backend must be running:**
   ```bash
   RESTART_ACADEMY_MATCH.bat
   ```

2. **Agent A must be executed for both domains:**
   - Execute Academy Sports Agent A
   - Execute Banking Agent A

### Run the Test
```bash
TEST_AGENT_B_COMPARISON.bat
```

Or directly with Python:
```bash
python test_agent_b_comparison.py
```

---

## Expected Output

### ✅ Success Output Example

```
================================================================================
ACADEMY SPORTS AGENT B TEST
================================================================================

ℹ️  Testing with customer: CUST_00001

Checking Academy Sports Response Structure:
✅ Has 'customer_id': str
✅ Has 'tailored_recommendations': list
   └─ Count: 3
✅ Has 'segment_recommendations': list
   └─ Count: 3
✅ Has 'recommendation_metadata': dict

Analyzing Academy Tailored Recommendations:
ℹ️  Total recommendations: 3

First recommendation keys:
  - product_id: str
  - product_name: str
  - main_category: str
  - propensity_score: float
  - reasoning: str
  - score_breakdown: dict (nested)

Required fields check:
✅ Has 'product_id'
✅ Has 'product_name'
✅ Has 'propensity_score'
✅ Has 'reasoning'

================================================================================
BANKING AGENT B TEST
================================================================================

ℹ️  Testing with customer: CUST_00001

Checking Banking Response Structure:
✅ Has 'success': bool
✅ Has 'customer_id': str
✅ Has 'tailored_recommendations': list
   └─ Count: 3
✅ Has 'segment_recommendations': list
   └─ Count: 3
✅ Has 'recommendation_metadata': dict

Analyzing Banking Tailored Recommendations:
ℹ️  Total recommendations: 3

Banking-Specific Checks:

Banking-specific fields:
✅ Has 'category': Savings
✅ Has 'annual_fee': 0
✅ Has 'min_balance': 1000
✅ Has 'interest_rate': 0.025
✅ Has 'eligibility_status': Eligible

12-Factor Score Breakdown:
✅ Has 'score_breakdown' (12-factor scoring)

12-Factor Score Breakdown:
  - eligibility_score: 0.950
  - financial_need_match: 0.820
  - relationship_depth: 0.750
  - product_pairing: 0.880
  - channel_fit: 0.700
  - life_stage_fit: 0.850
  - engagement_score: 0.780
  - growth_potential: 0.820
  - risk_alignment: 0.750
  - seasonal_relevance: 0.500
  - competitive_position: 0.800
  - cross_sell_synergy: 0.900

================================================================================
IMPLEMENTATION COMPARISON
================================================================================

Structure Match:
ℹ️  Common keys: 7
  ✓ customer_id
  ✓ customer_info
  ✓ recommendation_metadata
  ✓ segment_recommendations
  ✓ similar_products
  ✓ tailored_recommendations
  ✓ you_might_like

Recommendation Counts:

                 Section  Academy  Banking Match
  Tailored Recommendations        3        3    ✅
  Segment Recommendations        3        3    ✅

Recommendation Fields Comparison:

Common fields (10):
  ✓ eligibility_status
  ✓ in_stock
  ✓ product_id
  ✓ product_name
  ✓ propensity_score
  ✓ reasoning
  ✓ score
  ✓ score_breakdown

Banking-only fields (domain-specific): ['annual_fee', 'category', 'interest_rate', 'min_balance']

================================================================================
AI EXPLANATION TEST
================================================================================

ℹ️  Testing AI explanation for product: PROD_123

AI Explanation Response:
{
  "success": true,
  "explanation": "This Premium Savings Account is recommended because..."
}

✅ AI Explanation generated: 147 characters

Explanation:
This Premium Savings Account is recommended because it pairs perfectly with your existing Checking and Investment accounts, offering competitive rates.

================================================================================
FINAL SUMMARY
================================================================================

Compatibility Checks: 5/5
✅ Both have 'tailored_recommendations'
✅ Both have 'segment_recommendations'
✅ Both have 'recommendation_metadata'
✅ Banking has recommendations
✅ Banking has score_breakdown (12-factor)

🎉 ALL CHECKS PASSED!
Banking Agent B successfully matches Academy Sports structure!
```

---

## What to Look For

### ✅ Good Signs

1. **All structure checks pass**
   - Both have `tailored_recommendations`
   - Both have `segment_recommendations`
   - Both have `recommendation_metadata`

2. **Recommendation counts > 0**
   - Tailored: 3+
   - Segment: 3+

3. **Banking-specific fields present**
   - `category`
   - `annual_fee`
   - `min_balance`
   - `interest_rate`
   - `eligibility_status`

4. **12-Factor scoring breakdown**
   - `score_breakdown` dict with 12 factors
   - All scores between 0.0 and 1.0

5. **AI explanation works**
   - Returns 2-3 sentence explanation
   - Uses Together AI

### ⚠️ Warning Signs

1. **Missing recommendations**
   - Empty `tailored_recommendations`
   - Empty `segment_recommendations`

2. **Missing required fields**
   - No `propensity_score`
   - No `reasoning`
   - No `score_breakdown`

3. **AI explanation fails**
   - 500 error
   - Missing explanation text

### ❌ Error Signs

1. **Structure mismatch**
   - Missing `tailored_recommendations` or `segment_recommendations`
   - Different key names than Academy Sports

2. **API failures**
   - 404 errors (endpoint not found)
   - 500 errors (internal server error)

3. **No data**
   - No customers found (Agent A not run)
   - No recommendations generated

---

## Interpreting Results

### Scenario 1: All Checks Pass ✅
**Status:** Perfect!

**What it means:**
- Banking Agent B matches Academy Sports structure exactly
- All required fields present
- Banking-specific features working
- AI explanations functional

**Next steps:**
- Deploy to production
- Test with real users

---

### Scenario 2: Structure matches, but no recommendations ⚠️
**Status:** Agent B not initialized properly

**What it means:**
- Structure is correct
- Agent B logic may have issues
- Persona recommender might not be working

**Next steps:**
1. Check if Agent A was executed
2. Verify personas were created
3. Check backend logs for errors
4. Restart backend: `RESTART_ACADEMY_MATCH.bat`

---

### Scenario 3: Missing 12-factor scoring ⚠️
**Status:** Scorer not initialized

**What it means:**
- Recommendations work
- But scoring system not active
- May be using default scores

**Next steps:**
1. Check if `Banking12FactorScorer` imports correctly
2. Verify all dependencies installed
3. Check for import errors in backend logs

---

### Scenario 4: AI explanation fails ❌
**Status:** Together AI not configured

**What it means:**
- Core recommendations work
- But AI generation broken
- API key might be invalid

**Next steps:**
1. Check `.env` has `TOGETHER_API_KEY`
2. Verify API key is valid
3. Check Together AI rate limits
4. Review `together_ai.py` implementation

---

### Scenario 5: Structure completely different ❌
**Status:** Wrong implementation

**What it means:**
- Using old Agent B code
- Not matching Academy Sports structure

**Next steps:**
1. Re-run: `RESTART_ACADEMY_MATCH.bat`
2. Verify `agent_b_banking_enhanced_v2.py` has latest code
3. Check API endpoint uses `get_all_recommendations()`

---

## Comparison Checklist

Use this to manually verify the test results:

- [ ] **Structure Match**
  - [ ] Banking has `tailored_recommendations`
  - [ ] Banking has `segment_recommendations`
  - [ ] Banking has `recommendation_metadata`
  - [ ] Banking has `customer_info`

- [ ] **Recommendation Content**
  - [ ] Tailored count > 0
  - [ ] Segment count > 0
  - [ ] Each has `product_id`
  - [ ] Each has `product_name`
  - [ ] Each has `propensity_score`
  - [ ] Each has `reasoning`

- [ ] **Banking-Specific**
  - [ ] Has `category` field
  - [ ] Has `annual_fee` field
  - [ ] Has `min_balance` field
  - [ ] Has `interest_rate` field
  - [ ] Has `eligibility_status` field
  - [ ] Has `score_breakdown` dict
  - [ ] Score breakdown has 12 factors

- [ ] **12-Factor Scoring**
  - [ ] `eligibility_score`
  - [ ] `financial_need_match`
  - [ ] `relationship_depth`
  - [ ] `product_pairing`
  - [ ] `channel_fit`
  - [ ] `life_stage_fit`
  - [ ] `engagement_score`
  - [ ] `growth_potential`
  - [ ] `risk_alignment`
  - [ ] `seasonal_relevance`
  - [ ] `competitive_position`
  - [ ] `cross_sell_synergy`

- [ ] **AI Integration**
  - [ ] Explanation endpoint works
  - [ ] Returns text explanation
  - [ ] Uses Together AI
  - [ ] 2-3 sentences long

---

## Troubleshooting

### Issue: "No customers found"
**Solution:** Run Agent A first for both domains

### Issue: "Request failed: 404"
**Solution:** Backend not running or wrong port. Run `RESTART_ACADEMY_MATCH.bat`

### Issue: "AI explanation failed"
**Solution:** Check `.env` for `TOGETHER_API_KEY`

### Issue: "Structure mismatch"
**Solution:** Verify using latest `agent_b_banking_enhanced_v2.py` code

### Issue: "Empty recommendations"
**Solution:** Check if Agent A created personas, verify customer has transactions

---

## Files Modified for Academy Sports Match

1. `agents/agent_b_banking_enhanced_v2.py` - Complete rewrite
2. `api/main_unified_chromadb.py` - Updated endpoint to call `get_all_recommendations()`
3. `frontend/src/pages/banking/BankingAgentB.tsx` - Updated to display two sections

---

## Next Steps After Successful Test

1. **Test in browser:**
   - Navigate to Banking Agent B page
   - Select a customer
   - Click "Get Customer Recommendations"
   - Verify two sections appear (Tailored + Segment)
   - Click "Get AI Explanation" button

2. **Performance testing:**
   - Test with multiple customers
   - Verify response times < 3 seconds
   - Check if scoring is consistent

3. **Documentation:**
   - Update README with new structure
   - Create demo video
   - Document API endpoints

4. **Deployment:**
   - Push to GitHub
   - Update production environment
   - Monitor for errors
