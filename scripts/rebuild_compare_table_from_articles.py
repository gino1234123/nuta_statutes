from __future__ import annotations

import argparse
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


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
        p = idx + len("#article")
        while p < len(text) and text[p].isspace():
            p += 1

        # Support both:
        #   #article[...]
        #   #article()[...]
        if p < len(text) and text[p] == "(":
            p = find_balanced_end(text, p, "(", ")") + 1
            while p < len(text) and text[p].isspace():
                p += 1

        if p >= len(text) or text[p] != "[":
            i = idx + len(needle)
            continue

        bracket_open = p
        bracket_close = find_balanced_end(text, bracket_open, "[", "]")
        blocks.append(text[idx : bracket_close + 1])
        i = bracket_close + 1
    return blocks


def rebuild_table(table_text: str, article_blocks: list[str]) -> str:
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

    # Keep everything in #table up to and including table.header(...)
    prefix = table_text[table_start : header_paren_close + 1]

    rows = []
    for block in article_blocks:
        rows.append(f"\n\n  [{block}], [], [],")

    new_table = prefix + "," + "".join(rows) + "\n)"
    # Rebuild from #table(...) to EOF to avoid carrying corrupted trailing remnants.
    return table_text[:table_start] + new_table + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild comparison table rows from all #article[...] blocks. "
            "Keeps table header row unchanged; puts article blocks in column 1 "
            "and leaves columns 2-3 empty."
        )
    )
    parser.add_argument(
        "--source",
        default=None,
        help="Source .typ file to read all #article[...] from.",
    )
    parser.add_argument(
        "--table",
        default=None,
        help="Target comparison table .typ file.",
    )
    parser.add_argument(
        "--template",
        default=str(PROJECT_ROOT / "00_組織章程/章程修法對照表.typ"),
        help="Template comparison table .typ file (used for table/header format).",
    )
    args = parser.parse_args()

    source_value = args.source
    if not source_value:
        source_value = input("請輸入來源 .typ 路徑（用來抓取 #article[...]）：")
    source_value = normalize_path_input(source_value)
    if not source_value:
        raise ValueError("來源 .typ 路徑不可為空。")

    source_path = resolve_user_path(source_value)

    table_value = args.table
    if not table_value:
        default_table = source_path.parent / "章程修法對照表.typ"
        table_input = input(
            f"請輸入輸出 .typ 路徑（直接 Enter 使用預設：{default_table}）："
        )
        table_value = normalize_path_input(table_input) or str(default_table)
    else:
        table_value = normalize_path_input(table_value)

    table_path = resolve_user_path(table_value)
    template_path = resolve_user_path(normalize_path_input(args.template))

    source_text = source_path.read_text(encoding="utf-8")
    table_text = template_path.read_text(encoding="utf-8")

    article_blocks = get_article_blocks(source_text)
    if not article_blocks:
        raise ValueError("No #article[...] blocks found in source file.")

    rebuilt = rebuild_table(table_text, article_blocks)
    rebuilt = rebuilt.lstrip("\ufeff")
    table_path.parent.mkdir(parents=True, exist_ok=True)
    table_path.write_text(rebuilt, encoding="utf-8", newline="")
    out_path = table_path.resolve()
    if not out_path.exists():
        raise RuntimeError(f"Output file was not created: {out_path}")

    print(f"Updated: {out_path}")
    print(f"Template used: {template_path.resolve()}")
    print(f"Articles written to first column: {len(article_blocks)}")
    print("Columns 2 and 3 are empty for all body rows.")


if __name__ == "__main__":
    main()
