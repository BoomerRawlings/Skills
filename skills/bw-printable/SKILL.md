---
name: bw-printable
description: Make PDF, DOCX, PNG, and JPG content understandable when printed in grayscale while retaining useful color. Use for /bw-printable, black-and-white printing, grayscale-safe documents, color-dependent charts or maps, indistinguishable series or regions, low-contrast graphics, or requests to add print-visible image descriptions. Audits meaningful visual distinctions, applies reviewed patterns, outlines, markers, labels, filters, or luminance changes, keeps factual captions immediately below images on the same page, then runs the full /printable workflow.
---

# BW Printable

Produce a color-retaining PDF whose meaning survives ordinary grayscale printing. Never infer visual semantics silently.

## Contract

- Accept PDF, DOCX, PNG, and JPG. Always deliver `<document-title>-bw-printable.pdf` without overwriting.
- Preserve color where possible. Use grayscale only as a simulation and verification view.
- Require meaningful graphical boundaries to reach 3:1 contrast or gain a redundant pattern, border, marker, line style, or direct label.
- Require normal text to reach 4.5:1 and large text to reach 3:1.
- Apply the smallest sufficient change: direct labels; borders/markers/line styles; patterns; then luminance/recoloring.
- Preserve photographs as photographs. Apply restrained grayscale-safe filters; add a caption only when color carries meaning.
- Convert decorative visuals cleanly but do not label, pattern, or caption them.
- Add a visible 1-3 sentence description only when visual edits alone do not preserve meaning. State what the image shows, key relationships, and color-dependent meaning. Never speculate.
- Put every added caption immediately below its image and on the same page. For DOCX, bind the image paragraph to the caption. For PDF, use verified empty space or shrink the visual inside its existing box.
- Rasterize a selected PDF visual region when necessary. Ask before rasterizing or recomposing a whole page.
- Preserve source files and surrounding content. Fail closed on unclear meaning, insufficient caption space, or unverified output.

These thresholds follow W3C guidance for [use of color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html), [non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html), and [text contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).

## Workflow

1. Preserve the source. Work in a temporary directory. Load the PDF skill; load the documents skill for DOCX.
2. Audit:

   ```powershell
   python scripts/bw_visuals.py audit "input.pdf" --work-dir "bw-audit" --report "bw-audit.json"
   ```

3. Inspect every color preview, grayscale preview, and laser simulation. Treat automatic conflict pairs as candidates, not semantic truth.
4. Classify each visual as informational, photographic, or decorative. Confirm legends, labels, series, regions, and color-dependent meaning from visible source evidence.
5. Create `edits.json` from the reviewed findings. Use source colors and explicit regions. Add captions only when needed.
6. Apply:

   ```powershell
   python scripts/bw_visuals.py apply "input.pdf" --spec "edits.json" --output "intermediate.pdf"
   ```

7. Re-audit and inspect the modified visuals in color, grayscale, and laser simulation. Verify patterns and labels remain clear at print scale.
8. Run `/printable` on the intermediate file. In its spec set:

   ```json
   {
     "attribution": "Made using /bw-printable skill by Boomer Rawlings.",
     "output_suffix": "bw-printable"
   }
   ```

9. Render every final PDF page and inspect at 100% zoom. Verify the `/printable` cover, TOC, parity, and outside-edge numbering plus every modified visual and caption.
10. Deliver only the final PDF. Remove audit previews, reports, edit specs, and intermediates.

## Failure Loop

When blocked, present one issue at a time: exact cause, effect on grayscale understanding, recommended fix, then one yes/no or agree/disagree prompt. Apply the accepted fix and repeat until ready.

Examples:

- `Series A and Series B become 1.18:1 in grayscale. Add circle markers to A and square markers to B? yes/no`
- `Caption space contains source text. Shrink the image within its current box? yes/no`
- `The red region's meaning is unclear from the legend. Confirm it means "Delayed"? yes/no`
- `This edit requires whole-page rasterization. Approve rasterizing this page? yes/no`

## Edit Spec

Use normalized image coordinates (`0` to `1`) for labels and markers. Their sizes are nominal pixels at a 1000-pixel visual width and scale with the visual. PDF bounding boxes use one-based pages and points: `[x0, y0, x1, y1]` from the top-left.

```json
{
  "edits": [
    {
      "target": {"page": 2, "bbox": [72, 120, 540, 410]},
      "filters": {"autocontrast": false, "contrast": 1.05, "sharpness": 1.0},
      "recolors": [{"from": "#D62728", "to": "#8B0000", "tolerance": 24}],
      "patterns": [{"color": "#2CA02C", "tolerance": 24, "style": "diagonal", "spacing": 10}],
      "outlines": [{"color": "#D62728", "tolerance": 24, "width": 3}],
      "markers": [{"x": 0.5, "y": 0.4, "shape": "square", "size": 12}],
      "labels": [{"x": 0.6, "y": 0.3, "text": "Series B", "size": 13}],
      "caption": "The chart compares Series A and Series B. Series B uses diagonal hatching so the series remains identifiable in grayscale.",
      "shrink_inside": true,
      "caption_height": 42
    }
  ]
}
```

- For PDF empty-space captions, replace `shrink_inside` with `caption_bbox` immediately below the visual.
- For DOCX, target `{"media": "word/media/image1.png", "paragraph": 12}`. The paragraph is one-based.
- For standalone images, target `{"whole_image": true}`; output the intermediate as PDF.
- Supported patterns: `diagonal`, `backward-diagonal`, `crosshatch`, `dots`.
- Supported markers: `circle`, `square`, `triangle`, `diamond`.
- Do not use AI image generation to redraw charts, maps, labels, values, or legends. Apply deterministic edits to source pixels.

## Validation

```powershell
python scripts/bw_visuals.py self-test
```

Do not deliver without script validation and every-page visual inspection.
