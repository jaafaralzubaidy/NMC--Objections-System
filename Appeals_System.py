import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 🚀 Page Configuration ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- ⚡ البيانات والجلسة ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

if 'df_appeals' not in st.session_state:
    if not os.path.exists(appeals_file):
        pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "KPI", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date", "Admin Notes"]).to_csv(appeals_file, index=False)
    st.session_state.df_appeals = pd.read_csv(appeals_file)

if 'users_df' not in st.session_state:
    if not os.path.exists(users_file):
        initial_users = ["ahatim", "jsafaa"] # الأساسيين
        user_data = [{"username": u, "password": ('admin123' if u == 'jsafaa' else 'manager123'), "name": u.upper(), "role": ('Head Of Section' if u == 'ahatim' else 'Quality Engineer'), "first_login": False} for u in initial_users]
        pd.DataFrame(user_data).to_csv(users_file, index=False)
    st.session_state.users_df = pd.read_csv(users_file)

# --- 🔐 نظام المصادقة السريع ---
if 'authenticator' not in st.session_state:
    credentials = {'usernames': {}}
    for row in st.session_state.users_df.itertuples(index=False):
        credentials['usernames'][str(row.username)] = {'name': str(row.name), 'password': str(row.password), 'role': str(row.role)}
    st.session_state.authenticator = stauth.Authenticate(credentials, 'nmc_objections_cookie', 'auth_key_123', cookie_expiry_days=30)

authenticator = st.session_state.authenticator

# --- Custom CSS ---
st.markdown("""
    <style>
        .main-title { font-size:40px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        div[data-testid="stExpander"] { background-color: rgba(240, 242, 246, 0.5); border-radius: 10px; border: 1px solid #d1d5db; }
        .user-name-sidebar { color: #4CAF50; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
        .stat-card { padding: 20px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

res = authenticator.login('main')

if st.session_state["authentication_status"]:
    username = st.session_state["username"]
    user_info = st.session_state.users_df[st.session_state.users_df['username'] == username].iloc[0]
    
    # رسالة تغيير الباسوورد الإجبارية
    if user_info['first_login']:
        st.warning("⚠️ Security: Please set a new password.")
        with st.form("reset_pwd"):
            new_p = st.text_input("New Password", type="password")
            if st.form_submit_button("Save"):
                st.session_state.users_df.loc[st.session_state.users_df['username'] == username, ['password', 'first_login']] = [new_p, False]
                st.session_state.users_df.to_csv(users_file, index=False)
                st.success("Done! Please logout and login again."); st.stop()
        st.stop()

    st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {user_info["name"]}</div>', unsafe_allow_html=True)
    authenticator.logout('Logout', 'sidebar')

    # --- Tabs ---
    if username == 'jsafaa':
        main_tab, admin_users_tab = st.tabs(["📊 Main System", "👥 Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        # (هنا كود عرض الجداول والاعتراضات كما هو في نسختك الأصلية)
        st.write("Welcome to the main system dashboard.")

    # --- 👥 قسم إدارة الموظفين (المحدث) ---
    if username == 'jsafaa':
        with admin_users_tab:
            st.subheader("👥 Staff Management Console")

            # 1. إضافة موظف
            with st.expander("➕ Add New Employee"):
                nu = st.text_input("Username").lower().strip()
                nn = st.text_input("Display Name")
                if st.button("Register"):
                    if nu and nu not in st.session_state.users_df['username'].values:
                        new_u = {"username": nu, "password": "123", "name": nn, "role": "Employee", "first_login": True}
                        st.session_state.users_df = pd.concat([st.session_state.users_df, pd.DataFrame([new_u])], ignore_index=True)
                        st.session_state.users_df.to_csv(users_file, index=False)
                        # تحديث الـ Authenticator بالذاكرة فوراً
                        st.session_state.authenticator.credentials['usernames'][nu] = {'name': nn, 'password': '123', 'role': 'Employee'}
                        st.success(f"User {nu} added successfully!"); st.rerun()

            # 2. ريسيت باسوورد
            with st.expander("🔑 Reset Employee Password"):
                user_to_reset = st.selectbox("Select Employee to Reset", st.session_state.users_df['username'].values)
                if st.button("Reset to Default (123)"):
                    st.session_state.users_df.loc[st.session_state.users_df['username'] == user_to_reset, ['password', 'first_login']] = ["123", True]
                    st.session_state.users_df.to_csv(users_file, index=False)
                    # تحديث الذاكرة
                    st.session_state.authenticator.credentials['usernames'][user_to_reset]['password'] = '123'
                    st.success(f"Password for {user_to_reset} has been reset to 123."); st.rerun()

            # 3. مسح موظف
            with st.expander("🗑️ Delete Employee Account"):
                # استثناء المشرفين من قائمة المسح للأمان
                deletable_users = [u for u in st.session_state.users_df['username'].values if u not in ['jsafaa', 'ahatim']]
                user_to_delete = st.selectbox("Select Employee to Remove", deletable_users)
                confirm = st.checkbox(f"I confirm deleting {user_to_delete}")
                if st.button("Confirm Delete") and confirm:
                    # حذف من الداتا فريم
                    st.session_state.users_df = st.session_state.users_df[st.session_state.users_df['username'] != user_to_delete]
                    st.session_state.users_df.to_csv(users_file, index=False)
                    # حذف من نظام المصادقة في الذاكرة
                    if user_to_delete in st.session_state.authenticator.credentials['usernames']:
                        del st.session_state.authenticator.credentials['usernames'][user_to_delete]
                    st.warning(f"User {user_to_delete} removed from system."); st.rerun()

elif st.session_state["authentication_status"] is False: st.error("Username/password is incorrect")
elif st.session_state["authentication_status"] is None: st.info("Please enter your username and password")
