from __future__ import annotations

import argparse
from pathlib import Path


def get_spans(text: str, needle: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    i = 0
    while True:
        idx = text.find(needle, i)
        if idx < 0:
            break
        depth = 0
        k = idx
        while k < len(text):
            ch = text[k]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    k += 1
                    break
            k += 1
        if depth != 0:
            raise ValueError(f"Unclosed bracket span at index {idx} for needle {needle!r}.")
        spans.append((idx, k))
        i = k
    return spans


def get_article_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
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
            # Skip optional () arguments.
            depth = 0
            q = p
            while q < len(text):
                ch = text[q]
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        q += 1
                        break
                q += 1
            if depth != 0:
                raise ValueError(f"Unclosed parentheses for #article at index {idx}.")
            p = q
            while p < len(text) and text[p].isspace():
                p += 1
        if p >= len(text) or text[p] != "[":
            i = idx + len(needle)
            continue
        start = idx
        depth = 0
        k = p
        while k < len(text):
            ch = text[k]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    k += 1
                    break
            k += 1
        if depth != 0:
            raise ValueError(f"Unclosed bracket span for #article at index {idx}.")
        spans.append((start, k))
        i = k
    return spans


def read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_utf8_no_bom(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync #article blocks from draft typst file into first column of the comparison table."
    )
    parser.add_argument(
        "--draft",
        default="00_組織章程/章程草案.typ",
        help="Path to draft typst file.",
    )
    parser.add_argument(
        "--table",
        default="00_組織章程/章程修法對照表.typ",
        help="Path to comparison table typst file.",
    )
    args = parser.parse_args()

    draft_path = Path(args.draft)
    table_path = Path(args.table)

    draft = read_utf8(draft_path)
    table = read_utf8(table_path)

    draft_spans = get_article_spans(draft)
    draft_articles = [draft[a:b] for a, b in draft_spans]

    table_spans = get_spans(table, "[#article[")

    table_articles = []
    for start, end in table_spans:
        cell = table[start:end]
        table_articles.append(cell[1:-1])  # remove outer [ ]

    # Sequential alignment:
    # 1) map each existing first-column row to the corresponding draft article index
    # 2) detect missing draft rows and where to insert them
    mapping: list[int] = []
    missing_to_insert: list[tuple[int, int]] = []  # (insert_before_table_row_idx, draft_idx)
    i = 0  # draft index
    j = 0  # table first-column row index
    while j < len(table_articles) and i < len(draft_articles):
        if table_articles[j] == draft_articles[i]:
            mapping.append(i)
            i += 1
            j += 1
        else:
            missing_to_insert.append((j, i))
            i += 1

    while i < len(draft_articles):
        missing_to_insert.append((j, i))
        i += 1

    if j != len(table_articles):
        raise ValueError(
            "Table contains unexpected first-column #article rows that cannot align "
            f"with draft order. Remaining table rows: {len(table_articles) - j}."
        )

    # Build edit list and apply from right to left so offsets stay stable.
    edits: list[tuple[int, int, str]] = []

    # Replace existing first-column rows with draft rows by aligned index.
    for row_idx, draft_idx in enumerate(mapping):
        start, end = table_spans[row_idx]
        replacement = "[" + draft_articles[draft_idx] + "]"
        edits.append((start, end, replacement))

    # Insert missing rows at detected positions.
    for insert_before_row_idx, draft_idx in missing_to_insert:
        if insert_before_row_idx < len(table_spans):
            pos = table_spans[insert_before_row_idx][0]
        else:
            # Append before final ')' of #table(...)
            pos = table.rfind("\n)")
            if pos < 0:
                raise ValueError("Could not find table closing parenthesis for append insertion.")

        row = (
            "\n\n["
            + draft_articles[draft_idx]
            + "], [無對應條文], [待補條文說明],\n"
        )
        edits.append((pos, pos, row))

    result = table
    for start, end, replacement in sorted(edits, key=lambda x: x[0], reverse=True):
        result = result[:start] + replacement + result[end:]

    # Remove BOM if present.
    result = result.lstrip("\ufeff")

    # Final verification: first-column cells == draft articles and content matches.
    final_spans = get_spans(result, "[#article[")
    if len(final_spans) != len(draft_articles):
        raise ValueError(
            "Final first-column article cell count mismatch. "
            f"expected={len(draft_articles)}, got={len(final_spans)}"
        )

    for i, (start, end) in enumerate(final_spans):
        cell = result[start:end]
        article_text = cell[1:-1]  # remove outer [ ]
        if article_text != draft_articles[i]:
            raise ValueError(f"Mismatch at article index {i + 1}.")

    write_utf8_no_bom(table_path, result)

    print(f"Updated: {table_path}")
    print(f"Draft articles: {len(draft_articles)}")
    print(f"First-column article cells: {len(final_spans)}")
    print(f"Inserted missing rows: {len(missing_to_insert)}")
    print("Verification: PASS")


if __name__ == "__main__":
    main()
