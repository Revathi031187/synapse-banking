# Glossary: Complex Terms in This Project

Plain-language definitions for **non-technical** and **technical** stakeholders. Use this for demos, documentation, and onboarding.

---

## APY (Annual Percentage Yield)

**What it is:** The **real** yearly rate of return on savings or investments, including compound interest.

**In plain English:**  
If a product shows **5.75% APY**, a $10,000 balance would earn about **$575 in interest per year** (before taxes). APY is the number we use to compare “how much I earn” across savings, CDs, and other interest-bearing products.

**In this project:**  
- Products have an `interest_rate` or `interest_rate_apy` field.  
- “Earning potential” and “X products @ Y% APY” use APY.  
- The 12-factor scorer uses APY to score **product value** (higher APY = better for savers when other factors are equal).

**Technical note:** APY = (1 + periodic rate)^periods − 1, so it’s comparable across different compounding frequencies.

---

## WI (Wealth Investors)

**What it is:** **WI** is an internal shorthand for the **Wealth Investors** persona.

**In plain English:**  
Wealth Investors are the persona for high-net-worth, deposit-heavy customers who are good candidates for **premium and fee-based** products (e.g. wealth management, private banking, premium credit cards). You might see “WI” in logs (e.g. “Scoring 9 banking products for WI…”).

**In this project:**  
- Persona ID **4** maps to **Wealth Investors**.  
- For this persona we apply a **premium boost** so products with an **annual fee** don’t always rank last.  
- Segment eligibility for WI uses higher credit/deposit thresholds (e.g. Premium/Platinum tier).

---

## Banking & Product Terms

| Term | Plain English | In This Project |
|------|----------------|------------------|
| **APY** | Yearly return % including compounding (e.g. 5.75% APY on $10K ≈ $575/year). | Used for interest-earning products; drives “Earning potential” and product value score. |
| **Annual fee** | Yearly fee for a product (e.g. $95/year for a credit card). | Products can have `annual_fee`. For Wealth Investors, fee products get a score boost so they compete for top slots. |
| **Minimum balance** | Minimum $ required to open or keep an account (e.g. $1,000 for a CD). | Stored as `min_balance`. “Easy access” counts how many recommended products have **no** minimum. |
| **Category (product)** | **Segment** of the product catalog: **Personal**, **Business**, or **Agricultural**. | Used to filter recommendations (e.g. “Agricultural Banking” → only Agricultural products). |
| **Subcategory** | Product **type** within a segment: e.g. Loan, Checking, Savings, Investment, Credit. | Used for labels and for subcategory-level filtering when the UI sends a type (e.g. “Loan”) that isn’t a segment name. |

---

## Segmentation & Personas

| Term | Plain English | In This Project |
|------|----------------|------------------|
| **Segment** | A group of customers (or products) with similar traits. | **Customer segment** = Personal / Business / Agricultural. **Product segment** = same three; we filter products by segment when the user picks “Agricultural” etc. |
| **Macro segment** | A **broad** segment (e.g. “Traditional Members”) from clustering on deposits, products, behavior. | Built by Agent A; has a name, definition, key behaviors, and marketing opportunities. |
| **Micro segment** | A **narrow** slice inside a macro segment (e.g. “Ultra-Premium Traditional Leaders (Platinum)” with 9 customers). | Built by micro-segmentation; used for very targeted campaigns and “top customers” views. |
| **Persona** | A **named profile** of a typical customer type (e.g. “Wealth Investors”, “Household Savers”). | Comes from clustering (Agent A); each has an ID, name, and eligibility rules. Used for segment-based recommendations when no specific customer is selected. |
| **Tier** | Service/value level: Entry, Bronze, Silver, Gold, Platinum, Premium, Ultra-Premium. | Derived from deposits + income; drives **eligibility** (min credit, max fee) and synthetic customer profiles for personas. |
| **Percentile** | “Xth percentile” = you’re above X% of others. 50th = median; 90th = top 10%. | Used in segment insights (e.g. “50th percentile in deposits”) to say where the segment sits vs. all customers. |

---

## Scoring & Recommendations

| Term | Plain English | In This Project |
|------|----------------|------------------|
| **Suitability score** | A single 0–100% number: “How well does this product fit this customer/segment?” | Same as **compatibility** and **match score**: the **Banking 12-Factor** total score, often shown as a percentage. |
| **Compatibility** | Same as suitability: how well the product matches the customer/segment. | `compatibility = score × 100`; shown as “64.8% compatibility” in the UI. |
| **Match quality** | Average (and sometimes top) suitability across the recommended set. | Shown in the “Match Quality” KPI (e.g. 64%, Top: 0%). |
| **12-Factor scoring** | A **rule-based** model that scores each product on 12 banking factors (eligibility, fees, rates, need fit, value, etc.); weights sum to 100%. | Implemented in `Banking12FactorScorer`; produces `total_score` and detailed breakdown (eligibility_score, product_value, etc.). |
| **Eligibility** | “Does this customer meet the product’s requirements?” (credit, income, balance). | One of the 12 factors (e.g. 22% weight). Shown as “Eligibility 93%: You strongly qualify…” in explanations. |
| **Hybrid (50% ML + 50% rules)** | Final score = **0.5 × ML probability** + **0.5 × rule score**. | ML = logistic regression P(purchase \| customer, product); rules = Banking 12-Factor. Combined for ranking. |
| **ML probability** | The model’s estimate of “probability this customer would take this product” (0–1). | From `LogitRecommendationModel.predict_purchase_probability()`; used as the ML half of the hybrid score. |

---

## Metrics & Behavior

| Term | Plain English | In This Project |
|------|----------------|------------------|
| **Digital engagement** | How much the customer uses app/online vs. branch (e.g. 72% digital). | Stored as `digital_engagement_score` or similar; used in segment definitions and persona profiles. |
| **Cross-sell receptivity** | Likelihood the customer will accept additional products (e.g. “62% cross-sell receptive”). | Used in segment insights and in the 12-factor **intent_score** (e.g. 3% weight). |
| **Velocity** | Speed or volume of activity (e.g. transaction velocity). | Can appear in micro-segment “Activity” (e.g. “500 velocity”) as a behavioral metric. |
| **Credit utilization** | Share of available credit that’s used (e.g. 30% = using $3K of a $10K line). | Sometimes shown in micro-segment “Activity”; lower can mean “room for more credit” or conservative use. |
| **ROI (Return on Investment)** | For a product: (benefit − cost) / cost, or similar. | In banking 12-factor, **product value** can include ROI-style logic (e.g. interest earned minus fees vs. balance). |
| **CLV (Customer Lifetime Value)** | Total expected profit from a customer over their relationship. | May appear in data or analytics; not always used in the recommendation engine itself. |
| **Churn** | When a customer leaves or stops being active. | Referenced in use cases (e.g. “Churn Prediction”); churn-related features may be used in segmentation or scoring. |

---

## Quick Reference: Acronyms

| Acronym | Meaning |
|--------|---------|
| **APY** | Annual Percentage Yield |
| **WI** | Wealth Investors (persona) |
| **ML** | Machine Learning |
| **ROI** | Return on Investment |
| **CLV** | Customer Lifetime Value |
| **CD** | Certificate of Deposit |
| **KPI** | Key Performance Indicator |

---

## One-Sentence Demo Cheat Sheet

- **APY:** “The yearly interest rate we use to show how much you earn on savings or CDs.”  
- **WI:** “Shorthand for Wealth Investors—our high-net-worth persona; we boost premium (fee) products for them.”  
- **Suitability / Compatibility:** “One number (0–100%) that says how well this product fits this customer.”  
- **12-Factor:** “Our rule-based score: eligibility, fees, rates, need fit, value, and other factors, combined into one score.”  
- **Hybrid:** “We combine 50% ML probability and 50% 12-factor rules to rank products.”  
- **Macro vs micro segment:** “Macro = broad group (e.g. Traditional Members); micro = smaller slice (e.g. 9 Platinum customers) for targeted campaigns.”

You can keep this file in the repo and point stakeholders to it for consistent definitions.
