import streamlit as st
import pandas as pd

st.set_page_config(page_title="ERFT Case Design Calculator", layout="wide")

st.title("🧠 ERFT Case Design Calculator")

# -------------------------
# DROPDOWNS
# -------------------------
account_types = ["401k","403b","457","IRA","Roth IRA","Brokerage","Annuity","Pension","CD","Cash"]
tax_types = ["Pre-tax","After-tax","Roth"]
age_rules = ["None","59.5","62","65","RMD"]
growth_types = ["Fixed","Indexed","Variable"]
yesno = ["Yes","No"]

st.sidebar.header("Client Input")

account = st.sidebar.selectbox("Account Type", account_types)
value = st.sidebar.number_input("Value ($)", min_value=0.0, step=1000.0)

tax = st.sidebar.selectbox("Tax Type", tax_types)
age = st.sidebar.selectbox("Age Rule", age_rules)

penalty = st.sidebar.number_input("Penalty % (0-1)", min_value=0.0, max_value=1.0, step=0.01)
fee = st.sidebar.number_input("Fee % (0-1)", min_value=0.0, max_value=1.0, step=0.01)

growth = st.sidebar.selectbox("Growth Type", growth_types)
loan = st.sidebar.selectbox("Loan Option", yesno)
income = st.sidebar.selectbox("Income Option", yesno)

# -------------------------
# ERFT ENGINE
# -------------------------

def calc_risk(growth):
    return 3 if growth == "Variable" else 2 if growth == "Indexed" else 1

def calc_fees(fee):
    return 3 if fee > 0.01 else 2 if fee > 0.005 else 1

def calc_tax(tax):
    return 3 if tax == "Pre-tax" else 2 if tax == "After-tax" else 1

def calc_flex(penalty, age):
    if penalty > 0:
        return 3
    elif age != "None":
        return 2
    else:
        return 1

risk = calc_risk(growth)
fees = calc_fees(fee)
tax_score = calc_tax(tax)
flex = calc_flex(penalty, age)

total = risk + fees + tax_score + flex

# -------------------------
# BAND + RECOMMENDATION
# -------------------------

if total >= 11:
    band = "🔴 Critical"
    rec = "URGENT: Major restructuring conversation needed"
elif total >= 8:
    band = "🟠 High"
    rec = "Review & reposition opportunity"
elif total >= 5:
    band = "🟡 Moderate"
    rec = "Optimization potential exists"
else:
    band = "🟢 Low"
    rec = "System is relatively efficient"

opportunity_gap = max(0, total - 4)

# -------------------------
# DISPLAY
# -------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric("Risk", risk)
col2.metric("Fees", fees)
col3.metric("Taxes", tax_score)
col4.metric("Flexibility", flex)

st.subheader("Total ERFT Score")
st.metric("ERFT Score", total)

st.subheader("Classification")
st.write(band)

st.subheader("Auto Recommendation")
st.write(rec)

st.subheader("Opportunity Gap Score")
st.metric("Gap (vs target 4)", opportunity_gap)

# -------------------------
# CLIENT REPORT
# -------------------------

st.divider()
st.subheader("📄 Client Report (Printable View)")

report = f"""
Client Asset Summary

Account Type: {account}
Value: ${value:,.2f}

ERFT Breakdown:
- Risk: {risk}
- Fees: {fees}
- Taxes: {tax_score}
- Flexibility: {flex}

Total Score: {total}
Classification: {band}

Opportunity Gap: {opportunity_gap}

Recommendation:
{rec}
"""

st.text_area("Report", report, height=300)