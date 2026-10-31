#!/usr/bin/env python3
"""Small dependency-free Markdown to site HTML converter."""

from __future__ import annotations

import argparse
import html
import re
from datetime import datetime
from pathlib import Path


NAV = """  <nav class="top">
    <a href="/">Home</a>
    <a href="mailto:hi@datavorous.com">Email</a>
  </nav>"""


def parse_front_matter(markdown: str) -> tuple[dict[str, str], str]:
    if not markdown.startswith("---\n"):
        return {}, markdown

    end = markdown.find("\n---\n", 4)
    if end == -1:
        return {}, markdown

    fields: dict[str, str] = {}
    for line in markdown[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip().lower()] = value.strip()

    return fields, markdown[end + 5 :].lstrip("\n")


def format_date(value: str) -> str:
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%B %-d, %Y")
        except ValueError:
            pass
    return value


def inline_markdown(text: str) -> str:
    escaped = html.escape(text, quote=False)

    code_spans: list[str] = []

    def stash_code(match: re.Match[str]) -> str:
        code_spans.append(f"<code>{match.group(1)}</code>")
        return f"\u0000CODE{len(code_spans) - 1}\u0000"

    escaped = re.sub(r"`([^`]+)`", stash_code, escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"<em>\1</em>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", escaped)
    escaped = re.sub(r"~~([^~]+)~~", r"<s>\1</s>", escaped)

    for index, code in enumerate(code_spans):
        escaped = escaped.replace(f"\u0000CODE{index}\u0000", code)

    return escaped


def close_list(lines: list[str], in_list: bool) -> bool:
    if in_list:
        lines.append("</ul>")
    return False


def flush_paragraph(lines: list[str], paragraph: list[str]) -> None:
    if paragraph:
        text = " ".join(item.strip() for item in paragraph)
        lines.append(f"<p>{inline_markdown(text)}</p>")
        paragraph.clear()


def markdown_to_html(markdown: str) -> str:
    output: list[str] = []
    paragraph: list[str] = []
    blockquote: list[str] = []
    in_list = False
    in_code = False
    code_lines: list[str] = []

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            flush_paragraph(output, paragraph)
            in_list = close_list(output, in_list)
            if in_code:
                output.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(raw_line)
            continue

        if line.startswith(">"):
            flush_paragraph(output, paragraph)
            in_list = close_list(output, in_list)
            blockquote.append(line[1:].lstrip())
            continue

        if blockquote:
            output.append("<blockquote>")
            output.append(f"<p>{inline_markdown(' '.join(blockquote))}</p>")
            output.append("</blockquote>")
            blockquote.clear()

        if not line.strip():
            flush_paragraph(output, paragraph)
            in_list = close_list(output, in_list)
            continue

        if re.fullmatch(r"-{3,}", line.strip()):
            flush_paragraph(output, paragraph)
            in_list = close_list(output, in_list)
            output.append("<hr>")
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            flush_paragraph(output, paragraph)
            in_list = close_list(output, in_list)
            level = len(heading.group(1))
            output.append(f"<h{level}>{inline_markdown(heading.group(2))}</h{level}>")
            continue

        list_item = re.match(r"^[-*]\s+(.+)$", line)
        if list_item:
            flush_paragraph(output, paragraph)
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append(f"<li>{inline_markdown(list_item.group(1))}</li>")
            continue

        in_list = close_list(output, in_list)
        paragraph.append(line)

    if blockquote:
        output.append("<blockquote>")
        output.append(f"<p>{inline_markdown(' '.join(blockquote))}</p>")
        output.append("</blockquote>")

    flush_paragraph(output, paragraph)
    close_list(output, in_list)

    if in_code:
        output.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")

    return "\n\n".join(output)


def render_page(title: str, date: str, body: str, image: str = "") -> str:
    page_title = html.escape(f"{title} -- datavorous", quote=False)
    article_title = html.escape(title, quote=False)
    article_date = html.escape(date, quote=False)
    image_html = ""
    if image:
        image_src = html.escape(image, quote=True)
        image_alt = html.escape(title, quote=True)
        image_html = f"""
    <figure class="essay-hero">
      <img src="{image_src}" alt="{image_alt}">
    </figure>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page_title}</title>
<link rel="icon" type="image/x-icon" href="/media/favicon/favicon.ico">
<link rel="stylesheet" href="../index.css">
<script defer src="https://cloud.umami.is/script.js" data-website-id="e63babdf-cd85-4481-ba03-cebb2ac1e44b"></script>
</head>
<body>
<main>

{NAV}

  <article>
    <header>
      <h1>{article_title}</h1>
      <p class="meta">{article_date}</p>
    </header>
{image_html}
{indent_body(body)}
  </article>

</main>
</body>
</html>
"""


def indent_body(body: str) -> str:
    return "\n".join(f"    {line}" if line else line for line in body.splitlines())


def convert(source: Path, destination: Path) -> None:
    markdown = source.read_text(encoding="utf-8")
    front_matter, body_markdown = parse_front_matter(markdown)
    title = front_matter.get("title") or source.stem
    date = format_date(front_matter.get("date", ""))
    image = resolve_asset_path(front_matter.get("image", ""), destination)
    body_html = markdown_to_html(body_markdown)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_page(title, date, body_html, image), encoding="utf-8")


def resolve_asset_path(asset_path: str, destination: Path) -> str:
    if not asset_path or re.match(r"^[a-z]+://", asset_path) or asset_path.startswith("/"):
        return asset_path
    relative = Path(asset_path)
    output_dir = destination.parent
    return Path("../", relative).as_posix() if output_dir.name else relative.as_posix()


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Markdown into a datavorous essay HTML page.")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    convert(args.source, args.destination)


if __name__ == "__main__":
    main()
