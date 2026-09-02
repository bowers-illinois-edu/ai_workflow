#!/usr/bin/env python3
"""Unit tests for verify_bib.py, the verify-citations first-pass script.

These tests encode the *substantive point* of the script, not input-type in /
output-type out. The expected values are read from the skill specification
(../SKILL.md), so a test that fails means the code disagrees with the spec ---
not that the code changed. In particular:

  * the level ladder L0-L4 (SKILL.md section 3),
  * the failure categories F1-F6 (SKILL.md section 7.1),
  * the discrepancy rules (SKILL.md section 6.2), and
  * the three anchor cases documented in HANDOFF.md section 3:
      - a fabricated/unresolvable DOI -> F1,
      - a real DOI whose sources disagree on year by one (online-first vs
        print) -> L3, flagged not silently passed,
      - the reprint trap: a title search must prefer the 1983 Biometrika
        original over its 2006 book-chapter reprint, and "add discovered DOI"
        must fire only when the retrieved record matches the claim.

The live network wrappers (Client._get, get_json, and the real crossref_doi /
openalex_doi / arxiv_id round-trips) are DELIBERATELY not tested here: offline
determinism is a hard replication requirement, and check_entry takes its
client as a parameter, so a fake client exercises the whole decision logic
without a socket. Mocking urlopen would buy coverage of the HTTP plumbing at
the cost of that determinism; the trade is not worth it.

Run: python3 test_verify_bib.py     (or via the repo-root Makefile: make test)
"""

import os
import sys
import unittest

# scripts/ is not a package and the parent directories contain hyphens, so put
# the script's own directory on the path and import it by its module name.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
import verify_bib as vb  # noqa: E402


# --------------------------------------------------------------- test helpers

def make_rec(source, title, families, year, venue="", volume="", issue="",
             first_page="", doi=""):
    """A retrieved-record dict shaped like crossref_record/openalex_record."""
    return {"source": source, "title": title, "families": list(families),
            "year": year, "venue": venue, "volume": volume, "issue": issue,
            "first_page": first_page, "doi": doi}


def make_claim(title, families, year, venue="", volume="", issue="",
               first_page=""):
    """A claimed-entry dict shaped like claim_from_entry (no source/doi)."""
    return {"title": title, "families": list(families), "year": year,
            "venue": venue, "volume": volume, "issue": issue,
            "first_page": first_page}


def one_entry(bibtext):
    """Parse a .bib string known to hold exactly one checkable entry."""
    entries = vb.parse_bib(bibtext)
    assert len(entries) == 1, "expected one entry, got %d" % len(entries)
    return entries[0]


class FakeClient:
    """A stand-in for verify_bib.Client with canned, deterministic answers.

    check_entry only ever calls these five methods, each returning the
    (record_or_list, error) pair the real client returns. Nothing here touches
    the network, so the tests are reproducible on any machine.
    """

    def __init__(self, doi_records=None, search=None, arxiv=None):
        # doi -> {"crossref": rec_or_None, "openalex": rec_or_None}
        self.doi_records = doi_records or {}
        # "crossref" / "openalex" -> list of candidate records
        self.search = search or {}
        # arxiv id -> record
        self.arxiv = arxiv or {}

    def _doi(self, source, doi):
        entry = self.doi_records.get(doi)
        if entry is None:
            return None, "404"
        rec = entry.get(source)
        return (rec, None) if rec else (None, "404")

    def crossref_doi(self, doi):
        return self._doi("crossref", doi)

    def openalex_doi(self, doi):
        return self._doi("openalex", doi)

    def crossref_search(self, title, first_family):
        return list(self.search.get("crossref", [])), None

    def openalex_search(self, title):
        return list(self.search.get("openalex", [])), None

    def arxiv_id(self, aid):
        rec = self.arxiv.get(aid)
        return (rec, None) if rec else (None, "404")


# Rosenbaum and Rubin (1983), the reprint-trap anchor. The 2006 book chapter
# carries the identical title, which is exactly why title similarity alone is
# not enough (best_candidate docstring; HANDOFF.md section 3).
RR_TITLE = ("The central role of the propensity score in observational "
            "studies for causal effects")
RR_ORIG = make_rec("crossref:10.1093/biomet/70.1.41", RR_TITLE,
                   ["Rosenbaum", "Rubin"], "1983", "Biometrika",
                   "70", "1", "41", "10.1093/biomet/70.1.41")
RR_REPRINT = make_rec("crossref:10.1017/cbo9780511810725.016", RR_TITLE,
                      ["Rubin"], "2006", "Matched Sampling for Causal Effects",
                      "", "", "170", "10.1017/cbo9780511810725.016")


# ------------------------------------------------------- normalization / parse

class TestNormalization(unittest.TestCase):
    """SKILL.md 6.1: normalize before comparing (case, punctuation, accents
    written as ASCII, collapsed whitespace)."""

    def test_strip_latex_removes_commands_and_braces(self):
        self.assertEqual(vb.strip_latex(r"\textbf{Hi}~there--x"), "Hi there-x")

    def test_norm_folds_accents_to_ascii(self):
        # Source stays ASCII: the accented o is written as a \u escape, so the
        # file has no non-ASCII byte, but norm() sees a real accented char at
        # runtime. The \u00f3 escape is an accented o, so the argument reads
        # "Lopez-Lopez" with accented o's; norm() must fold it to "lopez lopez".
        self.assertEqual(vb.norm("L\u00f3pez-L\u00f3pez"), "lopez lopez")

    def test_norm_lowercases_and_strips_punctuation(self):
        self.assertEqual(vb.norm("The {ABC}: A Study!"), "the abc a study")


class TestFamilyNames(unittest.TestCase):
    """SKILL.md 6.2: authors compared as a full list, in order."""

    def test_comma_form(self):
        self.assertEqual(
            vb.family_names("Rosenbaum, Paul R. and Rubin, Donald B."),
            ["Rosenbaum", "Rubin"])

    def test_natural_order_form(self):
        self.assertEqual(
            vb.family_names("Paul R. Rosenbaum and Donald B. Rubin"),
            ["Rosenbaum", "Rubin"])

    def test_and_others_is_dropped(self):
        # "and others" is BibTeX's et al.; it is not a family name.
        self.assertEqual(vb.family_names("Smith, J. and others"), ["Smith"])


class TestIdentifierExtraction(unittest.TestCase):

    def test_doi_from_field(self):
        self.assertEqual(vb.get_doi({"doi": "10.1093/pan/mps038"}),
                         "10.1093/pan/mps038")

    def test_doi_recovered_from_url(self):
        # SKILL.md 2.2 lists URL as an identifier; a doi.org URL carries a DOI.
        self.assertEqual(
            vb.get_doi({"url": "https://doi.org/10.1093/pan/mps038"}),
            "10.1093/pan/mps038")

    def test_doi_trailing_period_stripped(self):
        self.assertEqual(vb.get_doi({"doi": "10.1234/x."}), "10.1234/x")

    def test_arxiv_from_archiveprefix(self):
        self.assertEqual(
            vb.get_arxiv_id({"archiveprefix": "arXiv", "eprint": "2401.12345"}),
            "2401.12345")

    def test_arxiv_from_url(self):
        self.assertEqual(
            vb.get_arxiv_id({"url": "https://arxiv.org/abs/2401.12345"}),
            "2401.12345")

    def test_no_arxiv_id_present(self):
        self.assertEqual(vb.get_arxiv_id({"journal": "Biometrika"}), "")


class TestBibParsing(unittest.TestCase):
    """SKILL.md 2: extract every entry to a verifiable list. Nested braces,
    quoted values, and @string/@comment skipping are the parse hazards."""

    BIB = r"""
@string{PA = "Political Analysis"}

@comment{this whole entry should be ignored}

@article{smith2019,
  author  = {Smith, Jane and Jones, John},
  title   = {The {ABC} of {XYZ}},
  journal = {Journal of Z},
  year    = {2019}
}

@book{doe2020,
  author    = {Doe, John},
  title     = "A Quoted Title",
  publisher = {Academic Press},
  year      = {2020}
}
"""

    def setUp(self):
        self.entries = vb.parse_bib(self.BIB)

    def test_string_and_comment_skipped(self):
        # Two real entries; @string and @comment are not entries.
        self.assertEqual([e["key"] for e in self.entries],
                         ["smith2019", "doe2020"])

    def test_types_captured(self):
        self.assertEqual([e["type"] for e in self.entries],
                         ["article", "book"])

    def test_nested_braces_preserved_in_value(self):
        self.assertEqual(self.entries[0]["fields"]["title"],
                         "The {ABC} of {XYZ}")

    def test_quoted_value_parsed(self):
        self.assertEqual(self.entries[1]["fields"]["title"], "A Quoted Title")


class TestClaimFromEntry(unittest.TestCase):

    def test_fields_extracted(self):
        entry = one_entry(r"""
@article{k,
  author  = {Bowers, Jake and Fredrickson, Mark and Panagopoulos, Costas},
  title   = {Reasoning about Interference},
  journal = {Political Analysis},
  volume  = {21},
  number  = {1},
  pages   = {97--124},
  year    = {2013}
}
""")
        claim = vb.claim_from_entry(entry)
        self.assertEqual(claim["families"],
                         ["Bowers", "Fredrickson", "Panagopoulos"])
        self.assertEqual(claim["year"], "2013")
        self.assertEqual(claim["venue"], "Political Analysis")
        self.assertEqual(claim["volume"], "21")
        self.assertEqual(claim["issue"], "1")
        # first_page is the number before the first dash of the page range.
        self.assertEqual(claim["first_page"], "97")

    def test_venue_falls_back_to_publisher(self):
        entry = one_entry(r"""
@book{b, author = {Doe, J.}, title = {A Book},
  publisher = {Academic Press}, year = {2020}}
""")
        self.assertEqual(vb.claim_from_entry(entry)["venue"], "Academic Press")


# ------------------------------------------------------------- record shaping

class TestRecordShaping(unittest.TestCase):
    """crossref_record / openalex_record turn raw API JSON into the common
    record dict the comparison uses."""

    def test_crossref_record(self):
        msg = {"title": ["A Clean Result"],
               "author": [{"family": "Smith"}, {"family": "Jones"}],
               "issued": {"date-parts": [[2019]]},
               "container-title": ["Journal of Z"],
               "volume": "14", "issue": "3", "page": "100-120",
               "DOI": "10.1/clean"}
        rec = vb.crossref_record(msg)
        self.assertEqual(rec["title"], "A Clean Result")
        self.assertEqual(rec["families"], ["Smith", "Jones"])
        self.assertEqual(rec["year"], "2019")
        self.assertEqual(rec["venue"], "Journal of Z")
        self.assertEqual(rec["first_page"], "100")
        self.assertEqual(rec["doi"], "10.1/clean")

    def test_openalex_record(self):
        w = {"display_name": "A Clean Result",
             "authorships": [{"author": {"display_name": "Jane Smith"}},
                             {"author": {"display_name": "John Jones"}}],
             "publication_year": 2019,
             "primary_location": {"source": {"display_name": "Journal of Z"}},
             "biblio": {"volume": "14", "issue": "3", "first_page": "100"},
             "ids": {"openalex": "https://openalex.org/W123"},
             "doi": "https://doi.org/10.1/clean"}
        rec = vb.openalex_record(w)
        self.assertEqual(rec["families"], ["Smith", "Jones"])
        self.assertEqual(rec["year"], "2019")
        self.assertEqual(rec["source"], "openalex:W123")
        self.assertEqual(rec["doi"], "10.1/clean")


# -------------------------------------------------------------- venue / compare

class TestAbbrevMatch(unittest.TestCase):
    """SKILL.md 6.2: tolerate journal-abbreviation variants."""

    def test_abbreviation_matches_full_name(self):
        self.assertTrue(vb.abbrev_match(
            "J. Am. Stat. Assoc.",
            "Journal of the American Statistical Association"))

    def test_different_journals_do_not_match(self):
        self.assertFalse(vb.abbrev_match(
            "Biometrika",
            "Journal of the American Statistical Association"))


class TestCompare(unittest.TestCase):
    """SKILL.md 6.2: what counts as a discrepancy. compare returns
    (core_ok, full_ok, issues): core = title + first author + year (L2 plus
    the year guard); full adds authors, venue, volume, issue, pages (L3)."""

    def _claim(self, **kw):
        base = dict(title="A Clean Result", families=["Smith", "Jones"],
                    year="2019", venue="Journal of Z", volume="14",
                    issue="3", first_page="100")
        base.update(kw)
        return make_claim(**base)

    def _rec(self, **kw):
        base = dict(source="crossref:x", title="A Clean Result",
                    families=["Smith", "Jones"], year="2019",
                    venue="Journal of Z", volume="14", issue="3",
                    first_page="100")
        base.update(kw)
        return make_rec(**base)

    def test_exact_match(self):
        core, full, issues = vb.compare(self._claim(), self._rec())
        self.assertTrue(core)
        self.assertTrue(full)
        self.assertEqual(issues, [])

    def test_year_off_by_one_breaks_core_and_is_noted(self):
        # SKILL.md 6.2 / 291: year off-by-one is the online-first-vs-print
        # trap and is a discrepancy, not a pass.
        core, full, issues = vb.compare(self._claim(), self._rec(year="2018"))
        self.assertFalse(core)
        self.assertTrue(any("off by one" in i for i in issues))

    def test_venue_abbreviation_tolerated(self):
        # An abbreviation is not a substitution; full_ok must survive it.
        rec = self._rec(venue="J. of Z")
        core, full, issues = vb.compare(self._claim(), rec)
        self.assertTrue(full)
        self.assertEqual(issues, [])

    def test_author_count_mismatch_breaks_full_not_core(self):
        # The reprint signature at field level: same first author and year,
        # but two authors claimed vs one found.
        core, full, issues = vb.compare(
            make_claim(RR_TITLE, ["Rosenbaum", "Rubin"], "1983"),
            make_rec("crossref:x", RR_TITLE, ["Rosenbaum"], "1983"))
        self.assertTrue(core)          # title + first author + year agree
        self.assertFalse(full)         # author count disagrees
        self.assertTrue(any("author count differs" in i for i in issues))

    def test_first_page_mismatch_breaks_full(self):
        core, full, issues = vb.compare(self._claim(), self._rec(first_page="170"))
        self.assertFalse(full)
        self.assertTrue(any("first page differs" in i for i in issues))

    def test_wrong_title_breaks_core(self):
        rec = self._rec(title="An Entirely Different Article About Nothing")
        core, full, issues = vb.compare(self._claim(), rec)
        self.assertFalse(core)
        self.assertTrue(any("title differs" in i for i in issues))


# ------------------------------------------------------------- best_candidate

class TestBestCandidate(unittest.TestCase):
    """The reprint-trap fix (HANDOFF.md section 3). Title similarity alone
    cannot separate a 1983 original from its identically titled 2006 reprint;
    year and venue agreement must break the tie toward the claimed version."""

    def test_prefers_original_over_reprint(self):
        claim = make_claim(RR_TITLE, ["Rosenbaum", "Rubin"], "1983",
                           "Biometrika", "70", "1", "41")
        # Reprint listed first, so a naive "take the top hit" would pick it.
        best = vb.best_candidate(claim, [RR_REPRINT, RR_ORIG])
        self.assertIsNotNone(best)
        self.assertEqual(best["year"], "1983")
        self.assertEqual(best["doi"], "10.1093/biomet/70.1.41")

    def test_two_near_ties_are_ambiguous_not_guessed(self):
        # SKILL.md 7.1 F5: multiple plausible candidates -> defer to Jake.
        claim = make_claim("A Study of Things", [], "")
        c1 = make_rec("crossref:10.1/a", "A Study of Things", ["Smith"],
                      "2019", doi="10.1/a")
        c2 = make_rec("crossref:10.2/b", "A Study of Things", ["Jones"],
                      "2020", doi="10.2/b")
        best, ambiguous = vb.best_candidate(claim, [c1, c2],
                                            return_ambiguity=True)
        self.assertIsNone(best)
        self.assertEqual(len(ambiguous), 2)

    def test_below_threshold_title_is_no_candidate(self):
        claim = make_claim("Completely Unrelated Title Here", [], "1999")
        best = vb.best_candidate(
            claim, [make_rec("crossref:10.9/z",
                             "Something Totally Different Indeed", ["X"],
                             "1999", doi="10.9/z")])
        self.assertIsNone(best)


# ------------------------------------------------------- check_entry (anchors)

class TestCheckEntryAnchors(unittest.TestCase):
    """End-to-end decision logic through check_entry with a fake client.
    These are the cases that ARE the point of the script."""

    def check(self, bibtext, client, do_search=True):
        return vb.check_entry(one_entry(bibtext), client, do_search,
                              lambda msg: None)

    def test_fabricated_doi_is_F1(self):
        # SKILL.md 7.1 F1: supplied DOI does not resolve. HANDOFF anchor
        # "fakepaper2021".
        r = self.check(r"""
@article{fakepaper2021,
  author  = {Nobody, A.},
  title   = {A Study That Does Not Exist},
  journal = {Journal of Nonexistence},
  year    = {2021},
  doi     = {10.9999/jcm.2021.4567}
}
""", FakeClient())  # empty client: every DOI 404s, no search hits
        self.assertEqual(r["level"], "L0")
        self.assertEqual(r["failure"], "F1")
        self.assertEqual(r["action"], "flagged-for-jake")

    def test_year_disagreement_is_L3_F4_and_flagged(self):
        # HANDOFF anchor "bfp2013": Crossref agrees (2013), OpenAlex says 2012
        # (online-first). The entry must land L3/F4 with the discrepancy in
        # the log, NOT silently pass to L4.
        claim_fields = dict(title="Reasoning about Interference Between Units",
                            families=["Bowers", "Fredrickson", "Panagopoulos"])
        doi = "10.1093/pan/mps038"
        cr = make_rec("crossref:%s" % doi, year="2013", venue="Political Analysis",
                      volume="21", issue="1", first_page="97", doi=doi,
                      **claim_fields)
        oa = make_rec("openalex:W2109712249", year="2012",
                      venue="Political Analysis", volume="21", issue="1",
                      first_page="97", doi=doi, **claim_fields)
        client = FakeClient(doi_records={doi: {"crossref": cr, "openalex": oa}})
        r = self.check(r"""
@article{bfp2013,
  author  = {Bowers, Jake and Fredrickson, Mark and Panagopoulos, Costas},
  title   = {Reasoning about Interference Between Units},
  journal = {Political Analysis},
  volume  = {21},
  number  = {1},
  pages   = {97--124},
  year    = {2013},
  doi     = {10.1093/pan/mps038}
}
""", client)
        self.assertEqual(r["level"], "L3")
        self.assertEqual(r["failure"], "F4")
        self.assertTrue(any("off by one" in i for i in r["issues"]))
        self.assertEqual(r["action"], "flagged-for-jake")

    def test_two_sources_agree_is_L4_accepted(self):
        # SKILL.md 3: L4 = metadata cross-confirmed by a second source.
        doi = "10.1/clean"
        fields = dict(title="A Clean Result", families=["Smith", "Jones"],
                      year="2019", venue="Journal of Z", volume="14",
                      issue="3", first_page="100")
        cr = make_rec("crossref:%s" % doi, doi=doi, **fields)
        oa = make_rec("openalex:W999", doi=doi, **fields)
        client = FakeClient(doi_records={doi: {"crossref": cr, "openalex": oa}})
        r = self.check(r"""
@article{clean2019,
  author  = {Smith, Jane and Jones, John},
  title   = {A Clean Result},
  journal = {Journal of Z},
  volume  = {14}, number = {3}, pages = {100--120}, year = {2019},
  doi     = {10.1/clean}
}
""", client)
        self.assertEqual(r["level"], "L4")
        self.assertEqual(r["failure"], "")
        self.assertEqual(r["action"], "accepted as-is")

    def test_discovered_doi_not_added_when_record_mismatches(self):
        # THE regression test for the reprint-trap fix. A title search finds
        # only the 2006 reprint DOI; its record does not match the 1983 claim.
        # SKILL.md 7.3: never auto-insert an unmatched record's DOI.
        client = FakeClient(
            search={"crossref": [RR_REPRINT]},
            doi_records={RR_REPRINT["doi"]: {"crossref": RR_REPRINT,
                                             "openalex": RR_REPRINT}})
        r = self.check(r"""
@article{rosenbaumrubin1983,
  author  = {Rosenbaum, Paul R. and Rubin, Donald B.},
  title   = {The central role of the propensity score in observational studies for causal effects},
  journal = {Biometrika},
  volume  = {70}, number = {1}, pages = {41--55}, year = {1983}
}
""", client)
        self.assertEqual(r["level"], "L1")     # record resolves but disagrees
        self.assertEqual(r["failure"], "F2")   # DOI resolves to a different work
        self.assertFalse(r["action"].startswith("add discovered DOI"))
        self.assertEqual(r["action"], "flagged-for-jake")
        self.assertTrue(any("does not match the claim" in n for n in r["notes"]))

    def test_discovered_doi_added_when_record_matches(self):
        # The other side of the gate (SKILL.md 5.3.5): a discovered DOI whose
        # record DOES match the claim is recommended for the .bib.
        doi = "10.5/found"
        fields = dict(title="A Findable Paper", families=["Smith"],
                      year="2019", venue="Journal of Z", volume="14",
                      issue="3", first_page="100")
        rec = make_rec("crossref:%s" % doi, doi=doi, **fields)
        oa = make_rec("openalex:W7", doi=doi, **fields)
        client = FakeClient(
            search={"crossref": [rec]},
            doi_records={doi: {"crossref": rec, "openalex": oa}})
        r = self.check(r"""
@article{findable,
  author  = {Smith, Jane},
  title   = {A Findable Paper},
  journal = {Journal of Z},
  volume  = {14}, number = {3}, pages = {100--120}, year = {2019}
}
""", client)
        self.assertTrue(r["action"].startswith("add discovered DOI"))
        self.assertIn(doi, r["action"])

    def test_no_record_anywhere_is_F3(self):
        # SKILL.md 7.1 F3: no record found in any source.
        r = self.check(r"""
@article{ghost,
  author  = {Ghost, G.},
  title   = {An Unfindable Title},
  journal = {Nowhere},
  year    = {2020}
}
""", FakeClient())
        self.assertEqual(r["level"], "L0")
        self.assertEqual(r["failure"], "F3")

    def test_ambiguous_search_is_F5(self):
        # SKILL.md 7.1 F5: multiple plausible candidates -> defer to Jake.
        # For the candidates to stay ambiguous they must be EQUALLY plausible:
        # same title, same year, same venue as the claim, differing only in
        # DOI. If one matched the claimed year and the other did not,
        # best_candidate would (correctly) award the year-agreement boost and
        # pick it, and there would be no ambiguity to defer.
        c1 = make_rec("crossref:10.1/a", "Ambiguous Title", ["Smith"],
                      "2019", venue="Journal of Z", doi="10.1/a")
        c2 = make_rec("crossref:10.2/b", "Ambiguous Title", ["Jones"],
                      "2019", venue="Journal of Z", doi="10.2/b")
        # check_entry retries OpenAlex whenever Crossref yields no single best
        # candidate, so both sources must surface the same ambiguous pair for
        # the F5 verdict to survive. This mirrors reality: OpenAlex aggregates
        # Crossref, so it sees the same two records. (A separate, narrow edge
        # -- Crossref ambiguous but OpenAlex empty -> mislabeled F3 -- is
        # reported to Jake, not encoded as the canonical F5 test.)
        client = FakeClient(search={"crossref": [c1, c2],
                                    "openalex": [c1, c2]})
        r = self.check(r"""
@article{amb,
  author  = {Someone, S.},
  title   = {Ambiguous Title},
  journal = {Journal of Z},
  year    = {2019}
}
""", client)
        self.assertEqual(r["failure"], "F5")
        self.assertTrue(any("multiple plausible candidates" in n
                            for n in r["notes"]))

    def test_doi_resolves_to_different_paper_is_F2(self):
        # SKILL.md 4.1 / 7.1 F2: a supplied DOI returns 200 but its metadata
        # disagrees with the claim -- "the most damaging failure mode", a
        # real-looking reference that resolves to a DIFFERENT paper. This is
        # the single scenario the whole tool exists to catch, so it is tested
        # directly, not only through the discovered-DOI path.
        doi = "10.1/real"
        wrong = make_rec("crossref:%s" % doi,
                         "An Unrelated Paper About Something Else",
                         ["Nobody"], "2005", venue="Some Other Journal", doi=doi)
        wrong_oa = make_rec("openalex:W55",
                            "An Unrelated Paper About Something Else",
                            ["Nobody"], "2005", venue="Some Other Journal", doi=doi)
        client = FakeClient(doi_records={doi: {"crossref": wrong,
                                               "openalex": wrong_oa}})
        r = self.check(r"""
@article{misdoi,
  author  = {Smith, Jane and Jones, John},
  title   = {A Clean Result},
  journal = {Journal of Z},
  year    = {2019},
  doi     = {10.1/real}
}
""", client)
        self.assertEqual(r["level"], "L1")   # the DOI resolves...
        self.assertEqual(r["failure"], "F2") # ...but to a different work
        self.assertEqual(r["action"], "flagged-for-jake")

    def test_doi_copied_from_nearby_reference_is_F2(self):
        # SKILL.md 4.1: "the DOI may have been copied from a nearby reference".
        # The title matches but the author list does not -- still F2, because
        # the resolved record is a different work despite the matching title.
        doi = "10.1/near"
        wrong = make_rec("crossref:%s" % doi, "A Clean Result",
                         ["Different", "People"], "2019",
                         venue="Journal of Z", doi=doi)
        client = FakeClient(doi_records={doi: {"crossref": wrong,
                                               "openalex": wrong}})
        r = self.check(r"""
@article{nearby,
  author  = {Smith, Jane and Jones, John},
  title   = {A Clean Result},
  journal = {Journal of Z},
  year    = {2019},
  doi     = {10.1/near}
}
""", client)
        self.assertEqual(r["level"], "L1")
        self.assertEqual(r["failure"], "F2")
        self.assertTrue(any("first author differs" in i for i in r["issues"]))


class TestCheckEntryArxiv(unittest.TestCase):
    """SKILL.md 5.2 / 7.1 F6: preprint handling and the preprint-vs-published
    boundary."""

    ARXIV_BIB = r"""
@article{pre2024,
  author       = {Smith, Jane},
  title        = {A Preprint},
  year         = {2024},
  archiveprefix = {arXiv},
  eprint       = {2401.12345}
}
"""

    def _arxiv_rec(self):
        return make_rec("arxiv:2401.12345", "A Preprint", ["Smith"], "2024",
                        venue="arXiv")

    def test_journal_version_found_is_F6(self):
        journal = make_rec("crossref:10.7/pub", "A Preprint", ["Smith"],
                           "2024", venue="Journal of Z", doi="10.7/pub")
        client = FakeClient(arxiv={"2401.12345": self._arxiv_rec()},
                            search={"crossref": [journal]})
        r = vb.check_entry(one_entry(self.ARXIV_BIB), client, True,
                           lambda m: None)
        self.assertEqual(r["failure"], "F6")
        self.assertTrue(any("journal version may exist" in n for n in r["notes"]))

    def test_arxiv_only_reaches_L3_but_needs_second_source(self):
        # No journal version: the preprint resolves and matches (L3), but a
        # single source cannot reach L4 (SKILL.md 3, 8.3).
        client = FakeClient(arxiv={"2401.12345": self._arxiv_rec()})
        r = vb.check_entry(one_entry(self.ARXIV_BIB), client, True,
                           lambda m: None)
        self.assertEqual(r["level"], "L3")
        self.assertEqual(r["failure"], "")
        self.assertTrue(any("second source" in n for n in r["notes"]))


# ------------------------------------------------------------------ reporting

class TestWriteMarkdown(unittest.TestCase):
    """SKILL.md 9: the verification log. Output must be ASCII (global CLAUDE.md
    rule; API metadata can carry accents) and must surface sub-L4 entries."""

    def test_log_is_ascii_and_lists_flagged_entries(self):
        results = [
            {"key": "clean", "type": "article", "level": "L4", "failure": "",
             "sources": ["crossref:10.1/clean", "openalex:W9"], "issues": [],
             "notes": [], "action": "accepted as-is"},
            {"key": "fake", "type": "article", "level": "L0", "failure": "F1",
             "sources": [], "issues": [], "notes": ["crossref: DOI ... not found"],
             "action": "flagged-for-jake"},
        ]
        text = vb.write_markdown(None, "refs.bib", results)
        text.encode("ascii")  # raises if any non-ASCII slipped through
        self.assertIn("| key | level | failure | sources | action |", text)
        self.assertIn("clean", text)
        self.assertIn("fake", text)
        # The F1 entry is sub-L4, so it must appear in the attention section.
        self.assertIn("Entries needing attention", text)


if __name__ == "__main__":
    unittest.main()
