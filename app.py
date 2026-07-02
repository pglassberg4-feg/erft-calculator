import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="ERFT Advisor Workstation", layout="wide")

st.markdown(
    "<h1 style='text-align:center;'>ERFT Advisor Workstation</h1>",
    unsafe_allow_html=True
)

st.caption("Stable Excel-style advisor system (multi-account + scenario modeling + client presentation)")

st.divider()

# =========================
# SESSION STATE (CRITICAL FIX: CLEAN SEPARATION)
# =========================
if "base_df" not in st.session_state:
    st.session_state.base_df = pd.DataFrame({
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

if "draft_df" not in st.session_state:
    st.session_state.draft_df = st.session_state.base_df.copy()

# =========================
# CONSTANTS
# =========================
account_types = ["401k","403b","457","IRA","Roth IRA","Brokerage","Annuity","Pension","CD","Cash"]
tax_types = ["Pre-tax","After-tax","Roth"]
age_rules = ["None","59.5","62","65","RMD"]
growth_types = ["Fixed","Indexed","Variable"]
yesno = ["Yes","No"]

BENCHMARK = 4.0

# =========================
# SCORING ENGINE (SINGLE SOURCE OF TRUTH)
# =========================
def compute_erft(df):
    df = df.copy()

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

    df["ERFT"] = [
        risk(r["GrowthType"]) +
        fees(r["FeePct"]) +
        taxes(r["TaxType"]) +
        flex(r["PenaltyPct"], r["AgeRule"])
        for _, r in df.iterrows()
    ]

    return df

# =========================
# CLEAN DATA
# =========================
def clean(df):
    df = df.copy()

    df["Value"] = pd.to_numeric(df["Value"], errors="coerce").fillna(0)
    df["FeePct"] = pd.to_numeric(df["FeePct"], errors="coerce").fillna(0)
    df["PenaltyPct"] = pd.to_numeric(df["PenaltyPct"], errors="coerce").fillna(0)

    df["Account"] = df["Account"].fillna("")
    df["TaxType"] = df["TaxType"].fillna("Pre-tax")
    df["AgeRule"] = df["AgeRule"].fillna("None")
    df["GrowthType"] = df["GrowthType"].fillna("Fixed")
    df["Loan"] = df["Loan"].fillna("No")
    df["Income"] = df["Income"].fillna("No")

    return df

# =========================
# VIEW MODE
# =========================
mode = st.radio(
    "View Mode",
    ["Client View", "Advisor View", "What-If Mode"],
    horizontal=True
)

# =========================
# EXCEL-STYLE EDITOR (STABLE STATE MODEL)
# =========================
st.subheader("Client Accounts (Excel-Style Input)")

edited = st.data_editor(
    st.session_state.draft_df,
    num_rows="dynamic",
    use_container_width=True,
    key="stable_editor",
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

# ONLY update draft if change detected (prevents rerun clearing bug)
if not edited.equals(st.session_state.draft_df):
    st.session_state.draft_df = edited.copy()

# =========================
# COMMIT / RESET CONTROLS
# =========================
col1, col2 = st.columns(2)

with col1:
    if st.button("💾 Commit Changes"):
        st.session_state.base_df = st.session_state.draft_df.copy()
        st.success("Saved successfully")

with col2:
    if st.button("↩️ Reset Draft"):
        st.session_state.draft_df = st.session_state.base_df.copy()
        st.warning("Draft reset")

# =========================
# ACTIVE DATA PIPELINE (SINGLE SOURCE OF TRUTH)
# =========================
df = clean(st.session_state.draft_df)
df = compute_erft(df)

total_value = df["Value"].sum()

weighted_erft = (
    (df["ERFT"] * df["Value"]).sum() / total_value
    if total_value > 0 else 0
)

opportunity_gap = max(0, weighted_erft - BENCHMARK)

top = df.loc[df["ERFT"].idxmax()] if len(df) > 0 else None

# =========================
# WHAT-IF MODE (FIXED ENGINE)
# =========================
if mode == "What-If Mode":

    st.subheader("Scenario Simulator")

    fee_shift = st.slider("Fee Reduction (%)", 0.0, 2.0, 0.5, 0.1)
    penalty_shift = st.slider("Penalty Reduction (%)", 0.0, 10.0, 2.0, 0.5)

    sim = df.copy()

    sim["FeePct"] = (sim["FeePct"] - fee_shift).clip(lower=0)
    sim["PenaltyPct"] = (sim["PenaltyPct"] - penalty_shift).clip(lower=0)

    sim = compute_erft(sim)

    sim_value = sim["Value"].sum()

    sim_weighted = (
        (sim["ERFT"] * sim["Value"]).sum() / sim_value
        if sim_value > 0 else 0
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Current Score", f"{weighted_erft:.2f}")
    col2.metric("Scenario Score", f"{sim_weighted:.2f}")
    col3.metric("Improvement", f"{weighted_erft - sim_weighted:.2f}")

    fig, ax = plt.subplots()
    ax.bar(["Current", "Scenario"], [weighted_erft, sim_weighted])
    st.pyplot(fig)

# =========================
# CLIENT VIEW (SIMPLIFIED STORY)
# =========================
elif mode == "Client View":

    st.subheader("Financial Overview")

    c1, c2, c3 = st.columns(3)

    c1.metric("Total Assets", f"${total_value:,.0f}")
    c2.metric("Efficiency Score", f"{weighted_erft:.2f}")
    c3.metric("Opportunity Gap", f"{opportunity_gap:.2f}")

    st.markdown("### What This Means")

    st.markdown("""
**Efficiency Score**
> Measures how optimized your financial structure is based on fees, taxes, growth type, and access to money.

**Opportunity Gap**
> Shows how far your current structure is from an efficient baseline (4.0).
""")

    if top is not None:
        st.info(f"Highest friction account: {top['Account']}")

# =========================
# ADVISOR VIEW
# =========================
else:

    st.subheader("Advisor Dashboard")

    st.dataframe(df, use_container_width=True)

    col1, col2 = st.columns(2)

    col1.metric("Weighted ERFT", f"{weighted_erft:.2f}")
    col2.metric("Opportunity Gap", f"{opportunity_gap:.2f}")

    st.subheader("ERFT by Account")

    fig, ax = plt.subplots()
    ax.bar(df["Account"], df["ERFT"])
    plt.xticks(rotation=45)
    st.pyplot(fig)

# =========================
# INSIGHT ENGINE
# =========================
st.divider()

st.subheader("Key Insight")

if top is not None:
    st.success(
        f"Primary optimization target: {top['Account']} "
        f"(ERFT {top['ERFT']:.2f}, ${top['Value']:,.0f})"
    )

st.caption("ERFT Score = structural efficiency across fees, taxes, growth type, and liquidity constraints.")
st.caption("Opportunity Gap = distance from efficient baseline (4.0).")