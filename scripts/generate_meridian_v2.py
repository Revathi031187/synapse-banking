"""
Meridian Bank Dataset Generator v2
Generates 5,000 customers across 5 distinct archetypes designed for K-Prototypes segmentation.

Archetypes (counts):
  Wealth Builder    ~950   high income/credit/deposits, mid digital, low churn
  Digital Native    ~850   young, very high digital, low deposits
  Everyday Essential ~1500 mid income/credit, moderate everything
  Retiree Anchor    ~900   elderly, high deposits, very low digital, low churn
  At-Risk Borrower  ~800   low credit (<640), low deposits, high churn

Key separation for K-Prototypes:
  credit_score  : At-Risk 478-640 vs others 580+  (strong)
  age           : Digital Native 21-38 vs Retiree 62-84  (no overlap)
  total_deposits: At-Risk $200-5.5K vs Retiree $32K-132K  (strong)
  digital_eng   : Digital Native 0.78-0.99 vs Retiree 0.07-0.48  (no overlap)
  income        : Wealth Builder $95K-235K vs all others max $82K  (strong)
"""

import random
import math
import csv
import os
from datetime import datetime, timedelta

random.seed(2025)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'preloaded', 'meridian_bank')
os.makedirs(DATA_DIR, exist_ok=True)

# ─── helpers ────────────────────────────────────────────────────────────────

def cnorm(mean, std, lo, hi, as_int=False):
    for _ in range(30):
        v = random.gauss(mean, std)
        if lo <= v <= hi:
            return int(round(v)) if as_int else round(v, 4)
    v = max(lo, min(hi, mean))
    return int(round(v)) if as_int else round(v, 4)

def wc(options, weights):
    r = random.random()
    cum = 0.0
    for o, w in zip(options, weights):
        cum += w
        if r < cum:
            return o
    return options[-1]

FIRST_NAMES = [
    "James","Sarah","Michael","Emma","Robert","Jennifer","David","Lisa","John","Ashley",
    "William","Patricia","Richard","Linda","Joseph","Barbara","Thomas","Margaret","Charles","Nancy",
    "Christopher","Karen","Daniel","Betty","Matthew","Helen","Anthony","Sandra","Mark","Donna",
    "Kevin","Carol","Steven","Ruth","Brian","Sharon","Timothy","Michelle","Ronald","Laura",
    "George","Kimberly","Kenneth","Dorothy","Joshua","Deborah","Raymond","Rachel","Edward","Amanda",
    "Ryan","Stephanie","Justin","Rebecca","Brandon","Sharon","Tyler","Melissa","Aaron","Christine",
    "Andrew","Jessica","Nathan","Jennifer","Eric","Amanda","Adam","Heather","Ian","Nicole",
]
LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Rodriguez","Martinez",
    "Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas","Taylor","Moore","Jackson","Martin",
    "Lee","Perez","Thompson","White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson",
    "Walker","Young","Allen","King","Wright","Scott","Torres","Nguyen","Hill","Flores",
    "Green","Adams","Nelson","Baker","Hall","Rivera","Campbell","Mitchell","Carter","Roberts",
    "Phillips","Evans","Turner","Torres","Parker","Collins","Edwards","Stewart","Morris","Rogers",
]
OCCUPATIONS_BY_ARCHETYPE = {
    "Wealth_Builder":    ["Financial Advisor","Attorney","Physician","Senior Manager","CEO","Director","Architect","Engineer"],
    "Digital_Native":    ["Software Engineer","Data Analyst","UX Designer","Marketing Specialist","Graphic Designer","Startup Founder"],
    "Everyday_Essential":["Teacher","Nurse","Sales Associate","Office Manager","Electrician","Accountant","Police Officer"],
    "Retiree_Anchor":    ["Retired Teacher","Retired Engineer","Retired Government Worker","Retired Business Owner","Retired Nurse"],
    "At_Risk_Borrower":  ["Retail Associate","Warehouse Worker","Food Service Worker","Delivery Driver","Freelancer","Gig Worker"],
}
LIFE_EVENTS = ["", "", "", "", "New baby", "Job change", "Home purchase", "Marriage", "Divorce", "Retirement", "Education"]

# ─── archetype configurations ───────────────────────────────────────────────

ARCHETYPES = [
    {
        "id": "Wealth_Builder", "count": 950,
        "customer_segment": "Personal", "customer_type": "High_Net_Worth",
        "income":                   (195000, 30000, 130000, 290000),
        "age":                      (48,      8,     35,     63),
        "credit_score":             (810,    22,    748,    850),
        "total_deposits":           (175000, 28000, 108000, 265000),
        "digital_engagement_score": (0.64,   0.13,  0.35,   0.88),
        "churn_probability":        (0.09,   0.03,  0.03,   0.18),
        "num_products":             (4.2,    0.9,   2.0,    7.0),
        "monthly_transaction_volume": (24,   6,     12,     42),
        "nps_score":                (74,    10,     48,     95),
        "overdraft_frequency":      (0.1,   0.3,   0.0,    2.0),
        "monthly_direct_deposit_amt":(13000, 2500,  7500,  22000),
        "outstanding_debt_total":   (55000, 22000,  0,   145000),
        "cross_sell_receptivity":   (0.66,  0.14,  0.32,   0.92),
        "fee_sensitivity_score":    (0.20,  0.07,  0.05,   0.38),
        "branch_visit_frequency":   (0.28,  0.10,  0.05,   0.52),
        "months_tenure":            (120,   48,    36,    240),
        # Categorical (K-Prototypes uses these)
        "risk_tolerance":    (["Conservative","Moderate","Aggressive"], [0.15, 0.45, 0.40]),
        "channel_preference":(["Digital","Hybrid","Branch"],            [0.50, 0.40, 0.10]),
        "home_ownership":    (["Own","Mortgage"],                       [0.65, 0.35]),
        "life_stage":        (["Pre-Retiree","Family"],                  [0.50, 0.50]),
        "geographic_region": (["Urban","Suburban"],                      [0.55, 0.45]),
        # Other categoricals
        "employment_type":       (["full_time_w2","self_employed"],              [0.60, 0.40]),
        "investment_risk_profile":(["moderate","aggressive"],                   [0.50, 0.50]),
        "balance_trend":         (["growing","stable"],                          [0.65, 0.35]),
        "financial_goal":        (["wealth_growth","retirement_planning","investment"],[0.45,0.35,0.20]),
        "preferred_rewards_type":(["travel","cashback","points"],                [0.50, 0.30, 0.20]),
        "preferred_loan_term":   (["long","medium"],                             [0.60, 0.40]),
        "primary_spending_category":(["travel","dining","luxury_goods"],         [0.40, 0.35, 0.25]),
        "preferred_communication_style":(["detailed_reports","email"],           [0.55, 0.45]),
        "travel_frequency":      (["international_frequent","domestic_frequent"],[0.60, 0.40]),
        "churn_risk_category": "Low",
    },
    {
        "id": "Digital_Native", "count": 850,
        "customer_segment": "Personal", "customer_type": "Digital_Native",
        "income":                   (82000,  15000, 52000, 122000),
        "age":                      (27,      5,    21,     38),
        "credit_score":             (700,    40,    598,    778),
        "total_deposits":           (42000,  10000, 18000,  70000),
        "digital_engagement_score": (0.92,   0.05,  0.78,   0.99),
        "churn_probability":        (0.30,   0.08,  0.15,   0.52),
        "num_products":             (2.5,    0.7,   1.0,    5.0),
        "monthly_transaction_volume": (30,   8,     14,     52),
        "nps_score":                (60,    15,     28,     88),
        "overdraft_frequency":      (0.8,   0.8,   0.0,    3.5),
        "monthly_direct_deposit_amt":(5800,  1200,  2800,   9500),
        "outstanding_debt_total":   (18000,  8000,  0,    48000),
        "cross_sell_receptivity":   (0.60,  0.14,  0.28,   0.88),
        "fee_sensitivity_score":    (0.58,  0.13,  0.28,   0.86),
        "branch_visit_frequency":   (0.12,  0.06,  0.02,   0.28),
        "months_tenure":            (32,    18,    8,      78),
        "risk_tolerance":    (["Conservative","Moderate","Aggressive"], [0.20, 0.45, 0.35]),
        "channel_preference":(["Digital","Hybrid"],                     [0.85, 0.15]),
        "home_ownership":    (["Rent","Mortgage"],                       [0.80, 0.20]),
        "life_stage":        (["Young Professional","Student"],          [0.65, 0.35]),
        "geographic_region": (["Urban","Suburban"],                      [0.70, 0.30]),
        "employment_type":       (["full_time_w2","part_time","freelance"],       [0.50, 0.25, 0.25]),
        "investment_risk_profile":(["moderate","aggressive"],                    [0.55, 0.45]),
        "balance_trend":         (["growing","stable","declining"],               [0.45, 0.35, 0.20]),
        "financial_goal":        (["home_purchase","savings_growth","debt_payoff"],[0.40, 0.35, 0.25]),
        "preferred_rewards_type":(["cash_back","points","travel"],                [0.50, 0.30, 0.20]),
        "preferred_loan_term":   (["short","medium"],                             [0.60, 0.40]),
        "primary_spending_category":(["online_retail","dining","entertainment"],  [0.45, 0.30, 0.25]),
        "preferred_communication_style":(["brief_direct","push_notifications"],   [0.60, 0.40]),
        "travel_frequency":      (["domestic_occasional","domestic_frequent"],    [0.60, 0.40]),
        "churn_risk_category": "Medium",
    },
    {
        "id": "Everyday_Essential", "count": 1500,
        "customer_segment": "Personal", "customer_type": "Mass_Market",
        "income":                   (72000,  12000, 45000, 102000),
        "age":                      (41,      9,    26,     58),
        "credit_score":             (710,    35,   620,    780),
        "total_deposits":           (52000,  12000, 25000,  88000),
        "digital_engagement_score": (0.45,   0.12,  0.18,   0.70),
        "churn_probability":        (0.26,   0.07,  0.12,   0.44),
        "num_products":             (3.0,    0.8,   1.0,    5.0),
        "monthly_transaction_volume": (20,   5,      9,     36),
        "nps_score":                (54,    14,     25,     82),
        "overdraft_frequency":      (0.5,   0.7,   0.0,    2.8),
        "monthly_direct_deposit_amt":(5200,  1000,  2500,   8500),
        "outstanding_debt_total":   (28000, 12000,  0,    68000),
        "cross_sell_receptivity":   (0.52,  0.13,  0.22,   0.80),
        "fee_sensitivity_score":    (0.48,  0.13,  0.20,   0.78),
        "branch_visit_frequency":   (0.40,  0.14,  0.12,   0.68),
        "months_tenure":            (78,    36,    18,    188),
        "risk_tolerance":    (["Conservative","Moderate"],          [0.40, 0.60]),
        "channel_preference":(["Branch","Hybrid","Digital"],        [0.40, 0.35, 0.25]),
        "home_ownership":    (["Own","Mortgage","Rent"],             [0.30, 0.40, 0.30]),
        "life_stage":        (["Family","Young Professional"],       [0.55, 0.45]),
        "geographic_region": (["Suburban","Urban","Rural"],          [0.50, 0.30, 0.20]),
        "employment_type":       (["full_time_w2","part_time"],              [0.70, 0.30]),
        "investment_risk_profile":(["conservative","moderate"],              [0.55, 0.45]),
        "balance_trend":         (["stable","growing","declining"],           [0.50, 0.30, 0.20]),
        "financial_goal":        (["savings_growth","debt_payoff","home_purchase"],[0.40,0.35,0.25]),
        "preferred_rewards_type":(["cash_back","points"],                    [0.60, 0.40]),
        "preferred_loan_term":   (["medium","long"],                         [0.55, 0.45]),
        "primary_spending_category":(["groceries","gas","utilities"],        [0.45, 0.30, 0.25]),
        "preferred_communication_style":(["email","phone"],                  [0.55, 0.45]),
        "travel_frequency":      (["domestic_occasional","no_travel"],       [0.55, 0.45]),
        "churn_risk_category": "Medium",
    },
    {
        "id": "Retiree_Anchor", "count": 900,
        "customer_segment": "Personal", "customer_type": "Retiree",
        "income":                   (62000,  12000, 35000,  90000),
        "age":                      (70,      6,    62,     84),
        "credit_score":             (780,    25,   708,    840),
        "total_deposits":           (125000, 25000, 65000, 198000),
        "digital_engagement_score": (0.25,   0.09,  0.07,   0.48),
        "churn_probability":        (0.07,   0.03,  0.02,   0.16),
        "num_products":             (3.5,    0.7,   2.0,    5.0),
        "monthly_transaction_volume": (13,   4,      5,     24),
        "nps_score":                (70,    10,     44,     90),
        "overdraft_frequency":      (0.05,  0.2,   0.0,    1.0),
        "monthly_direct_deposit_amt":(4500,  1000,  2000,   7800),
        "outstanding_debt_total":   (9000,  6000,   0,    30000),
        "cross_sell_receptivity":   (0.46,  0.12,  0.18,   0.72),
        "fee_sensitivity_score":    (0.38,  0.11,  0.14,   0.62),
        "branch_visit_frequency":   (0.70,  0.14,  0.38,   0.96),
        "months_tenure":            (192,   60,    72,    368),
        "risk_tolerance":    (["Conservative","Moderate"],  [0.75, 0.25]),
        "channel_preference":(["Branch","Hybrid"],          [0.72, 0.28]),
        "home_ownership":    (["Own"],                      [1.00]),
        "life_stage":        (["Retiree"],                  [1.00]),
        "geographic_region": (["Suburban","Rural"],         [0.60, 0.40]),
        "employment_type":       (["retired"],                                      [1.00]),
        "investment_risk_profile":(["conservative"],                                [1.00]),
        "balance_trend":         (["stable","declining"],                            [0.65, 0.35]),
        "financial_goal":        (["retirement_planning","wealth_preservation","estate_planning"],[0.50,0.35,0.15]),
        "preferred_rewards_type":(["cash_back","travel"],                            [0.65, 0.35]),
        "preferred_loan_term":   (["long","medium"],                                 [0.55, 0.45]),
        "primary_spending_category":(["healthcare","groceries","utilities"],         [0.45, 0.35, 0.20]),
        "preferred_communication_style":(["phone","mail","detailed_reports"],        [0.45, 0.35, 0.20]),
        "travel_frequency":      (["domestic_occasional","no_travel"],               [0.55, 0.45]),
        "churn_risk_category": "Low",
    },
    {
        "id": "At_Risk_Borrower", "count": 800,
        "customer_segment": "Personal", "customer_type": "Mass_Market",
        "income":                   (35000,  7000,  18000,  52000),
        "age":                      (35,      8,    23,     52),
        "credit_score":             (568,    38,   478,    640),
        "total_deposits":           (10000,  4000,  2500,  18000),
        "digital_engagement_score": (0.52,   0.14,  0.22,   0.78),
        "churn_probability":        (0.58,   0.12,  0.35,   0.85),
        "num_products":             (1.8,    0.6,   1.0,    3.0),
        "monthly_transaction_volume": (15,   5,      6,     28),
        "nps_score":                (33,    12,     10,     58),
        "overdraft_frequency":      (4.0,   2.0,   1.0,    9.0),
        "monthly_direct_deposit_amt":(2400,  600,   800,   4200),
        "outstanding_debt_total":   (42000, 12000, 10000,  78000),
        "cross_sell_receptivity":   (0.38,  0.13,  0.10,   0.65),
        "fee_sensitivity_score":    (0.78,  0.12,  0.50,   0.98),
        "branch_visit_frequency":   (0.35,  0.15,  0.08,   0.65),
        "months_tenure":            (36,    24,    6,      98),
        "risk_tolerance":    (["Conservative","Moderate"],  [0.65, 0.35]),
        "channel_preference":(["Digital","Branch"],         [0.50, 0.50]),
        "home_ownership":    (["Rent","Mortgage"],           [0.65, 0.35]),
        "life_stage":        (["Young Professional","Family"],[0.50, 0.50]),
        "geographic_region": (["Urban","Suburban"],          [0.60, 0.40]),
        "employment_type":       (["full_time_w2","part_time","contract"],           [0.40, 0.35, 0.25]),
        "investment_risk_profile":(["conservative","moderate"],                      [0.70, 0.30]),
        "balance_trend":         (["declining","stable"],                             [0.60, 0.40]),
        "financial_goal":        (["debt_payoff","savings_growth","emergency_fund"],  [0.55, 0.30, 0.15]),
        "preferred_rewards_type":(["cash_back","points"],                             [0.70, 0.30]),
        "preferred_loan_term":   (["short","medium"],                                 [0.55, 0.45]),
        "primary_spending_category":(["groceries","utilities","fast_food"],           [0.45, 0.30, 0.25]),
        "preferred_communication_style":(["brief_direct","email"],                    [0.55, 0.45]),
        "travel_frequency":      (["no_travel","domestic_occasional"],                [0.65, 0.35]),
        "churn_risk_category": "High",
    },
]

# ─── derived field helpers ───────────────────────────────────────────────────

def credit_tier(score):
    if score >= 750: return "Excellent"
    if score >= 700: return "Good"
    if score >= 650: return "Fair"
    return "Poor"

def nps_category(score):
    if score >= 70: return "Promoter"
    if score >= 50: return "Passive"
    return "Detractor"

def churn_cat(p):
    if p < 0.15: return "Low"
    if p < 0.30: return "Medium"
    if p < 0.50: return "High"
    return "Critical"

def clv_tier(clv):
    if clv >= 15000: return "Platinum"
    if clv >= 6000:  return "Gold"
    if clv >= 2000:  return "Silver"
    return "Bronze"

def fee_sensitivity_tier(score):
    if score >= 0.7: return "high"
    if score >= 0.4: return "medium"
    return "low"

# ─── customer generator ───────────────────────────────────────────────────────

def generate_customer(arch, cust_id):
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    occupation = random.choice(OCCUPATIONS_BY_ARCHETYPE[arch["id"]])

    income          = cnorm(*arch["income"])
    age             = cnorm(*arch["age"], as_int=True)
    credit_score_v  = cnorm(*arch["credit_score"], as_int=True)
    total_deposits  = round(cnorm(*arch["total_deposits"]), 2)
    digital_eng     = cnorm(*arch["digital_engagement_score"])
    churn_prob      = cnorm(*arch["churn_probability"])
    num_products    = max(1, int(round(cnorm(*arch["num_products"]))))
    monthly_txn     = cnorm(*arch["monthly_transaction_volume"], as_int=True)
    nps             = cnorm(*arch["nps_score"], as_int=True)
    overdraft_freq  = cnorm(*arch["overdraft_frequency"])
    direct_deposit  = round(cnorm(*arch["monthly_direct_deposit_amt"]), 2)
    outstanding_debt= round(cnorm(*arch["outstanding_debt_total"]), 2)
    cross_sell      = cnorm(*arch["cross_sell_receptivity"])
    fee_sens        = cnorm(*arch["fee_sensitivity_score"])
    branch_visit    = cnorm(*arch["branch_visit_frequency"])
    months_tenure   = cnorm(*arch["months_tenure"], as_int=True)

    risk_tol    = wc(*arch["risk_tolerance"])
    channel_pref= wc(*arch["channel_preference"])
    home_own    = wc(*arch["home_ownership"])
    life_stg    = wc(*arch["life_stage"])
    geo_region  = wc(*arch["geographic_region"])
    emp_type    = wc(*arch["employment_type"])
    inv_risk    = wc(*arch["investment_risk_profile"])
    bal_trend   = wc(*arch["balance_trend"])
    fin_goal    = wc(*arch["financial_goal"])
    rewards_type= wc(*arch["preferred_rewards_type"])
    loan_term   = wc(*arch["preferred_loan_term"])
    spend_cat   = wc(*arch["primary_spending_category"])
    comm_style  = wc(*arch["preferred_communication_style"])
    travel_freq = wc(*arch["travel_frequency"])
    churn_risk_cat = arch["churn_risk_category"]

    # Derived / calculated fields
    churn_risk_score = round(churn_prob * 100, 2)
    credit_score_declining = 1 if (arch["id"] == "At_Risk_Borrower" and random.random() < 0.45) else 0
    high_overdraft = 1 if overdraft_freq >= 3 else 0
    low_balance_flag = 1 if total_deposits < 2000 else 0
    debt_payment_missed = 1 if arch["id"] == "At_Risk_Borrower" and random.random() < 0.40 else 0
    competitor_offer = 1 if random.random() < (churn_prob * 0.6) else 0
    has_direct_dep = direct_deposit > 0 and random.random() > 0.2

    # CLV calculation
    clv = (total_deposits * 0.025 * 3
           + outstanding_debt * 0.035 * 3
           + num_products * 60
           + (income / 12) * 0.015 * 3)
    clv = round(clv, 2)

    annual_txn_value = round(income * random.uniform(0.35, 0.75), 2)
    expected_years = round(max(1.0, (1 - churn_prob) * random.uniform(3, 15)), 1)
    csat_score = round(random.gauss(nps / 25.0, 0.4), 1)
    csat_score = max(1.0, min(5.0, csat_score))
    branch_satisfaction = round(random.gauss(3.5 if channel_pref == "Branch" else 3.0, 0.5), 1)
    branch_satisfaction = max(1.0, min(5.0, branch_satisfaction))

    # Transaction trend features
    recent_txn = int(monthly_txn * random.uniform(0.8, 1.2))
    prev_txn = int(monthly_txn * random.uniform(0.8, 1.2))
    if recent_txn > prev_txn * 1.1:  txn_trend = "Increasing"
    elif recent_txn < prev_txn * 0.9: txn_trend = "Decreasing"
    else: txn_trend = "Stable"

    deposit_chg = round(random.gauss(0.02 if bal_trend == "growing" else (-0.015 if bal_trend == "declining" else 0), 0.08), 4)
    products_closed = 1 if arch["id"] == "At_Risk_Borrower" and random.random() < 0.25 else 0
    complaints = int(round(max(0, random.gauss(
        2.5 if arch["id"] == "At_Risk_Borrower" else 0.3, 0.8))))
    support_contacts = int(round(max(0, random.gauss(
        3.0 if arch["id"] == "At_Risk_Borrower" else 0.5, 0.8))))
    digital_decline = 1 if arch["id"] == "At_Risk_Borrower" and random.random() < 0.30 else 0
    ext_accounts = int(round(max(0, random.gauss(
        2.5 if arch["id"] in ["Wealth_Builder","Digital_Native"] else 0.8, 0.8))))
    life_event = wc(LIFE_EVENTS, [0.6, 0, 0, 0, 0.08, 0.08, 0.08, 0.06, 0.04, 0.04, 0.02])
    age_risk = round(min(1.0, max(0.0, (age - 18) / 80.0)), 4)
    credit_trend = wc(["Improving","Stable","Declining"],
                      [0.15, 0.60, 0.25] if arch["id"] == "At_Risk_Borrower"
                      else [0.20, 0.65, 0.15])
    address_changes = int(round(max(0, random.gauss(
        0.2 if arch["id"] == "Retiree_Anchor" else 0.8, 0.5))))

    # Dates
    today = datetime(2026, 6, 23)
    join_date = today - timedelta(days=months_tenure * 30)
    last_txn_days = int(round(max(0, random.gauss(15, 10))))
    last_txn_date = today - timedelta(days=last_txn_days)

    home_ownership_type = {"Own": "owned", "Mortgage": "mortgage", "Rent": "renter"}.get(home_own, "renter")
    owns_home = home_own in ("Own", "Mortgage")

    monthly_spend_primary = round(income / 12 * random.uniform(0.08, 0.20), 2)

    return {
        "customer_id": f"CUST_{cust_id:05d}",
        "customer_name": name,
        "customer_segment": arch["customer_segment"],
        "customer_type": arch["customer_type"],
        "age": age,
        "income": round(income, 2),
        "credit_score": credit_score_v,
        "total_deposits": total_deposits,
        "num_products": num_products,
        "digital_engagement_score": digital_eng,
        "branch_visit_frequency": branch_visit,
        "months_since_relationship_started": months_tenure,
        "monthly_transaction_volume": monthly_txn,
        "cross_sell_receptivity": cross_sell,
        "last_transaction_date": last_txn_date.strftime("%Y-%m-%d"),
        "days_since_last_transaction": last_txn_days,
        "recent_txn_count": recent_txn,
        "previous_txn_count": prev_txn,
        "txn_frequency_trend": txn_trend,
        "balance_trend": bal_trend,
        "deposit_change_3mo_pct": deposit_chg,
        "low_balance_flag": low_balance_flag,
        "products_closed_last_6mo": products_closed,
        "complaints_last_year": complaints,
        "support_contacts_last_3mo": support_contacts,
        "digital_engagement_decline": digital_decline,
        "competitor_offer_received": competitor_offer,
        "fee_sensitivity_score": fee_sens,
        "external_accounts_linked": ext_accounts,
        "recent_life_event": life_event,
        "age_risk_factor": age_risk,
        "nps_score": nps,
        "nps_category": nps_category(nps),
        "csat_score": csat_score,
        "branch_satisfaction": branch_satisfaction,
        "credit_score_declining": credit_score_declining,
        "overdrafts_last_3mo": int(overdraft_freq),
        "overdraft_frequency": round(overdraft_freq, 2),   # added — used by Agent A
        "high_overdraft_flag": high_overdraft,
        "debt_payment_missed": debt_payment_missed,
        "churn_risk_score": churn_risk_score,
        "churn_risk_category": churn_risk_cat,
        "churn_probability": churn_prob,
        "churned": 0,
        "churn_date": "",
        "recommended_retention_action": "",
        "suggested_retention_offer": "",
        "annual_transaction_value": annual_txn_value,
        "expected_relationship_years": expected_years,
        "customer_lifetime_value": clv,
        "clv_tier": clv_tier(clv),
        "credit_tier": credit_tier(credit_score_v),
        "fee_sensitivity_tier": fee_sensitivity_tier(fee_sens),
        "preferred_rewards_type": rewards_type,
        "has_direct_deposit": has_direct_dep,
        "monthly_direct_deposit_amt": direct_deposit if has_direct_dep else 0.0,
        "owns_home": owns_home,
        "investment_risk_profile": inv_risk,
        "preferred_loan_term": loan_term,
        "home_ownership_type": home_ownership_type,
        "outstanding_debt_total": outstanding_debt,
        "primary_spending_category": spend_cat,
        "monthly_spend_in_primary_cat": monthly_spend_primary,
        "financial_goal": fin_goal,
        "travel_frequency": travel_freq,
        "employment_type": emp_type,
        "has_competitor_credit_card": random.random() < 0.35,
        "life_stage": life_stg,
        "preferred_communication_style": comm_style,
        "credit_score_trend": credit_trend,
        "occupation": occupation,
        "address_changes_count": address_changes,
        # K-Prototypes categorical columns (added — Agent A uses these directly)
        "risk_tolerance": risk_tol,
        "channel_preference": channel_pref,
        "home_ownership": home_own,
        "geographic_region": geo_region,
    }

# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    customers = []
    cust_id = 1
    for arch in ARCHETYPES:
        for _ in range(arch["count"]):
            customers.append(generate_customer(arch, cust_id))
            cust_id += 1

    # Shuffle so archetypes are interleaved
    random.shuffle(customers)

    # Re-assign IDs in shuffled order
    for i, c in enumerate(customers, 1):
        c["customer_id"] = f"CUST_{i:05d}"

    out_path = os.path.join(DATA_DIR, "customers.csv")
    fieldnames = list(customers[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(customers)

    print(f"Written {len(customers)} customers to {out_path}")

    # Verification summary
    from collections import Counter
    arch_counts = Counter(c["customer_type"] for c in customers)
    print("\nCustomer type distribution:")
    for k, v in sorted(arch_counts.items()):
        print(f"  {k}: {v}")

    print("\nKey feature means by archetype (life_stage):")
    by_stage = {}
    for c in customers:
        ls = c["life_stage"]
        if ls not in by_stage:
            by_stage[ls] = []
        by_stage[ls].append(c)
    for ls, group in sorted(by_stage.items()):
        n = len(group)
        avg_inc = sum(float(c["income"]) for c in group) / n
        avg_dep = sum(float(c["total_deposits"]) for c in group) / n
        avg_credit = sum(float(c["credit_score"]) for c in group) / n
        avg_digital = sum(float(c["digital_engagement_score"]) for c in group) / n
        avg_age = sum(float(c["age"]) for c in group) / n
        print(f"  {ls:22s} n={n:4d}  income=${avg_inc:8,.0f}  deposits=${avg_dep:8,.0f}  credit={avg_credit:.0f}  digital={avg_digital:.2f}  age={avg_age:.0f}")


if __name__ == "__main__":
    main()
