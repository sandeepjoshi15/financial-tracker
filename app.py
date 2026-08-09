import streamlit as st
import pandas as pd
from datetime import datetime, date
import hashlib
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="FIRE Tracker | 15-70-15", page_icon="⚡", layout="wide")

# --- SECURITY & PERSISTENCE PROTOCOL ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_session_token(username):
    salt = "FIRE_TRACKER_SECURE_SALT_2026" 
    return hashlib.sha256((username + salt).encode()).hexdigest()

# URL Parameter Check (Survives Refresh)
if "user" in st.query_params and "auth" in st.query_params:
    if st.query_params["auth"] == generate_session_token(st.query_params["user"]):
        st.session_state.logged_in = True
        st.session_state.user = st.query_params["user"]

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- AUTHENTICATION WALL ---
if not st.session_state.logged_in:
    st.markdown("<br><br><h1 style='text-align: center;'>⚡ FIRE Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Secure access to your institutional-grade financial tracker.</p><br>", unsafe_allow_html=True)
    
    try:
        df_users = conn.read(worksheet="Users", usecols=[0, 1])
        df_users = df_users.dropna(how="all")
        if not df_users.empty:
            df_users.columns = df_users.columns.astype(str).str.strip()
        if df_users.empty or 'Username' not in df_users.columns:
            df_users = pd.DataFrame(columns=["Username", "Password"])
    except Exception as e:
        st.error(f"Database connection failed. Exact error: {e}")
        st.stop()
        
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        tab_login, tab_signup = st.tabs(["Login", "Sign Up"])
        
        with tab_login:
            with st.form("login_form"):
                log_user = st.text_input("Username").strip().lower()
                log_pin = st.text_input("PIN", type="password")
                if st.form_submit_button("Authenticate", use_container_width=True):
                    if log_user in df_users['Username'].values:
                        stored_hash = df_users.loc[df_users['Username'] == log_user, 'Password'].values[0]
                        if stored_hash == hash_password(log_pin):
                            st.session_state.logged_in = True
                            st.session_state.user = log_user
                            st.query_params["user"] = log_user
                            st.query_params["auth"] = generate_session_token(log_user)
                            st.rerun()
                        else:
                            st.error("Incorrect PIN.")
                    else:
                        st.error("User not found.")
                        
        with tab_signup:
            with st.form("signup_form"):
                st.caption("Create an isolated account instance.")
                new_user = st.text_input("Choose Username").strip().lower()
                new_pin = st.text_input("Choose PIN", type="password")
                confirm_pin = st.text_input("Confirm PIN", type="password")
                if st.form_submit_button("Initialize Account", use_container_width=True):
                    if new_user == "" or new_pin == "":
                        st.error("Fields cannot be empty.")
                    elif new_pin != confirm_pin:
                        st.error("PINs do not match.")
                    elif new_user in df_users['Username'].values:
                        st.error("Username already exists.")
                    else:
                        new_user_row = pd.DataFrame([{"Username": new_user, "Password": hash_password(new_pin)}])
                        updated_users = pd.concat([df_users, new_user_row], ignore_index=True)
                        conn.update(worksheet="Users", data=updated_users)
                        st.cache_data.clear()
                        st.success("✅ Account verified. Please log in.")
    st.stop()

# --- LOAD USER DATA ---
@st.cache_data(ttl=5)
def load_data():
    try:
        df = conn.read(worksheet="Transactions", usecols=[0, 1, 2, 3, 4])
        df = df.dropna(how="all")
        if not df.empty:
            df.columns = df.columns.astype(str).str.strip()
        if df.empty or 'User' not in df.columns:
            return pd.DataFrame(columns=["User", "Month", "Category", "SubCategory", "Amount"])
        return df
    except Exception as e:
        st.error(f"Database connection failed. Exact error: {e}")
        return pd.DataFrame(columns=["User", "Month", "Category", "SubCategory", "Amount"])

df_master = load_data()
df_user = df_master[df_master['User'] == st.session_state.user]

# Ensure 'Month' is parsed correctly as a date/period proxy for filtering
df_user['ParsedDate'] = pd.to_datetime(df_user['Month'], errors='coerce')

# --- MAIN APP HEADER ---
col_head1, col_head2 = st.columns([5, 1])
col_head1.markdown(f"<h2>⚡ Welcome, {st.session_state.user.capitalize()}</h2>", unsafe_allow_html=True)
with col_head2:
    st.write("") 
    if st.button("🚪 Logout", use_container_width=True):
        st.query_params.clear()
        st.session_state.logged_in = False
        st.session_state.user = ""
        st.rerun()

st.markdown("---")

# --- ADVANCED TIME HORIZON SELECTOR ---
col_mode1, col_mode2 = st.columns([2, 2])
with col_mode1:
    view_mode = st.radio("Analytics Horizon", ["Monthly View", "Preset / Macro View", "Custom Date Range"], horizontal=True)

if view_mode == "Monthly View":
    if 'active_month' not in st.session_state:
        st.session_state.active_month = datetime.today().strftime("%Y-%m")

    fy_months = pd.date_range(start="2026-04-01", end="2027-03-31", freq='MS')
    options = []
    for m in fy_months:
        m_key = m.strftime("%Y-%m")
        m_label = m.strftime("%b '%y").upper()
        has_data = not df_user[df_user['Month'] == m_key].empty
        options.append((m_key, f"● {m_label}" if has_data else m_label))

    selected_option = st.radio(
        "Select Reporting Period",
        options=[opt[1] for opt in options],
        index=[opt[0] for opt in options].index(st.session_state.active_month) if st.session_state.active_month in [opt[0] for opt in options] else 0,
        horizontal=True
    )
    st.session_state.active_month = [opt[0] for opt in options if opt[1] == selected_option][0]
    
    # Filter by specific Month string
    m_df = df_user[df_user['Month'] == st.session_state.active_month]
    period_title = datetime.strptime(st.session_state.active_month, "%Y-%m").strftime("%B %Y")

elif view_mode == "Preset / Macro View":
    macro_choice = st.selectbox("Select Macro Horizon", [
        "Current Financial Year (2026-2027)", 
        "Previous Financial Year (2025-2026)", 
        "Last Quarter", 
        "Last Month"
    ])
    
    today = date.today()
    if macro_choice == "Current Financial Year (2026-2027)":
        start_date = pd.to_datetime("2026-04-01")
        end_date = pd.to_datetime("2027-03-31")
    elif macro_choice == "Previous Financial Year (2025-2026)":
        start_date = pd.to_datetime("2025-04-01")
        end_date = pd.to_datetime("2026-03-31")
    elif macro_choice == "Last Quarter":
        # Rough rolling 3-month window
        end_date = pd.to_datetime(today)
        start_date = end_date - pd.DateOffset(months=3)
    else: # Last Month
        end_date = pd.to_datetime(today)
        start_date = end_date - pd.DateOffset(months=1)
        
    m_df = df_user[(df_user['ParsedDate'] >= start_date) & (df_user['ParsedDate'] <= end_date)]
    period_title = macro_choice

else: # Custom Date Range
    c_start, c_end = st.columns(2)
    custom_start = c_start.date_input("Start Date", value=date(2026, 4, 1))
    custom_end = c_end.date_input("End Date", value=date.today())
    
    start_date = pd.to_datetime(custom_start)
    end_date = pd.to_datetime(custom_end)
    
    m_df = df_user[(df_user['ParsedDate'] >= start_date) & (df_user['ParsedDate'] <= end_date)]
    period_title = f"{custom_start.strftime('%d %b %Y')} to {custom_end.strftime('%d %b %Y')}"

# --- CALCULATION ENGINE ---
income = m_df[m_df['Category'] == 'Income']['Amount'].sum()
survival = m_df[m_df['Category'] == 'Survival & Debt']['Amount'].sum()
wealth = m_df[m_df['Category'] == 'Wealth Engine']['Amount'].sum()
lifestyle = m_df[m_df['Category'] == 'Lifestyle']['Amount'].sum()

target_survival = income * 0.15
target_wealth = income * 0.70
target_lifestyle = income * 0.15

# --- KPI METRIC CARDS ---
st.markdown(f"### 📈 Performance Summary: {period_title}")
if income == 0:
    st.warning("⚠️ No 'Income' logged for this horizon. Targets cannot be calculated.")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Inflow", f"₹{income:,.0f}", f"Deployed: ₹{survival+wealth+lifestyle:,.0f}")

s_diff = target_survival - survival
c2.metric("Survival (15% Cap)", f"₹{survival:,.0f}", f"{'+' if s_diff >= 0 else ''}₹{s_diff:,.0f} vs Target", delta_color="normal" if s_diff >= 0 else "inverse")

w_diff = wealth - target_wealth
c3.metric("Wealth (70% Floor)", f"₹{wealth:,.0f}", f"{'+' if w_diff >= 0 else ''}₹{w_diff:,.0f} vs Target", delta_color="normal" if w_diff >= 0 else "inverse")

l_diff = target_lifestyle - lifestyle
c4.metric("Lifestyle (15% Cap)", f"₹{lifestyle:,.0f}", f"{'+' if l_diff >= 0 else ''}₹{l_diff:,.0f} vs Target", delta_color="normal" if l_diff >= 0 else "inverse")

st.markdown("<br>", unsafe_allow_html=True)

# --- WORKSPACE: CHARTS & INPUT ---
col_charts, col_input = st.columns([2.5, 1.5])

with col_charts:
    with st.container(border=True):
        st.markdown("#### 📊 Capital Allocation Breakdown")
        if income > 0 and (survival > 0 or wealth > 0 or lifestyle > 0):
            labels = ['Survival & Debt', 'Wealth Engine', 'Lifestyle']
            values = [survival, wealth, lifestyle]
            colors = ['#FF4B4B', '#00E676', '#00B0FF']
            
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.6, marker_colors=colors)])
            fig.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#FFF"),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("Awaiting sufficient data to generate visualizations.")

with col_input:
    with st.container(border=True):
        st.markdown("#### 📝 Log Transaction")
        with st.form("entry_form"):
            default_month = st.session_state.active_month if view_mode == "Monthly View" else datetime.today().strftime("%Y-%m")
            
            log_month = st.text_input("Target Month (YYYY-MM)", value=default_month)
            cat = st.selectbox("Category", ["Income", "Survival & Debt", "Wealth Engine", "Lifestyle"])
            sub_cat = st.text_input("Sub-Category / Description", placeholder="e.g., Salary, Rent, Groww SIP")
            amt = st.number_input("Amount (₹)", min_value=0.0, step=500.0)
            
            if st.form_submit_button("Add to Ledger", use_container_width=True):
                if sub_cat and amt > 0:
                    new_data = pd.DataFrame([{
                        "User": st.session_state.user,
                        "Month": log_month,
                        "Category": cat,
                        "SubCategory": sub_cat,
                        "Amount": amt
                    }])
                    updated_master = pd.concat([df_master, new_data], ignore_index=True)
                    conn.update(worksheet="Transactions", data=updated_master)
                    st.cache_data.clear() 
                    st.rerun()
                else:
                    st.error("Description and Amount required.")

# --- DATAFRAME LEDGER ---
st.markdown(f"#### 📓 Aggregated Ledger ({period_title})")
if not m_df.empty:
    breakdown = m_df.groupby(['Category', 'SubCategory'])['Amount'].sum().reset_index()
    st.dataframe(
        breakdown, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Category": st.column_config.TextColumn("Bucket"),
            "SubCategory": st.column_config.TextColumn("Transaction Type"),
            "Amount": st.column_config.NumberColumn("Deployed (₹)", format="₹%d")
        }
    )
else:
    st.info("No ledger entries found for this horizon.")
