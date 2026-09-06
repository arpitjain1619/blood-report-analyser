# SPRINT_BOARD.md — Health Report Analyzer (HRA)

> Planning board for expanding the **Blood** Report Analyser into a general
> **Health** Report Analyzer that can read many kinds of medical reports.
>
> **Status: planning only.** Per the project's own rules, this generalization is
> to be scoped deliberately before any implementation — treat this board as the
> scaffold for that scoping, not a locked build order.
>
> **Ordering:** stories are numbered in **dependency / build order** — by the time
> you reach a story, its dependencies are already behind it. HRA-01 is what you
> build first. Each card keeps its **epic tag** (E1–E8) so the thematic grouping
> isn't lost, and a **priority** field (High/Med/Low).
>
> **Story format:** Title/ID → Epic → Type/Priority/Estimate → Description →
> Technical notes → Acceptance criteria → Dependencies.
> **Estimates:** S / M / L / XL. **Prefix:** HRA = Health Report Analyzer.

---

## How to use this board

Columns to move stories through:

```
Backlog  →  To Do (this sprint)  →  In Progress  →  In Review  →  Done
```

Epics (themes, used here as tags rather than sort order):

- **E1 — Reading more report types**
- **E2 — Figuring out what kind of report it is**
- **E3 — Pulling the information out**
- **E4 — Knowing what's normal**
- **E5 — The advice library**
- **E6 — Being extra careful (safety)**
- **E7 — How the app is built (architecture)**
- **E8 — Things that apply across the board (cross-cutting)**

---

## Quick index (in build order)

| ID | Title | Epic | Priority | Est |
|----|-------|------|----------|-----|
| HRA-01 | Flexible extraction schema (numeric vs. narrative) | E3 | High | L |
| HRA-02 | Detect which report type an upload is | E2 | High | M |
| HRA-03 | PDF upload support | E1 | High | M |
| HRA-04 | Resilience on all new AI calls | E8 | High | S |
| HRA-05 | Handle unknown / unsupported report types | E2 | High | S |
| HRA-06 | Expand reference-range data by report type | E4 | High | L |
| HRA-07 | Preserve on-report units & printed ranges | E3 | Med | M |
| HRA-08 | Normalize inconsistent biomarker naming | E3 | Med | M |
| HRA-09 | Report-type-aware pipeline branching | E7 | High | L |
| HRA-10 | Support additional numeric panel types | E1 | High | L |
| HRA-11 | Grow and categorize the knowledge base | E5 | High | L |
| HRA-12 | Report-type-aware retrieval filtering | E5 | Med | M |
| HRA-13 | Per-section / per-biomarker structured output | E7 | Med | M |
| HRA-14 | Per-report-type disclaimers & non-diagnostic framing | E6 | High | M |
| HRA-15 | Responsible handling of critical / alarming values | E6 | High | M |
| HRA-16 | Multi-page & multi-panel uploads | E1 | Med | M |
| HRA-17 | Handle mixed reports (multiple types in one upload) | E2 | Med | M |
| HRA-18 | Extend MCP tool & frontend for type + multi-section | E7 | Med | M |
| HRA-19 | Age/sex-specific reference ranges | E4 | Low | M |
| HRA-20 | Fill known knowledge-base gaps | E5 | Low | S |
| HRA-21 | Decide how to "categorize" narrative findings | E4 | Med | S |
| HRA-22 | Narrative finding extraction | E3 | Med | L |
| HRA-23 | Support narrative / text-based reports | E1 | Med | XL |
| HRA-24 | Safety review gate for higher-stakes types | E6 | High | S |
| HRA-25 | Evaluation approach across report types | E8 | Med | L |
| HRA-26 | Update project docs for the HRA generalization | E8 | Med | S |

---

# Stories (build order)

## HRA-01 · Flexible extraction schema (numeric vs. narrative)
**Epic:** E3 — Pulling the information out · **Type:** Feature · **Priority:** High · **Est:** L

**Description**
As the system, I need a single extraction shape that can represent both numeric
results (`name, value, unit`) and narrative findings (free-text statements), so
different report types can flow through the same pipeline.

**Technical notes**
- Foundational schema change; many stories depend on it — hence first.
- Numeric entries: `{name, value, unit}`; narrative entries: `{finding_text,
  section}` or similar.
- Keep the mock-data shape (`mock_data.py`) in sync so mock mode still works.

**Acceptance criteria**
- [ ] Schema represents numeric and narrative findings without forcing one into
      the other.
- [ ] Existing blood-report flow still works under the new schema.
- [ ] `mock_data.py` updated to match.
- [ ] Downstream steps (categorize, advise) read the new shape.

**Dependencies:** none (foundational)

---

## HRA-02 · Detect which report type an upload is
**Epic:** E2 — Figuring out what kind of report it is · **Type:** Feature · **Priority:** High · **Est:** M

**Description**
As a user, when I upload a report, the system should work out what kind it is
(blood, thyroid, lipid, urine, etc.) so the rest of the pipeline can handle it
correctly. If it can't tell, it should say so rather than guess.

**Technical notes**
- New classification step runs before extraction, feeding its result into
  `analyze_report()`.
- Start simple: keyword/heading matching (rule-based, free) before an AI
  classifier — cheaper and testable, matches the DEC-003 principle.
- If an AI classifier is needed, it's a new AI call → retry/fallback per DEC-011
  (see HRA-04).
- Output a stable `report_type` enum plus a confidence signal; `"unknown"` is a
  valid result.
- Runs in `MOCK_AI=true` mode with a canned type.

**Acceptance criteria**
- [ ] Given a known report type, the correct `report_type` is returned.
- [ ] Given an unfamiliar report, it returns `"unknown"` and the pipeline degrades
      gracefully (no crash, no guessed advice).
- [ ] Given a mixed report, it either flags multiple types or picks the dominant
      one (behavior decided and documented).
- [ ] The result is passed through to the extraction step.
- [ ] Works in mock mode.
- [ ] Decision + reasoning recorded in `DECISIONS.md`.

**Dependencies:** none (foundational)

---

## HRA-03 · PDF upload support
**Epic:** E1 — Reading more report types · **Type:** Feature · **Priority:** High · **Est:** M

**Description**
As a user, I want to upload a PDF report directly, not only a photo/image.

**Technical notes**
- Most lab reports arrive as PDFs; common real path.
- Decide the approach: render PDF pages to images for the vision model, vs. extract
  the PDF's embedded text where present (many lab PDFs have selectable text — often
  more reliable and cheaper than vision).
- A hybrid (use text layer if present, else rasterize + vision) is likely best.
- Keep temp-file cleanup in `finally` per project rules.

**Acceptance criteria**
- [ ] A text-based PDF is analyzed without needing the vision model.
- [ ] A scanned/image-only PDF falls back to vision extraction.
- [ ] Temp files cleaned up on success and failure.
- [ ] Works in `MOCK_AI=true` mode.

**Dependencies:** none (foundational for E1)

---

## HRA-04 · Resilience on all new AI calls
**Epic:** E8 — Cross-cutting · **Type:** Tech · **Priority:** High · **Est:** S

**Description**
As a developer, I want every new AI call (classifier, narrative extractor) to carry
the same retry/fallback/timeout/validation the rest of the system has.

**Technical notes**
- Enforces DEC-011 (resilience on every AI call, not just the first).
- Reuse the existing fallback helper pattern where possible.
- Placed early so it's a habit applied as new AI calls appear, not retrofitted.

**Acceptance criteria**
- [ ] Every new AI call has retry + fallback + timeout + defensive validation.
- [ ] No new AI call ships without it (add to Definition of Done).

**Dependencies:** applies to HRA-02 (if AI-based), HRA-22, and any new AI call

---

## HRA-05 · Handle unknown / unsupported report types gracefully
**Epic:** E2 — Figuring out what kind of report it is · **Type:** Feature · **Priority:** High · **Est:** S

**Description**
As a user, if I upload something the app doesn't support, I want an honest message
rather than made-up analysis.

**Technical notes**
- Consumes the `"unknown"` result from HRA-02.
- No fabricated biomarkers, no guessed advice — mirrors the existing "no article →
  generic guidance only" behavior.

**Acceptance criteria**
- [ ] Unknown type produces a clear "not supported / can't analyze this" response.
- [ ] No hallucinated values or advice are returned.
- [ ] Frontend and MCP tool both surface this state cleanly.

**Dependencies:** HRA-02

---

## HRA-06 · Expand reference-range data by report type
**Epic:** E4 — Knowing what's normal · **Type:** Feature · **Priority:** High · **Est:** L

**Description**
As the system, I need normal ranges for far more markers than today's 19, organized
by report type, so new report types can be categorized.

**Technical notes**
- Extends `reference_ranges.py` (or a restructured version keyed by report type).
- Keep it plain data + rule-based comparison (DEC-003) — no AI for categorization.
- Structure to allow per-type grouping and future age/sex variants (HRA-19).

**Acceptance criteria**
- [ ] Reference data covers all supported numeric report types.
- [ ] Data is organized/queryable by report type.
- [ ] Categorization remains rule-based and correct.

**Dependencies:** HRA-02 (type drives which ranges apply)

---

## HRA-07 · Preserve on-report units and printed reference ranges
**Epic:** E3 — Pulling the information out · **Type:** Feature · **Priority:** Med · **Est:** M

**Description**
As a user, I want the app to keep the units and the normal range printed on my
actual report, since labs differ.

**Technical notes**
- Extraction should capture unit + printed range alongside each value.
- Printed ranges can supplement the app's own reference data (E4) when present.
- Decide precedence: report's printed range vs. app's stored range (document it).

**Acceptance criteria**
- [ ] Units captured per numeric value.
- [ ] Printed reference range captured when present on the report.
- [ ] Precedence rule between printed and stored ranges is defined and applied.

**Dependencies:** HRA-01

---

## HRA-08 · Normalize inconsistent biomarker naming across labs
**Epic:** E3 — Pulling the information out · **Type:** Feature · **Priority:** Med · **Est:** M

**Description**
As the system, I need to recognize that different labs name the same marker
differently (e.g. "SGPT" vs "ALT"), so categorization and advice still match.

**Technical notes**
- Build a synonym/alias map keyed to canonical names.
- Rule-based lookup first (deterministic, free) before any AI normalization.
- Unmapped names → flagged as unknown, not guessed (consistent with current
  "Unknown (no reference range)" behavior).

**Acceptance criteria**
- [ ] Known aliases resolve to the canonical marker name.
- [ ] Unmapped names are flagged, not silently mismatched.
- [ ] Alias map is easy to extend as new labs are seen.

**Dependencies:** HRA-01

---

## HRA-09 · Report-type-aware pipeline branching
**Epic:** E7 — How the app is built · **Type:** Tech · **Priority:** High · **Est:** L

**Description**
As a developer, I want the pipeline to branch by report type while keeping one
shared core, so behavior stays consistent and DRY.

**Technical notes**
- Keep `analyze_report()` as the single source of truth (per project rules); branch
  *within* it or via helpers, don't fork the pipeline.
- Type flows: detect → (numeric | narrative) extraction → type-aware categorize/
  advise.

**Acceptance criteria**
- [ ] One core entry point still serves CLI, API, and MCP.
- [ ] Branching is by report type, no duplicated pipeline logic.
- [ ] Existing blood-report path unchanged in behavior.

**Dependencies:** HRA-01, HRA-02

---

## HRA-10 · Support additional numeric panel types
**Epic:** E1 — Reading more report types · **Type:** Feature · **Priority:** High · **Est:** L

**Description**
As a user, I want to upload common numeric reports beyond blood counts — lipid,
thyroid, liver, kidney, HbA1c, vitamins, hormones — and have them analyzed the
same way blood reports are today.

**Technical notes**
- Reuse the existing pattern (extract → categorize → advise) per new numeric type;
  the difference is data, not flow.
- Add each new type's biomarkers to the reference-range data (HRA-06).
- Start with 2–3 new types to prove the pattern before scaling to all.

**Acceptance criteria**
- [ ] At least 3 new numeric report types analyze end-to-end.
- [ ] Each new type's markers are categorized High/Low/Normal correctly.
- [ ] No regression on existing blood-report analysis.
- [ ] Works in `MOCK_AI=true` mode.

**Dependencies:** HRA-01, HRA-06, HRA-09

---

## HRA-11 · Grow and categorize the knowledge base
**Epic:** E5 — The advice library · **Type:** Feature · **Priority:** High · **Est:** L

**Description**
As the system, I need many more advice articles than today's 14, organized by
report type, so retrieval has good material for every supported type.

**Technical notes**
- Add articles per report type; keep the non-diagnostic, doctor-consult framing in
  the content itself (per project rules).
- Adding/altering articles requires rebuilding `vector_store.json` (embeddings).
- Mind the embedding cost of a much larger corpus.

**Acceptance criteria**
- [ ] Articles exist for all supported report types.
- [ ] Articles are tagged/organized by report type.
- [ ] Vector store rebuilt and retrieval verified for new content.
- [ ] All article content stays non-diagnostic.

**Dependencies:** HRA-02, HRA-06

---

## HRA-12 · Report-type-aware retrieval filtering
**Epic:** E5 — The advice library · **Type:** Feature · **Priority:** Med · **Est:** M

**Description**
As the system, I want retrieval to pull only from articles matching the report
type, so (e.g.) thyroid advice never leaks into a kidney report.

**Technical notes**
- Add report-type metadata to each stored chunk; filter by it at query time.
- Requires storing metadata alongside embeddings in the vector store.

**Acceptance criteria**
- [ ] Retrieval for a given type only returns that type's chunks.
- [ ] Cross-type contamination does not occur in advice.
- [ ] Falls back to generic guidance when no matching chunk exists (existing
      behavior preserved).

**Dependencies:** HRA-11

---

## HRA-13 · Per-section / per-biomarker structured output
**Epic:** E7 — How the app is built · **Type:** Feature · **Priority:** Med · **Est:** M

**Description**
As a user, I want results grouped clearly (per marker or per section) instead of
one blended blob of advice.

**Technical notes**
- Already a pending TODO from the blood-only version; more important with multiple
  sections.
- Advice shape becomes structured (e.g. keyed by marker/section).
- Keep mock data in sync.

**Acceptance criteria**
- [ ] Advice returned as structured, grouped output.
- [ ] Frontend and MCP consume the structured shape.
- [ ] `mock_data.py` matches.

**Dependencies:** HRA-09

---

## HRA-14 · Per-report-type disclaimers & stronger non-diagnostic framing
**Epic:** E6 — Being extra careful · **Type:** Feature · **Priority:** High · **Est:** M

**Description**
As a user of a now-broader, higher-stakes tool, I want clear, appropriate
non-diagnostic framing for each report type, especially serious ones.

**Technical notes**
- Enforce disclaimer in both the prompt and the output (per project rules) — don't
  leave it to the model.
- Serious types (radiology/pathology) get stronger framing.
- Review wording per report type.

**Acceptance criteria**
- [ ] Every report type ends with an appropriate doctor-consult disclaimer.
- [ ] Higher-stakes types carry enhanced non-diagnostic language.
- [ ] No output diagnoses or recommends medication/dosage.

**Dependencies:** HRA-02

---

## HRA-15 · Responsible handling of critical / alarming values
**Epic:** E6 — Being extra careful · **Type:** Feature · **Priority:** High · **Est:** M

**Description**
As a user, if a value is severely out of range, I want it flagged calmly and
responsibly — not with alarm, and never as a diagnosis.

**Technical notes**
- Define what "critical" means per marker (data-driven, rule-based).
- Calm, factual tone; steer toward prompt medical attention without diagnosing.
- Prompt + content both enforce tone.

**Acceptance criteria**
- [ ] Critically abnormal values are identified via rules.
- [ ] Messaging is calm, non-alarming, non-diagnostic.
- [ ] Encourages timely professional consultation.

**Dependencies:** HRA-06, HRA-14

---

## HRA-16 · Multi-page and multi-panel uploads
**Epic:** E1 — Reading more report types · **Type:** Feature · **Priority:** Med · **Est:** M

**Description**
As a user, I want to upload a report that spans several pages or contains several
panels, and have all of it analyzed — not just the first page.

**Technical notes**
- Affects intake + extraction: all pages must reach the extractor.
- Interacts with mixed-report handling (HRA-17).

**Acceptance criteria**
- [ ] A multi-page upload has all pages processed.
- [ ] A report with multiple panels yields results for each panel.
- [ ] Nothing silently dropped; skipped content is reported.

**Dependencies:** HRA-03

---

## HRA-17 · Handle mixed reports (multiple types in one upload)
**Epic:** E2 — Figuring out what kind of report it is · **Type:** Feature · **Priority:** Med · **Est:** M

**Description**
As a user, I want to upload a document that contains several report types at once
(e.g. a full health-checkup packet) and have each section handled.

**Technical notes**
- Detection (HRA-02) must be able to return multiple types.
- Extraction and advice then run per detected section.
- Define behavior clearly: analyze all detected sections vs. dominant only.

**Acceptance criteria**
- [ ] A multi-type upload yields per-section results.
- [ ] Each section is categorized/advised using its own report type's data.
- [ ] Behavior documented in `DECISIONS.md`.

**Dependencies:** HRA-02, HRA-09, HRA-16

---

## HRA-18 · Extend MCP tool & frontend for report type + multi-section results
**Epic:** E7 — How the app is built · **Type:** Feature · **Priority:** Med · **Est:** M

**Description**
As a user, I want the ChatGPT tool and the web UI to show what report type was
detected and display grouped, multi-section results.

**Technical notes**
- MCP tool response + frontend rendering both need the new fields (report type,
  sections).
- Keep frontend/backend contract in sync (a called-out project rule).

**Acceptance criteria**
- [ ] Detected report type is shown to the user in both surfaces.
- [ ] Multi-section results render clearly.
- [ ] Backend/frontend response contract kept in sync.

**Dependencies:** HRA-09, HRA-13

---

## HRA-19 · Age/sex-specific reference ranges
**Epic:** E4 — Knowing what's normal · **Type:** Feature · **Priority:** Low · **Est:** M

**Description**
As a user, I want ranges that reflect age/sex where that's clinically standard, so
my results are judged fairly.

**Technical notes**
- Requires capturing/knowing age + sex (from the report or user input) — privacy
  consideration.
- Only apply where a standard age/sex variance genuinely exists; otherwise use the
  general range.

**Acceptance criteria**
- [ ] Where variants exist, the correct range is chosen by age/sex.
- [ ] Falls back to a general range when age/sex is unknown.
- [ ] Source of age/sex is clear and handled privately.

**Dependencies:** HRA-06

---

## HRA-20 · Fill known knowledge-base gaps
**Epic:** E5 — The advice library · **Type:** Chore · **Priority:** Low · **Est:** S

**Description**
As the system, I want to close known content gaps (e.g. low platelet count) as
coverage broadens.

**Technical notes**
- Track gaps as they're discovered (the current low-platelet gap is a known one).
- Each addition → rebuild vector store.

**Acceptance criteria**
- [ ] Identified gaps have articles added.
- [ ] Vector store rebuilt; retrieval verified.

**Dependencies:** HRA-11

---

## HRA-21 · Decide how to "categorize" narrative findings
**Epic:** E4 — Knowing what's normal · **Type:** Spike/Decision · **Priority:** Med · **Est:** S

**Description**
As the team, I need to decide how narrative findings are assessed, since there's no
number to compare to a range.

**Technical notes**
- Design spike, not a build task — output is a decision in `DECISIONS.md`.
- Options: no categorization (explain only), a coarse normal/attention flag, or
  leave judgement entirely to the doctor (safest).
- Ties directly to safety (E6). Do this before building narrative extraction.

**Acceptance criteria**
- [ ] A documented decision on narrative "categorization" exists in `DECISIONS.md`.
- [ ] The chosen approach is reflected in HRA-22/HRA-23 acceptance criteria.

**Dependencies:** HRA-01

---

## HRA-22 · Narrative finding extraction
**Epic:** E3 — Pulling the information out · **Type:** Feature · **Priority:** Med · **Est:** L

**Description**
As the system, I need to pull the key statements out of a written report so they
can be explained plainly to the user.

**Technical notes**
- Uses the vision/text model with a prompt tuned for extracting findings, not
  numbers.
- New AI usage → retry/fallback per DEC-011 (HRA-04); defensive parsing per rules.

**Acceptance criteria**
- [ ] Key findings extracted from a narrative report as discrete text items.
- [ ] Handles reports with no clear "findings" section gracefully.
- [ ] Works in mock mode.

**Dependencies:** HRA-01, HRA-04, HRA-21

---

## HRA-23 · Support narrative / text-based reports (end-to-end)
**Epic:** E1 — Reading more report types · **Type:** Feature · **Priority:** Med · **Est:** XL

**Description**
As a user, I want to upload reports written as sentences rather than number tables
— e.g. radiology or pathology reports — and get useful, safe, plain-language help
understanding them.

**Technical notes**
- Genuinely different problem: no numeric range, so numeric categorization doesn't
  apply — uses the HRA-21 decision.
- Highest-stakes type — gated by the safety review (HRA-24).
- The hardest phase; deliberately near-last.

**Acceptance criteria**
- [ ] A narrative report is accepted and key findings are extracted as text.
- [ ] Output is plain-language, non-diagnostic, and calm in tone.
- [ ] No numeric categorization is forced onto narrative findings.
- [ ] Enhanced disclaimer for this report type is present (HRA-14).

**Dependencies:** HRA-22, HRA-24, HRA-14

---

## HRA-24 · Safety review gate before enabling higher-stakes types
**Epic:** E6 — Being extra careful · **Type:** Gate/Decision · **Priority:** High · **Est:** S

**Description**
As the team, I want a deliberate safety review gate before narrative/radiology types
go live, since the project explicitly called for extra care here.

**Technical notes**
- A checkpoint, not code — outcome recorded in `DECISIONS.md`.
- Blocks HRA-23 from shipping until passed.

**Acceptance criteria**
- [ ] Documented safety review completed for higher-stakes types.
- [ ] Sign-off recorded before those types are enabled.

**Dependencies:** HRA-14, HRA-15

---

## HRA-25 · Evaluation approach for accuracy across report types
**Epic:** E8 — Cross-cutting · **Type:** Tech/Spike · **Priority:** Med · **Est:** L

**Description**
As the team, I want a way to check the app's answers are actually good across the
many new report types — extraction accuracy, correct categorization, safe advice.

**Technical notes**
- The long-standing "how do you know the output is good?" question, now bigger.
- Start with a small labelled set per report type and spot-checks.
- Not full test automation (still deprioritized per DEC-007) — an evaluation
  discipline, not a unit-test suite.

**Acceptance criteria**
- [ ] A repeatable way to assess extraction + categorization + advice quality per
      type exists.
- [ ] Results recorded so regressions are visible as coverage grows.

**Dependencies:** spans HRA-10, HRA-11, HRA-23

---

## HRA-26 · Update project docs for the HRA generalization
**Epic:** E8 — Cross-cutting · **Type:** Chore · **Priority:** Med · **Est:** S

**Description**
As a developer, I want the core docs updated to reflect the shift from Blood to
Health Report Analyzer, so context stays accurate.

**Technical notes**
- Touch `ARCHITECTURE.md`, `MASTER_CONTEXT.md`, `DECISIONS.md`, `CURRENT_STATUS.md`,
  `TODO.md`, `LEARNING_JOURNAL.md` as each piece lands.
- Record the *why* behind new decisions (per Documentation rules).
- Ongoing — nudge alongside every other story, not a one-off at the end.

**Acceptance criteria**
- [ ] Docs reflect the multi-report-type architecture as it's built.
- [ ] New decisions recorded with reasoning.

**Dependencies:** ongoing, alongside all stories

---

## Suggested first sprint (foundational slice)

The pieces most things depend on — clearing these unblocks the rest:

- **HRA-01** — flexible extraction schema
- **HRA-02** — report-type detection
- **HRA-03** — PDF support
- **HRA-04** — resilience on new AI calls
- **HRA-06** — expanded reference ranges (start with 2–3 types)

That slice lets the first new *numeric* report types (HRA-10) work end-to-end,
proving the pattern before the narrative-report phase (HRA-21 → HRA-22 → HRA-23),
which is the hardest and highest-stakes and is deliberately sequenced last.

---

*Board is planning-only until the HRA generalization is deliberately scoped for
implementation. Adjust IDs, estimates, and ordering to taste before starting.*
