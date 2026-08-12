# Handmade Story Visuals

An original Codex Skill that turns stories, scenes, educational content, and recurring narratives into consistent, reusable prompt packages for handmade visuals.

The Skill is model-agnostic and does not imitate specific artists, studios, or protected characters. It selects a suitable handmade medium for the content, preserves user-specified visible text and character details, and produces a positive prompt, a separate negative prompt, and a set of validation checks.

## Key Features

- Automatically recommends a handmade visual style based on the story, with support for manual selection.
- Includes 10 independently designed style recipes covering graphite, gouache, collage, chalk, wax crayon, and layered paper.
- Preserves required on-image text exactly, without translating, polishing, or changing punctuation.
- Locks character appearance, clothing, props, colors, and scene rules across a visual series.
- Respects user-provided aspect ratios for landscape, portrait, and other formats.
- Produces readable text output or structured JSON for automated workflows.
- Uses a deterministic compiler for reproducible style selection and prompt assembly.

## Included Styles

| ID | Style | Slug | Best For |
| --- | --- | --- | --- |
| S01 | Graphite Moment | `graphite-moment` | Restrained emotion, memories, and quiet moments |
| S02 | Street-Corner Gouache | `street-corner-gouache` | Neighborhoods, rainy nights, and people in everyday environments |
| S03 | Single-Line Fable | `single-line-fable` | Cause and effect, philosophical ideas, and visual metaphors |
| S04 | Windowlight Wax | `windowlight-wax` | Warm interiors, close relationships, and gentle stories |
| S05 | Ticket-Stub Collage | `ticket-stub-collage` | Travel, letters, memories, and meaningful objects |
| S06 | Midnight Chalk Stage | `midnight-chalk-stage` | Nighttime stories, imaginative scenes, and approachable explanations |
| S07 | Black-Gold Parable | `black-gold-parable` | Philosophical turns, traditional wisdom, and solemn narratives |
| S08 | Layered Paper Theatre | `layered-paper-theatre` | Fairy tales, dimensional scenes, and layered storytelling |
| S09 | Notebook Explainer | `notebook-explainer` | Step-by-step guides, educational content, and storyboards |
| S10 | Postcard Storybook | `postcard-storybook` | Everyday stories, warm moments, and general-purpose scenes |

When `auto` is selected, the compiler uses explainable keyword matching based on the subject and narrative focus. If no style matches, it falls back to `postcard-storybook`.

## Installation

Clone the repository into your Codex Skills directory:

```bash
git clone https://github.com/elliotwoo98-dotcom/handmade-story-visuals.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/handmade-story-visuals"
```

Restart Codex or open a new task to make the Skill available.

## Use in Codex

Describe the result you need in natural language. No command syntax is required:

```text
Turn "On a rainy night, a girl gives her only umbrella to an elderly stranger"
into a 9:16 handmade story visual. The image must include the exact text
"Leave the umbrella for someone who needs it more." Keep the character consistent:
short hair, a yellow raincoat, and red canvas shoes.
```

You can also select a catalog style or request continuity across multiple images:

```text
Use the black-gold-parable style to create prompt packages for three consecutive
scenes from this philosophical story. Keep the same character, clothing, and
aspect ratio across all three images. Do not include any visible text.
```

The Skill returns a prompt package by default. It generates images only when the user explicitly requests them and an image-generation tool is available.

## Use the Compiler Directly

Generate a readable prompt package:

```bash
python3 scripts/compile_prompt.py \
  --subject "On a rainy night, a girl gives her only umbrella to an elderly stranger" \
  --intent "Emphasize the emotional change before and after the act of kindness" \
  --style auto \
  --aspect 9:16 \
  --text "Leave the umbrella for someone who needs it more." \
  --character-lock "Girl: short hair, yellow raincoat, red canvas shoes"
```

Generate structured JSON:

```bash
python3 scripts/compile_prompt.py \
  --subject "The same girl returns to the bus stop the next day" \
  --style graphite-moment \
  --aspect 9:16 \
  --character-lock "Girl: short hair, yellow raincoat, red canvas shoes" \
  --series-context "Continue the rainy city, character proportions, and muted palette from the previous image" \
  --no-text \
  --format json
```

List all available styles:

```bash
python3 scripts/compile_prompt.py --list-styles
```

## Output

Each prompt package contains:

- Original input and continuity locks
- Selected style and selection evidence
- Positive prompt
- Separate negative prompt
- Visible-text requirements and pre-generation checks

The JSON output format is defined in [`references/output-schema.json`](references/output-schema.json).

## Project Structure

```text
handmade-story-visuals/
|-- README.md                      # Project overview, installation, and usage
|-- SKILL.md                       # Skill entry point and core workflow
|-- agents/openai.yaml             # Codex interface metadata
|-- references/
|   |-- styles.json                # Style catalog, aliases, and selection keywords
|   |-- workflow.md                # Continuity, lettering, and delivery checks
|   `-- output-schema.json         # JSON output contract
|-- scripts/compile_prompt.py       # Deterministic prompt compiler
`-- tests/test_compile_prompt.py    # Unit tests
```

## Testing

The project uses only the Python standard library. Run the test suite with:

```bash
python3 -m unittest discover -s tests -v
```

The tests cover style parsing, automatic recommendations, default fallback behavior, exact text preservation, no-text constraints, continuity locks, output structure, and command-line behavior.

## Design Principles

- Express the story faithfully before selecting a visual medium.
- Never rewrite user-provided visible text or character-lock details.
- Describe observable linework, materials, color, composition, and surface qualities.
- Do not use artist, studio, franchise, or protected-character names to request exact imitation.
- Verify exact lettering after image generation and use a separate typography pass when necessary.

## License

The Skill, style recipes, workflow, and scripts in this repository are original work. This project is licensed under the [MIT License](LICENSE), allowing use, modification, distribution, and commercial use while retaining the copyright and license notice.
