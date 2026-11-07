#!/usr/bin/env python3
"""Copy the master CV into an offer folder and write a tailoring report.

  python tools/tailor.py --offer offers/<folder> [--name <slug>] [--pdf]

The script does not invent content. It copies the master CV, extracts keywords
from ``offer.md`` and writes a checklist. A human or an AI agent then edits the
copy according to AGENTS.md and exports the PDF.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import load_config, warn_if_example  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OFFERS = ROOT / "offers"
CV_DIR = ROOT / "cv"

CFG, CFG_PATH = load_config()


def resolve_folder(value: str) -> Path:
    folder = Path(value).expanduser()
    if not folder.is_dir():
        folder = OFFERS / value
    return folder.resolve()


def contains(text: str, term: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


def write_report(folder: Path, text: str, master: Path, output: Path) -> Path:
    skills = CFG["skills"]
    lower = text.lower()
    tiers = (
        ("A / daily", skills.get("daily", [])),
        ("B / working", skills.get("working", [])),
        ("C / AI-assisted", skills.get("ai_assisted", [])),
    )
    found_by_tier = [
        (label, [item for item in tier if contains(lower, item)])
        for label, tier in tiers
    ]

    required_line = next(
        (line for line in text.splitlines() if line.startswith("required_skills:")),
        "",
    )
    required = required_line.replace("required_skills:", "").strip() or "—"
    forbidden = [
        item for item in skills.get("forbidden_core", []) if item.lower() in lower
    ]

    report = folder / "tailoring-report.md"
    report.write_text(
        f"# Tailoring report — {folder.name}\n\n"
        f"- Generated: {dt.date.today().isoformat()}\n"
        f"- Master: `{master.relative_to(ROOT)}`\n"
        f"- Output: `{output.relative_to(ROOT)}`\n\n"
        "## Keywords found in the offer\n\n"
        "| Tier | Skills |\n"
        "|---|---|\n"
        + "\n".join(
            f"| {label} | {', '.join(items) if items else '—'} |"
            for label, items in found_by_tier
        )
        + "\n\n## Required skills from the posting\n\n"
        f"{required}\n\n"
        "## Forbidden core skills in the offer\n\n"
        f"{', '.join(forbidden) if forbidden else 'none'}\n\n"
        "These are listed in `skills.forbidden_core` in `config.json`. Do not add "
        "them to the CV; be honest about the gap in interviews.\n\n"
        "## Checklist\n\n"
        "- [ ] Summary and first three bullets use the top offer keywords 1:1.\n"
        "- [ ] Every claim exists in the master CV; nothing was invented.\n"
        "- [ ] B/C skills were not promoted to A.\n"
        "- [ ] No tables, columns, images or Word headers (ATS-safe).\n"
        "- [ ] Dates use `Mon YYYY–Present`.\n"
        "- [ ] Contact details use full `https://` URLs.\n"
        "- [ ] A PDF was exported and uploaded.\n",
        encoding="utf-8",
    )
    return report


def export_pdf(docx: Path, folder: Path) -> Path | None:
    soffice = (
        os.environ.get("SOFFICE")
        or shutil.which("soffice")
        or shutil.which("libreoffice")
    )
    if not soffice:
        print(
            "PDF export skipped: LibreOffice not found. Install it or set "
            "SOFFICE=/path/to/soffice.",
            file=sys.stderr,
        )
        return None
    try:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(folder), str(docx)],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"PDF export failed: {exc.stderr.strip()}", file=sys.stderr)
        return None
    pdf = folder / (docx.stem + ".pdf")
    if not pdf.exists():
        print(f"PDF export failed: {pdf} was not created.", file=sys.stderr)
        return None
    return pdf


def main(args: argparse.Namespace) -> int:
    folder = resolve_folder(args.offer)
    if not folder.is_dir():
        print(f"Missing offer folder: {args.offer}", file=sys.stderr)
        return 1

    offer_file = folder / "offer.md"
    if not offer_file.exists():
        print(f"Missing file: {offer_file}", file=sys.stderr)
        return 1

    master_value = CFG["candidate"].get("master_cv", "cv/MASTER_CV_TEMPLATE.docx")
    master = ROOT / master_value
    if not master.exists():
        print(
            f"Master CV not found: {master}\n"
            "Put your CV there or update candidate.master_cv in config.json.",
            file=sys.stderr,
        )
        return 1

    slug = args.name or folder.name
    output_name = f"CV-{slug}{master.suffix.lower()}"
    output = folder / output_name
    cv_copy = CV_DIR / output_name
    CV_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copy2(master, output)
    shutil.copy2(master, cv_copy)

    text = offer_file.read_text(encoding="utf-8")
    report = write_report(folder, text, master, output)

    print(f"Copied master CV to: {output.relative_to(ROOT)}")
    print(f"Copy in cv/:        {cv_copy.relative_to(ROOT)}")
    print(f"Tailoring report:    {report.relative_to(ROOT)}")

    if args.pdf:
        if output.suffix.lower() != ".docx":
            print(
                "PDF export is only supported for a DOCX master CV. "
                "Export it manually instead.",
                file=sys.stderr,
            )
            return 1
        pdf = export_pdf(output, folder)
        if pdf:
            shutil.copy2(pdf, CV_DIR / pdf.name)
            print(f"PDF:                {pdf.relative_to(ROOT)}")
            print(f"PDF copy in cv/:    {(CV_DIR / pdf.name).relative_to(ROOT)}")
        else:
            return 1

    print(
        "\nNext: edit the DOCX so the summary and first bullets echo the offer, "
        "then run this script with --pdf (or tools/export_pdf.sh)."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tailor.py", description=__doc__.splitlines()[0]
    )
    parser.add_argument(
        "--offer",
        required=True,
        help="Offer folder, e.g. offers/acme-cloud-engineer",
    )
    parser.add_argument(
        "--name", default="", help="Output slug (default: the folder name)"
    )
    parser.add_argument(
        "--pdf", action="store_true", help="Also export a PDF with LibreOffice"
    )
    return parser


if __name__ == "__main__":
    warn_if_example(CFG_PATH)
    raise SystemExit(main(build_parser().parse_args()))
