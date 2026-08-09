import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import calendar

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="FIRE Dashboard", page_icon="🔥", layout="centered", initial_sidebar_state="expanded")

# --- CUSTOM CSS (Groww Dark Theme Replica) ---
st.markdown("""
<style>
    .main {background-color: #0b0c10;}
    .metric-card {
        background-color: #18191d;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #2d2e32;
        margin-bottom: 20px;
    }
    .net-pl {font-size: 28px; font-weight: 700; color: #4caf50; margin-bottom: 5px;}
    .sub-metric {display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px dashed #2d2e32;}
    .sub-metric:last-child {border-bottom: none;}
    .sub-text {color: #a0a0a0; font-size: 14px;}
    .sub-val {color: #e0e0e0; font-size: 14px; font-weight: 600;}
    .val-negative {color: #ff5722;}
    
    .month-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-top: 20px;
        padding: 20px 0;
        border-top: 1px solid #2d2e32;
    }
    .month-box {
        padding: 15px 5px;
        border-radius: 8px;
        text-align: center;
        font-weight: 700;
        font-size: 13px;
        border: 1px solid #2d2e32;
        color: #555;
    }
    .month-active-success {background-color: rgba(76, 175, 80, 0.15); color: #4caf50; border: 1px solid #4caf50;}
    .month-active-danger {background-color: rgba(255, 87, 34, 0.15); color: #ff5722; border: 1px solid #ff5722;}
    
    .order-row {
        display: flex; justify-content: space-between; 
        padding: 15px 0; border-bottom: 1px solid #2d2e32;
    }
    .order-title {font-weight: 600; color: #e0e0e0; font-size: 15px;}
    .order-sub {color: #777; font-size: 12px; margin-top: 4px;}
    .order-val {font-weight: 700; font-size: 15px; text-align: right;}
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE (Temporary DB for Demo) ---
if 'activities' not in st.session_state:
    st.session_state.activities = pd.DataFrame([
        {"Date": date(2026, 4, 15), "Category": "Lifestyle", "Activity": "Weekend Trip", "Cost": 12000},
        {"Date": date(2026, 5, 10), "Category": "Lifestyle", "Activity": "Dining Out", "Cost": 4500},
        {"Date": date(2026, 5, 22), "Category": "Lifestyle", "Activity": "Concert Tickets", "Cost": 8000},
        {"Date": date(2026, 6, 5), "Category": "Lifestyle", "Activity": "Shopping", "Cost": 16000}, # Over budget month
        {"Date": date(2026, 7, 18), "Category": "Lifestyle", "Activity": "Gym Yearly", "Cost": 14000},
        {"Date": date(2026, 8, 2), "Category": "Lifestyle", "Activity": "Groceries (Fancy)", "Cost": 3000},
    ])

# --- DATE LOGIC ENGINE ---
TODAY = date(2026, 8, 10) # Locked to your current timeline

def get_fy_dates(year):
    return date(year, 4, 1), date(year + 1, 3, 31)

st.sidebar.title("⚙️ Filters")
salary = st.sidebar.number_input("Net Monthly Salary (₹)", value=143000, step=1000)
st.sidebar.markdown("---")

date_preset = st.sidebar.selectbox("Date Range", [
    "Current financial year (2026-2027)",
    "Previous financial year (2025-2026)",
    "Last quarter",
    "Last 30 days",
    "Last trading day",
    "Custom"
])

# Calculate Date Ranges based on Dropdown
if date_preset == "Current financial year (2026-2027)":
    start_date, end_date = date(2026, 4, 1), TODAY
elif date_preset == "Previous financial year (2025-2026)":
    start_date, end_date = get_fy_dates(2025)
elif date_preset == "Last quarter":
    start_date, end_date = date(2026, 4, 1), date(2026, 6, 30) # Q1 FY27
elif date_preset == "Last 30 days":
    start_date, end_date = TODAY - timedelta(days=30), TODAY
elif date_preset == "Last trading day":
    start_date, end_date = TODAY - timedelta(days=3), TODAY - timedelta(days=3) # Assuming Friday
else:
    custom_dates = st.sidebar.date_input("Select Custom Range", [date(2026, 4, 1), TODAY])
    if len(custom_dates) == 2:
        start_date, end_date = custom_dates[0], custom_dates[1]
    else:
        start_date, end_date = custom_dates[0], custom_dates[0]

# Formatting the date display header
date_str = f"{start_date.strftime('%d %b \'%y')} - {end_date.strftime('%d %b \'%y')}"

# --- DATA FILTERING ---
df = st.session_state.activities
mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
f_df = df.loc[mask]

# Budget Math
months_in_range = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
target_lifestyle_monthly = salary * 0.15
total_lifestyle_target = target_lifestyle_monthly * months_in_range
total_lifestyle_spent = f_df['Cost'].sum()
net_status = total_lifestyle_target - total_lifestyle_spent

# --- MAIN UI ---
st.markdown(f"<div style='text-align: center; color: #a0a0a0; margin-bottom: 10px;'>🗓️ {date_str}</div>", unsafe_allow_html=True)

# 1. TOP SUMMARY CARD (Groww Style)
status_color = "#4caf50" if net_status >= 0 else "#ff5722"
status_sign = "+" if net_status >= 0 else "-"

card_html = f"""
<div class="metric-card">
    <div style="font-size: 12px; font-weight: 600; color: #777; letter-spacing: 1px;">NET LIFESTYLE BUDGET (REMAINING)</div>
    <div class="net-pl" style="color: {status_color};">{status_sign}₹{abs(net_status):,.2f}</div>
    <div style="margin-top: 20px;">
        <div class="sub-metric">
            <span class="sub-text">Total Budgeted (15% Target)</span>
            <span class="sub-val">₹{total_lifestyle_target:,.2f}</span>
        </div>
        <div class="sub-metric">
            <span class="sub-text">Actual Spent</span>
            <span class="sub-val val-negative">-₹{total_lifestyle_spent:,.2f}</span>
        </div>
    </div>
"""

# 2. DYNAMIC MONTH GRID
# Generate exactly 12 months for the FY view (Apr to Mar)
fy_start_year = start_date.year if start_date.month >= 4 else start_date.year - 1
grid_months = []
for i in range(12):
    m_date = date(fy_start_year, 4, 1) + relativedelta(months=i)
    grid_months.append(m_date)

grid_html = "<div class='month-grid'>"
for m in grid_months:
    m_str = m.strftime("%b'%y").upper()
    
    # Check if this month is in our selected range AND has data
    m_df = df[(df['Date'].dt.month == m.month) & (df['Date'].dt.year == m.year)]
    
    if m > TODAY:
        # Future month
        grid_html += f"<div class='month-box'>{m_str}</div>"
    elif m < start_date or m > end_date:
        # Outside filter range
        grid_html += f"<div class='month-box'>{m_str}</div>"
    elif m_df.empty:
        # No spending logged yet
        grid_html += f"<div class='month-box month-active-success'>{m_str}</div>"
    else:
        # Evaluate budget
        spent = m_df['Cost'].sum()
        if spent > target_lifestyle_monthly:
            grid_html += f"<div class='month-box month-active-danger'>{m_str}</div>"
        else:
            grid_html += f"<div class='month-box month-active-success'>{m_str}</div>"

grid_html += "</div></div>"
st.markdown(card_html + grid_html, unsafe_allow_html=True)

# 3. QUICK ADD BUTTON
with st.expander("➕ Log New Expense"):
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: e_name = st.text_input("Expense Name")
    with c2: e_cost = st.number_input("Amount (₹)", min_value=0, step=500)
    with c3: e_date = st.date_input("Date", TODAY)
    
    if st.button("Save", use_container_width=True):
        new_row = pd.DataFrame([{"Date": e_date, "Category": "Lifestyle", "Activity": e_name, "Cost": e_cost}])
        st.session_state.activities = pd.concat([st.session_state.activities, new_row], ignore_index=True)
        st.rerun()

# 4. TRANSACTIONS LIST (Groww Style)
st.markdown("<h3 style='margin-top: 30px; font-size: 18px;'>Recent Activity</h3>", unsafe_allow_html=True)

if f_df.empty:
    st.caption("No activities found for this period.")
else:
    for idx, row in f_df.sort_values(by="Date", ascending=False).iterrows():
        st.markdown(f"""
        <div class="order-row">
            <div>
                <div class="order-title">{row['Activity']}</div>
                <div class="order-sub">{row['Date'].strftime('%d %b %Y')} • {row['Category']}</div>
            </div>
            <div class="order-val val-negative">-₹{row['Cost']:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
