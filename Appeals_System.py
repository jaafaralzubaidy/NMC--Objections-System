import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
import io
from datetime import datetime, timedelta

# --- 🚀 Page Configuration ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- 🎨 Custom CSS (تنسيق البطاقات والألوان) ---
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

# --- 📂 Data Files Setup (حل مشكلة الملفات الفارغة) ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

def check_csv(file, columns):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(file, index=False)

check_csv(appeals_file, ["Employee", "Date", "Ticket Number", "KPI", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date", "Admin Notes"])

# --- ⚡ Session State ---
if 'users_df' not in st.session_state:
    if not os.path.exists(users_file) or os.stat(users_file).st_size == 0:
        # حل خطأ السطر 34: صياغة أنظف لبيانات المستخدمين
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

# --- 🔐 Authenticator ---
if 'authenticator' not in st.session_state:
    creds = {'usernames': {}}
    for row in st.session_state.users_df.itertuples(index=False):
        creds['usernames'][str(row.username)] = {'name': str(row.name), 'password': str(row.password), 'role': str(row.role)}
    st.session_state.authenticator = stauth.Authenticate(creds, 'nmc_objections_cookie', 'auth_key_123', cookie_expiry_days=30)

authenticator = st.session_state.authenticator

# --- 📤 Excel Function ---
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
    
    st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {user_info["name"]}</div>', unsafe_allow_html=True)
    authenticator.logout('Logout', 'sidebar')

    # --- 📊 Dashboard Statistics (إرجاع الإحصائيات) ---
    if username in ['jsafaa', 'ahatim']:
        df = st.session_state.df_appeals
        c1, c2, c3 = st.columns(3)
        with c1: 
            st.markdown(f'<div class="stat-card" style="background-color:#e3f2fd; border-color:#1565c0;"><div class="stat-label" style="color:#1565c0;">Total Objections</div><div class="stat-value">{len(df)}</div></div>', unsafe_allow_html=True)
        with c2: 
            p = len(df[(df['Quality Decision'] == 'Pending') | (df['Direct Manager'] == 'Pending')])
            st.markdown(f'<div class="stat-card" style="background-color:#fff3e0; border-color:#ef6c00;"><div class="stat-label" style="color:#ef6c00;">Pending Review</div><div class="stat-value">{p}</div></div>', unsafe_allow_html=True)
        with c3:
            acc = len(df[(df['Quality Decision'] == 'Accepted') & (df['Direct Manager'] == 'Accepted')])
            st.markdown(f'<div class="stat-card" style="background-color:#e8f5e9; border-color:#2e7d32;"><div class="stat-label" style="color:#2e7d32;">Fully Accepted</div><div class="stat-value">{acc}</div></div>', unsafe_allow_html=True)

    # --- Tabs ---
    if username == 'jsafaa':
        main_tab, admin_users_tab = st.tabs(["📊 Main System", "👥 Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        if username in ['jsafaa', 'ahatim']:
            st.subheader("🛠 MANAGEMENT CONTROL PANEL")
            # عرض الجدول مع الحالة النهائية
            df_display = st.session_state.df_appeals.copy()
            df_display['Status'] = df_display.apply(lambda r: "✅ Accepted" if r['Quality Decision'] == 'Accepted' and r['Direct Manager'] == 'Accepted' else ("❌ Rejected" if r['Quality Decision'] == 'Rejected' and r['Direct Manager'] == 'Rejected' else "⏳ Processing"), axis=1)
            st.dataframe(df_display, use_container_width=True)

            with st.expander("Update Decision"):
                if not st.session_state.df_appeals.empty:
                    idx = st.number_input("Row Index", 0, len(st.session_state.df_appeals)-1, 0)
                    col1, col2 = st.columns(2)
                    with col1:
