# Skills

Reusable Codex skills by Boomer Rawlings.

## Included skills

| Skill | Purpose |
| --- | --- |
| [`printable`](skills/printable/) | Adds a restrained cover, accurate table of contents, and outside-edge page numbers for duplex printing. |
| [`bw-printable`](skills/bw-printable/) | Makes color-dependent visuals understandable in grayscale, then runs the full `printable` workflow. |

Each skill has its own instructions, interface metadata, and scripts. `bw-printable` uses `printable`, but they remain separate skills and can be maintained independently.

## Structure

```text
skills/
├── printable/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   └── scripts/
└── bw-printable/
    ├── SKILL.md
    ├── agents/openai.yaml
    └── scripts/
```

Add future skills as new folders under `skills/` using the same pattern.

## Install

Clone the repository and copy either or both skill folders into your Codex skills directory.

```powershell
git clone https://github.com/BoomerRawlings/Skills.git
Copy-Item -Recurse .\Skills\skills\printable "$env:USERPROFILE\.codex\skills\"
Copy-Item -Recurse .\Skills\skills\bw-printable "$env:USERPROFILE\.codex\skills\"
python -m pip install -r .\Skills\requirements.txt
```

`printable` currently requires Microsoft Word on Windows when converting DOCX input. PDF input does not require Word.

## Use

Attach a document, then invoke:

- `/printable` for print-ready organization and duplex page numbering.
- `/bw-printable` when visuals must remain understandable in black and white.

Both skills preserve body content and produce a new PDF rather than overwriting the source.

## Add another skill

1. Create `skills/<skill-name>/SKILL.md`.
2. Add `agents/openai.yaml` and any needed scripts.
3. Add one row to the skills table above.
4. Validate the skill before publishing.
