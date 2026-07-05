# Springer Capital — Referral Program Fraud Detection Pipeline

## Overview
This project loads the referral-program source data (leads, referrals,
transactions, rewards, and user info), cleans and joins it into a single
report, converts all timestamps to local time, and flags each referral
reward as **valid** or **invalid** based on a documented set of business
rules — helping the fraud/ops team quickly spot suspicious referral
rewards.

## Project Structure
```
.
├── data/                          # Input CSV files (7 source tables)
├── output/                        # Generated reports (created on run)
│   ├── data_profiling_report.csv
│   ├── referral_fraud_report.csv
│   └── data_dictionary.xlsx
├── profile_data.py                # Step 1: data profiling script
├── referral_pipeline.py           # Step 2: cleaning, joins, fraud logic
├── build_data_dictionary.py       # Generates the Excel data dictionary
├── Dockerfile
├── requirements.txt
└── README.md
```

## What the Pipeline Does
1. **Load** all 7 CSV source files.
2. **Clean**
   - Removes duplicate `user_logs` records (same user logged more than
     once with identical data).
   - Removes duplicate `lead_log` records.
   - Keeps only the latest `user_referral_logs` entry per referral
     (some referrals had dozens of retry/webhook log rows).
   - Extracts the numeric reward value from text like `"10 days"`.
3. **Time Adjustment** — every UTC timestamp is converted to the
   relevant local time zone (referrer's home club time zone for referral
   events, the transaction's own time zone for transaction events).
4. **Join** all tables into one wide reporting table.
5. **String formatting** — names are converted to Title Case; club and
   location names are left as-is per the assignment spec.
6. **`referral_source_category`** is derived per the required logic
   (Online / Offline / the linked lead's source category).
7. **Fraud / validity check** (`is_business_logic_valid`) — see below.
8. **Null handling** — the final report has no blank cells. Missing
   text/IDs show `"Unknown"`, a missing reward shows `0`, and a missing
   timestamp shows `"N/A"` (documented in the data dictionary).

## Business / Fraud Logic Summary
A referral reward is marked **valid** (`TRUE`) if either:
- It was successfully completed (`Berhasil`), has a reward > 0, has a
  linked **PAID / NEW** transaction that happened *after* and in the
  *same month* as the referral, the referrer's membership is still
  active, the referrer's account is not deleted, and the reward was
  actually granted; **or**
- It is still pending / failed (`Menunggu` / `Tidak Berhasil`) and has
  no reward assigned yet (nothing to flag).

Everything else is marked **invalid** (`FALSE`) — for example: a reward
was assigned but the status isn't successful, a reward exists with no
transaction behind it, or the transaction date is before the referral
was even created.

### Interesting finding
In this dataset, **no referral reward was ever marked as "granted"**
(`is_reward_granted` is `False` for every log entry) — meaning some
referrals show a "Berhasil" status and a reward amount, but the reward
was technically never disbursed. That's flagged as invalid and worth a
manual look by the business team.

## How to Run

### Option A — Locally with Python
```bash
pip install -r requirements.txt
python profile_data.py        # writes output/data_profiling_report.csv
python referral_pipeline.py   # writes output/referral_fraud_report.csv
python build_data_dictionary.py  # writes output/data_dictionary.xlsx
```

### Option B — With Docker
```bash
# Build the image
docker build -t springer-referral-pipeline .

# Run it, mounting your local data/ and output/ folders
docker run --rm \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/output:/app/output" \
  springer-referral-pipeline
```
The final report will appear on your **host machine** at
`output/referral_fraud_report.csv` (the report is written outside the
container via the mounted volume).

## Cloud Storage Note
This project does not upload the report anywhere by default. If you
wish to push `output/referral_fraud_report.csv` to cloud storage (S3 /
GCS / Azure Blob), set your credentials as **environment variables** or
use your cloud provider's credential-file mechanism — never hard-code
credentials in the script.

## Data Dictionary
See `output/data_dictionary.xlsx` for a business-friendly explanation
of every column in the final report.
