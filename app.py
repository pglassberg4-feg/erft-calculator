import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="ERFT Advisor Platform", layout="wide")

st.markdown(
    "<h1 style='text-align: center;'>ERFT Financial Diagnostic Platform</h1>",
    unsafe_allow_html=True
)

st.divider()

# =========================
# SESSION STATE (EXCEL MODEL)
# =========================
if "committed" not in st.session_state:
    st.session_state.committed = pd.DataFrame({
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

if "draft" not in st.session_state:
    st.session_state.draft = st.session_state.committed.copy()

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
mode = st.radio(
    "View Mode",
    ["👤 Client View", "🧠 Advisor View", "🔮 What-If Mode"],
    horizontal=True
)

# =========================
# CONTROLS (EXCEL STYLE)
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("💾 Commit Changes"):
        st.session_state.committed = st.session_state.draft.copy()
        st.success("Changes saved")

with col2:
    if st.button("↩️ Reset Draft"):
        st.session_state.draft = st.session_state.committed.copy()
        st.warning("Draft reset")

with col3:
    auto_save = st.checkbox("Auto-save edits", value=False)

# =========================
# DATA EDITOR (STABLE GRID)
# =========================
st.subheader("Client Accounts")

edited = st.data_editor(
    st.session_state.draft,
    num_rows="dynamic",
    use_container_width=True,
    key="excel_grid",
    column_config={
        "Account": st.column_config.SelectboxColumn("Account", options=account_types),
        "TaxType": st.column_config.SelectboxColumn("Tax Type", options=tax_types),
        "AgeRule": st.column_config.SelectboxColumn("Age Rule", options=age_rules),
        "GrowthType": st.column_config.SelectboxColumn("Growth Type", options=growth_types),
        "Loan": st.column_config.SelectboxColumn("Loan", options=yesno),
        "Income": st.column_config.SelectboxColumn("Income", options=yesno),
        "Value": st.column_config.NumberColumn("Value ($)", min_value=0),
        "FeePct": st.column_config.NumberColumn("Fee (%)", min_value=0, max_value=10, step=0.1),
        "PenaltyPct": st.column_config.NumberColumn("Penalty (%)", min_value=0, max_value=20, step=0.5),
    }
)

if not edited.equals(st.session_state.draft):
    st.session_state.draft = edited.copy()
    if auto_save:
        st.session_state.committed = st.session_state.draft.copy()

df = st.session_state.draft.copy()

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

    fee_reduction = st.slider("Fee Reduction (%)", 0.0, 2.0, 0.5, 0.1)
    penalty_reduction = st.slider("Penalty Reduction (%)", 0.0, 10.0, 2.0, 0.5)

    sim = df.copy()
    sim["FeePct"] = (sim["FeePct"] - fee_reduction).clip(lower=0)
    sim["PenaltyPct"] = (sim["PenaltyPct"] - penalty_reduction).clip(lower=0)

    sim_erft = (sim["ERFT"] * sim["Value"]).sum() / total_value

    st.metric("Current ERFT", f"{weighted_erft:.2f}")
    st.metric("Simulated ERFT", f"{sim_erft:.2f}")
    st.metric("Improvement", f"{weighted_erft - sim_erft:.2f}")

# =========================
# CLIENT VIEW
# =========================
elif mode == "👤 Client View":

    st.subheader("Your Financial Overview")

    c1, c2, c3 = st.columns(3)

    c1.metric("Total Assets", f"${total_value:,.0f}")
    c2.metric("Efficiency Score", f"{weighted_erft:.1f}")
    c3.metric("Opportunity Gap", f"{gap:.1f}")

    if weighted_erft >= 11:
        msg = "Significant structural inefficiencies detected."
    elif weighted_erft >= 8:
        msg = "Meaningful optimization opportunities exist."
    elif weighted_erft >= 5:
        msg = "Moderate refinement potential."
    else:
        msg = "Relatively efficient structure."

    st.subheader("What This Means")
    st.write(msg)

    st.info(f"Highest friction account: {top['Account']}")

# =========================
# ADVISOR VIEW
# =========================
else:

    st.subheader("Advisor Dashboard")

    st.dataframe(df, use_container_width=True)

    st.metric("Weighted ERFT", f"{weighted_erft:.2f}")
    st.metric("Opportunity Gap", f"{gap:.2f}")

    st.subheader("ERFT by Account")

    fig, ax = plt.subplots()
    ax.bar(df["Account"], df["ERFT"])
    plt.xticks(rotation=45)
    st.pyplot(fig)

# =========================
# REPORT EXPORT
# =========================
st.divider()

report = f"""
ERFT CLIENT SUMMARY

Total Assets: ${total_value:,.0f}
Weighted ERFT: {weighted_erft:.2f}
Opportunity Gap: {gap:.2f}

Top Account: {top['Account']}
"""

st.text_area("Client Report", report, height=200)

st.download_button(
    "Download Report",
    report,
    file_name="ERFT_Report.txt"
)