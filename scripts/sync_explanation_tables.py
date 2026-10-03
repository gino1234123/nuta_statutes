#!/usr/bin/env python3
"""批次建立、同步或重建 Typst 逐條說明表。"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TABLE_SUFFIX = "逐條說明表.typ"
COMPARE_SUFFIX = "修法對照表.typ"


@dataclass(frozen=True)
class TableParts:
    before_table: str
    table_prefix: str
    body_prefix: str
    body_suffix: str
    after_table: str
    rows: list[tuple[str, str]]


def read_utf8(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_utf8(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def find_balanced_end(text: str, open_index: int) -> int:
    """找出括號區塊結尾，支援混合巢狀括號及字串。"""

    pairs = {"[": "]", "(": ")", "{": "}"}
    opening = text[open_index]
    if opening not in pairs:
        raise ValueError(f"索引 {open_index} 不是開括號。")

    stack = [opening]
    i = open_index + 1
    while i < len(text):
        ch = text[i]

        if ch in ('"', "'"):
            quote = ch
            i += 1
            while i < len(text):
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == quote:
                    i += 1
                    break
                i += 1
            continue

        if text.startswith("//", i):
            newline = text.find("\n", i + 2)
            i = len(text) if newline < 0 else newline + 1
            continue
        if text.startswith("/*", i):
            comment_end = text.find("*/", i + 2)
            if comment_end < 0:
                raise ValueError(f"索引 {open_index} 的括號區塊包含未閉合註解。")
            i = comment_end + 2
            continue

        if ch in pairs:
            stack.append(ch)
        elif ch in pairs.values():
            if not stack or pairs[stack[-1]] != ch:
                raise ValueError(f"索引 {open_index} 的括號區塊有不相符的括號。")
            stack.pop()
            if not stack:
                return i
        i += 1

    raise ValueError(f"索引 {open_index} 的括號區塊未閉合。")


def get_article_blocks(text: str) -> list[str]:
    """依原始順序取出 #article[...] 及 #article()[...] 區塊。"""

    blocks: list[str] = []
    needle = "#article"
    search_at = 0
    while True:
        article_at = text.find(needle, search_at)
        if article_at < 0:
            return blocks

        after_name = article_at + len(needle)
        if after_name < len(text) and (text[after_name].isalnum() or text[after_name] in "_-"):
            search_at = after_name
            continue

        cursor = after_name
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor < len(text) and text[cursor] == "(":
            cursor = find_balanced_end(text, cursor) + 1
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1

        if cursor >= len(text) or text[cursor] != "[":
            search_at = after_name
            continue

        close = find_balanced_end(text, cursor)
        blocks.append(text[article_at : close + 1])
        search_at = close + 1


def parse_top_level_cells(text: str, start: int, end: int) -> list[tuple[int, int, str]]:
    cells: list[tuple[int, int, str]] = []
    i = start
    while i < end:
        if text[i] in ('"', "'"):
            quote = text[i]
            i += 1
            while i < end:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        if text.startswith("//", i):
            newline = text.find("\n", i + 2, end)
            i = end if newline < 0 else newline + 1
            continue
        if text.startswith("/*", i):
            comment_end = text.find("*/", i + 2, end)
            if comment_end < 0:
                raise ValueError("#table 的內容包含未閉合註解。")
            i = comment_end + 2
            continue
        if text[i] == "[":
            close = find_balanced_end(text, i)
            if close >= end:
                raise ValueError("#table 的儲存格超出表格範圍。")
            cells.append((i, close + 1, text[i + 1 : close]))
            i = close + 1
            continue
        i += 1
    return cells


def parse_table(table_text: str) -> TableParts:
    table_start = table_text.find("#table(")
    if table_start < 0:
        raise ValueError("找不到 #table(...)。")

    paren_open = table_start + len("#table")
    paren_close = find_balanced_end(table_text, paren_open)
    header_start = table_text.find("table.header(", paren_open + 1, paren_close)
    if header_start < 0:
        raise ValueError("#table(...) 中找不到 table.header(...)。")

    header_open = header_start + len("table.header")
    header_close = find_balanced_end(table_text, header_open)
    if header_close > paren_close:
        raise ValueError("table.header(...) 超出 #table(...) 範圍。")

    body_start = header_close + 1
    cells = parse_top_level_cells(table_text, body_start, paren_close)
    if len(cells) % 2 != 0:
        raise ValueError(f"表格儲存格數量不是偶數：{len(cells)}。")

    if cells:
        first_cell = cells[0][0]
        last_cell_end = cells[-1][1]
        body_prefix = table_text[body_start:first_cell]
        body_suffix = table_text[last_cell_end:paren_close]
        # 每列由 make_row() 自行加上結尾逗號；移除舊末列留下的分隔逗號，
        # 避免重建既有表格時產生連續的 `,,`。
        first_content = len(body_suffix) - len(body_suffix.lstrip())
        if first_content < len(body_suffix) and body_suffix[first_content] == ",":
            body_suffix = body_suffix[:first_content] + body_suffix[first_content + 1 :]
    else:
        body_prefix = table_text[body_start:paren_close]
        body_suffix = ""

    rows = [(cells[i][2], cells[i + 1][2]) for i in range(0, len(cells), 2)]
    return TableParts(
        before_table=table_text[:table_start],
        table_prefix=table_text[table_start : header_close + 1],
        body_prefix=body_prefix,
        body_suffix=body_suffix,
        after_table=table_text[paren_close + 1 :],
        rows=rows,
    )


def article_from_first_cell(cell: str) -> str:
    articles = get_article_blocks(cell)
    if len(articles) != 1:
        raise ValueError("表格第一欄每個儲存格必須恰好包含一個 #article 區塊。")
    return articles[0].strip()


def make_row(article: str, explanation: str) -> str:
    return f"\n\n    [{article.strip()}], [{explanation}],"


def build_table(parts: TableParts, rows: list[tuple[str, str]]) -> str:
    body = "".join(make_row(article, explanation) for article, explanation in rows)
    return (
        parts.before_table
        + parts.table_prefix
        + parts.body_prefix
        + body
        + parts.body_suffix
        + ")"
        + parts.after_table
    )


def align_rows(
    existing_rows: list[tuple[str, str]], source_articles: list[str]
) -> list[tuple[str, str]]:
    """將既有列視為有順序的條文序列，允許新增及刪除，但拒絕重排。"""

    old_articles = [article_from_first_cell(cell) for cell, _ in existing_rows]
    source = [article.strip() for article in source_articles]
    synced: list[tuple[str, str]] = []
    source_at = 0

    for old_at, old_article in enumerate(old_articles):
        try:
            match_at = source.index(old_article, source_at)
        except ValueError:
            if old_article in source[:source_at]:
                raise ValueError(
                    f"既有第 {old_at + 1} 列的條文出現在已對齊條文之前，無法依順序對齊。"
                )
            # 這列已從來源刪除，不加入新表。
            continue

        while source_at < match_at:
            synced.append((source_articles[source_at], ""))
            source_at += 1
        synced.append((source_articles[match_at], existing_rows[old_at][1]))
        source_at = match_at + 1

    while source_at < len(source_articles):
        synced.append((source_articles[source_at], ""))
        source_at += 1
    return synced


def sync_table(table_text: str, source_articles: list[str]) -> str:
    parts = parse_table(table_text)
    rows = align_rows(parts.rows, source_articles)
    return build_table(parts, rows)


def rebuild_table(table_text: str, source_articles: list[str]) -> str:
    parts = parse_table(table_text)
    return build_table(parts, [(article, "") for article in source_articles])


def verify_table(result: str, source_articles: list[str], expect_empty_explanations: bool) -> None:
    parts = parse_table(result)
    if len(parts.rows) != len(source_articles):
        raise ValueError(f"驗證列數不符：預期 {len(source_articles)} 列，實際 {len(parts.rows)} 列。")

    for index, ((cell, explanation), source_article) in enumerate(
        zip(parts.rows, source_articles), start=1
    ):
        if article_from_first_cell(cell) != source_article.strip():
            raise ValueError(f"驗證第一欄條文不符（第 {index} 列）。")
        if expect_empty_explanations and explanation.strip():
            raise ValueError(f"驗證說明欄非空白（第 {index} 列）。")


def first_level_title(source_text: str, source_path: Path) -> str:
    match = re.search(r"(?m)^=\s+(.+?)\s*$", source_text)
    return (match.group(1).strip() if match else source_path.stem) + TABLE_SUFFIX.removesuffix(".typ")


def new_table_text(root: Path, source_path: Path, source_text: str, articles: list[str]) -> str:
    target_dir = source_path.parent
    style_path = root / "style.typ"
    relative_style = Path(os.path.relpath(style_path, target_dir)).as_posix()
    title = first_level_title(source_text, source_path)
    rows = "".join(make_row(article, "") for article in articles)
    return (
        f'#import "{relative_style}": *\n'
        "#show: statute-style\n\n"
        f"= {title}\n"
        "#table(\n"
        "  columns: (1fr, 1fr),\n"
        "  table.header(\n"
        "    repeat: true,\n"
        "    align(center)[新條文], align(center)[說明],\n"
        "  ),"
        f"{rows}\n"
        ")\n"
    )


def is_explanation_table(path: Path) -> bool:
    return path.name.endswith(TABLE_SUFFIX) or path.name.endswith(COMPARE_SUFFIX)


def scan_sources(root: Path, recursive: bool) -> list[Path]:
    excluded_dirs = {"scripts", "complied_pdf", "待處理"}
    folders = sorted(
        (path for path in root.iterdir() if path.is_dir() and path.name not in excluded_dirs),
        key=lambda path: path.name,
    )
    sources: list[Path] = []
    for folder in folders:
        if recursive or folder.name == "條例":
            candidates = folder.rglob("*.typ")
        else:
            candidates = folder.glob("*.typ")
        sources.extend(
            path
            for path in candidates
            if path.is_file() and not is_explanation_table(path)
        )
    return sorted(sources, key=lambda path: path.relative_to(root).as_posix())


def target_for(source: Path) -> Path:
    return source.with_name(f"{source.stem}{TABLE_SUFFIX}")


def process_source(root: Path, source: Path, mode: str, dry_run: bool) -> tuple[str, Path, str]:
    source_text = read_utf8(source)
    articles = get_article_blocks(source_text)
    target = target_for(source)
    if not articles:
        return "略過", target, "找不到 #article[...] 或 #article()[...]"

    if target.exists():
        old_text = read_utf8(target)
        result = sync_table(old_text, articles) if mode == "sync" else rebuild_table(old_text, articles)
        verify_table(result, articles, expect_empty_explanations=mode == "rebuild")
        status = "略過" if result == old_text else "將更新" if dry_run else "更新"
        if result != old_text and not dry_run:
            write_utf8(target, result)
        return status, target, f"{len(articles)} 列，已完成記憶體驗證"

    result = new_table_text(root, source, source_text, articles)
    verify_table(result, articles, expect_empty_explanations=True)
    if not dry_run:
        write_utf8(target, result)
    return ("將建立" if dry_run else "建立"), target, f"{len(articles)} 列，已完成記憶體驗證"


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="批次建立、同步或重建兩欄逐條說明表（使用繁體中文輸出）。"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=PROJECT_ROOT,
        metavar="PATH",
        help="專案根目錄（預設為本腳本上一層的專案根目錄）。",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        "-Recursive",
        action="store_true",
        help="遞迴掃描所有來源資料夾；預設僅遞迴資料夾名為「條例」者。",
    )
    parser.add_argument(
        "--mode",
        choices=("sync", "rebuild"),
        default="sync",
        help="sync 保留對齊的說明；rebuild 依來源重建並清空說明（預設 sync）。",
    )
    parser.add_argument("--dry-run", action="store_true", help="只解析、產生及驗證，不寫入檔案。")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    root = args.root.expanduser()
    if not root.is_absolute():
        root = (Path.cwd() / root).resolve()
    else:
        root = root.resolve()
    if not root.is_dir():
        print(f"失敗：根目錄不存在或不是資料夾：{root}", file=sys.stderr)
        return 1

    try:
        sources = scan_sources(root, args.recursive)
    except OSError as error:
        print(f"失敗：掃描根目錄時發生錯誤：{error}", file=sys.stderr)
        return 1

    print(f"根目錄：{root}")
    print(f"模式：{args.mode}；{'試跑，不寫入檔案' if args.dry_run else '將寫入檔案'}")
    print(f"掃描到 {len(sources)} 個候選來源檔案。")

    counts = {"建立": 0, "將建立": 0, "更新": 0, "將更新": 0, "略過": 0, "失敗": 0}
    failures = 0
    for source in sources:
        try:
            status, target, detail = process_source(root, source, args.mode, args.dry_run)
            counts[status] += 1
            relative_source = source.relative_to(root).as_posix()
            if status == "略過" and not target.exists():
                print(f"[略過] {relative_source}：{detail}")
            else:
                relative_target = target.relative_to(root).as_posix()
                print(f"[{status}] {relative_source} -> {relative_target}（{detail}）")
        except (OSError, ValueError) as error:
            failures += 1
            counts["失敗"] += 1
            print(f"[失敗] {source.relative_to(root).as_posix()}：{error}", file=sys.stderr)

    print(
        "總結："
        f"建立 {counts['建立'] + counts['將建立']}，"
        f"更新 {counts['更新'] + counts['將更新']}，"
        f"略過 {counts['略過']}，失敗 {failures}。"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
