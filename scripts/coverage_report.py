"""Account for every requested current-client route without certifying mocks as live tests."""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ADAPTERS = {
    ("GET", "/api/contributions/transcriptions"): "transport.js: withResults=false; explicit query preserved",
    ("PATCH", "/api/rag-chat/{accessKey}/message/{messageId}/feedback"): "transport.js: omit obsolete source field; plain/gzip bodies tested",
    ("POST", "/api/song/{songId}/rename"): "transport.js: optional explanation; omit additionalCheckShown; no invented prose",
    ("POST", "/api/edits/saveRevision"): "build_local.py + track-identities.js: actual worker replay preserves identities; notification preference is not fabricated",
}

DETAILS = {
    "/api/edits": "Real draft persistence, interrupted save and concurrent-tab conflict reconciliation remain unverified.",
    "/api/edits/{songId}/{revisionId}": "Compare replayed note/undo state after actual private-song save and reload.",
    "/api/edits/download": "Check real GP/MIDI download and reopen; blob response is currently passed unchanged.",
    "/api/comment/revision/{revisionId}/suggest": "Current extra instruction is optional in the actual caller; no translation identified for July's text-only mode.",
    "/api/chords/{revisionId}/detect": "Published-score null-body mode remains; current edited-score source needs an additional feature flow.",
    "/api/song/check-duplicate": "Generic body extraction differs; actual metadata/video query remains a candidate, not a demonstrated break.",
    "/api/requests/next": "Current explicitly supplies allowLowPriority; queue default semantics have not been verified.",
    "/api/video-points/{songId}/edited": "NOT adapted: current mode/parts/target/endTime and response lifecycle require UI/state migration, not a field rename.",
    "/api/preference": "NOT lifecycle-migrated: old dictionary GET/PUT exist; owner-aware import, migration and serialized writes are still missing.",
    "/api/user/{*}": "Wildcard naming may address the same profile resource as July's profileName; encoded/nested names need testing.",
    "/api/edits/{songId}": "NOT implemented: current draft-discard lifecycle; do not blindly DELETE drafts as a conflict workaround.",
}


def main():
    inventory = json.loads((ROOT / "artifacts/api-audit-2026-10-12/endpoint-inventory.json").read_text())
    receipt = json.loads((ROOT / "artifacts/local-qa/receipt.json").read_text())
    reads = receipt.get("reads", [])
    rows = []
    for source in inventory["routes"]:
        if source["status"] == "JULY-ONLY":
            continue
        method, route = source["method"], source["route"]
        key = (method, route)
        if key in ADAPTERS:
            implementation = "adapter-tested-offline"
            detail = ADAPTERS[key]
        elif source["status"] == "CURRENT-ONLY":
            implementation = "current-feature-not-ported"
            detail = "July has no matching caller; needs the current feature's state/UI flow. Not satisfied by allowing the URL."
        elif source["status"] == "REQUEST-SURFACE-DIFF":
            implementation = "semantic-review-open"
            detail = "Extracted request fields differ; endpoint-specific UI/state/response verification still needed."
        else:
            implementation = "unchanged-request-candidate"
            detail = "Pass-through; field equality is not response, authorization, or end-to-end verification."
        if route in DETAILS:
            detail += " " + DETAILS[route]
        pattern = re.escape(route)
        pattern = re.sub(r"\\\{.*?\\\}", "[^/]+", pattern)
        observed = [read for read in reads if read["method"] == method and re.fullmatch(pattern, read["path"])]
        rows.append({
            "method": method, "route": route, "implementation": implementation,
            "end_to_end_certified": False, "observed_public_responses": observed,
            "detail": detail, "july_sites": source["july_sites"], "current_sites": source["current_sites"],
        })
    assert len(rows) == 184, "Current-client scope drifted; review the inventory before publishing coverage"
    assert len({(row["method"], row["route"]) for row in rows}) == 184
    totals = dict(Counter(row["implementation"] for row in rows))
    report = {
        "scope": "184 current-client HTTP call patterns; six July-only patterns excluded by user request",
        "counts": totals, "end_to_end_certified": 0,
        "boundary": "No authenticated save, public publication, payment, credit-spending or moderation was performed. Public 200 responses and offline adapter tests are not end-to-end certification.",
        "routes": rows,
    }
    (ROOT / "docs/route-coverage-2026-10-12.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = ["# Current-client route coverage — 12 October 2026", "", report["scope"], "",
             "**Not complete: 0/184 end-to-end certified.** This is an implementation and evidence inventory, not a green checklist.", "",
             report["boundary"], "", "| Implementation state | Count |", "|---|---:|"]
    lines += [f"| {status} | {count} |" for status, count in totals.items()]
    lines += ["", "| Method | Pattern | Implementation | Public response evidence | Remaining boundary / adapter |", "|---|---|---|---|---|"]
    for row in rows:
        evidence = "; ".join(f"{read['status']} {read['path']}" for read in row["observed_public_responses"]) or "None"
        lines.append(f"| {row['method']} | `{row['route']}` | {row['implementation']} | {evidence} | {row['detail']} |")
    lines += ["", "Source offsets for every row are retained in the companion JSON and the original endpoint inventory.",
              "WebSocket protocols (bar completion, chat, lyrics), opaque signed uploads, dynamic SDK calls and full response schemas are outside the 184-pattern count and still need separate proof.", ""]
    (ROOT / "docs/route-coverage-2026-10-12.md").write_text("\n".join(lines))
    print(json.dumps(totals))


if __name__ == "__main__":
    main()
