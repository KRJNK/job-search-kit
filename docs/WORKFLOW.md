# Workflow

## Lifecycle

```text
                 ┌─────────────┐
 search ────────▶│    found    │
                 └──────┬──────┘
                        │ tailor
                        ▼
                 ┌─────────────┐
                 │  cv-ready   │
                 └──────┬──────┘
                        │ apply + verify
                        ▼
                 ┌─────────────┐
                 │   applied   │
                 └──────┬──────┘
                        │ reply
                        ▼
                 ┌─────────────┐
                 │  screening  │
                 └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │     tech    │
                 └──────┬──────┘
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
       ┌─────────────┐     ┌─────────────┐
       │    offer    │     │  rejected   │
       └─────────────┘     └─────────────┘
```

## Statuses

| Status | Meaning | Set by |
|---|---|---|
| `found` | Offer saved, no CV yet | `offers.py create` |
| `cv-ready` | Tailored CV and PDF exist | Tailor / human |
| `applied` | Application sent and confirmed | `apply.py mark-applied` |
| `screening` | Recruiter or HR conversation | Human |
| `tech` | Technical interview stage | Human |
| `offer` | Offer received | Human |
| `rejected` | Rejected or withdrawn | Human |

Keep the status lowercase and exact; the scripts compare it case-insensitively
but the tracker is easier to read when it is consistent.

## Tracker schema

`tracker.csv`:

```csv
company,role,link,status,applied_on,salary,notes
Acme Cloud,Cloud Engineer,https://example.com/jobs/123,applied,2026-11-07,"25 000–30 000 PLN permanent",source: justjoinit; folder: acme-cloud-cloud-engineer
```

| Column | Meaning |
|---|---|
| `company` | Company name |
| `role` | Role title |
| `link` | Canonical posting URL |
| `status` | One of the statuses above |
| `applied_on` | `YYYY-MM-DD`, empty until applied |
| `salary` | Salary range from the posting, if given |
| `notes` | Source and `folder:`; `folder:` is used by the scripts |

Do not rename the columns unless you also update `TRACKER_FIELDS` in
`tools/offers.py` and `tools/apply.py`.

## Folder layout

```text
offers/<company>-<role>/
├── offer.md                full posting + keywords + status
├── notes.md                interview notes, contacts, questions
├── cover-letter.md         optional
├── CV-<company>-<role>.docx
├── CV-<company>-<role>.pdf
├── tailoring-report.md     generated keyword report
└── application-draft.md    generated pre-flight
```

One folder = one offer. If the same company posts the same role twice, add a
numeric suffix (`-2`) and keep both links; the tracker uses the link to avoid
duplicates.

## Daily loop

1. **Search** — `tools/offers.py search` with your filters.
2. **Triage** — read the posting; discard offers that break your hard filters
   (employment type, remote policy).
3. **Create** — `tools/offers.py create --slug <slug>`.
4. **Analyse** — `tools/offers.py match --offer ...`.
5. **Tailor** — `tools/tailor.py --offer ...`, edit, export PDF.
6. **Queue** — `tools/apply.py queue`.
7. **Prepare** — `tools/apply.py prepare --offer ...`.
8. **Apply** — human reviews and sends; then `mark-applied`.
9. **Follow up** — after a week, note it in `notes.md`; update status when a
   reply arrives.

## Quality gates

Before status `cv-ready`:

- [ ] Summary and first three bullets echo the offer's top keywords.
- [ ] Every claim exists in the master CV.
- [ ] No B/C skill was promoted to A.
- [ ] DOCX is ATS-safe (no tables/columns/images/headers).
- [ ] PDF opens and looks right.
- [ ] File name follows `CV-<company>-<role>.docx`.

Before status `applied`:

- [ ] The correct CV was attached (check the file name in the form).
- [ ] Only recruitment consent is selected.
- [ ] Salary and availability answers match your policy.
- [ ] A visible confirmation was seen after sending.
- [ ] `mark-applied` recorded the date.

## Agent roles

The detailed playbook is in [`../AGENTS.md`](../AGENTS.md). The short version:

- **Finder** — searches and creates folders; never tailors.
- **Tailor** — creates the CV copy and edits it; never applies.
- **Applier** — prepares and (after approval) sends; never invents data.
- **Tracker** — records outcomes and notes.

One agent works on one offer at a time, and every write is
read-modify-write: read the current tracker or folder before editing it.
