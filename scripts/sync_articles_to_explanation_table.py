from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class TableParts:
    before_table: str
    table_prefix: str
    after_table: str
    rows: list[tuple[str, str]]


def normalize_path_input(raw: str) -> str:
    s = raw.strip()
    if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
        s = s[1:-1].strip()
    return s


def resolve_user_path(path_value: str) -> Path:
    p = Path(path_value)
    if p.is_absolute():
        return p
    return (PROJECT_ROOT / p).resolve()


def find_balanced_end(text: str, open_index: int, open_ch: str, close_ch: str) -> int:
    if text[open_index] != open_ch:
        raise ValueError(f"Expected '{open_ch}' at index {open_index}.")

    depth = 0
    i = open_index
    while i < len(text):
        ch = text[i]
        if ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return i
        i += 1

    raise ValueError(f"Unclosed '{open_ch}{close_ch}' block starting at {open_index}.")


def get_article_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    needle = "#article"
    i = 0
    while True:
        idx = text.find(needle, i)
        if idx < 0:
            break

        p = idx + len(needle)
        while p < len(text) and text[p].isspace():
            p += 1

        if p < len(text) and text[p] == "(":
            p = find_balanced_end(text, p, "(", ")") + 1
            while p < len(text) and text[p].isspace():
                p += 1

        if p >= len(text) or text[p] != "[":
            i = idx + len(needle)
            continue

        bracket_close = find_balanced_end(text, p, "[", "]")
        blocks.append(text[idx : bracket_close + 1])
        i = bracket_close + 1

    return blocks


def parse_top_level_cells(text: str, absolute_offset: int = 0) -> list[tuple[int, int, str]]:
    cells: list[tuple[int, int, str]] = []
    i = 0
    while i < len(text):
        if text[i] != "[":
            i += 1
            continue

        close = find_balanced_end(text, i, "[", "]")
        cells.append((absolute_offset + i, absolute_offset + close + 1, text[i + 1 : close]))
        i = close + 1

    return cells


def parse_table(table_text: str) -> TableParts:
    table_start = table_text.find("#table(")
    if table_start < 0:
        raise ValueError("Could not find '#table(' in table file.")

    paren_open = table_start + len("#table")
    paren_close = find_balanced_end(table_text, paren_open, "(", ")")
    table_inner = table_text[paren_open + 1 : paren_close]

    header_start_rel = table_inner.find("table.header(")
    if header_start_rel < 0:
        raise ValueError("Could not find 'table.header(' inside #table(...).")

    header_start = paren_open + 1 + header_start_rel
    header_paren_open = header_start + len("table.header")
    header_paren_close = find_balanced_end(table_text, header_paren_open, "(", ")")

    body_start = header_paren_close + 1
    if body_start < paren_close and table_text[body_start] == ",":
        body_start += 1

    body_text = table_text[body_start:paren_close]
    cells = parse_top_level_cells(body_text, body_start)
    if len(cells) % 2 != 0:
        raise ValueError(f"Expected an even number of body cells, got {len(cells)}.")

    rows = [(cells[i][2], cells[i + 1][2]) for i in range(0, len(cells), 2)]

    return TableParts(
        before_table=table_text[:table_start],
        table_prefix=table_text[table_start : header_paren_close + 1],
        after_table=table_text[paren_close + 1 :],
        rows=rows,
    )


def make_row(article: str, explanation: str) -> str:
    return f"\n\n    [{article}], [{explanation}],"


def article_from_first_cell(cell: str) -> str:
    articles = get_article_blocks(cell)
    if len(articles) != 1:
        raise ValueError("Each first-column body cell must contain exactly one #article block.")
    return articles[0].strip()


def build_table(parts: TableParts, rows: list[tuple[str, str]]) -> str:
    body = "".join(make_row(article, explanation) for article, explanation in rows)
    return parts.before_table + parts.table_prefix + "," + body + "\n)" + parts.after_table


def rebuild_table(table_text: str, article_blocks: list[str]) -> tuple[str, int, int]:
    parts = parse_table(table_text)
    rows = [(article, "") for article in article_blocks]
    return build_table(parts, rows), 0, len(rows)


def sync_table(table_text: str, article_blocks: list[str]) -> tuple[str, int, int]:
    parts = parse_table(table_text)
    existing_rows = [(article_from_first_cell(article_cell), explanation) for article_cell, explanation in parts.rows]

    synced_rows: list[tuple[str, str]] = []
    kept_explanations = 0
    inserted_blank_explanations = 0
    source_idx = 0
    row_idx = 0

    while source_idx < len(article_blocks):
        source_article = article_blocks[source_idx].strip()

        if row_idx < len(existing_rows) and existing_rows[row_idx][0] == source_article:
            explanation = existing_rows[row_idx][1]
            if explanation.strip():
                kept_explanations += 1
            synced_rows.append((article_blocks[source_idx], explanation))
            source_idx += 1
            row_idx += 1
            continue

        synced_rows.append((article_blocks[source_idx], ""))
        inserted_blank_explanations += 1
        source_idx += 1

    if row_idx != len(existing_rows):
        remaining = len(existing_rows) - row_idx
        raise ValueError(
            "Table contains unexpected first-column #article rows that cannot align "
            f"with source order. Remaining table rows: {remaining}."
        )

    return build_table(parts, synced_rows), kept_explanations, inserted_blank_explanations


def verify_table(result: str, article_blocks: list[str], expect_empty_explanations: bool) -> None:
    parts = parse_table(result)
    if len(parts.rows) != len(article_blocks):
        raise ValueError(
            f"Final row count mismatch. expected={len(article_blocks)}, got={len(parts.rows)}"
        )

    for i, ((article_cell, explanation), source_article) in enumerate(zip(parts.rows, article_blocks), start=1):
        article = article_from_first_cell(article_cell)
        if article != source_article.strip():
            raise ValueError(f"Mismatch at article index {i}.")
        if expect_empty_explanations and explanation.strip():
            raise ValueError(f"Expected empty explanation at article index {i}.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Sync or rebuild an explanation table from all #article blocks in a Typst source file."
        )
    )
    parser.add_argument(
        "--source",
        default="00_組織章程/章程草案.typ",
        help="Source .typ file to read all #article blocks from.",
    )
    parser.add_argument(
        "--table",
        default="00_組織章程/章程逐條說明表.typ",
        help="Target explanation table .typ file.",
    )
    parser.add_argument(
        "--mode",
        choices=("sync", "rebuild"),
        default="sync",
        help="sync preserves aligned explanations; rebuild clears all explanations.",
    )
    args = parser.parse_args()

    source_path = resolve_user_path(normalize_path_input(args.source))
    table_path = resolve_user_path(normalize_path_input(args.table))

    source_text = source_path.read_text(encoding="utf-8")
    table_text = table_path.read_text(encoding="utf-8")

    article_blocks = get_article_blocks(source_text)
    if not article_blocks:
        raise ValueError(f"No #article blocks found in source file: {source_path}")

    if args.mode == "sync":
        result, kept_explanations, inserted_blank_explanations = sync_table(table_text, article_blocks)
        verify_table(result, article_blocks, expect_empty_explanations=False)
    else:
        result, kept_explanations, inserted_blank_explanations = rebuild_table(table_text, article_blocks)
        verify_table(result, article_blocks, expect_empty_explanations=True)

    table_path.write_text(result, encoding="utf-8")

    print(f"Updated: {table_path}")
    print(f"Mode: {args.mode}")
    print(f"Articles: {len(article_blocks)}")
    print(f"Kept explanations: {kept_explanations}")
    print(f"Inserted blank explanations: {inserted_blank_explanations}")
    print("Verification: PASS")


if __name__ == "__main__":
    main()
