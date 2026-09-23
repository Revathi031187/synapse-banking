"""
Essential Churn Feature Generator for Banking
Adds ONLY critical churn features calculated from REAL transaction data
NO random generation - all metrics derived from actual behavior
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

try:
    from utils.banking_constants import DIGITAL_HIGH, DIGITAL_MED, DIGITAL_LOW
except ImportError:
    DIGITAL_HIGH, DIGITAL_MED, DIGITAL_LOW = 0.65, 0.40, 0.20


def _safe_int(v, default=0):
    try:
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return default
        if hasattr(v, "item"):
            v = v.item()
        return int(float(v))
    except (TypeError, ValueError):
        return default


def _safe_float(v, default=0.0):
    try:
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return default
        if hasattr(v, "item"):
            v = v.item()
        return float(v)
    except (TypeError, ValueError):
        return default


def _safe_div(a, b, default=0.0):
    try:
        av = _safe_float(a, 0.0)
        bv = _safe_float(b, 0.0)
        if abs(bv) < 1e-12:
            return default
        return av / bv
    except Exception:
        return default


def format_churn_risk_reason(row) -> str:
    """
    Human-readable explanation for why a customer has elevated churn risk,
    derived from the same behavioral signals as churn_risk_score.
    """
    def _get(key, default=None):
        try:
            if hasattr(row, "get"):
                v = row.get(key, default)
            else:
                v = row[key] if key in row.index else default
            if v is not None and pd.isna(v):
                return default
            return v
        except Exception:
            return default

    try:
        reasons = []
        recent = _safe_int(_get("recent_txn_count", 0))
        prev = _safe_int(_get("previous_txn_count", 0))
        dslt = _safe_float(_get("days_since_last_txn", 0))
        tv = _safe_float(_get("txn_velocity_change", 0))

        if recent == 0 and prev > 0:
            reasons.append("No transactions in the last 30 days after prior activity")
        elif recent == 0:
            reasons.append("No transactions in the last 30 days")
        if tv < -3:
            reasons.append("Sharp drop in transaction volume vs prior month")
        elif tv < -1 and recent < prev:
            reasons.append("Declining transaction activity")
        if dslt > 75:
            reasons.append(f"{int(dslt)}+ days since last banking activity")
        elif dslt > 45:
            reasons.append(f"{int(dslt)} days since last transaction")

        if _safe_int(_get("balance_risk", 0)) == 1:
            reasons.append("Low account balance")
        if _safe_int(_get("balance_below_expected", 0)) == 1:
            reasons.append("Savings balance below expected for income level")
        if _safe_int(_get("single_product_risk", 0)) == 1:
            reasons.append("Single-product relationship")
        if _safe_int(_get("low_product_adoption", 0)) == 1:
            reasons.append("Limited product depth vs tenure")
        if _safe_int(_get("digital_decline", 0)) == 1:
            reasons.append("Low digital engagement")
        if _safe_int(_get("branch_only_user", 0)) == 1:
            reasons.append("Branch-only channel pattern")
        if _safe_int(_get("credit_risk", 0)) == 1:
            reasons.append("Credit profile stress signals")

        score = _safe_float(_get("churn_risk_score", 0))
        raw_cat = str(_get("churn_risk_category", "") or "").strip()
        # Derive category from score if stored value is missing or NaN
        if raw_cat in ('', 'nan', 'NaN', 'None'):
            cat = ('Critical' if score >= 75 else 'High' if score >= 50 else 'Medium' if score >= 25 else 'Low')
        else:
            cat = raw_cat

        if not reasons:
            reasons.append(
                f"Composite model score {score:.0f}/100 ({cat}): "
                "weighs days since activity, transaction trend, balances vs income, product breadth, and digital usage."
            )
        else:
            reasons.append(f"Overall score {score:.0f}/100 ({cat})")

        seen = set()
        out = []
        for r in reasons:
            if r not in seen:
                seen.add(r)
                out.append(r)
        return "; ".join(out[:6])
    except Exception:
        sc = _safe_float(_get("churn_risk_score", 0))
        return (
            f"Elevated churn risk (score {sc:.0f}/100) from transaction recency, activity trend, "
            "balances, product relationships, and channel engagement."
        )


def format_retention_strategy(row) -> str:
    """
    Data-driven retention playbook: ties recommended action + offer type to observed signals.
    """
    def _get(key, default=None):
        try:
            if hasattr(row, "get"):
                v = row.get(key, default)
            else:
                v = row[key] if key in row.index else default
            if v is not None and pd.isna(v):
                return default
            return v
        except Exception:
            return default

    try:
        action = str(_get("recommended_retention_action", "") or "").strip()
        offer_hint = str(_get("suggested_retention_offer", "") or "").strip()
        cat = str(_get("churn_risk_category", "") or "").strip()
        score = _safe_float(_get("churn_risk_score", 0))
        deposits = _safe_float(_get("total_deposits", 0))
        income = _safe_float(_get("income", 0))
        nprod = _safe_int(_get("num_products", 0))
        digital = _safe_float(_get("digital_engagement_score", 0.5))
        dslt = _safe_float(_get("days_since_last_txn", 0))
        persona = str(_get("persona", "") or "").strip()
        customer_id = str(_get("customer_id", "") or "").strip()
        dslt_pct = _safe_float(_get("days_since_last_txn_pct", 0.5))
        digital_pct = _safe_float(_get("digital_engagement_pct", 0.5))
        deposits_pct = _safe_float(_get("total_deposits_pct", 0.5))
        txn_count_pct = _safe_float(_get("txn_count_90d_pct", 0.5))
        volatility_pct = _safe_float(_get("txn_amount_cv_90d_pct", 0.5))
        product_depth_pct = _safe_float(_get("active_products_180d_pct", 0.5))

        # Stable selector for deterministic (non-random) but varied copy across customers/personas.
        selector = sum(ord(c) for c in f"{customer_id}|{persona}|{action}|{offer_hint}") % 3

        action_variants = {
            "Urgent_Personal_Outreach": [
                "Launch high-touch recovery in 48-72 hours via outbound call, with branch backup for unresolved cases.",
                "Assign immediate relationship-manager outreach and lock a same-week follow-up conversation.",
                "Prioritize direct human intervention first, then confirm with a branch-assisted completion path.",
            ],
            "Proactive_Offer": [
                "Queue this customer in the next proactive retention wave with a personalized incentive.",
                "Run a targeted outreach burst with a tailored value proposition tied to current account behavior.",
                "Use a proactive campaign touch with an offer matched to observed friction and churn drivers.",
            ],
            "Monitor_Closely": [
                "Keep in weekly monitoring with staged nudges before risk moves into High.",
                "Apply light-touch follow-ups and track changes in recency/engagement each week.",
                "Use low-intensity nurture plus threshold alerts for any sharp deterioration.",
            ],
            "Standard_Care": [
                "Continue lifecycle messaging and standard service cadence; no urgent intervention.",
                "Maintain baseline CRM journeys with periodic value reminders.",
                "Keep routine engagement playbooks active and review if risk indicators rise.",
            ],
        }
        fallback_action = action.replace("_", " ") if action else "Case-by-case review"
        action_text = action_variants.get(action, [fallback_action] * 3)[selector]

        offer_variants = {
            "Min_Balance_Waiver": [
                "Lead with fee relief or minimum-balance waiver to remove immediate friction.",
                "Position a balance-waiver style offer as a fast stabilizer for day-to-day usage.",
                "Use cost-relief messaging first (waiver/fee reduction) before cross-sell.",
            ],
            "Digital_Incentive": [
                "Offer a digital adoption incentive (app action, enrollment bonus, or digital-only rate bump).",
                "Anchor the pitch on digital convenience plus a small app-led incentive.",
                "Pair retention messaging with a digital behavior reward to lift engagement frequency.",
            ],
            "Product_Bundle_Offer": [
                "Propose a practical bundle (e.g., checking + savings) to deepen relationship breadth.",
                "Use a simple two-product bundle to improve stickiness and wallet share.",
                "Present a bundle path with clear value stacking rather than a single standalone offer.",
            ],
            "Reactivation_Campaign": [
                "Run a reactivation sequence with low-friction next steps and a short time-bound perk.",
                "Trigger win-back messaging focused on easy restart actions and immediate value.",
                "Use a reactivation flow that reduces effort and reinforces near-term benefit.",
            ],
            "Loyalty_Reward": [
                "Reinforce tenure with a loyalty-style value message or relationship pricing.",
                "Use recognition messaging to reaffirm value and prevent passive drift.",
                "Position a loyalty benefit to reward continuity and reduce switch intent.",
            ],
        }
        offer_text = ""
        if offer_hint:
            offer_text = offer_variants.get(
                offer_hint, [offer_hint.replace("_", " ")] * 3
            )[selector]

        signal_tags = []
        if dslt_pct >= 0.75:
            signal_tags.append("inactive")
        elif dslt_pct >= 0.55:
            signal_tags.append("slowing_activity")
        if digital_pct <= 0.30:
            signal_tags.append("low_digital")
        elif digital_pct >= 0.70:
            signal_tags.append("high_digital")
        if product_depth_pct <= 0.30:
            signal_tags.append("shallow_relationship")
        if deposits_pct <= 0.35:
            signal_tags.append("balance_pressure")
        if volatility_pct >= 0.70:
            signal_tags.append("volatile_spend")
        if txn_count_pct <= 0.30:
            signal_tags.append("low_recent_activity")
        if not signal_tags:
            signal_tags.append("mixed_signals")

        channel_step = (
            "Start with outbound call + branch follow-up."
            if cat in ("High", "Critical")
            else ("Lead with digital outreach first." if digital >= DIGITAL_MED else "Lead with advisor-assisted outreach.")
        )
        evidence = (
            f"deposits ${deposits:,.0f}, income ${income:,.0f}/yr, "
            f"{nprod} product(s), digital {digital:.0%}, ~{int(dslt)} days since activity"
        )
        cr = _get("churn_risk_reason", None)
        if cr and str(cr).strip():
            drivers = str(cr).strip()[:280]
        else:
            reason_snip = format_churn_risk_reason(row)
            if reason_snip:
                drivers = reason_snip[:280]
            else:
                drivers = "Composite churn model signals from recency, transaction trend, relationship depth, and channel behavior."

        parts = [
            f"Action plan: {action_text}",
            f"Offer angle: {offer_text}" if offer_text else "Offer angle: Tailor the message to current friction and account behavior.",
            f"Primary signals: {', '.join(signal_tags)} ({evidence}).",
            f"Execution: {channel_step}",
            f"Why now: {drivers}",
        ]
        return " | ".join(parts)
    except Exception:
        return (
            "Review transaction recency, balances vs income, product depth, and channel usage; "
            "align retention touch to highest-risk signal first."
        )


def format_persona_churn_summary(
    persona_name: str,
    segment_size: int,
    at_risk_count: int,
    high_count: int,
    critical_count: int,
    avg_score_segment: float,
    avg_score_at_risk: float,
    top_action: str,
    avg_deposits_at_risk: float,
    avg_digital_at_risk: float,
    avg_dslt_at_risk: float,
) -> str:
    """
    Segment-level churn narrative from aggregated customer data (not generic copy).
    """
    if segment_size <= 0:
        return ""
    pct = (100.0 * at_risk_count / segment_size) if segment_size else 0.0
    action_plain = (top_action or "").replace("_", " ").strip() or "mixed actions"

    risk_share = (critical_count / at_risk_count) if at_risk_count else 0.0
    persona_selector = sum(ord(c) for c in persona_name) % 3

    pressure_label = (
        "stabilization"
        if pct >= 10 or avg_score_at_risk >= 70
        else "containment"
        if pct >= 4 or avg_score_at_risk >= 55
        else "watchlist"
    )
    critical_tone = (
        "Critical-heavy"
        if risk_share >= 0.35
        else "High-risk skewed"
        if at_risk_count > 0
        else "No acute-risk concentration"
    )

    action_playbooks = {
        "Urgent Personal Outreach": [
            "Run call-first outreach with branch appointment slots reserved for unresolved members.",
            "Use RM-led callbacks with 72-hour follow-up SLA for at-risk accounts.",
            "Prioritize human-assisted recovery sequence before campaign automation.",
        ],
        "Proactive Offer": [
            "Batch proactive incentives by deposit tier and recent inactivity bands.",
            "Launch targeted offer waves with stronger value for high-risk pockets.",
            "Use segmented proactive offers and suppress generic broad blasts.",
        ],
        "Monitor Closely": [
            "Keep this segment in weekly monitoring with trigger-based journey upgrades.",
            "Apply low-friction nurture and escalate only when recency worsens.",
            "Use lightweight touchpoints and score-threshold alerts for escalation.",
        ],
        "Standard Care": [
            "Maintain lifecycle baseline and focus interventions on outlier accounts only.",
            "Continue routine engagement and monitor drift in recency/digital activity.",
            "Keep steady-state journeys with periodic value reminders.",
        ],
    }
    action_hint = action_playbooks.get(
        action_plain, [f"Bias plays toward: {action_plain}."] * 3
    )[persona_selector]

    return (
        f"Segment snapshot: {persona_name} ({segment_size} customers) | "
        f"At-risk members: {at_risk_count} ({pct:.1f}%; {high_count} High, {critical_count} Critical) | "
        f"Risk posture: {pressure_label}, {critical_tone}. "
        f"Scores: segment avg {avg_score_segment:.1f}/100; at-risk avg {avg_score_at_risk:.1f}/100. "
        f"At-risk profile: deposits ${avg_deposits_at_risk:,.0f}, digital {avg_digital_at_risk:.0%}, "
        f"~{avg_dslt_at_risk:.0f} days since activity. "
        f"Recommended campaign motion: {action_plain}. {action_hint}"
    )


def add_essential_churn_features(customers_df, transactions_df):
    """
    Add ONLY essential churn prediction features calculated from REAL transaction data
    
    Essential churn indicators:
    1. Days since last transaction (engagement recency)
    2. Transaction velocity change (activity trend)
    3. Balance health (financial stability)
    4. Product engagement (relationship depth)
    5. Digital engagement shift (channel preference change)
    
    Returns enriched customer dataframe with 5-10 churn features max
    """
    
    df = customers_df.copy()
    
    # ============================================================================
    # 1. ENGAGEMENT RECENCY: Days since last transaction (REAL)
    # ============================================================================
    
    if transactions_df is not None and len(transactions_df) > 0:
        # Get last transaction date per customer
        transactions_df = transactions_df.copy()
        transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'])
        transactions_df['amount'] = pd.to_numeric(transactions_df.get('amount', 0), errors='coerce').fillna(0.0)
        transactions_df['channel'] = transactions_df.get('channel', '').astype(str)
        transactions_df['transaction_type'] = transactions_df.get('transaction_type', '').astype(str)
        last_txn = transactions_df.groupby('customer_id')['transaction_date'].max()
        df['last_transaction_date'] = df['customer_id'].map(last_txn)
        
        # Calculate days since last activity
        latest_date = transactions_df['transaction_date'].max()
        df['days_since_last_txn'] = (latest_date - df['last_transaction_date']).dt.days
        
        # Transaction frequency trend (last 30 days vs previous 30 days)
        thirty_days_ago = latest_date - timedelta(days=30)
        sixty_days_ago = latest_date - timedelta(days=60)
        
        recent_txns = transactions_df[transactions_df['transaction_date'] >= thirty_days_ago].groupby('customer_id').size()
        previous_txns = transactions_df[
            (transactions_df['transaction_date'] >= sixty_days_ago) & 
            (transactions_df['transaction_date'] < thirty_days_ago)
        ].groupby('customer_id').size()
        
        df['recent_txn_count'] = df['customer_id'].map(recent_txns).fillna(0)
        df['previous_txn_count'] = df['customer_id'].map(previous_txns).fillna(0)
        df['txn_velocity_change'] = df['recent_txn_count'] - df['previous_txn_count']

        # ============================================================================
        # 1B. BEHAVIORAL TRANSACTION METRICS (REAL, WINDOWED)
        # ============================================================================
        latest_date = transactions_df['transaction_date'].max()
        win_90 = transactions_df[transactions_df['transaction_date'] >= (latest_date - timedelta(days=90))]
        win_180 = transactions_df[transactions_df['transaction_date'] >= (latest_date - timedelta(days=180))]

        # Volume + value profile
        c90 = win_90.groupby('customer_id')
        df['txn_count_90d'] = df['customer_id'].map(c90.size()).fillna(0.0)
        df['avg_txn_amount_90d'] = df['customer_id'].map(c90['amount'].mean()).fillna(0.0)
        df['median_txn_amount_90d'] = df['customer_id'].map(c90['amount'].median()).fillna(0.0)
        df['txn_amount_std_90d'] = df['customer_id'].map(c90['amount'].std()).fillna(0.0)
        df['txn_amount_cv_90d'] = df.apply(
            lambda r: _safe_div(r.get('txn_amount_std_90d', 0.0), r.get('avg_txn_amount_90d', 0.0), 0.0),
            axis=1
        )

        # Channel mix
        ch = win_90.copy()
        ch['is_mobile'] = ch['channel'].str.lower().isin(['mobile', 'app', 'online']).astype(int)
        ch['is_branch'] = ch['channel'].str.lower().eq('branch').astype(int)
        df['mobile_share_90d'] = df['customer_id'].map(ch.groupby('customer_id')['is_mobile'].mean()).fillna(0.0)
        df['branch_share_90d'] = df['customer_id'].map(ch.groupby('customer_id')['is_branch'].mean()).fillna(0.0)
        ch['weekday'] = ch['transaction_date'].dt.dayofweek
        ch['is_weekend'] = (ch['weekday'] >= 5).astype(int)
        df['weekend_txn_share_90d'] = df['customer_id'].map(ch.groupby('customer_id')['is_weekend'].mean()).fillna(0.0)

        # Product breadth + intensity
        df['active_products_180d'] = df['customer_id'].map(
            win_180.groupby('customer_id')['product_id'].nunique()
        ).fillna(0.0)

        # Flow mix by transaction type
        t90 = win_90.copy()
        tx_type = t90['transaction_type'].str.lower()
        inflow_mask = tx_type.str.contains('deposit|credit|account_opened|interest', regex=True)
        outflow_mask = tx_type.str.contains('withdraw|debit|purchase|fee|payment|transfer', regex=True)
        t90['inflow_amount'] = np.where(inflow_mask, t90['amount'], 0.0)
        t90['outflow_amount'] = np.where(outflow_mask, t90['amount'].abs(), 0.0)
        inflow_by_c = t90.groupby('customer_id')['inflow_amount'].sum()
        outflow_by_c = t90.groupby('customer_id')['outflow_amount'].sum()
        df['inflow_90d'] = df['customer_id'].map(inflow_by_c).fillna(0.0)
        df['outflow_90d'] = df['customer_id'].map(outflow_by_c).fillna(0.0)
        df['inflow_outflow_ratio_90d'] = df.apply(
            lambda r: _safe_div(r.get('inflow_90d', 0.0), r.get('outflow_90d', 0.0), 0.0), axis=1
        )
    else:
        # Transaction data unavailable  -  churn scores will use estimated defaults.
        # Real transaction data is required for accurate churn predictions.
        import logging as _logging
        _logging.getLogger(__name__).warning(
            "[ChurnFeatureGenerator] No transaction data  -  churn risk scores are "
            "estimated defaults, not computed from real activity."
        )
        df['days_since_last_txn'] = 30  # Assume average activity
        df['txn_velocity_change'] = 0
        df['recent_txn_count'] = 5
        df['previous_txn_count'] = 5
        df['txn_count_90d'] = 0.0
        df['avg_txn_amount_90d'] = 0.0
        df['median_txn_amount_90d'] = 0.0
        df['txn_amount_std_90d'] = 0.0
        df['txn_amount_cv_90d'] = 0.0
        df['mobile_share_90d'] = 0.0
        df['branch_share_90d'] = 0.0
        df['weekend_txn_share_90d'] = 0.0
        df['active_products_180d'] = 0.0
        df['inflow_90d'] = 0.0
        df['outflow_90d'] = 0.0
        df['inflow_outflow_ratio_90d'] = 0.0
    
    # ============================================================================
    # 2. BALANCE HEALTH: Financial stability indicators (REAL)
    # ============================================================================
    
    # Low balance risk flag
    df['balance_risk'] = (df['total_deposits'] < 1000).astype(int)
    
    # Balance trend indicator (if deposit history available)
    if 'total_deposits' in df.columns:
        # Estimate trend from current balance vs income ratio
        expected_deposits = df['income'] * 0.15  # Expected savings rate
        df['balance_below_expected'] = (df['total_deposits'] < expected_deposits).astype(int)
    else:
        df['balance_below_expected'] = 0
    
    # ============================================================================
    # 3. PRODUCT ENGAGEMENT: Relationship depth (REAL)
    # ============================================================================
    
    # Single product flag (higher churn risk)
    df['single_product_risk'] = (df['num_products'] == 1).astype(int)
    
    # Low product adoption (below average for tenure)
    if 'tenure_months' in df.columns:
        expected_products = np.clip(df['tenure_months'] / 24, 1, 3)  # 1 product per 2 years
        df['low_product_adoption'] = (df['num_products'] < expected_products).astype(int)
    else:
        df['low_product_adoption'] = 0
    
    # ============================================================================
    # 4. DIGITAL ENGAGEMENT: Channel preference shift (REAL)
    # ============================================================================
    
    if 'digital_engagement_score' in df.columns:
        df['digital_decline'] = (df['digital_engagement_score'] < DIGITAL_LOW).astype(int)
        df['branch_only_user'] = (df['digital_engagement_score'] < 0.1).astype(int)
    else:
        df['digital_decline'] = 0
        df['branch_only_user'] = 0
    
    # ============================================================================
    # 5. CREDIT HEALTH: Financial stress indicators (REAL)
    # ============================================================================
    
    if 'credit_score' in df.columns:
        # Poor credit risk (below 650 is subprime)
        df['credit_risk'] = (df['credit_score'] < 650).astype(int)
    else:
        df['credit_risk'] = 0
    
    # ============================================================================
    # CHURN RISK SCORE: Calculated from real metrics ONLY
    # ============================================================================
    
    # Weighted risk score (0-100)
    churn_score = (
        # Engagement factors (50%)
        (df['days_since_last_txn'] / 90) * 20 +  # 20 pts for inactivity
        np.where(df['txn_velocity_change'] < -3, 15, 0) +  # 15 pts for declining activity
        (df['recent_txn_count'] == 0).astype(int) * 15 +  # 15 pts for zero recent activity
        
        # Balance factors (25%)
        df['balance_risk'] * 15 +  # 15 pts for low balance
        df['balance_below_expected'] * 10 +  # 10 pts for below expected savings
        
        # Relationship factors (15%)
        df['single_product_risk'] * 10 +  # 10 pts for single product
        df['low_product_adoption'] * 5 +  # 5 pts for low product adoption
        
        # Channel factors (10%)
        df['digital_decline'] * 10  # 10 pts for digital decline
    )
    
    df['churn_risk_score'] = churn_score.clip(0, 100)
    
    # ============================================================================
    # CHURN RISK CATEGORY
    # ============================================================================
    
    df['churn_risk_category'] = pd.cut(
        df['churn_risk_score'],
        bins=[0, 25, 50, 75, 100],
        labels=['Low', 'Medium', 'High', 'Critical'],
        include_lowest=True,   # ensures score=0.0 maps to 'Low' not NaN
    ).astype(str)
    # pd.cut returns Categorical; convert and clean up any residual 'nan' strings
    df['churn_risk_category'] = df.apply(
        lambda r: (
            'Critical' if r['churn_risk_score'] >= 75 else
            'High'     if r['churn_risk_score'] >= 50 else
            'Medium'   if r['churn_risk_score'] >= 25 else
            'Low'
        ) if r['churn_risk_category'] in ('nan', '', 'NaN', None) else r['churn_risk_category'],
        axis=1
    )
    
    # ============================================================================
    # CHURN PROBABILITY (Logistic transformation)
    # ============================================================================
    
    # Convert risk score to probability (0-1)
    df['churn_probability'] = 1 / (1 + np.exp(-(df['churn_risk_score'] - 50) / 15))
    
    # ============================================================================
    # RETENTION RECOMMENDATIONS (Action-based on risk)
    # ============================================================================
    
    def get_retention_action(row):
        """Recommend action based on risk level"""
        if row['churn_risk_score'] >= 75:
            return 'Urgent_Personal_Outreach'
        elif row['churn_risk_score'] >= 50:
            return 'Proactive_Offer'
        elif row['churn_risk_score'] >= 25:
            return 'Monitor_Closely'
        else:
            return 'Standard_Care'
    
    df['recommended_retention_action'] = df.apply(get_retention_action, axis=1)
    
    # Suggested retention offers based on primary risk factor
    def get_retention_offer(row):
        """Suggest offer based on specific risk factors"""
        if row['balance_risk'] == 1:
            return 'Min_Balance_Waiver'
        elif row['digital_decline'] == 1:
            return 'Digital_Incentive'
        elif row['single_product_risk'] == 1:
            return 'Product_Bundle_Offer'
        elif row['days_since_last_txn'] > 60:
            return 'Reactivation_Campaign'
        else:
            return 'Loyalty_Reward'
    
    df['suggested_retention_offer'] = df.apply(get_retention_offer, axis=1)

    # ============================================================================
    # RELATIVE INTELLIGENCE METRICS (PERCENTILES)
    # ============================================================================
    def _pct_rank(series):
        s = pd.to_numeric(series, errors='coerce')
        return s.rank(pct=True, method='average').fillna(0.5)

    df['days_since_last_txn_pct'] = _pct_rank(df['days_since_last_txn'])
    df['digital_engagement_pct'] = _pct_rank(df['digital_engagement_score'])
    df['total_deposits_pct'] = _pct_rank(df['total_deposits'])
    df['txn_count_90d_pct'] = _pct_rank(df['txn_count_90d'])
    df['txn_amount_cv_90d_pct'] = _pct_rank(df['txn_amount_cv_90d'])
    df['active_products_180d_pct'] = _pct_rank(df['active_products_180d'])

    df["churn_risk_reason"] = df.apply(format_churn_risk_reason, axis=1)
    df["retention_strategy"] = df.apply(format_retention_strategy, axis=1)

    return df


def generate_churn_report(customers_with_churn):
    """Generate a summary report of churn analysis (essential metrics only)"""
    
    report = {
        'total_customers': len(customers_with_churn),
        'at_risk_customers': len(customers_with_churn[customers_with_churn['churn_risk_category'].isin(['High', 'Critical'])]),
        'avg_churn_risk_score': customers_with_churn['churn_risk_score'].mean(),
        'churn_by_category': customers_with_churn['churn_risk_category'].value_counts().to_dict(),
        'retention_actions_needed': customers_with_churn['recommended_retention_action'].value_counts().to_dict(),
        'top_churn_indicators': {
            'inactive_30_days': len(customers_with_churn[customers_with_churn['days_since_last_txn'] > 30]),
            'declining_activity': len(customers_with_churn[customers_with_churn['txn_velocity_change'] < -2]),
            'low_balance': customers_with_churn['balance_risk'].sum(),
            'single_product': customers_with_churn['single_product_risk'].sum(),
            'digital_decline': customers_with_churn['digital_decline'].sum()
        }
    }
    
    return report


if __name__ == "__main__":
    print("Essential Churn Feature Generator for Banking")
    print("Generates 5-10 core churn features from REAL transaction data")
    print("NO random generation - production-ready")
