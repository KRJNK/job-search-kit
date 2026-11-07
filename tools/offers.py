#!/usr/bin/env python3
"""Search JustJoin.it / RocketJobs, create offer folders and analyse keywords.

Standard library only. Run from the repository root:

  python tools/offers.py search --keywords "kubernetes terraform" --remote-only --uop
  python tools/offers.py create --source justjoinit --slug <slug>
  python tools/offers.py match --offer offers/<company>-<role>
  python tools/offers.py linkedin-url --query "senior cloud engineer"

LinkedIn has no public API and requires a logged-in browser. ``linkedin-url``
only prints a search URL; paste the chosen posting into a new offer folder.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html as ihtml
import json
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import load_config, warn_if_example  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OFFERS = ROOT / "offers"
TRACKER = ROOT / "tracker.csv"
TEMPLATE = OFFERS / "_TEMPLATE.md"

CFG, CFG_PATH = load_config()

SOURCES = {
    "justjoinit": {
        "api": "https://justjoin.it/api/candidate-api/offers",
        "offer_url": "https://justjoin.it/job-offer/{slug}",
    },
    "rocketjobs": {
        "api": "https://rocketjobs.pl/api/candidate-api/offers",
        "offer_url": "https://rocketjobs.pl/job-offer/{slug}",
    },
}

TRACKER_FIELDS = [
    "company", "role", "link", "status", "applied_on", "salary", "notes",
]

UA = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) job-search-kit/1.0",
    "Accept": "application/json",
}

ALIASES = {
    "kubernetes": ["kubernetes", "k8s"],
    "github actions": ["github actions", "github-actions"],
    "gitlab ci": ["gitlab ci", "gitlab-ci", "gitlab"],
    "infrastructure as code": ["infrastructure as code", "iac"],
    "go": ["golang", "go"],
}


def http_json(url: str) -> dict:
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def slugify(text: str, limit: int = 60) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", text)[:limit].strip("-") or "offer"


def html_to_text(body_html: str) -> str:
    text = re.sub(
        r"</(p|div|li|ul|ol|h[1-6]|br|tr)>", "\n", body_html or "", flags=re.I
    )
    text = re.sub(r"<[^>]+>", "", text)
    text = ihtml.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_city(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = text.encode("ascii", "ignore").decode()
    return text.lower().strip()


def salary_range(offer: dict) -> str:
    for employment in offer.get("employmentTypes") or []:
        if employment.get("currencySource") != "original":
            continue
        low = employment.get("from")
        high = employment.get("to")
        currency = employment.get("currency") or ""
        kind = employment.get("type") or ""
        if low or high:
            return f"{low or '?'}–{high or '?'} {currency} {kind}".strip()
    return ""


def is_permanent(offer: dict) -> bool:
    """True when the posting includes an employment contract (permanent)."""
    return any(
        (item.get("type") or "").lower() == "permanent"
        for item in offer.get("employmentTypes") or []
    )


def ensure_tracker() -> None:
    if not TRACKER.exists():
        with TRACKER.open("w", encoding="utf-8", newline="") as handle:
            csv.DictWriter(handle, fieldnames=TRACKER_FIELDS).writeheader()


def append_tracker(row: dict) -> bool:
    ensure_tracker()
    with TRACKER.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if any((existing.get("link") or "") == row.get("link") for existing in rows):
        return False
    rows.append({field: row.get(field, "") for field in TRACKER_FIELDS})
    with TRACKER.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRACKER_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return True


def search(args: argparse.Namespace) -> int:
    settings = CFG["search"]
    source = args.source or "justjoinit"
    api = SOURCES[source]
    limit = args.limit or int(settings.get("limit") or 20)

    category = args.category if args.category is not None else settings.get("categories", "")
    if category == "__auto__":
        category = "devops" if source == "justjoinit" else ""
    keywords = args.keywords if args.keywords is not None else settings.get("keywords", "")
    city = args.city if args.city is not None else settings.get("city", "")
    seniority = [
        item.strip().lower()
        for item in (
            args.seniority
            if args.seniority is not None
            else settings.get("seniority", "")
        ).split(",")
        if item.strip()
    ]
    uop_only = args.uop if args.uop is not None else bool(settings.get("uop_only"))
    remote_only = (
        args.remote_only
        if args.remote_only is not None
        else bool(settings.get("remote_only"))
    )
    remote = args.remote if args.remote is not None else False
    hybrid_city = (
        args.hybrid_city
        if args.hybrid_city is not None
        else settings.get("hybrid_city", "")
    )
    if args.any_work_mode:
        hybrid_city = ""
        remote_only = False
        remote = False
    if args.any_contract:
        uop_only = False
    skills = args.skills or []

    collected: list[dict] = []
    start = 0
    step = min(limit, 50)
    while len(collected) < limit:
        query = {"itemsCount": step, "from": start}
        if category:
            query["categories"] = category
        if keywords:
            query["keywords"] = keywords
        if city:
            query["city"] = city
        url = api["api"] + "?" + urllib.parse.urlencode(query)
        try:
            payload = http_json(url)
        except Exception as exc:  # noqa: BLE001
            print(f"Could not fetch offers: {exc}", file=sys.stderr)
            return 1
        batch = payload.get("data", [])
        if not batch:
            break
        collected.extend(batch)
        meta = payload.get("meta", {})
        cursor = (meta.get("next") or {}).get("cursor")
        if cursor is None or len(batch) < step:
            break
        start = cursor

    def work_mode_matches(offer: dict) -> bool:
        mode = (offer.get("workplaceType") or "").lower()
        offer_city = (offer.get("city") or "").lower()
        if hybrid_city:
            if mode == "remote":
                return True
            return mode == "hybrid" and normalize_city(
                offer_city
            ) == normalize_city(hybrid_city)
        if remote_only:
            return mode == "remote"
        if remote:
            return mode in ("remote", "hybrid")
        return True

    results = []
    for offer in collected[: limit * 3]:
        if seniority and (offer.get("experienceLevel") or "").lower() not in seniority:
            continue
        if not work_mode_matches(offer):
            continue
        if skills:
            haystack = " ".join(
                [
                    offer.get("title", ""),
                    " ".join(
                        skill.get("name", "")
                        for skill in offer.get("requiredSkills") or []
                    ),
                ]
            ).lower()
            if not all(skill.lower() in haystack for skill in skills):
                continue
        if uop_only and not is_permanent(offer):
            continue
        results.append(offer)
        if len(results) >= limit:
            break

    if args.json_out:
        output = Path(args.json_out)
        output.write_text(
            json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"Saved {len(results)} offers to {output}")

    print(f"Found {len(results)} offers ({source}, scanned {len(collected)}).")
    print("-" * 100)
    for offer in results:
        skills_text = ", ".join(
            skill.get("name", "")
            for skill in (offer.get("requiredSkills") or [])[:6]
        )
        print(f"{offer.get('companyName', '?')} — {offer.get('title', '?')}")
        print(
            f"  {offer.get('experienceLevel', '?')} | "
            f"{offer.get('workplaceType', '?')} | "
            f"{offer.get('city', '?')} | {salary_range(offer)}"
        )
        print(f"  skills: {skills_text}")
        print(f"  slug: {offer.get('slug', '')}")
        print()

    if results:
        print(
            "Create an offer folder: python tools/offers.py create "
            f"--source {source} --slug <slug>"
        )
    return 0


def create_offer(args: argparse.Namespace) -> int:
    source = args.source
    api = SOURCES[source]
    slug = args.slug
    url = api["api"] + "/" + urllib.parse.quote(slug)
    try:
        detail = http_json(url)
    except Exception as exc:  # noqa: BLE001
        print(f"Could not fetch offer details: {exc}", file=sys.stderr)
        return 1

    body = html_to_text(detail.get("body", ""))
    required = [
        skill.get("name", "") for skill in detail.get("requiredSkills") or []
    ]
    nice = [
        skill.get("name", "") for skill in detail.get("niceToHaveSkills") or []
    ]
    link = args.link or api["offer_url"].format(slug=slug)
    company = slugify(detail.get("companyName", "company"), 40)
    role = slugify(detail.get("title", "role"), 40)
    folder = OFFERS / f"{company}-{role}"
    folder.mkdir(parents=True, exist_ok=True)

    offer_file = folder / "offer.md"
    if not offer_file.exists():
        offer_file.write_text(
            f"# Offer: {detail.get('companyName', '?')} — "
            f"{detail.get('title', '?')}\n"
            f"Link: {link}\n"
            f"Found on: {dt.date.today().isoformat()}\n"
            f"Source: {source} | seniority: {detail.get('experienceLevel', '?')} | "
            f"work mode: {detail.get('workplaceType', '?')} | "
            f"city: {detail.get('city', '?')} | "
            f"salary: {salary_range(detail)}\n"
            f"Published: {detail.get('publishedAt', '?')}\n"
            f"\n## Requirements (paste from the posting)\n\n{body}\n"
            f"\n## CV keywords\n\n"
            f"required_skills: {', '.join(required) or '—'}\n"
            f"nice_to_have: {', '.join(nice) or '—'}\n"
            f"\n## Interview questions\n\n\n## Status\n"
            f"- [ ] CV tailored\n- [ ] Applied\n- [ ] Response\n",
            encoding="utf-8",
        )

    added = append_tracker(
        {
            "company": detail.get("companyName", ""),
            "role": detail.get("title", ""),
            "link": link,
            "status": "found",
            "applied_on": "",
            "salary": salary_range(detail),
            "notes": f"source: {source}; folder: {folder.name}",
        }
    )
    print(f"Folder: {folder}")
    if added:
        print("Tracker: added a row with status 'found'.")
    else:
        print("Tracker: this link is already present, nothing added.")
    print(
        "Next: tailor the CV with python tools/tailor.py --offer "
        f"{folder.relative_to(ROOT)}"
    )
    return 0


def contains_term(text: str, term: str) -> bool:
    lower = term.lower()
    variants = ALIASES.get(lower, [lower])
    for variant in variants:
        if re.search(r"(?<![a-z0-9])" + re.escape(variant) + r"(?![a-z0-9])", text):
            return True
    return False


def match(args: argparse.Namespace) -> int:
    folder = Path(args.offer).expanduser()
    if not folder.is_dir():
        folder = OFFERS / args.offer
    folder = folder.resolve()
    offer_file = folder / "offer.md"
    if not offer_file.exists():
        print(f"Missing file: {offer_file}", file=sys.stderr)
        return 1

    text = offer_file.read_text(encoding="utf-8")
    lower = text.lower()
    skills = CFG["skills"]

    print(f"Analysis: {folder.name} (reading {offer_file.name})\n")
    tiers = (
        ("A / daily", skills.get("daily", [])),
        ("B / working", skills.get("working", [])),
        ("C / AI-assisted", skills.get("ai_assisted", [])),
    )
    for label, tier in tiers:
        found = [item for item in tier if contains_term(lower, item)]
        print(f"{label}: in the offer → use 1:1 in the summary and first bullets:")
        print(f"  {', '.join(found) or '—'}")
    print()

    required_line = next(
        (line for line in text.splitlines() if line.startswith("required_skills:")),
        "",
    )
    required = [
        item.strip()
        for item in required_line.replace("required_skills:", "").split(",")
        if item.strip()
    ]
    known = (
        skills.get("daily", [])
        + skills.get("working", [])
        + skills.get("ai_assisted", [])
    )
    gaps = [
        item
        for item in required
        if not any(contains_term(item.lower(), known_item) for known_item in known)
    ]
    if gaps:
        print(f"In the offer but outside your A/B/C tiers — do NOT add to the CV:")
        print(f"  {', '.join(gaps)}")
    print()

    forbidden = [
        item for item in skills.get("forbidden_core", []) if item.lower() in lower
    ]
    if forbidden:
        print(
            f"WARNING: the offer mentions {', '.join(forbidden)}, listed as "
            "forbidden core skills in config.json. Do not add them; be honest "
            "about the gap in interviews."
        )
    else:
        print("No forbidden core skills found in the offer.")
    print(
        "\nTailoring rule: put the offer's keywords 1:1 into the summary and the "
        "first three bullets, push the rest down, and never upgrade a B/C skill to A."
    )
    return 0


def linkedin_url(args: argparse.Namespace) -> int:
    query = {
        "keywords": args.query,
        "location": args.location,
        "f_TPR": args.period,
        "f_WT": args.work_type,
        "sortBy": "DD",
    }
    url = "https://www.linkedin.com/jobs/search/?" + urllib.parse.urlencode(query)
    print("LinkedIn has no public API and requires a logged-in browser.")
    print("Open this URL in your browser:\n")
    print(url)
    print(
        "\nCopy the full text of a posting into offers/<company>-<role>/offer.md "
        "(see offers/_TEMPLATE.md) and add a row to tracker.csv."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="offers.py", description=__doc__.splitlines()[0]
    )
    sub = parser.add_subparsers(dest="command", required=True)

    search_parser = sub.add_parser(
        "search", help="Search JustJoin.it / RocketJobs"
    )
    search_parser.add_argument(
        "--source", choices=sorted(SOURCES), default=None
    )
    search_parser.add_argument(
        "--category",
        default=None,
        help="API category, e.g. devops (use __auto__ for the source default)",
    )
    search_parser.add_argument(
        "--keywords", default=None, help="Full-text query sent to the API"
    )
    search_parser.add_argument(
        "--city", default=None, help="API city filter, e.g. krakow"
    )
    search_parser.add_argument(
        "--seniority",
        default=None,
        help="Local filter, comma separated: junior,mid,senior",
    )
    search_parser.add_argument(
        "--remote",
        action="store_const",
        const=True,
        default=None,
        help="Remote and hybrid offers",
    )
    search_parser.add_argument(
        "--remote-only",
        action="store_const",
        const=True,
        default=None,
        help="Fully remote offers only",
    )
    search_parser.add_argument(
        "--hybrid-city",
        default=None,
        help="Remote anywhere plus hybrid offers from this city",
    )
    search_parser.add_argument(
        "--uop",
        action="store_const",
        const=True,
        default=None,
        help="Only offers with a permanent employment contract",
    )
    search_parser.add_argument(
        "--any-work-mode",
        action="store_true",
        help="Ignore the remote/hybrid filters from config",
    )
    search_parser.add_argument(
        "--any-contract",
        action="store_true",
        help="Include offers without a permanent contract",
    )
    search_parser.add_argument(
        "--skills",
        nargs="*",
        default=None,
        help="All of these must appear in the title or required skills",
    )
    search_parser.add_argument("--limit", type=int, default=None)
    search_parser.add_argument(
        "--json-out", default="", help="Write raw results to a JSON file"
    )
    search_parser.set_defaults(func=search)

    create_parser = sub.add_parser(
        "create", help="Fetch offer details, create a folder and add a tracker row"
    )
    create_parser.add_argument(
        "--source", choices=sorted(SOURCES), default="justjoinit"
    )
    create_parser.add_argument("--slug", required=True)
    create_parser.add_argument("--link", default="")
    create_parser.set_defaults(func=create_offer)

    match_parser = sub.add_parser(
        "match", help="Compare an offer with your A/B/C skill tiers"
    )
    match_parser.add_argument(
        "--offer", required=True, help="Offer folder, e.g. offers/acme-cloud-engineer"
    )
    match_parser.set_defaults(func=match)

    linkedin_parser = sub.add_parser(
        "linkedin-url", help="Build a LinkedIn job search URL"
    )
    linkedin_parser.add_argument("--query", default="senior cloud engineer")
    linkedin_parser.add_argument("--location", default="European Union")
    linkedin_parser.add_argument(
        "--period",
        default="r604800",
        help="r86400=24h, r604800=week, r2592000=month",
    )
    linkedin_parser.add_argument(
        "--work-type", default="2", help="2=remote (empty = all)"
    )
    linkedin_parser.set_defaults(func=linkedin_url)

    return parser


def main() -> int:
    warn_if_example(CFG_PATH)
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
