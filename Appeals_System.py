import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 🚀 Page Configuration ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- Custom CSS ---
st.markdown("""
    <style>
        .main-title { font-size:40px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        div[data-testid="stExpander"] { background-color: rgba(240, 242, 246, 0.5); border-radius: 10px; border: 1px solid #d1d5db; }
        .user-name-sidebar { color: #4CAF50; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
        .notification-banner { padding: 15px; background-color: #ffeeb2; border-left: 6px solid #ffcc00; border-radius: 5px; color: #856404; font-weight: bold; margin-bottom: 20px; font-size: 18px; }
        .stat-card { padding: 20px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 10px; }
        .stat-label { font-size: 16px; font-weight: bold; margin-bottom: 5px; }
        .stat-value { font-size: 32px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- File Names ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

# --- 🛠️ Data Loading Functions (Optimized for Speed) ---
@st.cache_data
def get_all_data():
    if not os.path.exists(appeals_file):
        pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "KPI", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date", "Admin Notes"]).to_csv(appeals_file, index=False)
    return pd.read_csv(appeals_file)

@st.cache_data
def get_users_df():
    if not os.path.exists(users_file):
        initial_users = ["ahatim", "mkhalid", "hfalah", "hmuayyad", "alimad", "rriyad", "hjabbar", "hmuhammada", "arubayi", "aadil", "ayasin", "fahmad", "hakali", "musadiq", "itsattar", "amusadaq", "aanbari", "afahad", "rthair", "omsubhi", "rwahab", "mlayth", "yasadi", "yriyad", "abfaysal", "hasanhadi", "hamuhsin", "aybasheer", "marmahmud", "abisameer", "jsafaa", "muhahamid", "murqasim", "moayad", "dadnan", "abiabbas", "qriyad", "tmustafa", "sbahnan", "admuhammad", "amohammad", "shzuhayr"]
        user_data = []
        for u in initial_users:
            p = 'admin123' if u == 'jsafaa' else ('manager123' if u == 'ahatim' else '123')
            role = 'Head Of Section' if u == 'ahatim' else ('Quality Engineer' if u == 'jsafaa' else 'Employee')
            user_data.append({"username": u, "password": p, "name": u.upper(), "role": role, "first_login": True})
        pd.DataFrame(user_data).to_csv(users_file, index=False)
    
    df = pd.read_csv(users_file)
    if "first_login" not in df.columns:
        df["first_login"] = False
        df.to_csv(users_file, index=False)
    return df

users_df = get_users_df()
df_appeals = get_all_data()

# --- ⚡ التحسين الأهم: تخزين نظام المصادقة في الذاكرة لتسريع الدخول والخروج ---
if 'authenticator' not in st.session_state:
    credentials = {'usernames': {}}
    for row in users_df.itertuples(index=False):
        credentials['usernames'][str(row.username)] = {'name': str(row.name), 'password': str(row.password), 'role': str(row.role)}
    
    st.session_state.authenticator = stauth.Authenticate(credentials, 'nmc_objections_cookie', 'auth_key_123', cookie_expiry_days=30)

authenticator = st.session_state.authenticator

# واجهة الدخول
st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

res = authenticator.login('main')
if st.session_state["authentication_status"]:
    username = st.session_state["username"]
    full_name = st.session_state.authenticator.credentials['usernames'][username]['name']
    user_info = users_df[users_df['username'] == username].iloc[0]

    # --- 🛡️ Forced Password Change ---
    if user_info['first_login']:
        st.warning("⚠️ Security: You must change your password to continue.")
        with st.form("pwd_form"):
            new_p = st.text_input("New Password", type="password")
            conf_p = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Update"):
                if new_p == conf_p and len(new_p) >= 3:
                    users_df.loc[users_df['username'] == username, ['password', 'first_login']] = [new_p, False]
                    users_df.to_csv(users_file, index=False)
                    get_users_df.clear()
                    st.session_state.pop('authenticator', None) # تحديث الذاكرة
                    st.success("Password Updated! Please login again.")
                    st.session_state["authentication_status"] = None
                    st.rerun()
                else: st.error("Mismatch or too short!")
        st.stop()

    st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {full_name}</div>', unsafe_allow_html=True)
    authenticator.logout('Logout', 'sidebar')

    # --- 📊 Statistics (Admin Only) ---
    if username in ['jsafaa', 'ahatim']:
        pending_obs = df_appeals[(df_appeals['Quality Decision'] == 'Pending') | (df_appeals['Direct Manager'] == 'Pending')]
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="stat-card" style="background-color:#E1BEE7;"><div class="stat-label">Total</div><div class="stat-value">{len(df_appeals)}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="background-color:#FFCC80;"><div class="stat-label">Pending</div><div class="stat-value">{len(pending_obs)}</div></div>', unsafe_allow_html=True)
        with c3:
            acc = len(df_appeals[(df_appeals['Quality Decision'] == 'Accepted') & (df_appeals['Direct Manager'] == 'Accepted')])
            st.markdown(f'<div class="stat-card" style="background-color:#C8E6C9;"><div class="stat-label">Fully Accepted</div><div class="stat-value">{acc}</div></div>', unsafe_allow_html=True)

    # --- Tabs ---
    if username == 'jsafaa':
        main_tab, admin_users_tab = st.tabs(["📊 Main System", "👥 Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        if username in ['jsafaa', 'ahatim']:
            st.subheader("🛠 MANAGEMENT CONTROL PANEL")
            
            # عرض الحالة النهائية في الجدول للآدمن
            df_display = df_appeals.copy()
            def get_final_status(row):
                if row['Quality Decision'] == 'Accepted' and row['Direct Manager'] == 'Accepted': return "✅ Fully Accepted"
                if row['Quality Decision'] == 'Rejected' and row['Direct Manager'] == 'Rejected': return "❌ Fully Rejected"
