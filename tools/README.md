# Tools

All scripts are Python 3.10+ and use the standard library only, except the
optional LibreOffice PDF export. Run them from the repository root.

Configuration lives in `config.json` (copy it from `config.example.json`). When
`config.json` is missing, the scripts fall back to the example and print a
note — useful for a first look, not for a real search.

## `offers.py`

### Search

```bash
python3 tools/offers.py search --remote-only --uop
python3 tools/offers.py search --keywords "kubernetes terraform" --seniority senior --limit 20
python3 tools/offers.py search --source rocketjobs --remote --limit 15
python3 tools/offers.py search --hybrid-city Kraków --uop
```

- `--source` — `justjoinit` (default) or `rocketjobs`.
- `--category` — API category; `__auto__` uses the source default.
- `--keywords` — full-text query sent to the API.
- `--city` — API city filter, e.g. `krakow`.
- `--seniority` — local filter, comma separated.
- `--remote` — remote and hybrid.
- `--remote-only` — fully remote only.
- `--hybrid-city` — remote anywhere plus hybrid from that city.
- `--uop` — only permanent employment contracts.
- `--any-work-mode` — ignore the remote/hybrid filters from config.
- `--any-contract` — include offers without a permanent contract.
- `--skills` — all of them must appear in the title or required skills.
- `--limit` — number of results.
- `--json-out` — save raw results to JSON.

Flags override the corresponding `search.*` values in `config.json`.

### Create an offer folder

```bash
python3 tools/offers.py create --slug <slug-from-search>
```

Fetches the full posting, writes `offers/<company>-<role>/offer.md`, and adds a
`found` row to `tracker.csv`. It does not duplicate an existing link.

### Match an offer with your skill tiers

```bash
python3 tools/offers.py match --offer offers/<company>-<role>
```

Prints which daily/working/AI-assisted skills appear in the posting, which
required skills are outside your tiers (do not add them), and any forbidden
core skills.

### LinkedIn

```bash
python3 tools/offers.py linkedin-url --query "senior cloud engineer" --location "European Union"
```

LinkedIn has no public API. The command prints a search URL; open it in a
logged-in browser and paste the chosen posting into a new offer folder.

## `tailor.py`

```bash
python3 tools/tailor.py --offer offers/<folder>
python3 tools/tailor.py --offer offers/<folder> --pdf
python3 tools/tailor.py --offer offers/<folder> --name acme-cloud-engineer
```

- Copies `candidate.master_cv` to the offer folder and to `cv/`.
- Writes `tailoring-report.md` with keywords found, required skills and a
  checklist.
- `--pdf` exports a PDF with LibreOffice and copies it to `cv/`.
- `--name` overrides the output slug (defaults to the folder name).

The script does not edit the CV content. Do that in the DOCX, following
[`../AGENTS.md`](../AGENTS.md).

## `apply.py`

```bash
python3 tools/apply.py queue
python3 tools/apply.py prepare --offer offers/<folder>
python3 tools/apply.py mark-applied --offer offers/<folder>
python3 tools/apply.py mark-applied --offer offers/<folder> --date 2026-11-07
```

- `queue` lists offers in `cv-ready` / `found` (configurable), detects the
  application channel and checks the CV file size.
- `prepare` writes `application-draft.md` with the apply URL, CV list, consent
  policy and approval checklist.
- `mark-applied` sets `applied` and the date, and ticks `- [x] Applied` in
  `offer.md`.

None of these commands sends an application.

## `export_pdf.sh`

```bash
tools/export_pdf.sh
tools/export_pdf.sh offers/acme-cloud-engineer/CV-acme-cloud-engineer.docx
```

Converts `CV-*.docx` files to PDF with LibreOffice. Set `SOFFICE` if the binary
is not on `PATH`.

## Configuration reference

```json
{
  "candidate": {
    "name": "Your Name",
    "location": "City, Country",
    "email": "you@example.com",
    "phone": "+00 000 000 000",
    "github": "https://github.com/your-handle",
    "linkedin": "https://linkedin.com/in/your-handle",
    "master_cv": "cv/MASTER_CV_TEMPLATE.docx"
  },
  "search": {
    "categories": "devops",
    "keywords": "kubernetes terraform cloud",
    "seniority": "mid,senior",
    "city": "",
    "remote_only": true,
    "uop_only": true,
    "hybrid_city": "",
    "limit": 20
  },
  "apply": {
    "default_queue_statuses": "cv-ready,found",
    "recruitment_consent_only": true
  },
  "skills": {
    "daily": ["..."],
    "working": ["..."],
    "ai_assisted": ["..."],
    "forbidden_core": ["..."]
  }
}
```

`candidate.master_cv` is a path relative to the repository root.
