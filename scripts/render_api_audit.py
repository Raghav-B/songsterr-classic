"""Render an honest request-surface inventory from the frozen AST evidence.

Matching field names are only candidates for compatibility. Runtime acceptance,
response semantics and opaque payloads are not inferred from those matches.
"""
import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "artifacts/api-audit-2026-10-12"
DOCS = ROOT / "docs"
METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}

NOTES = {
    "/api/edits": "Same autosave envelope; edit tuples and retry/conflict state require round-trip validation. Blanket block must be narrowed.",
    "/api/edits/{songId}/{revisionId}": "Both consumers read edits + version and normalize cursor tuples. No response adapter identified; authenticated reload untested.",
    "/api/edits/saveRevision": "Current adds trackIdentities + revisionNotificationSubscribed. Structural-track preservation needs a state-aware adapter or explicit proof the backend safely infers identity.",
    "/api/edits/download": "Same fields and blob response. Export POST is blocked unnecessarily by preview policy; not a demonstrated protocol mismatch.",
    "/api/video-points/{songId}/edited": "Current supports mode/parts/target/endTime instead of old part. Needs semantic sync adapter for current behavior; never blindly rename part to parts.",
    "/api/song/{songId}/rename": "additionalCheckShown replaced by explanation. New text cannot be derived from the old boolean; add input or hand off to current UI.",
    "/api/preference": "GET/PUT remain and dictionary payloads are dynamic. New client adds serialized writes, POST merge/import, owner-aware local migration. No ordinary key/value translator proved necessary.",
    "/api/chords/{revisionId}/detect": "Null-body route remains; current additionally accepts edited source snapshot. Existing published-score mode is a candidate; edited-score mode needs snapshot support.",
    "/api/user/{profileName}": "Current uses /api/user/{*}. Parameter-placeholder change is not proof of a removed URL; test encoded/nested profile names.",
    "/api/user/{*}": "Current wildcard counterpart of July profileName route; not necessarily a distinct server resource.",
    "/auth/entitlement/refresh": "Not called by current graph. Server removal NOT established; preserve real account state and test normal refresh, never manufacture entitlements.",
    "/auth/profile/notifications": "No current call found. Current per-song notification APIs are not automatically an equivalent replacement for global profile preferences.",
    "/auth/stripe/session/status": "No current call found. Keep payments in current UI; do not assume a replacement without exercising the supported account flow.",
    "/api/voice/realtime-session": "July-only voice bootstrap plus external OpenAI request. Feature migration unresolved; unrelated to basic tab editing.",
    "/editor/{dynamic}/{dynamic}/chords/detect": "July auxiliary path. Must resolve host and lifecycle before replacing with /api/chords/...; current edited-score snapshot route is a candidate, not proven equivalent.",
    "/api/song/{songId}/request": "Current adds expectedCredits and request options. Requires user-visible credit/quote semantics for paid operations, not guessed defaults.",
    "/auth/bonus/activate-minutes": "Current supports credit-aware mode and expectedCredits. Keep legacy behavior unverified; do not synthesize credit approval.",
    "/auth/bonus/purchase-feature": "Current adds expectedCredits and credit-mode options. Paid-feature migration requires current quote/consent flow.",
    "/api/song/check-duplicate": "Current adds a second generic-body caller. Extractor shape difference alone does not establish a changed server contract.",
    "/api/requests/next": "Current supplies allowLowPriority true/false. July omission may use a default; verify queue behavior before adding a default.",
    "/api/rag-chat/{accessKey}/message/{messageId}/feedback": "Current omits source. Test whether legacy extra field is accepted; remove only if evidence requires it.",
    "/api/contributions/transcriptions": "Current adds withResults and dedicated result route. Basic list may remain compatible; richer results require feature adaptation.",
    "/api/comment/revision/{revisionId}/suggest": "Current query includes a spread object. Must inspect callers; opaque spread is not proof old fields were removed.",
    "/api/song/{songId}/publish": "Same PUT path/body absence and duplicate-409 consumer. Real publishing untested; never include in read-only probes.",
}


def groups(data):
    result = {}
    for call in data["calls"]:
        if call["method"] in METHODS and call["route"].startswith("/"):
            result.setdefault((call["method"], call["route"]), []).append(call)
    return result


def signature(calls):
    return sorted({field for call in calls for field in call["fields"] if field.startswith(("body.", "params."))})


def main():
    data = json.loads((AUDIT / "api-calls.json").read_text())
    assets = json.loads((AUDIT / "asset-receipt.json").read_text())
    proof = json.loads((AUDIT / "bundled-prototype.json").read_text())
    old, new = groups(data["july"]), groups(data["current"])
    rows = []
    for method, route in sorted(old.keys() | new.keys()):
        before, after = old.get((method, route), []), new.get((method, route), [])
        left, right = signature(before), signature(after)
        if not before:
            status = "CURRENT-ONLY"
        elif not after:
            status = "JULY-ONLY"
        elif left != right:
            status = "REQUEST-SURFACE-DIFF"
        else:
            status = "SAME-EXTRACTED-SURFACE"
        note = NOTES.get(route)
        if not note:
            if "transcrib" in route or "transcription" in route:
                note = "Transcription/credit flow: inspect dynamic payload and quote behavior; not required for ordinary note editing. No paid job executed."
            elif status == "CURRENT-ONLY":
                note = "New-client feature/call. Not needed merely to render July; port UI/state only if the feature is wanted."
            elif status == "JULY-ONLY":
                note = "Not found in current graph; not proof server support ended. Runtime validation or current-UI handoff required."
            elif status == "REQUEST-SURFACE-DIFF":
                note = "Inspect differences and opaque values; changed source shape does not prove the server rejects July."
            else:
                note = "No request-field adapter identified. Values, response semantics, authorization and end-to-end behavior remain unverified unless noted in guide."
        rows.append({"method":method,"route":route,"status":status,"july_fields":left,"current_fields":right,
                     "removed_fields":sorted(set(left)-set(right)),"added_fields":sorted(set(right)-set(left)),
                     "july_sites":[f"{c['file']}@{c['offset']}" for c in before],
                     "current_sites":[f"{c['file']}@{c['offset']}" for c in after],"assessment":note})
    summary = {"july_routes":len(old),"current_routes":len(new),"union_routes":len(rows),"statuses":dict(Counter(r["status"] for r in rows)),
               "july_js":data["july"]["parsed"],"current_js":data["current"]["parsed"],
               "july_dynamic_sites":len(data["july"]["unresolved"]),"current_dynamic_sites":len(data["current"]["unresolved"]),
               "scope":"Literal first-party relative HTTP route patterns, including form and beacon calls. Not a complete server specification or a compatibility certificate."}
    (AUDIT / "endpoint-inventory.json").write_text(json.dumps({"summary":summary,"routes":rows},indent=2)+"\n")
    with (AUDIT / "endpoint-inventory.csv").open("w") as handle:
        writer = csv.DictWriter(handle,fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k:json.dumps(v) if isinstance(v,list) else v for k,v in row.items()})
    lines = ["# Songsterr API request inventory — 12 October 2026", "", "Generated from frozen public client assets; no API mutations executed.", "",
             f"**{len(rows)} distinct relative HTTP method/route patterns:** {len(old)} July, {len(new)} current. Counts preserve path parameter names, so `/api/user/{{profileName}}` and `/api/user/{{*}}` are separate inventory rows, not necessarily different server URLs.", "",
             "## Read the labels correctly", "",
             "- **SAME-EXTRACTED-SURFACE:** no difference in recovered request field names. Not proof of equal values, response schema, or runtime success.",
             "- **REQUEST-SURFACE-DIFF:** inspect fields/callers; spreads and dynamic dictionary bodies may be an extraction difference rather than a protocol migration.",
             "- **JULY-ONLY:** no matching current call found, not a 404/deprecation claim.",
             "- **CURRENT-ONLY:** no July call found. Usually a new feature, not a prerequisite for old editing.",
             "- `<dynamic>`, `<spread>`, and `<computed-key>` explicitly identify values this static inventory does not fully resolve.", "",
             "`file@offset` is a zero-based JavaScript character offset in the frozen file. `asset-receipt.json` binds each filename to SHA-256. Full call-site options and surrounding response consumers are in `api-calls.json`.", "",
             "## Every discovered relative HTTP route", "", "| Method / route | Assessment | Field changes | Source locations |", "|---|---|---|---|"]
    for row in rows:
        changes = "Removed: " + ", ".join(row["removed_fields"]) + "; Added: " + ", ".join(row["added_fields"]) if row["removed_fields"] or row["added_fields"] else "No extracted field difference"
        sites = "July: " + "; ".join(row["july_sites"]) + "<br>Current: " + "; ".join(row["current_sites"])
        lines.append(f"| `{row['method']} {row['route']}` | **{row['status']}**. {row['assessment']} | {changes} | {sites} |")
    lines.extend(["", "## Non-literal requests and other transports", "", "These are coverage boundaries, not dropped evidence. Generic fetch/XHR implementations, signed upload destinations, audio resource URLs and dynamically constructed worker/WebSocket addresses need caller or runtime tracing.", ""])
    for label in ["july","current"]:
        lines.extend([f"### {label.title()} — {len(data[label]['unresolved'])} unresolved-address sites", "", "| Transport | Source | Expression |", "|---|---|---|"])
        for call in data[label]["unresolved"]:
            code = call["call"][:220].replace("|","\\|").replace("`","'")
            lines.append(f"| {call['method']} | {call['file']}@{call['offset']} | `{code}` |")
        other = [c for c in data[label]["calls"] if not (c["method"] in METHODS and c["route"].startswith("/"))]
        lines.extend(["", "Resolved external/transport patterns:", ""])
        for method, route in sorted({(c['method'],c['route']) for c in other}):
            lines.append(f"- `{method} {route}`")
    DOCS.mkdir(exist_ok=True)
    (DOCS / "api-endpoint-inventory-2026-10-12.md").write_text("\n".join(lines)+"\n")
    resource_paths = sorted({r['value'] for r in data['july']['resources']})
    (AUDIT / "additional-july-resource-strings.json").write_text(json.dumps(resource_paths,indent=2)+"\n")
    (AUDIT / "summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2))


if __name__ == "__main__":
    main()
