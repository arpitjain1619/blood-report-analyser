# SPRINT_BOARD.md — Health Report Analyzer (HRA)

> Planning board for expanding the **Blood** Report Analyser into a general
> **Health** Report Analyzer that can read many kinds of medical reports.
>
> **Progress note:** HRA-01 through HRA-15 are complete — their full story blocks
> are retained below (marked done, with completion notes) as a permanent record,
> not collapsed to summaries. Stories from HRA-16 onward were refined against the
> actual completed work — several were partly or wholly overtaken by earlier
> stories, so their scope reflects what genuinely remains.
>
> **Ordering:** dependency / build order. Each card keeps its epic tag (E1-E8) and
> a priority field.
>
> **Story format:** Title/ID -> Epic -> Type/Priority/Estimate -> Description ->
> Technical notes -> Acceptance criteria -> Dependencies.
> **Estimates:** S / M / L / XL. **Prefix:** HRA = Health Report Analyzer.

---

## Epics

- **E1** Reading more report types
- **E2** Figuring out what kind of report it is
- **E3** Pulling the information out
- **E4** Knowing what's normal
- **E5** The advice library
- **E6** Being extra careful (safety)
- **E7** How the app is built (architecture)
- **E8** Things that apply across the board (cross-cutting)

---

## Quick index (build order)

| ID     | Title                                                | Epic | Priority | Est | Status            |
| ------ | ---------------------------------------------------- | ---- | -------- | --- | ----------------- |
| HRA-01 | Flexible extraction schema (numeric vs. narrative)   | E3   | High     | L   | Done              |
| HRA-02 | Detect which report type an upload is                | E2   | High     | M   | Done              |
| HRA-03 | PDF upload support                                   | E1   | High     | M   | Done              |
| HRA-04 | Resilience on all new AI calls                       | E8   | High     | S   | Done              |
| HRA-05 | Handle unknown / unsupported report types            | E2   | High     | S   | Done              |
| HRA-06 | Expand reference-range data by report type           | E4   | High     | L   | Done              |
| HRA-07 | Preserve on-report units & printed ranges            | E3   | Med      | M   | Done              |
| HRA-08 | Normalize inconsistent biomarker naming              | E3   | Med      | M   | Done              |
| HRA-09 | Report-type-aware pipeline branching                 | E7   | High     | L   | Done              |
| HRA-10 | Support additional numeric panel types               | E1   | High     | L   | Done              |
| HRA-11 | Grow and categorize the knowledge base               | E5   | High     | L   | Done              |
| HRA-12 | Report-type-aware retrieval filtering                | E5   | Med      | M   | Done              |
| HRA-13 | Per-section / per-biomarker structured output        | E7   | Med      | M   | Done              |
| HRA-14 | Per-report-type disclaimers & non-diagnostic framing | E6   | High     | M   | Done              |
| HRA-15 | Responsible handling of critical / alarming values   | E6   | High     | M   | Done              |
| HRA-16 | Multi-page resilience (partial success)              | E1   | Med      | S   | Refined           |
| HRA-17 | Handle mixed reports (multiple types in one upload)  | E2   | Med      | L   | Refined           |
| HRA-18 | Surface report type + sections in MCP tool           | E7   | Med      | S   | Split             |
| HRA-19 | Age/sex-specific reference ranges                    | E4   | Low      | M   | Backlog           |
| HRA-20 | Fill known knowledge-base gaps                       | E5   | Low      | S   | Done (via HRA-11) |
| HRA-21 | Decide how to "categorize" narrative findings        | E4   | Med      | S   | Spike - gated     |
| HRA-22 | Narrative finding extraction                         | E3   | Med      | L   | Gated             |
| HRA-23 | Support narrative / text-based reports               | E1   | Med      | XL  | Gated (last)      |
| HRA-24 | Medical review gate (consolidated)                   | E6   | High     | S   | Refined           |
| HRA-25 | Evaluation approach across report types              | E8   | Med      | L   | Backlog           |
| HRA-26 | Refresh core project docs                            | E8   | Med      | M   | Refined (stale)   |

**Cross-cutting (not originally numbered):** Frontend reconnection, MCP auth,
Automated tests, Real deployment. See end of file.

---

# Stories

## HRA-01 - Flexible extraction schema (numeric vs. narrative) - DONE

**Epic:** E3 - **Type:** Feature - **Priority:** High - **Est:** L

**Description**
As the system, I need a single extraction shape that can represent both numeric
results and narrative findings, so different report types can flow through the
same pipeline.

**Technical notes**

- Foundational schema change; many stories depend on it.
- Numeric: {kind:"numeric", name, value, unit, status, ...}; narrative:
  {kind:"narrative", section, finding_text}.
- Keep mock data in sync.

**Acceptance criteria**

- [x] Represents numeric and narrative findings without forcing one into the other.
- [x] Existing blood-report flow still works under the new schema.
- [x] mock_data.py updated to match.
- [x] Downstream steps (categorize, advise) read the new shape.

**Completion note:** Unified typed-findings list (Option A) with a `kind`
discriminator; analyze_report returns {report_type, findings, advice}. Old
biomarkers/categorized keys removed. Verified in mock mode.

**Dependencies:** none (foundational)

---

## HRA-02 - Detect which report type an upload is - DONE

**Epic:** E2 - **Type:** Feature - **Priority:** High - **Est:** M

**Description**
As a user, when I upload a report, the system should work out what kind it is so
the rest of the pipeline handles it correctly. If it can't tell, it should say so
rather than guess.

**Technical notes**

- Classification step; rule-based first (DEC-003). Stable report_type; "unknown"
  is valid. Runs in mock mode.

**Acceptance criteria**

- [x] Known type -> correct report_type.
- [x] Unfamiliar report -> "unknown", graceful, no guessed advice.
- [x] Mixed report -> picks dominant (multi-type deferred to HRA-17).
- [x] Result passed through to extraction.
- [x] Works in mock mode.
- [x] Decision recorded (DEC-021).

**Completion note:** Rule-based detection via signature-marker set intersection
reading report_data.json; min-2-match threshold; "unknown" fallback. No AI call.
(Renumbered from the sample story's original HRA-12.)

**Dependencies:** none (foundational)

---

## HRA-03 - PDF upload support - DONE

**Epic:** E1 - **Type:** Feature - **Priority:** High - **Est:** M

**Description**
As a user, I want to upload a PDF report directly, not only a photo/image.

**Technical notes**

- Render PDF pages to images (PyMuPDF). Multi-page PDF = one report merged.
  Temp-file cleanup in finally.

**Acceptance criteria**

- [x] A PDF is analyzed end-to-end.
- [x] Multi-page PDFs have all pages extracted and merged.
- [x] Temp files cleaned up on success and failure.
- [x] Works across the HTTP path and the MCP path.

**Completion note:** pdf_utils.pdf_to_images (PyMuPDF, no system deps);
\_extract_biomarkers_from_pdf renders+extracts+merges all pages; /analyze-report and
/upload accept application/pdf; MCP tool derives temp-file extension from URL; tool
param renamed image_url->file_url, docstring says image OR PDF. Image-only render
path; text-layer extraction deferred.

**Dependencies:** none (foundational for E1)

---

## HRA-04 - Resilience on all new AI calls - DONE

**Epic:** E8 - **Type:** Tech - **Priority:** High - **Est:** S

**Description**
As a developer, every new AI call must carry the same retry/fallback/timeout/
validation the rest of the system has.

**Technical notes**

- Enforces DEC-011. Reuse the fallback helper pattern.

**Acceptance criteria**

- [x] Every new AI call has retry + fallback + timeout + defensive validation.
- [x] No new AI call ships without it (added to Definition of Done).

**Completion note:** Closed with no code - auditing HRA-01..03 showed no new AI
calls (detection rule-based; PDF non-AI reusing the resilient vision path).
Recorded the guard as a Definition-of-Done item and DEC-022.

**Dependencies:** applies to HRA-02, HRA-22

---

## HRA-05 - Handle unknown / unsupported report types gracefully - DONE

**Epic:** E2 - **Type:** Feature - **Priority:** High - **Est:** S

**Description**
As a user, if I upload something unsupported, I want an honest message rather than
made-up analysis.

**Technical notes**

- Consumes the "unknown" result from HRA-02. No fabricated biomarkers/advice.

**Acceptance criteria**

- [x] Unknown type -> clear "not supported" response.
- [x] No hallucinated values or advice.
- [x] Consistent response shape (same keys as success).

**Completion note:** analyze_report short-circuits on report_type=="unknown" before
categorize/advice, returning the standard shape with empty findings and an honest
unsupported message. Verified.

**Dependencies:** HRA-02

---

## HRA-06 - Expand reference-range data by report type - DONE

**Epic:** E4 - **Type:** Feature - **Priority:** High - **Est:** L

**Description**
As the system, I need normal ranges for far more markers than the original 19,
organized by report type.

**Technical notes**

- Reference data as JSON (DEC-020), organized by type. Categorization stays
  rule-based (DEC-003).

**Acceptance criteria**

- [x] Reference data covers all supported numeric report types.
- [x] Data organized/queryable by report type.
- [x] Categorization remains rule-based and correct.

**Completion note:** Unified report_data.json (Path 1) with five types (blood,
diabetes, lipid, thyroid, vitamins), each holding display_name, signature_markers,
ranges. Three marker kinds - range, direction, bands - all emitting a uniform
status + severity (normal/attention/unassessed). Retired report_types.json and
reference_ranges.py. Values illustrative, pending review (DEC-020).

**Dependencies:** HRA-02

---

## HRA-07 - Preserve on-report units and printed reference ranges - DONE

**Epic:** E3 - **Type:** Feature - **Priority:** Med - **Est:** M

**Description**
As a user, I want the app to keep the units and normal ranges printed on my actual
report, since labs differ.

**Technical notes**

- Extraction captures unit + printed range per marker. Precedence for whose range
  judges the value.

**Acceptance criteria**

- [x] Units captured per numeric value.
- [x] Printed reference range captured when present.
- [x] Precedence rule defined and applied; printed range displayed regardless.

**Completion note:** Extraction returns nested {value, unit, printed_range}.
Precedence: range markers prefer the report's printed range (parsed two-sided AND
one-sided </>), else JSON; bands/direction keep the JSON model. Every finding
carries printed_unit/printed_range for display plus a range_source provenance field
(report/data/none).

**Dependencies:** HRA-01

---

## HRA-08 - Normalize inconsistent biomarker naming across labs - DONE

**Epic:** E3 - **Type:** Feature - **Priority:** Med - **Est:** M

**Description**
As the system, I need to recognize that different labs name the same marker
differently (e.g. "SGPT" vs "ALT"), so categorization and advice still match.

**Technical notes**

- Rule-based alias map (no fuzzy matching - avoids mis-mapping similar names).
  Unmapped names flagged, not guessed.

**Acceptance criteria**

- [x] Known aliases resolve to the canonical marker name.
- [x] Unmapped names pass through unchanged (stay "unknown"), not mis-mapped.
- [x] Alias map easy to extend.

**Completion note:** Per-marker aliases in report_data.json; name_resolver.py builds
a normalized alias->canonical index and resolves names once, upstream of detection
and categorization. Normalization is case/whitespace/punctuation only (exact match
after tidying - deliberately NOT fuzzy, to avoid T3/T4-type mis-mapping). Unknown
names pass through safely.

**Dependencies:** HRA-01

---

## HRA-09 - Report-type-aware pipeline branching - DONE

**Epic:** E7 - **Type:** Tech - **Priority:** High - **Est:** L

**Description**
As a developer, the pipeline should branch by report type while keeping one shared
core.

**Technical notes**

- Keep analyze_report the single source of truth; branch within it. Numeric vs
  narrative paths.

**Acceptance criteria**

- [x] One core entry point still serves CLI, API, and MCP.
- [x] Branching by report category, no duplicated pipeline logic.
- [x] Existing blood path unchanged in behavior.

**Completion note:** category field per type in report_data.json; analyze_report is
an explicit router (extract -> resolve -> detect -> unknown check -> branch by
category). Numeric flow in \_analyze_numeric; narrative path an honest "not
supported yet" stub (\_analyze_narrative) - the seam for HRA-22/23. Numeric behavior
byte-identical.

**Dependencies:** HRA-01, HRA-02

---

## HRA-10 - Support additional numeric panel types - DONE

**Epic:** E1 - **Type:** Feature - **Priority:** High - **Est:** L

**Description**
As a user, I want to upload common numeric reports beyond blood counts and have them
analyzed the same way.

**Technical notes**

- Reuse the pattern per type; data-driven. Mock data + selection for testing.

**Acceptance criteria**

- [x] At least 3 new numeric report types analyze end-to-end.
- [x] Each new type categorized correctly.
- [x] No regression on blood.
- [x] Works in mock mode.

**Completion note:** All five types proven end-to-end in mock mode (range,
direction, bands; both precedence paths; inverted HDL band). Unified MOCK_REPORTS
keyed by type, each owning its biomarkers AND advice together; get_mock_biomarkers/
get_mock_advice; MOCK_REPORT env selects the type. Real vision of new types deferred
(mock skips the model).

**Dependencies:** HRA-01, HRA-06, HRA-09

---

## HRA-11 - Grow and categorize the knowledge base - DONE

**Epic:** E5 - **Type:** Feature - **Priority:** High - **Est:** L

**Description**
As the system, I need many more advice articles than the original set, organized by
report type.

**Technical notes**

- Articles per type; non-diagnostic framing in the content. Rebuild the vector
  store; carry type metadata.

**Acceptance criteria**

- [x] Articles exist for all supported report types.
- [x] Articles tagged/organized by report type.
- [x] Vector store rebuilt and retrieval verified.
- [x] All article content stays non-diagnostic.

**Completion note:** KB rebuilt from scratch as 21 comprehensive articles in type
subfolders (articles/<type>/), consistent template with a "How concerned to be"
section. load_articles.py reads subfolders and tags by type; build_vector_store.py
stores type per chunk (201 chunks, 3072-dim Gemini). Retrieval verified. Content
AI-drafted, PENDING DOCTOR REVIEW (see HRA-24).

**Dependencies:** HRA-02, HRA-06

---

## HRA-12 - Report-type-aware retrieval filtering - DONE

**Epic:** E5 - **Type:** Feature - **Priority:** Med - **Est:** M

**Description**
As the system, retrieval should pull only from articles matching the report type, so
(e.g.) thyroid advice never leaks into a kidney report.

**Technical notes**

- Filter stored chunks by their type metadata at query time.

**Acceptance criteria**

- [x] Retrieval for a type only returns that type's chunks.
- [x] No cross-type contamination.
- [x] Falls back to generic guidance when no matching chunk exists.

**Completion note:** retrieve_relevant_chunks takes report_type and hard-filters
candidates to that type before scoring; empty match -> [] -> generic fallback (and
skips the query embedding). Report type threaded pipeline -> advisor -> retriever.
Also fixed the abnormal-findings filter to test severity=="attention" (was status in
("High","Low"), which missed band statuses). Verified on a real PDF run.

**Dependencies:** HRA-11

---

## HRA-13 - Per-section / per-biomarker structured output - DONE

**Epic:** E7 - **Type:** Feature - **Priority:** Med - **Est:** M

**Description**
As a user, I want results grouped clearly (per finding) instead of one blended blob
of advice.

**Technical notes**

- Structured advice output. Keep mock data in sync.

**Acceptance criteria**

- [x] Advice returned as structured, grouped output.
- [x] mock_data.py matches (mock mode must not break).
- [x] Cross-finding reasoning preserved.

**Completion note:** advice is now {summary, findings:[{name, advice}]} (Shape 1, a
list - robust to model mis-naming keys). One AI call (preserves cross-finding
reasoning). Shared json_utils.extract_json (fence-tolerant) parses it; degrades to
summary-only on parse failure (advice never lost). Mock advice converted to the
structured shape for all five types. Real advisor call confirmed well-formed output.

**Dependencies:** HRA-09

---

## HRA-14 - Per-report-type disclaimers & stronger non-diagnostic framing - DONE

**Epic:** E6 - **Type:** Feature - **Priority:** High - **Est:** M

**Description**
As a user of a broader, higher-stakes tool, I want clear non-diagnostic framing for
each report type.

**Technical notes**

- Enforce disclaimer in code, not just the prompt. Per-type capability.

**Acceptance criteria**

- [x] Every report type ends with an appropriate doctor-consult disclaimer (guaranteed).
- [x] Higher-stakes types can carry enhanced language (mechanism ready).
- [x] No output diagnoses or recommends meds/dosages.

**Completion note:** Guaranteed disclaimer field stamped on every result on the
single exit path (covers numeric, unknown, narrative) - code-controlled, not
model-dependent (closes the fallback-path gap). Shared \_default_disclaimer with
per-type override capability (no duplication); get_disclaimer accessor.

**Dependencies:** HRA-02

---

## HRA-15 - Responsible handling of critical / alarming values - DONE

**Epic:** E6 - **Type:** Feature - **Priority:** High - **Est:** M

**Description**
As a user, if a value is severely out of range, I want it flagged calmly and
responsibly - not with alarm, and never as a diagnosis.

**Technical notes**

- Define "critical" per marker (data-driven, rule-based). Calm, non-alarming,
  non-diagnostic messaging.

**Acceptance criteria**

- [x] Critically abnormal values identified via rules.
- [x] Messaging calm, non-alarming, non-diagnostic.
- [x] Encourages timely professional consultation.

**Completion note:** New "critical" severity. range markers escalate via optional
critical_low/critical_high (defined for Hemoglobin, Platelets, TLC, TSH - a
deliberate subset); bands escalate via per-band critical severity (glucose split so
only >250 is critical). Any critical finding escalates to \_critical_disclaimer.
Verified: Hb 5.0 -> critical, Hb 12.0 -> attention. Critical thresholds AI-drafted,
PENDING DOCTOR REVIEW (priority) - see HRA-24.

**Dependencies:** HRA-06, HRA-14

---

## HRA-16 - Multi-page resilience (partial success) - REFINED

**Epic:** E1 - **Type:** Tech - **Priority:** Med - **Est:** S

**Description**
As a user, if I upload a multi-page PDF and one page can't be read, I still want the
readable pages analyzed, and to be told which page(s) were skipped - not have the
whole report fail.

**Refinement note**
Multi-page PDF merging already exists (HRA-03). The ONLY remaining gap is
resilience - today one failed page raises and kills the entire analysis.
Multi-type panels are HRA-17, not here.

**Technical notes**

- In \_extract_biomarkers_from_pdf, catch per-page failure, keep successful pages,
  collect skipped page numbers.
- Surface skipped pages in the result (e.g. skipped_pages field).
- Preserve temp-image cleanup in finally (already present).

**Acceptance criteria**

- [ ] Multi-page PDF with one unreadable page still returns results from the rest.
- [ ] Skipped pages reported in the result, not silently lost.
- [ ] Fully-successful multi-page PDF unchanged from today.

**Dependencies:** HRA-03 (done)

---

## HRA-17 - Handle mixed reports (multiple types in one upload) - REFINED

**Epic:** E2 - **Type:** Feature - **Priority:** Med - **Est:** L

**Description**
As a user, I want to upload a document containing several report types at once (e.g.
a full health-checkup packet) and have each section handled with its own type's
ranges and advice.

**Refinement note**
Still the biggest remaining engine feature. The pipeline currently assumes ONE type
per report (detects a single dominant type, categorizes everything as that).

**Technical notes**

- Detection must return multiple types from one upload.
- Group markers by type; run categorize + advice per section.
- Multi-section result shape (e.g. sections:[{report_type, findings, advice,
  disclaimer}, ...]).
- Often multi-page -> pairs with HRA-16.

**Acceptance criteria**

- [ ] Multi-type upload yields per-section results.
- [ ] Each section categorized/advised by its own type's data.
- [ ] Result shape holds multiple sections; single-type reports unchanged.
- [ ] Behavior documented in DECISIONS.md.

**Dependencies:** HRA-02, HRA-09 (done); pairs with HRA-16

---

## HRA-18 - Surface report type + sections in the MCP tool - SPLIT

**Epic:** E7 - **Type:** Feature - **Priority:** Med - **Est:** S

**Description**
As an MCP (ChatGPT) user, I want the tool to clearly return the detected report type,
structured advice, disclaimer, and severities.

**Refinement note**
Original HRA-18 covered MCP AND frontend. Split: the frontend half moves to the
Frontend cross-cutting item. This card is the MCP half only, likely mostly VERIFY
(the tool passes through analyze_report's full result) plus a docstring update -
confirm against the current mcp_server/server.py.

**Technical notes**

- Verify the tool returns the new fields (report_type, structured advice,
  disclaimer, severity, later sections).
- Update the tool docstring so the AI host knows what it returns.
- Tool rename (analyze_blood_report) deferred (connector-recreation caveat).

**Acceptance criteria**

- [ ] MCP result includes report type, structured advice, disclaimer.
- [ ] Tool description reflects current behavior.

**Dependencies:** HRA-13, HRA-14 (done); needs code verification

---

## HRA-19 - Age/sex-specific reference ranges - BACKLOG

**Epic:** E4 - **Type:** Feature - **Priority:** Low - **Est:** M

**Description**
As a user, I want ranges that reflect age/sex where clinically standard.

**Refinement note**
Fully intact, still deferred. Age/sex-banded thresholds are high-risk illustrative
data; the trustworthy-data side is harder than the code side and needs review.

**Technical notes**

- Capture age/sex (report or user input) - privacy consideration.
- Data shape for variant ranges; categorization picks the variant; general fallback
  when unknown.

**Acceptance criteria**

- [ ] Correct range chosen by age/sex where variants exist.
- [ ] Falls back to general range when age/sex unknown.
- [ ] Source of age/sex handled privately.

**Dependencies:** HRA-06 (done)

---

## HRA-20 - Fill known knowledge-base gaps - DONE (via HRA-11)

**Epic:** E5 - **Priority:** Low

**Refinement note**
Closed. HRA-11 rebuilt the KB with 21 articles including the previously-missing
low-platelet article (plus low WBC, high platelets, polycythemia, etc.). Ongoing
"add articles as real reports reveal gaps" folds into KB maintenance. The AI-drafted
content review is tracked under HRA-24.

**Original acceptance criteria (met):**

- [x] Identified gaps have articles added.
- [x] Vector store rebuilt; retrieval verified.

**Dependencies:** HRA-11

---

## HRA-21 - Decide how to "categorize" narrative findings - SPIKE (gated)

**Epic:** E4 - **Type:** Spike/Decision - **Priority:** Med - **Est:** S

**Description**
Decide how narrative findings are assessed, since there's no number to compare to a
range. Output is a DECISIONS.md entry, not code.

**Refinement note**
Unchanged. Gates HRA-22/23. Given the stakes, decide this WITH the doctor reviewer.
Options: explain-only, a coarse normal/attention flag, or leave judgement entirely
to the doctor.

**Acceptance criteria**

- [ ] Documented decision in DECISIONS.md.
- [ ] Chosen approach reflected in HRA-22/23 criteria.

**Dependencies:** HRA-01 (done)

---

## HRA-22 - Narrative finding extraction - GATED

**Epic:** E3 - **Type:** Feature - **Priority:** Med - **Est:** L

**Description**
Extract key statements from a written/narrative report (e.g. radiology) so they can
be explained plainly.

**Refinement note**
Hardest extraction work; the narrative branch is currently an honest stub (HRA-09).
New AI call -> resilience per HRA-04. Gated by HRA-21 and HRA-24.

**Acceptance criteria**

- [ ] Key findings extracted from a narrative report as discrete text items.
- [ ] Handles reports with no clear findings section gracefully.
- [ ] Works in mock mode.

**Dependencies:** HRA-01 (done), HRA-21

---

## HRA-23 - Support narrative / text-based reports (end-to-end) - GATED (last)

**Epic:** E1 - **Type:** Feature - **Priority:** Med - **Est:** XL

**Description**
Full end-to-end support for narrative reports (radiology, pathology) with safe,
plain-language explanation.

**Refinement note**
The final, hardest phase. The per-type disclaimer mechanism (HRA-14) is ready to
carry stronger radiology framing. Do last.

**Acceptance criteria**

- [ ] A narrative report is accepted; key findings extracted as text.
- [ ] Output plain-language, non-diagnostic, calm.
- [ ] No numeric categorization forced onto narrative findings.
- [ ] Enhanced disclaimer for the type present.

**Dependencies:** HRA-22, HRA-24, HRA-14 (done)

---

## HRA-24 - Medical review gate (consolidated) - REFINED

**Epic:** E6 - **Type:** Gate/Decision - **Priority:** High - **Est:** S

**Description**
A deliberate medical review pass before the tool's health content is trusted or
before higher-stakes types go live.

**Refinement note**
Broadened from "safety gate before narrative types" to consolidate ALL AI-drafted
medical content pending review into one pass with the doctor friend: the 21 KB
articles (HRA-11), the reference ranges (DEC-020), the critical thresholds (HRA-15),
and higher-stakes-type framing. One review, not several. The project's key safety
gate. Can run in parallel with other work.

**Acceptance criteria**

- [ ] Articles, reference ranges, and critical thresholds reviewed by the doctor.
- [ ] Corrections applied; "pending review" headers updated where signed off.
- [ ] Sign-off recorded before higher-stakes types (HRA-23) go live.

**Dependencies:** HRA-11, HRA-15 (done); ongoing

---

## HRA-25 - Evaluation approach across report types - BACKLOG

**Epic:** E8 - **Type:** Tech/Spike - **Priority:** Med - **Est:** L

**Description**
A repeatable way to assess extraction, categorization, and advice quality across the
five types.

**Refinement note**
Verification so far has been ad hoc (mock runs + one real PDF run). Not a unit-test
suite (DEC-007 still defers those) - an eval discipline: a small labelled set per
type + spot-checks.

**Acceptance criteria**

- [ ] Repeatable per-type quality assessment exists.
- [ ] Results recorded so regressions are visible.

**Dependencies:** spans HRA-10, HRA-11 (done), HRA-23

---

## HRA-26 - Refresh core project docs - REFINED (stale)

**Epic:** E8 - **Type:** Chore - **Priority:** Med - **Est:** M

**Description**
Update the core docs to reflect the current Health Report Analyzer.

**Refinement note**
Bigger than originally scoped. DECISIONS.md is current, BUT ARCHITECTURE.md,
MASTER_CONTEXT.md, CURRENT_STATUS.md, and CLAUDE.md still describe the OLD blood-only,
OpenRouter-based system - they predate BOTH the Claude/Gemini migration AND all the
HRA work, so they'd mislead a new session/contributor. Worth doing sooner rather
than later.

**Technical notes**

- Update provider (OpenRouter -> Claude + Gemini), scope (blood -> five types),
  pipeline shape (findings/severity/disclaimer/structured advice), data model
  (report_data.json), RAG/KB changes.
- Record the why for new decisions.

**Acceptance criteria**

- [ ] Core docs reflect the current architecture, provider, and scope.
- [ ] New decisions recorded with reasoning.

**Dependencies:** ongoing

---

# Cross-cutting items (real, not originally HRA-numbered)

- **Frontend reconnection** - deferred through every story since HRA-01. Still reads
  the old response shape (categorized, string advice); none of the HRA work reaches
  the browser yet. A large, dedicated effort. Absorbs the frontend half of HRA-18.
- **MCP authentication** - still "No Auth" (DEC-016), temporary. Needed before any
  longer-lived/public exposure.
- **Automated tests** - still deferred (DEC-007); production-leaning would want a
  suite eventually.
- **Real deployment** - hosting, CORS tightening, observability: largely untouched.

---

## Suggested sequencing for what's left

1. HRA-16 - page resilience (small; finishes multi-page honestly).
2. HRA-17 - mixed reports (biggest remaining engine feature).
3. HRA-18 - MCP surfacing (verify/small).
4. HRA-26 - docs refresh (stale docs undermine future sessions).
5. HRA-24 - consolidated medical review gate (run in parallel via the doctor).
6. Frontend - dedicated effort (absorbs HRA-18 frontend).
7. HRA-21 -> HRA-22 -> HRA-23 - narrative phase (hardest, gated, last).
8. HRA-19, HRA-25 - age/sex ranges; evaluation (as priorities allow).
9. Production - MCP auth, tests, deployment.

---

_Board reflects work through HRA-15. Completed stories retain full detail (marked
done); remaining stories refined against actual completed work._
