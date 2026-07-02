# AGENTS.md — ntua_statutes

## Build / Compile

- PDFs are generated from `.typ` files via `scripts/compile_typst_pdfs.ps1` (PowerShell).
- Requires `typst` CLI in PATH.
- All PDFs output flat to `complied_pdf/` (auto-created if missing). Old `.pdf` alongside `.typ` in subdirs are stale.
- Usage: `.\scripts\compile_typst_pdfs.ps1 [-Clean] [-Recursive]`
  - `-Clean`: delete existing PDFs before recompiling.
  - `-Recursive`: recurse into subdirs for `.typ` files.
- The script passes `--root <project-root>` to `typst compile` so `#import "../style.typ"` resolves correctly.
- The script excludes `scripts/` and `complied_pdf/` from folder enumeration.

## Project Structure

```
00_組織章程/    章程草案.typ      — 組織章程 draft
01_法規標準法/  法規標準法.typ
02_學生議會職權行使法/  學生議會職權行使法.typ
03_選舉罷免法/  選舉罷免法.typ
04_財務管理法/  財務管理法.typ
style.typ                    — shared Typst stylesheet (imported via `#import "../style.typ": *`)
章程修法對照表.typ           — comparison table (draft vs current law)
scripts/
  compile_typst_pdfs.ps1     — PDF compilation
  sync_articles_to_table.py  — sync #article blocks from draft into comparison table column 1
  rebuild_compare_table_from_articles.py — rebuild entire comparison table from #article blocks
complied_pdf/                — flat output directory for all compiled PDFs
```

## Typst Conventions

- Shared style in `style.typ`: `#let statute-style(body)`, auto-numbered `#article()`, `#para()`, `#subpara()`, `#item()`.
- All law docs use: `#import "../style.typ": *` then `#show: statute-style`.
- `#article(body)` auto-numbers in CJK (第X條). `#article()` without arguments uses implied body.
- Comparison table (`章程修法對照表.typ`) is a standalone file (does NOT import style.typ) — 3-column table with `#article[...]` in column 1.

## Python Scripts

- `sync_articles_to_table.py`: reads `#article[...]` blocks from a draft `.typ`, syncs them into column 1 of a comparison table `.typ`. Default: `--draft 00_組織章程/章程草案.typ --table 00_組織章程/章程修法對照表.typ`. Runs verification after write.
- `rebuild_compare_table_from_articles.py`: rebuilds entire comparison table rows from `#article[...]` blocks, leaving columns 2-3 empty. Interactive if `--source`/`--table` not provided.
- Both write UTF-8 without BOM.

## Misc

- No test framework, no CI, no linter, no formatter config.
- No `.gitignore`.
- All text in Traditional Chinese (zh-TW).
