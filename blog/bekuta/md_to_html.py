#!/usr/bin/env python3
"""Convert Markdown files into site-styled HTML blog posts."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Tuple

import markdown

SITE_URL = "https://datavorous.github.io"


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <title>{title}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="{description}">
    <meta name="author" content="{author}">
    {og_image_meta}
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/bash.min.js"></script>
    <script>hljs.highlightAll();</script>
    <link rel="stylesheet" href="{site_css}">
</head>
<body>
    <div class="nav-links">
        <a href="{home_href}">home</a> | <a href="https://github.com/datavorous">github</a> | <a href="https://x.com/datavorous_">twitter</a>
    </div>
{content}
</body>
</html>
"""


def get_relative_asset_path(from_file: Path, to_file: Path) -> str:
    return os.path.relpath(to_file.resolve(), start=from_file.parent.resolve())


def convert_markdown(md_text: str) -> str:
    return markdown.markdown(
        md_text,
        extensions=[
            "fenced_code",
            "tables",
            "sane_lists",
            "toc",
        ],
    )


def parse_front_matter(md_text: str) -> Tuple[dict[str, str], str]:
    lines = md_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, md_text

    metadata: dict[str, str] = {}
    end_index = None
    for i in range(1, len(lines)):
        line = lines[i].strip()
        if line == "---":
            end_index = i
            break
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip().lower()] = value.strip().strip('"').strip("'")

    if end_index is None:
        return {}, md_text

    body = "\n".join(lines[end_index + 1 :]).lstrip("\n")
    return metadata, body


def build_html(
    title: str,
    description: str,
    author: str,
    og_image: str | None,
    date_text: str | None,
    site_css: str,
    home_href: str,
    content: str,
) -> str:
    if date_text:
        date_block = f'\n<div class="publish-date">{date_text}</div>'
        h1_pattern = re.compile(r"(<h1\b[^>]*>.*?</h1>)", flags=re.DOTALL)
        if h1_pattern.search(content):
            content = h1_pattern.sub(r"\1" + date_block, content, count=1)
        else:
            content = f'<div class="publish-date">{date_text}</div>\n{content}'

    og_image_meta = ""
    if og_image:
        og_image_meta = (
            f'<meta property="og:image" content="{og_image}">\n'
            f'    <meta name="twitter:card" content="summary_large_image">\n'
            f'    <meta name="twitter:image" content="{og_image}">'
        )

    return TEMPLATE.format(
        title=title,
        description=description,
        author=author,
        og_image_meta=og_image_meta,
        site_css=site_css,
        home_href=home_href,
        content=content,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Markdown to site-themed HTML.")
    parser.add_argument("input", type=Path, help="Path to input markdown file.")
    parser.add_argument("output", type=Path, help="Path to output html file.")
    parser.add_argument("--title", default="", help="Page title.")
    parser.add_argument("--description", default="", help="Meta description.")
    parser.add_argument("--author", default="", help="Author meta field.")
    parser.add_argument("--date", default="", help="Publish date text (optional).")
    args = parser.parse_args()

    raw_md = args.input.read_text(encoding="utf-8")
    metadata, md_text = parse_front_matter(raw_md)
    content = convert_markdown(md_text)

    title = args.title or metadata.get("title") or args.input.stem
    description = args.description or metadata.get("description") or title
    author = args.author or metadata.get("author") or "datavorous"
    date_text = args.date.strip() or metadata.get("date") or None

    repo_root = Path(__file__).resolve().parents[2]
    css_path = repo_root / "extra" / "index.css"
    home_path = repo_root / "index.html"
    og_image_raw = metadata.get("og_image", "").strip()

    site_css = get_relative_asset_path(args.output, css_path)
    home_href = get_relative_asset_path(args.output, home_path)
    og_image = None
    if og_image_raw:
        if og_image_raw.startswith("http://") or og_image_raw.startswith("https://"):
            og_image = og_image_raw
        else:
            og_path = og_image_raw.lstrip("/")
            og_image = f"{SITE_URL}/{og_path}"

    html = build_html(
        title=title,
        description=description,
        author=author,
        og_image=og_image,
        date_text=date_text,
        site_css=site_css,
        home_href=home_href,
        content=content,
    )
    args.output.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
