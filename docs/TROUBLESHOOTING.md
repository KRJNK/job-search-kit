# Troubleshooting

## `Cannot parse config.json`

The file is not valid JSON. Common causes: a trailing comma, a missing quote,
or a comment (`//` is not allowed in JSON). Fix it or delete `config.json` to
fall back to the example.

Check it with:

```bash
python3 -m json.tool config.json > /dev/null
```

## The scripts use the example config

`config.json` does not exist. Copy it:

```bash
cp config.example.json config.json
```

The note is informational; the tools still run, but with placeholder data.

## Search returns nothing

- Loosen the filters: remove `--skills`, widen `--seniority`, clear `--city`.
- Try `--source rocketjobs`.
- Check that `categories` matches an existing API category. Use
  `--category __auto__` for the source default.
- The API may be temporarily unavailable. Retry later.

## `Could not fetch offers: HTTP Error 403`

The job board may block the default user agent or require a browser session.
This is not a bug in your config. Options:

1. Wait and retry.
2. Use the LinkedIn URL command or the board's website and paste the posting
   into a folder manually.
3. Update the `User-Agent` in `tools/offers.py` to a current browser string.

Respect the site's terms of service.

## `Missing file: offers/<folder>/offer.md`

The folder exists but the posting file is missing. Recreate the folder with
`tools/offers.py create`, or write `offer.md` from `offers/_TEMPLATE.md`.

## `Master CV not found`

`candidate.master_cv` points to a file that does not exist. Either put your CV
at that path or update `config.json`. Paths are relative to the repository root.

## PDF export does not run

The tools look for `soffice`, then `libreoffice`, then `$SOFFICE`.

```bash
command -v soffice
command -v libreoffice
export SOFFICE=/path/to/soffice
```

On Windows, use `tools/tailor.py --pdf` instead of the Bash script, and set:

```bat
set SOFFICE=C:\Program Files\LibreOffice\program\soffice.exe
```

If LibreOffice is not installed at all, open the DOCX in Word/Google Docs and
export the PDF manually.

## The generated PDF is in the wrong folder

`tools/tailor.py --pdf` writes it next to the DOCX and copies it to `cv/`.
`tools/export_pdf.sh` writes it next to each DOCX. Check the path printed by the
command.

## `permission denied: tools/export_pdf.sh`

Make it executable:

```bash
chmod +x tools/export_pdf.sh
```

Or run it through Bash: `bash tools/export_pdf.sh`.

## Unicode or encoding errors on Windows

Run the commands in Git Bash or WSL, and make sure your editor saves JSON and
Markdown as UTF-8. The scripts read and write UTF-8 explicitly.

## Git says my CV or config is ignored

That is intentional. `config.json`, `cv/CV-*.docx`, `cv/CV-*.pdf` and generated
offer files are git-ignored because they contain personal data. If you really
want to version them, keep the repository private and adjust `.gitignore`
carefully.

## The tracker row is not found by `mark-applied`

The row must have `folder: <name>` in its `notes` column. `offers.py create`
adds it automatically. If you added the row by hand, add the folder name.

## An offer link is not from JustJoin or RocketJobs

`apply.py` cannot fetch the details, so the channel is `not checked`. Open the
link manually and fill the form. The rest of the workflow still works.

## I changed the tracker columns and the scripts broke

The column names are part of the contract. If you rename them, update
`TRACKER_FIELDS` in both `tools/offers.py` and `tools/apply.py`.

## Still stuck

Open an issue with:

- the command you ran;
- the full error message;
- your Python version (`python3 --version`);
- **no personal data** — redact names, e-mails, phone numbers and CV contents.
