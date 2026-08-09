import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Aggressive FIRE Tracker (15/70/15)",
    page_icon="⚡",
    layout="centered",
)

st.title("⚡ Aggressive FIRE Tracker")
st.caption("Hyper-Aggressive 15 / 70 / 15 Financial Allocation Model")

st.markdown("---")

# 1. Salary Input
st.subheader("1. Income Input")
salary = st.number_input(
    "Net Monthly Salary (₹)", min_value=0.0, value=143000.0, step=1000.0
)

# Target Calculations
target_survival = salary * 0.15
target_wealth = salary * 0.70
target_lifestyle = salary * 0.15

st.markdown("---")

# 2. Actual Spending Inputs
st.subheader("2. Enter Monthly Actuals")

col1, col2, col3 = st.columns(3)

with col1:
    actual_survival = st.number_input(
        "Survival & Debt (₹)", min_value=0.0, value=21450.0, step=500.0
    )

with col2:
    actual_wealth = st.number_input(
        "Wealth Engine (₹)", min_value=0.0, value=100100.0, step=1000.0
    )

with col3:
    actual_lifestyle = st.number_input(
        "Lifestyle (₹)", min_value=0.0, value=21450.0, step=500.0
    )

st.markdown("---")

# 3. Status Dashboard
st.subheader("3. Performance Dashboard")

# Category I: Survival & Debt
st.markdown("### I. Bare-Bones Survival & Debt (Target: 15%)")
m1, m2 = st.columns(2)
m1.metric("Target Limit", f"₹{target_survival:,.2f}")
m2.metric(
    "Actual Spend",
    f"₹{actual_survival:,.2f}",
    delta=f"₹{target_survival - actual_survival:,.2f}",
    delta_color="normal",
)

if actual_survival <= target_survival:
    st.success(
        f"✅ **ON TRACK:** Under budget by ₹{target_survival - actual_survival:,.2f}."
    )
else:
    st.error(
        f"⚠️ **OFF TRACK:** Overspent by ₹{actual_survival - target_survival:,.2f}."
    )

st.markdown("---")

# Category II: Wealth Engine
st.markdown("### II. Wealth Engine / Investments (Target: 70%)")
m3, m4 = st.columns(2)
m3.metric("Target Goal", f"₹{target_wealth:,.2f}")
m4.metric(
    "Actual Invested",
    f"₹{actual_wealth:,.2f}",
    delta=f"₹{actual_wealth - target_wealth:,.2f}",
    delta_color="normal",
)

if actual_wealth >= target_wealth:
    st.success(
        f"✅ **ON TRACK:** Invested ₹{actual_wealth - target_wealth:,.2f} more than target!"
    )
else:
    st.error(
        f"⚠️ **OFF TRACK:** Short by ₹{target_wealth - actual_wealth:,.2f} on investments."
    )

st.markdown("---")

# Category III: Lifestyle
st.markdown("### III. Lifestyle & Discretionary (Target: 15%)")
m5, m6 = st.columns(2)
m5.metric("Target Cap", f"₹{target_lifestyle:,.2f}")
m6.metric(
    "Actual Spend",
    f"₹{actual_lifestyle:,.2f}",
    delta=f"₹{target_lifestyle - actual_lifestyle:,.2f}",
    delta_color="normal",
)

if actual_lifestyle <= target_lifestyle:
    st.success(
        f"✅ **ON TRACK:** Under lifestyle cap by ₹{target_lifestyle - actual_lifestyle:,.2f}."
    )
else:
    st.error(
        f"⚠️ **OFF TRACK:** Overspent on lifestyle by ₹{actual_lifestyle - target_lifestyle:,.2f}."
    )

st.markdown("---")

# 4. Granular Target Breakdown Table
st.subheader("4. Granular Target Breakdown")

breakdown_data = [
    {
        "Category": "I. Survival & Debt",
        "Item": "Home Loan Interest / Minimum EMI",
        "Target %": "7.0%",
        "Target (₹)": salary * 0.07,
    },
    {
        "Category": "I. Survival & Debt",
        "Item": "Groceries & Kitchen Supplies",
        "Target %": "3.5%",
        "Target (₹)": salary * 0.035,
    },
    {
        "Category": "I. Survival & Debt",
        "Item": "Utilities (Bills, Wifi, Phone)",
        "Target %": "2.5%",
        "Target (₹)": salary * 0.025,
    },
    {
        "Category": "I. Survival & Debt",
        "Item": "Commute & Fuel",
        "Target %": "1.0%",
        "Target (₹)": salary * 0.01,
    },
    {
        "Category": "I. Survival & Debt",
        "Item": "Insurance (Health & Term)",
        "Target %": "1.0%",
        "Target (₹)": salary * 0.01,
    },
    {
        "Category": "II. Wealth Engine",
        "Item": "Core Equity SIPs (Flexi-Cap / Index)",
        "Target %": "45.0%",
        "Target (₹)": salary * 0.45,
    },
    {
        "Category": "II. Wealth Engine",
        "Item": "Satellite Equity (Small-Cap / Stocks)",
        "Target %": "15.0%",
        "Target (₹)": salary * 0.15,
    },
    {
        "Category": "II. Wealth Engine",
        "Item": "Emergency Buffer (FD / Liquid)",
        "Target %": "10.0%",
        "Target (₹)": salary * 0.10,
    },
    {
        "Category": "III. Lifestyle",
        "Item": "Dining Out & Food Delivery",
        "Target %": "4.0%",
        "Target (₹)": salary * 0.04,
    },
    {
        "Category": "III. Lifestyle",
        "Item": "Shopping & Personal Care",
        "Target %": "4.0%",
        "Target (₹)": salary * 0.04,
    },
    {
        "Category": "III. Lifestyle",
        "Item": "Travel & Vacation Sinking Fund",
        "Target %": "3.5%",
        "Target (₹)": salary * 0.035,
    },
    {
        "Category": "III. Lifestyle",
        "Item": "Fitness & Sports",
        "Target %": "2.5%",
        "Target (₹)": salary * 0.025,
    },
    {
        "Category": "III. Lifestyle",
        "Item": "Subscriptions & Hobbies",
        "Target %": "1.0%",
        "Target (₹)": salary * 0.01,
    },
]
st.markdown("---")
st.subheader("🔥 Financial Discipline Streak")
st.caption("Keep your lifestyle spending under the 15% cap to build your streak.")

# Simulating historical monthly data for the visual
# True = Kept lifestyle under 15% cap, False = Breached budget
historical_months = [True, True, False, True, True, True] 

# Evaluate the current month based on your live inputs
current_month_success = actual_lifestyle <= target_lifestyle
all_months = historical_months + [current_month_success]

# Render the visual streak
streak_html = "<div style='display: flex; gap: 10px; font-size: 24px;'>"
for success in all_months:
    if success:
        streak_html += "<span style='color: #4caf50;'>🟢</span>"
    else:
        streak_html += "<span style='color: #cf6679;'>🔴</span>"
streak_html += "</div>"

st.markdown(streak_html, unsafe_allow_html=True)

current_streak = 0
for success in reversed(all_months):
    if success:
        current_streak += 1
    else:
        break

st.write(f"**Current Streak:** {current_streak} Months 🔥")
df = pd.DataFrame(breakdown_data)
df["Target (₹)"] = df["Target (₹)"].map("₹{:,.2f}".format)

st.dataframe(df, use_container_width=True, hide_index=True)
