# Agent B Testing Guide

## Quick Start (Easiest)

Just run this - it handles everything automatically:

```bash
QUICK_TEST_AGENT_B.bat
```

**What it does:**
- ✅ Checks if backend is running
- ✅ Auto-executes Banking Agent A (if needed)
- ✅ Tests Banking Agent B structure
- ✅ Validates Academy Sports compatibility
- ✅ Shows clear pass/fail results

---

## Available Test Scripts

### 1. `QUICK_TEST_AGENT_B.bat` ⭐ RECOMMENDED
**Use when:** You just want to quickly test if Banking Agent B works

**Requirements:**
- Backend running on port 8002

**What it tests:**
- Banking Agent B structure
- Compatibility with Academy Sports format
- Banking-specific features (12-factor scoring)
- AI explanations

**Auto-fixes:**
- Will execute Banking Agent A if no customers found
- Will skip Academy comparison if not available
- Will provide troubleshooting tips if errors occur

---

### 2. `RUN_FULL_AGENT_B_TEST.bat`
**Use when:** You want to test BOTH Academy Sports and Banking

**Requirements:**
- Backend running on port 8002
- Both Academy and Banking data loaded

**What it tests:**
- Academy Sports Agent B
- Banking Agent B
- Side-by-side structure comparison
- Field compatibility
- Domain-specific features

**Steps:**
1. Executes Academy Sports Agent A
2. Executes Banking Agent A
3. Runs full comparison test

---

### 3. `TEST_AGENT_B_COMPARISON.bat`
**Use when:** Agent A already executed for both domains

**Requirements:**
- Backend running
- Academy Agent A executed
- Banking Agent A executed

**What it tests:**
- Direct comparison of both implementations
- No auto-execution of Agent A

---

## Test Output Explained

### ✅ Success Output

```
================================================================================
FINAL SUMMARY
================================================================================

Banking Structure Checks: 5/5
✅ Banking has 'tailored_recommendations'
✅ Banking has 'segment_recommendations'
✅ Banking has 'recommendation_metadata'
✅ Banking has recommendations
✅ Banking has score_breakdown (12-factor)

✅ BANKING AGENT B STRUCTURE VALIDATED!
All Academy Sports structure requirements met!
```

**What this means:**
- Your implementation is working correctly
- Structure matches Academy Sports
- All required features present
- Ready for production use

---

### ⚠️ Partial Success Output

```
Banking Structure Checks: 4/5
✅ Banking has 'tailored_recommendations'
✅ Banking has 'segment_recommendations'
✅ Banking has 'recommendation_metadata'
✅ Banking has recommendations
❌ Banking has score_breakdown (12-factor)

⚠️  SOME CHECKS FAILED
Review the output above for details
```

**What this means:**
- Core structure is correct
- But some features missing (e.g., 12-factor scoring)
- Check the specific failed test above

**Common issues:**
- `score_breakdown` missing: Banking12FactorScorer not initialized
- Empty recommendations: No eligible products for customer
- Missing metadata: Agent initialization issue

---

### ❌ Failure Output

```
❌ Banking test failed - cannot provide summary

Troubleshooting:
  1. Is the backend running? Check: http://localhost:8002/health
  2. Try restarting: RESTART_ACADEMY_MATCH.bat
  3. Check backend logs for errors
```

**What this means:**
- Test couldn't complete
- Likely backend or data issue

**Fix:**
1. Check backend is running: `http://localhost:8002/health`
2. Restart: `RESTART_ACADEMY_MATCH.bat`
3. Review backend terminal for errors

---

## What Gets Tested

### Structure Tests
- [x] Has `tailored_recommendations` array
- [x] Has `segment_recommendations` array
- [x] Has `recommendation_metadata` object
- [x] Has `customer_info` object
- [x] Has `similar_products` (backward compatibility)
- [x] Has `you_might_like` (backward compatibility)

### Recommendation Content Tests
- [x] Each recommendation has `product_id`
- [x] Each recommendation has `product_name`
- [x] Each recommendation has `propensity_score`
- [x] Each recommendation has `reasoning`
- [x] Each recommendation has `score_breakdown`

### Banking-Specific Tests
- [x] Has `category` field (Savings, Investment, etc.)
- [x] Has `annual_fee` field
- [x] Has `min_balance` field
- [x] Has `interest_rate` field
- [x] Has `eligibility_status` field
- [x] Score breakdown contains 12 factors
- [x] All factor scores between 0.0 and 1.0

### 12-Factor Scoring Tests
- [x] `eligibility_score` - Credit/income/balance eligibility
- [x] `financial_need_match` - Product fits financial needs
- [x] `relationship_depth` - Customer relationship strength
- [x] `product_pairing` - Complementary products
- [x] `channel_fit` - Digital vs. branch preference
- [x] `life_stage_fit` - Age/life stage alignment
- [x] `engagement_score` - Activity level
- [x] `growth_potential` - Customer growth trajectory
- [x] `risk_alignment` - Risk profile match
- [x] `seasonal_relevance` - Timing considerations
- [x] `competitive_position` - Competitive positioning
- [x] `cross_sell_synergy` - Cross-sell opportunities

### AI Explanation Tests
- [x] `/api/banking/agent_b/explain` endpoint works
- [x] Returns AI-generated explanation
- [x] Uses Together AI
- [x] Explanation is 2-3 sentences
- [x] Explanation references customer profile
- [x] Explanation mentions product features

---

## Interpreting Results

### Scenario 1: All 5/5 checks pass ✅
**Status:** Perfect!

**What to do:**
1. Test in browser
2. Navigate to Banking Agent B page
3. Select a customer
4. Verify two sections appear (Tailored + Segment)
5. Click "Get AI Explanation"
6. Deploy to production

---

### Scenario 2: 4/5 checks pass (missing score_breakdown) ⚠️
**Status:** Core works, scoring not initialized

**Fix:**
```python
# Check if Banking12FactorScorer is imported correctly
from agents.banking_12_factor_scorer import Banking12FactorScorer

# Check if it's initialized in Agent B
self.enhanced_scorer = Banking12FactorScorer(...)
```

**Restart backend:** `RESTART_ACADEMY_MATCH.bat`

---

### Scenario 3: No recommendations returned ⚠️
**Status:** Agent B running, but no eligible products

**Possible causes:**
- Customer doesn't have transaction history
- No eligible products (credit/income requirements too high)
- All products already owned by customer

**Fix:**
1. Try different customer
2. Check product catalog has variety
3. Review eligibility requirements in products

---

### Scenario 4: Agent A auto-execution fails ❌
**Status:** Can't create personas

**Error:**
```
❌ Agent A execution failed: 500
```

**Fix:**
1. Check backend logs
2. Verify customer data exists
3. Check clustering dependencies installed
4. Manually execute: POST to `/api/banking/agent_a/execute`

---

### Scenario 5: Backend not running ❌
**Status:** Can't connect to API

**Error:**
```
❌ Backend is NOT running on port 8002
```

**Fix:**
```bash
RESTART_ACADEMY_MATCH.bat
```

---

## Manual Testing Checklist

After automated tests pass, manually verify in browser:

### Banking Agent B Page
- [ ] Navigate to "Banking → Agent B"
- [ ] Switch to "Customer Level" mode
- [ ] Customer dropdown is populated
- [ ] Select a customer
- [ ] Click "Get Customer Recommendations"
- [ ] **Verify TWO sections appear:**
  - [ ] 🎯 "Tailored For You" (blue cards)
  - [ ] 👥 "Popular in Your Segment" (purple cards)
- [ ] Each section has 3+ products
- [ ] Each product shows:
  - [ ] Product name
  - [ ] Category
  - [ ] Score (percentage)
  - [ ] Reasoning
- [ ] Click "Get AI Explanation" on first product
- [ ] AI explanation loads (2-3 sentences)
- [ ] Explanation is relevant and personalized

### Banking Agent A Page (Prerequisite)
- [ ] Navigate to "Banking → Agent A"
- [ ] Click "Execute Agent A"
- [ ] Personas are created (5 cards)
- [ ] Each persona has:
  - [ ] Name (e.g., "Traditional Members")
  - [ ] Customer count
  - [ ] Avg balance
  - [ ] Digital adoption %
- [ ] Macro dashboard loads
- [ ] Micro segments visible

---

## Common Issues & Solutions

### Issue: "No customers found"
**Solution:** Execute Agent A first (test does this automatically now)

### Issue: "score_breakdown missing"
**Solution:** Check `Banking12FactorScorer` initialization in Agent B

### Issue: "Empty tailored_recommendations"
**Solution:** Try different customer, or check product eligibility criteria

### Issue: "AI explanation fails"
**Solution:** Verify `TOGETHER_API_KEY` in `.env` file

### Issue: "Structure mismatch"
**Solution:** Ensure using latest `agent_b_banking_enhanced_v2.py`

### Issue: "Backend errors"
**Solution:** 
1. Read backend terminal logs
2. Check import errors
3. Restart backend
4. Verify all dependencies installed

---

## Next Steps After Passing

1. **Browser Testing**
   - Test with multiple customers
   - Verify AI explanations quality
   - Check loading times

2. **Performance Testing**
   - Test with 10+ customers in sequence
   - Verify response times < 3 seconds
   - Check memory usage

3. **Data Quality**
   - Verify recommendations are relevant
   - Check score distributions
   - Validate eligibility checks work

4. **Documentation**
   - Update README
   - Create demo video
   - Document API changes

5. **Deployment**
   - Commit changes to git
   - Push to remote repository
   - Deploy to production environment
   - Monitor for errors

---

## Support

If tests fail and troubleshooting doesn't help:

1. **Check backend logs:** Look in terminal running uvicorn
2. **Review documentation:** See `AGENT_B_ACADEMY_SPORTS_MATCH.md`
3. **Verify files:** Ensure all new files are present:
   - `agents/agent_b_banking_enhanced_v2.py`
   - `agents/banking_12_factor_scorer.py`
   - `agents/agent_b_banking_persona_aligned.py`
4. **Test Academy Sports:** Verify Academy Agent B works (as reference)
5. **Compare responses:** Use comparison test to see differences
