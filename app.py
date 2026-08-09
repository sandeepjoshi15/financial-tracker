import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="FIRE Tracker | 15-70-15", page_icon="⚡", layout="wide")

# --- CUSTOM CSS (Fintech Aesthetic) ---
st.markdown("""
<style>
    /* Main Background & Text */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* Custom Metric Cards */
    .kpi-container {
        display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap;
    }
    .kpi-card {
        background: linear-gradient(145deg, #1A1C23 0%, #121418 100%);
        border: 1px solid #2A2D35;
        border-radius: 12px;
        padding: 20px;
        flex: 1;
        min-width: 200px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s ease;
    }
    .kpi-card:hover { transform: translateY(-3px); border-color: #4CAF50; }
    .kpi-title { font-size: 12px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;}
    .kpi-value { font-size: 28px; font-weight: 700; color: #FFF; margin-bottom: 5px;}
    .kpi-sub { font-size: 13px; font-weight: 600; }
    .text-green { color: #00E676; }
    .text-red { color: #FF3D00; }
    .text-blue { color: #00B0FF; }
    
    /* Headers & Dividers */
    h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 700 !important; }
    hr { border-color: #2A2D35; }
</style>
""", unsafe_allow_html=True)

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
    st.markdown("<br><br><h1 style='text-align: center; color: #FFF;'>⚡ FIRE Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Secure access to your institutional-grade financial tracker.</p><br>", unsafe_allow_html=True)
    
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

# --- MAIN APP HEADER ---
col_head1, col_head2 = st.columns([5, 1])
col_head1.markdown(f"<h2>⚡ Welcome, {st.session_state.user.capitalize()}</h2>", unsafe_allow_html=True)
with col_head2:
    st.write("") # Padding
    if st.button("🚪 Secure Logout", use_container_width=True):
        st.query_params.clear()
        st.session_state.logged_in = False
        st.session_state.user = ""
        st.rerun()

st.markdown("---")

# --- NAVIGATION: MONTH SELECTOR ---
if 'active_month' not in st.session_state:
    st.session_state.active_month = datetime.today().strftime("%Y-%m")

fy_months = pd.date_range(start="2026-04-01", end="2027-03-31", freq='MS')
options = []
for m in fy_months:
    m_key = m.strftime("%Y-%m")
    m_label = m.strftime("%b '%y").upper()
    has_data = not df_user[df_user['Month'] == m_key].empty
    options.append((m_key, f"● {m_label}" if has_data else m_label))

# Streamlit native horizontal selection
selected_option = st.radio(
    "Select Reporting Period",
    options=[opt[1] for opt in options],
    index=[opt[0] for opt in options].index(st.session_state.active_month) if st.session_state.active_month in [opt[0] for opt in options] else 0,
    horizontal=True,
    label_visibility="collapsed"
)
st.session_state.active_month = [opt[0] for opt in options if opt[1] == selected_option][0]
m_df = df_user[df_user['Month'] == st.session_state.active_month]

# --- CALCULATION ENGINE ---
income = m_df[m_df['Category'] == 'Income']['Amount'].sum()
survival = m_df[m_df['Category'] == 'Survival & Debt']['Amount'].sum()
wealth = m_df[m_df['Category'] == 'Wealth Engine']['Amount'].sum()
lifestyle = m_df[m_df['Category'] == 'Lifestyle']['Amount'].sum()

target_survival = income * 0.15
target_wealth = income * 0.70
target_lifestyle = income * 0.15

# --- KPI CARDS (Custom HTML) ---
st.markdown("<br>", unsafe_allow_html=True)
if income == 0:
    st.warning("⚠️ No 'Income' logged for this period. Targets cannot be calculated.")

c1, c2, c3, c4 = st.columns(4)

# Income Card
c1.markdown(f"""
<div class="kpi-card" style="border-top: 3px solid #00B0FF;">
    <div class="kpi-title">Total Cash Inflow</div>
    <div class="kpi-value">₹{income:,.0f}</div>
    <div class="kpi-sub text-blue">Deployed: ₹{survival+wealth+lifestyle:,.0f}</div>
</div>
""", unsafe_allow_html=True)

# Survival Card
s_diff = target_survival - survival
s_color = "text-green" if s_diff >= 0 else "text-red"
c2.markdown(f"""
<div class="kpi-card" style="border-top: 3px solid {'#00E676' if s_diff >= 0 else '#FF3D00'};">
    <div class="kpi-title">Survival (15% Cap)</div>
    <div class="kpi-value">₹{survival:,.0f}</div>
    <div class="kpi-sub {s_color}">Target: ₹{target_survival:,.0f} ({'+' if s_diff >= 0 else ''}₹{s_diff:,.0f})</div>
</div>
""", unsafe_allow_html=True)

# Wealth Card
w_diff = wealth - target_wealth
w_color = "text-green" if w_diff >= 0 else "text-red"
c3.markdown(f"""
<div class="kpi-card" style="border-top: 3px solid {'#00E676' if w_diff >= 0 else '#FF3D00'};">
    <div class="kpi-title">Wealth (70% Floor)</div>
    <div class="kpi-value">₹{wealth:,.0f}</div>
    <div class="kpi-sub {w_color}">Target: ₹{target_wealth:,.0f} ({'+' if w_diff >= 0 else ''}₹{w_diff:,.0f})</div>
</div>
""", unsafe_allow_html=True)

# Lifestyle Card
l_diff = target_lifestyle - lifestyle
l_color = "text-green" if l_diff >= 0 else "text-red"
c4.markdown(f"""
<div class="kpi-card" style="border-top: 3px solid {'#00E676' if l_diff >= 0 else '#FF3D00'};">
    <div class="kpi-title">Lifestyle (15% Cap)</div>
    <div class="kpi-value">₹{lifestyle:,.0f}</div>
    <div class="kpi-sub {l_color}">Target: ₹{target_lifestyle:,.0f} ({'+' if l_diff >= 0 else ''}₹{l_diff:,.0f})</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- WORKSPACE: CHARTS & INPUT ---
col_charts, col_input = st.columns([2.5, 1.5])

with col_charts:
    with st.container(border=True):
        st.markdown("#### 📊 Capital Allocation")
        if income > 0 and (survival > 0 or wealth > 0 or lifestyle > 0):
            # Plotly Sunburst / Donut
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
            cat = st.selectbox("Category", ["Income", "Survival & Debt", "Wealth Engine", "Lifestyle"])
            sub_cat = st.text_input("Sub-Category / Description", placeholder="e.g., Salary, Rent, Groww SIP")
            amt = st.number_input("Amount (₹)", min_value=0.0, step=500.0)
            
            if st.form_submit_button("Add to Ledger", use_container_width=True):
                if sub_cat and amt > 0:
                    new_data = pd.DataFrame([{
                        "User": st.session_state.user,
                        "Month": st.session_state.active_month,
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
st.markdown("#### 📓 Categorized Ledger")
if not m_df.empty:
    breakdown = m_df.groupby(['Category', 'SubCategory'])['Amount'].sum().reset_index()
    # Format for display
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
    st.info("No ledger entries for this period.")
