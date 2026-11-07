# CV

This folder holds the master CV and every generated version.

## Master CV

- `MASTER_CV_TEMPLATE.docx` — a clean, ATS-friendly starter. Replace it with
  your real CV, or point `candidate.master_cv` in `config.json` at your file.
- `MASTER_CV_TEMPLATE.md` — the same content as editable Markdown, useful for
  copying into Word or Google Docs.

Rules:

1. **One master.** Edit only the master when your experience changes. Never
   edit it while tailoring.
2. **ATS-safe.** No tables, columns, images, text boxes or Word headers.
   Standard headings: `Summary`, `Experience`, `Skills`, `Certifications`,
   `Education & Languages`.
3. **Dates.** `Mon YYYY–Present`, e.g. `Apr 2022–Present`.
4. **Contact.** Full URLs, e.g. `https://github.com/your-handle` and
   `https://linkedin.com/in/your-handle`.
5. **Length.** One to two pages. Keep the most relevant evidence first.
6. **Truth.** Every claim must be defensible in an interview.

## Generated versions

`tools/tailor.py` copies the master to:

```text
cv/CV-<slug>.docx
offers/<folder>/CV-<slug>.docx
```

PDFs are produced on demand:

```bash
python3 tools/tailor.py --offer offers/<folder> --pdf
# or
tools/export_pdf.sh
```

Generated `CV-*.docx` and `CV-*.pdf` files are git-ignored, because they
contain personal data.

## Recommended workflow

1. Duplicate the master into the offer folder with `tools/tailor.py`.
2. Read `offers/<folder>/offer.md` and `tailoring-report.md`.
3. Reweight the summary and the first three bullets around the offer's themes.
4. Reorder experience bullets; do not invent anything.
5. Export the PDF and check it visually.
6. Upload the PDF where a form requires it; keep the DOCX for edits.

## Naming

- Master: `MASTER_CV_TEMPLATE.docx` (or your own `candidate.master_cv`).
- Per offer: `CV-<company>-<role>.docx`, e.g. `CV-acme-cloud-engineer.docx`.
- The same name is used in `cv/` and in the offer folder.
