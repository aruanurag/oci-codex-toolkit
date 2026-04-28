# Workbook QA Checklist

Use this checklist before delivering a generated or edited `.xlsx`.

## Structure

- Sheet names are concise, unique, and customer-readable.
- Hidden or very-hidden sheets from an input workbook remain hidden unless intentionally changed.
- Existing sheets, defined names, tables, charts, and formulas are preserved unless the task required edits.
- New sheets have a clear purpose and do not duplicate stale intermediate data.

## Layout

- Header rows are frozen when tables are long.
- Filters are enabled for large tabular sheets.
- Columns are wide enough for labels and formatted values.
- Number, currency, percent, and date formats match the data semantics.
- Summary or assumption cells are visibly separated from raw data.

## Formulas

- Formulas use Excel syntax and expected sheet/range references.
- Totals and summaries are formulas when users are expected to edit inputs later.
- Formula-heavy outputs are recalculated with Excel or LibreOffice when available.
- If recalculation is not available, the final response states that cached formula values may be stale.

## Validation

- Reopen the workbook after writing.
- Run `scripts/inspect_xlsx.py` on the output and review sheet dimensions, formula counts, tables, and external links.
- For edited workbooks, compare the before/after inspection and explain intentional structure changes.
- Avoid delivering a workbook if Excel/LibreOffice reports repair prompts, unreadable content, or broken package relationships.
