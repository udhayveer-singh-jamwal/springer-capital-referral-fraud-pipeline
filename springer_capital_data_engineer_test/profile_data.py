"""
profile_data.py
----------------
Data profiling script for the Springer Capital referral program tables.
For every source table, this produces: data type, null count, % populated,
distinct value count, min/max value, and max actual string length.

Output: output/data_profiling_report.csv (one section per table)
"""

import pandas as pd
import os

DATA_DIR = "data"
OUTPUT_DIR = "output"
TABLES = [
    "lead_log.csv",
    "paid_transactions.csv",
    "referral_rewards.csv",
    "user_logs.csv",
    "user_referral_logs.csv",
    "user_referral_statuses.csv",
    "user_referrals.csv",
]


def profile_table(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    rows = []
    n = len(df)
    for col in df.columns:
        series = df[col]
        null_count = series.isnull().sum()
        pct_populated = round((n - null_count) / n * 100, 2) if n else 0
        distinct_count = series.nunique(dropna=True)
        non_null = series.dropna()
        try:
            min_val = non_null.min()
            max_val = non_null.max()
        except Exception:
            min_val, max_val = None, None
        try:
            max_len = non_null.astype(str).map(len).max()
        except Exception:
            max_len = None
        rows.append({
            "table_name": table_name,
            "column_name": col,
            "data_type": str(series.dtype),
            "null_count": int(null_count),
            "percentage_populated": pct_populated,
            "distinct_value_count": int(distinct_count),
            "min_value": min_val,
            "max_value": max_val,
            "max_actual_length": max_len,
        })
    return pd.DataFrame(rows)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_profiles = []
    for table_file in TABLES:
        table_name = table_file.replace(".csv", "")
        path = os.path.join(DATA_DIR, table_file)
        df = pd.read_csv(path)
        profile = profile_table(df, table_name)
        all_profiles.append(profile)
        print(f"Profiled {table_name}: {len(df)} rows, {len(df.columns)} columns")

    result = pd.concat(all_profiles, ignore_index=True)
    out_path = os.path.join(OUTPUT_DIR, "data_profiling_report.csv")
    result.to_csv(out_path, index=False)
    print(f"\nData profiling report saved to {out_path}")


if __name__ == "__main__":
    main()
