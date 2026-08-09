import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
from github import Github

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="FIRE Dashboard | 15-70-15",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE (Local Database Simulation) ---
# --- DATABASE SETUP (GitHub CSV Integration) ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = "YOUR_USERNAME/financial-tracker" # ⚠️ CHANGE THIS TO YOUR ACTUAL REPO NAME
FILE_PATH = "data.csv"

@st.cache_data(ttl=10) # Prevents the app from hitting GitHub API limits
def load_data():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        contents = repo.get_contents(FILE_PATH)
        df = pd.read_csv(io.StringIO(contents.decoded_content.decode('utf-8')))
        return df, contents.sha
    except:
        # If the CSV doesn't exist yet, return an empty layout
        return pd.DataFrame(columns=["Date", "Category", "Activity", "Cost", "Joy Score", "ROI"]), None

if 'activities' not in st.session_state:
    df, sha = load_data()
    st.session_state.activities = df
    st.session_state.file_sha = sha

# --- SIDEBAR CONTROLS ---
st.sidebar.title("⚙️ Global Controls")
st.sidebar.markdown("Define your parameters for the current view.")

# Date Filter
st.sidebar.subheader("Date Range")
date_range = st.sidebar.date_input(
    "Select Period",
    value=(datetime.today().date() - timedelta(days=30), datetime.today().date()),
    max_value=datetime.today().date()
)

# Income Input
st.sidebar.subheader("Income Details")
salary = st.sidebar.number_input("Net Monthly Salary (₹)", min_value=0, value=143000, step=1000)

st.sidebar.markdown("---")
st.sidebar.caption("Target Framework: Hyper-Aggressive 15 / 70 / 15")

# --- CORE CALCULATIONS ---
target_survival = salary * 0.15
target_wealth = salary * 0.70
target_lifestyle = salary * 0.15

# --- MAIN UI TABS ---
st.title("🔥 Financial Independence Dashboard")
tab1, tab2, tab3 = st.tabs(["📊 Capital Allocation", "🎯 Activity ROI", "⚡ Discipline Streaks"])

# ==========================================
# TAB 1: CAPITAL ALLOCATION DASHBOARD
# ==========================================
with tab1:
    st.markdown("### Monthly Cash Flow Tracking")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        actual_survival = st.number_input("Actual Survival & Debt Spend (₹)", min_value=0.0, value=21450.0, step=1000.0)
    with col2:
        actual_wealth = st.number_input("Actual Wealth Deployed (₹)", min_value=0.0, value=100100.0, step=1000.0)
    with col3:
        actual_lifestyle = st.number_input("Actual Lifestyle Spend (₹)", min_value=0.0, value=15000.0, step=1000.0)

    st.markdown("---")
    
    # Visualizations
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Donut Chart for Target vs Actual
        labels = ['Survival & Debt', 'Wealth Engine', 'Lifestyle']
        target_vals = [target_survival, target_wealth, target_lifestyle]
        actual_vals = [actual_survival, actual_wealth, actual_lifestyle]
        
        fig_donut = go.Figure()
        fig_donut.add_trace(go.Pie(labels=labels, values=actual_vals, hole=0.6, marker_colors=['#ff9999','#66b3ff','#99ff99']))
        fig_donut.update_layout(title_text="Actual Capital Allocation", annotations=[dict(text='Deployed', x=0.5, y=0.5, font_size=20, showarrow=False)])
        st.plotly_chart(fig_donut, use_container_width=True)

    with chart_col2:
        # Bar Chart for Targets vs Actuals
        fig_bar = go.Figure(data=[
            go.Bar(name='Target (₹)', x=labels, y=target_vals, marker_color='rgba(200, 200, 200, 0.5)'),
            go.Bar(name='Actual (₹)', x=labels, y=actual_vals, marker_color=['#cf6679', '#4caf50', '#03dac6'])
        ])
        fig_bar.update_layout(barmode='group', title_text="Target vs. Actual Burn Rate")
        st.plotly_chart(fig_bar, use_container_width=True)


# ==========================================
# TAB 2: ACTIVITY-BASED ROI
# ==========================================
with tab2:
    st.markdown("### Log & Measure Discretionary Spending")
    
    # Input Form
    with st.expander("➕ Log a New Activity", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns([2, 2, 2, 1])
        with f_col1:
            a_cat = st.selectbox("Category", ["Fitness", "Dining", "Shopping", "Travel", "Hobbies", "Other"])
        with f_col2:
            a_name = st.text_input("Activity Name", placeholder="e.g., Badminton")
        with f_col3:
            a_cost = st.number_input("Cost (₹)", min_value=0, value=500, step=100)
        with f_col4:
            a_joy = st.slider("Joy (1-10)", 1, 10, 7)
            
        if st.button("Save Activity", use_container_width=True):
            # 1. Calculate ROI
            roi_val = a_cost / a_joy if a_joy > 0 else a_cost
            
            # 2. Create the new row
            new_entry = pd.DataFrame([{
                "Date": datetime.today().date(),
                "Category": a_cat,
                "Activity": a_name,
                "Cost": a_cost,
                "Joy Score": a_joy,
                "ROI": round(roi_val, 2)
            }])
            
            # 3. Update the temporary memory
            st.session_state.activities = pd.concat([st.session_state.activities, new_entry], ignore_index=True)
            
            # 4. Push the permanent update to GitHub
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)
            csv_string = st.session_state.activities.to_csv(index=False)
            
            with st.spinner("Writing to database..."):
                if st.session_state.file_sha:
                    res = repo.update_file(FILE_PATH, "Appended new activity", csv_string, st.session_state.file_sha)
                    st.session_state.file_sha = res['commit'].sha
                else:
                    res = repo.create_file(FILE_PATH, "Initial CSV creation", csv_string)
                    st.session_state.file_sha = res['content'].sha
                
            st.success("✅ Activity Permanently Saved to GitHub!")

    # Filter Data based on Sidebar Date Range
    df = st.session_state.activities
    if len(date_range) == 2:
        start_date, end_date = date_range
        mask = (pd.to_datetime(df['Date']).dt.date >= start_date) & (pd.to_datetime(df['Date']).dt.date <= end_date)
        filtered_df = df.loc[mask]
    else:
        filtered_df = df

    # Analytics View
    if not filtered_df.empty:
        st.markdown("#### Cost vs. Satisfaction Matrix")
        st.caption("Lower on the Y-axis and further right on the X-axis means highly optimal spending.")
        
        # Interactive Scatter Plot
        fig_scatter = px.scatter(
            filtered_df, x="Joy Score", y="Cost", color="Category", size="Cost", 
            hover_name="Activity", size_max=40, template="plotly_dark",
            labels={"Cost": "Rupees Spent (₹)", "Joy Score": "Satisfaction (1-10)"}
        )
        fig_scatter.update_layout(xaxis=dict(range=[0, 11]))
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        st.dataframe(filtered_df.sort_values(by="Date", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("No activities logged in the selected date range.")


# ==========================================
# TAB 3: DISCIPLINE STREAKS
# ==========================================
with tab3:
    st.markdown("### Lifestyle Budget Compliance")
    st.caption("Keeping your lifestyle spending under 15% triggers a successful month.")
    
    # Calculate current status
    is_successful = actual_lifestyle <= target_lifestyle
    
    st.metric(
        label="Current Month Status", 
        value="Under Budget" if is_successful else "Over Budget",
        delta=f"₹{target_lifestyle - actual_lifestyle:,.2f} remaining" if is_successful else f"Exceeded by ₹{actual_lifestyle - target_lifestyle:,.2f}",
        delta_color="normal"
    )
    
    st.markdown("---")
    st.markdown("#### Annual Heatmap (Simulated)")
    
    # Render a highly visual calendar grid (Simulated data for aesthetics)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    status = ["success", "success", "danger", "success", "success", "success", "success", "current", "pending", "pending", "pending", "pending"]
    
    cols = st.columns(12)
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"<div style='text-align:center; font-weight:bold;'>{months[i]}</div>", unsafe_allow_html=True)
            if status[i] == "success":
                st.markdown("<div style='height:40px; background-color:#4caf50; border-radius:8px; margin-top:10px;'></div>", unsafe_allow_html=True)
            elif status[i] == "danger":
                st.markdown("<div style='height:40px; background-color:#cf6679; border-radius:8px; margin-top:10px;'></div>", unsafe_allow_html=True)
            elif status[i] == "current":
                color = "#4caf50" if is_successful else "#cf6679"
                st.markdown(f"<div style='height:40px; background-color:{color}; border: 3px solid white; border-radius:8px; margin-top:10px;'></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='height:40px; background-color:#333333; border-radius:8px; margin-top:10px;'></div>", unsafe_allow_html=True)
