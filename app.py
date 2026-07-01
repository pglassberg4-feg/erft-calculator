import streamlit as st
import pandas as pd

st.set_page_config(page_title="ERFT Multi-Account Dashboard", layout="wide")

st.title("🧠 ERFT Multi-Account Diagnostic System")

# -------------------------
# SESSION STATE INIT
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
# DATA EDITOR (MULTI-ACCOUNT INPUT)
# -------------------------
st.subheader("📥 Client Accounts")

edited_df = st.data_editor(
    st.session_state.data,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Account": st.column_config.SelectboxColumn("Account", options=account_types),
        "TaxType": st.column_config.SelectboxColumn("Tax Type", options=tax_types),
        "AgeRule": st.column_config.SelectboxColumn("Age Rule", options=age_rules),
        "GrowthType": st.column_config.SelectboxColumn("Growth Type", options=growth_types),
        "Loan": st.column_config.SelectboxColumn("Loan", options=yesno),
        "Income": st.column_config.SelectboxColumn("Income", options=yesno),
    }
)

st.session_state.data = edited_df

df = edited_df.copy()

# -------------------------
# SAFETY CHECK
# -------------------------
if df.empty:
    st.warning("Add at least one account to generate ERFT analysis.")
    st.stop()

# -------------------------
# SCORING FUNCTIONS
# -------------------------
def risk(g): 
    return 3 if g == "Variable" else 2 if g == "Indexed" else 1

def fees(f): 
    return 3 if f > 0.01 else 2 if f > 0.005 else 1

def taxes(t): 
    return 3 if t == "Pre-tax" else 2 if t == "After-tax" else 1

def flex(p, a): 
    if p > 0:
        return 3
    elif a != "None":
        return 2
    return 1

# -------------------------
# APPLY SCORING
# -------------------------
risk_scores = []
fee_scores = []
tax_scores = []
flex_scores = []
total_scores = []

for _, row in df.iterrows():
    r = risk(row.get("GrowthType","Fixed"))
    f = fees(row.get("FeePct",0))
    t = taxes(row.get("TaxType","Pre-tax"))
    fl = flex(row.get("PenaltyPct",0), row.get("AgeRule","None"))

    risk_scores.append(r)
    fee_scores.append(f)
    tax_scores.append(t)
    flex_scores.append(fl)

    total_scores.append(r + f + t + fl)

df["Risk"] = risk_scores
df["FeesScore"] = fee_scores
df["TaxScore"] = tax_scores
df["FlexScore"] = flex_scores
df["ERFT_Total"] = total_scores

# -------------------------
# PORTFOLIO METRICS
# -------------------------
df["Value"] = pd.to_numeric(df["Value"], errors="coerce").fillna(0)

total_value = df["Value"].sum()

weighted_erft = (
    (df["ERFT_Total"] * df["Value"]).sum() / total_value
    if total_value > 0 else 0
)

opportunity_gap = max(0, weighted_erft - 4)

# -------------------------
# RECOMMENDATION ENGINE
# -------------------------
if weighted_erft >= 11:
    rec = "🔴 URGENT: Major restructuring recommended"
elif weighted_erft >= 8:
    rec = "🟠 High priority review & repositioning opportunity"
elif weighted_erft >= 5:
    rec = "🟡 Moderate optimization potential"
else:
    rec = "🟢 Low friction household structure"

# -------------------------
# DASHBOARD
# -------------------------
st.divider()
st.subheader("📊 Household Summary")

col1, col2, col3 = st.columns(3)

col1.metric("Total Value", f"${total_value:,.0f}")
col2.metric("Weighted ERFT Score", f"{weighted_erft:.2f}")
col3.metric("Opportunity Gap", f"{opportunity_gap:.2f}")

st.subheader("🧠 Recommendation")
st.write(rec)

# -------------------------
# ACCOUNT BREAKDOWN
# -------------------------
st.subheader("📋 Account-Level ERFT Breakdown")
st.dataframe(df, use_container_width=True)

# -------------------------
# INSIGHT BOX
# -------------------------
st.subheader("🔎 Key Insight")

highest = df.loc[df["ERFT_Total"].idxmax()] if not df.empty else None

if highest is not None:
    st.info(
        f"Highest friction account: {highest['Account']} "
        f"(ERFT {highest['ERFT_Total']}) — primary optimization target."
    )

# -------------------------
# DOWNLOAD REPORT
# -------------------------
csv = df.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇️ Download Client ERFT Report (CSV)",
    data=csv,
    file_name="erft_report.csv",
    mime="text/csv"
)