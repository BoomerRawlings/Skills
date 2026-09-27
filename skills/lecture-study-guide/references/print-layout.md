# Printable guide design

Carry forward the user's demonstrated layout, while adapting to the course and input shape. This is a design recipe, not a fixed 30-page template.

## Hierarchy and navigation

Use four visibly distinct levels:

1. Navy module/major-section banner with gold module/section label; alternate alignment across facing pages.
2. Large dark page-topic title.
3. Pale-blue topic strip with a blue edge rule and bold subheading.
4. Gold-tinted official-question/pitfall strips; compact marked IDs for practice and answer blocks.

Use size, placement and shape as well as color, so a grayscale print remains navigable. Outside module tabs at distinct vertical positions help flipping through a bound packet. For many modules, group/reuse tab positions rather than pushing tabs beyond the paper. Labels must fit, including multi-digit module numbers and long titles.

Default palette for this user: UCSD navy `#182B49`, blue `#00629B`, gold `#C69214`; pale tints `#EAF1F6` and `#F7F1E2`. Mostly white pages, black body text. Do not add an official university seal or imply university authorship. Use another supplied theme when requested.

## Page system

- Letter portrait by default; honor A4 or other sizes.
- Duplex, long-edge binding. Mirror inner/outer margins, with outside folios on odd-right/even-left pages. Suggested Letter margins: inner 54 pt, outer 42 pt; adapt for binding requirements.
- Keep banners/tabs at least 18 pt from paper edges; use a larger clearance if the printer requires it. Reserve a footer/navigation exclusion zone. Body text, citations and writing rules all obey it.
- Cover, linked contents/bookmarks, module material, reference register, then pitfalls/testing and a separate answer key. Contents may occupy multiple pages. No automatic blank divider pages; an even page count is not required unless requested. Duplex sheet count is `ceil(page_count / 2)`.
- On a teaching page with a useful slide, put the real slide in approximately the upper half and related notes below, usually in two columns. Preserve aspect ratio and readable labels. Text-only pages should use available space instead of leaving an empty image box.
- Repeat a slide on a continuation page when the explanatory content needs it. Prefer an additional readable page over tiny text. A complex figure may need a full-width or larger image.
- Start around 10.5-11 pt body text with 12.5-14 pt leading; small references around 8.5-9 pt, subscript citation labels around 7-8 pt. These are starting points, not a reason to shrink an overfull page indefinitely.
- Keep related headings, paragraphs and answer blocks together. If a block cannot fit, split at a conceptual boundary and provide an explicit continuation title. Plan columns by measured height rather than merely counting paragraphs.
- Use spare review space for limited ruled retrieval notes. Writing space is useful; gratuitous blank pages are not.

## Digital and printed traceability

Link contents and bookmarks to actual destinations. Give questions and answer-key entries reciprocal links. Provide compact footer links to contents and sources. Print source-register titles, timestamps/page references and exact companion filenames. Do not rely on clickable labels alone for paper usability.

Keep a whole citation cluster on one line where possible; wrap only deliberately at a sensible boundary for unusually long clusters. In ReportLab, `<nobr>` alone may not prevent wrapping across separate hyperlink fragments. Use nonbreaking spaces inside the cluster, e.g. `[1.01,\u00a01.02]`, and inside labels such as `Notes\u00a0p.\u00a015`. Inspect the actual rendered result and ensure each reference remains clickable.

Treat page numbers, source labels, contents and answer links as derived data. Do not keep a fixed page-count assertion from the example packet. Verify all destination pages and locations after re-pagination.

## Implementation choices

Use the available PDF skill and bundled runtime when present. ReportLab is suitable for measured layouts; another reliable local renderer is acceptable. Discover fonts instead of assuming Windows Calibri. Embed available readable fonts and confirm superscripts, subscripts, arrows and scientific symbols render correctly. Check actual Unicode before attributing a shell display-decoding problem to the PDF.

The prior course-specific builder may serve as a local reference if available. It is not a dependency of this skill. Never copy its absolute paths, four-module indexing, fixed question ranges, fixed source splits, specific video IDs or 30-page assertions into a new batch.

Measure text, images, bars and writing rules against page bounds. Explicit overflow errors are preferable to invisible clipping. Set print preferences to no scaling and long-edge duplex where supported, while still giving the user actual print instructions. Preserve the previous final PDF until a replacement builds successfully.
