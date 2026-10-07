# Workflow data

UTF-8 JSON, without comments. Unknown fields are rejected to catch typos. All listed strings must contain non-whitespace text. Text is literal: HTML and Markdown are not rendered.

| Object | Required | Optional |
| --- | --- | --- |
| Root | `title`, `description`, `plans` | `eyebrow`, `footer` |
| Plan | `id`, `title`, `summary`, `steps` | `status` |
| Step | `id`, `title`, `description`, `artifact` | `checkpoint`, `related`, `resources` |
| Artifact | `title`, `code` | `language`, `note` |
| Resource | `label`, `url` | — |

- `plans` and `steps` are nonempty arrays; `related` and `resources` are arrays when present.
- Every other field is a string, except `artifact` (object) and `related` (array of strings).
- IDs start with a letter and contain only ASCII letters, digits, underscores, and hyphens. Plan IDs are globally unique. Step IDs are unique within their plan; reuse across plans is allowed.
- A step's `related` entries identify prerequisites in the same plan: `A.related: ["B"]` means explanation A depends on implementation B. Dashed arrows point from A to B. Duplicate, self, and dangling references are rejected. This is a display of declared dependencies, not an executable scheduler. Cycles between different steps may represent feedback loops.
- `checkpoint` states what must be true before moving on. `artifact.note` gives context about the shown artifact. `language` is a display label, not an instruction to execute code.
- Resource URLs must be absolute `https://` or `http://` URLs, without credentials, spaces, or control characters. Relative paths, `javascript:`, `data:`, `file:`, and protocol-relative URLs are rejected.

## Minimal complete example

```json
{
  "title": "Publish a useful note",
  "description": "A small editorial workflow, with the actual working artifacts beside each step.",
  "plans": [
    {
      "id": "publish",
      "title": "Draft to publication",
      "summary": "Agree on the reader's question, then use it to review the draft.",
      "steps": [
        {
          "id": "brief",
          "title": "Define the question",
          "description": "Name one reader and the decision the note helps them make.",
          "artifact": {
            "title": "Brief",
            "code": "Reader: first-time contributor\nQuestion: Which issue should I start with?\nUseful outcome: choose one bounded task"
          }
        },
        {
          "id": "review",
          "title": "Review against the brief",
          "description": "Check that the draft actually supports the reader's decision.",
          "checkpoint": "A reader can choose a task without asking for missing context.",
          "artifact": {
            "title": "Review checklist",
            "language": "text",
            "code": "[ ] Explain the decision\n[ ] Include a concrete example\n[ ] Link the next action"
          },
          "related": ["brief"]
        }
      ]
    }
  ]
}
```

Validate before building:

```sh
node scripts/validate.mjs my-workflow.json
```

Errors include the data path and reason, for example `data.plans[0].steps[1].related[0]: unknown step ...`.

## Writing useful pairs

Keep the explanation focused on purpose, inputs, and decisions. Put the concrete working material in `artifact.code`, even when that material is prose. A prompt should contain enough context to use; a checklist should have observable criteria; sample output should be labeled as a sample. Add `related` on the consuming step and point it at the prerequisite step. Do not connect steps merely because both exist.

Artifacts can contain quotes, angle brackets, code, and line breaks. The generator escapes embedded JSON; the renderer displays strings as text. Never change this to HTML interpolation when adapting the implementation.
