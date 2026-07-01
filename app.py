import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="ERFT Advisor Platform", layout="wide")

# =========================
# HEADER / BRANDING
# =========================
st.markdown(
    "<h1 style='text-align: center;'>ERFT Financial Diagnostic Platform</h1>",
    unsafe_allow_html=True
)

st.divider()

# =========================
# SESSION STATE INIT
# =========================
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

# =========================
# OPTIONS
# =========================
account_types = ["401k","403b","457","IRA","Roth IRA","Brokerage","Annuity","Pension","CD","Cash"]
tax_types = ["Pre-tax","After-tax","Roth"]
age_rules = ["None","59.5","62","65","RMD"]
growth_types = ["Fixed","Indexed","Variable"]
yesno = ["Yes","No"]

# =========================
# VIEW MODE
# =========================
mode = st.radio("View Mode", ["👤 Client View", "🧠 Advisor View", "🔮 What-If Mode"], horizontal=True)

# =========================
# DATA INPUT
# =========================
st.subheader("Client Accounts")

df = st.data_editor(
    st.session_state.data,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Value": st.column_config.NumberColumn("Value ($)", min_value=0),
        "FeePct": st.column_config.NumberColumn("Fee (%)", min_value=0, max_value=10, step=0.1),
        "PenaltyPct": st.column_config.NumberColumn("Penalty (%)", min_value=0, max_value=20, step=0.5),
        "Account": st.column_config.SelectboxColumn("Account", options=account_types),
        "TaxType": st.column_config.SelectboxColumn("Tax Type", options=tax_types),
        "AgeRule": st.column_config.SelectboxColumn("Age Rule", options=age_rules),
        "GrowthType": st.column_config.SelectboxColumn("Growth Type", options=growth_types),
        "Loan": st.column_config.SelectboxColumn("Loan", options=yesno),
        "Income": st.column_config.SelectboxColumn("Income", options=yesno),
    }
)

st.session_state.data = df.copy()

if df.empty:
    st.warning("Add at least one account.")
    st.stop()

# =========================
# CLEAN DATA
# =========================
df["Value"] = pd.to_numeric(df["Value"], errors="coerce").fillna(0)
df["FeePct"] = pd.to_numeric(df["FeePct"], errors="coerce").fillna(0)
df["PenaltyPct"] = pd.to_numeric(df["PenaltyPct"], errors="coerce").fillna(0)

df["TaxType"] = df["TaxType"].fillna("Pre-tax")
df["GrowthType"] = df["GrowthType"].fillna("Fixed")
df["AgeRule"] = df["AgeRule"].fillna("None")

# =========================
# SCORING ENGINE
# =========================
def risk(g):
    return 3 if g == "Variable" else 2 if g == "Indexed" else 1

def fees(f):
    return 3 if f >= 2 else 2 if f >= 1 else 1

def taxes(t):
    return 3 if t == "Pre-tax" else 2 if t == "After-tax" else 1

def flex(p, a):
    score = 3 if p >= 10 else 2 if p >= 3 else 1
    if a != "None":
        score += 0.5
    return min(score, 3)

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

df["ERFT"] = totals
df["Risk"] = risk_scores
df["Fees"] = fee_scores
df["Taxes"] = tax_scores
df["Flex"] = flex_scores

# =========================
# PORTFOLIO METRICS
# =========================
total_value = df["Value"].sum()
weighted_erft = (df["ERFT"] * df["Value"]).sum() / total_value if total_value > 0 else 0
gap = max(0, weighted_erft - 4)

top = df.loc[df["ERFT"].idxmax()]

# =========================
# WHAT-IF MODE
# =========================
if mode == "🔮 What-If Mode":

    st.subheader("Scenario Simulator")

    reduce_fees = st.slider("Simulated Fee Reduction (%)", 0.0, 2.0, 0.5, 0.1)
    reduce_penalty = st.slider("Simulated Liquidity Improvement (%)", 0.0, 10.0, 2.0, 0.5)

    sim_df = df.copy()
    sim_df["FeePct"] = (sim_df["FeePct"] - reduce_fees).clip(lower=0)
    sim_df["PenaltyPct"] = (sim_df["PenaltyPct"] - reduce_penalty).clip(lower=0)

    sim_erft = (sim_df["ERFT"] * sim_df["Value"]).sum() / total_value

    st.metric("Current ERFT", f"{weighted_erft:.2f}")
    st.metric("Simulated ERFT", f"{sim_erft:.2f}")
    st.metric("Improvement", f"{weighted_erft - sim_erft:.2f}")

# =========================
# CLIENT VIEW
# =========================
elif mode == "👤 Client View":

    st.subheader("Your Financial Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Assets", f"${total_value:,.0f}")
    col2.metric("Financial Efficiency Score", f"{weighted_erft:.1f}")
    col3.metric("Opportunity Gap", f"{gap:.1f}")

    if weighted_erft >= 11:
        msg = "Your structure has significant inefficiencies."
    elif weighted_erft >= 8:
        msg = "There are meaningful optimization opportunities."
    elif weighted_erft >= 5:
        msg = "Your plan is generally solid with refinement potential."
    else:
        msg = "Your structure is relatively efficient."

    st.subheader("What This Means")
    st.write(msg)

    st.info(f"Highest friction account: {top['Account']}")

# =========================
# ADVISOR VIEW + CHARTS
# =========================
else:

    st.subheader("Advisor Dashboard")

    st.dataframe(df, use_container_width=True)

    st.metric("Weighted ERFT", f"{weighted_erft:.2f}")
    st.metric("Opportunity Gap", f"{gap:.2f}")

    st.subheader("ERFT Distribution")

    fig1, ax1 = plt.subplots()
    ax1.bar(df["Account"], df["ERFT"])
    plt.xticks(rotation=45)
    st.pyplot(fig1)

    st.subheader("Fee vs Penalty Exposure")

    fig2, ax2 = plt.subplots()
    ax2.scatter(df["FeePct"], df["PenaltyPct"], s=df["Value"]/10000)
    ax2.set_xlabel("Fee %")
    ax2.set_ylabel("Penalty %")
    st.pyplot(fig2)

# =========================
# PDF REPORT (AUTO GENERATION)
# =========================
st.divider()
st.subheader("Client Report Export")

report_text = f"""
ERFT Financial Summary

Total Assets: ${total_value:,.0f}
Weighted Score: {weighted_erft:.2f}
Opportunity Gap: {gap:.2f}

Highest Friction Account: {top['Account']}
"""

st.text_area("Report Preview", report_text, height=200)

st.download_button(
    "Download Report (TXT)",
    report_text,
    file_name="ERFT_Client_Report.txt"
)