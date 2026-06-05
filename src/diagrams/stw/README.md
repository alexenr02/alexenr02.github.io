# Software Thread Watchdog - Diagrams

Mermaid source files for the STW case study. Each `.mmd` file is one diagram.
They are imported as raw text by the project page and rendered in the browser by
`src/components/common/Mermaid.astro`, so editing a `.mmd` file is all you need
to change a diagram. No build step or component edit required.

## Files

| File                       | Section                  | Diagram type     |
| -------------------------- | ------------------------ | ---------------- |
| `01-problem-statement.mmd` | 1. Problem Statement     | `flowchart TD`   |
| `02-design-evolution.mmd`  | 2. Design Evolution      | `flowchart LR`   |
| `03-state-machine.mmd`     | 3. Architecture          | `stateDiagram-v2`|
| `03-slot-model.mmd`        | 3. Architecture          | `flowchart TD`   |
| `04-frame-layout.mmd`      | 4. CAN Diagnostic Report | `packet-beta`    |
| `04-fault-flow.mmd`        | 4. CAN Diagnostic Report | `flowchart LR`   |
| `05-cross-platform.mmd`    | 5. Cross-Platform Notes  | `flowchart TB`   |

Where each diagram appears on the page is wired up in
`src/content/projects/software-thread-watchdog.mdx` (the `import ... ?raw` lines
near the top, and the `<Mermaid />` tags in the body).

## How to fine-tune a diagram

1. Start the dev server so changes hot-reload:

```bash
npm run dev
```

2. Open the page: `http://localhost:4321/projects/software-thread-watchdog/`.
3. Edit the relevant `.mmd` file and save. The diagram re-renders on reload.

On the page, each diagram has an expand button (top-right) and is clickable:
clicking opens a near-fullscreen popup over a blurred backdrop. Inside the popup
the mouse wheel zooms toward the cursor, dragging pans, and double-click resets.
Press Escape or click the backdrop to close.

### Editing the diagram text (content and shapes)

- A node is `ID["Label text"]`. Change the text inside the quotes to relabel.
- Line breaks inside a label differ by diagram type:
  - In flowcharts use `\n` (the two characters `\` and `n`, not a real newline).
  - In the state diagram (`stateDiagram-v2`) use `<br/>` instead; `\n` shows up
    as literal text there.
- `A --> B` is a solid arrow, `A -.-> B` is a dashed arrow,
  `A -- "text" --> B` puts a label on the arrow.
- `{"..."}` is a decision/diamond node, `["..."]` is a box.
- `subgraph Name["Title"] ... end` groups nodes into a labeled box.
- Do not use emojis in labels.

To change the layout direction of a flowchart, edit its first line:
`flowchart TD` (top-down), `LR` (left-right), `TB`, or `RL`. Inside a subgraph,
`direction TB` overrides direction for that group only.

Validate any diagram syntax quickly by pasting it into the
[Mermaid Live Editor](https://mermaid.live).

### Editing colors, fonts, and curves (the look)

Visual styling is centralized in `src/components/common/Mermaid.astro`:

- `diagramVars` holds the colors for every diagram (node fill, borders, text,
  edge/line color, cluster background). The current look is high-contrast:
  white boxes, black borders, black text, black arrows. Tweak the hex values
  there to recolor everything at once. To give connectors their own color,
  change `lineColor` (and `edgeLabelBackground` for the label chips).
- Diagrams always render on a white canvas (set in the component's `.mermaid-diagram`
  style) so the black arrows stay visible in dark mode. Change that `background`
  if you switch to a dark box scheme.
- Layout uses the ELK engine (`layout: 'elk'`). ELK routes edges as right angles
  and connects them to the center of a box side, so each arrow approaches its box
  perpendicular and only the tip touches. `elk.mergeEdges: false` keeps parallel
  arrows separated; `nodeSpacing` / `rankSpacing` control spacing.
- Rendering is serialized by a single-flight guard in this file. Keep that guard:
  two overlapping Mermaid runs corrupt each other and trigger a "Syntax error"
  graphic, which is what caused earlier intermittent failures.
- `fontFamily` and `fontSize` are also set there.

To style a single node instead of all diagrams, use a Mermaid `classDef` inside
that one `.mmd` file, for example:

```text
classDef warn fill:#3a2a10,stroke:#f5a623,color:#fff;
class S1 warn;
```

### The frame layout diagram (`packet-beta`)

This one uses byte ranges, not nodes: `0-7: "Task ID"`. To change a field, edit
its label; to resize a field, change its bit range and keep the ranges
contiguous from 0 to 63 (8 bytes).

## Adding a new diagram

1. Add a `new-name.mmd` file in this folder.
2. In `software-thread-watchdog.mdx`, import it:
   `import newName from '../../diagrams/stw/new-name.mmd?raw';`
3. Place it in the body where you want it:
   `<Mermaid code={newName} label="Optional label" caption="Optional caption" />`
