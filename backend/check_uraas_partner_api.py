#!/usr/bin/env python3
"""Check the URAAS partner API against its partner documentation.

Runs every endpoint from the "URAAS Partner API" doc (papers, Special
Collections, analytics, registry, crawl status) plus the keyword and citation
endpoints, and checks status codes, response shapes and the error contract
(401 / 403 / 404 / 429 bodies are JSON {"status": "error", "message": ...}).

Standalone: needs only `requests`, no DOCiD app or database.

Usage (from backend/):
    export URAAS_API_KEY=uraas_live_...        # never hard-code the key
    python check_uraas_partner_api.py           # read-only checks
    python check_uraas_partner_api.py --markdown > uraas_report.md
    python check_uraas_partner_api.py --crawl   # also trigger a real UNILAG crawl
    python check_uraas_partner_api.py --rate-limit  # also burst to hit the 429

--crawl starts a real crawl that can end in real DOCiD registrations and puts
the key on a 10-minute cooldown. --rate-limit uses up the key's 120/min budget,
so it runs last.

Exit code: 0 if no check FAILs, 1 if any does, 2 on bad setup (no key).
"""
import argparse
import os
import sys
import time

import requests

DEFAULT_BASE_URL = "https://lordkiki-apa-uraas.hf.space"
UNKNOWN_ID = 999999999
PAPER_FIELDS = ("id", "title", "doi", "url", "docid", "download_url",
                "has_local_pdf", "access_policy")
VALID_SPIDERS = ("openalex", "crossref", "arxiv", "orcid", "semantic_scholar",
                 "europepmc", "core", "pubmed", "openaire", "doaj", "ajol")

PASS, FAIL, WARN, SKIP = "PASS", "FAIL", "WARN", "SKIP"


class Checker:
    def __init__(self, base_url, api_key, timeout):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.results = []

    # ------------------------------------------------------------------ utils
    def record(self, name, outcome, detail=""):
        self.results.append((name, outcome, detail))
        print("  [%s] %s%s" % (outcome, name, (" - " + detail) if detail else ""),
              file=sys.stderr)

    def request(self, method, path, key="valid", **kwargs):
        """Send a request. key: "valid", "none" or any other string to send as-is."""
        headers = dict(kwargs.pop("headers", {}) or {})
        if key == "valid":
            headers["X-API-Key"] = self.api_key
        elif key != "none":
            headers["X-API-Key"] = key
        kwargs.setdefault("timeout", self.timeout)
        return self.session.request(method, self.base_url + path,
                                    headers=headers, **kwargs)

    def get(self, name, path, expect=200, **kwargs):
        """GET path and record a FAIL unless the status matches. Returns the
        response (or None on a network error / wrong status)."""
        try:
            resp = self.request("GET", path, **kwargs)
        except requests.RequestException as exc:
            self.record(name, FAIL, "request error: %s" % exc.__class__.__name__)
            return None
        if resp.status_code != expect:
            self.record(name, FAIL, "HTTP %s, expected %s%s"
                        % (resp.status_code, expect, body_hint(resp)))
            return None
        return resp

    def get_json(self, name, path, expect=200, want_object=True, **kwargs):
        resp = self.get(name, path, expect=expect, **kwargs)
        if resp is None:
            return None
        try:
            data = resp.json()
        except ValueError:
            self.record(name, FAIL, "HTTP %s but body is not JSON (%s)"
                        % (resp.status_code, resp.headers.get("Content-Type", "?")))
            return None
        if want_object and not isinstance(data, dict):
            self.record(name, FAIL, "expected a JSON object, got %s" % shape_hint(data))
            return None
        return data

    def check_error(self, name, resp, expect):
        """Record PASS if resp has the expected error status and JSON body."""
        if resp is None:
            return
        if resp.status_code != expect:
            self.record(name, FAIL, "HTTP %s, expected %s%s"
                        % (resp.status_code, expect, body_hint(resp)))
            return
        problem = error_body_problem(resp)
        if problem:
            self.record(name, FAIL, "HTTP %s but %s" % (expect, problem))
        else:
            self.record(name, PASS, "HTTP %s, JSON error body" % expect)

    def safe(self, method, path, **kwargs):
        try:
            return self.request(method, path, **kwargs)
        except requests.RequestException as exc:
            self.record("%s %s" % (method, path), FAIL,
                        "request error: %s" % exc.__class__.__name__)
            return None

    # ----------------------------------------------------------------- checks
    def check_auth(self):
        print("Authentication", file=sys.stderr)
        self.check_error("No key -> 401 (GET /api/stats)",
                         self.safe("GET", "/api/stats", key="none"), 401)
        self.check_error("Invalid key -> 401 (GET /api/stats)",
                         self.safe("GET", "/api/stats",
                                   key="uraas_live_invalid_key_for_testing"), 401)
        # Only GETs here: a POST that failed open would mutate URAAS data.
        self.check_error("Valid key, admin endpoint -> 403 (GET /api/admin/api-keys)",
                         self.safe("GET", "/api/admin/api-keys"), 403)
        resp = self.safe("GET", "/api/partner/not-a-real-endpoint")
        if resp is not None and resp.status_code == 404:
            self.record("Valid key, unlisted path -> 403", WARN,
                        "got 404; doc says anything outside the allowlist is 403")
        else:
            self.check_error("Valid key, unlisted path -> 403", resp, 403)

    def check_stats(self):
        name = "GET /api/stats"
        data = self.get_json(name, "/api/stats")
        if data is None:
            return
        problems = []
        if data.get("status") != "success":
            problems.append("status=%r" % data.get("status"))
        edges = data.get("network_edges")
        authors = data.get("top_authors")
        if not isinstance(edges, list):
            problems.append("network_edges not a list")
        elif edges and not has_keys(edges[0], ("source", "target", "weight")):
            problems.append("network_edges[0] missing source/target/weight")
        if not isinstance(authors, list):
            problems.append("top_authors not a list")
        elif authors and not has_keys(authors[0], ("author", "count", "orcid", "ror")):
            problems.append("top_authors[0] missing author/count/orcid/ror")
        if problems:
            self.record(name, FAIL, "; ".join(problems))
        else:
            self.record(name, PASS, "%d edges, %d top authors" % (len(edges), len(authors)))

    def check_tree(self):
        """Returns the flat list of papers from /api/papers/tree."""
        name = "GET /api/papers/tree"
        data = self.get_json(name, "/api/papers/tree")
        if data is None:
            return []
        tree = data.get("data")
        if not isinstance(tree, dict):
            self.record(name, FAIL, "'data' is not a faculty -> department object")
            return []
        papers, problems = [], []
        for faculty, departments in tree.items():
            if not isinstance(departments, dict):
                problems.append("faculty %r is not a department object" % faculty)
                continue
            for department, items in departments.items():
                if not isinstance(items, list):
                    problems.append("%s / %s is not a list" % (faculty, department))
                    continue
                papers.extend(p for p in items if isinstance(p, dict))
        missing = sorted({f for p in papers for f in PAPER_FIELDS if f not in p})
        if missing:
            problems.append("papers missing fields: %s" % ", ".join(missing))
        bad_docid = [p.get("id") for p in papers
                     if "docid" in p and not isinstance(p["docid"], str)]
        if bad_docid:
            problems.append("%d papers have a non-string docid (doc: '' when unset)"
                            % len(bad_docid))
        with_docid = sum(1 for p in papers if p.get("docid"))
        summary = "%d faculties, %d papers, %d with a DOCiD" % (
            len(tree), len(papers), with_docid)
        if problems:
            self.record(name, FAIL, summary + "; " + "; ".join(problems[:3]))
        elif not papers:
            self.record(name, WARN, summary + "; no papers to test per-paper endpoints")
        else:
            self.record(name, PASS, summary)
        return papers

    def check_paper(self, pid):
        name = "GET /api/papers/<id>"
        data = self.get_json(name, "/api/papers/%s" % pid)
        if data is None:
            return
        record = data.get("data", data) if isinstance(data, dict) else None
        if not isinstance(record, dict):
            self.record(name, FAIL, "body is not an object")
            return
        if not record.get("title"):
            self.record(name, FAIL, "no title (id %s)" % pid)
            return
        documented = ("abstract", "authors", "doi", "publication_date",
                      "docid", "ark", "ror")
        absent = [f for f in documented if f not in record]
        detail = "id %s" % pid
        if absent:
            detail += "; fields not present: %s (doc says 'where present')" % ", ".join(absent)
        self.record(name, PASS, detail)

    def check_download(self, paper):
        name = "GET /api/papers/<id>/download"
        pid = paper.get("id")
        is_open = bool(paper.get("download_url") or paper.get("has_local_pdf"))
        try:
            resp = self.request("GET", "/api/papers/%s/download" % pid,
                                allow_redirects=False, stream=True)
        except requests.RequestException as exc:
            self.record(name, FAIL, "request error: %s" % exc.__class__.__name__)
            return
        try:
            ctype = resp.headers.get("Content-Type", "")
            code = resp.status_code
            if not is_open:
                # The doc doesn't say what a closed-access download returns.
                self.record(name, WARN, "id %s is not open access: HTTP %s %s "
                            "(behaviour undocumented)" % (pid, code, ctype))
            elif code in (301, 302, 303, 307, 308) and resp.headers.get("Location"):
                self.record(name, PASS, "id %s redirects (HTTP %s)" % (pid, code))
            elif code == 200 and "pdf" in ctype.lower():
                self.record(name, PASS, "id %s streams %s" % (pid, ctype))
            else:
                self.record(name, FAIL, "id %s is open access but got HTTP %s %s"
                            % (pid, code, ctype))
        finally:
            resp.close()

    def check_bibtex(self, pid):
        name = "GET /api/papers/<id>/bibtex"
        resp = self.get(name, "/api/papers/%s/bibtex" % pid)
        if resp is None:
            return
        ctype = resp.headers.get("Content-Type", "")
        problems = []
        if not ctype.startswith("text/plain"):
            problems.append("Content-Type %r, doc says text/plain" % ctype)
        if not resp.text.lstrip().startswith("@"):
            problems.append("body doesn't start with a BibTeX entry (@...)")
        if problems:
            self.record(name, FAIL, "; ".join(problems))
        else:
            self.record(name, PASS, "id %s" % pid)

    def check_json_ok(self, name, path, params=None):
        """GET path, require 200 + JSON object/list. Returns the parsed body."""
        data = self.get_json(name, path, want_object=False, params=params)
        if data is None:
            return None
        if isinstance(data, dict) and data.get("status") == "error":
            self.record(name, FAIL, "HTTP 200 but status=error: %s" % data.get("message"))
            return None
        self.record(name, PASS, shape_hint(data))
        return data

    def check_keywords(self, pid, term):
        found = self.check_json_ok("GET /api/keywords/<id>", "/api/keywords/%s" % pid)
        self.check_json_ok("GET /api/keywords/<id>/related",
                           "/api/keywords/%s/related" % pid)
        if term is None:
            term = first_keyword(found) or "culture"
        self.check_json_ok("GET /api/keywords/search?q=%s" % term,
                           "/api/keywords/search", params={"q": term})
        self.check_json_ok("GET /api/keywords/coverage", "/api/keywords/coverage")
        self.check_json_ok("GET /api/analytics/keyword-cloud",
                           "/api/analytics/keyword-cloud")

    def check_citations(self, pid):
        self.check_json_ok("GET /api/citations/<id>", "/api/citations/%s" % pid)
        self.check_json_ok("GET /api/citations/<id>/graph",
                           "/api/citations/%s/graph" % pid)
        self.check_json_ok("GET /api/citations/coverage", "/api/citations/coverage")

    def check_special_collections(self):
        self.check_json_ok("GET /api/analytics/special-collections",
                           "/api/analytics/special-collections")
        name = "GET /api/analytics/special-collections/overview"
        data = self.get_json(name, "/api/analytics/special-collections/overview")
        if data is None:
            return
        problems = []
        co = data.get("co_occurrence")
        if not isinstance(co, dict) or not isinstance(co.get("labels"), list) \
                or not isinstance(co.get("matrix"), list):
            problems.append("co_occurrence needs labels + matrix lists")
        else:
            n = len(co["labels"])
            if len(co["matrix"]) != n or any(
                    not isinstance(row, list) or len(row) != n for row in co["matrix"]):
                problems.append("co_occurrence matrix isn't %dx%d" % (n, n))
        for key, fields in (("countries", ("code", "name", "papers")),
                            ("custodians", ("institution", "count")),
                            ("influential", ("id", "title", "categories",
                                             "citations", "sc_score"))):
            value = data.get(key)
            if not isinstance(value, list):
                problems.append("%s not a list" % key)
            elif value and not has_keys(value[0], fields):
                problems.append("%s[0] missing some of %s" % (key, "/".join(fields)))
        if problems:
            self.record(name, FAIL, "; ".join(problems))
        else:
            self.record(name, PASS, "%d categories, %d countries, %d influential" % (
                len(co["labels"]), len(data["countries"]), len(data["influential"])))

    def check_registry(self):
        name = "GET /api/university-registry"
        data = self.get_json(name, "/api/university-registry", want_object=False)
        if data is None:
            return
        entries = registry_entries(data)
        if entries is None:
            self.record(name, FAIL, "can't find a list or map of institutions; %s"
                        % shape_hint(data))
            return
        self.record(name, PASS, "%d institutions (doc says 52)" % len(entries))

    def check_institution_info(self):
        name = "GET /api/institution/info?institution=unilag"
        data = self.get_json(name, "/api/institution/info",
                             params={"institution": "unilag"})
        if data is not None:
            info = data.get("data") or {}
            expected = {"institution_name": "University of Lagos",
                        "country_name": "Nigeria", "country_code": "NG"}
            wrong = ["%s=%r" % (k, info.get(k)) for k, v in expected.items()
                     if info.get(k) != v]
            if data.get("status") != "success" or wrong:
                self.record(name, FAIL, "status=%r %s" % (data.get("status"), " ".join(wrong)))
            else:
                self.record(name, PASS, "University of Lagos, NG")
        name = "GET /api/institution/info (no institution)"
        data = self.get_json(name, "/api/institution/info")
        if data is not None:
            info = data.get("data") or {}
            set_fields = [k for k, v in info.items() if v is not None]
            if set_fields:
                self.record(name, FAIL, "doc says null fields, got %s" % ", ".join(set_fields))
            else:
                self.record(name, PASS, "null fields")

    def check_not_found(self):
        for path in ("/api/papers/%d" % UNKNOWN_ID,
                     "/api/papers/%d/bibtex" % UNKNOWN_ID,
                     "/api/keywords/%d" % UNKNOWN_ID,
                     "/api/citations/%d" % UNKNOWN_ID):
            self.check_error("Unknown id -> 404 (GET %s)" % path,
                             self.safe("GET", path), 404)

    def crawl_status(self, name="GET /api/partner/crawl/status"):
        data = self.get_json(name, "/api/partner/crawl/status")
        if data is None:
            return None
        status = data.get("status")
        if status not in ("running", "idle"):
            self.record(name, FAIL, "status=%r, expected running or idle" % status)
            return None
        self.record(name, PASS, status)
        return status

    def check_crawl(self, target, spider):
        before = self.crawl_status("GET /api/partner/crawl/status (before trigger)")
        name = "POST /api/partner/crawl/start (target %d, %s)" % (target, spider)
        if before == "running":
            self.record(name, SKIP, "a crawl is already running; rerun when idle")
            return
        body = {"target": target, "spider": spider, "boost_special": True}
        resp = self.safe("POST", "/api/partner/crawl/start", json=body)
        if resp is None:
            return
        if resp.status_code == 429:
            self.record(name, SKIP, "key is on the 10-minute cooldown%s" % body_hint(resp))
            return
        try:
            data = resp.json()
        except ValueError:
            data = None
        if resp.status_code != 200 or not isinstance(data, dict) \
                or data.get("status") != "success":
            self.record(name, FAIL, "HTTP %s%s" % (resp.status_code, body_hint(resp)))
            return
        self.record(name, PASS, data.get("message", ""))
        self.check_error("Second trigger within 10 min -> 429 (cooldown)",
                         self.safe("POST", "/api/partner/crawl/start", json=body), 429)
        time.sleep(2)
        after = self.crawl_status("GET /api/partner/crawl/status (after trigger)")
        if after == "idle":
            self.record("Crawl shows as running after trigger", WARN,
                        "status is idle 2s after a successful trigger")

    def check_rate_limit(self, limit=120):
        name = "Rate limit -> 429 within %d requests/60s" % limit
        print("Rate limit burst (up to %d requests)" % (limit + 10), file=sys.stderr)
        for i in range(1, limit + 11):
            try:
                resp = self.request("GET", "/api/partner/crawl/status")
            except requests.RequestException as exc:
                self.record(name, FAIL, "request %d: %s" % (i, exc.__class__.__name__))
                return
            if resp.status_code == 429:
                problem = error_body_problem(resp)
                self.record(name, FAIL if problem else PASS,
                            "429 on request %d of the burst%s"
                            % (i, ("; " + problem) if problem else ""))
                return
        self.record(name, FAIL, "no 429 after %d requests" % (limit + 10))

    # -------------------------------------------------------------------- run
    def run(self, paper_id=None, keyword=None, crawl=False, crawl_target=1,
            crawl_spider="openalex", rate_limit=False):
        self.check_auth()
        print("Read endpoints", file=sys.stderr)
        self.check_stats()
        papers = self.check_tree()

        paper = pick_paper(papers, paper_id)
        if paper is None:
            for ep in ("papers/<id>", "papers/<id>/download", "papers/<id>/bibtex",
                       "keywords/<id>", "keywords/<id>/related", "citations/<id>",
                       "citations/<id>/graph"):
                self.record("GET /api/" + ep, SKIP, "no paper id (pass --paper-id)")
        else:
            pid = paper["id"]
            self.check_paper(pid)
            self.check_download(paper)
            self.check_bibtex(pid)
            self.check_keywords(pid, keyword)
            self.check_citations(pid)
        if paper is None:
            self.check_json_ok("GET /api/keywords/coverage", "/api/keywords/coverage")
            self.check_json_ok("GET /api/analytics/keyword-cloud",
                               "/api/analytics/keyword-cloud")
            self.check_json_ok("GET /api/citations/coverage", "/api/citations/coverage")

        self.check_special_collections()
        self.check_registry()
        self.check_institution_info()
        print("Not-found handling", file=sys.stderr)
        self.check_not_found()

        print("Crawl", file=sys.stderr)
        if crawl:
            self.check_crawl(crawl_target, crawl_spider)
        else:
            self.crawl_status()
            self.record("POST /api/partner/crawl/start", SKIP,
                        "starts a real crawl; rerun with --crawl")

        if rate_limit:
            self.check_rate_limit()
        else:
            self.record("Rate limit -> 429", SKIP, "rerun with --rate-limit")
        return self.results


# ------------------------------------------------------------------- helpers
def has_keys(obj, keys):
    return isinstance(obj, dict) and all(k in obj for k in keys)


def body_hint(resp, limit=120):
    text = (resp.text or "").strip().replace("\n", " ")
    return (": " + text[:limit]) if text else ""


def error_body_problem(resp):
    """None if the body is the documented {"status": "error", "message": ...}."""
    try:
        data = resp.json()
    except ValueError:
        return "body is not JSON (%s)" % resp.headers.get("Content-Type", "?")
    if not isinstance(data, dict) or data.get("status") != "error" \
            or not data.get("message"):
        return "body isn't {status: error, message}: %s" % shape_hint(data)
    return None


def shape_hint(data):
    if isinstance(data, dict):
        keys = sorted(data.keys())
        return "keys: %s%s" % (", ".join(keys[:8]), "..." if len(keys) > 8 else "")
    if isinstance(data, list):
        return "list of %d" % len(data)
    return type(data).__name__


def pick_paper(papers, paper_id):
    if paper_id is not None:
        for p in papers:
            if str(p.get("id")) == str(paper_id):
                return p
        return {"id": paper_id}
    with_id = [p for p in papers if p.get("id") is not None]
    if not with_id:
        return None
    # Prefer an open-access paper so the download check has something to fetch.
    for p in with_id:
        if p.get("download_url") or p.get("has_local_pdf"):
            return p
    return with_id[0]


def first_keyword(data):
    """Best-effort: find a keyword string in an undocumented response shape."""
    if isinstance(data, dict):
        for key in ("keywords", "data", "results"):
            if key in data:
                found = first_keyword(data[key])
                if found:
                    return found
        for key in ("keyword", "term", "name"):
            if isinstance(data.get(key), str) and data[key].strip():
                return data[key].strip()
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, str) and item.strip():
                return item.strip()
            found = first_keyword(item)
            if found:
                return found
    return None


def registry_entries(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "universities", "institutions", "registry"):
            if isinstance(data.get(key), (list, dict)):
                return registry_entries(data[key]) if isinstance(data[key], list) \
                    else list(data[key].values())
        values = [v for v in data.values() if isinstance(v, dict)]
        if values and len(values) == len(data):
            return values
    return None


def print_report(results, base_url, markdown):
    counts = {k: sum(1 for r in results if r[1] == k) for k in (PASS, FAIL, WARN, SKIP)}
    summary = "%d pass, %d fail, %d warn, %d skipped" % (
        counts[PASS], counts[FAIL], counts[WARN], counts[SKIP])
    when = time.strftime("%Y-%m-%d %H:%M %Z")
    if markdown:
        print("# URAAS partner API check\n")
        print("Target: %s  \nRun: %s  \nResult: %s\n" % (base_url, when, summary))
        print("| Result | Check | Detail |")
        print("|---|---|---|")
        for name, outcome, detail in results:
            print("| %s | %s | %s |" % (outcome, name.replace("|", "\\|"),
                                        detail.replace("|", "\\|")))
    else:
        width = max(len(r[0]) for r in results) if results else 10
        print("\nURAAS partner API check - %s - %s" % (base_url, when))
        for name, outcome, detail in results:
            print("%-4s  %-*s  %s" % (outcome, width, name, detail))
        print("\n" + summary)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base-url", default=os.environ.get("URAAS_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--paper-id", help="paper id for per-paper checks "
                        "(default: first open-access paper in /api/papers/tree)")
    parser.add_argument("--keyword", help="term for /api/keywords/search "
                        "(default: first keyword of the chosen paper)")
    parser.add_argument("--timeout", type=float, default=60.0,
                        help="seconds per request (HF Spaces can be slow to wake)")
    parser.add_argument("--crawl", action="store_true",
                        help="trigger a real UNILAG crawl and check the cooldown")
    parser.add_argument("--crawl-target", type=int, default=1,
                        help="papers for --crawl, 1-50 (default 1)")
    parser.add_argument("--crawl-spider", default="openalex", choices=VALID_SPIDERS)
    parser.add_argument("--rate-limit", action="store_true",
                        help="send a burst to check the 120/min limit returns 429")
    parser.add_argument("--markdown", action="store_true",
                        help="print the report as a Markdown table")
    args = parser.parse_args(argv)

    api_key = os.environ.get("URAAS_API_KEY", "").strip()
    if not api_key:
        print("Set URAAS_API_KEY to the partner key first.", file=sys.stderr)
        return 2
    if not 1 <= args.crawl_target <= 50:
        print("--crawl-target must be 1-50.", file=sys.stderr)
        return 2

    checker = Checker(args.base_url, api_key, args.timeout)
    results = checker.run(paper_id=args.paper_id, keyword=args.keyword,
                          crawl=args.crawl, crawl_target=args.crawl_target,
                          crawl_spider=args.crawl_spider, rate_limit=args.rate_limit)
    print_report(results, checker.base_url, args.markdown)
    return 1 if any(r[1] == FAIL for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
