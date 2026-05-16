# CLAUDE_BIB.md

This file gives an AI assistant (Claude, ChatGPT, or similar) instructions for verifying the bibliography of a paper, memo, talk, grant, or referee response before it leaves the desk. The scope is every citation that appears in a piece of writing intended for an external audience.

This is a companion to:

- `CLAUDE.md` --- general writing style, ASCII discipline, intellectual engagement.
- `CLAUDE_CODING.md` --- coding preferences.
- `CLAUDE_MATH.md` --- mathematical-statistics work. Section 13 of that file states the citation rules at the level of authoring. This file states the rules at the level of verification.

Read this file before declaring a draft ready for submission, posting, circulation, or transmission to a coauthor for sign-off. Run the verification passes (section 8). Report what passed, what failed, and what was not checkable.

ASCII only. Use `---` for em dashes, `--` for en dashes, `->` for arrows, straight quotes, `...` for ellipses. In LaTeX source, use LaTeX commands.

The premise: large language models hallucinate citations. They invent DOIs that look syntactically correct but resolve to nothing. They confidently attribute results to the wrong author, the wrong year, the wrong venue. They merge two real papers into a fictional third. A bibliography that has not been verified through independent external sources is not trustworthy --- regardless of how plausible each entry looks.

The cost of a fabricated citation is high: referee distrust, retraction risk, reputational damage. The cost of verification is low: a few API calls per reference. Run the checks.

---

## 1. When to run this protocol

Run the full protocol when:

- a paper, memo, or grant is about to be submitted, posted, or circulated;
- a referee response is about to be sent;
- a slide deck with cited references will be presented to an external audience;
- a coauthor is about to receive a draft for sign-off;
- any AI assistant (including you) drafted, edited, expanded, or "filled in" the bibliography or any in-text citation.

Run an abbreviated protocol (sections 2--4 only) when:

- adding a single citation during ordinary drafting;
- pulling a reference Jake supplied from memory and you have not yet checked it;
- inheriting a `.bib` file from a previous project.

If you are unsure whether to run the full or abbreviated protocol, run the full one. The marginal cost is small.

---

## 2. Extract the bibliography to a verifiable list

Before checking anything, produce a working list of citations in a stable, line-oriented format. This is the object you will iterate over.

### 2.1 Sources to scan

- the `.bib` file or files used by the document;
- any in-text citation that does not resolve to a `.bib` entry (some workflows allow inline citations);
- footnote-style references in non-BibTeX documents (`.md`, `.docx`, `.qmd` exported to other formats);
- references mentioned in figure or table captions;
- citations inside appendices and supplementary material;
- references inside response-to-reviewer letters.

Do not rely on the rendered PDF alone --- a broken `\cite{}` may not render but the entry still needs verification if it appears in the source.

### 2.2 Per-entry fields to extract

For each reference, record what the document claims:

- **type**: journal article, book, book chapter, working paper, preprint, conference paper, report, website, dataset, software.
- **authors**: full list in stated order, with given and family names.
- **year**: stated publication year.
- **title**: exact title as written.
- **venue**: journal, book publisher, conference, repository.
- **volume, issue, pages**: when applicable.
- **DOI**: if present.
- **arXiv id**: if present (e.g., `2401.12345` or `math.ST/0601001`).
- **URL**: if present and the only identifier.
- **edition / editors**: for books and chapters.
- **BibTeX key**: so you can refer to specific entries unambiguously when reporting.

Build this as a table or a structured list. The verification log in section 9 will refer back to it.

### 2.3 Flag entries the AI may have produced

If you (the assistant) wrote or edited the bibliography in this session or a previous one, mark every entry you touched. AI-touched entries are the highest-priority targets for verification because the failure mode you are guarding against is your own.

If a coauthor used a different AI to draft a section, treat those references as AI-touched until proven otherwise.

---

## 3. Verification levels

Each citation should reach one of the following levels. State the level reached for every entry in the final report.

- **L0 --- unchecked.** No verification performed.
- **L1 --- identifier resolves.** A DOI or arXiv id was supplied and resolves to a real record.
- **L2 --- title and first author match.** The resolved record's title and first author match the claimed values (after normalization for case, punctuation, accents written as ASCII, and trailing punctuation).
- **L3 --- full metadata match.** Authors (full list, in order), year, venue, volume, issue, and pages match the claimed values within a single authoritative source.
- **L4 --- cross-confirmed.** The metadata at L3 is independently confirmed by a second source (e.g., Crossref + OpenAlex, or Crossref + the publisher page, or arXiv + journal record for a published preprint).
- **L5 --- author-confirmed.** For citations that depend on a specific claim (a theorem number, a page reference, a quotation, a numerical result), the cited passage was located in the actual work, not only in metadata.

Submission-grade threshold:

- L4 for every entry, and
- L5 for every citation that is doing real work in the argument (anchoring a method, supplying a number Jake quotes, attributing a specific theorem).

If you cannot reach L4 for an entry, flag it (see section 7) rather than silently leaving it at L2 or L3.

---

## 4. Verification sources

You will use several external sources. Each has different coverage and different failure modes. Use them in combination; do not trust any single one.

### 4.1 Crossref REST API (primary identifier source)

Documentation: `https://www.crossref.org/documentation/retrieve-metadata/` and the REST API at `https://api.crossref.org/`.

Crossref is the registration authority for most journal DOIs. It is the canonical source for "does this DOI exist and what is its metadata?"

Lookups to use:

- **DOI lookup**: `GET https://api.crossref.org/works/{DOI}` --- returns the registered metadata for a DOI. A 404 means the DOI does not exist. A 200 means the DOI is real; you still must compare its metadata to the claim.
- **Bibliographic search**: `GET https://api.crossref.org/works?query.bibliographic=...&query.author=...&rows=5` --- when no DOI is supplied, search by title and author. Inspect the top results and decide whether one matches.
- **Author filter**: `query.author=` with given and family names.
- **Title query**: `query.title=` (exact field) or `query.bibliographic=` (looser).
- **Container title**: `query.container-title=` to constrain by journal.

Polite-pool etiquette: include a `mailto` parameter (`?mailto=jwbowers@illinois.edu`) so Crossref routes your request to the polite pool and provides better rate limits. Use a descriptive User-Agent string when possible.

Failure modes to anticipate:

- DOI returns 404 --- the DOI is fabricated, or there is a typo. Search Crossref by title and author to recover.
- DOI returns 200 but with metadata that disagrees with the claim --- this is the most damaging failure mode and the reason to compare fields, not just check existence.
- DOI resolves but points to a different paper than the title and authors claim --- the DOI may have been copied from a nearby reference.
- Crossref returns no match for a title search --- the venue may not deposit DOIs with Crossref (some social science journals, most books, all working papers). Move to OpenAlex or the publisher site.
- Title differences from typesetting (smart quotes, em dashes, accented characters): normalize both strings before comparing.

### 4.2 OpenAlex (broad coverage, free, programmatic)

Documentation: `https://developers.openalex.org/`.

OpenAlex aggregates Crossref, PubMed, arXiv, ROR, ORCID, and other sources into a unified graph. It often catches works Crossref misses (older papers, working papers, theses, some book chapters).

Lookups to use:

- **DOI lookup**: `GET https://api.openalex.org/works/doi:{DOI}` (URL-encode the DOI or use the `https://doi.org/` form).
- **Title search**: `GET https://api.openalex.org/works?search={title}&per_page=5`.
- **Author + year filter**: `GET https://api.openalex.org/works?filter=author.id:A1234,publication_year:2019`.
- **OpenAlex work ID**: works have stable IDs of the form `W1234567890`; you can record these in the verification log for traceability.

Use OpenAlex as the second source for cross-confirmation at L4. If Crossref says one thing and OpenAlex says another, investigate --- usually OpenAlex is mirroring Crossref, so a disagreement indicates either a recent correction or a problem with one of the records.

Polite-pool etiquette: include `?mailto=jwbowers@illinois.edu`. OpenAlex has generous rate limits in the polite pool.

OpenAlex fields useful for verification: `display_name` (title), `authorships[].author.display_name`, `publication_year`, `primary_location.source.display_name` (venue), `biblio.volume`, `biblio.issue`, `biblio.first_page`, `biblio.last_page`, `doi`, `ids.openalex`, `ids.mag`, `ids.pmid`.

### 4.3 ORCID (author disambiguation)

Documentation: `https://info.orcid.org/documentation/integration-and-api-faq/`. Public API base: `https://pub.orcid.org/v3.0/`.

ORCID is for resolving author identity --- which "J. Smith" wrote this paper. Use it when:

- a citation has an unusual or ambiguous author name and the claim is sensitive (e.g., a specific author's well-known result);
- you suspect an author's name has been corrupted (transliteration, initials swapped, hyphenation lost);
- the author's ORCID is supplied in the `.bib` entry and you want to confirm it matches the work.

Lookups to use:

- **Profile**: `GET https://pub.orcid.org/v3.0/{ORCID}` --- with header `Accept: application/json`.
- **Works list**: `GET https://pub.orcid.org/v3.0/{ORCID}/works` --- returns a person's claimed works, often with DOIs. Useful for confirming "yes, this person did publish this paper."
- **Search**: ORCID's public search is more cumbersome than Crossref's; prefer Crossref/OpenAlex for author search and use ORCID for confirmation once you have a candidate ID.

ORCID does not replace Crossref or OpenAlex --- it is a supplement for author identity. Its main value is catching cases where two scholars share a name and the wrong one was credited.

### 4.4 arXiv (preprints and physics/math/CS literature)

API base: `http://export.arxiv.org/api/query`.

arXiv is the canonical source for preprints in mathematics, statistics, computer science, physics, and several other fields. For citations to preprints, this is the primary source.

Lookups to use:

- **By arXiv id**: `GET http://export.arxiv.org/api/query?id_list={arxiv_id}` --- returns Atom XML with title, authors, abstract, primary category, version history.
- **By title and author**: `GET http://export.arxiv.org/api/query?search_query=ti:%22{title}%22+AND+au:{lastname}&max_results=5`.

arXiv ids come in two formats: pre-April 2007 (`math.ST/0601001`) and post-April 2007 (`2401.12345` or `2401.12345v2`). Strip version suffixes for the canonical id; keep them when the citation refers to a specific version.

Common arXiv-related failure modes:

- A preprint was later published in a journal; the citation should usually point to the journal version. Check whether a journal DOI exists via Crossref or OpenAlex before citing the arXiv id alone.
- The arXiv id is well-formed but does not exist (404). Real ids only.
- The cited content (theorem number, page reference) is in a different version than the one fetched. Note the version explicitly when this matters.

### 4.5 Google Scholar (coverage backstop, no API)

URL: `https://scholar.google.com/scholar?q=...`.

Google Scholar has no public API and aggressively rate-limits scraping. Use it through the WebFetch tool (or equivalent), one query at a time, only when the other sources have failed to confirm a reference.

Useful for:

- citations to books, theses, working papers, conference papers, and government reports that Crossref and OpenAlex miss;
- finding the canonical published version of a working paper;
- confirming that a result exists in the literature when the original citation is incomplete.

Limitations:

- results pages are HTML, not structured data --- parse carefully;
- Google Scholar will sometimes silently block automated requests; if a fetch returns a CAPTCHA page or an empty result, do not retry aggressively;
- Scholar can return mirror sites and predatory journals --- prefer hits that link back to a recognized publisher or to arXiv;
- citation counts are not verification --- a high count does not prove a paper exists as claimed.

When Scholar is the only source that confirms a reference, mark the entry as L2 at best, and note that confirmation is by Scholar alone in the report.

### 4.6 Other useful sources

- **DOI.org resolver** (`https://doi.org/{DOI}`): a 200 response with a real landing page is independent corroboration of L1. A 404 or unresolved redirect is a red flag even if Crossref shows metadata (which can happen for very recently registered DOIs).
- **PubMed and PMC** (`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`): for biomedical references; not typically central to Jake's work but useful when methods papers cross into biostatistics.
- **Semantic Scholar API** (`https://api.semanticscholar.org/`): another aggregator, sometimes useful as a third source, especially for computer science.
- **Zenodo, OSF, Dataverse**: for data and software citations; each has its own DOI registration and metadata API.
- **Publisher landing pages**: a direct check of the journal's article page is the ground truth when an authoritative answer is needed (volume, issue, pages, exact title).
- **The Wayback Machine** (`https://web.archive.org/`): for URLs that have moved or disappeared; record the archived URL alongside the live one if the cited resource is at risk.
- **MathSciNet** and **zbMATH**: paywalled but authoritative for mathematics. If you have access, use them as a third source for math papers.

---

## 5. Per-citation verification protocol

For each entry produced in section 2, do the following. Stop at the first level that fails and record the failure.

### 5.1 If a DOI is supplied

1. Query Crossref: `GET https://api.crossref.org/works/{DOI}?mailto=jwbowers@illinois.edu`. Confirm a 200 response. (L1 candidate.)
2. Compare the returned `title`, `author`, `issued.date-parts`, `container-title`, `volume`, `issue`, `page` to the claim. Flag any mismatch.
3. Query OpenAlex: `GET https://api.openalex.org/works/doi:{DOI}?mailto=jwbowers@illinois.edu`. Confirm matching metadata. (L4 candidate.)
4. For book or chapter DOIs, also confirm `publisher` and `editor` if claimed.
5. If the citation supports a specific claim (a theorem, a number, a quotation), open the article or preprint and locate the claim. (L5.)

### 5.2 If no DOI but an arXiv id is supplied

1. Query arXiv: `GET http://export.arxiv.org/api/query?id_list={arxiv_id}`. Confirm a non-empty result. (L1.)
2. Compare returned title, authors, and submission date to the claim. (L2--L3.)
3. Query Crossref or OpenAlex by title and first author to check whether a journal version exists. If so, prefer the journal DOI in the citation (unless the paper specifically cites the preprint version, e.g., for a result that was revised between preprint and publication).
4. If a journal version exists and is the one being cited, run section 5.1 against the DOI as well.

### 5.3 If neither DOI nor arXiv id is supplied

1. Search Crossref by title and first author. Inspect the top 5 results. If one matches the full metadata, record its DOI and proceed as in section 5.1.
2. If Crossref returns no good match, search OpenAlex by title. OpenAlex covers some works Crossref does not (working papers, theses, older books).
3. If neither finds the work, search arXiv (for technical fields) and Google Scholar (as a backstop).
4. If found in Scholar but not in Crossref or OpenAlex, attempt to retrieve the publisher's landing page directly via WebFetch and confirm the metadata there.
5. If a DOI is discovered during this process, add it to the `.bib` entry --- a citation is more durable with a DOI than without.

### 5.4 If the entry is a book

1. Search Crossref or OpenAlex by title and first author or editor. Books are less reliably indexed than journal articles.
2. Cross-check with the publisher's website for edition, year, ISBN.
3. Record ISBN if available. Open Library (`https://openlibrary.org/`) provides a searchable catalog with ISBNs.
4. For a specific theorem, page, or chapter citation, confirm that the edition cited contains the cited material at the cited location. Different editions paginate differently.

### 5.5 If the entry is a working paper or technical report

1. Working papers often live on author or institutional pages; verify the URL resolves and points to the claimed document.
2. Check whether a published version now exists (Crossref or OpenAlex by title and author). If so, flag for Jake's decision: cite the working paper, the published version, or both.
3. If the URL no longer resolves, find an archived copy (Wayback Machine, SSRN, the author's current homepage). Update the citation; record the archive URL.

### 5.6 If the entry is software or data

1. Cite to a versioned, citable artifact (DOI from Zenodo, CRAN archive, etc.) rather than a moving URL.
2. Confirm the version number cited exists and is documented at the linked location.
3. For R packages, CRAN provides a citation record (`citation("packagename")`); for non-CRAN packages, look for a `CITATION` file or a Zenodo DOI.

### 5.7 If the entry is a website or blog post

1. Confirm the URL resolves.
2. Archive it (Wayback Machine `Save Page Now`) and record the archived URL alongside the live one.
3. Record the access date.
4. If the cited content has changed since first cited, decide with Jake whether to cite the archived version, the live version, or both.

---

## 6. Comparing claimed metadata to retrieved metadata

The point of the lookups is to compare, not just to resolve. A DOI that resolves but with the wrong author list is more dangerous than a missing DOI --- it looks legitimate at first glance.

### 6.1 What to compare, and how

- **Title**: normalize both strings: lowercase, strip leading/trailing punctuation, collapse whitespace, convert non-ASCII to ASCII equivalents (`accent` -> `accent`), strip subtitle delimiters. If they still differ, inspect the difference. Minor punctuation differences are fine; rewording is not.
- **Authors**: compare the full list, in order. Watch for:
  - missing or extra authors,
  - swapped first/last names (especially for non-English names),
  - initials vs full given names,
  - hyphenation (`Lopez-Lopez` vs `Lopez Lopez`),
  - married-name and pseudonym changes,
  - corporate authors written as a person name.
- **Year**: exact match. Year-off-by-one is a common AI failure (especially confusing publication year with preprint year, or online-first year with print year). When the journal has a difference between online and print publication years, prefer the year of formal publication.
- **Venue**: tolerate minor variants (`J. Am. Stat. Assoc.` vs `Journal of the American Statistical Association`) but watch for outright substitution.
- **Volume, issue, pages**: exact match. Page-range errors and volume errors are easy AI failure modes.
- **DOI**: if the DOI was supplied, it must resolve and its registered metadata must match. If the DOI was discovered, record it in the `.bib`.

### 6.2 What counts as a discrepancy

- Title: any non-trivial wording difference. Capitalization, punctuation, and subtitle-separator differences are usually fine. Word substitutions, additions, or deletions are not.
- Authors: any change in the list, the order, or the surname spelling. Given-name initialing is fine.
- Year: any difference.
- Venue: substitution of one journal for another, or any conference-vs-journal swap.
- Pages: any difference.

### 6.3 What to do with a discrepancy

- If the discrepancy is small (capitalization, formatting): correct the `.bib` entry to match Crossref or OpenAlex.
- If the discrepancy is substantive (different author list, different year, different venue): the entry may be wrong, the resolved record may be a different paper, or the discrepancy may reveal a real ambiguity (e.g., a working-paper version vs the published version). Flag the entry and present the discrepancy to Jake with the candidate record so he can decide.
- If the entry cannot be resolved to any record (no match in Crossref, OpenAlex, arXiv, or Scholar): the entry is presumed fabricated until proven otherwise. Flag it with high priority.

---

## 7. Handling failures

A citation that does not reach L4 must be flagged, not silently accepted.

### 7.1 Categories of failure

- **F1 --- no such DOI.** The supplied DOI does not resolve.
- **F2 --- DOI resolves to a different paper.** Authors, title, or year disagree substantively.
- **F3 --- no record found.** No Crossref, OpenAlex, arXiv, or Scholar hit for the title and authors as claimed.
- **F4 --- partial record only.** The paper exists but a field of the citation is wrong (e.g., wrong volume, wrong pages, wrong year).
- **F5 --- ambiguous match.** Multiple plausible candidate records; cannot determine which one the citation refers to without Jake's input.
- **F6 --- preprint cited as published, or vice versa.** A journal version exists but the citation points to the preprint, or the cited published version has not actually appeared.
- **F7 --- specific claim not located.** The work exists and matches the citation, but the specific claim (theorem number, page reference, quotation) could not be located in the work.

### 7.2 What to do for each category

- F1, F3: do not silently delete the entry. Present it to Jake as suspected-fabricated, along with the best candidate (if any) found in the alternate sources.
- F2, F4: present the discrepancy to Jake with the candidate corrected entry. Do not auto-correct an entry whose correction would change the meaning of the in-text claim (e.g., if a different author is correct, the substantive citation may also be wrong).
- F5: present the candidates; ask Jake to choose.
- F6: ask Jake which version to cite. The choice matters when a result changed between versions.
- F7: locate the actual cited claim or flag the in-text claim itself as needing rechecking; this is often a symptom of a citation that was generated to support a sentence rather than the sentence being grounded in a source.

### 7.3 Never do these

- Never silently insert a citation that an AI assistant produced without verifying it.
- Never silently delete a citation that fails verification --- the substance the citation supports may also be wrong, and Jake needs to know.
- Never replace a failed citation with a "similar" one without Jake's approval. Doing so changes the substantive claim.
- Never paraphrase a citation in a way that strengthens the cited claim (see CLAUDE_MATH.md section 13.2).

---

## 8. Verification passes

Run the applicable passes before declaring the bibliography ready. Report which were run.

### 8.1 Pass A --- existence

For every entry, confirm the work exists. At minimum, every entry reaches L1 (if DOI/arXiv id supplied) or L2 (title and first author match in at least one external source).

### 8.2 Pass B --- metadata match

For every entry, confirm the bibliographic metadata in the `.bib` matches the resolved record. Every entry reaches L3.

### 8.3 Pass C --- cross-confirmation

For every entry, confirm the metadata in two independent sources. Every entry reaches L4. Typical pairs: Crossref + OpenAlex; Crossref + publisher page; arXiv + journal DOI for a preprint-then-published paper.

### 8.4 Pass D --- substantive claim location

For every citation that supports a specific claim, locate the claim in the cited work. This may mean opening the PDF and finding theorem 3.2 on page 47. Every such entry reaches L5.

This pass is the most expensive and the most valuable. Skipping it is how a citation can be technically correct (the paper exists and the metadata matches) while the in-text claim is false (the paper does not say what we say it says).

### 8.5 Pass E --- in-text consistency

For every in-text citation (`\cite{key}`), confirm:

- the `key` resolves to a `.bib` entry;
- the entry has been verified at L4 (or L5 if substantive);
- the surrounding sentence describes the cited work accurately --- author count ("Smith and Jones, 2019" not "Smith, 2019" if there are two authors), year, and substance.

A `.bib` may be clean while in-text citations still misrepresent the count of authors, the year, or the substance.

### 8.6 Pass F --- non-AI sanity check

Read the entire bibliography once more without using API tools, just looking for plausibility. Some failure modes survive automated checking:

- a journal that does not publish in the field of the cited paper;
- an author who is not known to work in this area;
- a year before the cited author began publishing or after they died;
- a venue that no longer exists in the cited year;
- a page range that is implausibly long or short for the venue.

Jake's domain knowledge is the strongest filter for these. If you notice anything implausible, flag it for him.

### 8.7 Reporting rule

Do not say "checked." Say what was checked and what was found.

Good:

- "Reached L4 for 32 of 35 entries via Crossref + OpenAlex. Entries `smith2020`, `jones2019`, `lee2021` did not reach L4; details below."
- "Pass D run for 8 entries that anchor specific theorems; 7 located, 1 (`vapnik1998`, theorem 3.2) not located at the cited page --- the relevant result appears at p. 134, not p. 47."

Bad:

- "Bibliography verified."

---

## 9. Verification log

Produce a verification log as a structured table or list. The log is the artifact Jake reviews. Include, per entry:

- BibTeX key,
- citation (short form: author, year, short title),
- level reached (L0--L5),
- sources consulted (e.g., `crossref:DOI`, `openalex:W...`, `arxiv:2401.12345`, `scholar`),
- discrepancies found,
- action taken (`accepted as-is`, `corrected: <field> changed from X to Y`, `flagged: <reason>`, `flagged-for-jake: <decision needed>`),
- timestamp.

The log goes in the project repository (typical location: `bib_verification.md` or in `notes/`), not in the published paper. Jake can then re-run verification incrementally on later drafts: entries already at L4 with unchanged metadata do not need re-checking.

For entries that did not reach L4, the log entry should make it easy to decide what to do next:

```
key: smith2020
claim: "Smith, J. (2020). The X of Y. Journal of Z, 14(3), 100-120."
sources tried: crossref (no DOI match), openalex (no match), arxiv (no match), scholar (no match)
status: F3 --- no record found in any source
recommendation: appears fabricated; Jake should remove the citation or supply a correct reference
```

---

## 10. Special cases

### 10.1 Bowers's own work

When verifying citations to Jake's own papers, two extra checks:

- the ORCID `0000-0002-4048-1166` should match;
- the canonical short citation Jake uses for the paper in conversation should match the bibliographic entry.

The point is not redundant checking but consistency: if Jake refers to "the 2017 PA paper" and the `.bib` has it under a different year or venue, one of them is wrong.

### 10.2 Self-citation from a working paper

When citing a working paper that Jake or a coauthor has written, check whether the working paper has since become a published article. If yes, prefer the published citation unless the in-text claim refers to a version that differs between preprint and publication.

### 10.3 Citations to forthcoming work

For "forthcoming" or "in press" citations, verify with the publisher that the article is in the production queue. A genuine "forthcoming" should have a DOI reserved (Crossref will show it with a status indicating acceptance). If no record exists at all, the citation is to a manuscript, not a forthcoming article, and should be cited as such.

### 10.4 Citations to a specific version of a software package

Cite to a versioned release (CRAN archive, Zenodo DOI for a tagged release, or a permalink that includes a commit hash for a git repository). Confirm the version cited matches the version used for the result the citation supports.

### 10.5 Citations to a specific dataset

Cite to a versioned, citable artifact. Confirm the version, the access date, and the location resolve. Replication packages often have their own DOIs (Dataverse, ICPSR).

### 10.6 Page-range citations to long works

For a citation to a specific page or section of a book or long report, verify the edition. Page numbers differ between editions. If the citation does not specify an edition and the page number is to a substantive claim, ask Jake which edition was consulted.

### 10.7 Citations attached to a quotation

For any cited quotation, locate the quotation in the source and confirm it appears as quoted (allowing for minor formatting differences). Misquotation is a separate failure mode from misattribution and both are caught at this step.

---

## 11. Workflow

A practical run-through for a paper draft:

1. Extract every reference from the document into a list (section 2). Record the BibTeX key, the claimed fields, and whether an AI assistant produced or edited the entry.
2. For each entry, run the verification protocol (section 5) using the sources in section 4 in the order: DOI -> Crossref -> OpenAlex -> arXiv -> ORCID -> Scholar -> publisher page.
3. Record each lookup in the verification log (section 9). Note the level reached and any discrepancies.
4. After the per-entry passes, run passes A--E in turn. For Pass D, identify the citations that do real work (anchor a theorem, supply a number, support a quotation) and locate each cited claim in the source.
5. Run pass F (non-AI sanity check) to catch plausibility failures the APIs miss.
6. Produce a report for Jake with three sections: (a) entries that reached L4 with no action needed; (b) entries that reached L4 only after correction, with the correction described; (c) entries that did not reach L4 and require Jake's decision.

For incremental verification on a later draft, only re-check entries whose `.bib` fields changed since the last verification log timestamp, and any entries marked AI-touched in the new draft.

---

## 12. Tooling notes

You will typically need:

- a JSON parser to read Crossref, OpenAlex, ORCID, Semantic Scholar responses;
- an XML/Atom parser for arXiv responses (or a regex if the parse is shallow);
- an HTML fetcher for Google Scholar and publisher pages;
- a string-normalization function for comparing titles and author names;
- a way to URL-encode DOIs (forward slashes and special characters must be encoded).

When the WebFetch tool returns truncated content, request specific endpoints rather than HTML pages where possible --- the JSON APIs from Crossref and OpenAlex are stable and parseable.

When the user's environment provides a tool like `curl` via Bash, prefer that for API calls because it is auditable and the response is fully visible. Use WebFetch when the only sensible interface is HTML.

Rate limits: Crossref and OpenAlex are generous in the polite pool. arXiv asks for one query every 3 seconds. ORCID public API is unauthenticated and rate-limited; do not loop aggressively. Google Scholar will block you fast --- use it sparingly.

---

## 13. Final checklist

Before declaring the bibliography ready:

1. Every entry reached at least L4, or is flagged with a specific reason.
2. Every citation that supports a substantive claim reached L5.
3. The verification log records, per entry, the sources consulted, the level reached, and any corrections made.
4. AI-touched entries are explicitly identified and verified at the same standard as Jake-written entries.
5. In-text citations are consistent with the `.bib`: author counts, years, and surrounding prose match the source.
6. Entries that failed verification were presented to Jake for decision, not silently dropped or replaced.
7. The sanity-check pass (8.6) flagged no implausibilities, or any flags were resolved.
8. Citations to specific pages, theorems, equations, or quotations were located in the actual work.
9. Forthcoming, working-paper, software, and dataset citations are cited to versioned, resolvable artifacts.
10. The verification log is committed to the project repository so the next draft can verify incrementally.

If any of these is no, name what is missing rather than describing the bibliography as ready.

---

## Closing note

A fabricated citation is a quiet failure --- it looks like a real reference, it survives a quick read, and a casual reviewer may not catch it. A referee who does catch it has every reason to wonder what else in the paper was invented.

The protocol in this file is verbose because the failure mode is subtle. Each lookup is cheap. The verification log is reusable across drafts. The cost compounds slowly; the savings (in trust, in retraction risk, in time spent answering "where does this claim come from?") compound quickly.

When in doubt, check one more source. When still in doubt, flag it for Jake.
