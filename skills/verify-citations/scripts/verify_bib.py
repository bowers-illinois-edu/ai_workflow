#!/usr/bin/env python3
"""Scripted first pass for the verify-citations skill.

Parses a .bib file, checks each entry against Crossref and OpenAlex (and
arXiv for preprints), compares normalized metadata field by field, assigns
each entry a verification level (L0-L4) and, on failure, a category (F1-F6),
and writes a draft verification log in markdown.

The levels follow SKILL.md section 3:
  L0 unchecked; L1 identifier resolves; L2 title and first author match;
  L3 full metadata match within one source; L4 cross-confirmed by a second
  source. L5 (locating the cited claim inside the work) is out of scope
  here and stays manual, as do Passes E and F of section 8.

Stdlib only, so it runs on a bare macOS or Linux python3. ASCII-only output.

Usage:
  python3 verify_bib.py refs.bib [-o log.md] [--json log.json]
      [--mailto EMAIL] [--only key1,key2] [--no-search] [--quiet]

Exit status: 0 if every checked entry reached L4, 2 otherwise, 1 on usage
errors. The exit status exists so a Makefile can gate a submission on it.
"""

import argparse
import difflib
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

DEFAULT_MAILTO = "jwbowers@illinois.edu"
# Crossref and OpenAlex route requests with a mailto to their polite pools,
# which have better rate limits and stability than the anonymous pools.
CROSSREF_DELAY = 0.5
ARXIV_DELAY = 3.0  # arXiv asks for no more than one query every 3 seconds.
TIMEOUT = 30

STOPWORDS = {"of", "the", "and", "for", "in", "on", "a", "an", "de", "der"}


# ---------------------------------------------------------------- bib parsing

def strip_latex(s):
    """Reduce LaTeX markup to comparable plain text (lossy on purpose)."""
    s = re.sub(r"\\[a-zA-Z]+\s*", " ", s)  # commands like \textbf, \'
    s = s.replace("~", " ").replace("--", "-")
    s = re.sub(r"[{}]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def norm(s):
    """Normalization for comparison: ASCII, lowercase, alphanumeric words."""
    s = strip_latex(s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9 ]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def find_matching_brace(text, start):
    """Index just past the brace that closes text[start] ('{' expected)."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return len(text)


def parse_fields(body):
    """Parse 'name = value' pairs from the inside of a bib entry."""
    fields = {}
    i = 0
    n = len(body)
    while i < n:
        m = re.compile(r"\s*([\w-]+)\s*=\s*").match(body, i)
        if not m:
            # Skip to the next comma at depth zero and try again.
            depth = 0
            while i < n and (body[i] != "," or depth != 0):
                if body[i] == "{":
                    depth += 1
                elif body[i] == "}":
                    depth -= 1
                i += 1
            i += 1
            continue
        name = m.group(1).lower()
        i = m.end()
        parts = []
        while i < n:
            if body[i] == "{":
                j = find_matching_brace(body, i)
                parts.append(body[i + 1:j - 1])
                i = j
            elif body[i] == '"':
                j = body.find('"', i + 1)
                j = n if j == -1 else j
                parts.append(body[i + 1:j])
                i = j + 1
            else:
                m2 = re.compile(r"[^,#]*").match(body, i)
                parts.append(m2.group(0).strip())
                i = m2.end()
            # '#' concatenates strings/macros; join naively and move on.
            m3 = re.compile(r"\s*#\s*").match(body, i)
            if m3:
                i = m3.end()
                continue
            break
        fields[name] = re.sub(r"\s+", " ", " ".join(p for p in parts if p)).strip()
        m4 = re.compile(r"\s*,\s*").match(body, i)
        i = m4.end() if m4 else i + 1
    return fields


def parse_bib(text):
    """Return a list of {key, type, fields} dicts; skip @comment/@string."""
    entries = []
    i = 0
    while True:
        at = text.find("@", i)
        if at == -1:
            break
        m = re.compile(r"@\s*([\w-]+)\s*\{").match(text, at)
        if not m:
            i = at + 1
            continue
        etype = m.group(1).lower()
        end = find_matching_brace(text, m.end() - 1)
        if etype in ("comment", "string", "preamble"):
            i = end
            continue
        inner = text[m.end():end - 1]
        km = re.compile(r"\s*([^,\s]+)\s*,").match(inner)
        if not km:
            i = end
            continue
        entries.append({
            "key": km.group(1),
            "type": etype,
            "fields": parse_fields(inner[km.end():]),
        })
        i = end
    return entries


def family_names(author_field):
    """Family names, in order, from a BibTeX author field."""
    fams = []
    for name in re.split(r"\s+and\s+", author_field, flags=re.I):
        name = name.strip()
        if not name or norm(name) == "others":
            continue
        if "," in name:
            fams.append(strip_latex(name.split(",")[0]).strip())
        else:
            toks = strip_latex(name).split()
            fams.append(toks[-1] if toks else name)
    return fams


def get_doi(fields):
    doi = fields.get("doi", "")
    if not doi:
        m = re.search(r"doi\.org/(10\.\S+?)(?:[\s}\"]|$)", fields.get("url", ""))
        doi = m.group(1) if m else ""
    return doi.strip().rstrip(".").replace("https://doi.org/", "")


def get_arxiv_id(fields):
    if norm(fields.get("archiveprefix", "")) == "arxiv" and fields.get("eprint"):
        return fields["eprint"].strip()
    blob = " ".join(fields.get(k, "") for k in ("eprint", "url", "note", "journal", "howpublished"))
    m = re.search(r"(?:arxiv[:.]?\s*|arxiv\.org/abs/)(\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})",
                  blob, flags=re.I)
    return m.group(1) if m else ""


# ------------------------------------------------------------------- lookups

class Client:
    def __init__(self, mailto, quiet):
        self.mailto = mailto
        self.quiet = quiet
        self.last_arxiv = 0.0
        self.ua = "verify-citations-skill/1.0 (mailto:%s)" % mailto

    def _get(self, url):
        req = urllib.request.Request(url, headers={"User-Agent": self.ua})
        last_err = "unknown error"
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                    return r.read().decode("utf-8", "replace"), None
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None, "404"
                last_err = "http %d" % e.code
                if e.code not in (429, 500, 502, 503):
                    return None, last_err
            except Exception as e:  # network down, timeout, bad TLS, ...
                last_err = str(e)
            time.sleep(2.0 * (attempt + 1))
        return None, last_err

    def get_json(self, url):
        body, err = self._get(url)
        if body is None:
            return None, err
        try:
            return json.loads(body), None
        except ValueError as e:
            return None, "bad json: %s" % e

    def crossref_doi(self, doi):
        time.sleep(CROSSREF_DELAY)
        url = "https://api.crossref.org/works/%s?mailto=%s" % (
            urllib.parse.quote(doi, safe=""), self.mailto)
        data, err = self.get_json(url)
        if data is None:
            return None, err
        return crossref_record(data.get("message", {})), None

    def crossref_search(self, title, first_family):
        time.sleep(CROSSREF_DELAY)
        q = {"query.bibliographic": title, "rows": "5", "mailto": self.mailto}
        if first_family:
            q["query.author"] = first_family
        data, err = self.get_json("https://api.crossref.org/works?" + urllib.parse.urlencode(q))
        if data is None:
            return [], err
        return [crossref_record(it) for it in data.get("message", {}).get("items", [])], None

    def openalex_doi(self, doi):
        time.sleep(CROSSREF_DELAY)
        url = "https://api.openalex.org/works/doi:%s?mailto=%s" % (
            urllib.parse.quote(doi, safe=""), self.mailto)
        data, err = self.get_json(url)
        if data is None:
            return None, err
        return openalex_record(data), None

    def openalex_search(self, title):
        time.sleep(CROSSREF_DELAY)
        q = {"search": title, "per_page": "5", "mailto": self.mailto}
        data, err = self.get_json("https://api.openalex.org/works?" + urllib.parse.urlencode(q))
        if data is None:
            return [], err
        return [openalex_record(it) for it in data.get("results", [])], None

    def arxiv_id(self, aid):
        # Respect arXiv's requested 3-second spacing between queries.
        wait = ARXIV_DELAY - (time.time() - self.last_arxiv)
        if wait > 0:
            time.sleep(wait)
        self.last_arxiv = time.time()
        body, err = self._get("http://export.arxiv.org/api/query?id_list=" +
                              urllib.parse.quote(re.sub(r"v\d+$", "", aid)))
        if body is None:
            return None, err
        try:
            root = ET.fromstring(body)
        except ET.ParseError as e:
            return None, "bad xml: %s" % e
        ns = {"a": "http://www.w3.org/2005/Atom"}
        entry = root.find("a:entry", ns)
        if entry is None or entry.find("a:title", ns) is None:
            return None, "404"
        title = (entry.findtext("a:title", "", ns) or "").strip()
        if norm(title) == "error":
            return None, "404"
        authors = [a.findtext("a:name", "", ns) or "" for a in entry.findall("a:author", ns)]
        year = (entry.findtext("a:published", "", ns) or "")[:4]
        return {"source": "arxiv:%s" % aid, "title": title,
                "families": [a.split()[-1] for a in authors if a.split()],
                "year": year, "venue": "arXiv", "volume": "", "issue": "",
                "first_page": "", "doi": ""}, None


def crossref_record(msg):
    titles = msg.get("title") or [""]
    fams, date = [], msg.get("issued", {}).get("date-parts", [[None]])
    for a in msg.get("author", []) or []:
        fams.append(a.get("family") or a.get("name") or "")
    year = date[0][0] if date and date[0] else None
    return {"source": "crossref:%s" % msg.get("DOI", ""),
            "title": titles[0], "families": fams,
            "year": str(year or ""), "venue": (msg.get("container-title") or [""])[0],
            "volume": str(msg.get("volume") or ""), "issue": str(msg.get("issue") or ""),
            "first_page": str(msg.get("page") or "").split("-")[0],
            "doi": msg.get("DOI", "")}


def openalex_record(w):
    fams = []
    for au in w.get("authorships", []) or []:
        name = (au.get("author") or {}).get("display_name") or ""
        fams.append(name.split()[-1] if name.split() else "")
    loc = (w.get("primary_location") or {}).get("source") or {}
    bib = w.get("biblio") or {}
    return {"source": "openalex:%s" % (w.get("ids", {}).get("openalex", "") or "").split("/")[-1],
            "title": w.get("display_name") or "", "families": fams,
            "year": str(w.get("publication_year") or ""), "venue": loc.get("display_name") or "",
            "volume": str(bib.get("volume") or ""), "issue": str(bib.get("issue") or ""),
            "first_page": str(bib.get("first_page") or ""),
            "doi": (w.get("doi") or "").replace("https://doi.org/", "")}


# ---------------------------------------------------------------- comparison

def title_sim(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def abbrev_match(a, b):
    """'J. Am. Stat. Assoc.' should match 'Journal of the American ...'."""
    ta = [t for t in norm(a).split() if t not in STOPWORDS]
    tb = [t for t in norm(b).split() if t not in STOPWORDS]
    if not ta or not tb:
        return False
    short, full = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    j = 0
    for tok in short:
        while j < len(full) and not full[j].startswith(tok):
            j += 1
        if j == len(full):
            return False
        j += 1
    return True


def compare(claim, rec):
    """Compare a claimed entry to a retrieved record.

    Returns (core_ok, full_ok, issues). core_ok = title + first author +
    year agree (the L2 standard plus year, which guards against the
    online-first vs print trap). full_ok adds the remaining claimed fields
    (the L3 standard). Issues are strings for the log.
    """
    issues = []
    core_ok = True

    sim = title_sim(claim["title"], rec["title"])
    if norm(claim["title"]) != norm(rec["title"]) and sim < 0.95:
        issues.append("title differs (similarity %.2f): found %r" % (sim, rec["title"]))
        core_ok = False

    cf, rf = claim["families"], rec["families"]
    if cf and rf:
        if norm(cf[0]) not in norm(rf[0]) and norm(rf[0]) not in norm(cf[0]):
            issues.append("first author differs: claimed %r, found %r" % (cf[0], rf[0]))
            core_ok = False

    if claim["year"] and rec["year"] and claim["year"] != rec["year"]:
        note = " (off by one: online-first vs print?)" if \
            abs(int(claim["year"]) - int(rec["year"])) == 1 else ""
        issues.append("year differs: claimed %s, found %s%s" % (claim["year"], rec["year"], note))
        core_ok = False

    full_ok = core_ok

    if cf and rf:
        if len(cf) != len(rf):
            issues.append("author count differs: claimed %d, found %d" % (len(cf), len(rf)))
            full_ok = False
        else:
            for c, r in zip(cf, rf):
                if norm(c) not in norm(r) and norm(r) not in norm(c):
                    issues.append("author differs: claimed %r, found %r" % (c, r))
                    full_ok = False

    if claim["venue"] and rec["venue"]:
        nv, rv = norm(claim["venue"]), norm(rec["venue"])
        if nv != rv and nv not in rv and rv not in nv and not abbrev_match(nv, rv):
            issues.append("venue differs: claimed %r, found %r" % (claim["venue"], rec["venue"]))
            full_ok = False

    for field in ("volume", "issue"):
        if claim[field] and rec[field] and norm(claim[field]) != norm(rec[field]):
            issues.append("%s differs: claimed %s, found %s" % (field, claim[field], rec[field]))
            full_ok = False

    if claim["first_page"] and rec["first_page"]:
        cp = re.sub(r"\D", "", claim["first_page"])
        rp = re.sub(r"\D", "", rec["first_page"])
        if cp and rp and cp != rp:
            issues.append("first page differs: claimed %s, found %s" %
                          (claim["first_page"], rec["first_page"]))
            full_ok = False

    return core_ok, full_ok, issues


def claim_from_entry(entry):
    f = entry["fields"]
    pages = f.get("pages", "")
    return {"title": f.get("title", ""),
            "families": family_names(f.get("author", f.get("editor", ""))),
            "year": re.sub(r"\D", "", f.get("year", ""))[:4],
            "venue": f.get("journal", f.get("booktitle", f.get("publisher", ""))),
            "volume": f.get("volume", ""), "issue": f.get("number", ""),
            "first_page": pages.split("-")[0].strip() if pages else ""}


# ------------------------------------------------------------- entry checking

MANUAL_TYPES = {"book", "incollection", "inbook", "techreport", "unpublished",
                "misc", "phdthesis", "mastersthesis", "manual"}


def check_entry(entry, client, do_search, log):
    claim = claim_from_entry(entry)
    result = {"key": entry["key"], "type": entry["type"], "level": "L0",
              "failure": "", "sources": [], "issues": [], "notes": [],
              "action": ""}
    doi = get_doi(entry["fields"])
    aid = get_arxiv_id(entry["fields"])
    records = []

    def try_doi(d, discovered=False):
        for name, fn in (("crossref", client.crossref_doi), ("openalex", client.openalex_doi)):
            rec, err = fn(d)
            if rec:
                records.append(rec)
                result["sources"].append(rec["source"])
            elif err == "404":
                result["notes"].append("%s: DOI %s not found" % (name, d))
            else:
                result["notes"].append("%s: lookup failed (%s)" % (name, err))
        if discovered and records:
            result["discovered_doi"] = d

    if doi:
        try_doi(doi)
        if not records and all("not found" in n for n in result["notes"]):
            result["failure"] = "F1"
            if do_search:
                cands, _ = client.crossref_search(claim["title"], claim["families"][:1] and claim["families"][0])
                best = best_candidate(claim, cands)
                if best:
                    result["notes"].append("candidate for the fabricated/typoed DOI: %s (%s)"
                                           % (best["doi"], best["source"]))
    elif aid:
        rec, err = client.arxiv_id(aid)
        if rec:
            records.append(rec)
            result["sources"].append(rec["source"])
            if do_search:
                # A published version should usually be cited instead (F6).
                cands, _ = client.crossref_search(claim["title"], claim["families"][:1] and claim["families"][0])
                best = best_candidate(claim, cands)
                if best and best["doi"]:
                    result["failure"] = "F6"
                    result["notes"].append("journal version may exist: DOI %s; Jake decides which to cite"
                                           % best["doi"])
        elif err == "404":
            result["failure"] = "F1"
            result["notes"].append("arxiv id %s not found" % aid)
        else:
            result["notes"].append("arxiv: lookup failed (%s)" % err)
    elif do_search and claim["title"]:
        cands, err1 = client.crossref_search(claim["title"], claim["families"][:1] and claim["families"][0])
        best, ambiguous = best_candidate(claim, cands, return_ambiguity=True)
        if best is None:
            oa, err2 = client.openalex_search(claim["title"])
            best, ambiguous = best_candidate(claim, oa, return_ambiguity=True)
        if ambiguous:
            result["failure"] = "F5"
            result["notes"].append("multiple plausible candidates; Jake decides: " +
                                   "; ".join("%s (%s)" % (c["title"][:60], c["source"]) for c in ambiguous))
        elif best:
            if best["doi"]:
                try_doi(best["doi"], discovered=True)
            else:
                records.append(best)
                result["sources"].append(best["source"])
        if not records and not ambiguous:
            result["failure"] = "F3"
    else:
        result["notes"].append("no identifier and search disabled; unchecked")

    # Levels from however many records resolved.
    if records:
        result["level"] = "L1"
        comparisons = [compare(claim, r) for r in records]
        core_hits = sum(1 for c in comparisons if c[0])
        full_hits = sum(1 for c in comparisons if c[1])
        for (core_ok, full_ok, issues), r in zip(comparisons, records):
            for msg in issues:
                result["issues"].append("[%s] %s" % (r["source"], msg))
        if core_hits >= 1:
            result["level"] = "L2"
        if full_hits >= 1:
            result["level"] = "L3"
        if full_hits >= 1 and core_hits >= 2 and len(records) >= 2:
            result["level"] = "L4"
        if result["level"] in ("L1",):
            result["failure"] = result["failure"] or "F2"
        elif result["level"] in ("L2", "L3") and result["issues"]:
            result["failure"] = result["failure"] or "F4"
        elif result["level"] == "L3" and len(records) == 1:
            result["notes"].append("only one source resolved; needs a second source for L4")
    elif not result["failure"] and not result["notes"]:
        result["failure"] = "F3"

    # A discovered DOI is only a recommendation when its record matches the
    # claim; a resolving-but-wrong record must go to Jake, not into the .bib.
    if result.pop("discovered_doi", None):
        if result["level"] in ("L2", "L3", "L4"):
            result["action"] = "add discovered DOI %s to the .bib entry" % records[0]["doi"]
        else:
            result["notes"].append("search found DOI %s but its record does not match the claim"
                                   % records[0]["doi"])

    if entry["type"] in MANUAL_TYPES:
        result["notes"].append("entry type %r: manual verification recommended "
                               "(publisher page, Open Library, or archive) per SKILL.md 5.4-5.7"
                               % entry["type"])

    if result["level"] == "L4" and not result["issues"]:
        result["action"] = result["action"] or "accepted as-is"
    elif not result["action"]:
        result["action"] = "flagged-for-jake"
    log("  %s: %s %s" % (entry["key"], result["level"],
                         result["failure"] or ""))
    return result


def best_candidate(claim, cands, return_ambiguity=False):
    """Pick the search hit whose title matches; F5 when two stay close.

    Title similarity alone is not enough: classic papers are reprinted in
    collected volumes under the same title (Rosenbaum and Rubin 1983 also
    exists as a 2006 book chapter), so year and venue agreement break the
    tie in favor of the version the entry actually claims.
    """
    scored = []
    for c in cands:
        if not c["title"]:
            continue
        sim = title_sim(claim["title"], c["title"])
        if sim < 0.93:
            continue
        if claim["year"] and c["year"] == claim["year"]:
            sim += 0.05
        if claim["venue"] and c["venue"]:
            nv, rv = norm(claim["venue"]), norm(c["venue"])
            if nv == rv or nv in rv or rv in nv or abbrev_match(nv, rv):
                sim += 0.03
        scored.append((sim, c))
    scored.sort(key=lambda t: -t[0])
    best = scored[0][1] if scored else None
    ambiguous = []
    if len(scored) > 1 and scored[0][0] - scored[1][0] < 0.02 and \
            scored[0][1].get("doi") != scored[1][1].get("doi"):
        ambiguous = [scored[0][1], scored[1][1]]
        best = None
    if return_ambiguity:
        return best, ambiguous
    return best


# ------------------------------------------------------------------ reporting

def write_markdown(path, bibfile, results):
    lines = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    counts = {}
    for r in results:
        counts[r["level"]] = counts.get(r["level"], 0) + 1
    lines.append("# Verification log: %s" % bibfile)
    lines.append("")
    lines.append("Generated %s by verify_bib.py (scripted first pass; L5, in-text" % now)
    lines.append("consistency, and the plausibility read remain manual --- see the")
    lines.append("verify-citations skill, sections 8.4-8.6).")
    lines.append("")
    lines.append("Levels: " + ", ".join("%s: %d" % (k, counts[k]) for k in sorted(counts)))
    lines.append("")
    lines.append("| key | level | failure | sources | action |")
    lines.append("|-----|-------|---------|---------|--------|")
    for r in results:
        lines.append("| %s | %s | %s | %s | %s |" % (
            r["key"], r["level"], r["failure"] or "-",
            ", ".join(r["sources"]) or "-", r["action"]))
    below = [r for r in results if r["level"] != "L4" or r["issues"]]
    if below:
        lines.append("")
        lines.append("## Entries needing attention")
        for r in below:
            lines.append("")
            lines.append("```")
            lines.append("key: %s" % r["key"])
            lines.append("level: %s%s" % (r["level"], "  failure: %s" % r["failure"] if r["failure"] else ""))
            lines.append("sources tried: %s" % (", ".join(r["sources"]) or "none resolved"))
            for msg in r["issues"]:
                lines.append("discrepancy: %s" % msg)
            for msg in r["notes"]:
                lines.append("note: %s" % msg)
            lines.append("action: %s" % r["action"])
            lines.append("```")
    text = "\n".join(lines) + "\n"
    # The log is plain ASCII by construction of norm(); guard anyway because
    # API metadata (author names, titles) can carry accented characters.
    text = unicodedata.normalize("NFKD", text).encode("ascii", "replace").decode()
    if path:
        with open(path, "w") as fh:
            fh.write(text)
    return text


def main():
    ap = argparse.ArgumentParser(description="Scripted first pass for the verify-citations skill.")
    ap.add_argument("bibfile")
    ap.add_argument("-o", "--output", help="markdown log path (default: stdout)")
    ap.add_argument("--json", dest="json_out", help="also write full results as JSON")
    ap.add_argument("--mailto", default=DEFAULT_MAILTO)
    ap.add_argument("--only", help="comma-separated BibTeX keys to check")
    ap.add_argument("--no-search", action="store_true",
                    help="skip title/author searches for entries without identifiers")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    with open(args.bibfile) as fh:
        entries = parse_bib(fh.read())
    if args.only:
        keep = {k.strip() for k in args.only.split(",")}
        entries = [e for e in entries if e["key"] in keep]
    if not entries:
        print("no entries found", file=sys.stderr)
        return 1

    def log(msg):
        if not args.quiet:
            print(msg, file=sys.stderr)

    client = Client(args.mailto, args.quiet)
    log("checking %d entries..." % len(entries))
    results = [check_entry(e, client, not args.no_search, log) for e in entries]

    text = write_markdown(args.output, args.bibfile, results)
    if not args.output:
        print(text)
    else:
        log("wrote %s" % args.output)
    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump(results, fh, indent=2)

    return 0 if all(r["level"] == "L4" and not r["issues"] for r in results) else 2


if __name__ == "__main__":
    sys.exit(main())
