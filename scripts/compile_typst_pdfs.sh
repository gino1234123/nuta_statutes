#!/usr/bin/env bash
set -u
set -o pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd -- "$script_dir/.." && pwd)"
recursive=false
clean=false

usage() {
  cat <<'EOF'
Usage: scripts/compile_typst_pdfs.sh [options]

Options:
  -r, --recursive, -Recursive   Recurse into subdirectories for .typ files.
  -c, --clean, -Clean           Delete existing output PDFs before compiling.
      --root PATH, -Root PATH   Project root. Defaults to this script's parent.
  -h, --help                    Show this help.
EOF
}

while (($#)); do
  case "$1" in
    -r|--recursive|-Recursive)
      recursive=true
      shift
      ;;
    -c|--clean|-Clean)
      clean=true
      shift
      ;;
    --root|-Root)
      if (($# < 2)); then
        echo "error: $1 requires a path" >&2
        exit 2
      fi
      root="$(cd -- "$2" && pwd)"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! command -v typst >/dev/null 2>&1; then
  echo "typst command not found. Please install Typst and make sure it is in PATH." >&2
  exit 127
fi

output_dir="$root/complied_pdf"
mkdir -p -- "$output_dir"

mapfile -d '' folders < <(
  find "$root" -mindepth 1 -maxdepth 1 -type d \
    ! -name scripts \
    ! -name complied_pdf \
    -print0 | sort -z
)

if ((${#folders[@]} == 0)); then
  echo "warning: No folders (excluding 'scripts' and 'complied_pdf') were found under: $root" >&2
  exit 0
fi

typ_files=()
for folder in "${folders[@]}"; do
  if [[ "$recursive" == true ]]; then
    while IFS= read -r -d '' typ_file; do
      typ_files+=("$typ_file")
    done < <(find "$folder" -type f -name '*.typ' -print0 | sort -z)
  else
    while IFS= read -r -d '' typ_file; do
      typ_files+=("$typ_file")
    done < <(find "$folder" -maxdepth 1 -type f -name '*.typ' -print0 | sort -z)
  fi
done

if ((${#typ_files[@]} == 0)); then
  echo "warning: No .typ files were found in matching folders." >&2
  exit 0
fi

failed=()

for typ_file in "${typ_files[@]}"; do
  base="$(basename -- "$typ_file")"
  pdf="$output_dir/${base%.typ}.pdf"

  if [[ "$clean" == true && -e "$pdf" ]]; then
    rm -f -- "$pdf"
  fi

  echo "Compiling $typ_file -> $pdf"

  if ! typst compile --root "$root" "$typ_file" "$pdf"; then
    failed+=("$typ_file")
    echo "Compile failed: $typ_file" >&2
  fi
done

if ((${#failed[@]} > 0)); then
  echo
  echo "The following files failed to compile:"
  for typ_file in "${failed[@]}"; do
    echo "  $typ_file"
  done
  exit 1
fi

echo
echo "Done: compiled ${#typ_files[@]} Typst file(s)."
