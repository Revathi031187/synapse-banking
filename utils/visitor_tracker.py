"""
Meridian Bank anonymous visitor tracking — SQLite-backed, cookie-based.
Three tables: visitor_sessions, visitor_interactions, visitor_personas.
Auto-creates data/visitor_tracking.db on first import.
"""
import hashlib
import json
import logging
import math
import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_DB_PATH = Path(__file__).parent.parent / "data" / "visitor_tracking.db"

# ── Persona inference: product category → persona label ─────────────────────

_CATEGORY_PERSONA: Dict[str, str] = {
    # Wealth Builder
    "Mortgage":        "Wealth Builder",
    "Home Equity":     "Wealth Builder",
    "HELOC":           "Wealth Builder",
    "Investment":      "Wealth Builder",
    "Business":        "Wealth Builder",
    # Retiree Anchor
    "CD":              "Retiree Anchor",
    "Money Market":    "Retiree Anchor",
    "Savings":         "Retiree Anchor",
    # Everyday Essential
    "Checking":        "Everyday Essential",
    "Personal":        "Everyday Essential",
    "Debit":           "Everyday Essential",
    # Digital Native
    "Credit":          "Digital Native",
    "Credit Card":     "Digital Native",
    "Rewards":         "Digital Native",
    "Premium":         "Digital Native",
    # At-Risk Saver (fallback)
    "Other":           "At-Risk Saver",
}

_UTM_TO_CHANNEL: Dict[str, str] = {
    "email":        "email",
    "sms":          "sms",
    "inapp":        "in_app",
    "in_app":       "in_app",
    "direct_mail":  "direct_mail",
    "directmail":   "direct_mail",
    "branch":       "branch",
    "web":          "web",
}


# ── DB init ──────────────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS visitor_sessions (
                session_id        TEXT PRIMARY KEY,
                visitor_id        TEXT NOT NULL,
                visit_number      INTEGER DEFAULT 1,
                visit_timestamp   TEXT,
                referrer_channel  TEXT,
                utm_campaign      TEXT,
                device_type       TEXT,
                time_on_page      INTEGER DEFAULT 0,
                scroll_depth      REAL DEFAULT 0.0,
                cta_clicked       TEXT,
                converted         INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS visitor_interactions (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                visitor_id        TEXT NOT NULL,
                session_id        TEXT NOT NULL,
                product_id        TEXT,
                product_category  TEXT,
                interaction_type  TEXT,
                dwell_time        INTEGER DEFAULT 0,
                timestamp         TEXT,
                context           TEXT
            );

            CREATE TABLE IF NOT EXISTS visitor_personas (
                visitor_id         TEXT PRIMARY KEY,
                inferred_persona   TEXT,
                confidence         REAL DEFAULT 0.0,
                top_category       TEXT,
                preferred_channel  TEXT,
                first_seen         TEXT,
                last_seen          TEXT,
                total_visits       INTEGER DEFAULT 1,
                mapped_customer_id TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_vi_visitor ON visitor_interactions(visitor_id);
            CREATE INDEX IF NOT EXISTS idx_vs_visitor ON visitor_sessions(visitor_id);

            CREATE TABLE IF NOT EXISTS visitor_registrations (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                visitor_id     TEXT NOT NULL,
                first_name     TEXT NOT NULL,
                email          TEXT NOT NULL,
                phone          TEXT,
                consent_given  INTEGER DEFAULT 0,
                registered_at  TEXT,
                password_hash  TEXT,
                password_salt  TEXT,
                UNIQUE(email)
            );
            CREATE INDEX IF NOT EXISTS idx_vr_email ON visitor_registrations(email);
        """)
    # Migrate: add password columns to existing tables that predate this schema
    with _connect() as conn:
        for col, definition in [("password_hash", "TEXT"), ("password_salt", "TEXT")]:
            try:
                conn.execute(f"ALTER TABLE visitor_registrations ADD COLUMN {col} {definition}")
            except Exception:
                pass  # column already exists
    logger.info("[VisitorTracker] DB ready at %s", _DB_PATH)


# Auto-init on import
try:
    init_db()
except Exception as _e:
    logger.warning("[VisitorTracker] DB init failed: %s", _e)


# ── Visit registration ───────────────────────────────────────────────────────

def register_visit(
    visitor_id: Optional[str],
    referrer_channel: Optional[str],
    utm_campaign: Optional[str],
    device_type: Optional[str],
) -> Dict:
    """
    Register a visit. Generates visitor_id if absent.
    Returns { session_id, visitor_id, visit_number, personalized }.
    """
    if not visitor_id:
        visitor_id = str(uuid.uuid4())

    channel = _UTM_TO_CHANNEL.get((referrer_channel or "").lower(), referrer_channel or "web")
    now = datetime.now(timezone.utc).isoformat()
    session_id = str(uuid.uuid4())

    with _connect() as conn:
        # Upsert visitor_personas
        row = conn.execute(
            "SELECT total_visits, inferred_persona FROM visitor_personas WHERE visitor_id = ?",
            (visitor_id,)
        ).fetchone()

        if row:
            visit_number = int(row["total_visits"]) + 1
            conn.execute(
                "UPDATE visitor_personas SET total_visits = ?, last_seen = ? WHERE visitor_id = ?",
                (visit_number, now, visitor_id)
            )
        else:
            visit_number = 1
            conn.execute(
                """INSERT INTO visitor_personas
                   (visitor_id, preferred_channel, first_seen, last_seen, total_visits)
                   VALUES (?, ?, ?, ?, 1)""",
                (visitor_id, channel, now, now)
            )

        # Insert session
        conn.execute(
            """INSERT INTO visitor_sessions
               (session_id, visitor_id, visit_number, visit_timestamp, referrer_channel, utm_campaign, device_type)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (session_id, visitor_id, visit_number, now, channel, utm_campaign, device_type)
        )

    return {
        "session_id":  session_id,
        "visitor_id":  visitor_id,
        "visit_number": visit_number,
        "personalized": visit_number >= 2,
    }


# ── Interaction logging ──────────────────────────────────────────────────────

def log_interaction(
    visitor_id: str,
    session_id: str,
    product_id: Optional[str],
    product_category: Optional[str],
    interaction_type: str,
    dwell_time: int,
    context: Optional[Dict] = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """INSERT INTO visitor_interactions
               (visitor_id, session_id, product_id, product_category, interaction_type, dwell_time, timestamp, context)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                visitor_id, session_id, product_id, product_category,
                interaction_type, dwell_time, now,
                json.dumps(context) if context else None,
            )
        )
    # Re-infer persona after each interaction
    try:
        _update_persona(visitor_id)
    except Exception as e:
        logger.debug("[VisitorTracker] Persona update skipped: %s", e)


def _update_persona(visitor_id: str) -> None:
    """Recompute and persist inferred persona from total dwell by category."""
    persona, confidence, top_cat = infer_persona(visitor_id)
    if persona:
        with _connect() as conn:
            conn.execute(
                """UPDATE visitor_personas
                   SET inferred_persona = ?, confidence = ?, top_category = ?
                   WHERE visitor_id = ?""",
                (persona, confidence, top_cat, visitor_id)
            )


# ── Persona inference ────────────────────────────────────────────────────────

def infer_persona(visitor_id: str) -> Tuple[Optional[str], float, Optional[str]]:
    """
    Aggregate total dwell_time by product_category for this visitor.
    Maps top category to a persona label. Returns (persona, confidence, top_category).
    Low-engagement visitors fall back to "At-Risk Saver".
    """
    with _connect() as conn:
        rows = conn.execute(
            """SELECT product_category, SUM(dwell_time) as total_dwell
               FROM visitor_interactions
               WHERE visitor_id = ? AND product_category IS NOT NULL
               GROUP BY product_category
               ORDER BY total_dwell DESC""",
            (visitor_id,)
        ).fetchall()

    if not rows:
        return None, 0.0, None

    total_dwell_all = sum(r["total_dwell"] for r in rows)
    if total_dwell_all < 500:  # less than 0.5 s total — not enough signal
        return "At-Risk Saver", 0.2, None

    top = rows[0]
    top_cat = top["product_category"]
    top_dwell = top["total_dwell"]
    confidence = min(1.0, top_dwell / max(total_dwell_all, 1))

    persona = _CATEGORY_PERSONA.get(top_cat, "Everyday Essential")

    # Multi-card click pattern → Digital Native override
    with _connect() as conn:
        click_count = conn.execute(
            """SELECT COUNT(*) as cnt FROM visitor_interactions
               WHERE visitor_id = ? AND interaction_type IN ('card_click', 'cta_click')""",
            (visitor_id,)
        ).fetchone()["cnt"]

    if click_count >= 4 and confidence < 0.6:
        persona = "Digital Native"
        confidence = max(confidence, 0.5)

    return persona, round(confidence, 3), top_cat


# ── Visitor persona fetch ────────────────────────────────────────────────────

def get_visitor_persona(visitor_id: str) -> Optional[Dict]:
    """Return visitor_personas row as dict, or None if visitor unknown."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM visitor_personas WHERE visitor_id = ?",
            (visitor_id,)
        ).fetchone()
    return dict(row) if row else None


# ── Session update ───────────────────────────────────────────────────────────

def update_session(
    session_id: str,
    time_on_page: Optional[int] = None,
    scroll_depth: Optional[float] = None,
    cta_clicked: Optional[str] = None,
    converted: Optional[bool] = None,
) -> None:
    parts, vals = [], []
    if time_on_page is not None:
        parts.append("time_on_page = ?"); vals.append(time_on_page)
    if scroll_depth is not None:
        parts.append("scroll_depth = ?"); vals.append(round(scroll_depth, 3))
    if cta_clicked is not None:
        parts.append("cta_clicked = ?"); vals.append(cta_clicked)
    if converted is not None:
        parts.append("converted = ?"); vals.append(1 if converted else 0)
    if not parts:
        return
    vals.append(session_id)
    with _connect() as conn:
        conn.execute(
            f"UPDATE visitor_sessions SET {', '.join(parts)} WHERE session_id = ?",
            vals
        )


# ── Identify (link visitor → customer) ──────────────────────────────────────

def link_visitor_to_customer(visitor_id: str, customer_id: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE visitor_personas SET mapped_customer_id = ? WHERE visitor_id = ?",
            (customer_id, visitor_id)
        )


# ── Analytics helpers ────────────────────────────────────────────────────────

def get_visitor_sessions(visitor_id: str) -> List[Dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM visitor_sessions WHERE visitor_id = ? ORDER BY visit_timestamp",
            (visitor_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_visitor_interactions(visitor_id: str, limit: int = 100) -> List[Dict]:
    with _connect() as conn:
        rows = conn.execute(
            """SELECT * FROM visitor_interactions
               WHERE visitor_id = ? ORDER BY timestamp DESC LIMIT ?""",
            (visitor_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Visitor registration (name / email / phone capture) ──────────────────────

# ── Password helpers ─────────────────────────────────────────────────────────

def _hash_password(password: str, salt: Optional[str] = None) -> tuple:
    """Return (hash_hex, salt_hex) using PBKDF2-HMAC-SHA256."""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations=200_000
    )
    return dk.hex(), salt


def _verify_password(password: str, stored_hash: str, salt: str) -> bool:
    computed, _ = _hash_password(password, salt)
    return secrets.compare_digest(computed, stored_hash)


def register_visitor(
    visitor_id: str,
    first_name: str,
    email: str,
    phone: Optional[str],
    consent: bool,
    password: Optional[str] = None,
) -> Dict:
    """
    Save visitor identity details. Hashes password if provided.
    Returns { ok, already_existed }.
    """
    now = datetime.now(timezone.utc).isoformat()
    pw_hash, pw_salt = (_hash_password(password) if password else (None, None))
    with _connect() as conn:
        existing = conn.execute(
            "SELECT id FROM visitor_registrations WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
        already_existed = existing is not None
        conn.execute(
            """INSERT INTO visitor_registrations
               (visitor_id, first_name, email, phone, consent_given, registered_at,
                password_hash, password_salt)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(email) DO UPDATE SET
                 visitor_id    = excluded.visitor_id,
                 first_name    = excluded.first_name,
                 phone         = excluded.phone,
                 consent_given = excluded.consent_given,
                 registered_at = excluded.registered_at,
                 password_hash = COALESCE(excluded.password_hash, visitor_registrations.password_hash),
                 password_salt = COALESCE(excluded.password_salt, visitor_registrations.password_salt)""",
            (visitor_id, first_name.strip(), email.strip().lower(),
             phone or None, 1 if consent else 0, now, pw_hash, pw_salt)
        )
    return {"ok": True, "already_existed": already_existed}


def signin_visitor(email: str, password: str) -> Dict:
    """
    Authenticate a registered visitor by email + password.
    Returns { ok, visitor_id, first_name, inferred_persona } on success,
    { ok: False, error: str } on failure.
    """
    with _connect() as conn:
        row = conn.execute(
            """SELECT vr.visitor_id, vr.first_name, vr.password_hash, vr.password_salt,
                      vp.inferred_persona
               FROM visitor_registrations vr
               LEFT JOIN visitor_personas vp ON vp.visitor_id = vr.visitor_id
               WHERE vr.email = ?""",
            (email.strip().lower(),)
        ).fetchone()

    if not row:
        return {"ok": False, "error": "No account found with that email address."}

    pw_hash = row["password_hash"]
    pw_salt = row["password_salt"]

    if not pw_hash or not pw_salt:
        # Account was registered before password support — accept any password
        # and store the new hash now
        new_hash, new_salt = _hash_password(password)
        with _connect() as conn:
            conn.execute(
                "UPDATE visitor_registrations SET password_hash=?, password_salt=? WHERE visitor_id=?",
                (new_hash, new_salt, row["visitor_id"])
            )
    elif not _verify_password(password, pw_hash, pw_salt):
        return {"ok": False, "error": "Incorrect password. Please try again."}

    return {
        "ok": True,
        "visitor_id":  row["visitor_id"],
        "first_name":  row["first_name"],
        "persona":     row["inferred_persona"],
    }


def lookup_by_email(email: str) -> Optional[Dict]:
    """
    Cross-device sign-in: find a registered visitor by email.
    Returns { visitor_id, first_name, inferred_persona } or None if not found.
    """
    with _connect() as conn:
        row = conn.execute(
            """SELECT vr.visitor_id, vr.first_name, vp.inferred_persona
               FROM visitor_registrations vr
               LEFT JOIN visitor_personas vp ON vp.visitor_id = vr.visitor_id
               WHERE vr.email = ?""",
            (email.strip().lower(),)
        ).fetchone()
    return dict(row) if row else None


def get_registration(visitor_id: str) -> Optional[Dict]:
    """
    Return registration details for a visitor_id (used by personalize endpoint
    to include first_name in the personalized hero response).
    """
    with _connect() as conn:
        row = conn.execute(
            "SELECT first_name, email, phone FROM visitor_registrations WHERE visitor_id = ?",
            (visitor_id,)
        ).fetchone()
    return dict(row) if row else None
