#!/usr/bin/env bash
# Export every CV DOCX in offers/ to PDF with LibreOffice.
#
#   tools/export_pdf.sh                 # all offers/*/CV-*.docx
#   tools/export_pdf.sh path/to/CV.docx # one or more files
#
# Requires: LibreOffice (soffice). Override the binary with SOFFICE=...
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
soffice="${SOFFICE:-}"
if [[ -z "$soffice" ]]; then
  if command -v soffice >/dev/null 2>&1; then
    soffice="soffice"
  elif command -v libreoffice >/dev/null 2>&1; then
    soffice="libreoffice"
  else
    echo "LibreOffice not found. Install it or set SOFFICE=/path/to/soffice." >&2
    exit 1
  fi
fi

if [[ $# -gt 0 ]]; then
  files=("$@")
else
  mapfile -t files < <(find "$root/offers" -type f -name 'CV-*.docx' | sort)
fi

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No CV-*.docx files found."
  exit 0
fi

for file in "${files[@]}"; do
  [[ -f "$file" ]] || { echo "Skipping missing file: $file" >&2; continue; }
  dir="$(dirname "$file")"
  "$soffice" --headless --convert-to pdf --outdir "$dir" "$file" >/dev/null
  echo "OK: ${file%.docx}.pdf"
done
