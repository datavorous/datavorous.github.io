#!/usr/bin/env python3
"""Convert site HTML pages back into Markdown."""

from __future__ import annotations

import argparse
import os
import re
import shutil
from dataclasses import dataclass, field
from html import escape
from html.parser import HTMLParser
from pathlib import Path


VOID_TAGS = {"br", "hr", "img", "meta", "link", "input"}
SKIP_TAGS = {"script", "style"}
SOURCE_DIR = Path()
DESTINATION_DIR = Path()
PROJECT_ROOT = Path()


@dataclass
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list["Node | str"] = field(default_factory=list)

    def has_class(self, name: str) -> bool:
        return name in self.attrs.get("class", "").split()


class TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return

        node = Node(tag, {key: value or "" for key, value in attrs})
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth or tag in VOID_TAGS:
            return

        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.stack[-1].children.append(data)


def parse_html(path: Path) -> Node:
    parser = TreeBuilder()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser.root


def find_first(node: Node, predicate) -> Node | None:
    if predicate(node):
        return node
    for child in node.children:
        if isinstance(child, Node):
            found = find_first(child, predicate)
            if found:
                return found
    return None


def find_all(node: Node, predicate) -> list[Node]:
    found = [node] if predicate(node) else []
    for child in node.children:
        if isinstance(child, Node):
            found.extend(find_all(child, predicate))
    return found


def text_content(node: Node) -> str:
    parts: list[str] = []
    for child in node.children:
        if isinstance(child, str):
            parts.append(child)
        else:
            parts.append(text_content(child))
    return clean_text("".join(parts))


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def raw_text_content(node: Node) -> str:
    parts: list[str] = []
    for child in node.children:
        if isinstance(child, str):
            parts.append(child)
        else:
            parts.append(raw_text_content(child))
    return "".join(parts).strip("\n")


def markdown_text(text: str) -> str:
    return text.replace("\\", "\\\\")


def markdown_url(url: str, copy_asset: bool = False) -> str:
    url = rewrite_url(url, copy_asset)
    if re.search(r"[\s()]", url):
        return f"<{url}>"
    return url


def rewrite_url(url: str, copy_asset: bool = False) -> str:
    if (
        not url
        or url.startswith("#")
        or url.startswith("/")
        or re.match(r"^[a-z][a-z0-9+.-]*:", url)
        or not SOURCE_DIR
        or not DESTINATION_DIR
    ):
        return url

    first_part = Path(url).parts[0] if Path(url).parts else ""
    if first_part in {"img", "images"} and (SOURCE_DIR / first_part).is_dir():
        return url

    target = (SOURCE_DIR / url).resolve()
    if copy_asset:
        copied = copy_linked_asset(target)
        if copied:
            return copied
    return Path(os.path.relpath(target, DESTINATION_DIR)).as_posix()


def copy_linked_asset(target: Path) -> str:
    if not target.exists() and PROJECT_ROOT:
        matches = list(PROJECT_ROOT.rglob(target.name))
        if len(matches) == 1:
            target = matches[0]

    if not target.exists() or not target.is_file():
        return ""

    asset_dir = DESTINATION_DIR / "media"
    asset_dir.mkdir(parents=True, exist_ok=True)
    destination = asset_dir / target.name
    if target.resolve() != destination.resolve():
        shutil.copy2(target, destination)
    return (Path("media") / target.name).as_posix()


def inline(node: Node | str) -> str:
    if isinstance(node, str):
        return markdown_text(node)

    children = "".join(inline(child) for child in node.children)
    if node.tag == "code":
        return f"`{text_content(node).replace('`', '\\`')}`"
    if node.tag in {"em", "i"}:
        return f"*{children}*"
    if node.tag in {"strong", "b"}:
        return f"**{children}**"
    if node.tag == "s":
        return f"~~{children}~~"
    if node.tag == "a":
        href = node.attrs.get("href", "")
        return f"[{children}]({markdown_url(href)})" if href else children
    if node.tag == "br":
        return "\n"
    if node.tag == "img":
        src = node.attrs.get("src", "")
        alt = node.attrs.get("alt", "")
        return f"![{alt}]({markdown_url(src, copy_asset=True)})" if src else ""
    return children


def normalize_inline(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r" +([,.;:?!)])", r"\1", text)
    text = re.sub(r"([(]) +", r"\1", text)
    return text.strip()


def is_block(node: Node) -> bool:
    return node.tag in {
        "blockquote",
        "div",
        "figure",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "ol",
        "p",
        "pre",
        "table",
        "ul",
    }


def render_blocks(children: list[Node | str], level: int = 0) -> list[str]:
    blocks: list[str] = []
    for child in children:
        if isinstance(child, str):
            continue

        tag = child.tag
        if tag in {"nav", "footer"}:
            continue
        if tag in {"p", "figcaption"}:
            text = normalize_inline("".join(inline(item) for item in child.children))
            if text:
                blocks.append(text)
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            depth = int(tag[1])
            text = normalize_inline("".join(inline(item) for item in child.children))
            blocks.append(f"{'#' * depth} {text}")
        elif tag in {"ul", "ol"}:
            blocks.extend(render_list(child, ordered=tag == "ol"))
        elif tag == "pre":
            code = raw_text_content(child)
            blocks.append(f"```\n{code}\n```")
        elif tag == "blockquote":
            quote = render_blocks(child.children)
            blocks.append("\n".join(f"> {line}" if line else ">" for line in "\n\n".join(quote).splitlines()))
        elif tag == "figure":
            blocks.extend(render_figure(child))
        elif tag == "hr":
            blocks.append("---")
        elif tag == "img":
            rendered = inline(child)
            if rendered:
                blocks.append(rendered)
        elif tag == "table":
            rendered = render_table(child)
            if rendered:
                blocks.append(rendered)
        else:
            blocks.extend(render_blocks(child.children, level))
    return blocks


def render_list(node: Node, ordered: bool) -> list[str]:
    lines: list[str] = []
    items = [child for child in node.children if isinstance(child, Node) and child.tag == "li"]
    for index, item in enumerate(items, start=1):
        marker = f"{index}." if ordered else "-"
        blocks = render_list_item(item)
        if not blocks:
            continue
        first, *rest = "\n\n".join(blocks).splitlines()
        lines.append(f"{marker} {first}")
        lines.extend(f"   {line}" if line else "" for line in rest)
    return ["\n".join(lines)] if lines else []


def render_list_item(item: Node) -> list[str]:
    blocks: list[str] = []
    inline_parts: list[str] = []

    def flush_inline() -> None:
        text = normalize_inline("".join(inline_parts))
        if text:
            blocks.append(text)
        inline_parts.clear()

    for child in item.children:
        if isinstance(child, str):
            inline_parts.append(child)
        elif is_block(child):
            flush_inline()
            blocks.extend(render_blocks([child]))
        else:
            inline_parts.append(inline(child))

    flush_inline()
    return blocks


def render_figure(node: Node) -> list[str]:
    image = find_first(node, lambda item: item.tag == "img")
    if not image:
        return render_blocks(node.children)

    src = image.attrs.get("src", "")
    alt = image.attrs.get("alt", "")
    blocks = [f"![{alt}]({markdown_url(src, copy_asset=True)})"]
    caption = find_first(node, lambda item: item.tag == "figcaption")
    if caption:
        blocks.append(f"*{normalize_inline(''.join(inline(item) for item in caption.children))}*")
    return blocks


def render_table(node: Node) -> str:
    rows = find_all(node, lambda item: item.tag == "tr")
    rendered_rows: list[list[str]] = []
    for row in rows:
        cells = [child for child in row.children if isinstance(child, Node) and child.tag in {"th", "td"}]
        if cells:
            rendered_rows.append([normalize_inline("".join(inline(item) for item in cell.children)) for cell in cells])

    if not rendered_rows:
        return ""

    width = max(len(row) for row in rendered_rows)
    rendered_rows = [row + [""] * (width - len(row)) for row in rendered_rows]
    header, *body = rendered_rows
    separator = ["---"] * width
    lines = [markdown_table_row(header), markdown_table_row(separator)]
    lines.extend(markdown_table_row(row) for row in body)
    return "\n".join(lines)


def markdown_table_row(cells: list[str]) -> str:
    escaped = [cell.replace("|", "\\|") for cell in cells]
    return "| " + " | ".join(escaped) + " |"


def front_matter(root: Node, source: Path, project_root: Path) -> str:
    title = (
        find_first(root, lambda node: node.has_class("post-title"))
        or find_first(root, lambda node: node.tag == "article" and find_first(node, lambda item: item.tag == "h1"))
        or find_first(root, lambda node: node.tag == "title")
    )
    if title and title.tag == "article":
        title = find_first(title, lambda node: node.tag == "h1")
    subtitle = find_first(root, lambda node: node.has_class("post-subtitle"))
    date = find_first(root, lambda node: node.has_class("post-meta")) or find_first(root, lambda node: node.has_class("meta"))

    fields = {
        "title": text_content(title) if title else source.parent.name,
        "subtitle": text_content(subtitle) if subtitle else "",
        "date": text_content(date) if date else "",
        "source": source.relative_to(project_root).as_posix() if source.is_relative_to(project_root) else source.as_posix(),
    }

    lines = ["---"]
    for key, value in fields.items():
        if value:
            lines.append(f"{key}: {escape(value, quote=False)}")
    lines.append("---")
    return "\n".join(lines)


def markdown_from_html(source: Path, destination: Path, project_root: Path) -> str:
    global SOURCE_DIR, DESTINATION_DIR, PROJECT_ROOT
    SOURCE_DIR = source.parent
    DESTINATION_DIR = destination.parent
    PROJECT_ROOT = project_root

    root = parse_html(source)
    article = find_first(root, lambda node: node.tag == "article")
    body = article or find_first(root, lambda node: node.tag == "main") or root
    children = body.children
    if article:
        children = [child for child in children if not (isinstance(child, Node) and child.tag == "header")]
    blocks = render_blocks(children)
    content = "\n\n".join(blocks).strip()
    return front_matter(root, source, project_root) + "\n\n" + content + "\n"


def destination_for(source: Path, output_root: Path, project_root: Path) -> Path:
    source = source.resolve()
    relative = source.relative_to(project_root) if source.is_relative_to(project_root) else Path(source.name)
    return output_root / relative.with_suffix(".md")


def copy_assets(source: Path, destination: Path) -> None:
    for asset_dir in ("img", "images"):
        source_dir = source.parent / asset_dir
        if source_dir.is_dir():
            target_dir = destination.parent / asset_dir
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.copytree(source_dir, target_dir)


def source_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(path.rglob("*.html")))
        else:
            files.append(path)
    return files


def convert(source: Path, destination: Path, project_root: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(markdown_from_html(source, destination, project_root), encoding="utf-8")
    copy_assets(source, destination)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert site HTML pages into Markdown.")
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path("md"))
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    output_root = args.output.resolve()
    for source in source_files(args.sources):
        destination = destination_for(source, output_root, project_root)
        convert(source.resolve(), destination, project_root)
        print(f"{source} -> {destination}")


if __name__ == "__main__":
    main()
