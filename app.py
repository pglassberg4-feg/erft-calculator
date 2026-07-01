import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="ERFT Hardened System", layout="wide")

st.title("🧠 ERFT Multi-Account Diagnostic System (Hardened)")

# -------------------------
# DEFAULT DATA STRUCTURE
# -------------------------
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame({
        "Account": [],
        "Value": [],
        "TaxType": [],
        "AgeRule": [],
        "PenaltyPct": [],
        "FeePct": [],
        "GrowthType": [],
        "Loan": [],
        "Income": []
    })

# -------------------------
# OPTIONS
# -------------------------
account_types = ["401k","403b","457","IRA","Roth IRA","Brokerage","Annuity","Pension","CD","Cash"]
tax_types = ["Pre-tax","After-tax","Roth"]
age_rules = ["None","59.5","62","65","RMD"]
growth_types = ["Fixed","Indexed","Variable"]
yesno = ["Yes","No"]

# -------------------------
# INPUT TABLE
# -------------------------
st.subheader("📥 Client Accounts (Edit Table)")

df = st.data_editor(
    st.session_state.data,
    num_rows="dynamic",
    width="stretch",
    column_config={
        "Account": st.column_config.SelectboxColumn("Account", options=account_types),
        "TaxType": st.column_config.SelectboxColumn("Tax Type", options=tax_types),
        "AgeRule": st.column_config.SelectboxColumn("Age Rule", options=age_rules),
        "GrowthType": st.column_config.SelectboxColumn("Growth Type", options=growth_types),
        "Loan": st.column_config.SelectboxColumn("Loan", options=yesno),
        "Income": st.column_config.SelectboxColumn("Income", options=yesno),
        "Value": st.column_config.NumberColumn("Value ($)", min_value=0),
        "FeePct": st.column_config.NumberColumn("Fee %", min_value=0, max_value=1),
        "PenaltyPct": st.column_config.NumberColumn("Penalty %", min_value=0, max_value=1),
    }
)

st.session_state.data = df

# -------------------------
# SAFETY: EMPTY CHECK
# -------------------------
if df.empty:
    st.warning("Add at least one account to generate analysis.")
    st.stop()

# -------------------------
# DATA CLEANING (CRITICAL HARDENING LAYER)
# -------------------------
df = df.copy()

def safe_num(col):
    return pd.to_numeric(df[col], errors="coerce").fillna(0)

df["Value"] = safe_num("Value")
df["FeePct"] = safe_num("FeePct")
df["PenaltyPct"] = safe_num("PenaltyPct")

df["TaxType"] = df["TaxType"].fillna("Pre-tax")
df["GrowthType"] = df["GrowthType"].fillna("Fixed")
df["AgeRule"] = df["AgeRule"].fillna("None")

# -------------------------
# SCORING ENGINE (SAFE)
# -------------------------
def risk(g):
    return 3 if g == "Variable" else 2 if g == "Indexed" else 1

def fees(f):
    f = 0 if pd.isna(f) else f
    return 3 if f > 0.01 else 2 if f > 0.005 else 1

def taxes(t):
    return 3 if t == "Pre-tax" else 2 if t == "After-tax" else 1

def flex(p, a):
    p = 0 if pd.isna(p) else p
    if p > 0:
        return 3
    if a != "None":
        return 2
    return 1

risk_scores, fee_scores, tax_scores, flex_scores, totals = [], [], [], [], []

for _, row in df.iterrows():
    r = risk(row["GrowthType"])
    f = fees(row["FeePct"])
    t = taxes(row["TaxType"])
    fl = flex(row["PenaltyPct"], row["AgeRule"])

    risk_scores.append(r)
    fee_scores.append(f)
    tax_scores.append(t)
    flex_scores.append(fl)
    totals.append(r + f + t + fl)

df["Risk"] = risk_scores
df["FeesScore"] = fee_scores
df["TaxScore"] = tax_scores
df["FlexScore"] = flex_scores
df["ERFT_Total"] = totals

# -------------------------
# PORTFOLIO CALCS (SAFE)
# -------------------------
total_value = df["Value"].sum()

if total_value > 0:
    weighted_erft = (df["ERFT_Total"] * df["Value"]).sum() / total_value
else:
    weighted_erft = 0

opportunity_gap = max(0, weighted_erft - 4)

# -------------------------
# RECOMMENDATION ENGINE
# -------------------------
if weighted_erft >= 11:
    rec = "🔴 URGENT: Structural redesign required"
elif weighted_erft >= 8:
    rec = "🟠 High priority optimization opportunity"
elif weighted_erft >= 5:
    rec = "🟡 Moderate improvement potential"
else:
    rec = "🟢 Low-friction household structure"

# -------------------------
# MISSING DATA WARNING SYSTEM
# -------------------------
missing_flags = df[
    (df["Account"].isna()) |
    (df["Value"] == 0)
]

# -------------------------
# DASHBOARD
# -------------------------
st.divider()
st.subheader("📊 Household Summary")

c1, c2, c3 = st.columns(3)

c1.metric("Total Value", f"${total_value:,.0f}")
c2.metric("Weighted ERFT", f"{weighted_erft:.2f}")
c3.metric("Opportunity Gap", f"{opportunity_gap:.2f}")

st.subheader("🧠 Recommendation")
st.write(rec)

# -------------------------
# DATA QUALITY PANEL (HARDENING FEATURE)
# -------------------------
st.subheader("⚠️ Data Quality Check")

if len(missing_flags) > 0:
    st.error("Some accounts are missing key data (Account or Value). Fix before presenting.")
    st.dataframe(missing_flags, width="stretch")
else:
    st.success("All accounts are complete.")

# -------------------------
# ACCOUNT TABLE
# -------------------------
st.subheader("📋 Account Breakdown (ERFT Engine Output)")
st.dataframe(df, width="stretch")

# -------------------------
# TOP OPPORTUNITY TARGET
# -------------------------
if not df.empty:
    top = df.loc[df["ERFT_Total"].idxmax()]
    st.info(
        f"Top optimization target: {top['Account']} "
        f"(ERFT {top['ERFT_Total']}, ${top['Value']:,.0f})"
    )

# -------------------------
# EXPORT
# -------------------------
csv = df.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇️ Download ERFT Report (CSV)",
    data=csv,
    file_name="ERFT_Hardened_Report.csv",
    mime="text/csv"
)