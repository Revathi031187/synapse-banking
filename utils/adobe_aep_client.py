"""
Adobe Experience Platform (AEP) activation client.

Uses customer-supplied credentials (client id, org id, access token, sandbox,
tenant id) to validate access and provision a personalization field group +
schema in the Schema Registry. This is the real network call behind the
"Activation" tab's Adobe Experience Platform connector — failures surface the
raw Adobe API error back to the caller so the UI can show exactly what went
wrong (status, title, detail, registry request id, sub-errors).

Also provides dataset creation (Catalog Service) and single-record ingestion
(Batch Ingestion Service) for the "Create Dataset" action that pulls a
customer's Agent D result into a dataset bound to an already-provisioned schema.
"""
import time
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

PLATFORM_BASE = "https://platform.adobe.io"
SCHEMA_REGISTRY_BASE = f"{PLATFORM_BASE}/data/foundation/schemaregistry"
CATALOG_BASE = f"{PLATFORM_BASE}/data/foundation/catalog"
BATCHES_BASE = f"{PLATFORM_BASE}/data/foundation/import/batches"
EXPORT_BATCHES_BASE = f"{PLATFORM_BASE}/data/foundation/export/batches"
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
                            "offerName": {"type": "string", "title": "Offer Name"},
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
    # (or reuse it if a prior activation already created one — titles must be unique per tenant).
    # Scoped to schema_title (not just industry) so a new schema name always gets its own
    # field group — otherwise every schema, old or new, would keep resolving to whatever
    # field group a fixed title happened to match, silently reusing stale field definitions.
    schema_title_for_fg = (schema_name or "").strip() or DEFAULT_SCHEMA_NAME
    fg_title = f"{label} NBA Personalization Attributes — {schema_title_for_fg}"
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


def _find_dataset_by_name(name: str, headers: Dict[str, str]) -> Optional[str]:
    """Look up an existing dataset by exact name via the Catalog Service. Returns
    its id if found, else None — makes dataset creation idempotent the same way
    _find_by_title does for field groups/schemas."""
    try:
        resp = requests.get(
            f"{CATALOG_BASE}/dataSets",
            headers=headers,
            params={"property": f"name=={name}"},
            timeout=REQUEST_TIMEOUT,
            verify=False,
        )
    except requests.RequestException:
        return None

    if resp.status_code >= 400:
        return None

    body = resp.json() or {}
    return next(iter(body.keys()), None)  # Catalog returns {"<id>": {...}} keyed by id


def create_dataset(
    client_id: str,
    org_id: str,
    access_token: str,
    sandbox: str,
    schema_name: str,
    dataset_name: str,
) -> Dict[str, str]:
    """
    Resolve schema_name to its $id in the Schema Registry, then create (or reuse,
    if one with this exact name already exists) a dataset bound to that schema.

    Raises AdobeAEPError on any failure.
    """
    headers = _headers(access_token, client_id, org_id, sandbox)

    schema = _find_by_title("schemas", schema_name, headers)
    if schema is None:
        raise AdobeAEPError(
            step="schema_lookup",
            message=f"No schema named '{schema_name}' found in sandbox '{sandbox}'. Connect to AEP first to create it.",
        )
    schema_id = schema.get("$id")

    existing_id = _find_dataset_by_name(dataset_name, headers)
    if existing_id:
        return {"datasetId": existing_id, "schemaId": schema_id}

    try:
        resp = requests.post(
            f"{CATALOG_BASE}/dataSets",
            headers=headers,
            json={"name": dataset_name, "schemaRef": {"id": schema_id, "contentType": "application/vnd.adobe.xed+json;version=1"}},
            timeout=REQUEST_TIMEOUT,
            verify=False,
        )
    except requests.RequestException as e:
        raise AdobeAEPError(step="dataset_creation", message=f"Could not reach Adobe Experience Platform: {e}")

    if resp.status_code >= 400:
        raise AdobeAEPError(step="dataset_creation", response=resp)

    # Catalog Service returns a list of new resource paths, e.g. ["@/dataSets/64abc123..."]
    created = resp.json()
    if not created:
        raise AdobeAEPError(step="dataset_creation", message="AEP dataset creation returned no dataset id")
    dataset_id = created[0].rsplit("/", 1)[-1]
    return {"datasetId": dataset_id, "schemaId": schema_id}


def ingest_records(
    client_id: str,
    org_id: str,
    access_token: str,
    sandbox: str,
    dataset_id: str,
    records: List[Dict[str, Any]],
    poll_attempts: int = 12,
    poll_delay: float = 3.0,
) -> Dict[str, Any]:
    """
    Push one or more records into dataset_id via the 4-step Batch Ingestion flow:
    create batch -> upload one multi-line NDJSON file (one line per record) ->
    mark complete -> poll status. All records land in a single batch.

    Raises AdobeAEPError on any failure (including AEP reporting batch status "failed").
    """
    headers = _headers(access_token, client_id, org_id, sandbox)

    try:
        resp = requests.post(
            BATCHES_BASE,
            headers=headers,
            json={"datasetId": dataset_id, "inputFormat": {"format": "json"}},
            timeout=REQUEST_TIMEOUT,
            verify=False,
        )
    except requests.RequestException as e:
        raise AdobeAEPError(step="batch_creation", message=f"Could not reach Adobe Experience Platform: {e}")
    if resp.status_code >= 400:
        raise AdobeAEPError(step="batch_creation", response=resp)
    batch_id = resp.json()["id"]

    upload_url = f"{BATCHES_BASE}/{batch_id}/datasets/{dataset_id}/files/activation-records.json"
    try:
        # The batch file-upload endpoint rejects application/json (415) — it wants the
        # raw bytes as application/octet-stream regardless of the batch's inputFormat.
        resp = requests.put(
            upload_url,
            headers={**headers, "Content-Type": "application/octet-stream"},
            data=_to_ndjson(records).encode("utf-8"),
            timeout=REQUEST_TIMEOUT,
            verify=False,
        )
    except requests.RequestException as e:
        raise AdobeAEPError(step="batch_upload", message=f"Could not reach Adobe Experience Platform: {e}")
    if resp.status_code >= 400:
        raise AdobeAEPError(step="batch_upload", response=resp)

    try:
        # Signaling completion is a bodiless POST with action=COMPLETE as a query
        # param — not a PATCH with a JSON body (that returns 405 Method Not Allowed).
        resp = requests.post(
            f"{BATCHES_BASE}/{batch_id}",
            headers=headers,
            params={"action": "COMPLETE"},
            timeout=REQUEST_TIMEOUT,
            verify=False,
        )
    except requests.RequestException as e:
        raise AdobeAEPError(step="batch_completion", message=f"Could not reach Adobe Experience Platform: {e}")
    if resp.status_code >= 400:
        raise AdobeAEPError(step="batch_completion", response=resp)

    status, batch_errors, metrics = _poll_batch_status(batch_id, headers, poll_attempts, poll_delay)

    # A batch's top-level status can say "success" even when every record inside it
    # was individually rejected by validation — status only reflects "the file processed
    # without a system error," not "the records actually landed." metrics.failedRecordCount
    # is the authoritative signal; this is what was silently reporting false success before.
    failed_record_count = int((metrics or {}).get("failedRecordCount") or 0)
    input_record_count = int((metrics or {}).get("inputRecordCount") or len(records))

    if status == "failed" or failed_record_count > 0:
        row_errors = _fetch_row_errors(batch_id, headers) if not batch_errors else []
        detail = (
            "; ".join(f"[{e.get('code')}] {e.get('description')}" for e in batch_errors if isinstance(e, dict))
            or "; ".join(row_errors)
            or (
                f"{failed_record_count} of {input_record_count} record(s) failed validation (no error detail returned)"
                if failed_record_count
                else f"AEP batch {batch_id} failed validation/ingestion (no error detail returned)"
            )
        )
        err = AdobeAEPError(step="batch_validation", message=detail)
        err.sub_errors = batch_errors or row_errors
        raise err

    return {"batchId": batch_id, "status": status, "recordCount": len(records)}


def _poll_batch_status(batch_id: str, headers: Dict[str, str], attempts: int, delay: float) -> tuple:
    last_status = "unknown"
    errors: List[Any] = []
    metrics: Dict[str, Any] = {}
    for _ in range(attempts):
        try:
            resp = requests.get(f"{BATCHES_BASE}/{batch_id}", headers=headers, timeout=REQUEST_TIMEOUT, verify=False)
        except requests.RequestException:
            break
        if resp.status_code >= 400:
            break
        body = resp.json() or {}
        last_status = body.get("status", "unknown")
        errors = body.get("errors") or []
        metrics = body.get("metrics") or {}
        if last_status in ("success", "failed"):
            break
        time.sleep(delay)
    return last_status, errors, metrics


def _fetch_row_errors(batch_id: str, headers: Dict[str, str]) -> List[str]:
    """
    Best-effort fetch of per-record rejection reasons for a batch whose top-level
    status/errors didn't explain a nonzero failedRecordCount. Two-step: list the
    error files for this batch, then read each file's _errors. Never raises —
    returns [] on any failure so a diagnostics hiccup doesn't mask the real error.
    """
    try:
        listing = requests.get(
            f"{EXPORT_BATCHES_BASE}/{batch_id}/meta",
            headers=headers,
            params={"path": "row_errors"},
            timeout=REQUEST_TIMEOUT,
            verify=False,
        )
        if listing.status_code >= 400:
            return []
        files = (listing.json() or {}).get("data") or []

        messages: List[str] = []
        for f in files[:5]:  # cap — this is a diagnostic aid, not a full report
            href = ((f.get("_links") or {}).get("self") or {}).get("href")
            if not href:
                continue
            file_resp = requests.get(href, headers=headers, timeout=REQUEST_TIMEOUT, verify=False)
            if file_resp.status_code >= 400:
                continue
            for err in (file_resp.json() or {}).get("_errors") or []:
                messages.append(f"[{err.get('code')}] {err.get('message')}")
            if len(messages) >= 10:
                break
        return messages[:10]
    except requests.RequestException:
        return []


def _to_ndjson(records: List[Dict[str, Any]]) -> str:
    import json
    return "\n".join(json.dumps(r) for r in records)
