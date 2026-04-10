import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 🚀 تحسين استجابة الصفحة وتثبيت التنسيق ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- CSS لمعالجة مشكلة اللون الأبيض وضمان وضوح الكتابة ---
st.markdown("""
    <style>
        .main-title { font-size:40px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        div[data-testid="stExpander"] { 
            background-color: rgba(240, 242, 246, 0.5); 
            border-radius: 10px; 
            border: 1px solid #d1d5db;
        }
        .stMarkdown h3 { color: #1E3A8A !important; }
        .user-name-sidebar { color: #4CAF50; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- File Names ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

# --- 🛠️ دوال قراءة البيانات الذكية ---
def get_all_data():
    if 'main_df' not in st.session_state:
        if not os.path.exists(appeals_file):
            pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date", "KPI"]).to_csv(appeals_file, index=False)
        st.session_state.main_df = pd.read_csv(appeals_file)
    return st.session_state.main_df

def get_users_df():
    if 'u_df' not in st.session_state:
        if not os.path.exists(users_file):
            initial_users = ["ahatim", "mkhalid", "hfalah", "hmuayyad", "alimad", "rriyad", "hjabbar", "hmuhammada", "arubayi", "aadil", "ayasin", "fahmad", "hakali", "musadiq", "itsattar", "amusadaq", "aanbari", "afahad", "rthair", "omsubhi", "rwahab", "mlayth", "yasadi", "yriyad", "abfaysal", "hasanhadi", "hamuhsin", "aybasheer", "marmahmud", "abisameer", "jsafaa", "muhahamid", "murqasim", "moayad", "dadnan", "abiabbas", "qriyad", "tmustafa", "sbahnan", "admuhammad", "amohammad", "shzuhayr", "farook"]
            user_data = []
            for u in initial_users:
                p = 'admin123' if u == 'jsafaa' else ('manager123' if u in ['ahatim', 'farook'] else '123')
                # تعديل المسمى الوظيفي لفاروق هنا
                if u == 'farook':
                    role = 'Team Leader'
                elif u == 'ahatim':
                    role = 'Head Of Section'
                elif u == 'jsafaa':
                    role = 'Quality Engineer'
                else:
                    role = 'Employee'
                user_data.append({"username": u, "password": p, "name": u.upper(), "role": role, "Force_Change": True})
            pd.DataFrame(user_data).to_csv(users_file, index=False)
        
        df = pd.read_csv(users_file)
        
        # تحديث بيانات فاروق إذا كان موجوداً مسبقاً بمسمى قديم
        if 'farook' in df['username'].values:
            df.loc[df['username'] == 'farook', 'role'] = 'Team Leader'
            df.to_csv(users_file, index=False)
        else:
            new_user = {"username": "farook", "password": "manager123", "name": "FAROOK", "role": "Team Leader", "Force_Change": True}
            df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
            df.to_csv(users_file, index=False)

        if "Force_Change" not in df.columns:
            df["Force_Change"] = df["password"].astype(str).isin(['123', 'admin123', 'manager123'])
            df.to_csv(users_file, index=False)
        st.session_state.u_df = df
    return st.session_state.u_df

users_df = get_users_df()
df_appeals = get_all_data()

# --- Authenticator Setup ---
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][row['username']] = {'name': f"{row['name']} ({row['role']})", 'password': str(row['password'])}

if 'auth_obj' not in st.session_state:
    st.session_state.auth_obj = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30)

authenticator = st.session_state.auth_obj

# --- App Interface ---
st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

try:
    authenticator.login()
except:
    try: authenticator.login('main')
    except: authenticator.login('Login', 'main')

if st.session_state.get("authentication_status"):
    username = st.session_state.get("username")
    user_row = users_df[users_df['username'] == username].iloc[0]
    needs_change = str(user_row.get('Force_Change', 'False')).lower() == 'true'
    
    if needs_change:
        st.warning("⚠️ Security Alert: You must update your password to proceed.")
        with st.form("force_pass_change"):
            new_pw = st.text_input("Enter New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("Update Password"):
                if not new_pw:
                    st.error("❌ Password cannot be empty.")
                elif new_pw == str(user_row['password']):
                    st.error("❌ Use a password different from the current one.")
                elif new_pw != confirm_pw:
                    st.error("❌ Passwords do not match.")
                else:
                    users_df.loc[users_df['username'] == username, 'password'] = new_pw
                    users_df.loc[users_df['username'] == username, 'Force_Change'] = False
                    users_df.to_csv(users_file, index=False)
                    st.session_state.pop('u_df')
                    st.success("✅ Password updated! Please wait for reload.")
                    st.rerun()
        authenticator.logout('Logout', 'sidebar')
        st.stop()

    if username in credentials['usernames']:
        display_name = credentials['usernames'][username]['name']
        st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {display_name}</div>', unsafe_allow_html=True)
    
    authenticator.logout('Logout', 'sidebar')
    
    # --- إدارة التبويبات حسب الصلاحية ---
    if username in ['jsafaa', 'farook']:
        main_tab, admin_users_tab = st.tabs(["📊 Main System", "👥 Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        if username in ['jsafaa', 'ahatim', 'farook']:
            st.subheader("🛠 MANAGEMENT CONTROL PANEL")
            st.dataframe(df_appeals, use_container_width=True)
            with st.expander("Update Decisions"):
                if not df_appeals.empty:
                    row_idx =
