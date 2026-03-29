import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
import io
from datetime import datetime, timedelta

# --- 🚀 Page Configuration ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- 🎨 Custom CSS ---
st.markdown("""
    <style>
        .main-title { font-size:40px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        div[data-testid="stExpander"] { background-color: rgba(240, 242, 246, 0.5); border-radius: 10px; border: 1px solid #d1d5db; }
        .user-name-sidebar { color: #4CAF50; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
        .stat-card { padding: 20px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 10px; border-left: 6px solid; min-height: 120px; }
        .stat-label { font-size: 16px; font-weight: bold; margin-bottom: 5px; color: #333; }
        .stat-value { font-size: 32px; font-weight: bold; color: #000; }
    </style>
""", unsafe_allow_html=True)

# --- 📂 Data Management ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

def initialize_files():
    if not os.path.exists(appeals_file) or os.stat(appeals_file).st_size == 0:
        pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "KPI", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date", "Admin Notes"]).to_csv(appeals_file, index=False)
    
    if not os.path.exists(users_file) or os.stat(users_file).st_size == 0:
        initial_users = [
            {"username": "ahatim", "password": "manager123", "name": "AHATIM", "role": "Head Of Section", "first_login": False},
            {"username": "jsafaa", "password": "admin123", "name": "JSAFAA", "role": "Quality Engineer", "first_login": False}
        ]
        pd.DataFrame(initial_users).to_csv(users_file, index=False)

initialize_files()

if 'df_appeals' not in st.session_state:
    st.session_state.df_appeals = pd.read_csv(appeals_file)
if 'users_df' not in st.session_state:
    st.session_state.users_df = pd.read_csv(users_file)

# --- 🔐 Auth System ---
if 'authenticator' not in st.session_state:
    creds = {'usernames': {}}
    for _, row in st.session_state.users_df.iterrows():
        creds['usernames'][str(row['username'])] = {'name': str(row['name']), 'password': str(row['password']), 'role': str(row['role'])}
    st.session_state.authenticator = stauth.Authenticate(creds, 'nmc_objections_cookie', 'auth_key_123', cookie_expiry_days=30)

authenticator = st.session_state.authenticator

# --- 🛠 Functions ---
def save_data():
    st.session_state.df_appeals.to_csv(appeals_file, index=False)
    st.session_state.users_df.to_csv(users_file, index=False)

def export_to_excel(df):
    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Objections')
    except:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Objections')
    return output.getvalue()

# --- 🚀 Main UI ---
st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM PRO</div><hr>', unsafe_allow_html=True)

res = authenticator.login('main')

if st.session_state["authentication_status"]:
    username = st.session_state["username"]
    user_info = st.session_state.users_df[st.session_state.users_df['username'] == username].iloc[0]
    
    st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {user_info["name"]}</div>', unsafe_allow_html=True)
    authenticator.logout('Logout', 'sidebar')

    # --- 📊 Stats Overview (For Admin/Manager) ---
    if username in ['jsafaa', 'ahatim']:
        df = st.session_state.df_appeals
        total = len(df)
        pending = len(df[(df['Quality Decision'] == 'Pending') | (df['Direct Manager'] == 'Pending')])
        accepted = len(df[(df['Quality Decision'] == 'Accepted') & (df['Direct Manager'] == 'Accepted')])

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="stat-card" style="background-color:#e3f2fd; border-color:#1565c0;"><div class="stat-label">Total Objections</div><div class="stat-value">{total}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="background-color:#fff3e0; border-color:#ef6c00;"><div class="stat-label">Pending Review</div><div class="stat-value">{pending}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card" style="background-color:#e8f5e9; border-color:#2e7d32;"><div class="stat-label">Fully Accepted</div><div class="stat-value">{accepted}</div></div>', unsafe_allow_html=True)

    # --- Tabs ---
    if username == 'jsafaa':
        main_tab, admin_users_tab = st.tabs(["📊 Main System", "👥 Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        if username in ['jsafaa', 'ahatim']:
            st.subheader("🛠 MANAGEMENT CONTROL PANEL")
            st.dataframe(st.session_state.df_appeals, use_container_width=True)
            
            with st.expander("Update Entry"):
                if not st.session_state.df_appeals.empty:
                    row_idx = st.number_input("Select Index", 0, len(st.session_state.df_appeals)-1, 0)
                    col_a, col_b = st.columns(2)
                    with col_a:
                        q_val = st.selectbox("Quality Decision", ["Pending", "Accepted", "Rejected"], key="q_edit", disabled=(username == 'ahatim'))
                    with col
