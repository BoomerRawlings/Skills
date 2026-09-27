# Separate source and visual audits

Audit the completed draft, not only the notes that generated it. Keep source findings and visual findings in separate records outside the final-PDF folder. Record fixes and their verification without retaining a raw session log.

## Pass 1: source and coverage audit

Use an independent reviewer where practical. Give the reviewer source materials, the actual PDF and the coverage map; do not merely ask whether the author's prose seems plausible.

Check:

- Every official question and closing prompt is present with correct wording; answers address each requested part. No entire module or required objective silently disappears.
- Every substantive claim is supported at the cited location. Important caveats, negations, quantities, causal claims and definitions retain their intended scope.
- Slide images and narration agree with the written explanation. Read graph axes, legends, conditions, units and figure captions. When they conflict, investigate the original study or an authoritative source; add a concise, explicitly labeled clarification instead of propagating the conflict.
- A course-specific simplification is distinguished from a general scientific claim. Do not expand association into causation, an illustrative value into a universal limit, or an example into an exclusive rule.
- Supplementary sources actually support the clarification. Verify authors versus editors, title, year, DOI/URL and exact passage/figure. Source existence alone is insufficient.
- Practice tests a taught distinction and its answer is defensible. Hypothetical data and inferred study emphasis are labeled; no claim that generated questions are the professor's real test.
- Citation IDs land on the intended source row, not merely the right page; source links use the correct video and timestamp seconds. Printed filenames correspond to retained files.

Document unresolved findings by location, evidence, needed correction and status. Resolve material findings before the visual audit. If source access prevents closure, report the limit and keep the artifact labeled partial/draft, unless the user explicitly narrows the scope.

## Pass 2: page-by-page visual audit

After source closure, render the actual PDF (normally 120-150 dpi) and view every page individually. A contact sheet may guide triage but does not replace individual inspection.

Inspect hierarchy, title wrapping, meaningful page transitions, column balance, graph labels, image clarity/crop, scientific symbols, citation clusters, short navigation labels, rules, footer clearances and outside folios. Check source-register and answer-key pages as carefully as teaching pages. Verify color is supplementary rather than the sole carrier of meaning.

Fix, regenerate and reinspect affected pages. For a global style change, inspect all pages. If factual content changes, reopen the relevant source audit before the new visual check. A formatting-only change needs coverage and link rechecks, not an unnecessary repeat of all external research.

## Mechanical helper

`scripts/check_pdf.py` is read-only with respect to the input PDF. It checks parseability, page dimensions, replacement characters, internal destination existence/bounds, local linked-file existence, unexpected attachments, expected text/URLs and final SHA-256. It does not fetch websites, understand claims, prove exact source-row correspondence or inspect visual layout.

Invoke with an expected-content file derived from supplied inputs and the authored coverage map, not reverse-engineered from the generated PDF:

```json
{
  "required_text": [
    {"id": "M01-Q1", "text": "Exact supplied question wording"},
    {"id": "M01-A1", "text": "A distinctive required answer passage"}
  ],
  "required_uris": ["https://www.youtube.com/watch?v=VIDEO_ID&t=60s"]
}
```

The example is illustrative: supply actual content, omit unused fields and never ship placeholder IDs/URLs. Include all official questions and all expected answer/content blocks, not just a sample, when checking complete coverage. The helper normalizes whitespace and common typographic punctuation; a missing-text finding still requires inspection rather than changing the expectation to hide an omission.

```text
python scripts/check_pdf.py guide.pdf --expected expected.json --report pdf-check.json
```

Optional `--expect-pages N` is useful only when checking a known final version, never as a fixed target for every packet. `--allow-attachments` is only for an explicitly requested attachment-bearing PDF. Without `--expected`, the result explicitly says coverage was not checked. Exit status 0 means mechanical checks passed, 1 means findings, 2 means invocation/input failure.

## Release record

Preserve final page count, duplex sheet count, artifact hash, supplied-question/answer coverage, source-audit status, per-page visual status and concrete limitations. Recheck the file named in the final response, not an earlier draft. Give concise print instructions. Keep the output folder to the requested final artifact(s); reproducible inputs and audit reports belong in a separate course/project archive.

Do not claim physical printer testing, working remote links, scientific correctness or complete visual inspection based solely on the helper. If a tool is unavailable or cleanup is denied, record that actual limit; do not invent success or create a workaround that bypasses the restriction.
