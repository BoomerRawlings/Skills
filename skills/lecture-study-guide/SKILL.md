---
name: lecture-study-guide
description: "Collect lecture links, transcripts, slides and study questions; organize source files and build a cited, printable study guide with practice questions and separate source and visual audits. Use for a new lecture batch, weekly course packet or revision of an existing guide."
---

# Lecture Study Guide

Turn a lecture batch into retained source material and one compact, printable study guide. Begin with intake when inputs are missing; when they are already supplied, proceed. A request to use this skill authorizes the requested local document work, not LMS submissions, sharing, messages or publishing.

## 1. Establish the batch and collect missing inputs

Read project instructions and state if present. Locate the course root, existing lecture folder, prior guides and supplied attachments. Distinguish a new batch from a revision. Reuse verified existing files rather than requesting them again.

Read [intake-and-sources.md](references/intake-and-sources.md). Ask one compact intake covering only unresolved essentials:

- Course and week/module range; destination if ambiguous.
- Lecture links or files; available transcripts or captions.
- Official study questions, objectives and other assigned material.
- Slide files or links, if available.

Accept unordered links, pasted LMS text and attachments; organize them for the user. Verify titles and module mapping, not just list order. Slides and official questions are optional: if absent, work from supported lecture content and label generated objectives/questions. If lecture content itself is unavailable, request it and continue independent modules; do not invent its contents. Ask any necessary file-upload request in the normal conversation, not a text-only question tool.

Carry forward the user's established defaults: dense but readable, structural prose, no rhetorical filler, one printable PDF, real slides where useful, linked subscript citations, cover/contents, mirrored duplex layout, distinct headings, pitfalls and original testing with a separate answer key. Default to Letter and UCSD navy/blue/gold for this user's course packets; honor a different course theme, paper size or layout when requested. Do not require a formatting questionnaire.

## 2. Preserve and organize the sources

Create a small batch manifest with module IDs, titles, source URLs/files, question IDs and provenance, transcript status, source extent (full lecture, excerpt, notes or unknown), slide provenance and unresolved gaps. Use project-relative paths. Preserve provided raw text separately from cleaned transcripts where useful; do not copy lecture content into this skill. Do not label supplied notes/excerpts as a verbatim or complete transcript, or supplied questions as instructor-authored without evidence.

Prefer supplied transcripts/slides. Otherwise try a suitable caption/transcript mechanism, then an available authorized browser transcript view. Bound retries: after two distinct failed approaches or a repeated access/rate-limit barrier, request missing material and advance supported modules as partial work. Retain the whole requested batch as incomplete until the missing material arrives or the user narrows scope. Avoid large video downloads when captions or selected visible frames suffice. Do not bypass sign-in or access controls. Use available computer-use instructions for browser operations.

Clean transcripts conservatively: remove UI clutter, add punctuation/paragraphs and topical headings, correct obvious caption errors using context, retain substantive examples, qualifications and speaker self-corrections. Preserve original timestamps and flag uncertainty. Keep full cleaned transcripts when user-supplied or otherwise permissible; use source-linked notes when complete reproduction is unavailable or restricted. Summaries and scientific clarifications remain separate from the transcript.

Use stable filenames in the existing lecture folder; for a new structure, `Lectures/` and `Study Guide/` are reasonable defaults. Link each summary to its transcript and source. Save required intermediate material without overwriting unrelated files.

## 3. Plan coverage and write study content

Map every supplied question and substantive objective to notes, an answer and precise source evidence. Preserve supplied wording and distinguish instructor, user, generated or unknown provenance. Include relevant closing lecture retrieval prompts. Group overlapping answers only when every original question remains findable. Do not infer missing answers from the question alone. Claims of coverage are bounded by the supplied source extent; an excerpt-based packet is not evidence of complete lecture coverage.

Write explanations that support reconstruction: definitions, mechanisms in order, comparisons, diagram/graph interpretation, examples, limitations and distinctions likely to be confused. Ground study emphasis in stated objectives, repeated lecture emphasis and worked examples. Describe it as an inference about useful preparation, never privileged knowledge of an actual quiz.

End with pitfalls, original application/retrieval questions and a separately located answer key. Test the taught distinctions, including reasoning errors and boundary cases; explain why plausible wrong answers fail. Label hypothetical scenarios and numerical data. Let coverage and difficulty determine practice count; do not copy the original packet's fixed counts.

## 4. Use real figures and traceable references

Prefer supplied slide pages; otherwise capture relevant original frames with their actual video timestamps. Inspect animation completeness, axes, labels, annotations and lecturer overlays before selecting a frame. Repeat a relevant slide on continuation pages when useful. If no usable slide exists, use a text page; never pass an invented diagram off as a lecture slide.

Attach subscript citations near supported claims. Each citation should identify a stable source-register entry, which links to a video timestamp or exact slide/page/section and the saved companion file. Print human-readable source titles, locations and exact filenames for paper use. Verify source passages, not just working URLs. Clearly distinguish lecture wording from supplementary clarification; a slide and its narration can disagree. Cite authoritative primary/institutional material for corrections.

## 5. Build the printable PDF

Read [print-layout.md](references/print-layout.md). Use an available PDF skill for the environment's creation/rendering contract; otherwise use a suitable local PDF workflow. Discover runtimes, fonts and rendering tools rather than embedding device paths.

Create one final PDF in the course's `Study Guide/` folder unless the user specifies otherwise. Retain sources, authoring inputs and audit records elsewhere. Derive pagination, contents, numbering, references and answer destinations from actual content. Do not force a fixed module count, slide count or page count. Exclude full transcripts from the printable guide by default.

## 6. Audit in two distinct passes

Read [audits.md](references/audits.md). First finish the draft, then audit sources and coverage against the actual PDF. Resolve source findings before the visual pass. Use an independent reviewer when available, preferably someone who did not draft the section; otherwise perform an explicitly separate pass.

Then render and inspect every page individually. Fix cutoffs, broken citation clusters, misleading slide crops, weak hierarchy, imbalance and footer collisions; re-render and inspect changed pages. Layout-only edits still require content/link checks. Never substitute a successful script or a contact sheet for page-by-page visual review.

Use the read-only helper for mechanical checks:

```text
python scripts/check_pdf.py path/to/guide.pdf --expected path/to/expected.json --report path/to/pdf-check.json
```

Resolve the script path relative to this skill. Its expected-content format and limits are documented in the audit reference. A passing helper is not a source or visual audit.

## 7. Deliver and preserve continuity

Verify the exact final PDF, then open/link it with the environment's artifact conventions. Report actual page/sheet counts and print settings concisely. State unresolved source gaps or audit limits honestly; do not claim completeness if a module remains unsupported.

Keep reproducible inputs and separate audit reports outside the final-PDF folder; record meaningful completion state and next inputs in project state when the course work is ongoing. Preserve relative companion-link structure. Clean only known task scratch files, within current permissions; do not retry policy-blocked cleanup through another tool or broaden it. Never package credentials, signed download URLs, browser state or global Codex runtime data. Stop after the requested batch; later skill changes or recurring automation require their own request.
