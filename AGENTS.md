# AGENTS.md — Job Search Kit

This file is the operating manual for an AI agent working in this repository.
It is deliberately generic: the candidate's real details live in `config.json`
and in the private copy of the repository, never in this public template.

If you are the candidate: read this file once, adjust `config.json`, and give
your agent the repository. If you are the agent: follow the rules below and ask
before any irreversible action.

## 1. Goal

Find roles that match the candidate's declared profile, create one folder per
offer, tailor the CV by **reweighting existing content**, track every
application, and prepare applications with a human approval gate.

## 2. Roles

Work on one offer per role at a time. Each role owns one folder and one tracker
row; read the current file before writing (read-modify-write).

### Finder

- Search with the filters in `config.json`:
  - `search.uop_only` — only permanent employment contracts;
  - `search.remote_only` — fully remote, unless `search.hybrid_city` allows a
    hybrid exception for that city.
- Use `python3 tools/offers.py search` and `python3 tools/offers.py create`.
- Create the folder from `offers/_TEMPLATE.md`, add a `found` row to
  `tracker.csv`, and do **not** tailor the CV.

### Tailor

- Take a row with status `found`.
- Read `offers/<folder>/offer.md` and `python3 tools/offers.py match`.
- Copy the master CV with `python3 tools/tailor.py`.
- Edit the copy according to §4, then export a PDF.
- Set the status to `cv-ready`. Do not apply.

### Applier

- Take rows with status `cv-ready`.
- Run `python3 tools/apply.py prepare --offer offers/<folder>`.
- Fill the form or prepare the draft, show the candidate what will be sent, and
  **stop**. Send only after the candidate writes `APPLY <folder-name>`.
- After sending, run `python3 tools/apply.py mark-applied --offer <folder>`.
- Verify success by a visible confirmation (toast, dialog, application ID), not
  by the absence of an error.

### Tracker

- After an interview or a reply, add notes to the offer folder and update the
  status: `applied → screening → tech → offer` or `rejected`.
- Keep one row per application; never duplicate a link.

## 3. Hard rules

1. **Tell the truth about skills.** The tiers in `config.json` are the source
   of truth:
   - `skills.daily` — used daily, may lead the CV;
   - `skills.working` — real but secondary experience;
   - `skills.ai_assisted` — only as “AI-assisted”, never as expert;
   - `skills.forbidden_core` — never add, even if the offer demands them.
2. **Tailoring means reweighting, not inventing.** Put the offer's keywords 1:1
   into the summary and the first three bullets, push the rest down. Never
   upgrade a B/C skill to A.
3. **ATS-safe documents.** Clean DOCX: no tables, no columns, no images, no
   Word headers. Standard headings (`Summary`, `Experience`, `Skills`,
   `Certifications`). Dates as `Mon YYYY–Present`. Full `https://` URLs.
4. **One file per offer.** Name it `CV-<company>-<role>.docx` inside the offer
   folder and copy it to `cv/`.
5. **The master CV is sacred.** Never edit it while tailoring. Change it only
   when the candidate asks.
6. **Privacy.** Candidate contact details belong in application documents and
   `config.json` only — never in logs, commit messages, public issues or chat
   transcripts.

## 4. Tailoring checklist

- [ ] Read the full posting and the `required_skills` line.
- [ ] Run `tools/offers.py match` and note which A/B/C skills appear.
- [ ] Rewrite the summary around the offer's top three themes.
- [ ] Reorder the experience bullets so the relevant ones come first.
- [ ] Keep every claim traceable to the master CV.
- [ ] Do not add tools, certifications or years of experience that are absent.
- [ ] Check that the DOCX is ATS-safe.
- [ ] Export the PDF and verify it opens and has the right page count.

## 5. Workflow

```text
search → create folder + tracker row (found)
       → tailor CV (cv-ready)
       → prepare application (draft)
       → human writes APPLY <folder>
       → send + verify (applied)
       → screening → tech → offer / rejected
```

Statuses are documented in [`docs/WORKFLOW.md`](docs/WORKFLOW.md).

## 6. Application approval gate

- `tools/apply.py` never sends anything.
- The candidate must write `APPLY <folder-name>` for each application. One
  approval = one offer.
- Show the draft and a screenshot of the filled form before sending.
- Default consent policy: recruitment consent only. Marketing, future
  recruitment pools, data sharing with capital groups and account creation are
  **no**, unless the candidate explicitly says otherwise.
- Do not create accounts on job boards or ATS portals without asking.

## 7. File conventions

- Offer folder: `offers/<company>-<role>/`
- Posting: `offers/<folder>/offer.md`
- Cover letter: `offers/<folder>/cover-letter.md`
- Notes: `offers/<folder>/notes.md`
- Tailored CV: `offers/<folder>/CV-<company>-<role>.docx` (+ `.pdf`)
- Tailoring report: `offers/<folder>/tailoring-report.md`
- Application draft: `offers/<folder>/application-draft.md`
- Tracker columns: `company,role,link,status,applied_on,salary,notes`
- Folder name is repeated in `tracker.csv` notes as `folder: <name>`.

## 8. What to ask the candidate

Ask before:

- changing the master CV;
- publishing or pushing the private copy;
- applying to an offer, or creating any account;
- changing the consent policy or salary expectations;
- deleting an offer folder or tracker row.
