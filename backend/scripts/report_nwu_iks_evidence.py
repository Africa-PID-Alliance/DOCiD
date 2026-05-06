#!/usr/bin/env python3
"""
NWU IKS Languages Articles — read-only evidence digest.

Reads the public DSpace 9 discover endpoint (no auth) for the
"Faculty of Humanities > Languages > Articles" collection and writes a
markdown summary suitable for pasting into the integration reply email.

Usage:
    python3 backend/scripts/report_nwu_iks_evidence.py \
        > meeting-notes/clients/north-west-university/2026-05-06-local-evidence-harvest.md

Side effects: makes 1 paginated GET request to repository.nwu.ac.za (55 items
fits in one page at size=100). No DB writes, no DOCiD/Cordra calls.
No DB writes, no DOCiD/Cordra calls, no Flask app loaded.
"""
from __future__ import annotations

import sys
import time
from collections import Counter
from datetime import datetime, timezone

import requests

BASE_URL = "https://repository.nwu.ac.za/server/api/discover/search/objects"
COLLECTION_UUID = "4196b018-e48c-4f7e-ba5e-4cb1414e3449"
COLLECTION_LABEL = "Faculty of Humanities > Languages > Articles"
COLLECTION_BROWSE_URL = (
    "https://repository.nwu.ac.za/collections/"
    f"{COLLECTION_UUID}/browse/dateissued"
)
PAGE_SIZE = 100
HTTP_TIMEOUT = 30
USER_AGENT = "DOCiD-evidence-script/1.0 (ekariz@gmail.com; one-off audit)"


def fetch_all_items() -> list[dict]:
    """Page through discover/search/objects until exhausted; return raw item dicts.

    Terminates strictly on `page + 1 >= totalPages` to avoid silent truncation
    when DSpace returns a non-final empty page. Raises RuntimeError if the
    response lacks `page` metadata (we cannot trust count-based pagination
    without it).
    """
    items: list[dict] = []
    page = 0
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    max_pages_safety = 200  # 20,000-item cap; the IKS collection has 55

    while page < max_pages_safety:
        params = {
            "dsoType": "item",
            "scope": COLLECTION_UUID,
            "page": page,
            "size": PAGE_SIZE,
        }
        response = requests.get(BASE_URL, params=params, headers=headers, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        payload = response.json()

        search_result = payload.get("_embedded", {}).get("searchResult", {})
        page_info = search_result.get("page")
        if not page_info or "totalPages" not in page_info:
            raise RuntimeError(
                f"DSpace response missing page metadata at page={page}; "
                "cannot trust pagination — refusing to silently truncate."
            )
        objects = search_result.get("_embedded", {}).get("objects", [])

        for search_object in objects:
            indexable_object = search_object.get("_embedded", {}).get("indexableObject", {})
            if indexable_object.get("type") == "item":
                items.append(indexable_object)

        total_pages = page_info.get("totalPages", 0)
        if page + 1 >= total_pages:
            break
        page += 1
        time.sleep(0.2)  # polite

    return items


def first_metadata_value(item: dict, field: str) -> str | None:
    values = item.get("metadata", {}).get(field, [])
    if not values:
        return None
    raw = values[0].get("value", "")
    return raw.strip() or None


def all_metadata_values(item: dict, field: str) -> list[str]:
    return [
        entry.get("value", "").strip()
        for entry in item.get("metadata", {}).get(field, [])
        if entry.get("value", "").strip()
    ]


def build_report(items: list[dict]) -> str:
    total = len(items)
    with_doi = sum(1 for item in items if first_metadata_value(item, "dc.identifier.doi"))
    with_abstract = sum(1 for item in items if first_metadata_value(item, "dc.description.abstract"))
    with_sdg = sum(1 for item in items if all_metadata_values(item, "dc.description.sustainable"))

    year_counts: Counter[str] = Counter()
    language_counts: Counter[str] = Counter()
    contributor_counts: Counter[str] = Counter()
    type_counts: Counter[str] = Counter()
    sdg_value_counts: Counter[str] = Counter()
    sample_titles: list[str] = []

    for item in items:
        issued = first_metadata_value(item, "dc.date.issued") or ""
        year = issued[:4]
        if year.isdigit():
            year_counts[year] += 1

        for language in all_metadata_values(item, "dc.language.iso"):
            language_counts[language] += 1

        for author in all_metadata_values(item, "dc.contributor.author"):
            contributor_counts[author] += 1

        for type_value in all_metadata_values(item, "dc.type"):
            type_counts[type_value] += 1

        for sdg_value in all_metadata_values(item, "dc.description.sustainable"):
            sdg_value_counts[sdg_value] += 1

        title = first_metadata_value(item, "dc.title") or item.get("name") or "(untitled)"
        if len(sample_titles) < 10:
            sample_titles.append(title)

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    lines: list[str] = []
    lines.append("# NWU IKS Languages Articles — Local Evidence Harvest")
    lines.append("")
    lines.append(f"- **Generated:** {generated_at}")
    lines.append(f"- **Source collection:** [{COLLECTION_LABEL}]({COLLECTION_BROWSE_URL})")
    lines.append(f"- **Collection UUID:** `{COLLECTION_UUID}`")
    lines.append(f"- **Mode:** read-only audit (no DB writes, no CORDRA, no DOCiD minting)")
    lines.append("")
    lines.append("## Counts")
    lines.append(f"- Items inspected: **{total}**")
    lines.append(f"- With DOI (`dc.identifier.doi`): **{with_doi}** ({pct(with_doi, total)})")
    lines.append(f"- With abstract: **{with_abstract}** ({pct(with_abstract, total)})")
    lines.append(f"- With SDG metadata (`dc.description.sustainable`): **{with_sdg}** ({pct(with_sdg, total)})")
    lines.append(f"- Distinct contributors: **{len(contributor_counts)}**")
    lines.append("")
    lines.append("## Year coverage (`dc.date.issued`)")
    if year_counts:
        for year, count in sorted(year_counts.items()):
            lines.append(f"- {year}: {count}")
    else:
        lines.append("- (no `dc.date.issued` values found)")
    lines.append("")
    lines.append("## Language breakdown (`dc.language.iso`)")
    if language_counts:
        for language, count in language_counts.most_common():
            lines.append(f"- `{language}`: {count}")
    else:
        lines.append("- (no `dc.language.iso` values found)")
    lines.append("")
    lines.append("## Resource type breakdown (`dc.type`)")
    if type_counts:
        for type_value, count in type_counts.most_common():
            lines.append(f"- {type_value}: {count}")
    else:
        lines.append("- (no `dc.type` values found)")
    lines.append("")
    lines.append("## Top 10 contributors (`dc.contributor.author`)")
    if contributor_counts:
        for name, count in contributor_counts.most_common(10):
            lines.append(f"- {name} ({count})")
    else:
        lines.append("- (no `dc.contributor.author` values found)")
    lines.append("")
    lines.append("## SDG values observed (`dc.description.sustainable`)")
    if sdg_value_counts:
        for sdg_value, count in sdg_value_counts.most_common():
            lines.append(f"- {sdg_value}: {count}")
    else:
        lines.append("- (field is configured per Songezo Mpikashe but no items have populated values)")
    lines.append("")
    lines.append("## Sample titles (first 10)")
    for title in sample_titles:
        lines.append(f"- {title}")
    lines.append("")
    return "\n".join(lines)


def pct(part: int, whole: int) -> str:
    if whole == 0:
        return "0%"
    return f"{(100 * part / whole):.0f}%"


def main() -> int:
    try:
        items = fetch_all_items()
    except requests.RequestException as fetch_error:
        print(f"ERROR: failed to fetch from {BASE_URL}: {fetch_error}", file=sys.stderr)
        return 1
    sys.stdout.write(build_report(items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
