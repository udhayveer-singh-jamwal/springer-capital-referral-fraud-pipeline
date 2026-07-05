"""
referral_pipeline.py
---------------------
Springer Capital - Referral Program Data Pipeline & Fraud Detection

This script:
  1. Loads all source CSV files into DataFrames.
  2. Cleans the data (removes exact duplicate records, fixes data types,
     normalizes null representations).
  3. Converts all UTC timestamps to local time using each record's
     associated timezone.
  4. Joins the referral tables into a single denormalized reporting table.
  5. Applies string casing rules (Title Case, except club/location names).
  6. Derives `referral_source_category` based on business rules.
  7. Applies fraud-detection business logic to flag each referral reward
     as valid / invalid (`is_business_logic_valid`).
  8. Writes the final report to output/referral_fraud_report.csv

Run with:  python referral_pipeline.py
"""

import os
import pandas as pd
from zoneinfo import ZoneInfo

DATA_DIR = "data"
OUTPUT_DIR = "output"

pd.set_option("mode.chained_assignment", None)


def load_data():
    files = {
        "lead_log": "lead_log.csv",
        "paid_transactions": "paid_transactions.csv",
        "referral_rewards": "referral_rewards.csv",
        "user_logs": "user_logs.csv",
        "user_referral_logs": "user_referral_logs.csv",
        "user_referral_statuses": "user_referral_statuses.csv",
        "user_referrals": "user_referrals.csv",
    }
    data = {}
    for name, filename in files.items():
        data[name] = pd.read_csv(os.path.join(DATA_DIR, filename))
    return data


def clean_data(data: dict) -> dict:
    ul = data["user_logs"].drop(columns=["id"]).drop_duplicates(subset=["user_id"])
    ul["membership_expired_date"] = pd.to_datetime(ul["membership_expired_date"])
    data["user_logs"] = ul

    ll = data["lead_log"].drop_duplicates(subset=["lead_id"])
    data["lead_log"] = ll

    url = data["user_referral_logs"].copy()
    url["created_at"] = pd.to_datetime(url["created_at"], utc=True)
    url = url.sort_values("created_at").drop_duplicates(subset=["user_referral_id"], keep="last")
    data["user_referral_logs"] = url

    rr = data["referral_rewards"].copy()
    rr["num_reward_days"] = rr["reward_value"].astype(str).str.extract(r"(\d+)").astype(float)
    data["referral_rewards"] = rr

    ur = data["user_referrals"].copy()
    ur["referral_at"] = pd.to_datetime(ur["referral_at"], utc=True)
    ur["updated_at"] = pd.to_datetime(ur["updated_at"], utc=True)
    data["user_referrals"] = ur

    pt = data["paid_transactions"].copy()
    pt["transaction_at"] = pd.to_datetime(pt["transaction_at"], utc=True)
    data["paid_transactions"] = pt

    return data


def to_local(utc_series: pd.Series, tz_series: pd.Series) -> pd.Series:
    out = []
    for ts, tz in zip(utc_series, tz_series):
        if pd.isnull(ts) or pd.isnull(tz):
            out.append(pd.NaT)
            continue
        try:
            out.append(ts.tz_convert(ZoneInfo(tz)).tz_localize(None))
        except Exception:
            out.append(ts.tz_localize(None))
    return pd.Series(out, index=utc_series.index)


def title_case(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.title().replace({"Nan": None})


def derive_source_category(row):
    if row["referral_source"] == "User Sign Up":
        return "Online"
    if row["referral_source"] == "Draft Transaction":
        return "Offline"
    if row["referral_source"] == "Lead":
        return row.get("lead_source_category")
    return None


def is_valid_referral(row) -> bool:
    reward_days = row["num_reward_days"]
    has_reward = pd.notnull(reward_days) and reward_days > 0
    status = row["referral_status"]
    has_txn = pd.notnull(row["transaction_id"])
    txn_status_paid = row["transaction_status"] == "PAID"
    txn_type_new = row["transaction_type"] == "NEW"
    txn_after_referral = (
        pd.notnull(row["transaction_at"]) and pd.notnull(row["referral_at"])
        and row["transaction_at"] > row["referral_at"]
    )
    same_month = (
        pd.notnull(row["transaction_at"]) and pd.notnull(row["referral_at"])
        and row["transaction_at"].year == row["referral_at"].year
        and row["transaction_at"].month == row["referral_at"].month
    )
    membership_active = (
        pd.notnull(row["membership_expired_date"]) and pd.notnull(row["transaction_at"])
        and row["membership_expired_date"].date() >= row["transaction_at"].date()
    )
    referrer_not_deleted = row.get("referrer_is_deleted") is False
    reward_granted = row.get("is_reward_granted") is True

    valid_1 = (
        has_reward and status == "Berhasil" and has_txn and txn_status_paid
        and txn_type_new and txn_after_referral and same_month
        and membership_active and referrer_not_deleted and reward_granted
    )
    valid_2 = status in ("Menunggu", "Tidak Berhasil") and not has_reward

    return bool(valid_1 or valid_2)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    data = load_data()
    data = clean_data(data)

    ur = data["user_referrals"]
    ul = data["user_logs"]
    pt = data["paid_transactions"]
    rr = data["referral_rewards"]
    urs = data["user_referral_statuses"]
    url = data["user_referral_logs"]
    ll = data["lead_log"]

    df = ur.copy()

    referrer_cols = ul.rename(columns={
        "user_id": "referrer_id", "name": "referrer_name",
        "phone_number": "referrer_phone_number", "homeclub": "referrer_homeclub",
        "timezone_homeclub": "referrer_timezone",
        "membership_expired_date": "membership_expired_date",
        "is_deleted": "referrer_is_deleted",
    })[["referrer_id", "referrer_name", "referrer_phone_number",
        "referrer_homeclub", "referrer_timezone",
        "membership_expired_date", "referrer_is_deleted"]]
    df = df.merge(referrer_cols, on="referrer_id", how="left")

    df = df.merge(
        rr.rename(columns={"id": "referral_reward_id"})[["referral_reward_id", "num_reward_days"]],
        on="referral_reward_id", how="left",
    )

    df = df.merge(
        urs.rename(columns={"id": "user_referral_status_id", "description": "referral_status"})[
            ["user_referral_status_id", "referral_status"]
        ],
        on="user_referral_status_id", how="left",
    )

    df = df.merge(pt, on="transaction_id", how="left")

    df = df.merge(
        url.rename(columns={"user_referral_id": "referral_id", "created_at": "reward_granted_at_utc"})[
            ["referral_id", "is_reward_granted", "reward_granted_at_utc"]
        ],
        on="referral_id", how="left",
    )
    df.loc[df["is_reward_granted"] != True, "reward_granted_at_utc"] = pd.NaT

    df = df.merge(
        ll.rename(columns={"lead_id": "referee_id", "source_category": "lead_source_category"})[
            ["referee_id", "lead_source_category"]
        ],
        on="referee_id", how="left",
    )

    df["referral_at"] = to_local(df["referral_at"], df["referrer_timezone"])
    df["updated_at"] = to_local(df["updated_at"], df["referrer_timezone"])
    df["transaction_at"] = to_local(df["transaction_at"], df["timezone_transaction"])
    df["reward_granted_at"] = to_local(df["reward_granted_at_utc"], df["referrer_timezone"])

    df["referral_source_category"] = df.apply(derive_source_category, axis=1)

    df["referrer_name"] = title_case(df["referrer_name"])
    df["referee_name"] = title_case(df["referee_name"])

    df["is_business_logic_valid"] = df.apply(is_valid_referral, axis=1)

    df.insert(0, "referral_details_id", range(101, 101 + len(df)))

    final_cols = [
        "referral_details_id", "referral_id", "referral_source",
        "referral_source_category", "referral_at",
        "referrer_id", "referrer_name", "referrer_phone_number", "referrer_homeclub",
        "referee_id", "referee_name", "referee_phone",
        "referral_status", "num_reward_days",
        "transaction_id", "transaction_status", "transaction_at",
        "transaction_location", "transaction_type",
        "updated_at", "reward_granted_at",
        "is_business_logic_valid",
    ]
    report = df[final_cols].copy()

    # --- Handling nulls: the task requires no nulls in the final report.
    # Rather than dropping rows (which would destroy legitimate referrals
    # that simply have no transaction/reward yet), we make missingness
    # explicit with documented placeholder values:
    #   - text/id fields missing upstream data -> "Unknown"
    #   - reward day count with no reward assigned -> 0
    #   - timestamps with no applicable event -> "N/A"
    str_cols = report.select_dtypes(include="object").columns
    report[str_cols] = report[str_cols].fillna("Unknown")

    report["num_reward_days"] = report["num_reward_days"].fillna(0).astype(int)

    for ts_col in ["referral_at", "updated_at", "transaction_at", "reward_granted_at"]:
        report[ts_col] = report[ts_col].astype(object).where(report[ts_col].notnull(), "N/A")

    out_path = os.path.join(OUTPUT_DIR, "referral_fraud_report.csv")
    report.to_csv(out_path, index=False)

    print(f"Pipeline complete. {len(report)} rows written to {out_path}")
    print(report["is_business_logic_valid"].value_counts())


if __name__ == "__main__":
    main()
