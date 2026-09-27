# Intake, source files and traceability

## Opening exchange

Inventory first. If a user says only "make this week's guide," a useful intake is:

> I found the existing course folder and will reuse its format. Send the week/module range, lecture links or files, and any study questions. Include transcripts or slides if you have them; they can arrive separately.

Adapt this to what is missing. If the class or destination is unclear, ask for it. If all inputs are already present, state the interpreted batch and begin. For an existing guide revision, inspect its authoring files and change the requested part without restarting intake. Asking for lecture inputs is a stage, not a mandatory interruption on every invocation.

Do not treat "optional slides" as a blocker. Distinguish:

| Available | Action |
|---|---|
| Transcript + questions + slides | Map, clean, cite and build. |
| Video link + questions | Verify video/module; retrieve captions or transcript if available. |
| Transcript without video/timestamps | Cite exact saved-file headings or paragraph IDs; do not fabricate times. |
| Lecture content without questions | Generate clearly labeled study objectives and original practice. |
| Questions without accessible lecture content | Preserve the questions; request source content before presenting lecture-grounded answers. General background, if requested, must be labeled. |
| Some modules complete, others inaccessible | Process complete modules; keep missing modules visible. Do not call the whole batch complete. |
| Slides inaccessible behind LMS sign-in | Use supplied exports or visible authorized video frames; ask for slides only if needed. |

A user can narrow the scope to available modules. Record that change rather than silently dropping an inaccessible module.

## Batch manifest

Use JSON, YAML or concise Markdown; choose what fits the authoring workflow. Include these fields without requiring empty placeholders:

- Course, batch/week label, course root, final destination, theme and print defaults.
- Module ID/title/order; verified video URL and title, or local source filename.
- Transcript source: user-pasted, supplied file, human captions, automatic captions, transcription or unavailable. Separately record source extent: full lecture, excerpt, notes or unknown; record language and relevant uncertainty. Clean excerpts/notes under their accurate labels, not as a complete verbatim transcript.
- Supplied question/objective IDs and exact wording; provenance: instructor, user, generated or unknown. Closing retrieval prompts kept separately. Unknown authorship is not a reason to discard a question or interrupt intake.
- Source section IDs, exact headings and timestamps/page locations.
- Selected slide ID, original file/page or video URL/time, image file and actual crop bounds.
- Coverage entries mapping objective/question -> explanatory section -> answer -> evidence -> relevant practice.
- Status: ready, partial or awaiting source; concrete unresolved gaps.

For timestamps store seconds as well as a readable value when useful. Support hours for long lectures. Reordering modules must not redirect citations to a different source. Reference labels may be generated, but source IDs must remain stable during revisions.

## Transcript and summary files

Respect the existing course structure. A new lecture can use:

```text
Lectures/
  Module 05 - Topic.md
  Module 05 - Topic - Transcript.md
Study Guide/
  Course - Week 2 - Study Guide.pdf
```

The summary holds provenance, study questions, concise notes and a transcript link. The transcript holds source metadata, linked section headings and readable source text. Keep important qualifications, examples and uncertainties. Do not silently insert textbook corrections into the instructor's words. Put corrections in study notes with an explicit source clarification and supporting evidence.

Retain dates and course logistics only when relevant; do not manufacture a due-date year or treat LMS point values as study priorities. File naming should handle repeated titles and multi-video modules without collisions.

## Caption and frame acquisition

Use current available capabilities. Do not assume a particular YouTube downloader or API is installed or still working. A failed command is not evidence that no transcript exists. Prefer caption-only retrieval, user-supplied material, or a visible transcript UI over downloading whole recordings. Record which source was actually used.

When capturing slides, verify the displayed video/time and wait until animations reveal the relevant labels. Retain labels, axes, legends, attribution and meaningful annotations. Exclude browser chrome and unrelated personal information. Do not alter scientific figures to make them agree with narration. Prefer rendering original slide pages when supplied. Test actual frame bounds instead of trusting an unverified crop argument.

If automatic speech-to-text is necessary and available, label it as such and review terminology, numbers and negations. Tool access failure does not authorize alternative account access, login bypasses or fabricated transcripts.

## Reference register

Use stable entries such as `M05-S03` for a lecture section and `S1` for a supplementary source. Each records:

- Lecturer/source author, lecture or document title, module and section.
- Exact timestamp range or page/figure/paragraph locator.
- Source link and retained local filename.
- For supplementary material: actual author/editor roles, year, exact title, URL/DOI and claim supported.

Cite cross-module evidence when a claim relies on another lecture. A plausible claim cited to an adjacent but irrelevant section is a citation defect. Relative file links must be URI-encoded and tested from the final PDF's directory. The printed locator must remain useful when the link cannot be opened. No full transcripts embedded by default.
