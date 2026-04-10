import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- Page Configuration ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

st.markdown("""
    <style>
        .main-title { font-size:40px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        div[data-testid="stExpander"] { 
            background-color: rgba(240, 242, 246, 0.5); 
            border-radius: 10px; border: 1px solid #d1d5db;
        }
        .user-name-sidebar { color: #4CAF50; font-weight: bold; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

# --- Data Loading Functions ---
def load_data():
    if not os.path.exists(appeals_file):
        cols = ["Employee", "Date", "Ticket Number", "Tab", "Details", 
                "Quality Decision", "Direct Manager", "Objection Issue Date", "KPI"]
        pd.DataFrame(columns=cols).to_csv(appeals_file, index=False)
    return pd.read_csv(appeals_file)

def load_users():
    if not os.path.exists(users_file):
        # Initial Admin/Manager Setup
        data = [
            {"username": "jsafaa", "password": "admin123", "name": "SAFAA", "role": "Quality Engineer", "Force_Change": True},
            {"username": "ahatim", "password": "manager123", "name": "HATIM", "role": "Head Of Section", "Force_Change": True},
            {"username": "farook", "password": "manager123", "name": "FAROOK", "role": "Team Leader", "Force_Change": True}
        ]
        pd.DataFrame(data).to_csv(users_file, index=False)
    df = pd.read_csv(users_file)
    # Ensure Farook is Team Leader
    if 'farook' in df['username'].values:
        df.loc[df['username'] == 'farook', 'role'] = 'Team Leader'
    return df

users_df = load_users()
df_appeals = load_data()

# --- Authentication Setup ---
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][row['username']] = {
        'name': f"{row['name']} ({row['role']})",
        'password': str(row['password'])
    }

authenticator = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_key', cookie_expiry_days=30)

st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

try:
    authenticator.login()
except Exception:
    st.info("Please Login")

if st.session_state.get("authentication_status"):
    username = st.session_state.get("username")
    user_info = users_df[users_df['username'] == username].iloc[0]
    
    # --- Force Password Change Feature ---
    if str(user_info.get('Force_Change', 'False')).lower() == 'true':
        st.warning("⚠️ You must update your password to proceed.")
        with st.form("pwd_form"):
            new_p = st.text_input("New Password", type="password")
            conf_p = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Update"):
                if new_p and new_p == conf_p and new_p != str(user_info['password']):
                    users_df.loc[users_df['username'] == username, 'password'] = new_p
                    users_df.loc[users_df['username'] == username, 'Force_Change'] = False
                    users_df.to_csv(users_file, index=False)
                    st.success("✅ Success! Please reload.")
                    st.rerun()
                else: st.error("Invalid Input or Passwords don't match.")
        st.stop()

    st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {credentials["usernames"][username]["name"]}</div>', unsafe_allow_html=True)
    authenticator.logout('Logout', 'sidebar')

    # --- Tabs Logic ---
    is_admin = username in ['jsafaa', 'farook']
    is_mgmt = username in ['jsafaa', 'ahatim', 'farook']

    tabs = ["📊 System", "👥 Manage Staff"] if is_admin else ["📊 System"]
    active_tabs = st.tabs(tabs)

    with active_tabs[0]:
        if is_mgmt:
            st.subheader("🛠 MANAGEMENT CONTROL PANEL")
            st.dataframe(df_appeals, use_container_width=True)
            with st.expander("Update Decisions"):
                if not df_appeals.empty:
                    idx = st.number_input("Select Row ID", 0, len(df_appeals)-1, 0)
                    c1, c2 = st.columns(2)
                    with c1:
                        # Only Quality (Safaa) can edit Quality Decision
                        q_dis = (username != 'jsafaa')
                        q_val = st.text_area("Quality Decision", value=df_appeals.loc[idx, "Quality Decision"], disabled=q_dis)
                    with c2:
                        # Management (Hatim/Farook) can edit Manager Decision
                        m_dis = (username == 'jsafaa')
                        m_val = st.text_area("Head Of Section Decision", value=df_appeals.loc[idx, "Direct Manager"], disabled=m_dis)
                    if st.button("Save"):
                        df_appeals.loc[idx, "Quality Decision"] = q_val
                        df_appeals.loc[idx, "Direct Manager"] = m_val
                        df_appeals.to_csv(appeals_file, index=False
