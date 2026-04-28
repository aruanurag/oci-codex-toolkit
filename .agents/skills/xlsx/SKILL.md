---
name: xlsx
description: Create, inspect, edit, analyze, repair, and validate Excel `.xlsx` workbooks. Use when Codex needs to work with spreadsheets, preserve formulas and formatting, generate workbook deliverables, convert tabular data to Excel, audit workbook structure, recalculate formulas, or verify that an `.xlsx` opens cleanly after edits.
---

# XLSX Workbooks

## Core Rules

- Treat the workbook as a structured package, not just a table. Preserve sheets, formulas, defined names, formatting, freeze panes, filters, tables, charts, and hidden sheets unless the user asks to change them.
- Prefer `pandas` for data analysis and bulk table transforms when it is available; prefer `openpyxl` for `.xlsx` creation, edits, formulas, formatting, workbook metadata, and validation.
- Never assume formula results are recalculated by `openpyxl`; it writes formulas but does not evaluate them. Recalculate with Excel or LibreOffice when formula correctness matters.
- Do not overwrite the only copy of a user workbook unless explicitly asked. Write a new output path by default.
- Keep visible spreadsheet layout presentation-ready: meaningful sheet names, frozen headers, filters, appropriate column widths, number formats, and a summary sheet when useful.
- Validate the final workbook by reopening or inspecting it before delivery.

## Workflow

1. Identify the task type: inspect/read, create, edit, analyze, convert, repair, or validate.
2. Inspect existing workbooks before editing:
   - Run `python3 scripts/inspect_xlsx.py path/to/workbook.xlsx --output /tmp/workbook-inspection.json` for a dependency-free package-level summary.
   - If `openpyxl` or `pandas` is available, use it for deeper cell/data checks.
3. For creation and edits:
   - Use `openpyxl` when available for workbook-native `.xlsx` output.
   - Use `pandas` for dataframe transforms, then finish formatting with `openpyxl`.
   - If required packages are missing, use project dependencies if present; otherwise ask before installing new packages.
4. For formulas:
   - Preserve existing formulas unless the user requested formula changes.
   - Set formulas explicitly in Excel syntax.
   - Recalculate with `python3 scripts/recalc_xlsx.py input.xlsx --output output.xlsx` when formulas, charts, pivots, or dependent summaries are material to the task.
5. Validate:
   - Reopen with `openpyxl.load_workbook(..., data_only=False)` when available.
   - Run `scripts/inspect_xlsx.py` on the output and compare workbook structure to expectations.
   - For formula-heavy workbooks, run `scripts/recalc_xlsx.py` or explain why recalculation could not be performed.

## Task Guidance

### Inspecting Workbooks

Use `scripts/inspect_xlsx.py` first when you need a quick map of a workbook without loading large cell contents into context. It reports sheet names, dimensions, formulas, merged cells, tables, drawings, comments, external links, calculation mode, and defined names.

### Creating Workbooks

Build workbooks with:

- one clear purpose per sheet
- a `Summary` or `README` sheet when the workbook has multiple tabs or non-obvious assumptions
- Excel tables for structured data ranges when appropriate
- frozen header rows, filters, readable widths, and consistent number/date formats
- formulas rather than hardcoded totals when the workbook is meant to stay editable

### Editing Existing Workbooks

Before writing:

- inspect workbook structure
- identify sheets/cells/ranges that will change
- preserve unrelated sheets and workbook properties
- save to a new file unless the user requests in-place editing

After writing:

- inspect the output workbook
- recalculate if formulas or charts depend on changed cells
- summarize changed sheets and any validation gaps

### Analysis And Data Extraction

For pure analysis, use `pandas.read_excel()` when available and the workbook is tabular. For styled or formula-rich workbooks, use `openpyxl` so hidden sheets, formulas, merged cells, and metadata are not lost.

### Recalculation

Use `scripts/recalc_xlsx.py` to force recalculation when possible:

```bash
python3 scripts/recalc_xlsx.py input.xlsx --output output.xlsx
```

The script tries LibreOffice first and Microsoft Excel automation on macOS when available. If neither backend is available, it exits with a clear error and leaves the original workbook untouched.

## Resources

- `scripts/inspect_xlsx.py`: dependency-free workbook package inspection.
- `scripts/recalc_xlsx.py`: clean-room workbook recalculation helper using LibreOffice or Excel automation when available.
- `references/workbook-qa.md`: checklist for presentation-ready and calculation-safe workbook delivery.
