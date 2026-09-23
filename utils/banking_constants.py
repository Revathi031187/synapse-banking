"""
Shared banking constants  -  single source of truth for thresholds used across
Agent C, 12-factor scorer, churn generator, and MTA engine.

Import pattern:
    from utils.banking_constants import DIGITAL_HIGH, DIGITAL_MED, DIGITAL_LOW, CHANNELS, CHANNEL_LABELS
"""

# ── MTA / delivery channels ──────────────────────────────────────────────────
# Ordered by typical reach priority: digital first, physical last.
CHANNELS = ["in_app", "email", "sms", "direct_mail", "branch", "outbound_call", "web"]

CHANNEL_LABELS = {
    "in_app":        "In-App",
    "email":         "Email",
    "sms":           "SMS",
    "direct_mail":   "Direct Mail",
    "branch":        "Branch",
    "outbound_call": "Outbound Call",
    "web":           "Web",
}

# Channels that exist in MTA touchpoint history CSV (journey data available).
# outbound_call and web are tracked for fatigue but have no Markov journey data.
MTA_JOURNEY_CHANNELS = ["in_app", "email", "sms", "direct_mail", "branch"]

# ── Digital engagement thresholds ────────────────────────────────────────────
# Used consistently across Agent C, 12-factor scorer, churn generator, MTA engine.
#
#   Score ≥ DIGITAL_HIGH  →  digital-first customer (in-app / web preferred)
#   Score ≥ DIGITAL_MED   →  hybrid customer (email works well)
#   Score <  DIGITAL_MED  →  low digital / branch-first customer
#   Score <  DIGITAL_LOW  →  branch-only, digital outreach counter-productive
#
DIGITAL_HIGH = 0.65   # threshold for "high digital engagement"
DIGITAL_MED  = 0.40   # threshold for "moderate digital engagement"
DIGITAL_LOW  = 0.20   # threshold for "low digital / branch-first"

# Alias used by 12-factor scorer channel fit logic
DIGITAL_REQUIRED_HIGH = DIGITAL_HIGH   # replaces the scattered 0.7 / 0.65
DIGITAL_REQUIRED_LOW  = DIGITAL_LOW    # replaces the scattered 0.3

# ── Persona names ────────────────────────────────────────────────────────────
PERSONAS = [
    "Digital Native",
    "Wealth Builder",
    "Everyday Essential",
    "Retiree Anchor",
    "At-Risk Saver",
]

# ── MTA fallback attribution weights per persona ─────────────────────────────
# Used by MTAEngine._fallback_attribution() when journey data is insufficient.
# Weights must sum to 1.0 per persona. web and outbound_call share residual weight.
MTA_FALLBACK_ATTRIBUTION = {
    "Digital Native": {
        "in_app": 0.55, "email": 0.16, "sms": 0.09,
        "direct_mail": 0.03, "branch": 0.03, "web": 0.10, "outbound_call": 0.04,
    },
    "Wealth Builder": {
        "in_app": 0.22, "email": 0.32, "sms": 0.07,
        "direct_mail": 0.14, "branch": 0.10, "web": 0.08, "outbound_call": 0.07,
    },
    "Everyday Essential": {
        "in_app": 0.28, "email": 0.30, "sms": 0.12,
        "direct_mail": 0.09, "branch": 0.06, "web": 0.10, "outbound_call": 0.05,
    },
    "Retiree Anchor": {
        "in_app": 0.04, "email": 0.18, "sms": 0.05,
        "direct_mail": 0.27, "branch": 0.32, "web": 0.03, "outbound_call": 0.11,
    },
    "At-Risk Saver": {
        "in_app": 0.18, "email": 0.22, "sms": 0.26,
        "direct_mail": 0.08, "branch": 0.06, "web": 0.08, "outbound_call": 0.12,
    },
}

MTA_FALLBACK_ATTRIBUTION_DEFAULT = {
    "in_app": 0.26, "email": 0.24, "sms": 0.14,
    "direct_mail": 0.12, "branch": 0.09, "web": 0.09, "outbound_call": 0.06,
}

# ── Fatigue thresholds ────────────────────────────────────────────────────────
FATIGUE_CONSECUTIVE_THRESHOLD = 3   # consecutive no-opens to flag fatigue
FATIGUE_TOTAL_SENDS_MIN       = 3   # minimum sends before fatigue is evaluated
MTA_MIN_PERSONAL_SENDS        = 3   # minimum sends to trust personal signal over segment

# ── Agent D stack limits ──────────────────────────────────────────────────────
MAX_LIVE_STACK      = 12
MAX_PER_CATEGORY    = 3
MAX_ABANDONED_SLOTS = 2
MAX_SAVED_SLOTS     = 2
DEPRIORITIZE_MIN_SHOWS = 3
