"""
Adobe Experience Platform (AEP) activation client.

Uses customer-supplied credentials (client id, org id, access token, sandbox,
tenant id) to validate access and provision a personalization field group +
schema in the Schema Registry. This is the real network call behind the
"Activation" tab's Adobe Experience Platform connector — failures surface the
raw Adobe API error back to the caller so the UI can show exactly what went
wrong (status, title, detail, registry request id, sub-errors).
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
import urllib3

from utils.logger import get_logger

# Windows dev boxes commonly sit behind a corporate TLS-inspecting proxy whose
# root CA isn't in the local trust store, which makes verified HTTPS calls to
# platform.adobe.io fail with CERTIFICATE_VERIFY_FAILED. Same workaround used
# elsewhere in this codebase (utils/together_ai.py, utils/claude_client.py).
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = get_logger("AdobeAEP")

SCHEMA_REGISTRY_BASE = "https://platform.adobe.io/data/foundation/schemaregistry"
PROFILE_CLASS_REF = "https://ns.adobe.com/xdm/context/profile"
REQUEST_TIMEOUT = 20  # seconds


class AdobeAEPError(Exception):
    """Raised when a call to Adobe Experience Platform fails, carrying the full
    Adobe error payload so the caller can render a detailed diagnostic."""

    def __init__(self, step: str, response: Optional[requests.Response] = None, message: Optional[str] = None):
        self.step = step
        self.status: Optional[int] = response.status_code if response is not None else None
        self.title = "Request Failed"
        self.detail = message or "Unknown error"
        self.type: Optional[str] = None
        self.registry_request_id: Optional[str] = None
        self.sub_errors: List[Any] = []
        self.raw_response: Optional[Dict[str, Any]] = None
        self.timestamp = datetime.now(timezone.utc).isoformat()

        if response is not None:
            try:
                body = response.json()
            except ValueError:
                body = {"detail": response.text[:2000]}
            self.raw_response = body
            self.detail = body.get("detail") or body.get("message") or self.detail
            self.title = body.get("title") or self.title
            self.type = body.get("type")
            report = body.get("report") or {}
            self.registry_request_id = (
                report.get("registryRequestId")
                or report.get("requestId")
                or response.headers.get("x-request-id")
            )
            self.sub_errors = body.get("errors") or report.get("sub-errors") or []
            self.timestamp = report.get("timestamp") or self.timestamp

        super().__init__(self.detail)


def _headers(access_token: str, client_id: str, org_id: str, sandbox: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "x-api-key": client_id,
        "x-gw-ims-org-id": org_id,
        "x-sandbox-name": sandbox,
        "Content-Type": "application/json",
    }


def _field_group_body(tenant_id: str, title: str) -> Dict[str, Any]:
    return {
        "type": "object",
        "title": title,
        "description": "Fields written by the NBA Personalization Agent activation pipeline.",
        "meta:intendedToExtend": [PROFILE_CLASS_REF],
        "definitions": {
            "customFields": {
                "type": "object",
                "properties": {
                    f"_{tenant_id}": {
                        "type": "object",
                        "properties": {
                            "nbaPersona": {"type": "string", "title": "NBA Persona"},
                            "recommendedProductId": {"type": "string", "title": "Recommended Product ID"},
                            "offerScore": {"type": "number", "title": "Offer Score"},
                            "lastActivationDate": {
                                "type": "string",
                                "format": "date-time",
                                "title": "Last Activation Date",
                            },
                        },
                    }
                },
            }
        },
        # A field group's allOf may only reference other field groups (via local $refs) —
        # meta:intendedToExtend is what declares which class(es) it's compatible with.
        # Referencing the Profile class directly here is rejected as XDM-1507 ("classes"
        # aren't allowed in a field group's allOf).
        "allOf": [{"$ref": "#/definitions/customFields"}],
    }


def _find_by_title(kind: str, title: str, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Look up an existing tenant field group/schema by exact title. Returns the
    id-only listing entry ({"$id": ..., "title": ..., "version": ...}) if found,
    else None. Used to make activation idempotent — Adobe rejects a second
    create with the same title (XDM-1521 "Title not unique")."""
    try:
        resp = requests.get(
            f"{SCHEMA_REGISTRY_BASE}/tenant/{kind}",
            headers={**headers, "Accept": "application/vnd.adobe.xed-id+json"},
            params={"property": f"title=={title}"},
            timeout=REQUEST_TIMEOUT,
            verify=False,
        )
    except requests.RequestException:
        return None

    if resp.status_code >= 400:
        return None

    results = (resp.json() or {}).get("results") or []
    return results[0] if results else None


def _schema_body(title: str, field_group_id: str) -> Dict[str, Any]:
    return {
        "type": "object",
        "title": title,
        "description": "Schema representing customers activated from the NBA Personalization Agent.",
        "allOf": [{"$ref": PROFILE_CLASS_REF}, {"$ref": field_group_id}],
        "meta:class": PROFILE_CLASS_REF,
    }


DEFAULT_SCHEMA_NAME = "Synapse-Connection-Test-Schema"


def validate_and_activate(
    client_id: str,
    org_id: str,
    access_token: str,
    sandbox: str,
    tenant_id: str,
    industry: str = "banking",
    schema_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validates the supplied AEP credentials, then provisions a field group and a
    schema describing the personalization attributes this platform activates
    into the customer's Adobe Experience Platform sandbox.

    Raises AdobeAEPError (with full diagnostic detail) on any failure.
    """
    label = "F&M Bank" if industry == "banking" else "Academy Sports"
    headers = _headers(access_token, client_id, org_id, sandbox)

    # Step 1 — validate credentials with a cheap, read-only call
    try:
        resp = requests.get(
            f"{SCHEMA_REGISTRY_BASE}/tenant/schemas",
            headers={**headers, "Accept": "application/vnd.adobe.xed-id+json"},
            params={"limit": 1},
            timeout=REQUEST_TIMEOUT,
            verify=False,
        )
    except requests.RequestException as e:
        raise AdobeAEPError(step="auth_validation", message=f"Could not reach Adobe Experience Platform: {e}")

    if resp.status_code >= 400:
        raise AdobeAEPError(step="auth_validation", response=resp)

    # Step 2 — create the field group holding this platform's personalization attributes
    # (or reuse it if a prior activation already created one — titles must be unique per tenant)
    fg_title = f"{label} NBA Personalization Attributes"
    field_group = _find_by_title("fieldgroups", fg_title, headers)
    if field_group is None:
        try:
            resp = requests.post(
                f"{SCHEMA_REGISTRY_BASE}/tenant/fieldgroups",
                headers=headers,
                json=_field_group_body(tenant_id, fg_title),
                timeout=REQUEST_TIMEOUT,
                verify=False,
            )
        except requests.RequestException as e:
            raise AdobeAEPError(step="fieldgroup_creation", message=f"Could not reach Adobe Experience Platform: {e}")

        if resp.status_code >= 400:
            raise AdobeAEPError(step="fieldgroup_creation", response=resp)

        field_group = resp.json()

    field_group_id = field_group.get("$id")

    # Step 3 — assemble a schema on top of the Individual Profile class + new field group
    # (or reuse it if a prior activation already created one)
    schema_title = (schema_name or "").strip() or DEFAULT_SCHEMA_NAME
    schema = _find_by_title("schemas", schema_title, headers)
    if schema is None:
        try:
            resp = requests.post(
                f"{SCHEMA_REGISTRY_BASE}/tenant/schemas",
                headers=headers,
                json=_schema_body(schema_title, field_group_id),
                timeout=REQUEST_TIMEOUT,
                verify=False,
            )
        except requests.RequestException as e:
            raise AdobeAEPError(step="schema_creation", message=f"Could not reach Adobe Experience Platform: {e}")

        if resp.status_code >= 400:
            raise AdobeAEPError(step="schema_creation", response=resp)

        schema = resp.json()

    return {
        "schemaId": schema.get("$id"),
        "schemaTitle": schema.get("title", schema_title),
        "fieldGroupId": field_group_id,
        "fieldGroupTitle": field_group.get("title", fg_title),
        "tenantId": tenant_id,
        "sandbox": sandbox,
        "imsOrg": org_id,
        "connectedAt": datetime.now(timezone.utc).isoformat(),
    }
