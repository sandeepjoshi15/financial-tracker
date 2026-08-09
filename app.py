import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="FIRE Dashboard", page_icon="🔥", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .metric-card {background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333;}
    .metric-title {color: #aaa; font-size: 14px; font-weight: bold; text-transform: uppercase;}
    .metric-val {color: #fff; font-size: 28px; font-weight: bold;}
    .status-green {color: #4caf50;}
    .status-red {color: #ff5722;}
</style>
""", unsafe_allow_html=True)

import hashlib

# --- SECURITY PROTOCOL ---
def hash_password(password):
    """Returns a SHA-256 hash of the password."""
    return hashlib.sha256(password.encode()).hexdigest()

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- AUTHENTICATION WALL ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""

if not st.session_state.logged_in:
    st.title("🔒 Access Your Dashboard")
    
    # Load user database
    try:
        df_users = conn.read(worksheet="Users", usecols=[0, 1])
        df_users = df_users.dropna(how="all")
        
        # Bulletproof Fix 1: Strip accidental spaces from Google Sheet headers
        if not df_users.empty:
            df_users.columns = df_users.columns.str.strip()
            
        # Bulletproof Fix 2: If the sheet is completely blank, force the correct structure
        if df_users.empty or 'Username' not in df_users.columns:
            df_users = pd.DataFrame(columns=["Username", "Password"])
            
    except Exception as e:
        st.error("Error connecting to Users database. Please ensure the 'Users' tab exists in your Google Sheet.")
        st.stop()
        
    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])
    
    with tab_login:
        with st.form("login_form"):
            log_user = st.text_input("Username").strip().lower()
            log_pin = st.text_input("PIN", type="password")
            if st.form_submit_button("Login", use_container_width=True):
                if log_user in df_users['Username'].values:
                    stored_hash = df_users.loc[df_users['Username'] == log_user, 'Password'].values[0]
                    if stored_hash == hash_password(log_pin):
                        st.session_state.logged_in = True
                        st.session_state.user = log_user
                        st.rerun()
                    else:
                        st.error("Incorrect PIN.")
                else:
                    st.error("User not found.")
                    
    with tab_signup:
        with st.form("signup_form"):
            st.caption("Create a new account. Your PIN will be securely hashed.")
            new_user = st.text_input("Choose a Username").strip().lower()
            new_pin = st.text_input("Choose a PIN", type="password")
            confirm_pin = st.text_input("Confirm PIN", type="password")
            
            if st.form_submit_button("Create Account", use_container_width=True):
                if new_user == "" or new_pin == "":
                    st.error("Fields cannot be empty.")
                elif new_pin != confirm_pin:
                    st.error("PINs do not match.")
                elif new_user in df_users['Username'].values:
                    st.error("Username already exists. Choose another.")
                else:
                    # Save the hashed password to the Google Sheet
                    new_user_row = pd.DataFrame([{"Username": new_user, "Password": hash_password(new_pin)}])
                    updated_users = pd.concat([df_users, new_user_row], ignore_index=True)
                    conn.update(worksheet="Users", data=updated_users)
                    st.cache_data.clear() # Reset cache so the new user can log in immediately
                    st.success("✅ Account created! You can now log in.")
    st.stop() # Halts execution so unauthenticated users cannot see the main app

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5) 
def load_data():
    try:
        df = conn.read(worksheet="Transactions", usecols=[0, 1, 2, 3, 4])
        df = df.dropna(how="all") 
        
        # Bulletproof Fix 1: Strip accidental spaces from Google Sheet headers
        if not df.empty:
            df.columns = df.columns.astype(str).str.strip()
            
        # Bulletproof Fix 2: If the sheet is completely blank or missing headers, force the correct structure
        if df.empty or 'User' not in df.columns:
            return pd.DataFrame(columns=["User", "Month", "Category", "SubCategory", "Amount"])
            
        return df
    except Exception as e:
        st.error(f"Database connection failed. Exact error: {e}") 
        return pd.DataFrame(columns=["User", "Month", "Category", "SubCategory", "Amount"])

df_master = load_data()

# Filter data strictly for the logged-in user
df_user = df_master[df_master['User'] == st.session_state.user]

# --- APP NAVIGATION ---
colA, colB = st.columns([4, 1])
colA.title(f"🔥 Welcome, {st.session_state.user.capitalize()}")
if colB.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.rerun()

st.markdown("### Select Financial Month")

if 'active_month' not in st.session_state:
    st.session_state.active_month = "2026-08"

# Month Grid
fy_months = pd.date_range(start="2026-04-01", end="2027-03-31", freq='MS')
cols = st.columns(6)
for i, m in enumerate(fy_months):
    m_key = m.strftime("%Y-%m")
    m_label = m.strftime("%b '%y").upper()
    
    has_data = not df_user[df_user['Month'] == m_key].empty
    display_label = f"✅ {m_label}" if has_data else m_label
    btn_type = "primary" if st.session_state.active_month == m_key else "secondary"
    
    if cols[i%6].button(display_label, type=btn_type, use_container_width=True, key=m_key):
        st.session_state.active_month = m_key
        st.rerun()

st.markdown("---")

# --- ACTIVE WORKSPACE ---
active_m_obj = datetime.strptime(st.session_state.active_month, "%Y-%m")
st.subheader(f"Workspace: {active_m_obj.strftime('%B %Y')}")

m_df = df_user[df_user['Month'] == st.session_state.active_month]

# Calculate Aggregates
income = m_df[m_df['Category'] == 'Income']['Amount'].sum()
survival = m_df[m_df['Category'] == 'Survival & Debt']['Amount'].sum()
wealth = m_df[m_df['Category'] == 'Wealth Engine']['Amount'].sum()
lifestyle = m_df[m_df['Category'] == 'Lifestyle']['Amount'].sum()

target_survival = income * 0.15
target_wealth = income * 0.70
target_lifestyle = income * 0.15

# UI Layout
col_log, col_dash = st.columns([1, 2])

with col_log:
    st.markdown("#### Log New Entry")
    with st.form("entry_form"):
        cat = st.selectbox("Broad Category", ["Income", "Survival & Debt", "Wealth Engine", "Lifestyle"])
        sub_cat = st.text_input("Sub-Category (e.g., Salary, Home Loan, Swiggy, Groww SIP)")
        amt = st.number_input("Amount (₹)", min_value=0.0, step=500.0)
        
        if st.form_submit_button("Save to Ledger", use_container_width=True):
            if sub_cat and amt > 0:
                new_data = pd.DataFrame([{
                    "User": st.session_state.user,
                    "Month": st.session_state.active_month,
                    "Category": cat,
                    "SubCategory": sub_cat,
                    "Amount": amt
                }])
                
                # Append and upload to Google Sheets
                updated_master = pd.concat([df_master, new_data], ignore_index=True)
                conn.update(worksheet="Transactions", data=updated_master)
                st.cache_data.clear() # Force app to pull fresh data
                st.success("Entry Saved!")
                st.rerun()
            else:
                st.error("Please enter a sub-category and amount.")

with col_dash:
    st.markdown("#### Performance Targets")
    if income == 0:
        st.warning("⚠️ Log your 'Income' for this month to generate your budget targets.")
    
    c1, c2, c3 = st.columns(3)
    
    c1.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Survival (Cap: ₹{target_survival:,.0f})</div>
        <div class="metric-val">₹{survival:,.0f}</div>
        <div class="{'status-green' if (target_survival - survival) >= 0 else 'status-red'}" style="margin-top: 5px;">
            {'+' if (target_survival - survival) >= 0 else ''}₹{target_survival - survival:,.0f}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    c2.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Wealth (Target: ₹{target_wealth:,.0f})</div>
        <div class="metric-val">₹{wealth:,.0f}</div>
        <div class="{'status-green' if (wealth - target_wealth) >= 0 else 'status-red'}" style="margin-top: 5px;">
            {'+' if (wealth - target_wealth) >= 0 else ''}₹{wealth - target_wealth:,.0f}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    c3.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Lifestyle (Cap: ₹{target_lifestyle:,.0f})</div>
        <div class="metric-val">₹{lifestyle:,.0f}</div>
        <div class="{'status-green' if (target_lifestyle - lifestyle) >= 0 else 'status-red'}" style="margin-top: 5px;">
            {'+' if (target_lifestyle - lifestyle) >= 0 else ''}₹{target_lifestyle - lifestyle:,.0f}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>#### Ledger Breakdown", unsafe_allow_html=True)
    if not m_df.empty:
        # Group by Category and SubCategory for clean analysis
        breakdown = m_df.groupby(['Category', 'SubCategory'])['Amount'].sum().reset_index()
        breakdown['Amount'] = breakdown['Amount'].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(breakdown, use_container_width=True, hide_index=True)
    else:
        st.caption("No entries for this month yet.")
