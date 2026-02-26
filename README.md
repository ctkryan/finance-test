# Workday Journal Download Workflow

This repository includes everything needed to automate Workday journal extraction for month-end reporting.

## What you get

- A GitHub Actions workflow that runs automatically at **03:00 UTC on day 1 of every month**.
- A manual "Run workflow" option for ad-hoc reruns/backfills.
- A Python script that downloads journal entries from Workday Financial Accounting API.
- Output files in both JSON and CSV format.
- Uploaded workflow artifacts for downstream reporting.

---

## Step-by-step: make this work end-to-end

## 1) Add these files to your repository

You should have:

- `.github/workflows/workday-month-end-journals.yml`
- `scripts/download_workday_journals.py`

(Already included in this repo.)

## 2) Confirm the workflow is present on your default branch

Push your branch and merge it to your default branch (`main` or equivalent). GitHub scheduled workflows only run from the default branch.

## 3) Create Workday API credentials

From your Workday/security admin team, obtain:

1. **Base URL** (example: `https://impl.workday.com`)
2. **Tenant** (example: `my-company`)
3. **API token** with permission to read Financial Accounting journal entries

You need access to this endpoint pattern:

`/ccx/api/v1/{tenant}/financialAccounting/journalEntries`

## 4) Add required GitHub repository secrets

In GitHub:

1. Go to **Repository → Settings → Secrets and variables → Actions**.
2. Click **New repository secret**.
3. Add all three secrets exactly as named:
   - `WORKDAY_BASE_URL`
   - `WORKDAY_TENANT`
   - `WORKDAY_API_TOKEN`

If names do not match exactly, the workflow will fail.

## 5) Manually run once to verify setup

In GitHub:

1. Go to **Actions** tab.
2. Select **Workday Month-End Journal Download**.
3. Click **Run workflow**.
4. (Optional) Enter:
   - `year`: `2026`
   - `month`: `1`
5. Click **Run workflow**.

If you leave `year` and `month` empty, it automatically pulls the **previous month**.

## 6) Download the output artifact

After the run succeeds:

1. Open the workflow run.
2. Scroll to **Artifacts**.
3. Download artifact named like `workday-journals-<run_id>`.
4. Extract files:
   - `workday_journals_YYYY-MM.json`
   - `workday_journals_YYYY-MM.csv`

## 7) Verify monthly automation

The workflow schedule is set to:

```cron
0 3 1 * *
```

This means **03:00 UTC on the 1st day of each month**.

---

## Local run (optional, useful for troubleshooting)

### Prerequisites

- Python 3.11+ preferred (3.9+ generally works for this script)
- Network access to Workday API

### Commands

```bash
export WORKDAY_BASE_URL="https://impl.workday.com"
export WORKDAY_TENANT="your-tenant"
export WORKDAY_API_TOKEN="your-token"
python scripts/download_workday_journals.py --year 2026 --month 1 --output-dir output
```

If `--year` and `--month` are omitted, the script defaults to the previous month.

### See command options

```bash
python scripts/download_workday_journals.py --help
```

---

## Troubleshooting

- **`Missing required environment variables`**
  - Ensure all 3 env vars/secrets are set (`WORKDAY_BASE_URL`, `WORKDAY_TENANT`, `WORKDAY_API_TOKEN`).

- **`year and month must both be provided`**
  - Provide both together, or provide neither.

- **HTTP 401/403 from Workday**
  - Token is invalid/expired or missing permissions.

- **HTTP 404 on endpoint**
  - Base URL or tenant value is incorrect.

- **Workflow succeeds but no artifact files**
  - Check API response and script logs for empty dataset or query period mismatch.
