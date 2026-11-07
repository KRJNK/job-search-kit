# Job Search Kit

A small, scriptable workspace for running a technical job search — with an AI
agent or on your own. Search job boards, create one folder per offer, tailor a
CV, track every application, and keep a human approval gate before anything is
sent.

The repository is a **template**: it contains no real candidate data. Your
personal configuration, CV and applications stay in `config.json`, `cv/` and
`offers/`, which are either git-ignored or meant for your own private copy.

## What it does

- Searches **JustJoin.it** and **RocketJobs** through their public candidate API.
- Filters by seniority, work mode (remote / hybrid city), employment type
  (permanent contract) and required skills.
- Creates one folder per offer with the full posting and a tracker row.
- Compares an offer with your declared A/B/C skill tiers and flags skills you
  must not invent.
- Copies a master CV into the offer folder and writes a tailoring checklist.
- Exports ATS-friendly PDFs with LibreOffice.
- Prepares an application pre-flight and records the result after a human
  approves sending.
- Defines an agent playbook in [`AGENTS.md`](AGENTS.md).

## Requirements

- **Python 3.10+** — the tools use the standard library only, no `pip install`.
- **Git** — to keep your private copy under version control.
- **LibreOffice** (optional) — only for DOCX → PDF export.
- **GitHub CLI** (optional) — only if you want to publish your own private copy.

## Quick start

```bash
# Replace your-account with the account you are cloning from
# (or copy the URL from the repository's Code button).
git clone https://github.com/your-account/job-search-kit.git
cd job-search-kit

# 1. Create your personal configuration (git-ignored).
cp config.example.json config.json
$EDITOR config.json

# 2. Put your master CV at cv/MASTER_CV_TEMPLATE.docx
#    or point candidate.master_cv in config.json at your own file.

# 3. Search offers.
python3 tools/offers.py search --remote-only --uop

# 4. Create a folder for a chosen offer.
python3 tools/offers.py create --slug <slug-from-the-results>

# 5. Copy the master CV and get a tailoring checklist.
python3 tools/tailor.py --offer offers/<company>-<role>

# 6. Edit the CV, export the PDF, then prepare the application.
python3 tools/tailor.py --offer offers/<company>-<role> --pdf
python3 tools/apply.py prepare --offer offers/<company>-<role>
```

The full step-by-step guide is in [`docs/START.md`](docs/START.md).

## Repository layout

```text
job-search-kit/
├── README.md                 this file
├── AGENTS.md                 playbook for an AI agent working in this repo
├── config.example.json       profile, search filters, skill tiers
├── tracker.csv               one row per application
├── cv/                       master CV and generated PDFs
├── offers/                   one folder per offer
│   ├── _TEMPLATE.md
│   └── _EXAMPLE-cloud-engineer/
├── notes/                    salary bands, interview questions
├── tools/                    Python and shell scripts
└── docs/                     startup, workflow and applying guides
```

## Commands

| Command | Purpose |
|---|---|
| `python3 tools/offers.py search` | Search JustJoin.it / RocketJobs |
| `python3 tools/offers.py create --slug <slug>` | Create an offer folder and tracker row |
| `python3 tools/offers.py match --offer offers/<folder>` | Compare the offer with your skill tiers |
| `python3 tools/offers.py linkedin-url` | Build a LinkedIn search URL |
| `python3 tools/tailor.py --offer offers/<folder>` | Copy the master CV + write a report |
| `python3 tools/tailor.py --offer offers/<folder> --pdf` | The same, plus a PDF |
| `python3 tools/apply.py queue` | List offers ready to apply to |
| `python3 tools/apply.py prepare --offer offers/<folder>` | Pre-flight + application draft |
| `python3 tools/apply.py mark-applied --offer offers/<folder>` | Record a sent application |
| `tools/export_pdf.sh` | Convert every `offers/*/CV-*.docx` to PDF |

Every script has `--help`. Details are in [`tools/README.md`](tools/README.md).

## How the search works

`tools/offers.py` reads API defaults from `config.json`:

- `search.categories` — API category, e.g. `devops`;
- `search.keywords` — full-text query, e.g. `kubernetes terraform`;
- `search.seniority` — local filter, e.g. `mid,senior`;
- `search.remote_only` — only fully remote offers;
- `search.hybrid_city` — remote anywhere plus hybrid offers from that city
  (takes precedence over `remote_only`);
- `search.uop_only` — only offers with a permanent employment contract.

The JustJoin/RocketJobs API changes from time to time. If a query stops
working, see [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md).

## The human approval gate

The scripts **never submit an application**. `apply.py prepare` writes a draft,
and the candidate must explicitly approve before a form is sent. This is
deliberate: wrong CVs, wrong consents and wrong salary answers are expensive.

Read [`docs/APPLYING.md`](docs/APPLYING.md) before the first real application.

## Privacy

- `config.json` is git-ignored.
- Generated CVs, PDFs and application drafts are git-ignored.
- The public template contains only fictional example data.
- If you fork this for your own search, keep your copy **private** unless you
  have removed every personal detail.

## Customisation

1. **Profile and filters** — `config.json`.
2. **Skill tiers** — `config.json` → `skills.daily`, `skills.working`,
   `skills.ai_assisted`, `skills.forbidden_core`.
3. **Statuses** — `found`, `cv-ready`, `applied`, `screening`, `tech`,
   `offer`, `rejected` (documented in [`docs/WORKFLOW.md`](docs/WORKFLOW.md)).
4. **Agent behaviour** — [`AGENTS.md`](AGENTS.md).

## Docs

- [`docs/START.md`](docs/START.md) — setup and first application, step by step.
- [`docs/WORKFLOW.md`](docs/WORKFLOW.md) — statuses, tracker schema, daily loop.
- [`docs/APPLYING.md`](docs/APPLYING.md) — channels, consents and approval gate.
- [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) — common problems.

## License

MIT — see [`LICENSE`](LICENSE).

## Disclaimer

This is a personal productivity toolkit, not a recruitment service. Job board
APIs and ATS forms change without notice. Always verify what a form will send,
respect the terms of the sites you use, and never submit an application you
have not reviewed.
