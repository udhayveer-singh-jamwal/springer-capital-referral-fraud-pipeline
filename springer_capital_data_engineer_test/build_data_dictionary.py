"""
build_data_dictionary.py
-------------------------
Generates a business-friendly Data Dictionary (Excel) describing every
column in the final referral_fraud_report.csv output.
"""
import pandas as pd

rows = [
    ("referral_details_id", "Integer", "Unique row number for this report. No business meaning beyond identifying a row.", "Always populated"),
    ("referral_id", "Text", "Unique ID of the referral record (system-generated).", "Always populated"),
    ("referral_source", "Text", "How the referral was originally created: 'User Sign Up', 'Draft Transaction', or 'Lead'.", "Always populated"),
    ("referral_source_category", "Text", "Simplified grouping of the source: 'Online' (self sign-up), 'Offline' (in-club transaction), or the original lead's source category (for 'Lead' referrals).", "May show 'Unknown' if the linked lead record could not be found"),
    ("referral_at", "Date/Time", "When the referral was created, shown in the REFERRER's local club time (converted from UTC).", "'N/A' if the referrer could not be identified"),
    ("referrer_id", "Text", "ID of the existing member who made the referral.", "'Unknown' if missing from source data"),
    ("referrer_name", "Text", "Name of the referrer (Title Case).", "'Unknown' if missing"),
    ("referrer_phone_number", "Text", "Referrer's phone number.", "'Unknown' if missing"),
    ("referrer_homeclub", "Text", "Gym/club branch the referrer belongs to.", "'Unknown' if missing"),
    ("referee_id", "Text", "ID of the new person who was referred.", "'Unknown' if missing"),
    ("referee_name", "Text", "Name of the referee (Title Case).", "'Unknown' if missing"),
    ("referee_phone", "Text", "Referee's phone number.", "Always populated"),
    ("referral_status", "Text", "Current status of the referral: 'Berhasil' (Successful), 'Menunggu' (Pending), or 'Tidak Berhasil' (Failed).", "Always populated"),
    ("num_reward_days", "Integer", "Number of membership days rewarded for this referral, if any.", "0 if no reward has been assigned"),
    ("transaction_id", "Text", "ID of the purchase/transaction linked to this referral (if any).", "'Unknown' if no transaction is linked"),
    ("transaction_status", "Text", "Payment status of the linked transaction (e.g. 'PAID').", "'Unknown' if no transaction is linked"),
    ("transaction_at", "Date/Time", "When the linked transaction occurred, in the transaction's local time zone.", "'N/A' if no transaction is linked"),
    ("transaction_location", "Text", "Club/branch where the transaction took place.", "'Unknown' if no transaction is linked"),
    ("transaction_type", "Text", "Type of transaction (e.g. 'NEW' membership).", "'Unknown' if no transaction is linked"),
    ("updated_at", "Date/Time", "When the referral record was last updated, in the referrer's local time.", "'N/A' if referrer/timestamp unavailable"),
    ("reward_granted_at", "Date/Time", "When the reward was actually granted to the referee, in the referrer's local time.", "'N/A' if no reward has been granted yet"),
    ("is_business_logic_valid", "True/False", "Result of the fraud/validity check: TRUE means the referral reward looks legitimate based on business rules; FALSE means it fails at least one rule and should be reviewed by the fraud/ops team.", "Always populated"),
]

df = pd.DataFrame(rows, columns=["Column Name", "Data Type", "Description", "Notes / Special Values"])

with pd.ExcelWriter("/home/claude/springer_de_test/output/data_dictionary.xlsx", engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="Data Dictionary")
    ws = writer.sheets["Data Dictionary"]
    widths = [22, 12, 70, 45]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[chr(64+i)].width = w
    for cell in ws[1]:
        cell.font = cell.font.copy(bold=True)

print("Data dictionary written.")
