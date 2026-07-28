# 🚀 Quick Start Guide - Agent B Banking V2

## Testing the Complete Implementation

Follow these steps to test the newly implemented Agent B Banking system.

---

## Prerequisites

1. Backend dependencies installed
2. Frontend dependencies installed
3. F&M Bank data present at `data/preloaded/fmb_bank/`
4. Together AI API key configured in `.env`

---

## Step 1: Run Unit Tests (Optional but Recommended)

```bash
# From project root
python tests/test_agent_b_banking.py
```

**Expected output:**
```
✅ Phase 1 PASSED: Banking 12-Factor Scorer
✅ Phase 2 PASSED: Persona-Aligned Recommender
✅ Phase 3 PASSED: Together AI Integration
✅ Phase 4 PASSED: Enhanced V2 Agent
✅ Integration Test PASSED

OVERALL: 5/5 tests passed
🎉 ALL TESTS PASSED! Agent B Banking is ready for deployment.
```

---

## Step 2: Start Backend

```bash
# Terminal 1
python api/main_unified_chromadb.py
```

**Expected output:**
```
✅ Banking Agent A initialized
✅ Banking Agent B Enhanced V2 initialized (Agentic AI)
  - Persona-aligned recommendations: ✓
  - Banking 12-factor scoring: ✓
  - Together AI explanations: ✓
  - 3 personas loaded

INFO:     Uvicorn running on http://0.0.0.0:8002
```

---

## Step 3: Start Frontend

```bash
# Terminal 2
cd frontend
npm run dev
```

**Expected output:**
```
VITE ready in 500ms

➜  Local:   http://localhost:5173/
```

---

## Step 4: Test in Browser

### 4.1 Navigate to Application
Open browser: http://localhost:5173/

### 4.2 Execute Agent A First
1. Click "Banking" in navigation
2. Click "Agent A: Customer Segmentation"
3. Click "Execute Segmentation"
4. Wait for personas to be created (3-5 seconds)
5. Verify 3-4 personas are displayed

### 4.3 Execute Agent B
1. Click "Agent B: Product Recommendations"
2. Mode: Select "Customer Level"
3. Select a customer from dropdown
   - Example: `CUST_00001`
4. Scoring Method: Choose "Rule-Based" or "Hybrid (AI + Rules)"
5. Number of Recommendations: Set to 5
6. Click "Get Customer Recommendations"

### 4.4 Verify Recommendations
**Expected sections:**

**Tailored Recommendations:**
- 3-5 products displayed
- Each with score (0-100%)
- Rule-based reasoning shown
- 12-factor breakdown collapsible section
- "Get AI Explanation" button

**Segment Popular:**
- 3-5 products popular in customer's segment
- Adoption rates shown

### 4.5 Test AI Explanations
1. Click "💡 Get AI Explanation" on any product
2. Wait 2-3 seconds for Together AI to generate explanation
3. Verify:
   - Loading spinner appears
   - AI explanation appears in purple gradient box
   - Explanation is 2-3 sentences
   - Explanation is personalized and professional

**Example AI Explanation:**
> "The Premium Credit Card is an excellent match for you as a Young Professional. With your strong credit score of 750 and income of $85,000, you easily qualify for this card. This card will help you build your credit history while earning rewards on everyday purchases, perfectly aligned with your financial growth phase."

### 4.6 Test 12-Factor Breakdown
1. Click "🎯 How is this score calculated?" on any recommendation
2. Verify all 12 factors are displayed:
   - 1️⃣ Eligibility (credit, income, balance)
   - 2️⃣ Financial Need Match
   - 3️⃣ Relationship Depth
   - 4️⃣ Product Pairing
   - 5️⃣ Channel Fit
   - 6️⃣ Complexity Match
   - 7️⃣ Intent Score
   - 8️⃣ Segment Affinity
   - 9️⃣ Transaction Pattern
   - 🔟 Product Rating
   - 1️⃣1️⃣ Popularity
   - 1️⃣2️⃣ (Removed - now 11 factors)
3. Verify each factor shows:
   - Score percentage
   - Explanation text

---

## Step 5: Test Persona-Level Recommendations

1. Mode: Switch to "Persona Level"
2. Select a persona from dropdown
   - Example: "Traditional Members (500 customers)"
3. Click "Get Persona Recommendations"
4. Verify:
   - Recommendations are shown for a random customer in that persona
   - Products match persona characteristics
   - Explanations reference persona name

---

## Step 6: Test Different Recommendation Types (API Testing)

You can also test via API directly:

### Persona-Aligned (Primary):
```bash
curl -X POST http://localhost:8002/api/banking/agent_b/execute \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST_00001",
    "top_n": 5
  }'
```

### Get AI Explanation:
```bash
curl -X POST http://localhost:8002/api/banking/agent_b/explain \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST_00001",
    "product_id": "PROD_001"
  }'
```

---

## Expected Behavior Summary

### ✅ What Should Work:

1. **Banking-Specific Scoring:**
   - Eligibility checks (credit, income, balance)
   - Financial need matching (age, deposits, income)
   - Product pairing (complementary banking products)
   - NO retail factors (price_alignment, category_match, brand_loyalty)

2. **Persona-Aligned Recommendations:**
   - Products match persona characteristics
   - Eligibility thresholds based on persona averages
   - Category diversity in recommendations

3. **AI Explanations:**
   - Generated on-demand (not pre-computed)
   - Personalized to customer + product
   - Professional and customer-focused
   - 2-3 sentences

4. **12-Factor Breakdown:**
   - All 11 banking factors displayed
   - Each with score and explanation
   - Formula explanation at bottom

### ❌ What Should NOT Happen:

1. Retail factors like "price_alignment" or "brand_loyalty"
2. Pre-computed AI explanations (should be on-demand)
3. Recommendations for products customer already has
4. Recommendations customer doesn't qualify for (without warning)
5. Generic explanations not personalized to customer

---

## Troubleshooting

### Issue: Agent A not executed error
**Solution:** Execute Agent A first from the Agent A page

### Issue: No AI explanation generated
**Solution:** Check Together AI API key in `.env` file

### Issue: No recommendations returned
**Solution:** 
- Check data is loaded (`data/preloaded/fmb_bank/`)
- Verify Agent A created personas
- Check backend logs for errors

### Issue: 12-factor breakdown not showing
**Solution:** Click the "🎯 How is this score calculated?" button to expand

### Issue: Frontend not connecting to backend
**Solution:** 
- Verify backend is running on port 8002
- Check VITE_API_BASE_URL in frontend/.env

---

## Success Indicators

### Backend Logs:
```
✅ Banking Agent B Enhanced V2 initialized (Agentic AI)
  - Persona-aligned recommendations: ✓
  - Banking 12-factor scoring: ✓
  - Together AI explanations: ✓
  - 3 personas loaded
```

### Frontend UI:
- Purple gradient boxes for AI explanations
- Blue gradient boxes for rule-based reasoning
- Collapsible 12-factor breakdowns with color-coded factors
- Score displayed as percentage (0-100%)

### AI Explanation Quality:
- Mentions customer's specific financial situation
- References eligibility and qualifications
- Explains tangible benefit
- Professional but conversational tone
- No jargon or technical terms

---

## Performance Expectations

- **Agent A execution:** 3-5 seconds for 5000 customers
- **Agent B recommendations:** <2 seconds for 5 products
- **AI explanation generation:** 2-3 seconds per product
- **12-factor calculation:** <100ms per product

---

## Next Steps After Testing

1. ✅ Verify all tests pass
2. ✅ Test in browser with real data
3. ✅ Test AI explanation generation
4. ✅ Verify 12-factor breakdowns are accurate
5. ✅ Compare with old implementation (if available)
6. 🚀 Deploy to production (if all tests pass)

---

## Questions or Issues?

Refer to:
- Implementation summary: `AGENT_B_BANKING_COMPLETE_IMPLEMENTATION.md`
- Test file: `tests/test_agent_b_banking.py`
- Plan: `.cursor/plans/agent_b_banking_-_complete_agentic_ai_rebuild_54702ff1.plan.md`

---

## 🎉 You're All Set!

If all steps above work correctly, your Agent B Banking V2 implementation is **production-ready**! 🚀
