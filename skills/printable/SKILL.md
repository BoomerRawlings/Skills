---
name: printable
description: Prepare PDF and DOCX documents for duplex printing without changing body content. Use when Codex must create a print-ready PDF with a sparse cover, optional inside-cover metadata, a verified two-level table of contents, preserved or generated page labels, outside-edge page numbers, recto body start, and strict render-and-verify QA. Also use for requests phrased as /printable, print-ready, add a cover and TOC, paginate a document, or prepare a document for binding.
---

# Printable

Create one print-ready PDF. Preserve the source and fail closed when fidelity or pagination cannot be proven.

## Contract

- Accept PDF and DOCX directly. Convert another format only with an installed reliable converter; otherwise pause.
- Never overwrite. Name output `<document-title>-printable.pdf`; add `-2`, `-3`, etc. when occupied.
- Use a sparse, typography-only, mostly monochrome cover. Include only reliable title, subtitle, and author data.
- Put reliable author, edition/version, publication date, publisher, and source URL data on the inside cover. Do not generate claims or summaries.
- Limit the TOC to two meaningful heading levels. Add exactly `Made using /printable skill by Boomer Rawlings.` at the bottom of its final page.
- Leave cover, inside cover, TOC, and inserted blanks unnumbered. Begin the body on a right-hand page.
- Reuse complete, consistent source page labels, including non-1 starts. Otherwise generate labels from 1 unless the user directs another start.
- Place generated labels at the bottom-right of odd physical pages and bottom-left of even physical pages.
- Preserve PDF body pages visually. Never reflow them. If a generated label lacks safe footer space, ask before uniformly scaling body pages within the same paper size.
- For DOCX only, permit widow/orphan control, keep-with-next, keep-together, and paragraph-spacing changes no larger than 2 pt. Never change text, fonts, margins, or line spacing.
- Preserve body page sizes. Match generated front matter to the dominant body size. For materially mixed sizes, ask whether to keep them or scale-to-fit.

## Workflow

1. Preserve the source. Work in a temporary directory.
2. Also load the PDF skill. For DOCX, load the documents skill and use installed Microsoft Word headlessly for conversion and field updates; use LibreOffice only if already available.
3. Run inspection:

   ```powershell
   python scripts/printable.py inspect "input.pdf" --report "inspection.json"
   ```

4. Review the report and every candidate cover, TOC, heading, body boundary, page label, and mixed-size warning. Prefer PDF bookmarks, then DOCX heading styles, then conservative typography inference. Never invent structure.
5. If blocked, state one exact cause and impact, recommend one resolution, and ask one yes/no or agree/disagree question. Apply the accepted resolution and repeat until ready. For image-only PDFs without OCR, ask `Install Tesseract OCR? yes/no` before installing anything.
6. Edit `suggested_spec` from the report into a temporary `spec.json`. Keep only confirmed headings. Set `body_start`, `body_end`, optional `cover_source_page`, optional `toc_source_pages`, numbering policy, and approved scaling policy.
7. Build:

   ```powershell
   python scripts/printable.py build "input.pdf" --spec "spec.json"
   ```

8. Render every output page:

   ```powershell
   python scripts/printable.py render "Document Title-printable.pdf" --output-dir "qa-pages"
   ```

9. Inspect every PNG at 100% zoom. Verify no clipping, overlap, missing glyphs, broken tables, awkward fragments, unsafe footer marks, wrong parity, or blank/duplicated front matter. Check every TOC entry against its printed body label.
10. Rebuild and rerender after any change. Deliver only the final PDF; remove temporary reports, specs, converted files, and QA images.

## Spec

`inspect` emits this structure under `suggested_spec`:

```json
{
  "title": "Document Title",
  "subtitle": "",
  "author": "",
  "inside_metadata": {},
  "body_start": 1,
  "body_end": 20,
  "cover_source_page": null,
  "toc_source_pages": [],
  "headings": [{"title": "Introduction", "level": 1, "source_page": 1}],
  "reuse_existing_numbers": false,
  "mask_existing_numbers": false,
  "number_start": 1,
  "mixed_page_policy": "keep",
  "scale_for_footer": false,
  "attribution": "Made using /printable skill by Boomer Rawlings.",
  "output_suffix": "printable"
}
```

- Page indexes are one-based source-PDF positions.
- Use `cover_source_page` or `toc_source_pages` only after visual verification. Exclude reused front matter from the body range.
- Set `mixed_page_policy` to `scale-to-fit` only after approval.
- Set `scale_for_footer` to `true` only after approval.
- Set `mask_existing_numbers` to `true` only after approval to cover unusable source labels before generating replacements; visually inspect every mask.
- Existing TOC pages are reused only when every entry and printed label verifies; otherwise generate a fresh TOC.
- Leave `attribution` and `output_suffix` unchanged unless another installed skill explicitly extends `/printable`.

## Validation

Run the bundled smoke test after changing the script:

```powershell
python scripts/printable.py self-test
```

Do not deliver when script validation or visual inspection is incomplete.
