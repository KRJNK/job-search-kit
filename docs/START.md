# Startup guide

From a fresh clone to your first prepared application. Allow about 15 minutes.

## 0. Checklist

- [ ] Python 3.10 or newer (`python3 --version`).
- [ ] Git.
- [ ] LibreOffice (optional, for PDF export).
- [ ] A master CV in DOCX format.
- [ ] A JustJoin.it or RocketJobs account if you want to apply there.
- [ ] Your real skill tiers written down — honestly.

## 1. Clone the repository

```bash
# Replace your-account with the account you are cloning from
# (or copy the URL from the repository's Code button).
git clone https://github.com/your-account/job-search-kit.git
cd job-search-kit
```

If you plan to use this for a real search, keep your copy **private**: create
your own empty private repository and push to it.

## 2. Check the toolchain

```bash
python3 --version          # 3.10+
git --version
command -v soffice || command -v libreoffice   # optional
```

The Python tools need no third-party packages.

## 3. Create your configuration

```bash
cp config.example.json config.json
```

`config.json` is git-ignored. Fill in three blocks.

### `candidate`

```json
"candidate": {
  "name": "Your Name",
  "location": "City, Country",
  "email": "you@example.com",
  "phone": "+00 000 000 000",
  "github": "https://github.com/your-handle",
  "linkedin": "https://linkedin.com/in/your-handle",
  "master_cv": "cv/MASTER_CV_TEMPLATE.docx"
}
```

`master_cv` is a path relative to the repository root.

### `search`

```json
"search": {
  "categories": "devops",
  "keywords": "kubernetes terraform cloud",
  "seniority": "mid,senior",
  "city": "",
  "remote_only": true,
  "uop_only": true,
  "hybrid_city": "",
  "limit": 20
}
```

- `remote_only: true` keeps only fully remote offers.
- Set `hybrid_city` to allow remote offers **plus** hybrid offers from that
  city, e.g. `"Kraków"`. It takes precedence over `remote_only`.
- `uop_only: true` keeps only permanent employment contracts.
- Leave `city` empty to search the whole country.

### `skills`

This is the most important block. It is your truth anchor:

- `daily` — used daily, may lead the CV;
- `working` — real but secondary experience;
- `ai_assisted` — only as “AI-assisted”, never as expert;
- `forbidden_core` — never add, even if an offer demands them.

Do not pad these lists. The whole value of the toolkit is that tailoring
reweights real evidence instead of inventing it.

## 4. Add your master CV

Either replace `cv/MASTER_CV_TEMPLATE.docx` with your CV and keep the path, or
put your file elsewhere and update `candidate.master_cv`.

If you start from the template, read [`../cv/README.md`](../cv/README.md) for
the ATS rules.

## 5. Smoke test

```bash
python3 tools/offers.py --help
python3 tools/offers.py search --limit 5
```

You should see a short list of offers. The first run prints a note that
`config.example.json` is being used if `config.json` is missing.

## 6. Search with your filters

```bash
python3 tools/offers.py search --remote-only --uop --limit 20
```

Useful variations:

```bash
# Remote or hybrid from one city
python3 tools/offers.py search --hybrid-city Kraków --uop

# Narrow by keywords and seniority
python3 tools/offers.py search --keywords "kubernetes terraform" --seniority senior

# Only offers mentioning specific skills
python3 tools/offers.py search --skills kubernetes aws --uop
```

Pick a slug from the output.

## 7. Create an offer folder

```bash
python3 tools/offers.py create --slug <slug>
```

This creates `offers/<company>-<role>/offer.md`, saves the full posting, and
adds a `found` row to `tracker.csv`.

## 8. Tailor the CV

```bash
python3 tools/offers.py match --offer offers/<company>-<role>
python3 tools/tailor.py --offer offers/<company>-<role>
```

`match` tells you which of your skills appear in the posting and which required
skills are outside your profile (do not add them). `tailor` copies the master
CV and writes `tailoring-report.md`.

Now edit the copy in the offer folder:

1. Rewrite the summary around the offer's top three themes.
2. Put the most relevant experience bullets first.
3. Keep every claim traceable to the master CV.
4. Export the PDF:

```bash
python3 tools/tailor.py --offer offers/<company>-<role> --pdf
```

Check the PDF visually, then set the tracker status to `cv-ready`.

## 9. Prepare the application

```bash
python3 tools/apply.py prepare --offer offers/<company>-<role>
```

This writes `application-draft.md` with the channel, apply URL, CV list and the
approval checklist. Read [`APPLYING.md`](APPLYING.md) before sending.

The scripts never send anything. A human fills the form (or reviews the filled
form), checks consents, and sends.

## 10. Record the application

```bash
python3 tools/apply.py mark-applied --offer offers/<company>-<role>
```

This sets `applied` and the date in `tracker.csv`, and ticks the checkbox in
`offer.md`.

## Daily loop

```bash
python3 tools/offers.py search --remote-only --uop
python3 tools/offers.py create --slug <slug>
python3 tools/offers.py match --offer offers/<folder>
python3 tools/tailor.py --offer offers/<folder> --pdf
python3 tools/apply.py queue
python3 tools/apply.py prepare --offer offers/<folder>
```

## Windows notes

- Use `python` instead of `python3` if that is how Python is installed.
- Git Bash or WSL works well for the shell commands.
- If `soffice` is not on `PATH`, set it for the session:
  `set SOFFICE=C:\Program Files\LibreOffice\program\soffice.exe`.
- `tools/export_pdf.sh` requires Bash; on Windows use the `--pdf` option of
  `tools/tailor.py` instead.

## Next

- [`WORKFLOW.md`](WORKFLOW.md) — statuses, tracker schema, quality gates.
- [`APPLYING.md`](APPLYING.md) — channels, consents, approval gate.
- [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) — when something breaks.
