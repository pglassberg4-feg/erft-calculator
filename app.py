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

st.caption("Multi-account diagnostic + scenario planning + client presentation system")

st.divider()

# =========================
# SESSION STATE
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

if "working_df" not in st.session_state:
    st.session_state.working_df = st.session_state.base_df.copy()

# =========================
# SCORING ENGINE (SINGLE SOURCE OF TRUTH)
# =========================
def compute_erft(df):
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

    df = df.copy()

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

    df["TaxType"] = df["TaxType"].fillna("Pre-tax")
    df["GrowthType"] = df["GrowthType"].fillna("Fixed")
    df["AgeRule"] = df["AgeRule"].fillna("None")

    return df

# =========================
# SIDEBAR CONTROLS (WORKSTATION FEEL)
# =========================
st.sidebar.header("Workstation Controls")

view_mode = st.sidebar.radio(
    "Mode",
    ["Client View", "Advisor View", "What-If Engine"]
)

auto_save = st.sidebar.checkbox("Auto-save edits", value=False)

st.sidebar.divider()

st.sidebar.caption("Benchmark assumption: Efficient structure ≈ 4.0 ERFT")

# =========================
# EDITOR (WORKING LAYER)
# =========================
st.subheader("Client Portfolio Input")

edited = st.data_editor(
    st.session_state.working_df,
    num_rows="dynamic",
    use_container_width=True,
    key="grid"
)

if not edited.equals(st.session_state.working_df):
    st.session_state.working_df = edited.copy()
    if auto_save:
        st.session_state.base_df = st.session_state.working_df.copy()

# =========================
# ACTIVE DATA PIPELINE
# =========================
base_df = clean(st.session_state.working_df)
active_df = compute_erft(base_df)

# =========================
# PORTFOLIO METRICS
# =========================
total_value = active_df["Value"].sum()

weighted_erft = (
    (active_df["ERFT"] * active_df["Value"]).sum() / total_value
    if total_value > 0 else 0
)

opportunity_gap = max(0, weighted_erft - 4)

top = active_df.loc[active_df["ERFT"].idxmax()] if len(active_df) else None

# =========================
# WHAT-IF ENGINE
# =========================
if view_mode == "What-If Engine":

    st.subheader("Scenario Modeling")

    fee_shift = st.slider("Fee Reduction (%)", 0.0, 2.0, 0.5, 0.1)
    penalty_shift = st.slider("Penalty Reduction (%)", 0.0, 10.0, 2.0, 0.5)

    sim = base_df.copy()
    sim["FeePct"] = (sim["FeePct"] - fee_shift).clip(lower=0)
    sim["PenaltyPct"] = (sim["PenaltyPct"] - penalty_shift).clip(lower=0)

    sim = compute_erft(sim)

    sim_value = sim["Value"].sum()

    sim_weighted = (
        (sim["ERFT"] * sim["Value"]).sum() / sim_value
        if sim_value > 0 else 0
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Current ERFT", f"{weighted_erft:.2f}")
    col2.metric("Simulated ERFT", f"{sim_weighted:.2f}")
    col3.metric("Improvement", f"{weighted_erft - sim_weighted:.2f}")

    st.subheader("Scenario Impact Visualization")

    fig, ax = plt.subplots()
    ax.bar(["Current", "Scenario"], [weighted_erft, sim_weighted])
    st.pyplot(fig)

# =========================
# CLIENT VIEW (SIMPLIFIED STORY)
# =========================
elif view_mode == "Client View":

    st.subheader("Your Financial Overview")

    c1, c2, c3 = st.columns(3)

    c1.metric("Total Assets", f"${total_value:,.0f}")
    c2.metric("Efficiency Score", f"{weighted_erft:.2f}")
    c3.metric("Opportunity Gap", f"{opportunity_gap:.2f}")

    st.markdown("### What this means")

    if weighted_erft >= 11:
        msg = "Your structure shows significant inefficiencies."
    elif weighted_erft >= 8:
        msg = "There are meaningful optimization opportunities."
    elif weighted_erft >= 5:
        msg = "Moderate improvement potential exists."
    else:
        msg = "Your structure is relatively efficient."

    st.write(msg)

    if top is not None:
        st.info(f"Highest friction account: {top['Account']}")

# =========================
# ADVISOR VIEW (FULL DIAGNOSTICS)
# =========================
else:

    st.subheader("Advisor Diagnostics Panel")

    st.dataframe(active_df, use_container_width=True)

    col1, col2 = st.columns(2)

    col1.metric("Weighted ERFT", f"{weighted_erft:.2f}")
    col2.metric("Opportunity Gap", f"{opportunity_gap:.2f}")

    st.subheader("Account Friction Map")

    fig, ax = plt.subplots()
    ax.bar(active_df["Account"], active_df["ERFT"])
    plt.xticks(rotation=45)
    st.pyplot(fig)

    st.subheader("Fee vs Liquidity Pressure")

    fig2, ax2 = plt.subplots()
    ax2.scatter(active_df["FeePct"], active_df["PenaltyPct"], s=active_df["Value"]/10000)
    ax2.set_xlabel("Fee %")
    ax2.set_ylabel("Penalty %")
    st.pyplot(fig2)

# =========================
# INSIGHT ENGINE (CROSS-PORTFOLIO)
# =========================
st.divider()

st.subheader("Key Insight Engine")

if top is not None:
    st.success(
        f"Primary optimization target: {top['Account']} "
        f"(ERFT {top['ERFT']:.2f}, ${top['Value']:,.0f})"
    )

st.caption("ERFT measures structural efficiency across fees, taxes, growth type, and liquidity constraints.")
st.caption("Opportunity Gap = distance from efficient benchmark (4.0).")