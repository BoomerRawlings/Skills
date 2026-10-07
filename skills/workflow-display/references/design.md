# Preserve pairs, connections, and motion

Inspired by Boomer Rawlings' paired implementation walkthrough. Its transferable idea is an explanation directly paired with the artifact that makes the explanation concrete, connected to other relevant pairs. Matching a particular palette is unnecessary.

## Layout

On wide screens, show a readable explanation column and an artifact column in the same step row. On narrow screens, stack each explanation immediately with its artifact. Do not stack all explanations before all artifacts. Keep step identity visible when content unfolds, and allow long code lines to scroll inside the artifact rather than widening the page.

Plans group coherent processes. Their step order communicates the reading sequence; explicit related links communicate dependencies. `A.related: ["B"]` points from explanation A to required implementation B. Solid lines pair a step with its own artifact; dashed arrows show dependencies. Label connections well enough that readers can understand them without relying on color alone.

Artifact blocks preserve whitespace and scroll internally by default. The Wrap button is useful for prose; keep wrapping off for aligned tables or code whose layout matters.

## Motion and geometry

Opening a plan should unfold its contents smoothly. Connection changes should remain visually attached to the relevant cards throughout opening, closing, switching, and resizing. Measure the actual rendered anchors, not assumed row heights. Long descriptions and artifacts change geometry.

Keep animation durations short enough for repeated exploration. Respect the operating system's reduced-motion preference by removing unnecessary travel and interpolation while keeping the same final information and connections. Keep pointer and keyboard interactions equivalent; selected or expanded states must be exposed to assistive technology.

## Customization

`assets/workflow.css` owns visual styling; `assets/workflow.js` owns rendering and interactions; `assets/template.html` is the document shell. Edit these source assets and rebuild. The generator injects the `{{STYLES}}`, `{{DATA}}`, and `{{SCRIPT}}` markers exactly once each. Do not remove or duplicate them.

Use the destination site's typography, spacing, surfaces, and accent colors. Preserve visible focus, text contrast, explanation/artifact grouping, and connection readability. No logo, network font, brand color, framework, or external animation library is required.

For framework integration, keep the same data contract, render user strings as text, and use safe external links. After mounting or layout changes, recalculate connector positions. Avoid measuring hidden content as if it were visible. Scope IDs and events so multiple display instances can coexist.

## Browser acceptance check

1. Switch every plan and open/close content repeatedly. Verify the correct pairs remain together and motion settles cleanly.
2. Activate a related-step link. Confirm the intended step and its artifact are clear; inspect connections after the layout settles.
3. Resize from desktop to a narrow phone width. Verify connector endpoints, local code scrolling, and no page-level horizontal overflow.
4. Use only the keyboard through the controls and links; verify focus and expanded/selected state.
5. Enable reduced motion and repeat the interactions. The information and final state must match.
6. Try a long multiline artifact and text containing `<script>`, `&`, quotes, and template-marker strings. They must appear as text and leave interactions functional.

The Node regression tests cannot replace these browser checks.
