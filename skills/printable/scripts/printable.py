#!/usr/bin/env python3
"""Inspect, assemble, and render conservative print-ready PDFs."""

from __future__ import annotations

import argparse
import base64
import copy
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

try:
    import fitz
    from docx import Document
    from pypdf import PageObject, PdfReader, PdfWriter, Transformation
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
except ImportError as exc:
    raise SystemExit(f"Missing required runtime dependency: {exc.name}") from exc


ATTRIBUTION = "Made using /printable skill by Boomer Rawlings."
FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


class PrintableError(RuntimeError):
    def __init__(self, reason: str, resolution: str, prompt: str):
        super().__init__(reason)
        self.reason = reason
        self.resolution = resolution
        self.prompt = prompt


def blocked(reason: str, resolution: str, prompt: str) -> None:
    raise PrintableError(reason, resolution, prompt)


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", norm(value).lower())


def safe_name(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', " ", norm(value))
    value = re.sub(r"\s+", " ", value).rstrip(" .")
    return value[:120] or "document"


def unique_output(source: Path, title: str, suffix: str = "printable") -> Path:
    base = source.parent / f"{safe_name(title)}-{suffix}.pdf"
    if not base.exists():
        return base
    index = 2
    while True:
        candidate = source.parent / f"{safe_name(title)}-{suffix}-{index}.pdf"
        if not candidate.exists():
            return candidate
        index += 1


def register_font() -> None:
    global FONT, FONT_BOLD
    choices = [
        (Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/arialbd.ttf")),
        (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
    ]
    for regular, bold_font in choices:
        if regular.exists() and bold_font.exists():
            pdfmetrics.registerFont(TTFont("PrintableSans", str(regular)))
            pdfmetrics.registerFont(TTFont("PrintableSansBold", str(bold_font)))
            FONT, FONT_BOLD = "PrintableSans", "PrintableSansBold"
            return


def wrap_text(text: str, font: str, size: float, width: float) -> list[str]:
    words = norm(text).split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if pdfmetrics.stringWidth(trial, font, size) <= width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def dominant_size(doc: fitz.Document, start: int = 0, end: int | None = None) -> tuple[tuple[float, float], list[tuple[float, float]]]:
    end = len(doc) if end is None else end
    sizes = [(round(doc[i].rect.width, 1), round(doc[i].rect.height, 1)) for i in range(start, end)]
    if not sizes:
        blocked("No body pages remain after applying the selected range.", "Choose a valid body range.", "Change the body range? yes/no")
    return Counter(sizes).most_common(1)[0][0], sorted(set(sizes))


def page_lines(page: fitz.Page) -> list[dict]:
    result: list[dict] = []
    data = page.get_text("dict")
    for block in data.get("blocks", []):
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = norm("".join(span.get("text", "") for span in spans))
            if not text:
                continue
            result.append({
                "text": text,
                "size": max((float(span.get("size", 0)) for span in spans), default=0),
                "bold": any("bold" in span.get("font", "").lower() for span in spans),
                "bbox": list(line.get("bbox", (0, 0, 0, 0))),
            })
    return result


def outline_entries(reader: PdfReader) -> list[dict]:
    entries: list[dict] = []

    def walk(items, level: int = 1) -> None:
        for item in items:
            if isinstance(item, list):
                walk(item, level + 1)
                continue
            try:
                page = reader.get_destination_page_number(item) + 1
                title = norm(getattr(item, "title", str(item)))
            except Exception:
                continue
            if title:
                entries.append({"title": title, "level": min(level, 2), "source_page": page})

    try:
        walk(reader.outline)
    except Exception:
        pass
    return entries


def inferred_headings(doc: fitz.Document) -> list[dict]:
    all_lines = [line for page in doc for line in page_lines(page)]
    weighted = [line["size"] for line in all_lines for _ in range(max(1, len(line["text"]) // 12)) if line["size"]]
    if not weighted:
        return []
    body_size = sorted(weighted)[len(weighted) // 2]
    candidates: list[tuple[float, int, str]] = []
    for page_index, page in enumerate(doc):
        for line in page_lines(page):
            text = line["text"]
            y0 = line["bbox"][1]
            if y0 < 24 or y0 > page.rect.height * 0.86 or len(text) > 110:
                continue
            score = line["size"] / max(body_size, 1)
            if score >= 1.22 or (line["bold"] and score >= 1.08):
                if not re.fullmatch(r"(?:page\s+)?\d+(?:\s+of\s+\d+)?", text, re.I):
                    candidates.append((line["size"], page_index + 1, text))
    sizes = sorted({round(size, 1) for size, _, _ in candidates}, reverse=True)[:2]
    return [
        {"title": text, "level": 1 if round(size, 1) == sizes[0] else 2, "source_page": page}
        for size, page, text in candidates
        if round(size, 1) in sizes
    ]


NUMBER_RE = re.compile(r"^\s*(?:page\s+)?([ivxlcdm]+|\d+)(?:\s+of\s+\d+)?\s*$", re.I)


def roman_value(value: str) -> int | None:
    if not re.fullmatch(r"[ivxlcdm]+", value, re.I):
        return None
    values = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
    total, previous = 0, 0
    for char in reversed(value.lower()):
        current = values[char]
        total += -current if current < previous else current
        previous = max(previous, current)
    return total


def number_candidates(page: fitz.Page) -> list[dict]:
    found: list[dict] = []
    for line in page_lines(page):
        if line["bbox"][1] < page.rect.height * 0.82:
            continue
        match = NUMBER_RE.fullmatch(line["text"])
        if match:
            found.append({"label": match.group(1), "bbox": line["bbox"]})
    return found


def existing_labels(doc: fitz.Document, start: int, end: int) -> dict[int, str]:
    labels: dict[int, str] = {}
    numeric: list[int] = []
    for index in range(start, end):
        candidates = number_candidates(doc[index])
        if len(candidates) != 1:
            blocked(
                f"Source page {index + 1} has {len(candidates)} usable footer page labels; exactly one is required.",
                "Generate fresh body numbering or correct the selected body range.",
                "Generate fresh numbering? yes/no",
            )
        label = candidates[0]["label"]
        labels[index + 1] = label
        numeric.append(int(label) if label.isdigit() else (roman_value(label) or -10_000))
    if any(value < 0 for value in numeric) or any(b != a + 1 for a, b in zip(numeric, numeric[1:])):
        blocked("Existing body page labels are not a complete increasing sequence.", "Generate fresh body numbering.", "Generate fresh numbering? yes/no")
    return labels


def ocr_preview(doc: fitz.Document, pages: list[int]) -> dict[str, str]:
    binary = shutil.which("tesseract")
    if not binary:
        return {}
    previews: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="printable-ocr-") as temp:
        for page_number in pages:
            image = Path(temp) / f"page-{page_number}.png"
            pix = doc[page_number - 1].get_pixmap(matrix=fitz.Matrix(2.5, 2.5), alpha=False)
            pix.save(image)
            run = subprocess.run([binary, str(image), "stdout", "--psm", "6"], capture_output=True, text=True, encoding="utf-8", errors="replace")
            if run.returncode == 0:
                previews[str(page_number)] = norm(run.stdout)[:1000]
    return previews


def prepare_docx(source: Path, destination: Path) -> list[dict]:
    document = Document(source)
    headings: list[dict] = []
    for paragraph in document.paragraphs:
        style = norm(paragraph.style.name if paragraph.style else "")
        paragraph.paragraph_format.widow_control = True
        match = re.fullmatch(r"Heading\s+([12])", style, re.I)
        if match and norm(paragraph.text):
            paragraph.paragraph_format.keep_with_next = True
            headings.append({"title": norm(paragraph.text), "level": int(match.group(1)), "source_page": None})
        elif style.lower().startswith("caption"):
            paragraph.paragraph_format.keep_with_next = True
    document.save(destination)
    return headings


def word_to_pdf(source: Path, destination: Path) -> None:
    src = str(source.resolve()).replace("'", "''")
    dst = str(destination.resolve()).replace("'", "''")
    script = f"""
$ErrorActionPreference = 'Stop'
$word = $null
$doc = $null
try {{
  $word = New-Object -ComObject Word.Application
  $word.Visible = $false
  $word.DisplayAlerts = 0
  $doc = $word.Documents.Open('{src}', $false, $true)
  foreach ($field in $doc.Fields) {{ [void]$field.Update() }}
  $doc.ExportAsFixedFormat('{dst}', 17)
}} finally {{
  if ($doc -ne $null) {{ $doc.Close(0) }}
  if ($word -ne $null) {{ $word.Quit() }}
}}
"""
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    run = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded], capture_output=True, text=True, timeout=180)
    if run.returncode or not destination.exists():
        blocked("Microsoft Word could not convert the DOCX reliably.", "Repair Word automation or install LibreOffice.", "Retry after repairing the converter? yes/no")


def map_heading_pages(doc: fitz.Document, headings: list[dict], start: int, end: int) -> list[dict]:
    page_compact = [compact(doc[index].get_text()) for index in range(start, end)]
    mapped: list[dict] = []
    for heading in headings:
        title = norm(str(heading.get("title", "")))
        level = int(heading.get("level", 1))
        if not title or level not in (1, 2):
            blocked("Each TOC heading needs non-empty text and level 1 or 2.", "Correct the heading list.", "Correct the headings? yes/no")
        requested = heading.get("source_page")
        if requested is not None:
            page_number = int(requested)
            if not start + 1 <= page_number <= end:
                blocked(f"Heading '{title}' points outside the body range.", "Correct its source_page.", "Correct the heading page? yes/no")
            page_text = page_compact[page_number - start - 1]
            if page_text and compact(title) not in page_text:
                blocked(f"Heading '{title}' was not found on source page {page_number}.", "Correct or remove that TOC entry.", "Correct the TOC entry? yes/no")
        else:
            matches = [start + offset + 1 for offset, text in enumerate(page_compact) if compact(title) and compact(title) in text]
            if len(matches) != 1:
                blocked(f"Heading '{title}' maps to {len(matches)} body pages; one is required.", "Specify its exact one-based source_page.", "Specify the heading page? yes/no")
            page_number = matches[0]
        mapped.append({"title": title, "level": level, "source_page": page_number})
    mapped.sort(key=lambda item: item["source_page"])
    if not mapped:
        blocked("No verified headings remain for the TOC.", "Confirm at least one meaningful heading.", "Add a verified heading? yes/no")
    return mapped


def inspect_pdf(path: Path, docx_headings: list[dict] | None = None) -> dict:
    doc = fitz.open(path)
    reader = PdfReader(str(path))
    metadata = reader.metadata or {}
    first_lines = page_lines(doc[0]) if len(doc) else []
    ranked = sorted(first_lines, key=lambda line: (line["size"], -line["bbox"][1]), reverse=True)
    title = norm(str(metadata.get("/Title", ""))) or (ranked[0]["text"] if ranked else path.stem)
    author = norm(str(metadata.get("/Author", "")))
    outline = outline_entries(reader)
    heading_source = "docx-styles" if docx_headings is not None else ("pdf-bookmarks" if outline else "typography-inference")
    headings = docx_headings if docx_headings is not None else (outline or inferred_headings(doc))
    if docx_headings is not None:
        headings = map_heading_pages(doc, headings, 0, len(doc))
    size, sizes = dominant_size(doc)
    image_only = [index + 1 for index, page in enumerate(doc) if len(norm(page.get_text())) < 12]
    likely_scanned = bool(doc) and len(image_only) * 5 >= len(doc) * 4
    toc_pages = [index + 1 for index, page in enumerate(doc[: min(8, len(doc))]) if re.search(r"\b(?:table of )?contents\b", page.get_text(), re.I)]
    report = {
        "input": str(path.resolve()),
        "page_count": len(doc),
        "title_candidate": title,
        "author_candidate": author,
        "dominant_page_size_points": list(size),
        "page_sizes_points": [list(item) for item in sizes],
        "mixed_page_sizes": len(sizes) > 1,
        "heading_source": heading_source,
        "headings_require_confirmation": heading_source == "typography-inference",
        "heading_candidates": headings,
        "toc_page_candidates": toc_pages,
        "page_number_candidates": {str(i + 1): number_candidates(page) for i, page in enumerate(doc)},
        "image_only_pages": image_only,
        "likely_scanned_document": likely_scanned,
        "ocr_available": bool(shutil.which("tesseract")),
        "ocr_preview": ocr_preview(doc, image_only),
        "blockers": [],
    }
    if not headings:
        report["blockers"].append("No reliable TOC headings were found.")
    if likely_scanned and not shutil.which("tesseract"):
        report["blockers"].append("Image-only pages detected and Tesseract OCR is unavailable.")
    report["suggested_spec"] = {
        "title": title,
        "subtitle": "",
        "author": author,
        "inside_metadata": {"Author": author} if author else {},
        "body_start": 1,
        "body_end": len(doc),
        "cover_source_page": None,
        "toc_source_pages": [],
        "headings": headings,
        "reuse_existing_numbers": False,
        "mask_existing_numbers": False,
        "number_start": 1,
        "mixed_page_policy": None if len(sizes) > 1 else "keep",
        "scale_for_footer": False,
        "attribution": ATTRIBUTION,
        "output_suffix": "printable",
    }
    doc.close()
    return report


def inspect_source(source: Path) -> dict:
    suffix = source.suffix.lower()
    if suffix == ".pdf":
        return inspect_pdf(source)
    if suffix == ".docx":
        with tempfile.TemporaryDirectory(prefix="printable-docx-") as temp:
            prepared = Path(temp) / "prepared.docx"
            converted = Path(temp) / "converted.pdf"
            headings = prepare_docx(source, prepared)
            word_to_pdf(prepared, converted)
            report = inspect_pdf(converted, headings)
            report["input"] = str(source.resolve())
            report["converted_with"] = "Microsoft Word"
            return report
    blocked(f"Unsupported input format: {suffix or 'none'}.", "Convert it to PDF with an installed reliable converter.", "Convert the source to PDF? yes/no")


def make_cover(title: str, subtitle: str, author: str, size: tuple[float, float]) -> bytes:
    stream = io.BytesIO()
    c = canvas.Canvas(stream, pagesize=size)
    width, height = size
    y = height * 0.62
    lines = wrap_text(title, FONT_BOLD, 27, width - 108)
    c.setFillGray(0.10)
    c.setFont(FONT_BOLD, 27)
    for line in lines[:4]:
        c.drawCentredString(width / 2, y, line)
        y -= 34
    if subtitle:
        y -= 8
        c.setFillGray(0.30)
        c.setFont(FONT, 13)
        for line in wrap_text(subtitle, FONT, 13, width - 130)[:3]:
            c.drawCentredString(width / 2, y, line)
            y -= 18
    if author:
        c.setFillGray(0.25)
        c.setFont(FONT, 10)
        c.drawCentredString(width / 2, height * 0.18, author)
    c.showPage()
    c.save()
    return stream.getvalue()


def make_inside(metadata: dict, size: tuple[float, float]) -> bytes:
    stream = io.BytesIO()
    c = canvas.Canvas(stream, pagesize=size)
    width, height = size
    items = [(norm(str(key)), norm(str(value))) for key, value in metadata.items() if norm(str(value))]
    if items:
        c.setFillGray(0.25)
        c.setFont(FONT_BOLD, 10)
        c.drawString(54, height - 72, "Document information")
        y = height - 98
        for label, value in items:
            c.setFont(FONT_BOLD, 8.5)
            c.drawString(54, y, label)
            c.setFont(FONT, 8.5)
            for line in wrap_text(value, FONT, 8.5, width - 170):
                c.drawString(140, y, line)
                y -= 11
            y -= 5
    c.showPage()
    c.save()
    return stream.getvalue()


def toc_chunks(headings: list[dict], width: float, height: float) -> list[list[tuple[dict, list[str]]]]:
    chunks: list[list[tuple[dict, list[str]]]] = [[]]
    y = height - 105
    for heading in headings:
        font = FONT_BOLD if heading["level"] == 1 else FONT
        font_size = 10 if heading["level"] == 1 else 9
        indent = 0 if heading["level"] == 1 else 18
        lines = wrap_text(heading["title"], font, font_size, width - 108 - indent)
        needed = len(lines) * 12 + 5
        if y - needed < 58 and chunks[-1]:
            chunks.append([])
            y = height - 105
        chunks[-1].append((heading, lines))
        y -= needed
    return chunks


def make_toc(headings: list[dict], labels: dict[int, str], size: tuple[float, float], attribution: str = ATTRIBUTION) -> bytes:
    width, height = size
    chunks = toc_chunks(headings, width, height)
    stream = io.BytesIO()
    c = canvas.Canvas(stream, pagesize=size)
    for chunk_index, chunk in enumerate(chunks):
        c.setFillGray(0.10)
        c.setFont(FONT_BOLD, 20)
        c.drawString(54, height - 68, "Contents" if chunk_index == 0 else "Contents (continued)")
        y = height - 105
        for heading, lines in chunk:
            font = FONT_BOLD if heading["level"] == 1 else FONT
            font_size = 10 if heading["level"] == 1 else 9
            indent = 0 if heading["level"] == 1 else 18
            c.setFont(font, font_size)
            for line_index, line in enumerate(lines):
                c.drawString(54 + indent, y, line)
                if line_index == len(lines) - 1:
                    c.drawRightString(width - 54, y, labels[heading["source_page"]])
                y -= 12
            y -= 5
        if chunk_index == len(chunks) - 1:
            c.setFillGray(0.45)
            c.setFont(FONT, 6.5)
            c.drawCentredString(width / 2, 28, attribution)
        c.showPage()
    c.save()
    return stream.getvalue()


def overlay_text(text: str, size: tuple[float, float], side: str, attribution: bool = False) -> PageObject:
    width, _ = size
    stream = io.BytesIO()
    c = canvas.Canvas(stream, pagesize=size)
    c.setFillGray(0.25 if not attribution else 0.45)
    c.setFont(FONT, 8 if not attribution else 6.5)
    if attribution:
        c.drawCentredString(width / 2, 28, text)
    elif side == "right":
        c.drawRightString(width - 28, 22, text)
    else:
        c.drawString(28, 22, text)
    c.showPage()
    c.save()
    return PdfReader(io.BytesIO(stream.getvalue())).pages[0]


def mask_overlay(boxes: list[list[float]], size: tuple[float, float]) -> PageObject:
    width, height = size
    stream = io.BytesIO()
    c = canvas.Canvas(stream, pagesize=size)
    c.setFillColorRGB(1, 1, 1)
    for x0, y0, x1, y1 in boxes:
        c.rect(max(0, x0 - 3), max(0, height - y1 - 2), min(width - x0 + 3, x1 - x0 + 6), y1 - y0 + 4, fill=1, stroke=0)
    c.showPage()
    c.save()
    return PdfReader(io.BytesIO(stream.getvalue())).pages[0]


def footer_safe(page: fitz.Page, side: str) -> bool:
    width, height = page.rect.width, page.rect.height
    if side == "center":
        clip = fitz.Rect(width / 2 - 150, height - 44, width / 2 + 150, height)
    else:
        clip = fitz.Rect(width - 78 if side == "right" else 0, height - 44, width if side == "right" else 78, height)
    pix = page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2), colorspace=fitz.csGRAY, alpha=False, clip=clip)
    samples = pix.samples
    return not samples or sum(value < 225 for value in samples) / len(samples) < 0.006


def fitted_page(page: PageObject, target: tuple[float, float], bottom_margin: float) -> PageObject:
    if page.rotation:
        page.transfer_rotation_to_content()
    source_w, source_h = float(page.mediabox.width), float(page.mediabox.height)
    target_w, target_h = target
    usable_w, usable_h = target_w - 36, target_h - bottom_margin - 18
    scale = min(usable_w / source_w, usable_h / source_h)
    tx = (target_w - source_w * scale) / 2
    ty = bottom_margin + (usable_h - source_h * scale) / 2
    result = PageObject.create_blank_page(width=target_w, height=target_h)
    result.merge_transformed_page(page, Transformation().scale(scale).translate(tx, ty))
    return result


def output_page(page: PageObject, target: tuple[float, float], scale: bool, bottom_margin: float = 0) -> PageObject:
    page = copy.deepcopy(page)
    return fitted_page(page, target, bottom_margin) if scale else page


def add_reader_pages(writer: PdfWriter, data: bytes) -> int:
    reader = PdfReader(io.BytesIO(data))
    for page in reader.pages:
        writer.add_page(page)
    return len(reader.pages)


def source_as_pdf(source: Path, temp: Path) -> Path:
    if source.suffix.lower() == ".pdf":
        return source
    if source.suffix.lower() == ".docx":
        prepared = temp / "prepared.docx"
        converted = temp / "converted.pdf"
        prepare_docx(source, prepared)
        word_to_pdf(prepared, converted)
        return converted
    blocked(f"Unsupported input format: {source.suffix or 'none'}.", "Convert it to PDF first.", "Convert the source to PDF? yes/no")


def verify_output(source_pdf: Path, output: Path, headings: list[dict], labels: dict[int, str], body_start: int, body_end: int, output_body_start: int, toc_output_pages: list[int], generated_numbers: bool) -> None:
    source_doc = fitz.open(source_pdf)
    output_doc = fitz.open(output)
    expected_body_count = body_end - body_start + 1
    if len(output_doc) - output_body_start != expected_body_count:
        blocked("Output body page count differs from the selected source body.", "Rebuild after correcting assembly.", "Rebuild the PDF? yes/no")
    toc_text = compact(" ".join(output_doc[index - 1].get_text() for index in toc_output_pages))
    for heading in headings:
        if compact(heading["title"]) not in toc_text or compact(labels[heading["source_page"]]) not in toc_text:
            blocked(f"TOC verification failed for '{heading['title']}'.", "Regenerate the TOC from the confirmed heading map.", "Regenerate the TOC? yes/no")
    for offset, source_index in enumerate(range(body_start - 1, body_end)):
        src_text = compact(source_doc[source_index].get_text())
        out_page = output_doc[output_body_start + offset]
        out_text = compact(out_page.get_text())
        if src_text and src_text not in out_text:
            blocked(f"Body text verification failed on source page {source_index + 1}.", "Stop and inspect the conversion or scaling result.", "Inspect and retry? yes/no")
        if generated_numbers:
            label = labels[source_index + 1]
            hits = [rect for rect in out_page.search_for(label) if rect.y0 > out_page.rect.height * 0.82]
            if not hits:
                blocked(f"Generated page label {label} was not found in the output footer.", "Rebuild page-number overlays.", "Rebuild numbering? yes/no")
    source_doc.close()
    output_doc.close()


def build(source: Path, spec: dict, requested_output: Path | None) -> Path:
    title = norm(str(spec.get("title", "")))
    if not title:
        blocked("The cover title is empty or unreliable.", "Confirm the document title.", "Use a confirmed title? yes/no")
    suffix = re.sub(r"[^a-z0-9-]+", "-", norm(str(spec.get("output_suffix", "printable"))).lower()).strip("-") or "printable"
    attribution = norm(str(spec.get("attribution", ATTRIBUTION))) or ATTRIBUTION
    output = requested_output or unique_output(source, title, suffix)
    if output.exists():
        blocked(f"Output already exists: {output}", "Choose the next available filename.", "Use a new filename? yes/no")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="printable-build-") as temp_dir:
        source_pdf = source_as_pdf(source, Path(temp_dir))
        fitz_doc = fitz.open(source_pdf)
        reader = PdfReader(str(source_pdf))
        body_start = int(spec.get("body_start", 1))
        body_end = int(spec.get("body_end", len(reader.pages)))
        if body_start < 1 or body_end > len(reader.pages) or body_start > body_end:
            blocked("The selected body range is invalid.", "Choose a body range within the converted PDF.", "Correct the body range? yes/no")
        headings = map_heading_pages(fitz_doc, list(spec.get("headings", [])), body_start - 1, body_end)
        dominant, sizes = dominant_size(fitz_doc, body_start - 1, body_end)
        policy = spec.get("mixed_page_policy", "keep")
        if len(sizes) > 1 and policy not in ("keep", "scale-to-fit"):
            blocked("Body pages use materially mixed sizes and no policy was confirmed.", "Choose keep or scale-to-fit.", "Keep mixed page sizes? yes/no")
        reuse_numbers = bool(spec.get("reuse_existing_numbers", False))
        mask_numbers = bool(spec.get("mask_existing_numbers", False))
        if reuse_numbers and mask_numbers:
            blocked("Existing numbering cannot be reused and masked simultaneously.", "Choose reuse or mask-and-replace.", "Reuse existing numbering? yes/no")
        detected_numbers = {page: number_candidates(fitz_doc[page - 1]) for page in range(body_start, body_end + 1)}
        if not reuse_numbers and any(detected_numbers.values()) and not mask_numbers:
            pages = [page for page, candidates in detected_numbers.items() if candidates]
            blocked(f"Existing footer page labels were detected on source page(s): {pages[:8]}.", "Reuse them if consistent, or approve mask-and-replace.", "Mask and replace existing numbering? yes/no")
        if reuse_numbers:
            labels = existing_labels(fitz_doc, body_start - 1, body_end)
        else:
            number_start = int(spec.get("number_start", 1))
            labels = {page: str(number_start + page - body_start) for page in range(body_start, body_end + 1)}
        toc_source_pages = [int(page) for page in spec.get("toc_source_pages", [])]
        cover_source_page = spec.get("cover_source_page")
        excluded = set(toc_source_pages)
        if cover_source_page is not None:
            excluded.add(int(cover_source_page))
        if any(body_start <= page <= body_end for page in excluded):
            blocked("Reused front matter overlaps the selected body range.", "Move body_start past reused front matter.", "Correct the body boundary? yes/no")
        writer = PdfWriter()
        if cover_source_page is None:
            add_reader_pages(writer, make_cover(title, norm(str(spec.get("subtitle", ""))), norm(str(spec.get("author", ""))), dominant))
        else:
            page_number = int(cover_source_page)
            if not 1 <= page_number <= len(reader.pages):
                blocked("The reused cover page is outside the source.", "Correct cover_source_page.", "Correct the cover page? yes/no")
            writer.add_page(reader.pages[page_number - 1])
        add_reader_pages(writer, make_inside(dict(spec.get("inside_metadata", {})), dominant))
        toc_output_pages: list[int] = []
        if toc_source_pages:
            for page_number in toc_source_pages:
                if not 1 <= page_number <= len(reader.pages):
                    blocked("A reused TOC page is outside the source.", "Correct toc_source_pages.", "Correct the TOC pages? yes/no")
                page = copy.deepcopy(reader.pages[page_number - 1])
                if page_number == toc_source_pages[-1]:
                    fitz_page = fitz_doc[page_number - 1]
                    if not footer_safe(fitz_page, "center"):
                        blocked("The reused TOC has no safe attribution footer space.", "Generate a fresh TOC.", "Generate a fresh TOC? yes/no")
                    if page.rotation:
                        page.transfer_rotation_to_content()
                    size = (float(page.mediabox.width), float(page.mediabox.height))
                    page.merge_page(overlay_text(attribution, size, "right", attribution=True))
                writer.add_page(page)
                toc_output_pages.append(len(writer.pages))
        else:
            toc_data = make_toc(headings, labels, dominant, attribution)
            toc_count = add_reader_pages(writer, toc_data)
            toc_output_pages = list(range(len(writer.pages) - toc_count + 1, len(writer.pages) + 1))
        if len(toc_output_pages) % 2 == 1:
            writer.add_blank_page(width=dominant[0], height=dominant[1])
        output_body_start = len(writer.pages)
        if (output_body_start + 1) % 2 == 0:
            blocked("Internal parity error: body would begin on a left-hand page.", "Rebuild front matter parity.", "Rebuild parity? yes/no")
        scale_for_footer = bool(spec.get("scale_for_footer", False))
        unsafe_pages: list[int] = []
        if not reuse_numbers:
            for offset, page_number in enumerate(range(body_start, body_end + 1)):
                physical = output_body_start + offset + 1
                side = "right" if physical % 2 else "left"
                if not footer_safe(fitz_doc[page_number - 1], side) and not (mask_numbers and detected_numbers[page_number]):
                    unsafe_pages.append(page_number)
            if unsafe_pages and not scale_for_footer:
                blocked(f"Generated numbering overlaps or risks clipping on source page(s): {unsafe_pages[:8]}.", "Uniformly scale body pages within the same paper size.", "Scale body pages slightly? yes/no")
        normalize_sizes = policy == "scale-to-fit"
        for offset, page_number in enumerate(range(body_start, body_end + 1)):
            physical = output_body_start + offset + 1
            side = "right" if physical % 2 else "left"
            source_page = copy.deepcopy(reader.pages[page_number - 1])
            if mask_numbers and detected_numbers[page_number]:
                if source_page.rotation:
                    source_page.transfer_rotation_to_content()
                source_size = (float(source_page.mediabox.width), float(source_page.mediabox.height))
                boxes = [candidate["bbox"] for candidate in detected_numbers[page_number]]
                source_page.merge_page(mask_overlay(boxes, source_size))
            page = output_page(source_page, dominant, normalize_sizes or scale_for_footer, 44 if scale_for_footer else 0)
            if not reuse_numbers:
                if page.rotation:
                    page.transfer_rotation_to_content()
                page_size = (float(page.mediabox.width), float(page.mediabox.height))
                page.merge_page(overlay_text(labels[page_number], page_size, side))
            writer.add_page(page)
        writer.add_metadata({"/Title": title, "/Author": norm(str(spec.get("author", ""))), "/Producer": f"/{suffix} skill"})
        with output.open("wb") as handle:
            writer.write(handle)
        verify_output(source_pdf, output, headings, labels, body_start, body_end, output_body_start, toc_output_pages, not reuse_numbers)
        fitz_doc.close()
    return output


def render_pdf(source: Path, output_dir: Path, dpi: int) -> int:
    if output_dir.exists() and any(output_dir.iterdir()):
        blocked(f"QA directory is not empty: {output_dir}", "Choose an empty QA directory.", "Use a new QA directory? yes/no")
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(source)
    matrix = fitz.Matrix(dpi / 72, dpi / 72)
    for index, page in enumerate(doc):
        page.get_pixmap(matrix=matrix, alpha=False).save(output_dir / f"page-{index + 1:04d}.png")
    count = len(doc)
    doc.close()
    return count


def self_test() -> None:
    register_font()
    with tempfile.TemporaryDirectory(prefix="printable-test-") as temp_dir:
        temp = Path(temp_dir)
        source = temp / "source.pdf"
        c = canvas.Canvas(str(source), pagesize=(612, 792))
        headings = []
        for index, title in enumerate(("Chapter One", "First Topic", "Chapter Two", "Final Topic"), start=1):
            c.setFont(FONT_BOLD, 18 if index in (1, 3) else 14)
            c.drawString(72, 700, title)
            c.setFont(FONT, 11)
            c.drawString(72, 660, f"Body content unique to source page {index}.")
            c.showPage()
            headings.append({"title": title, "level": 1 if index in (1, 3) else 2, "source_page": index})
        c.save()
        spec = {
            "title": "Printable Self Test",
            "subtitle": "",
            "author": "Boomer Rawlings",
            "inside_metadata": {"Author": "Boomer Rawlings"},
            "body_start": 1,
            "body_end": 4,
            "cover_source_page": None,
            "toc_source_pages": [],
            "headings": headings,
            "reuse_existing_numbers": False,
            "mask_existing_numbers": False,
            "number_start": 1,
            "mixed_page_policy": "keep",
            "scale_for_footer": False,
        }
        output = build(source, spec, temp / "result.pdf")
        qa = temp / "qa"
        count = render_pdf(output, qa, 96)
        assert count == 8, count
        assert len(list(qa.glob("page-*.png"))) == count
        print("self-test passed")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("input", type=Path)
    inspect_cmd.add_argument("--report", type=Path)
    build_cmd = sub.add_parser("build")
    build_cmd.add_argument("input", type=Path)
    build_cmd.add_argument("--spec", type=Path, required=True)
    build_cmd.add_argument("--output", type=Path)
    render_cmd = sub.add_parser("render")
    render_cmd.add_argument("input", type=Path)
    render_cmd.add_argument("--output-dir", type=Path, required=True)
    render_cmd.add_argument("--dpi", type=int, default=144)
    sub.add_parser("self-test")
    return root


def main() -> int:
    register_font()
    args = parser().parse_args()
    try:
        if args.command == "inspect":
            if not args.input.exists():
                blocked(f"Input does not exist: {args.input}", "Choose an existing source file.", "Choose another source? yes/no")
            report = inspect_source(args.input)
            payload = json.dumps(report, indent=2, ensure_ascii=False)
            if args.report:
                if args.report.exists():
                    blocked(f"Inspection report already exists: {args.report}", "Choose a new report path.", "Use a new report path? yes/no")
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(payload + "\n", encoding="utf-8")
                print(args.report.resolve())
            else:
                print(payload)
        elif args.command == "build":
            if not args.input.exists() or not args.spec.exists():
                blocked("Input or spec file does not exist.", "Choose existing input and spec files.", "Correct the paths? yes/no")
            spec = json.loads(args.spec.read_text(encoding="utf-8"))
            print(build(args.input, spec, args.output).resolve())
        elif args.command == "render":
            if not args.input.exists():
                blocked(f"Input does not exist: {args.input}", "Choose an existing PDF.", "Choose another PDF? yes/no")
            print(f"rendered {render_pdf(args.input, args.output_dir, args.dpi)} pages")
        else:
            self_test()
        return 0
    except PrintableError as exc:
        print(json.dumps({"status": "blocked", "reason": exc.reason, "resolution": exc.resolution, "prompt": exc.prompt}, ensure_ascii=False), file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(json.dumps({"status": "blocked", "reason": f"Spec JSON is invalid: {exc}", "resolution": "Correct the JSON syntax.", "prompt": "Correct the spec? yes/no"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
