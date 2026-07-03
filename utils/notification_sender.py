"""
Meridian Bank notification sender — email (SMTP) and SMS (Twilio).
All credentials are read from environment variables; nothing is hardcoded.
"""
import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ── SMTP config (set in .env) ────────────────────────────────────────────────
SMTP_HOST   = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT   = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER   = os.getenv("SMTP_USER", "")
SMTP_PASS   = os.getenv("SMTP_PASS", "")
SMTP_FROM   = os.getenv("SMTP_FROM", "") or SMTP_USER

# ── Twilio config (set in .env) ──────────────────────────────────────────────
TWILIO_ACCOUNT_SID  = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN   = os.getenv("TWILIO_AUTH_TOKEN", "")
# Normalize FROM number at load time — strip spaces, dashes, parens
TWILIO_FROM_NUMBER  = "".join(
    c for c in os.getenv("TWILIO_FROM_NUMBER", "") if c in "0123456789+#*"
)
TWILIO_COUNTRY_CODE = os.getenv("TWILIO_DEFAULT_COUNTRY_CODE", "1")


# ── Branded HTML email template ──────────────────────────────────────────────

def build_branded_email_html(
    customer_name: str,
    offer_name: str,
    headline_value: str,
    email_body: str,
    benefit_1: str = "",
    benefit_2: str = "",
    benefit_3: str = "",
    terms_summary: str = "",
    days_remaining: Optional[int] = None,
    persona_name: str = "",
) -> str:
    """Returns a Meridian Bank branded HTML email."""

    # Benefits rows
    benefits_rows = ""
    for b in filter(None, [benefit_1, benefit_2, benefit_3]):
        benefits_rows += (
            '<tr><td style="padding:7px 0;color:#374151;font-size:14px;">'
            '<span style="color:#1B4F8A;font-weight:700;margin-right:8px;">&#10003;</span>'
            f'{b}</td></tr>'
        )

    benefits_block = ""
    if benefits_rows:
        benefits_block = (
            '<table width="100%" cellpadding="0" cellspacing="0" '
            'style="background:#EFF6FF;border-radius:8px;padding:4px 16px;margin:0 0 24px;">'
            + benefits_rows
            + '</table>'
        )

    urgency_badge = ""
    if days_remaining and days_remaining < 30:
        urgency_badge = (
            '<div style="display:inline-block;background:#FEF3C7;border:1px solid #F59E0B;'
            'color:#92400E;padding:4px 14px;border-radius:20px;font-size:12px;'
            f'font-weight:700;margin-bottom:18px;">&#9200; Offer ends in {days_remaining} days</div><br>'
        )

    persona_label = ""
    if persona_name:
        persona_label = (
            f'<p style="color:#6B7280;font-size:12px;margin:0 0 6px;">'
            f'Personalized for: <strong>{persona_name}</strong></p>'
        )

    terms_block = ""
    if terms_summary:
        terms_block = (
            f'<p style="color:#9CA3AF;font-size:12px;line-height:1.6;margin:0 0 16px;">'
            f'{terms_summary}</p>'
        )

    # Replace [Name] / [name] placeholders in the LLM-generated body
    _name = customer_name.strip() if customer_name else ""
    clean_body = email_body
    if _name:
        import re as _re
        clean_body = _re.sub(r'\[Name\]', _name, clean_body, flags=_re.IGNORECASE)
    body_html = clean_body.replace("\n", "<br>")

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{offer_name}</title>
</head>
<body style="margin:0;padding:0;background:#F3F4F6;font-family:'Segoe UI',Arial,sans-serif;">

  <!-- ── Header ── -->
  <table width="100%" cellpadding="0" cellspacing="0" style="background:linear-gradient(135deg,#1B4F8A 0%,#2563EB 100%);">
    <tr>
      <td>
        <table width="600" cellpadding="0" cellspacing="0" align="center">
          <tr>
            <td style="padding:22px 32px 18px;">
              <span style="color:#FFFFFF;font-size:21px;font-weight:700;letter-spacing:-0.5px;">
                &#127970; Meridian Bank
              </span>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>

  <!-- ── Hero strip ── -->
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#1E3A5F;">
    <tr>
      <td>
        <table width="600" cellpadding="0" cellspacing="0" align="center">
          <tr>
            <td style="padding:18px 32px 20px;">
              <p style="color:#93C5FD;font-size:11px;text-transform:uppercase;
                         letter-spacing:1.2px;margin:0 0 5px;font-weight:600;">{offer_name}</p>
              <p style="color:#FFFFFF;font-size:30px;font-weight:800;margin:0;line-height:1.2;">
                {headline_value}
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>

  <!-- ── Body card ── -->
  <table width="600" cellpadding="0" cellspacing="0" align="center"
         style="background:#FFFFFF;box-shadow:0 2px 10px rgba(0,0,0,0.08);">
    <tr>
      <td style="padding:30px 32px 8px;">
        {persona_label}
        <p style="color:#111827;font-size:15px;line-height:1.75;margin:0 0 22px;">
          {body_html}
        </p>
        {urgency_badge}
        {benefits_block}
        <!-- CTA button -->
        <table cellpadding="0" cellspacing="0" style="margin:0 0 22px;">
          <tr>
            <td style="background:#1B4F8A;border-radius:6px;">
              <a href="#"
                 style="display:inline-block;padding:13px 30px;color:#FFFFFF;
                        font-weight:700;font-size:14px;text-decoration:none;
                        letter-spacing:0.3px;">
                Apply Now &rarr;
              </a>
            </td>
          </tr>
        </table>
        {terms_block}
      </td>
    </tr>
  </table>

  <!-- ── Divider strip ── -->
  <table width="600" cellpadding="0" cellspacing="0" align="center"
         style="background:#EFF6FF;border-top:3px solid #2563EB;">
    <tr>
      <td style="padding:12px 32px;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="color:#1D4ED8;font-size:11px;font-weight:600;">Checking</td>
            <td style="color:#1D4ED8;font-size:11px;font-weight:600;text-align:center;">Savings</td>
            <td style="color:#1D4ED8;font-size:11px;font-weight:600;text-align:center;">Credit Cards</td>
            <td style="color:#1D4ED8;font-size:11px;font-weight:600;text-align:right;">Loans</td>
          </tr>
        </table>
      </td>
    </tr>
  </table>

  <!-- ── Footer ── -->
  <table width="600" cellpadding="0" cellspacing="0" align="center">
    <tr>
      <td style="padding:18px 32px;text-align:center;">
        <p style="color:#9CA3AF;font-size:11px;line-height:1.7;margin:0;">
          <strong style="color:#6B7280;">Meridian Bank</strong> &bull; 123 Financial District &bull; Member FDIC<br>
          This offer is personalized based on your financial profile and is exclusively for you.<br>
          To unsubscribe, reply STOP or manage preferences in your online banking account.
        </p>
      </td>
    </tr>
  </table>

</body>
</html>"""


# ── Public send functions ────────────────────────────────────────────────────

def send_offer_email(
    to_email: str,
    customer_name: str,
    subject: str,
    email_body: str,
    offer_intelligence: Dict[str, Any],
    persona_name: str = "",
) -> Dict[str, Any]:
    """
    Send a Meridian Bank branded HTML offer email via SMTP.
    Reads SMTP_HOST/PORT/USER/PASS/FROM from environment.
    """
    if not SMTP_USER or not SMTP_PASS:
        raise ValueError(
            "SMTP credentials not configured. "
            "Set SMTP_USER and SMTP_PASS in your .env file."
        )

    # Extract offer details from the intelligence dict
    selected = offer_intelligence.get("selected_offer") or {}
    html_body = build_branded_email_html(
        customer_name=customer_name or "Valued Customer",
        offer_name=selected.get("offer_name") or offer_intelligence.get("offer_name") or "Special Offer",
        headline_value=selected.get("headline_value") or offer_intelligence.get("headline_value") or "",
        email_body=email_body,
        benefit_1=selected.get("content_benefit_1") or "",
        benefit_2=selected.get("content_benefit_2") or "",
        benefit_3=selected.get("content_benefit_3") or "",
        terms_summary=selected.get("terms_summary") or "",
        days_remaining=selected.get("days_remaining"),
        persona_name=persona_name,
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Meridian Bank <{SMTP_FROM}>"
    msg["To"]      = to_email
    msg["X-Mailer"] = "Meridian Bank NBA Platform"

    msg.attach(MIMEText(email_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_FROM, to_email, msg.as_string())

    logger.info(f"[NOTIFY] ✉️  Email sent → {to_email} | subject='{subject}'")
    return {"success": True, "to": to_email, "channel": "email"}


def send_offer_sms(
    to_phone: str,
    sms_text: str,
    customer_name: str = "",
) -> Dict[str, Any]:
    """
    Send a personalized offer SMS via the Twilio Messages REST API.
    Uses requests directly so verify=False is applied with no interceptor chain.
    Reads TWILIO_ACCOUNT_SID/AUTH_TOKEN/FROM_NUMBER/SSL_VERIFY from environment.
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        raise ValueError(
            "Twilio credentials not configured. "
            "Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in your .env file."
        )
    if not TWILIO_FROM_NUMBER:
        raise ValueError("TWILIO_FROM_NUMBER not configured in .env file.")

    import requests as _req
    import urllib3

    # Normalize phone number
    phone = (
        to_phone.strip()
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )
    if not phone.startswith("+"):
        phone = f"+{TWILIO_COUNTRY_CODE}{phone.lstrip('0')}"

    ssl_verify = os.getenv("TWILIO_SSL_VERIFY", "true").lower() != "false"
    if not ssl_verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        logger.warning("[NOTIFY] Twilio SSL verification disabled (TWILIO_SSL_VERIFY=false)")

    url = (
        f"https://api.twilio.com/2010-04-01/Accounts"
        f"/{TWILIO_ACCOUNT_SID}/Messages.json"
    )
    try:
        resp = _req.post(
            url,
            data={
                "Body": sms_text[:160],
                "From": TWILIO_FROM_NUMBER,
                "To": phone,
            },
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            verify=ssl_verify,
            timeout=15,
        )
    except Exception as req_err:
        logger.error(f"[NOTIFY] Twilio request error: {req_err}")
        raise RuntimeError(f"Twilio request failed: {req_err}") from req_err

    if resp.status_code not in (200, 201):
        try:
            err_body = resp.json()
            err_msg = err_body.get("message", "") or resp.text
            err_code = err_body.get("code", 0)
        except Exception:
            err_msg = resp.text or resp.reason
            err_code = 0

        # Make error messages actionable for common Twilio issues
        if err_code == 21606 or "is not a Twilio phone number" in err_msg:
            err_msg = (
                f"{err_msg} — TWILIO_FROM_NUMBER ({TWILIO_FROM_NUMBER}) must be a "
                "Twilio-provisioned number. Check Twilio Console › Phone Numbers › Active Numbers."
            )
        elif "country mismatch" in err_msg.lower() or err_code == 21408:
            err_msg = (
                f"{err_msg} — Enable SMS for the destination country in "
                "Twilio Console › Messaging › Settings › Geo Permissions."
            )
        elif err_code == 21610 or "unsubscribed recipient" in err_msg.lower():
            err_msg = f"{err_msg} — Recipient has opted out of SMS from this number."
        elif err_code in (21211, 21614):
            err_msg = (
                f"{err_msg} — TO number ({phone}) is invalid or not SMS-capable. "
                "Verify number format and add country code (+91 for India, +1 for US)."
            )
        elif err_code == 20003 or "authenticate" in err_msg.lower():
            err_msg = f"{err_msg} — Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env."
        elif "trial" in err_msg.lower() or "verified" in err_msg.lower():
            err_msg = (
                f"{err_msg} — Twilio trial accounts can only SMS to Verified Caller IDs. "
                "Add the recipient number at Twilio Console › Verified Caller IDs."
            )

        logger.error(f"[NOTIFY] Twilio API {resp.status_code} (code {err_code}): {err_msg}")
        raise RuntimeError(f"SMS failed ({resp.status_code}): {err_msg}")

    data = resp.json()
    logger.info(
        f"[NOTIFY] 📱 SMS sent → {phone} | "
        f"sid={data.get('sid')} | status={data.get('status')}"
    )
    return {
        "success": True,
        "to": phone,
        "sid": data.get("sid", ""),
        "status": data.get("status", ""),
        "channel": "sms",
    }
