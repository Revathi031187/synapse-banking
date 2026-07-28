"""
Generate Meridian Community Bank synthetic dataset from scratch.

Produces:
  data/preloaded/meridian_bank/customers.csv         (5,000 rows, 68 columns)
  data/preloaded/meridian_bank/products.csv          (28 products)
  data/preloaded/meridian_bank/transactions.csv      (60K-100K rows)
  data/preloaded/meridian_bank/wishlist.csv
  data/preloaded/meridian_bank/incomplete_applications.csv
  data/preloaded/meridian_bank/recommendation_impressions.csv
  data/config/product_offers.json                   (~80 offers)
"""

import os
import sys
import csv
import json
import random
import math
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "data", "preloaded", "meridian_bank")
CFG  = os.path.join(ROOT, "data", "config")
os.makedirs(DEST, exist_ok=True)
os.makedirs(CFG,  exist_ok=True)

random.seed(2024)
TODAY = datetime(2025, 6, 4)

# ── name pool ─────────────────────────────────────────────────────────────────

FIRST_NAMES = [
    "James","Mary","Robert","Patricia","John","Jennifer","Michael","Linda",
    "David","Barbara","William","Elizabeth","Richard","Susan","Joseph","Jessica",
    "Thomas","Sarah","Charles","Karen","Christopher","Lisa","Daniel","Nancy",
    "Matthew","Betty","Anthony","Margaret","Mark","Sandra","Donald","Ashley",
    "Steven","Dorothy","Paul","Kimberly","Andrew","Emily","Kenneth","Donna",
    "Joshua","Michelle","Kevin","Carol","Brian","Amanda","George","Melissa",
    "Edward","Deborah","Ronald","Stephanie","Timothy","Rebecca","Jason","Sharon",
    "Jeffrey","Laura","Ryan","Cynthia","Jacob","Kathleen","Gary","Amy",
    "Nicholas","Angela","Eric","Shirley","Jonathan","Anna","Stephen","Brenda",
    "Larry","Pamela","Justin","Emma","Scott","Nicole","Brandon","Helen",
    "Benjamin","Samantha","Samuel","Katherine","Raymond","Christine","Gregory","Debra",
    "Frank","Rachel","Alexander","Carolyn","Patrick","Janet","Jack","Catherine",
    "Dennis","Maria","Jerry","Heather","Tyler","Diane","Aaron","Julie",
    "Jose","Joyce","Adam","Victoria","Henry","Kelly","Nathan","Christina",
    "Douglas","Ruth","Zachary","Joan","Peter","Evelyn","Kyle","Lauren",
    "Walter","Alice","Harold","Judith","Jeremy","Anna","Keith","Rose",
    "Roger","Janice","Terry","Julia","Sean","Olivia","Gerald","Jacqueline",
    "Carl","Grace","Austin","Megan","Arthur","Denise","Lawrence","Amber",
    "Jesse","Marilyn","Dylan","Beverly","Bryan","Danielle","Joe","Theresa",
    "Jordan","Sophia","Billy","Martha","Bruce","Gloria","Albert","Emma",
    "Willie","Madison","Ethan","Hazel","Wayne","Ella","Lori","Jean",
]

LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
    "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson","Thomas",
    "Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson","White",
    "Harris","Sanchez","Clark","Ramirez","Lewis","Robinson","Walker","Young",
    "Allen","King","Wright","Scott","Torres","Nguyen","Hill","Flores",
    "Green","Adams","Nelson","Baker","Hall","Rivera","Campbell","Mitchell",
    "Carter","Roberts","Gomez","Phillips","Evans","Turner","Diaz","Parker",
    "Cruz","Edwards","Collins","Reyes","Stewart","Morris","Morales","Murphy",
    "Cook","Rogers","Gutierrez","Ortiz","Morgan","Cooper","Peterson","Bailey",
    "Reed","Kelly","Howard","Ramos","Kim","Cox","Ward","Richardson",
    "Watson","Brooks","Chavez","Wood","James","Bennett","Gray","Mendoza",
    "Ruiz","Hughes","Price","Alvarez","Castillo","Sanders","Patel","Myers",
    "Long","Ross","Foster","Jimenez","Powell","Jenkins","Perry","Russell",
    "Sullivan","Bell","Coleman","Butler","Henderson","Barnes","Gonzales","Fisher",
    "Vasquez","Simmons","Romero","Jordan","Patterson","Alexander","Hamilton","Graham",
    "Reynolds","Griffin","Wallace","Moreno","West","Cole","Hayes","Bryant",
    "Herrera","Gibson","Ellis","Tran","Medina","Aguilar","Stevens","Murray",
    "Ford","Castro","Marshall","Owens","Harrison","Fernandez","McDonald","Woods",
    "Washington","Kennedy","Wells","Vargas","Henry","Chen","Freeman","Webb",
    "Tucker","Guzman","Burns","Crawford","Olson","Simpson","Porter","Hunter",
]

STATES = ["AL","AR","FL","GA","IL","IN","KY","MI","MN","MS","MO","OH","TN","WI","NC","SC","VA","WV","IA","KS"]

# ── helpers ───────────────────────────────────────────────────────────────────

def rnd_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def weighted_choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]

def fmt_date(d):
    return d.strftime("%Y-%m-%d")

def rand_date(start_days_ago, end_days_ago=0):
    days = random.randint(end_days_ago, start_days_ago)
    return TODAY - timedelta(days=days)

# ── products definition ───────────────────────────────────────────────────────

PRODUCTS = [
    # ── PERSONAL CHECKING ────────────────────────────────────────────────────
    {
        "product_id":"MRD_P001","product_name":"Meridian Essential Checking",
        "category":"Personal","subcategory":"Checking",
        "annual_fee":0,"monthly_fee":0,"min_balance":0,"interest_rate":0.0,
        "description":"No-fee everyday checking with free mobile deposit, Bill Pay, and Zelle. No minimum balance required.",
        "target_segment":"Personal","customer_types":"Mass_Market,Young_Professional,Digital_Native",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"none","credit_tier_required":"any",
        "rate_tier_excellent":0.0,"rate_tier_good":0.0,"rate_tier_fair":0.0,
        "aum_fee_pct":0.0,"avg_rating":4.4,"min_credit_score":0,"min_income":0,
        "complexity_score":1,"digital_required":0,
    },
    {
        "product_id":"MRD_P002","product_name":"Meridian Plus Checking",
        "category":"Personal","subcategory":"Checking",
        "annual_fee":0,"monthly_fee":12,"min_balance":0,"interest_rate":0.0005,
        "description":"Full-featured checking with 0.05% APY on your balance. Monthly fee waived with $500+ direct deposit.",
        "target_segment":"Personal","customer_types":"Mass_Market,Young_Professional",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"direct_deposit_500","credit_tier_required":"any",
        "rate_tier_excellent":0.0,"rate_tier_good":0.0,"rate_tier_fair":0.0,
        "aum_fee_pct":0.0,"avg_rating":4.2,"min_credit_score":0,"min_income":20000,
        "complexity_score":1,"digital_required":0,
    },
    {
        "product_id":"MRD_P003","product_name":"Meridian Prestige Checking",
        "category":"Personal","subcategory":"Checking",
        "annual_fee":0,"monthly_fee":25,"min_balance":2500,"interest_rate":0.001,
        "description":"Premium checking with 0.10% APY, unlimited ATM fee rebates, and a dedicated relationship banker. Waived with $2,500 daily balance.",
        "target_segment":"Personal","customer_types":"High_Net_Worth,Young_Professional",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"balance_2500","credit_tier_required":"any",
        "rate_tier_excellent":0.0,"rate_tier_good":0.0,"rate_tier_fair":0.0,
        "aum_fee_pct":0.0,"avg_rating":4.5,"min_credit_score":0,"min_income":50000,
        "complexity_score":2,"digital_required":0,
    },
    # ── PERSONAL SAVINGS ──────────────────────────────────────────────────────
    {
        "product_id":"MRD_P004","product_name":"Meridian Basic Savings",
        "category":"Personal","subcategory":"Savings",
        "annual_fee":0,"monthly_fee":0,"min_balance":0,"interest_rate":0.008,
        "description":"Simple savings account with 0.80% APY. No monthly fee, no minimum balance. FDIC insured.",
        "target_segment":"Personal","customer_types":"Mass_Market,Young_Professional,Retiree",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"none","credit_tier_required":"any",
        "rate_tier_excellent":0.0,"rate_tier_good":0.0,"rate_tier_fair":0.0,
        "aum_fee_pct":0.0,"avg_rating":4.1,"min_credit_score":0,"min_income":0,
        "complexity_score":1,"digital_required":0,
    },
    {
        "product_id":"MRD_P005","product_name":"Meridian High-Yield Savings",
        "category":"Personal","subcategory":"Savings",
        "annual_fee":0,"monthly_fee":0,"min_balance":1000,"interest_rate":0.045,
        "description":"Earn 4.50% APY on every dollar above $1,000. No monthly fee. Automatic transfers from checking available.",
        "target_segment":"Personal","customer_types":"Mass_Market,Young_Professional,High_Net_Worth",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"none","credit_tier_required":"any",
        "rate_tier_excellent":0.0,"rate_tier_good":0.0,"rate_tier_fair":0.0,
        "aum_fee_pct":0.0,"avg_rating":4.6,"min_credit_score":0,"min_income":0,
        "complexity_score":1,"digital_required":0,
    },
    {
        "product_id":"MRD_P006","product_name":"Meridian Money Market",
        "category":"Personal","subcategory":"Savings",
        "annual_fee":0,"monthly_fee":0,"min_balance":5000,"interest_rate":0.0475,
        "description":"4.75% APY money market account with check-writing privileges. Tiered rates reward higher balances. $5,000 minimum.",
        "target_segment":"Personal","customer_types":"High_Net_Worth,Mass_Market,Retiree",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"balance_5000","credit_tier_required":"any",
        "rate_tier_excellent":0.0,"rate_tier_good":0.0,"rate_tier_fair":0.0,
        "aum_fee_pct":0.0,"avg_rating":4.5,"min_credit_score":0,"min_income":0,
        "complexity_score":2,"digital_required":0,
    },
    # ── CDs ───────────────────────────────────────────────────────────────────
    {
        "product_id":"MRD_P007","product_name":"Meridian 12-Month CD",
        "category":"Personal","subcategory":"CD",
        "annual_fee":0,"monthly_fee":0,"min_balance":500,"interest_rate":0.05,
        "description":"Lock in 5.00% APY for 12 months. FDIC insured up to $250,000. Penalty for early withdrawal.",
        "target_segment":"Personal","customer_types":"Mass_Market,Retiree,High_Net_Worth",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"none","credit_tier_required":"any",
        "rate_tier_excellent":0.0,"rate_tier_good":0.0,"rate_tier_fair":0.0,
        "aum_fee_pct":0.0,"avg_rating":4.4,"min_credit_score":0,"min_income":0,
        "complexity_score":1,"digital_required":0,
    },
    {
        "product_id":"MRD_P008","product_name":"Meridian 24-Month CD",
        "category":"Personal","subcategory":"CD",
        "annual_fee":0,"monthly_fee":0,"min_balance":500,"interest_rate":0.0485,
        "description":"4.85% APY for a 24-month term. Great for medium-term goals. Early withdrawal penalty of 180 days interest.",
        "target_segment":"Personal","customer_types":"Mass_Market,Retiree,High_Net_Worth",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"none","credit_tier_required":"any",
        "rate_tier_excellent":0.0,"rate_tier_good":0.0,"rate_tier_fair":0.0,
        "aum_fee_pct":0.0,"avg_rating":4.3,"min_credit_score":0,"min_income":0,
        "complexity_score":1,"digital_required":0,
    },
    # ── CREDIT CARDS ─────────────────────────────────────────────────────────
    {
        "product_id":"MRD_P009","product_name":"Meridian Cash Back Card",
        "category":"Personal","subcategory":"Credit",
        "annual_fee":0,"monthly_fee":0,"min_balance":0,"interest_rate":0.0,
        "description":"Unlimited 1.5% cash back on every purchase. 3% on groceries and gas. No annual fee. No rotating categories.",
        "target_segment":"Personal","customer_types":"Mass_Market,Young_Professional,Digital_Native",
        "rewards_type":"cash_back","cash_back_pct":1.5,"intro_apr_months":15,"regular_apr_pct":20.99,
        "fee_waiver_condition":"none","credit_tier_required":"good",
        "rate_tier_excellent":19.99,"rate_tier_good":22.99,"rate_tier_fair":24.99,
        "aum_fee_pct":0.0,"avg_rating":4.6,"min_credit_score":670,"min_income":30000,
        "complexity_score":2,"digital_required":0,
    },
    {
        "product_id":"MRD_P010","product_name":"Meridian Rewards Visa",
        "category":"Personal","subcategory":"Credit",
        "annual_fee":95,"monthly_fee":0,"min_balance":0,"interest_rate":0.0,
        "description":"3x points on dining and travel, 2x on gas. 60,000 bonus points after $3,000 spend in first 3 months. $50 annual dining credit.",
        "target_segment":"Personal","customer_types":"Young_Professional,High_Net_Worth",
        "rewards_type":"travel_points","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":21.49,
        "fee_waiver_condition":"none","credit_tier_required":"good",
        "rate_tier_excellent":20.49,"rate_tier_good":21.49,"rate_tier_fair":0.0,
        "aum_fee_pct":0.0,"avg_rating":4.7,"min_credit_score":700,"min_income":50000,
        "complexity_score":3,"digital_required":1,
    },
    {
        "product_id":"MRD_P011","product_name":"Meridian Platinum Card",
        "category":"Personal","subcategory":"Credit",
        "annual_fee":195,"monthly_fee":0,"min_balance":0,"interest_rate":0.0,
        "description":"4x points on travel booked through Meridian. Priority Pass airport lounge access. $200 annual travel credit. Concierge service.",
        "target_segment":"Personal","customer_types":"High_Net_Worth",
        "rewards_type":"travel_points","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":22.49,
        "fee_waiver_condition":"none","credit_tier_required":"excellent",
        "rate_tier_excellent":21.49,"rate_tier_good":0.0,"rate_tier_fair":0.0,
        "aum_fee_pct":0.0,"avg_rating":4.8,"min_credit_score":740,"min_income":75000,
        "complexity_score":4,"digital_required":1,
    },
    {
        "product_id":"MRD_P012","product_name":"Meridian Secured Card",
        "category":"Personal","subcategory":"Credit",
        "annual_fee":35,"monthly_fee":0,"min_balance":300,"interest_rate":0.0,
        "description":"Build or rebuild your credit with a secured card. $300–$3,000 credit limit. Reports to all three major bureaus monthly.",
        "target_segment":"Personal","customer_types":"Mass_Market,Young_Professional",
        "rewards_type":"cash_back","cash_back_pct":1.0,"intro_apr_months":0,"regular_apr_pct":24.99,
        "fee_waiver_condition":"none","credit_tier_required":"any",
        "rate_tier_excellent":0.0,"rate_tier_good":0.0,"rate_tier_fair":24.99,
        "aum_fee_pct":0.0,"avg_rating":4.2,"min_credit_score":300,"min_income":12000,
        "complexity_score":1,"digital_required":0,
    },
    # ── LOANS ─────────────────────────────────────────────────────────────────
    {
        "product_id":"MRD_P013","product_name":"Meridian Auto Loan",
        "category":"Personal","subcategory":"Auto",
        "annual_fee":0,"monthly_fee":0,"min_balance":0,"interest_rate":0.0649,
        "description":"Finance your new or used vehicle at competitive rates. Terms from 36 to 84 months. Rate discount with auto-pay.",
        "target_segment":"Personal","customer_types":"Mass_Market,Young_Professional,High_Net_Worth",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"none","credit_tier_required":"fair",
        "rate_tier_excellent":6.49,"rate_tier_good":9.99,"rate_tier_fair":14.99,
        "aum_fee_pct":0.0,"avg_rating":4.3,"min_credit_score":580,"min_income":25000,
        "complexity_score":2,"digital_required":0,
    },
    {
        "product_id":"MRD_P014","product_name":"Meridian Personal Loan",
        "category":"Personal","subcategory":"Personal Loan",
        "annual_fee":0,"monthly_fee":0,"min_balance":0,"interest_rate":0.0899,
        "description":"Unsecured personal loan from $5,000 to $50,000. Fixed rate, fixed term. Fund debt consolidation, home improvement, or major purchases.",
        "target_segment":"Personal","customer_types":"Mass_Market,Young_Professional",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"none","credit_tier_required":"fair",
        "rate_tier_excellent":8.99,"rate_tier_good":13.99,"rate_tier_fair":19.99,
        "aum_fee_pct":0.0,"avg_rating":4.2,"min_credit_score":620,"min_income":30000,
        "complexity_score":2,"digital_required":0,
    },
    {
        "product_id":"MRD_P015","product_name":"Meridian Home Equity Loan",
        "category":"Personal","subcategory":"Home Equity",
        "annual_fee":0,"monthly_fee":0,"min_balance":0,"interest_rate":0.0725,
        "description":"Fixed-rate home equity loan from $25,000 to $250,000. Up to 85% LTV. 10 to 20-year terms. Tax-deductible interest may apply.",
        "target_segment":"Personal","customer_types":"Mass_Market,High_Net_Worth",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"none","credit_tier_required":"good",
        "rate_tier_excellent":7.25,"rate_tier_good":8.25,"rate_tier_fair":9.50,
        "aum_fee_pct":0.0,"avg_rating":4.4,"min_credit_score":660,"min_income":45000,
        "complexity_score":3,"digital_required":0,
    },
    {
        "product_id":"MRD_P016","product_name":"Meridian HELOC",
        "category":"Personal","subcategory":"HELOC",
        "annual_fee":50,"monthly_fee":0,"min_balance":0,"interest_rate":0.0850,
        "description":"Variable-rate line of credit secured by your home. Draw period 10 years, repayment 20 years. Interest-only payments during draw.",
        "target_segment":"Personal","customer_types":"Mass_Market,High_Net_Worth",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"none","credit_tier_required":"good",
        "rate_tier_excellent":8.25,"rate_tier_good":9.00,"rate_tier_fair":10.25,
        "aum_fee_pct":0.0,"avg_rating":4.3,"min_credit_score":660,"min_income":45000,
        "complexity_score":3,"digital_required":0,
    },
    {
        "product_id":"MRD_P017","product_name":"Meridian 30yr Fixed Mortgage",
        "category":"Personal","subcategory":"Mortgage",
        "annual_fee":0,"monthly_fee":0,"min_balance":0,"interest_rate":0.0675,
        "description":"30-year fixed mortgage with competitive rates. Conventional loans up to $766,550. 20% down avoids PMI. Online application, local servicing.",
        "target_segment":"Personal","customer_types":"Mass_Market,Young_Professional,High_Net_Worth",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"none","credit_tier_required":"good",
        "rate_tier_excellent":6.75,"rate_tier_good":7.00,"rate_tier_fair":7.25,
        "aum_fee_pct":0.0,"avg_rating":4.5,"min_credit_score":640,"min_income":40000,
        "complexity_score":4,"digital_required":0,
    },
    {
        "product_id":"MRD_P018","product_name":"Meridian FHA Mortgage",
        "category":"Personal","subcategory":"Mortgage",
        "annual_fee":0,"monthly_fee":0,"min_balance":0,"interest_rate":0.065,
        "description":"FHA loan with as little as 3.5% down. Credit scores as low as 580 accepted. Ideal for first-time homebuyers.",
        "target_segment":"Personal","customer_types":"Mass_Market,Young_Professional",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"none","credit_tier_required":"fair",
        "rate_tier_excellent":6.50,"rate_tier_good":6.75,"rate_tier_fair":7.00,
        "aum_fee_pct":0.0,"avg_rating":4.4,"min_credit_score":580,"min_income":30000,
        "complexity_score":3,"digital_required":0,
    },
    # ── INVESTMENTS ───────────────────────────────────────────────────────────
    {
        "product_id":"MRD_P019","product_name":"Meridian Traditional IRA",
        "category":"Personal","subcategory":"Investment",
        "annual_fee":25,"monthly_fee":0,"min_balance":0,"interest_rate":0.0,
        "description":"Tax-deferred retirement savings. Contribute up to $7,000/year ($8,000 if 50+). Access to mutual funds, ETFs, and bonds.",
        "target_segment":"Personal","customer_types":"Mass_Market,Young_Professional,High_Net_Worth",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"balance_5000","credit_tier_required":"any",
        "rate_tier_excellent":0.0,"rate_tier_good":0.0,"rate_tier_fair":0.0,
        "aum_fee_pct":0.0025,"avg_rating":4.5,"min_credit_score":0,"min_income":0,
        "complexity_score":3,"digital_required":0,
    },
    {
        "product_id":"MRD_P020","product_name":"Meridian Roth IRA",
        "category":"Personal","subcategory":"Investment",
        "annual_fee":25,"monthly_fee":0,"min_balance":0,"interest_rate":0.0,
        "description":"Tax-free growth and withdrawals in retirement. Contribute after-tax dollars up to $7,000/year. No required minimum distributions.",
        "target_segment":"Personal","customer_types":"Young_Professional,Mass_Market,High_Net_Worth",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"balance_5000","credit_tier_required":"any",
        "rate_tier_excellent":0.0,"rate_tier_good":0.0,"rate_tier_fair":0.0,
        "aum_fee_pct":0.0025,"avg_rating":4.6,"min_credit_score":0,"min_income":0,
        "complexity_score":3,"digital_required":1,
    },
    # ── BUSINESS ──────────────────────────────────────────────────────────────
    {
        "product_id":"MRD_B001","product_name":"Meridian Business Essential Checking",
        "category":"Business","subcategory":"Checking",
        "annual_fee":0,"monthly_fee":15,"min_balance":0,"interest_rate":0.0,
        "description":"Business checking with 200 free transactions/month. ACH, wire, and online bill pay included. Waived with $1,500 average balance.",
        "target_segment":"Business","customer_types":"Small_Business",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"balance_1500","credit_tier_required":"any",
        "rate_tier_excellent":0.0,"rate_tier_good":0.0,"rate_tier_fair":0.0,
        "aum_fee_pct":0.0,"avg_rating":4.2,"min_credit_score":0,"min_income":0,
        "complexity_score":2,"digital_required":0,
    },
    {
        "product_id":"MRD_B002","product_name":"Meridian Business Plus Checking",
        "category":"Business","subcategory":"Checking",
        "annual_fee":0,"monthly_fee":30,"min_balance":0,"interest_rate":0.0002,
        "description":"Unlimited transactions, 0.02% APY on balances, dedicated business banker, and cash management tools.",
        "target_segment":"Business","customer_types":"Small_Business,Commercial_Real_Estate",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"balance_5000","credit_tier_required":"any",
        "rate_tier_excellent":0.0,"rate_tier_good":0.0,"rate_tier_fair":0.0,
        "aum_fee_pct":0.0,"avg_rating":4.3,"min_credit_score":0,"min_income":0,
        "complexity_score":3,"digital_required":0,
    },
    {
        "product_id":"MRD_B003","product_name":"Meridian Business Savings",
        "category":"Business","subcategory":"Savings",
        "annual_fee":0,"monthly_fee":0,"min_balance":500,"interest_rate":0.035,
        "description":"3.50% APY business savings. Separate your operating and reserve funds. Up to 6 withdrawals per month.",
        "target_segment":"Business","customer_types":"Small_Business,Commercial_Real_Estate",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"none","credit_tier_required":"any",
        "rate_tier_excellent":0.0,"rate_tier_good":0.0,"rate_tier_fair":0.0,
        "aum_fee_pct":0.0,"avg_rating":4.3,"min_credit_score":0,"min_income":0,
        "complexity_score":2,"digital_required":0,
    },
    {
        "product_id":"MRD_B004","product_name":"Meridian Business Line of Credit",
        "category":"Business","subcategory":"Business Loan",
        "annual_fee":150,"monthly_fee":0,"min_balance":0,"interest_rate":0.0799,
        "description":"Revolving line of credit $25K–$500K. Draw as needed, pay interest only on what you use. Annual review.",
        "target_segment":"Business","customer_types":"Small_Business,Commercial_Real_Estate",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"none","credit_tier_required":"good",
        "rate_tier_excellent":7.99,"rate_tier_good":10.99,"rate_tier_fair":14.99,
        "aum_fee_pct":0.0,"avg_rating":4.4,"min_credit_score":660,"min_income":75000,
        "complexity_score":4,"digital_required":0,
    },
    {
        "product_id":"MRD_B005","product_name":"Meridian Business Rewards Card",
        "category":"Business","subcategory":"Credit",
        "annual_fee":95,"monthly_fee":0,"min_balance":0,"interest_rate":0.0,
        "description":"3x points on business travel and software subscriptions, 2x on office supplies and dining. $500 welcome bonus after $3,000 spend.",
        "target_segment":"Business","customer_types":"Small_Business,Commercial_Real_Estate",
        "rewards_type":"travel_points","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":21.99,
        "fee_waiver_condition":"none","credit_tier_required":"good",
        "rate_tier_excellent":20.99,"rate_tier_good":21.99,"rate_tier_fair":0.0,
        "aum_fee_pct":0.0,"avg_rating":4.5,"min_credit_score":680,"min_income":50000,
        "complexity_score":3,"digital_required":1,
    },
    # ── AGRICULTURAL ──────────────────────────────────────────────────────────
    {
        "product_id":"MRD_A001","product_name":"Meridian Farm Operating Line",
        "category":"Agricultural","subcategory":"Agricultural Loan",
        "annual_fee":100,"monthly_fee":0,"min_balance":0,"interest_rate":0.0725,
        "description":"Seasonal operating line of credit for crops, livestock, and equipment. $50K–$2M. Annual review with experienced agricultural lenders.",
        "target_segment":"Agricultural","customer_types":"Row_Crop_Farmer,Livestock_Rancher,Vineyard_Orchard_Owner",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"none","credit_tier_required":"fair",
        "rate_tier_excellent":7.25,"rate_tier_good":8.99,"rate_tier_fair":10.99,
        "aum_fee_pct":0.0,"avg_rating":4.4,"min_credit_score":600,"min_income":30000,
        "complexity_score":3,"digital_required":0,
    },
    {
        "product_id":"MRD_A002","product_name":"Meridian Equipment Term Loan",
        "category":"Agricultural","subcategory":"Agricultural Loan",
        "annual_fee":0,"monthly_fee":0,"min_balance":0,"interest_rate":0.0699,
        "description":"Finance tractors, combines, irrigation systems, and farm equipment. Terms up to 7 years. Up to 100% financing on new equipment.",
        "target_segment":"Agricultural","customer_types":"Row_Crop_Farmer,Livestock_Rancher,Vineyard_Orchard_Owner",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"none","credit_tier_required":"fair",
        "rate_tier_excellent":6.99,"rate_tier_good":8.49,"rate_tier_fair":10.49,
        "aum_fee_pct":0.0,"avg_rating":4.5,"min_credit_score":580,"min_income":25000,
        "complexity_score":2,"digital_required":0,
    },
    {
        "product_id":"MRD_A003","product_name":"Meridian Land Improvement Loan",
        "category":"Agricultural","subcategory":"Agricultural Loan",
        "annual_fee":0,"monthly_fee":0,"min_balance":0,"interest_rate":0.0675,
        "description":"Fund drainage, irrigation, storage facilities, and soil improvements. Terms up to 15 years. Low rates for FSA-guaranteed borrowers.",
        "target_segment":"Agricultural","customer_types":"Row_Crop_Farmer,Livestock_Rancher,Vineyard_Orchard_Owner",
        "rewards_type":"none","cash_back_pct":0.0,"intro_apr_months":0,"regular_apr_pct":0.0,
        "fee_waiver_condition":"none","credit_tier_required":"fair",
        "rate_tier_excellent":6.75,"rate_tier_good":7.99,"rate_tier_fair":9.99,
        "aum_fee_pct":0.0,"avg_rating":4.4,"min_credit_score":580,"min_income":20000,
        "complexity_score":3,"digital_required":0,
    },
]

PRODUCT_FIELDS = [
    "product_id","product_name","category","subcategory",
    "annual_fee","monthly_fee","min_balance","interest_rate",
    "description","target_segment","customer_types",
    "rewards_type","cash_back_pct","intro_apr_months","regular_apr_pct",
    "fee_waiver_condition","credit_tier_required",
    "rate_tier_excellent","rate_tier_good","rate_tier_fair",
    "aum_fee_pct","avg_rating","min_credit_score","min_income",
    "complexity_score","digital_required",
]

# ── offer catalog ─────────────────────────────────────────────────────────────

OFFERS = [
    # ── MRD_P001 Essential Checking ──────────────────────────────────────────
    {
        "offer_id":"MRD_OFF_001","product_id":"MRD_P001",
        "offer_name":"Summer $300 Checking Bonus","offer_type":"signup_bonus",
        "is_evergreen":False,"offer_end_date":"2025-09-30",
        "headline_value":"Earn $300 cash bonus",
        "value_amount":300,"value_currency":"USD",
        "spend_requirement":1000,"spend_window_days":90,
        "qualifying_action":"direct_deposit_setup","min_direct_deposit_amt":500,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":True,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":None,"excluded_if_holds_subcategory":"Checking",
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":1,"base_offer_score":0.82,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"in_app",
        "content_hero_stat":"$300 cash bonus",
        "content_how_to_earn":"Open Meridian Essential Checking, set up $500+ direct deposit, and use your debit card for $1,000 in purchases within 90 days.",
        "content_benefit_1":"Zero monthly fees — ever","content_benefit_2":"Free Zelle and mobile deposit","content_benefit_3":"Instant mobile account opening",
        "scoring_weights":{"spending_pattern_boost":0.3,"life_stage_boost":0.2,"digital_boost":0.4,"fee_sensitivity_boost":0.6},
    },
    {
        "offer_id":"MRD_OFF_002","product_id":"MRD_P001",
        "offer_name":"Refer a Friend — Earn $75","offer_type":"referral_bonus",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"Earn $75 for every friend you refer",
        "value_amount":75,"value_currency":"USD",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"referral","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":True,
        "min_tenure_months":3,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":"Checking","excluded_if_holds_subcategory":None,
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":1,"base_offer_score":0.60,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":False,"channel_branch":True,
        "preferred_channel":"in_app",
        "content_hero_stat":"$75 per referral",
        "content_how_to_earn":"Share your unique referral link. When your friend opens an account and completes a direct deposit, you both earn $75.",
        "content_benefit_1":"No limit on referrals","content_benefit_2":"Paid within 10 business days","content_benefit_3":"Share via app or email",
        "scoring_weights":{"spending_pattern_boost":0.1,"life_stage_boost":0.1,"digital_boost":0.5,"fee_sensitivity_boost":0.4},
    },
    # ── MRD_P002 Plus Checking ────────────────────────────────────────────────
    {
        "offer_id":"MRD_OFF_003","product_id":"MRD_P002",
        "offer_name":"Fee Waiver for Life on Plus Checking","offer_type":"fee_waiver",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"Never pay a monthly fee",
        "value_amount":144,"value_currency":"USD",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"direct_deposit_setup","min_direct_deposit_amt":500,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":None,"excluded_if_holds_subcategory":None,
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":1,"base_offer_score":0.75,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":False,"channel_branch":True,
        "preferred_channel":"email",
        "content_hero_stat":"$0 monthly fee — permanently",
        "content_how_to_earn":"Set up a monthly direct deposit of $500 or more and your $12 monthly fee disappears for good.",
        "content_benefit_1":"Earn 0.05% APY on your balance","content_benefit_2":"Unlimited debit card use","content_benefit_3":"Free standard checks",
        "scoring_weights":{"spending_pattern_boost":0.2,"life_stage_boost":0.3,"digital_boost":0.3,"fee_sensitivity_boost":0.8},
    },
    {
        "offer_id":"MRD_OFF_004","product_id":"MRD_P002",
        "offer_name":"$200 Loyalty Upgrade Bonus","offer_type":"loyalty_reward",
        "is_evergreen":False,"offer_end_date":"2025-12-31",
        "headline_value":"$200 for upgrading from Essential to Plus",
        "value_amount":200,"value_currency":"USD",
        "spend_requirement":500,"spend_window_days":60,
        "qualifying_action":"account_upgrade","min_direct_deposit_amt":500,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":True,
        "min_tenure_months":6,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":"Checking","excluded_if_holds_subcategory":None,
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":1,"base_offer_score":0.70,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"in_app",
        "content_hero_stat":"$200 upgrade bonus",
        "content_how_to_earn":"Upgrade your Essential Checking to Plus, set up a $500 direct deposit, and spend $500 with your debit card in 60 days.",
        "content_benefit_1":"Earn interest on your balance","content_benefit_2":"Free standard checks","content_benefit_3":"Priority customer service",
        "scoring_weights":{"spending_pattern_boost":0.2,"life_stage_boost":0.4,"digital_boost":0.3,"fee_sensitivity_boost":0.5},
    },
    # ── MRD_P003 Prestige Checking ───────────────────────────────────────────
    {
        "offer_id":"MRD_OFF_005","product_id":"MRD_P003",
        "offer_name":"$500 Prestige Checking Bonus","offer_type":"signup_bonus",
        "is_evergreen":False,"offer_end_date":"2025-10-31",
        "headline_value":"Earn $500 welcome bonus",
        "value_amount":500,"value_currency":"USD",
        "spend_requirement":2000,"spend_window_days":90,
        "qualifying_action":"direct_deposit_setup","min_direct_deposit_amt":2500,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":True,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":None,"excluded_if_holds_subcategory":"Checking",
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":2,"base_offer_score":0.85,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"branch",
        "content_hero_stat":"$500 premium welcome",
        "content_how_to_earn":"Open Prestige Checking, set up a payroll direct deposit of $2,500+, and spend $2,000 within 90 days.",
        "content_benefit_1":"Unlimited ATM fee rebates worldwide","content_benefit_2":"Dedicated relationship banker","content_benefit_3":"Earn 0.10% APY on your balance",
        "scoring_weights":{"spending_pattern_boost":0.3,"life_stage_boost":0.5,"digital_boost":0.4,"fee_sensitivity_boost":0.3},
    },
    {
        "offer_id":"MRD_OFF_006","product_id":"MRD_P003",
        "offer_name":"Retention: Free Year of Prestige Checking","offer_type":"loyalty_reward",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"12 months free — no fee, no minimum",
        "value_amount":300,"value_currency":"USD",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"retention_acceptance","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":True,
        "min_tenure_months":12,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":"Checking","excluded_if_holds_subcategory":None,
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":True,
        "offer_complexity":1,"base_offer_score":0.90,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":False,"channel_branch":True,
        "preferred_channel":"in_app",
        "content_hero_stat":"12 months, zero fees",
        "content_how_to_earn":"As a valued Meridian customer, accept this offer to waive all Prestige Checking fees for the next 12 months — no strings attached.",
        "content_benefit_1":"Keep all your premium benefits","content_benefit_2":"$300 value over 12 months","content_benefit_3":"No minimum balance required",
        "scoring_weights":{"spending_pattern_boost":0.1,"life_stage_boost":0.3,"digital_boost":0.2,"fee_sensitivity_boost":0.9},
    },
    # ── MRD_P005 High-Yield Savings ───────────────────────────────────────────
    {
        "offer_id":"MRD_OFF_007","product_id":"MRD_P005",
        "offer_name":"5.00% APY Intro Rate — 6 Months","offer_type":"cd_rate_bump",
        "is_evergreen":False,"offer_end_date":"2025-09-30",
        "headline_value":"Earn 5.00% APY for your first 6 months",
        "value_amount":0.5,"value_currency":"pct_apr_reduction",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"open_account","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":5.00,"rate_duration_months":6,
        "new_customer_only":True,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":None,"excluded_if_holds_subcategory":"Savings",
        "min_deposits_required":1000,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":1,"base_offer_score":0.88,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"email",
        "content_hero_stat":"5.00% APY intro rate",
        "content_how_to_earn":"Open a new High-Yield Savings with $1,000 or more. Earn 5.00% APY for your first 6 months, then our standard 4.50% thereafter.",
        "content_benefit_1":"FDIC insured up to $250,000","content_benefit_2":"No monthly fees","content_benefit_3":"Transfer funds to checking instantly",
        "scoring_weights":{"spending_pattern_boost":0.1,"life_stage_boost":0.4,"digital_boost":0.3,"fee_sensitivity_boost":0.5},
    },
    {
        "offer_id":"MRD_OFF_008","product_id":"MRD_P005",
        "offer_name":"Relationship Rate Boost +0.25%","offer_type":"cd_rate_bump",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"Earn 4.75% APY as a checking customer",
        "value_amount":0.25,"value_currency":"pct_apr_reduction",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"open_account","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":4.75,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":"Checking","excluded_if_holds_subcategory":None,
        "min_deposits_required":1000,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":1,"base_offer_score":0.80,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":False,"channel_branch":True,
        "preferred_channel":"in_app",
        "content_hero_stat":"4.75% APY for Meridian checking customers",
        "content_how_to_earn":"Already banking with us? Your Meridian checking account unlocks a 0.25% rate boost on High-Yield Savings — automatically.",
        "content_benefit_1":"No action needed if you have checking","content_benefit_2":"Applies to your full balance","content_benefit_3":"Rate reviewed quarterly",
        "scoring_weights":{"spending_pattern_boost":0.1,"life_stage_boost":0.3,"digital_boost":0.2,"fee_sensitivity_boost":0.5},
    },
    # ── MRD_P007 12-Month CD ──────────────────────────────────────────────────
    {
        "offer_id":"MRD_OFF_009","product_id":"MRD_P007",
        "offer_name":"Relationship CD Rate Bump +0.15%","offer_type":"cd_rate_bump",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"Earn 5.15% APY — exclusive for checking customers",
        "value_amount":0.15,"value_currency":"pct_apr_reduction",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"open_account","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":5.15,"rate_duration_months":12,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":"Checking","excluded_if_holds_subcategory":None,
        "min_deposits_required":500,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":1,"base_offer_score":0.82,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"email",
        "content_hero_stat":"5.15% APY for checking customers",
        "content_how_to_earn":"Open a 12-Month CD with $500 or more. Your existing Meridian checking account automatically earns you an extra 0.15% APY.",
        "content_benefit_1":"Guaranteed 5.15% for full 12 months","content_benefit_2":"FDIC insured","content_benefit_3":"Automatic renewal option",
        "scoring_weights":{"spending_pattern_boost":0.05,"life_stage_boost":0.5,"digital_boost":0.2,"fee_sensitivity_boost":0.4},
    },
    {
        "offer_id":"MRD_OFF_010","product_id":"MRD_P007",
        "offer_name":"CD Ladder Starter — Open 2, Rate Unlock","offer_type":"cd_rate_bump",
        "is_evergreen":False,"offer_end_date":"2025-12-31",
        "headline_value":"Open 2 CDs and unlock 5.25% APY",
        "value_amount":0.25,"value_currency":"pct_apr_reduction",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"open_account","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":5.25,"rate_duration_months":12,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":None,"excluded_if_holds_subcategory":None,
        "min_deposits_required":2000,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":2,"base_offer_score":0.72,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"branch",
        "content_hero_stat":"5.25% APY when you ladder 2 CDs",
        "content_how_to_earn":"Open both a 12-Month and a 24-Month CD with at least $1,000 each. The combined deposit unlocks an extra 0.25% on the 12-Month CD.",
        "content_benefit_1":"Diversify your maturity dates","content_benefit_2":"Best guaranteed rate in our lineup","content_benefit_3":"Speak to a banker to set up your ladder",
        "scoring_weights":{"spending_pattern_boost":0.05,"life_stage_boost":0.6,"digital_boost":0.2,"fee_sensitivity_boost":0.3},
    },
    # ── MRD_P009 Cash Back Card ───────────────────────────────────────────────
    {
        "offer_id":"MRD_OFF_011","product_id":"MRD_P009",
        "offer_name":"$200 Welcome Bonus","offer_type":"signup_bonus",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"Earn $200 after first purchase",
        "value_amount":200,"value_currency":"USD",
        "spend_requirement":500,"spend_window_days":90,
        "qualifying_action":"first_purchase","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":670,
        "required_existing_products":None,"excluded_if_holds_subcategory":"Credit",
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":1,"base_offer_score":0.85,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"in_app",
        "content_hero_stat":"$200 cash back",
        "content_how_to_earn":"Apply for the Meridian Cash Back Card and spend just $500 within the first 90 days. That's about $170/month — groceries and gas alone can get you there.",
        "content_benefit_1":"3% cash back on groceries and gas","content_benefit_2":"1.5% on everything else","content_benefit_3":"No annual fee, ever",
        "scoring_weights":{"spending_pattern_boost":0.5,"life_stage_boost":0.3,"digital_boost":0.3,"fee_sensitivity_boost":0.7},
    },
    {
        "offer_id":"MRD_OFF_012","product_id":"MRD_P009",
        "offer_name":"0% Intro APR — 15 Months","offer_type":"intro_apr",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"0% APR for 15 months on purchases",
        "value_amount":15,"value_currency":"months",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"open_account","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":0.0,"rate_duration_months":15,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":670,
        "required_existing_products":None,"excluded_if_holds_subcategory":"Credit",
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":2,"base_offer_score":0.78,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":False,
        "preferred_channel":"email",
        "content_hero_stat":"0% APR for 15 months",
        "content_how_to_earn":"New cardholders enjoy 0% intro APR on all purchases for 15 months from account opening. Then a variable APR of 20.99%–24.99% applies.",
        "content_benefit_1":"Finance big purchases interest-free","content_benefit_2":"No balance transfer fee in first 60 days","content_benefit_3":"1.5% cash back even during intro period",
        "scoring_weights":{"spending_pattern_boost":0.2,"life_stage_boost":0.4,"digital_boost":0.2,"fee_sensitivity_boost":0.6},
    },
    {
        "offer_id":"MRD_OFF_013","product_id":"MRD_P009",
        "offer_name":"3% Grocery Cashback Boost — 6 Months","offer_type":"cashback_boost",
        "is_evergreen":False,"offer_end_date":"2025-08-31",
        "headline_value":"5% cash back on groceries for 6 months",
        "value_amount":5.0,"value_currency":"pct_cashback",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"first_purchase","min_direct_deposit_amt":None,
        "cashback_category":"groceries","cashback_pct":5.0,"rate_pct":None,"rate_duration_months":6,
        "new_customer_only":True,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":670,
        "required_existing_products":None,"excluded_if_holds_subcategory":"Credit",
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":1,"base_offer_score":0.80,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":False,"channel_branch":False,
        "preferred_channel":"in_app",
        "content_hero_stat":"5% on every grocery run for 6 months",
        "content_how_to_earn":"New Cash Back Card members automatically earn 5% on grocery purchases (up to $1,500 in spend) during your first 6 months.",
        "content_benefit_1":"$75 extra per month on $1,500 grocery spend","content_benefit_2":"Applies at supermarkets and warehouse clubs","content_benefit_3":"Then 3% indefinitely",
        "scoring_weights":{"spending_pattern_boost":0.9,"life_stage_boost":0.3,"digital_boost":0.3,"fee_sensitivity_boost":0.5},
    },
    # ── MRD_P010 Rewards Visa ─────────────────────────────────────────────────
    {
        "offer_id":"MRD_OFF_014","product_id":"MRD_P010",
        "offer_name":"60,000 Points Welcome Bonus","offer_type":"signup_bonus",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"Earn 60,000 points — worth $600 in travel",
        "value_amount":600,"value_currency":"USD",
        "spend_requirement":3000,"spend_window_days":90,
        "qualifying_action":"first_purchase","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":700,
        "required_existing_products":None,"excluded_if_holds_subcategory":"Credit",
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":2,"base_offer_score":0.88,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"in_app",
        "content_hero_stat":"60,000 points ($600 in travel)",
        "content_how_to_earn":"Spend $3,000 in purchases in your first 3 months and earn 60,000 bonus points — that's $600 toward flights, hotels, and rental cars.",
        "content_benefit_1":"3x points on dining and travel","content_benefit_2":"$50 annual dining credit","content_benefit_3":"Points never expire with active card",
        "scoring_weights":{"spending_pattern_boost":0.6,"life_stage_boost":0.4,"digital_boost":0.5,"fee_sensitivity_boost":0.2},
    },
    {
        "offer_id":"MRD_OFF_015","product_id":"MRD_P010",
        "offer_name":"5x Points on Dining — Limited Time","offer_type":"cashback_boost",
        "is_evergreen":False,"offer_end_date":"2025-09-30",
        "headline_value":"5x points on every restaurant visit",
        "value_amount":5.0,"value_currency":"pct_cashback",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"first_purchase","min_direct_deposit_amt":None,
        "cashback_category":"dining","cashback_pct":5.0,"rate_pct":None,"rate_duration_months":3,
        "new_customer_only":True,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":700,
        "required_existing_products":None,"excluded_if_holds_subcategory":"Credit",
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":2,"base_offer_score":0.82,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":False,"channel_branch":False,
        "preferred_channel":"in_app",
        "content_hero_stat":"5x points at restaurants for 3 months",
        "content_how_to_earn":"New Rewards Visa cardholders earn 5x points on dining purchases for their first 3 months (up to $2,000 spend). Perfect for food lovers.",
        "content_benefit_1":"$500 in dining = 2,500 points ($25 value)","content_benefit_2":"Applies to all restaurants and delivery apps","content_benefit_3":"Then 3x permanently",
        "scoring_weights":{"spending_pattern_boost":0.8,"life_stage_boost":0.3,"digital_boost":0.5,"fee_sensitivity_boost":0.2},
    },
    {
        "offer_id":"MRD_OFF_016","product_id":"MRD_P010",
        "offer_name":"Annual Fee Waived — Year 1","offer_type":"fee_waiver",
        "is_evergreen":False,"offer_end_date":"2025-12-31",
        "headline_value":"$95 annual fee waived for your first year",
        "value_amount":95,"value_currency":"USD",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"open_account","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":True,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":700,
        "required_existing_products":None,"excluded_if_holds_subcategory":"Credit",
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":1,"base_offer_score":0.76,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"email",
        "content_hero_stat":"$95 annual fee — completely waived year 1",
        "content_how_to_earn":"Apply now and your $95 annual fee is automatically waived for the first year. Keep all the rewards, pay nothing until year 2.",
        "content_benefit_1":"Risk-free trial of premium rewards","content_benefit_2":"Full access to 3x dining points","content_benefit_3":"$50 dining credit still included",
        "scoring_weights":{"spending_pattern_boost":0.3,"life_stage_boost":0.3,"digital_boost":0.3,"fee_sensitivity_boost":0.8},
    },
    # ── MRD_P011 Platinum Card ────────────────────────────────────────────────
    {
        "offer_id":"MRD_OFF_017","product_id":"MRD_P011",
        "offer_name":"100,000 Points Platinum Launch Offer","offer_type":"signup_bonus",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"100,000 points — worth $1,000 in travel",
        "value_amount":1000,"value_currency":"USD",
        "spend_requirement":5000,"spend_window_days":90,
        "qualifying_action":"first_purchase","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":740,
        "required_existing_products":None,"excluded_if_holds_subcategory":"Credit",
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":3,"base_offer_score":0.90,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"in_app",
        "content_hero_stat":"100,000 points ($1,000 in travel)",
        "content_how_to_earn":"Spend $5,000 in purchases in the first 3 months. You'll have $1,000 in travel value — flights, hotels, and upgrades.",
        "content_benefit_1":"$200 annual travel credit included","content_benefit_2":"Priority Pass lounge access worldwide","content_benefit_3":"4x points on all travel bookings",
        "scoring_weights":{"spending_pattern_boost":0.7,"life_stage_boost":0.4,"digital_boost":0.6,"fee_sensitivity_boost":0.1},
    },
    {
        "offer_id":"MRD_OFF_018","product_id":"MRD_P011",
        "offer_name":"Companion Ticket Offer","offer_type":"cashback_boost",
        "is_evergreen":False,"offer_end_date":"2025-11-30",
        "headline_value":"Free companion airline ticket each year",
        "value_amount":400,"value_currency":"USD",
        "spend_requirement":15000,"spend_window_days":365,
        "qualifying_action":"first_purchase","min_direct_deposit_amt":None,
        "cashback_category":"travel","cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":740,
        "required_existing_products":None,"excluded_if_holds_subcategory":None,
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":3,"base_offer_score":0.78,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":False,
        "preferred_channel":"email",
        "content_hero_stat":"Free companion airline ticket",
        "content_how_to_earn":"Spend $15,000 in a calendar year and earn a companion ticket on any domestic flight. Valued at up to $400.",
        "content_benefit_1":"Fly your partner or friend free","content_benefit_2":"Applies to main cabin and above","content_benefit_3":"Renewal benefit each card anniversary",
        "scoring_weights":{"spending_pattern_boost":0.8,"life_stage_boost":0.3,"digital_boost":0.6,"fee_sensitivity_boost":0.1},
    },
    # ── MRD_P013 Auto Loan ────────────────────────────────────────────────────
    {
        "offer_id":"MRD_OFF_019","product_id":"MRD_P013",
        "offer_name":"0.25% Rate Discount with Auto-Pay","offer_type":"rate_discount",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"0.25% rate reduction with automatic payments",
        "value_amount":0.25,"value_currency":"pct_apr_reduction",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"auto_pay_enrollment","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":"Checking","excluded_if_holds_subcategory":None,
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":1,"base_offer_score":0.78,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":False,"channel_branch":True,
        "preferred_channel":"in_app",
        "content_hero_stat":"0.25% off your auto loan rate",
        "content_how_to_earn":"Enroll in auto-pay from your Meridian checking account and lock in a 0.25% rate reduction for the life of your auto loan.",
        "content_benefit_1":"Saves $150–$400 over the life of a typical loan","content_benefit_2":"Never miss a payment","content_benefit_3":"Enrollment takes 2 minutes in the app",
        "scoring_weights":{"spending_pattern_boost":0.2,"life_stage_boost":0.3,"digital_boost":0.5,"fee_sensitivity_boost":0.5},
    },
    {
        "offer_id":"MRD_OFF_020","product_id":"MRD_P013",
        "offer_name":"45-Day Rate Lock Guarantee","offer_type":"rate_discount",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"Lock in today's rate for 45 days",
        "value_amount":0,"value_currency":"USD",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"pre_approval","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":None,"excluded_if_holds_subcategory":None,
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":1,"base_offer_score":0.70,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":False,"channel_branch":True,
        "preferred_channel":"email",
        "content_hero_stat":"Your rate locked in for 45 days",
        "content_how_to_earn":"Get pre-approved today and your rate is guaranteed for 45 days — even if market rates rise while you shop for your vehicle.",
        "content_benefit_1":"Shop confidently, rate stays fixed","content_benefit_2":"Pre-approval in under 3 minutes","content_benefit_3":"No impact on your credit score to check",
        "scoring_weights":{"spending_pattern_boost":0.1,"life_stage_boost":0.4,"digital_boost":0.4,"fee_sensitivity_boost":0.3},
    },
    # ── MRD_P014 Personal Loan ────────────────────────────────────────────────
    {
        "offer_id":"MRD_OFF_021","product_id":"MRD_P014",
        "offer_name":"Balance Transfer Personal Loan","offer_type":"balance_transfer_promo",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"Pay off high-interest debt at a lower rate",
        "value_amount":0,"value_currency":"USD",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"open_account","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":"poor","min_credit_score_override":620,
        "required_existing_products":None,"excluded_if_holds_subcategory":None,
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":2,"base_offer_score":0.80,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"email",
        "content_hero_stat":"Consolidate and save on interest",
        "content_how_to_earn":"Use your Meridian Personal Loan to pay off higher-rate credit cards or other debts. Fixed rate, fixed payment, faster payoff.",
        "content_benefit_1":"Single monthly payment replaces multiple bills","content_benefit_2":"Rates from 8.99% vs 20%+ on cards","content_benefit_3":"No prepayment penalty",
        "scoring_weights":{"spending_pattern_boost":0.1,"life_stage_boost":0.4,"digital_boost":0.2,"fee_sensitivity_boost":0.7},
    },
    {
        "offer_id":"MRD_OFF_022","product_id":"MRD_P014",
        "offer_name":"Relationship Rate Discount 0.50%","offer_type":"rate_discount",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"0.50% lower rate for Meridian banking customers",
        "value_amount":0.50,"value_currency":"pct_apr_reduction",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"auto_pay_enrollment","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":"Checking","excluded_if_holds_subcategory":None,
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":1,"base_offer_score":0.75,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":False,"channel_branch":True,
        "preferred_channel":"in_app",
        "content_hero_stat":"0.50% off your personal loan rate",
        "content_how_to_earn":"Enroll in auto-pay from your Meridian checking account. Your rate drops 0.50% automatically — saving you hundreds over the life of your loan.",
        "content_benefit_1":"Combined with checking = maximum savings","content_benefit_2":"Rate locked for full loan term","content_benefit_3":"Easy enrollment in the app",
        "scoring_weights":{"spending_pattern_boost":0.1,"life_stage_boost":0.3,"digital_boost":0.4,"fee_sensitivity_boost":0.6},
    },
    # ── MRD_P015 Home Equity Loan ─────────────────────────────────────────────
    {
        "offer_id":"MRD_OFF_023","product_id":"MRD_P015",
        "offer_name":"No Closing Costs on Home Equity Loan","offer_type":"fee_waiver",
        "is_evergreen":False,"offer_end_date":"2025-10-31",
        "headline_value":"$0 closing costs — save up to $3,000",
        "value_amount":3000,"value_currency":"USD",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"open_account","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":660,
        "required_existing_products":None,"excluded_if_holds_subcategory":None,
        "min_deposits_required":None,"requires_homeowner":True,"churn_only":False,
        "offer_complexity":3,"base_offer_score":0.85,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"branch",
        "content_hero_stat":"$0 closing costs — pay nothing upfront",
        "content_how_to_earn":"Open a Meridian Home Equity Loan before October 31 and all closing costs are waived. Save up to $3,000 in origination and appraisal fees.",
        "content_benefit_1":"Tap up to 85% of your home equity","content_benefit_2":"Fixed rate, predictable monthly payments","content_benefit_3":"Tax-deductible interest may apply — ask your advisor",
        "scoring_weights":{"spending_pattern_boost":0.1,"life_stage_boost":0.5,"digital_boost":0.2,"fee_sensitivity_boost":0.6},
    },
    {
        "offer_id":"MRD_OFF_024","product_id":"MRD_P015",
        "offer_name":"Home Improvement Rate Special 7.25%","offer_type":"rate_discount",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"7.25% fixed rate for home improvements",
        "value_amount":0,"value_currency":"USD",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"stated_purpose_home_improvement","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":7.25,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":660,
        "required_existing_products":None,"excluded_if_holds_subcategory":None,
        "min_deposits_required":None,"requires_homeowner":True,"churn_only":False,
        "offer_complexity":3,"base_offer_score":0.78,
        "channel_in_app":False,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"branch",
        "content_hero_stat":"7.25% fixed rate for home improvements",
        "content_how_to_earn":"Use your Home Equity Loan for qualified home improvements and lock in our best fixed rate of 7.25% for excellent credit customers.",
        "content_benefit_1":"Increase your home's value with equity","content_benefit_2":"Fixed rate never changes","content_benefit_3":"Interest may be tax deductible",
        "scoring_weights":{"spending_pattern_boost":0.1,"life_stage_boost":0.5,"digital_boost":0.1,"fee_sensitivity_boost":0.4},
    },
    # ── MRD_P017 Mortgage ─────────────────────────────────────────────────────
    {
        "offer_id":"MRD_OFF_025","product_id":"MRD_P017",
        "offer_name":"60-Day Rate Lock","offer_type":"rate_discount",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"Lock your rate for 60 days, free",
        "value_amount":0,"value_currency":"USD",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"pre_approval","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":640,
        "required_existing_products":None,"excluded_if_holds_subcategory":None,
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":3,"base_offer_score":0.82,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"email",
        "content_hero_stat":"60-day rate lock — guaranteed",
        "content_how_to_earn":"Get pre-approved for a Meridian Mortgage and we'll lock your rate for 60 days at no cost. Shop for your home with confidence.",
        "content_benefit_1":"Protected from rising rates while you search","content_benefit_2":"No fee for the rate lock","content_benefit_3":"Local loan officer supports you through closing",
        "scoring_weights":{"spending_pattern_boost":0.05,"life_stage_boost":0.5,"digital_boost":0.3,"fee_sensitivity_boost":0.4},
    },
    {
        "offer_id":"MRD_OFF_026","product_id":"MRD_P017",
        "offer_name":"$1,000 Closing Cost Credit","offer_type":"fee_waiver",
        "is_evergreen":False,"offer_end_date":"2025-12-31",
        "headline_value":"$1,000 off your closing costs",
        "value_amount":1000,"value_currency":"USD",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"open_account","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":640,
        "required_existing_products":"Checking","excluded_if_holds_subcategory":None,
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":3,"base_offer_score":0.85,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"branch",
        "content_hero_stat":"$1,000 closing cost credit",
        "content_how_to_earn":"Existing Meridian banking customers who finance through Meridian Mortgage receive a $1,000 closing cost credit automatically applied at settlement.",
        "content_benefit_1":"Keep more cash for moving and furnishing","content_benefit_2":"Auto-applied — no forms to file","content_benefit_3":"Combinable with down payment assistance programs",
        "scoring_weights":{"spending_pattern_boost":0.05,"life_stage_boost":0.5,"digital_boost":0.2,"fee_sensitivity_boost":0.5},
    },
    # ── MRD_P019 Traditional IRA ──────────────────────────────────────────────
    {
        "offer_id":"MRD_OFF_027","product_id":"MRD_P019",
        "offer_name":"Fee-Free IRA for 2 Years","offer_type":"fee_waiver",
        "is_evergreen":False,"offer_end_date":"2025-12-31",
        "headline_value":"$0 annual fee for your first 2 years",
        "value_amount":50,"value_currency":"USD",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"open_account","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":None,"excluded_if_holds_subcategory":"Investment",
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":2,"base_offer_score":0.78,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"email",
        "content_hero_stat":"2 years of IRA fees waived ($50 value)",
        "content_how_to_earn":"Open a Meridian Traditional IRA by December 31 and your $25 annual fee is waived for the first two years. Your retirement savings go further.",
        "content_benefit_1":"Invest in stocks, ETFs, and mutual funds","content_benefit_2":"Tax deduction on contributions up to $7,000","content_benefit_3":"Free rollover from previous employer 401(k)",
        "scoring_weights":{"spending_pattern_boost":0.05,"life_stage_boost":0.7,"digital_boost":0.3,"fee_sensitivity_boost":0.4},
    },
    {
        "offer_id":"MRD_OFF_028","product_id":"MRD_P019",
        "offer_name":"Retirement Ready Match — Deposit $500, Get $50","offer_type":"signup_bonus",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"Deposit $500, we add $50",
        "value_amount":50,"value_currency":"USD",
        "spend_requirement":500,"spend_window_days":90,
        "qualifying_action":"first_deposit","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":None,"excluded_if_holds_subcategory":"Investment",
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":2,"base_offer_score":0.80,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":False,"channel_branch":True,
        "preferred_channel":"in_app",
        "content_hero_stat":"We match $50 on your first $500 IRA deposit",
        "content_how_to_earn":"Open a Traditional IRA and deposit at least $500 within 90 days. Meridian adds $50 directly to your IRA — a 10% instant return to kick off your retirement savings.",
        "content_benefit_1":"Instant 10% boost on your first deposit","content_benefit_2":"Tax-deferred growth from day one","content_benefit_3":"Max contribution: $7,000/year ($8,000 if 50+)",
        "scoring_weights":{"spending_pattern_boost":0.05,"life_stage_boost":0.6,"digital_boost":0.3,"fee_sensitivity_boost":0.4},
    },
    # ── MRD_P020 Roth IRA ────────────────────────────────────────────────────
    {
        "offer_id":"MRD_OFF_029","product_id":"MRD_P020",
        "offer_name":"Roth IRA Young Saver Promo","offer_type":"fee_waiver",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"Zero fees until age 35",
        "value_amount":75,"value_currency":"USD",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"open_account","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":None,"excluded_if_holds_subcategory":"Investment",
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":2,"base_offer_score":0.82,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":False,"channel_branch":True,
        "preferred_channel":"in_app",
        "content_hero_stat":"No annual fee until you turn 35",
        "content_how_to_earn":"Open a Meridian Roth IRA before age 35 and pay zero annual maintenance fees until your 35th birthday. Start your tax-free retirement journey now.",
        "content_benefit_1":"Tax-free growth and withdrawals in retirement","content_benefit_2":"No required minimum distributions ever","content_benefit_3":"Contribute after-tax dollars up to $7,000/year",
        "scoring_weights":{"spending_pattern_boost":0.05,"life_stage_boost":0.8,"digital_boost":0.5,"fee_sensitivity_boost":0.5},
    },
    {
        "offer_id":"MRD_OFF_030","product_id":"MRD_P020",
        "offer_name":"$75 Roth IRA Welcome Contribution","offer_type":"signup_bonus",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"Meridian adds $75 to your new Roth IRA",
        "value_amount":75,"value_currency":"USD",
        "spend_requirement":1000,"spend_window_days":90,
        "qualifying_action":"first_deposit","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":None,"excluded_if_holds_subcategory":"Investment",
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":2,"base_offer_score":0.80,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":False,"channel_branch":True,
        "preferred_channel":"in_app",
        "content_hero_stat":"$75 added to your Roth IRA instantly",
        "content_how_to_earn":"Open a Roth IRA and deposit $1,000 within 90 days. Meridian contributes $75 directly into your account — your first step toward tax-free retirement.",
        "content_benefit_1":"Start compounding tax-free today","content_benefit_2":"$75 is yours to invest immediately","content_benefit_3":"Withdraw contributions (not earnings) anytime",
        "scoring_weights":{"spending_pattern_boost":0.05,"life_stage_boost":0.7,"digital_boost":0.4,"fee_sensitivity_boost":0.4},
    },
    # ── MRD_B001 Business Essential Checking ─────────────────────────────────
    {
        "offer_id":"MRD_OFF_031","product_id":"MRD_B001",
        "offer_name":"$400 Business Account Opening Bonus","offer_type":"signup_bonus",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"Earn $400 for your business",
        "value_amount":400,"value_currency":"USD",
        "spend_requirement":5000,"spend_window_days":90,
        "qualifying_action":"direct_deposit_setup","min_direct_deposit_amt":2000,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":True,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":None,"excluded_if_holds_subcategory":"Checking",
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":2,"base_offer_score":0.82,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"branch",
        "content_hero_stat":"$400 business welcome bonus",
        "content_how_to_earn":"Open Meridian Business Essential Checking, set up $2,000 monthly ACH deposits, and process $5,000 in transactions within 90 days.",
        "content_benefit_1":"200 free transactions per month","content_benefit_2":"Free online bill pay and ACH","content_benefit_3":"Dedicated small business banker",
        "scoring_weights":{"spending_pattern_boost":0.2,"life_stage_boost":0.2,"digital_boost":0.4,"fee_sensitivity_boost":0.5},
    },
    {
        "offer_id":"MRD_OFF_032","product_id":"MRD_B001",
        "offer_name":"Fee Waiver + Free Business Debit Card","offer_type":"fee_waiver",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"Zero monthly fee with $1,500 average balance",
        "value_amount":180,"value_currency":"USD",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"maintain_balance","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":None,
        "required_existing_products":None,"excluded_if_holds_subcategory":None,
        "min_deposits_required":1500,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":1,"base_offer_score":0.72,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":False,"channel_branch":True,
        "preferred_channel":"email",
        "content_hero_stat":"$0 monthly fee — just maintain $1,500",
        "content_how_to_earn":"Maintain an average daily balance of $1,500 and your $15 monthly fee disappears. Plus get your first business debit card at no cost.",
        "content_benefit_1":"Savings of $180/year","content_benefit_2":"Free business debit card (up to 2 employees)","content_benefit_3":"Mobile deposit included",
        "scoring_weights":{"spending_pattern_boost":0.2,"life_stage_boost":0.2,"digital_boost":0.3,"fee_sensitivity_boost":0.8},
    },
    # ── MRD_B005 Business Rewards Card ───────────────────────────────────────
    {
        "offer_id":"MRD_OFF_033","product_id":"MRD_B005",
        "offer_name":"$500 Business Welcome Bonus","offer_type":"signup_bonus",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"Earn $500 for your business expenses",
        "value_amount":500,"value_currency":"USD",
        "spend_requirement":3000,"spend_window_days":90,
        "qualifying_action":"first_purchase","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":680,
        "required_existing_products":None,"excluded_if_holds_subcategory":"Credit",
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":2,"base_offer_score":0.85,
        "channel_in_app":True,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"in_app",
        "content_hero_stat":"$500 for your first $3,000 in business spending",
        "content_how_to_earn":"Apply for the Meridian Business Rewards Card and spend $3,000 on business purchases in the first 3 months to earn a $500 welcome bonus.",
        "content_benefit_1":"3x points on travel and software","content_benefit_2":"2x on office supplies and dining","content_benefit_3":"Employee cards at no extra cost",
        "scoring_weights":{"spending_pattern_boost":0.3,"life_stage_boost":0.3,"digital_boost":0.5,"fee_sensitivity_boost":0.3},
    },
    # ── MRD_A001 Farm Operating Line ─────────────────────────────────────────
    {
        "offer_id":"MRD_OFF_034","product_id":"MRD_A001",
        "offer_name":"Spring Operating Line Rate Special","offer_type":"rate_discount",
        "is_evergreen":False,"offer_end_date":"2025-08-31",
        "headline_value":"Lock in 7.25% for your spring operating line",
        "value_amount":0.50,"value_currency":"pct_apr_reduction",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"open_account","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":7.25,"rate_duration_months":12,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":600,
        "required_existing_products":None,"excluded_if_holds_subcategory":None,
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":2,"base_offer_score":0.82,
        "channel_in_app":False,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"branch",
        "content_hero_stat":"7.25% rate — our best for spring planting",
        "content_how_to_earn":"Apply for a Farm Operating Line before August 31 and lock in 7.25% for the first year. Dedicated agricultural lenders with crop expertise.",
        "content_benefit_1":"Up to $2M credit line","content_benefit_2":"Interest-only during growing season","content_benefit_3":"Annual review with your ag banker",
        "scoring_weights":{"spending_pattern_boost":0.1,"life_stage_boost":0.3,"digital_boost":0.1,"fee_sensitivity_boost":0.5},
    },
    # ── MRD_A002 Equipment Term Loan ─────────────────────────────────────────
    {
        "offer_id":"MRD_OFF_035","product_id":"MRD_A002",
        "offer_name":"100% Financing on New Equipment","offer_type":"rate_discount",
        "is_evergreen":True,"offer_end_date":None,
        "headline_value":"Zero down on new farm equipment",
        "value_amount":0,"value_currency":"USD",
        "spend_requirement":None,"spend_window_days":None,
        "qualifying_action":"open_account","min_direct_deposit_amt":None,
        "cashback_category":None,"cashback_pct":None,"rate_pct":None,"rate_duration_months":None,
        "new_customer_only":False,"existing_customer_only":False,
        "min_tenure_months":0,"max_tenure_months":None,
        "excluded_credit_tiers":None,"min_credit_score_override":580,
        "required_existing_products":None,"excluded_if_holds_subcategory":None,
        "min_deposits_required":None,"requires_homeowner":False,"churn_only":False,
        "offer_complexity":2,"base_offer_score":0.78,
        "channel_in_app":False,"channel_email":True,"channel_direct_mail":True,"channel_branch":True,
        "preferred_channel":"branch",
        "content_hero_stat":"100% financing — no down payment needed",
        "content_how_to_earn":"Finance new farm equipment with Meridian and we'll cover 100% of the purchase price. Keep your operating cash for inputs and labor.",
        "content_benefit_1":"Terms up to 7 years","content_benefit_2":"Manufacturer rebates applied directly","content_benefit_3":"Decision in 48 hours",
        "scoring_weights":{"spending_pattern_boost":0.1,"life_stage_boost":0.3,"digital_boost":0.1,"fee_sensitivity_boost":0.5},
    },
]


# ── customer generation ───────────────────────────────────────────────────────

CUSTOMER_CONFIGS = [
    # (segment, customer_type, count, age_range, income_range, credit_range)
    ("Personal","Mass_Market",       2200,(25,75),(28000,95000),(580,780)),
    ("Personal","Young_Professional", 900,(22,38),(40000,120000),(650,800)),
    ("Personal","High_Net_Worth",     550,(35,70),(120000,400000),(720,850)),
    ("Personal","Retiree",            750,(62,85),(20000,80000),(640,800)),
    ("Personal","Digital_Native",     400,(18,32),(25000,75000),(620,780)),
    # micro-extras to reach 5000
    ("Personal","Mass_Market",        200,(50,80),(22000,60000),(540,720)),
]

def pick_geographic_region():
    return weighted_choice(["Urban","Suburban","Rural"], [0.38,0.45,0.17])

def derive_life_stage(age, home_ownership_type, income):
    if age < 23: return "student"
    if age < 32 and home_ownership_type == "renter": return "young_single"
    if 25 <= age <= 40 and home_ownership_type in ("owner_with_mortgage","renter") and income < 100000:
        return weighted_choice(["young_single","new_family"], [0.45,0.55])
    if 32 <= age <= 50: return weighted_choice(["new_family","growing_family"], [0.4,0.6])
    if 50 <= age <= 62: return "empty_nester"
    if 62 <= age <= 70: return "pre_retiree"
    return "retiree"

def derive_home_ownership_type(age, income, deposits, customer_type):
    base_own = 0.20
    if age >= 35: base_own += 0.22
    if age >= 50: base_own += 0.15
    if income >= 70000: base_own += 0.12
    if deposits >= 20000: base_own += 0.10
    if customer_type in ("High_Net_Worth","Retiree","Commercial_Real_Estate"): base_own += 0.18
    prob_own = min(base_own, 0.85)
    prob_mortgage = min(0.55 - (age - 35) * 0.005 if age > 35 else 0.55, 0.55)
    r = random.random()
    if r < prob_own * 0.3: return "owner_free_clear"
    if r < prob_own: return "owner_with_mortgage"
    return "renter"

def derive_employment_type(age, customer_type, income):
    if customer_type in ("Row_Crop_Farmer","Livestock_Rancher","Vineyard_Orchard_Owner"):
        return "self_employed"
    if customer_type in ("Small_Business","Commercial_Real_Estate"):
        return weighted_choice(["self_employed","full_time_w2"], [0.65,0.35])
    if customer_type == "Retiree" or age >= 68:
        return "retired"
    if age < 23:
        return weighted_choice(["student","part_time"], [0.6,0.4])
    if income < 30000:
        return weighted_choice(["part_time","contractor","full_time_w2"], [0.3,0.2,0.5])
    return weighted_choice(["full_time_w2","contractor","self_employed"], [0.72,0.16,0.12])

def derive_primary_spending_category(customer_type, age, income):
    if customer_type in ("Young_Professional","Digital_Native"):
        return weighted_choice(["dining","travel","online_retail","groceries","gas"], [0.30,0.25,0.22,0.13,0.10])
    if customer_type == "High_Net_Worth":
        return weighted_choice(["travel","dining","groceries","online_retail","gas"], [0.35,0.25,0.20,0.12,0.08])
    if customer_type == "Retiree" or age >= 65:
        return weighted_choice(["groceries","utilities","gas","dining","online_retail"], [0.35,0.25,0.18,0.12,0.10])
    if customer_type in ("Small_Business","Commercial_Real_Estate"):
        return weighted_choice(["online_retail","dining","travel","gas","groceries"], [0.28,0.22,0.22,0.18,0.10])
    return weighted_choice(["groceries","gas","dining","online_retail","utilities"], [0.32,0.22,0.20,0.16,0.10])

def derive_financial_goal(age, home_ownership_type, income, customer_type):
    if age < 30: return weighted_choice(["build_emergency_fund","pay_off_debt","home_purchase"], [0.35,0.35,0.30])
    if age < 45:
        if home_ownership_type == "renter":
            return weighted_choice(["home_purchase","pay_off_debt","grow_wealth"], [0.45,0.30,0.25])
        return weighted_choice(["grow_wealth","pay_off_debt","retirement_savings"], [0.35,0.35,0.30])
    if age < 60:
        return weighted_choice(["retirement_savings","grow_wealth","pay_off_debt"], [0.45,0.35,0.20])
    return weighted_choice(["retirement_savings","grow_wealth","build_emergency_fund"], [0.55,0.30,0.15])

def derive_travel_frequency(income, customer_type, age):
    if customer_type in ("High_Net_Worth",) and income > 150000:
        return weighted_choice(["international_frequent","domestic_frequent","domestic_occasional","none"], [0.35,0.30,0.25,0.10])
    if customer_type == "Young_Professional" and income > 60000:
        return weighted_choice(["domestic_frequent","international_occasional","domestic_occasional","none"], [0.30,0.25,0.30,0.15])
    if age >= 65:
        return weighted_choice(["domestic_occasional","none","domestic_frequent","international_occasional"], [0.35,0.30,0.20,0.15])
    return weighted_choice(["none","domestic_occasional","domestic_frequent","international_occasional"], [0.30,0.35,0.20,0.15])

def derive_preferred_communication_style(digital_engagement, age):
    if digital_engagement >= 0.75 and age < 45:
        return weighted_choice(["brief_direct","visual_first","numbers_focused","detailed_explanation"], [0.45,0.30,0.15,0.10])
    if age >= 60:
        return weighted_choice(["detailed_explanation","numbers_focused","brief_direct","visual_first"], [0.40,0.30,0.20,0.10])
    return weighted_choice(["brief_direct","numbers_focused","detailed_explanation","visual_first"], [0.35,0.25,0.25,0.15])

def derive_churn_risk(tenure, digital_engagement, complaints, overdrafts, balance_trend, products_closed, competitor_received):
    score = 0.0
    if tenure < 12: score += 20
    elif tenure < 24: score += 10
    if digital_engagement < 0.3: score += 15
    if complaints > 2: score += 20
    elif complaints > 0: score += 8
    if overdrafts > 2: score += 12
    if balance_trend == "Declining": score += 15
    if products_closed > 0: score += 18
    if competitor_received: score += 10
    score += random.uniform(-5, 5)
    score = clamp(score, 0, 100)
    if score >= 65: cat = "Critical"
    elif score >= 40: cat = "High"
    elif score >= 20: cat = "Medium"
    else: cat = "Low"
    return round(score, 2), cat, round(score / 100, 4)

def generate_customers():
    path = os.path.join(DEST, "customers.csv")

    FIELDNAMES = [
        # core identity
        "customer_id","customer_name","customer_segment","customer_type","age","income","credit_score",
        "total_deposits","num_products","digital_engagement_score","branch_visit_frequency",
        "months_since_relationship_started","monthly_transaction_volume","cross_sell_receptivity",
        # transaction signals
        "last_transaction_date","days_since_last_transaction","recent_txn_count","previous_txn_count",
        "txn_frequency_trend","balance_trend","deposit_change_3mo_pct",
        # risk flags
        "low_balance_flag","products_closed_last_6mo","complaints_last_year","support_contacts_last_3mo",
        "digital_engagement_decline","competitor_offer_received","fee_sensitivity_score",
        "external_accounts_linked","recent_life_event","age_risk_factor",
        # satisfaction
        "nps_score","nps_category","csat_score","branch_satisfaction",
        # more risk
        "credit_score_declining","overdrafts_last_3mo","high_overdraft_flag","debt_payment_missed",
        # churn
        "churn_risk_score","churn_risk_category","churn_probability",
        "churned","churn_date","recommended_retention_action","suggested_retention_offer",
        # financial
        "annual_transaction_value","expected_relationship_years","customer_lifetime_value","clv_tier",
        # JPM-style fields (kept for scorer compat)
        "credit_tier","fee_sensitivity_tier","preferred_rewards_type",
        "has_direct_deposit","monthly_direct_deposit_amt",
        "owns_home","investment_risk_profile","preferred_loan_term",
        # NEW Meridian-specific fields
        "home_ownership_type","outstanding_debt_total","primary_spending_category",
        "monthly_spend_in_primary_cat","financial_goal","travel_frequency",
        "employment_type","has_competitor_credit_card","life_stage","preferred_communication_style",
        # Meridian v2 fields
        "credit_score_trend","occupation","address_changes_count",
    ]

    rows = []
    cid = 1
    for seg, ctype, count, (age_lo, age_hi), (inc_lo, inc_hi), (cs_lo, cs_hi) in CUSTOMER_CONFIGS:
        for _ in range(count):
            name  = rnd_name()
            age   = random.randint(age_lo, age_hi)
            income= round(random.triangular(inc_lo, inc_hi, (inc_lo+inc_hi)*0.45), 2)
            cs    = random.randint(cs_lo, cs_hi)
            deps  = round(max(0, income * random.uniform(0.05, 0.80) * (1 + (age-30)*0.008)), 2)
            num_prods = random.choices([1,2,3,4,5,6,7,8], weights=[25,25,20,12,8,5,3,2], k=1)[0]
            _raw_d   = random.betavariate(2, 2) * 0.9 + 0.05
            _raw_b   = max(0.01, 1 - _raw_d + random.uniform(-0.2, 0.2))
            _eng_tot = _raw_d + _raw_b
            digital  = round(_raw_d / _eng_tot, 4)
            branch_f = round(_raw_b / _eng_tot, 4)
            tenure   = random.choices(
                range(1,241),
                weights=[max(1, 241-m) for m in range(1,241)],
                k=1)[0]
            mtv      = int(max(1, random.lognormvariate(2.5, 0.7)))
            xsell    = round(clamp(random.betavariate(2,3), 0.05, 0.95), 4)
            fee_sens = round(clamp(random.betavariate(2,2.5), 0.05, 0.95), 4)

            last_txn_days  = random.choices([0,1,3,7,14,30,60,90,180], weights=[20,15,15,12,10,10,8,5,5], k=1)[0]
            last_txn_date  = fmt_date(TODAY - timedelta(days=last_txn_days))
            recent_count   = int(max(0, mtv * random.uniform(0.7,1.3)))
            prev_count     = int(max(0, mtv * random.uniform(0.6,1.4)))
            txn_trend      = weighted_choice(["Increasing","Stable","Declining"], [0.30,0.45,0.25])
            bal_trend      = weighted_choice(["Improving","Stable","Declining"], [0.32,0.42,0.26])
            dep_chg        = round(random.normalvariate(2.5, 8.0), 2)
            low_bal        = 1 if deps < 500 else 0
            prods_closed   = random.choices([0,1,2], weights=[80,15,5], k=1)[0]
            complaints     = random.choices([0,1,2,3], weights=[75,15,7,3], k=1)[0]
            support_cts    = random.choices([0,1,2,3,4], weights=[60,20,12,5,3], k=1)[0]
            dig_decline    = 1 if digital < 0.3 and random.random() < 0.4 else 0
            comp_recv      = 1 if random.random() < 0.18 else 0
            ext_accts      = random.choices([0,1,2,3], weights=[50,30,15,5], k=1)[0]
            life_event     = weighted_choice(["","","","","Job_Change","Marriage","Divorce","Relocation","Retirement"],
                                             [40,20,10,5,10,7,3,3,2])
            age_risk       = round(clamp(abs(age-45)/45, 0, 1), 4)
            nps            = int(clamp(random.normalvariate(42, 22), -100, 100))
            nps_cat        = "Promoter" if nps>=50 else ("Detractor" if nps<0 else "Passive")
            csat           = round(clamp(random.normalvariate(3.8, 0.8), 1, 5), 1)
            branch_sat     = round(clamp(random.normalvariate(3.9, 0.7), 1, 5), 1)
            cs_declining   = 1 if random.random() < 0.12 else 0
            overdrafts     = random.choices([0,1,2,3,4], weights=[60,20,10,6,4], k=1)[0]
            hi_od          = 1 if overdrafts >= 3 else 0
            debt_missed    = 1 if random.random() < 0.08 else 0
            churn_score, churn_cat, churn_prob = derive_churn_risk(
                tenure, digital, complaints, overdrafts, bal_trend, prods_closed, comp_recv)
            churned        = 1 if random.random() < churn_prob * 0.05 else 0
            churn_date     = fmt_date(rand_date(365, 30)) if churned else ""
            retention_actions = ["Proactive Outreach","Fee Review","Product Offer","Relationship Meeting","Digital Onboarding","Satisfaction Survey"]
            retention_offers  = ["Fee Waiver","Rate Bonus","Cashback Boost","Bonus Points","Free Service Upgrade","Relationship Discount"]
            ret_action     = random.choice(retention_actions) if churn_cat in ("High","Critical") else ""
            ret_offer      = random.choice(retention_offers)  if churn_cat in ("High","Critical") else ""
            atv            = round(mtv * 12 * random.uniform(80, 500), 2)
            exp_yrs        = round(max(1, random.normalvariate(12 - churn_prob * 8, 3)), 1)
            clv            = round(atv * exp_yrs * random.uniform(0.05, 0.18), 2)
            clv_tier       = "Platinum" if clv > 15000 else ("Gold" if clv > 7000 else ("Silver" if clv > 2500 else "Bronze"))

            # derived fields (JPM-compat)
            credit_tier    = "excellent" if cs>=750 else ("good" if cs>=700 else ("fair" if cs>=650 else "poor"))
            fee_sens_tier  = "high" if fee_sens>=0.7 else ("medium" if fee_sens>=0.4 else "low")
            pref_rewards   = derive_preferred_rewards_type(income, digital, age)
            has_dd         = "True" if (tenure >= 12 and income >= 35000 and random.random() < 0.68) else "False"
            dd_amt         = round(income/12 * random.uniform(0.9,1.1), 2) if has_dd == "True" else 0.0
            owns_home      = "True" if age >= 35 and income >= 55000 and random.random() < 0.60 else "False"
            inv_risk       = ("conservative" if age>=60 else ("moderate" if age>=40 else
                              weighted_choice(["conservative","moderate","aggressive"],[0.15,0.45,0.40])))
            loan_term      = weighted_choice(["short","medium","long"],
                              [0.45,0.40,0.15] if income>=80000 else ([0.20,0.45,0.35] if age<35 else [0.35,0.45,0.20]))

            # NEW Meridian fields
            home_own_type  = derive_home_ownership_type(age, income, deps, ctype)
            out_debt       = round(max(0, random.lognormvariate(8.5, 1.2)) if random.random() < 0.65 else 0.0, 2)
            prim_spend_cat = derive_primary_spending_category(ctype, age, income)
            monthly_spend  = round(max(50, random.lognormvariate(5.8, 0.6)), 2)
            fin_goal       = derive_financial_goal(age, home_own_type, income, ctype)
            travel_freq    = derive_travel_frequency(income, ctype, age)
            emp_type       = derive_employment_type(age, ctype, income)
            has_comp_cc    = "True" if random.random() < 0.42 else "False"
            life_stage     = derive_life_stage(age, home_own_type, income)
            comm_style     = derive_preferred_communication_style(digital, age)

            # v2 columns
            cs_trend       = "Declining" if cs_declining else ("Improving" if random.random() < 0.4 else "Stable")
            _occ_pools = {
                "high": ["Finance","Technology","Healthcare","Manager","Professional","Business Owner"],
                "mid":  ["Education","Government","Healthcare","Retail","Technology","Manager","Professional"],
                "low":  ["Retail","Service","Education","Government"],
            }
            if emp_type == "retired" or life_stage == "retiree":
                occupation = "Retired"
            elif life_stage == "student" or age < 22:
                occupation = "Student"
            elif income >= 75000:
                occupation = random.choice(_occ_pools["high"])
            elif income >= 35000:
                occupation = random.choice(_occ_pools["mid"])
            else:
                occupation = random.choice(_occ_pools["low"])
            addr_changes = max(0, min(3, round(3 - (tenure / 60) * 2.5 + random.uniform(-0.5, 0.5))))

            row = {
                "customer_id": f"CUST_{cid:05d}",
                "customer_name": name,
                "customer_segment": seg,
                "customer_type": ctype,
                "age": age,
                "income": income,
                "credit_score": cs,
                "total_deposits": deps,
                "num_products": num_prods,
                "digital_engagement_score": digital,
                "branch_visit_frequency": branch_f,
                "months_since_relationship_started": tenure,
                "monthly_transaction_volume": mtv,
                "cross_sell_receptivity": xsell,
                "last_transaction_date": last_txn_date,
                "days_since_last_transaction": last_txn_days,
                "recent_txn_count": recent_count,
                "previous_txn_count": prev_count,
                "txn_frequency_trend": txn_trend,
                "balance_trend": bal_trend,
                "deposit_change_3mo_pct": dep_chg,
                "low_balance_flag": low_bal,
                "products_closed_last_6mo": prods_closed,
                "complaints_last_year": complaints,
                "support_contacts_last_3mo": support_cts,
                "digital_engagement_decline": dig_decline,
                "competitor_offer_received": comp_recv,
                "fee_sensitivity_score": fee_sens,
                "external_accounts_linked": ext_accts,
                "recent_life_event": life_event,
                "age_risk_factor": age_risk,
                "nps_score": nps,
                "nps_category": nps_cat,
                "csat_score": csat,
                "branch_satisfaction": branch_sat,
                "credit_score_declining": cs_declining,
                "overdrafts_last_3mo": overdrafts,
                "high_overdraft_flag": hi_od,
                "debt_payment_missed": debt_missed,
                "churn_risk_score": churn_score,
                "churn_risk_category": churn_cat,
                "churn_probability": churn_prob,
                "churned": churned,
                "churn_date": churn_date,
                "recommended_retention_action": ret_action,
                "suggested_retention_offer": ret_offer,
                "annual_transaction_value": atv,
                "expected_relationship_years": exp_yrs,
                "customer_lifetime_value": clv,
                "clv_tier": clv_tier,
                "credit_tier": credit_tier,
                "fee_sensitivity_tier": fee_sens_tier,
                "preferred_rewards_type": pref_rewards,
                "has_direct_deposit": has_dd,
                "monthly_direct_deposit_amt": dd_amt,
                "owns_home": owns_home,
                "investment_risk_profile": inv_risk,
                "preferred_loan_term": loan_term,
                "home_ownership_type": home_own_type,
                "outstanding_debt_total": out_debt,
                "primary_spending_category": prim_spend_cat,
                "monthly_spend_in_primary_cat": monthly_spend,
                "financial_goal": fin_goal,
                "travel_frequency": travel_freq,
                "employment_type": emp_type,
                "has_competitor_credit_card": has_comp_cc,
                "life_stage": life_stage,
                "preferred_communication_style": comm_style,
                "credit_score_trend": cs_trend,
                "occupation": occupation,
                "address_changes_count": addr_changes,
            }
            rows.append(row)
            cid += 1

    # shuffle so segment order is mixed
    random.shuffle(rows)
    # re-assign customer IDs after shuffle
    for i, row in enumerate(rows, 1):
        row["customer_id"] = f"CUST_{i:05d}"

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  customers: {len(rows)} rows -> {path}")
    return rows


# ── products csv ──────────────────────────────────────────────────────────────

def generate_products():
    path = os.path.join(DEST, "products.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PRODUCT_FIELDS)
        writer.writeheader()
        writer.writerows(PRODUCTS)
    print(f"  products: {len(PRODUCTS)} rows -> {path}")


# ── transactions csv ──────────────────────────────────────────────────────────

PERSONAL_PRODUCTS  = ["MRD_P002","MRD_P005","MRD_P009","MRD_P013","MRD_P017","MRD_P014","MRD_P021"]
PREMIUM_PRODUCTS   = ["MRD_P003","MRD_P006","MRD_P010","MRD_P011","MRD_P022","MRD_P026"]
CHANNELS           = ["Mobile","Online","Branch","ATM","Phone"]
CHANNEL_WEIGHTS    = [0.38,0.27,0.23,0.08,0.04]
TXN_TYPES          = ["account_opened","deposit","purchase","transfer","payment","withdrawal","direct_deposit"]
TXN_WEIGHTS        = [0.05,0.20,0.30,0.12,0.15,0.12,0.06]

def generate_transactions(customers):
    path = os.path.join(DEST, "transactions.csv")
    fields = ["transaction_id","customer_id","product_id","transaction_date","transaction_type","amount","channel"]
    tid = 1
    written = 0

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for row in customers:
            cid  = row["customer_id"]
            seg  = row["customer_segment"]
            ctype= row["customer_type"]
            mtv  = int(row.get("monthly_transaction_volume",5))
            tenure= int(row.get("months_since_relationship_started") or row.get("tenure_months", 12))
            # scale total transactions roughly by tenure × monthly volume
            n_txns = int(clamp(mtv * min(tenure, 24) * random.uniform(0.4,0.8), 5, 400))

            # pick product pool
            if ctype in ("High_Net_Worth",):
                pool = PERSONAL_PRODUCTS + PREMIUM_PRODUCTS
            elif ctype == "Digital_Native":
                pool = PERSONAL_PRODUCTS + ["MRD_P009","MRD_P020"]
            else:
                pool = PERSONAL_PRODUCTS

            for _ in range(n_txns):
                pid     = random.choice(pool)
                days_ago = random.randint(0, min(tenure*30, 730))
                txn_date= fmt_date(TODAY - timedelta(days=days_ago))
                txn_type= weighted_choice(TXN_TYPES, TXN_WEIGHTS)
                amount  = round(max(1, random.lognormvariate(5.5, 1.0)), 2)
                channel = weighted_choice(CHANNELS, CHANNEL_WEIGHTS)

                writer.writerow({
                    "transaction_id": f"TXN_{tid:07d}",
                    "customer_id": cid,
                    "product_id": pid,
                    "transaction_date": txn_date,
                    "transaction_type": txn_type,
                    "amount": amount,
                    "channel": channel,
                })
                tid   += 1
                written += 1

    print(f"  transactions: {written} rows -> {path}")


# ── ancillary files ───────────────────────────────────────────────────────────

def generate_ancillary(customers):
    product_ids = [p["product_id"] for p in PRODUCTS]
    cust_ids    = [c["customer_id"] for c in customers]

    # wishlist
    wl_path = os.path.join(DEST, "wishlist.csv")
    with open(wl_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["customer_id","product_id","added_date","notes"])
        w.writeheader()
        for cid in random.sample(cust_ids, int(len(cust_ids)*0.08)):
            for _ in range(random.randint(1,2)):
                w.writerow({
                    "customer_id": cid,
                    "product_id": random.choice(product_ids),
                    "added_date": fmt_date(rand_date(120)),
                    "notes": "",
                })
    print(f"  wishlist: written -> {wl_path}")

    # incomplete applications
    ia_path = os.path.join(DEST, "incomplete_applications.csv")
    steps   = ["personal_info","financial_details","document_upload","review","sign"]
    with open(ia_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["customer_id","product_id","started_date","last_step"])
        w.writeheader()
        for cid in random.sample(cust_ids, int(len(cust_ids)*0.04)):
            w.writerow({
                "customer_id": cid,
                "product_id": random.choice(product_ids),
                "started_date": fmt_date(rand_date(45)),
                "last_step": random.choice(steps),
            })
    print(f"  incomplete_applications: written -> {ia_path}")

    # recommendation impressions
    ri_path = os.path.join(DEST, "recommendation_impressions.csv")
    with open(ri_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["customer_id","product_id","shown_count","click_count","last_shown_date"])
        w.writeheader()
        for cid in random.sample(cust_ids, int(len(cust_ids)*0.20)):
            for _ in range(random.randint(1,3)):
                shown  = random.randint(1,6)
                clicks = random.randint(0, min(shown,2))
                w.writerow({
                    "customer_id": cid,
                    "product_id": random.choice(product_ids),
                    "shown_count": shown,
                    "click_count": clicks,
                    "last_shown_date": fmt_date(rand_date(60)),
                })
    print(f"  recommendation_impressions: written -> {ri_path}")


# ── product offers json ───────────────────────────────────────────────────────

def generate_offers():
    path = os.path.join(CFG, "product_offers.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(OFFERS, f, indent=2, ensure_ascii=False)
    print(f"  product_offers: {len(OFFERS)} offers -> {path}")


# ── derive_preferred_rewards_type (reused from jpm script) ───────────────────

def derive_preferred_rewards_type(income, digital, age):
    income = float(income)
    digital= float(digital)
    age    = int(age)
    if income >= 80000 and digital >= 0.6 and age < 55:
        return "travel_points" if random.random() < 0.72 else "cash_back"
    if income >= 40000:
        return "cash_back" if random.random() < 0.65 else "none"
    return "none" if random.random() < 0.5 else "cash_back"


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating Meridian Community Bank dataset...")
    print(f"  Dest : {DEST}")
    print(f"  Config: {CFG}")
    print()

    print("1. Generating customers...")
    customers = generate_customers()

    print("2. Generating products...")
    generate_products()

    print("3. Generating transactions...")
    generate_transactions(customers)

    print("4. Generating ancillary files...")
    generate_ancillary(customers)

    print("5. Generating product offers JSON...")
    generate_offers()

    print()
    total = sum(c for _,_,c,*_ in CUSTOMER_CONFIGS)
    print(f"Done. {len(customers)} customers, {len(PRODUCTS)} products, {len(OFFERS)} offers.")
    print(f"Files written to {DEST}/")
    print(f"Offers written to {CFG}/product_offers.json")
