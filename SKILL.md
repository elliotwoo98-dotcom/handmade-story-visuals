---
name: handmade-story-visuals
description: Create original handmade narrative image prompts from stories, scenes, educational content, and recurring-character series. Use when users ask for hand-drawn, collage, paper-craft, sketch, chalk, crayon, gouache, or storybook visuals; need automatic style selection; need exact visible-text preservation; or need consistent prompt packages for a visual series.
---

# Handmade Story Visuals

Turn a scene or story into a tool-independent prompt package using an original handmade visual language. Deliver prompts by default; generate images only when the user explicitly asks and an image tool is available.

## Workflow

1. Extract the subject, narrative focus, aspect ratio, visible text, character locks, and series context. Keep supplied wording exact.
2. Respect an explicitly named catalog style. Otherwise select `auto` and let the compiler recommend one from the content.
3. Read [references/styles.json](references/styles.json) when comparing styles or explaining a recommendation. Do not blend recipes unless the user explicitly requests a hybrid.
4. Run [scripts/compile_prompt.py](scripts/compile_prompt.py) to produce the positive prompt, negative prompt, selected-style evidence, and checks.
5. Return the compiled package in the requested format. If no format is requested, return the readable text form.
6. Before image generation or handoff, apply the checks in [references/workflow.md](references/workflow.md).

## Compile A Prompt

Use one `--text` argument for each exact string that must appear in the image:

```bash
python3 scripts/compile_prompt.py \
  --subject "雨夜里，女孩把唯一的伞递给陌生老人" \
  --intent "突出善意发生前后的情绪变化" \
  --style auto \
  --aspect 9:16 \
  --text "把伞留给更需要的人" \
  --character-lock "女孩：短发、黄色雨衣、红色布鞋"
```

For a production pipeline, request structured output:

```bash
python3 scripts/compile_prompt.py \
  --subject "同一位女孩第二天回到公交站" \
  --style graphite-moment \
  --aspect 9:16 \
  --character-lock "女孩：短发、黄色雨衣、红色布鞋" \
  --series-context "沿用上一张的雨夜城市、人物比例与低饱和配色" \
  --no-text \
  --format json
```

List the available styles with:

```bash
python3 scripts/compile_prompt.py --list-styles
```

## Guardrails

- Preserve each `--text` value byte-for-byte in the prompt package. Do not translate, polish, shorten, merge, or add punctuation.
- Treat character locks and series context as fixed continuity data, not optional inspiration.
- Keep style selection separate from subject matter. Never replace the user's scene merely to fit a recipe.
- Describe visual properties instead of naming artists, studios, franchises, or protected characters. Do not claim exact imitation.
- Avoid inserting an aspect ratio when the user has not supplied one.
- Do not promise that an image model will spell text correctly. Verify the rendered image; use a separate typography pass when exact lettering is critical.
- Keep positive and negative prompts separate. Do not hide content changes inside the negative prompt.

## Resources

- [references/styles.json](references/styles.json): canonical style catalog and aliases.
- [references/workflow.md](references/workflow.md): selection, continuity, lettering, and delivery checks.
- [references/output-schema.json](references/output-schema.json): structured output contract.
- [scripts/compile_prompt.py](scripts/compile_prompt.py): deterministic prompt compiler.
