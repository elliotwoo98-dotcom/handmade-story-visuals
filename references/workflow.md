# Production Workflow

## 1. Freeze The Request

Record these inputs before selecting a style:

- Subject: who or what is visible, doing what, and where.
- Narrative focus: the emotion, explanation, or turning point the image must communicate.
- Format: aspect ratio or destination if supplied.
- Visible text: every exact string that must be rendered.
- Character locks: traits that cannot drift between images.
- Series context: recurring palette, location, props, framing, and world rules.

Do not infer new visible text. When no text is supplied, default to a text-free image.

## 2. Select One Style

Honor a valid style ID, slug, Chinese name, or alias. For `auto`, score the subject and narrative focus against `recommend_keywords` in `styles.json`. Give concrete subject signals more weight than generic intent words so a location, medium, or event is not displaced by broad emotional language. The compiler returns matched keywords so the choice remains inspectable.

When no keyword matches, use the catalog's `default_style`. Change the selected style only when the user's priorities conflict with its `avoid_for` guidance. Explain that conflict briefly instead of silently blending styles.

## 3. Lock Continuity

For a series, reuse all of the following on every compilation:

- The same style slug.
- The same aspect ratio.
- The full character-lock strings, including colors and distinctive objects.
- The same series context unless the story explicitly changes it.
- Previously approved spellings and visible-text punctuation.

Treat a changed costume, time of day, or location as a scene change. Do not let it erase unrelated identity traits.

## 4. Compile And Generate

Use `scripts/compile_prompt.py` instead of reconstructing the recipe manually. Pass the positive prompt and negative prompt to separate fields when the image backend supports them. If it accepts only one prompt, append a clearly labeled avoidance paragraph after the positive prompt without rewriting either section.

If the user asks for image generation, generate only after the prompt package is ready. Preserve the compiled package alongside the result so later frames can reuse the same locks.

## 5. Verify

Check the output in this order:

1. The requested event is visually legible.
2. Character identity and locked props remain stable.
3. The selected handmade medium is visible in lines, surfaces, and edges, not merely named in metadata.
4. Composition suits the supplied aspect ratio.
5. Every supplied visible string matches exactly and no extra text appears.
6. No signature, watermark, brand mark, known character, artist name, or studio name was introduced.

If lettering fails, keep the approved illustration and correct only the lettering layer. Do not regenerate the entire scene unless the composition also failed.
