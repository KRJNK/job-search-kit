#!/usr/bin/env python3
"""Application queue, pre-flight checks and status updates.

  python tools/apply.py queue
  python tools/apply.py prepare --offer offers/<folder>
  python tools/apply.py mark-applied --offer offers/<folder> [--date YYYY-MM-DD]

This script never submits an application. It prepares a draft and records a
decision made by a human, or by an agent that has explicit approval (see
AGENTS.md and docs/APPLYING.md).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import load_config, warn_if_example  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OFFERS = ROOT / "offers"
TRACKER = ROOT / "tracker.csv"

CFG, CFG_PATH = load_config()

TRACKER_FIELDS = [
    "company", "role", "link", "status", "applied_on", "salary", "notes",
]
PDF_LIMIT_MB = 5

UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) job-search-kit/1.0",
    "Accept": "application/json",
}

ATS_MAP = [
    ("myworkdayjobs.com", "workday"),
    ("greenhouse.io", "greenhouse"),
    ("lever.co", "lever"),
    ("smartrecruiters.com", "smartrecruiters"),
    ("workable.com", "workable"),
    ("ashbyhq.com", "ashby"),
    ("teamtailor.com", "teamtailor"),
    ("traffit.com", "traffit"),
    ("elevato.net", "elevato"),
    ("e-recruiter", "e-recruiter"),
    ("erecruiter", "e-recruiter"),
    ("olx.pl", "olx"),
    ("pracuj.pl", "pracuj"),
]

APIS = {
    "justjoin.it": "https://justjoin.it/api/candidate-api/offers",
    "rocketjobs.pl": "https://rocketjobs.pl/api/candidate-api/offers",
}


def http_json(url: str) -> dict:
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def source_and_slug(link: str) -> tuple[str, str]:
    """Return ``(api_base, slug)`` for JustJoin/RocketJobs links, else empty."""
    try:
        parsed = urllib.parse.urlparse(link)
    except Exception:  # noqa: BLE001
        return "", ""
    host = (parsed.hostname or "").lower()
    base = next((value for key, value in APIS.items() if key in host), "")
    segments = [item for item in parsed.path.split("/") if item]
    slug = (
        segments[-1]
        if segments and segments[0] == "job-offer" and len(segments) >= 2
        else ""
    )
    return base, slug


def classify_channel(apply_url: str | None) -> str:
    if not apply_url:
        return "jjit-form"
    lower = apply_url.lower()
    for fragment, name in ATS_MAP:
        if fragment in lower:
            return name
    try:
        host = urllib.parse.urlparse(apply_url).hostname or "?"
    except Exception:  # noqa: BLE001
        host = "?"
    return f"external:{host}"


def folder_from_notes(notes: str) -> str:
    for part in (notes or "").split(";"):
        part = part.strip()
        if part.lower().startswith("folder:"):
            return part.split(":", 1)[1].strip()
    return ""


def find_cvs(folder: Path) -> list[tuple[Path, int]]:
    return sorted(
        (
            (path, path.stat().st_size)
            for path in folder.glob("CV-*")
            if path.suffix.lower() in (".pdf", ".docx")
        ),
        key=lambda item: (item[0].suffix.lower() != ".pdf", item[0].name),
    )


def read_tracker() -> list[dict]:
    if not TRACKER.exists():
        with TRACKER.open("w", encoding="utf-8", newline="") as handle:
            csv.DictWriter(handle, fieldnames=TRACKER_FIELDS).writeheader()
        return []
    with TRACKER.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_tracker(rows: list[dict]) -> None:
    with TRACKER.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRACKER_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def queue(args: argparse.Namespace) -> int:
    statuses = {
        item.strip().lower()
        for item in (
            args.status or CFG["apply"].get("default_queue_statuses", "")
        ).split(",")
        if item.strip()
    }
    rows = read_tracker()
    selected = [
        row
        for row in rows
        if (row.get("status") or "").strip().lower() in statuses
        and (row.get("link") or "").strip()
    ]
    if not selected:
        print(f"No offers with status: {', '.join(sorted(statuses))}")
        return 0

    print(f"Application queue ({len(selected)}):\n" + "-" * 100)
    for index, row in enumerate(selected, 1):
        company = row.get("company", "?")
        role = row.get("role", "?")
        link = row.get("link", "")
        folder_name = folder_from_notes(row.get("notes", ""))
        folder = OFFERS / folder_name
        channel = "not checked (no link)"
        cv_info = "no folder"

        if link:
            base, slug = source_and_slug(link)
            if base and slug:
                try:
                    detail = http_json(base + "/" + urllib.parse.quote(slug))
                    channel = classify_channel(detail.get("applyUrl"))
                    if detail.get("applyUrl"):
                        channel += f" -> {detail['applyUrl']}"
                except Exception as exc:  # noqa: BLE001
                    channel = f"api-error: {exc}"
            else:
                channel = "manual (link is not JustJoin/RocketJobs)"

        if folder.is_dir():
            cvs = find_cvs(folder)
            if cvs:
                descriptions = []
                for path, size in cvs:
                    too_large = (
                        path.suffix.lower() == ".pdf"
                        and size > PDF_LIMIT_MB * 1024 * 1024
                    )
                    flag = "TOO LARGE >5MB" if too_large else "OK"
                    descriptions.append(
                        f"{path.name} ({size // 1024} KB, {flag})"
                    )
                cv_info = "; ".join(descriptions)
            else:
                cv_info = "NO CV-*.pdf/docx in the folder"

        print(f"{index}. {company} — {role} [{row.get('status')}]")
        print(f"   link: {link}")
        print(f"   channel: {channel}")
        print(f"   CV: {cv_info}")
        if channel == "jjit-form":
            print(
                "   next: fill the JustJoin form, show a screenshot, wait for "
                "approval, then send"
            )
        elif channel.startswith("api-error") or channel.startswith("not checked"):
            print("   next: check the link manually")
        elif channel.startswith("manual"):
            print(
                "   next: open the link manually, fill the form, wait for "
                "approval, then send"
            )
        else:
            print(
                "   next: open the external ATS, fill it, wait for approval, "
                "then send"
            )
        print()

    print("Next: python tools/apply.py prepare --offer offers/<folder>")
    return 0


def prepare(args: argparse.Namespace) -> int:
    folder = Path(args.offer).expanduser()
    if not folder.is_dir():
        folder = OFFERS / args.offer
    folder = folder.resolve()
    if not folder.is_dir():
        print(f"Missing folder: {args.offer}", file=sys.stderr)
        return 1

    link = ""
    offer_file = folder / "offer.md"
    if offer_file.exists():
        for line in offer_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("Link:"):
                link = line.replace("Link:", "").strip()
                break

    channel = "manual (link is not JustJoin/RocketJobs)"
    apply_url = ""
    base, slug = source_and_slug(link)
    if base and slug:
        try:
            detail = http_json(base + "/" + urllib.parse.quote(slug))
            apply_url = detail.get("applyUrl") or ""
            channel = classify_channel(detail.get("applyUrl"))
        except Exception as exc:  # noqa: BLE001
            channel = f"api-error: {exc}"
    elif link:
        apply_url = link
    else:
        channel = "unknown (add a Link: line to offer.md)"

    cvs = find_cvs(folder)
    cv_lines = []
    for path, size in cvs:
        ok = not (
            path.suffix.lower() == ".pdf" and size > PDF_LIMIT_MB * 1024 * 1024
        )
        cv_lines.append(
            f"- {path.name} ({size // 1024} KB) "
            f"{'OK' if ok else 'TOO LARGE — compress before uploading'}"
        )

    recruitment_only = CFG["apply"].get("recruitment_consent_only", True)
    if recruitment_only:
        consent = (
            "- [ ] marketing / account creation: NO\n"
            "- [ ] recruitment consent: YES (implied by submitting the form)\n"
        )
    else:
        consent = "- [ ] follow your own consent policy\n"

    draft = folder / "application-draft.md"
    draft.write_text(
        f"# Application draft: {folder.name}\n"
        f"Link: {link}\n"
        f"Channel: {channel}\n"
        + (f"Apply URL: {apply_url}\n" if apply_url else "")
        + f"Prepared on: {dt.date.today().isoformat()}\n\n"
        "## CV in the folder\n"
        + ("\n".join(cv_lines) if cv_lines else "- NO CV — run the tailor step first")
        + "\n\n"
        "## Form data (copy from the master CV; never log it publicly)\n"
        "- full name, email, phone: as in CV-*.docx\n"
        "- JustJoin uploads require a PDF (max 5 MB)\n\n"
        "## Consents\n"
        + consent
        + "\n## Approval gate\n"
        "- [ ] draft shown to the candidate (this file + form screenshot)\n"
        "- [ ] candidate wrote: APPLY <folder-name>\n"
        "- [ ] after sending: python tools/apply.py mark-applied --offer "
        f"offers/{folder.name}\n",
        encoding="utf-8",
    )

    print(f"Folder: {folder.name}\nChannel: {channel}")
    if apply_url:
        print(f"Apply URL: {apply_url}")
    print("CV:")
    print("\n".join(cv_lines) if cv_lines else "  NO CV — run the tailor step first")
    print(f"\nDraft: {draft.relative_to(ROOT)}")
    print("Show it to the candidate and wait for APPLY <folder-name>.")
    return 0


def mark_applied(args: argparse.Namespace) -> int:
    rows = read_tracker()
    target = args.offer.strip().lower().rstrip("/")
    if "/" in target or "\\" in target:
        target = target.replace("\\", "/").split("/")[-1]

    row = next(
        (
            item
            for item in rows
            if folder_from_notes(item.get("notes", "")).lower() == target
        ),
        None,
    )
    if row is None:
        print(f"No tracker row for folder: {args.offer}", file=sys.stderr)
        return 1

    row["status"] = "applied"
    row["applied_on"] = args.date or dt.date.today().isoformat()
    write_tracker(rows)

    actual_folder = folder_from_notes(row.get("notes", ""))
    offer_file = OFFERS / actual_folder / "offer.md"
    if offer_file.exists():
        text = offer_file.read_text(encoding="utf-8").replace(
            "- [ ] Applied", "- [x] Applied"
        )
        offer_file.write_text(text, encoding="utf-8")

    print(
        f"Saved: {row.get('company')} — {row.get('role')} -> applied "
        f"({row['applied_on']})."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="apply.py", description=__doc__.splitlines()[0]
    )
    sub = parser.add_subparsers(dest="command", required=True)

    queue_parser = sub.add_parser(
        "queue", help="List offers ready to apply to, with channel and CV status"
    )
    queue_parser.add_argument(
        "--status", default="", help="Comma separated statuses (default from config)"
    )
    queue_parser.set_defaults(func=queue)

    prepare_parser = sub.add_parser(
        "prepare", help="Pre-flight one offer and write application-draft.md"
    )
    prepare_parser.add_argument("--offer", required=True)
    prepare_parser.set_defaults(func=prepare)

    mark_parser = sub.add_parser(
        "mark-applied", help="Record an application after it was sent"
    )
    mark_parser.add_argument("--offer", required=True)
    mark_parser.add_argument("--date", default="")
    mark_parser.set_defaults(func=mark_applied)

    return parser


def main() -> int:
    warn_if_example(CFG_PATH)
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
