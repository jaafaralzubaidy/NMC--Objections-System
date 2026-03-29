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
        .stat-label { font-size: 16px; font-weight: bold; margin-bottom: 5px; }
        .stat-value { font-size: 32px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 📂 Data Files Setup ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

def check_csv(file, columns):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(file, index=False)

check_csv(appeals_file, ["Employee", "Date", "Ticket Number", "KPI", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date", "Admin Notes"])

# --- ⚡ Session State & Users ---
if 'users_df' not in st.session_state:
    if not os.path.exists(users_file) or os.stat(users_file).st_size == 0:
        initial_users = ["ahatim", "jsafaa"]
        user_data = []
        for u in initial_users:
            role = 'Head Of Section' if u == 'ahatim' else 'Quality Engineer'
            pwd = 'manager123' if u == 'ahatim' else 'admin123'
            user_data.append({"username": u, "password": pwd, "name": u.upper(), "role": role, "first_login": False})
        pd.DataFrame(user_data).to_csv(users_file, index=False)
    st.session_state.users_df = pd.read_csv(users_file)

if 'df_appeals' not in st.session_state:
    st.session_state.df_appeals = pd.read_csv(appeals_file)

# --- 🔐 Authenticator Setup ---
if 'authenticator' not in st.session_state:
    creds = {'usernames': {}}
    for row in st.session_state.users_df.itertuples(index=False):
        creds['usernames'][str(row.username)] = {'name': str(row.name), 'password': str(row.password), 'role': str(row.role)}
    st.session_state.authenticator = stauth.Authenticate(creds, 'nmc_objections_cookie', 'auth_key_123', cookie_expiry_days=30)

authenticator = st.session_state.authenticator

# --- 📤 Excel Export Function ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM PRO</div><hr>', unsafe_allow_html=True)

res = authenticator.login('main')

if st.session_state["authentication_status"]:
    username = st.session_state["username"]
    user_info = st.session_state.users_df[st.session_state.users_df['username'] == username].iloc[0]
    full_name = user_info['name']

    # Force Password Change
    if user_info['first_login']:
        st.warning("⚠️ Security: Change your password.")
        with st.form("pwd_form"):
            new_p = st.text_input("New Password", type="password")
            if st.form_submit_button("Update"):
                st.session_state.users_df.loc[st.session_state.users_df['username'] == username, ['password', 'first_login']] = [new_p, False]
                st.session_state.users_df.to_csv(users_file, index=False)
                st.success("Updated! Please logout and login again."); st.stop()
        st.stop()

    st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {full_name}</div>', unsafe_allow_html=True)
    authenticator.logout('Logout', 'sidebar')

    # --- 📊 Dashboard Statistics (Admin/Manager) ---
    if username in ['jsafaa', 'ahatim']:
        df = st.session_state.df_appeals
        pending_obs = df[(df['Quality Decision'] == 'Pending') | (df['Direct Manager'] == 'Pending')]
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="stat-card" style="background-color:#e3f2fd; border-color:#1565c0;"><div class="stat-label" style="color:#1565c0;">Total Objections</div><div class="stat-value">{len(df)}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="background-color:#fff3e0; border-color:#ef6c00;"><div class="stat-label" style="color:#ef6c00;">Pending Review</div><div class="stat-value">{len(pending_obs)}</div></div>', unsafe_allow_html=True)
        with c3:
            acc = len(df[(df['Quality Decision'] == 'Accepted') & (df['Direct Manager'] == 'Accepted')])
            st.markdown(f'<div class="stat-card" style="background-color:#e8f5e9; border-color:#
