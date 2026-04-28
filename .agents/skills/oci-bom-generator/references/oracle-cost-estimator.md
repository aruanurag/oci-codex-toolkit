# Oracle Cost Estimator Browser Workflow

Use this only when the user explicitly asks for Oracle Cost Estimator validation, import/export, or a customer-facing estimator session.

## Safety Gate

Before entering architecture details into oracle.com, confirm the exact action and data:

- destination: Oracle Cost Estimator at `https://www.oracle.com/cloud/costestimator.html`
- data: service names, SKUs, quantities, usage assumptions, and generated estimate files
- action: import, add items, save, export, or copy estimate results

Do not save favorites, export files, import files, or submit estimate details without that confirmation.

## Read-Only Inspection

1. Open the Cost Estimator page in the in-app browser.
2. Inspect the page structure and identify import/export or Advanced Search/SKU entry controls.
3. If the browser runtime is unavailable, mark `browser_validation.status` as `skipped` and continue with local BOM outputs.

## Validation Flow

1. Generate the local BOM JSON first.
2. Prefer import/export if Oracle exposes a compatible JSON flow.
3. If import is not compatible, use Advanced Search or SKU search and add items by part number.
4. Export Oracle's estimate as JSON or CSV when confirmed by the user.
5. Compare Oracle's monthly total to the local JSON total.
6. Record status:
   - `passed`: variance is within the agreed tolerance
   - `needs_review`: variance exceeds tolerance or a SKU could not be matched
   - `skipped`: browser, import, export, or confirmation was unavailable

## Default Tolerance

Use 1% total monthly variance as the default tolerance unless the user asks for a stricter threshold.
