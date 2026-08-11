#!/usr/bin/env python3
"""Compile a deterministic prompt package from the handmade style catalog."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = SKILL_ROOT / "references" / "styles.json"
SCHEMA_VERSION = "1.0"
SUBJECT_KEYWORD_WEIGHT = 3
RECIPE_FIELDS = (
    "medium",
    "line",
    "palette",
    "composition",
    "light",
    "surface",
    "characters",
    "lettering",
)
RECIPE_LABELS = {
    "medium": "材料",
    "line": "线条",
    "palette": "配色",
    "composition": "构图",
    "light": "光线",
    "surface": "手作痕迹",
    "characters": "人物",
    "lettering": "文字承载",
}


class CatalogError(ValueError):
    """Raised when the bundled style catalog is malformed."""


def _normalise(value: str) -> str:
    return re.sub(r"[\s_]+", "-", value.strip().casefold())


def _require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"{label} must be a non-empty string")
    return value


def _require_string_list(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise CatalogError(f"{label} must be a non-empty list")
    for index, item in enumerate(value):
        _require_nonempty_string(item, f"{label}[{index}]")
    return value


def validate_catalog(catalog: Any) -> dict[str, Any]:
    if not isinstance(catalog, dict):
        raise CatalogError("catalog root must be an object")

    _require_nonempty_string(catalog.get("catalog_version"), "catalog_version")
    default_style = _require_nonempty_string(catalog.get("default_style"), "default_style")
    styles = catalog.get("styles")
    if not isinstance(styles, list) or not styles:
        raise CatalogError("styles must be a non-empty list")

    selectors: dict[str, str] = {}
    slugs: set[str] = set()
    for index, style in enumerate(styles):
        label = f"styles[{index}]"
        if not isinstance(style, dict):
            raise CatalogError(f"{label} must be an object")

        style_id = _require_nonempty_string(style.get("id"), f"{label}.id")
        slug = _require_nonempty_string(style.get("slug"), f"{label}.slug")
        name = _require_nonempty_string(style.get("name"), f"{label}.name")
        if not re.fullmatch(r"S[0-9]{2}", style_id):
            raise CatalogError(f"{label}.id must match S00")
        if not re.fullmatch(r"[a-z0-9-]+", slug):
            raise CatalogError(f"{label}.slug must use lowercase letters, digits, and hyphens")
        if slug in slugs:
            raise CatalogError(f"duplicate style slug: {slug}")
        slugs.add(slug)

        aliases = _require_string_list(style.get("aliases"), f"{label}.aliases")
        _require_nonempty_string(style.get("summary"), f"{label}.summary")
        _require_string_list(style.get("best_for"), f"{label}.best_for")
        _require_string_list(style.get("avoid_for"), f"{label}.avoid_for")
        keywords = _require_string_list(
            style.get("recommend_keywords"), f"{label}.recommend_keywords"
        )
        if any(len(keyword.strip()) < 2 for keyword in keywords):
            raise CatalogError(f"{label}.recommend_keywords cannot contain one-character terms")
        _require_string_list(style.get("negative"), f"{label}.negative")

        recipe = style.get("recipe")
        if not isinstance(recipe, dict):
            raise CatalogError(f"{label}.recipe must be an object")
        if set(recipe) != set(RECIPE_FIELDS):
            missing = sorted(set(RECIPE_FIELDS) - set(recipe))
            extra = sorted(set(recipe) - set(RECIPE_FIELDS))
            raise CatalogError(f"{label}.recipe fields mismatch; missing={missing}, extra={extra}")
        for field in RECIPE_FIELDS:
            _require_nonempty_string(recipe[field], f"{label}.recipe.{field}")

        for selector in (style_id, slug, name, *aliases):
            token = _normalise(selector)
            if token == "auto":
                raise CatalogError(f"reserved selector used by {slug}: {selector}")
            if token in selectors:
                raise CatalogError(
                    f"duplicate selector {selector!r} shared by {selectors[token]} and {slug}"
                )
            selectors[token] = slug

    if default_style not in slugs:
        raise CatalogError(f"default_style does not match a slug: {default_style}")
    return catalog


def load_catalog(path: Path | str = DEFAULT_CATALOG) -> dict[str, Any]:
    catalog_path = Path(path)
    try:
        payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CatalogError(f"catalog not found: {catalog_path}") from exc
    except json.JSONDecodeError as exc:
        raise CatalogError(f"invalid JSON in {catalog_path}: {exc}") from exc
    return validate_catalog(payload)


def _style_selectors(style: dict[str, Any]) -> Iterable[str]:
    yield style["id"]
    yield style["slug"]
    yield style["name"]
    yield from style["aliases"]


def resolve_style(catalog: dict[str, Any], query: str) -> dict[str, Any]:
    token = _normalise(query)
    for style in catalog["styles"]:
        if any(_normalise(selector) == token for selector in _style_selectors(style)):
            return style
    valid = ", ".join(style["slug"] for style in catalog["styles"])
    raise ValueError(f"unknown style {query!r}; choose one of: {valid}")


def recommend_style(
    catalog: dict[str, Any], subject: str, intent: str = ""
) -> tuple[dict[str, Any], list[str], str]:
    subject_text = subject.casefold()
    intent_text = intent.casefold()
    ranked: list[tuple[int, int, int, int, dict[str, Any], list[str]]] = []
    for index, style in enumerate(catalog["styles"]):
        subject_hits = [
            keyword
            for keyword in style["recommend_keywords"]
            if keyword.casefold() in subject_text
        ]
        intent_hits = [
            keyword
            for keyword in style["recommend_keywords"]
            if keyword.casefold() in intent_text and keyword not in subject_hits
        ]
        hits = [*subject_hits, *intent_hits]
        score = len(subject_hits) * SUBJECT_KEYWORD_WEIGHT + len(intent_hits)
        ranked.append((score, len(subject_hits), len(hits), -index, style, hits))

    score, _, _, _, style, hits = max(ranked, key=lambda item: item[:4])
    if score:
        return style, hits, "automatic"
    fallback = resolve_style(catalog, catalog["default_style"])
    return fallback, [], "fallback"


def _quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _deduplicate(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _validate_inputs(
    subject: str,
    visible_text: Sequence[str],
    character_locks: Sequence[str],
) -> None:
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("subject must be a non-empty string")
    for label, values in (
        ("visible_text", visible_text),
        ("character_locks", character_locks),
    ):
        for index, value in enumerate(values):
            if not isinstance(value, str) or value == "":
                raise ValueError(f"{label}[{index}] must be a non-empty string")


def build_prompt(
    style: dict[str, Any],
    *,
    subject: str,
    intent: str = "",
    aspect: str | None = None,
    visible_text: Sequence[str] = (),
    character_locks: Sequence[str] = (),
    series_context: str = "",
) -> str:
    sections = [
        f"【画面任务】\n{subject}",
    ]
    if intent:
        sections.append(f"【叙事重点】\n{intent}")

    sections.append(
        f"【风格身份】\n{style['name']}（{style['slug']}）。{style['summary']}"
    )
    recipe_lines = [
        f"- {RECIPE_LABELS[field]}：{style['recipe'][field]}" for field in RECIPE_FIELDS
    ]
    sections.append("【视觉配方】\n" + "\n".join(recipe_lines))

    if aspect:
        sections.append(f"【画幅】\n使用用户指定的 {aspect}；为该画幅重新组织构图，不裁掉关键动作。")

    if character_locks:
        lock_lines = [f"- {_quoted(value)}" for value in character_locks]
        sections.append(
            "【角色连续性（锁定数据）】\n"
            + "\n".join(lock_lines)
            + "\n逐项保留这些特征；场景变化不得导致无关身份特征漂移。"
        )

    if series_context:
        sections.append(
            "【系列连续性（锁定数据）】\n"
            + series_context
            + "\n沿用其中未被本次场景明确改写的设定。"
        )

    if visible_text:
        text_lines = [f"{index}. {_quoted(value)}" for index, value in enumerate(visible_text, 1)]
        sections.append(
            "【画面文字（锁定数据）】\n"
            "只呈现下列字符串，逐字、逐标点保持原样：\n"
            + "\n".join(text_lines)
            + "\n不得翻译、润色、缩写、拆字、合并、增删标点，也不得添加其他可见字符。"
        )
    else:
        sections.append("【画面文字】\n画面中不出现任何文字、字母、数字、签名、水印或品牌标识。")

    sections.append(
        "【原创边界】\n只使用上述通用材料、线条、色彩与构图特征；不引用艺术家、工作室、影视作品或现成角色名称，不复制已知作品构图。"
    )
    return "\n\n".join(sections)


def build_negative_prompt(style: dict[str, Any], *, has_visible_text: bool) -> str:
    lettering_avoidance = (
        ["错字", "漏字", "多字", "擅自改写", "随机字符", "额外标题"]
        if has_visible_text
        else ["任何可见文字", "字母", "数字"]
    )
    global_avoidance = [
        "水印",
        "平台标识",
        "未经要求的签名",
        "品牌标识",
        "现成IP角色",
        "艺术家姓名",
        "工作室姓名",
        "照搬已知作品构图",
    ]
    return "，".join(_deduplicate([*style["negative"], *lettering_avoidance, *global_avoidance]))


def build_quality_checks(
    *,
    aspect: str | None,
    visible_text: Sequence[str],
    character_locks: Sequence[str],
    series_context: str,
) -> list[str]:
    checks = [
        "主体、动作、地点和叙事转折与用户描述一致",
        "线条、边缘和表面能看出所选手作材料，而不是只有风格标签",
        "未引入艺术家、工作室、现成角色、品牌标识、签名或水印",
    ]
    if aspect:
        checks.append(f"成图使用 {aspect}，关键动作和文字均未被裁切")
    if character_locks:
        checks.append("逐项核对所有角色锁定特征，未发生无关漂移")
    if series_context:
        checks.append("与系列上下文中的配色、空间、道具和世界规则保持一致")
    if visible_text:
        checks.append("逐字核对每个锁定字符串，并确认没有任何额外可见文字")
    else:
        checks.append("画面中没有任何可见文字、字母、数字、签名、水印或品牌标识")
    return checks


def compile_package(
    catalog: dict[str, Any],
    *,
    subject: str,
    intent: str = "",
    style_query: str = "auto",
    aspect: str | None = None,
    visible_text: Sequence[str] = (),
    character_locks: Sequence[str] = (),
    series_context: str = "",
) -> dict[str, Any]:
    _validate_inputs(subject, visible_text, character_locks)
    if _normalise(style_query) == "auto":
        style, matched_keywords, selection_mode = recommend_style(catalog, subject, intent)
    else:
        style = resolve_style(catalog, style_query)
        matched_keywords = []
        selection_mode = "explicit"

    prompt = build_prompt(
        style,
        subject=subject,
        intent=intent,
        aspect=aspect,
        visible_text=visible_text,
        character_locks=character_locks,
        series_context=series_context,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "selected_style": {
            "id": style["id"],
            "slug": style["slug"],
            "name": style["name"],
            "selection_mode": selection_mode,
            "matched_keywords": matched_keywords,
        },
        "inputs": {
            "subject": subject,
            "intent": intent,
            "aspect": aspect,
            "visible_text": list(visible_text),
            "character_locks": list(character_locks),
            "series_context": series_context,
        },
        "prompt": prompt,
        "negative_prompt": build_negative_prompt(style, has_visible_text=bool(visible_text)),
        "quality_checks": build_quality_checks(
            aspect=aspect,
            visible_text=visible_text,
            character_locks=character_locks,
            series_context=series_context,
        ),
    }


def format_text(package: dict[str, Any]) -> str:
    style = package["selected_style"]
    matched = "、".join(style["matched_keywords"]) or "无（使用默认通用风格）"
    if style["selection_mode"] == "explicit":
        selection = "用户指定"
    elif style["selection_mode"] == "automatic":
        selection = f"自动推荐；命中：{matched}"
    else:
        selection = "自动回退；未命中关键词"
    checks = "\n".join(
        f"{index}. {item}" for index, item in enumerate(package["quality_checks"], 1)
    )
    return (
        f"风格：{style['id']} {style['name']}（{style['slug']}）\n"
        f"选择方式：{selection}\n\n"
        f"正向提示词：\n{package['prompt']}\n\n"
        f"反向提示词：\n{package['negative_prompt']}\n\n"
        f"检查清单：\n{checks}"
    )


def list_styles(catalog: dict[str, Any], output_format: str) -> str:
    rows = [
        {
            "id": style["id"],
            "slug": style["slug"],
            "name": style["name"],
            "summary": style["summary"],
            "aliases": style["aliases"],
        }
        for style in catalog["styles"]
    ]
    if output_format == "json":
        return json.dumps(rows, ensure_ascii=False, indent=2)
    return "\n".join(
        f"{row['id']}  {row['name']}  [{row['slug']}] - {row['summary']}" for row in rows
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compile an original handmade narrative image prompt package."
    )
    parser.add_argument("--subject", help="Scene, story beat, or content to depict")
    parser.add_argument("--intent", default="", help="Narrative focus or communication goal")
    parser.add_argument("--style", default="auto", help="Style ID, slug, name, alias, or auto")
    parser.add_argument("--aspect", help="User-supplied aspect ratio, such as 9:16")
    text_group = parser.add_mutually_exclusive_group()
    text_group.add_argument(
        "--text",
        action="append",
        default=[],
        help="Exact visible string; repeat for multiple strings",
    )
    text_group.add_argument(
        "--no-text",
        action="store_true",
        help="Explicitly request a text-free image (also the default)",
    )
    parser.add_argument(
        "--character-lock",
        action="append",
        default=[],
        help="Fixed character traits; repeat for multiple characters",
    )
    parser.add_argument("--series-context", default="", help="Palette, world, prop, and framing locks")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--list-styles", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        catalog = load_catalog(args.catalog)
        if args.list_styles:
            print(list_styles(catalog, args.format))
            return 0
        if not args.subject:
            parser.error("--subject is required unless --list-styles is used")
        package = compile_package(
            catalog,
            subject=args.subject,
            intent=args.intent,
            style_query=args.style,
            aspect=args.aspect,
            visible_text=args.text,
            character_locks=args.character_lock,
            series_context=args.series_context,
        )
        if args.format == "json":
            print(json.dumps(package, ensure_ascii=False, indent=2))
        else:
            print(format_text(package))
        return 0
    except (CatalogError, ValueError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
