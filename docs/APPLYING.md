# Applying

The toolkit helps you prepare applications. It never sends one on its own.

## Channels

`tools/apply.py queue` classifies each offer:

| Channel | Meaning |
|---|---|
| `jjit-form` | Form on the JustJoin.it offer page |
| `workday` | Workday ATS (`*.myworkdayjobs.com`) |
| `greenhouse`, `lever`, `smartrecruiters`, `workable`, `ashby`, `teamtailor` | External ATS |
| `traffit`, `e-recruiter`, `elevato` | Recruiter platforms |
| `external:<host>` | Anything else |
| `not checked` | No JustJoin/RocketJobs link |

For external channels, open the `Apply URL` from
`application-draft.md`. Some companies hide the form behind a login; ask the
candidate before creating an account.

## Pre-flight

```bash
python3 tools/apply.py prepare --offer offers/<folder>
```

The draft contains:

- the channel and apply URL;
- the CV files in the folder, with size checks (JustJoin: PDF max 5 MB);
- the consent policy;
- the approval checklist.

Read it, open the form, and compare the fields with the CV.

## Approval gate

1. Fill the form or prepare the exact text to paste.
2. Show the candidate the draft **and** a screenshot of the filled form.
3. Stop.
4. The candidate writes `APPLY <folder-name>`.
5. Send.
6. Verify a visible confirmation: a toast, a dialog, an application ID, or an
   email. “No error” is not confirmation.
7. Record it:

```bash
python3 tools/apply.py mark-applied --offer offers/<folder>
```

One `APPLY` approves one offer. Never batch applications.

## Consents

Default policy, controlled by `apply.recruitment_consent_only` in
`config.json`:

- **Yes** — the recruitment consent required to process the application.
- **No** — marketing, future recruitment pools, sharing data with capital
  groups, creating a candidate account.

If a form makes an optional consent look required, ask the candidate. Do not
tick a box just to get past validation.

## Common form fields

- **Name, e-mail, phone** — copy from the master CV, exactly.
- **Location** — city and country from the CV; remote roles still ask.
- **Salary expectations** — use the range in the posting or your own policy.
  Never invent a number in the form that contradicts `config.json` or the
  candidate's instructions.
- **Availability** — agree on the wording with the candidate beforehand.
- **English level** — match the CV.
- **CV upload** — PDF unless the form accepts DOCX; keep the file name.
- **Links** — full `https://` URLs.

## External ATS notes

- **Workday** — create no account unless asked; some postings allow an
  unauthenticated application, others do not.
- **Greenhouse / Lever / Ashby** — usually public forms, no account.
- **e-recruiter / traffit** — public forms; selects sometimes need a real click
  and progressive validation reveals missing fields only after the first
  submit. Fill, submit, read the errors, fix, resubmit.
- **Numeric-only salary fields** — enter a single number, not a range.
- **CV upload** — if the upload silently fails, check the file size and the
  accepted extensions.

## LinkedIn

LinkedIn has no public application API and requires a logged-in browser. Use
`tools/offers.py linkedin-url` to build the search URL, then apply through the
page. A “1-click Apply” button can send immediately — never click it before
checking which CV is selected.

## After sending

- Update `tracker.csv` (`applied` + date) — `mark-applied` does this.
- Save the confirmation (screenshot or e-mail) in the offer folder if you want
  a record; do not commit personal data to a public repository.
- Follow up after about a week if there is no reply.
- When a reply arrives, update the status: `screening`, `tech`, `offer` or
  `rejected`, and add notes to `notes.md`.

## What not to do

- Do not apply with a CV tailored for a different company.
- Do not select marketing or future-recruitment consents by default.
- Do not create accounts on job boards or ATS portals without approval.
- Do not send an application without a visible confirmation.
- Do not paste personal data into logs, issues or public chat.
