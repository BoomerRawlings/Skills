# Skills

Reusable Codex skills by Boomer Rawlings.

## Included skills

| Skill | Purpose |
| --- | --- |
| [`printable`](skills/printable/) | Adds a restrained cover, accurate table of contents, and outside-edge page numbers for duplex printing. |
| [`bw-printable`](skills/bw-printable/) | Makes color-dependent visuals understandable in grayscale, then runs the full `printable` workflow. |
| [`lecture-study-guide`](skills/lecture-study-guide/) | Collects lecture inputs and builds a cited, printable study guide with practice questions and separate source and visual audits. |

Each skill has its own instructions, interface metadata, and scripts. `bw-printable` uses `printable`, but they remain separate skills and can be maintained independently.

## Structure

```text
skills/
├── printable/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   └── scripts/
├── bw-printable/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   └── scripts/
└── lecture-study-guide/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── references/
    └── scripts/
```

Add future skills as new folders under `skills/` using the same pattern.

## Install

Clone the repository and copy the skill folders you want into your Codex skills directory.

```powershell
git clone https://github.com/BoomerRawlings/Skills.git
Copy-Item -Recurse .\Skills\skills\printable "$env:USERPROFILE\.codex\skills\"
Copy-Item -Recurse .\Skills\skills\bw-printable "$env:USERPROFILE\.codex\skills\"
Copy-Item -Recurse .\Skills\skills\lecture-study-guide "$env:USERPROFILE\.codex\skills\"
python -m pip install -r .\Skills\requirements.txt
```

`printable` currently requires Microsoft Word on Windows when converting DOCX input. PDF input does not require Word.

## Use

Attach a document, then invoke:

- `/printable` for print-ready organization and duplex page numbering.
- `/bw-printable` when visuals must remain understandable in black and white.

Both skills preserve body content and produce a new PDF rather than overwriting the source.

For a lecture packet, invoke `$lecture-study-guide` with the course/week, lecture links or files, and any study questions, transcripts or slides. It inventories existing materials and asks only for missing inputs. The workflow produces organized sources, a cited guide, original practice and an answer key, followed by separate source and page-by-page visual audits. Letter duplex layout and UCSD colors are configurable defaults; no university affiliation is implied.

Transcript retrieval and PDF rendering use the tools available in your Codex environment. Inaccessible lecture content remains a documented gap until supplied; the skill does not guarantee caption access. Its optional Python helper requires `pypdf` (included in `requirements.txt`):

```text
python skills/lecture-study-guide/scripts/check_pdf.py guide.pdf --expected expected.json --report pdf-check.json
```

The helper checks PDF structure, links and expected text; it does not verify source claims or visual layout. See [audit instructions](skills/lecture-study-guide/references/audits.md) for the expected-content format and review process.

## Add another skill

1. Create `skills/<skill-name>/SKILL.md`.
2. Add `agents/openai.yaml` and any needed scripts.
3. Add one row to the skills table above.
4. Validate the skill before publishing.
