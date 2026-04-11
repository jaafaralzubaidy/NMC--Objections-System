import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

st.markdown("""
    <style>
        .main-title { font-size:35px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        .user-name-sidebar { color: #4CAF50; font-weight: bold; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

# --- 2. إدارة الموظفين والبيانات ---
def get_users_df():
    initial_users = [
        "ahatim", "mkhalid", "hfalah", "hmuayyad", "alimad", "rriyad", "hjabbar", 
        "hmuhammada", "arubayi", "aadil", "ayasin", "fahmad", "hakali", "musadiq", 
        "itsattar", "amusadaq", "aanbari", "afahad", "rthair", "omsubhi", "rwahab", 
        "mlayth", "yasadi", "yriyad", "abfaysal", "hasanhadi", "hamuhsin", "aybasheer", 
        "marmahmud", "abisameer", "jsafaa", "muhahamid", "murqasim", "moayad", 
        "dadnan", "abiabbas", "qriyad", "tmustafa", "sbahnan", "admuhammad", 
        "amohammad", "shzuhayr", "farook"
    ]

    if os.path.exists(users_file):
        df = pd.read_csv(users_file)
        existing = df['username'].tolist()
        new_entries = []
        for u in initial_users:
            if u not in existing:
                p = 'admin123' if u == 'jsafaa' else ('manager123' if u in ['ahatim', 'farook'] else '123')
                role = 'Head Of Section' if u == 'ahatim' else ('Team Leader' if u == 'farook' else ('Quality Engineer' if u == 'jsafaa' else 'Employee'))
                new_entries.append({"username": u, "password": p, "name": u.upper(), "role": role, "Force_Change": True})
        if new_entries:
            df = pd.concat([df, pd.DataFrame(new_entries)], ignore_index=True)
            df.to_csv(users_file, index=False)
        return df
    else:
        user_data = []
        for u in initial_users:
            p = 'admin123' if u == 'jsafaa' else ('manager123' if u in ['ahatim', 'farook'] else '123')
            role = 'Head Of Section' if u == 'ahatim' else ('Team Leader' if u == 'farook' else ('Quality Engineer' if u == 'jsafaa' else 'Employee'))
            user_data.append({"username": u, "password": p, "name": u.upper(), "role": role, "Force_Change": True})
        df = pd.DataFrame(user_data)
        df.to_csv(users_file, index=False)
        return df

if 'u_df' not in st.session_state:
    st.session_state.u_df = get_users_df()

if 'main_df' not in st.session_state:
    if os.path.exists(appeals_file):
        st.session_state.main_df = pd.read_csv(appeals_file)
    else:
        cols = ["Employee", "Date", "Ticket Number", "Tab", "KPI", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date"]
        st.session_state.main_df = pd.DataFrame(columns=cols)

# --- 3. نظام المصادقة ---
credentials = {'usernames': {}}
for _, row in st.session_state.u_df.iterrows():
    credentials['usernames'][str(row['username'])] = {
        'name': str(row['name']),
        'password': str(row['password'])
    }

authenticator = stauth.Authenticate(credentials, 'nmc_portal_cookie', 'auth_key_123', cookie_expiry_days=30)

# --- 4. واجهة تسجيل الدخول ---
st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

# استدعاء دالة الدخول وتجنب الأخطاء الشائعة
try:
    authenticator.login()
except Exception:
    try:
        authenticator.login(location='main')
    except Exception:
        authenticator.login('Login', 'main')

if st.session_state.get("authentication_status"):
    username = st.session_state["username"]
    name = st.session_state["name"]
    
    # جلب بيانات المستخدم الحالي (تم تصحيح الأقواس هنا)
    user_row = st.session_state.u_df[st.session_state.u_df['username'] == username].iloc[0]

    # إجبار تغيير الباسوورد للموظفين الجدد
    if str(user_row['Force_Change']).lower() == 'true':
        st.warning("⚠️ Security: Please update your password to proceed.")
        with st.form("reset_form"):
            new_p = st.text_input("New Password", type="password")
            if st.form_submit_button("Update Password"):
                if new_p and new_p != "123":
                    st.session_state.u_df.loc[st.session_state.u_df['username'] == username, 'password'] = new_p
                    st.session_state.u_df.loc[st.session_state.u_df['username'] == username, 'Force_Change'] = False
                    st.session_state.u_df.to_csv(users_file, index=False)
                    st.success("Updated! Please refresh.")
                    st.rerun()
        st.stop()

    # الواجهة الجانبية
    st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {name}</div>', unsafe_allow_html=True)
    authenticator.logout('Logout', 'sidebar')

    # الصلاحيات
    is_admin = username in ['jsafaa', 'farook']
    is_mgmt = username in ['jsafaa', 'ahatim', 'farook']

    # نظام التبويبات
    if is_admin:
        t1, t2, t3 = st.tabs(["📊 Dashboard", "📤 Submit", "👥 Manage Staff"])
    elif is_mgmt:
        t1, t2 = st.tabs(["📊 Dashboard", "📤 Submit"])
    else:
        t1, t2 = st.tabs(["📤 Submit", "📜 History"])

    # لوحة المدير
    if is_mgmt:
        with t1:
            st.subheader("Submissions List")
            st.dataframe(st.session_state.main_df, use_container_width=True)

    # نموذج الاعتراض
    target_tab = t2 if is_mgmt else t1
    with target_tab:
        st.subheader("New Objection")
        with st.form("obj_form"):
            tkt = st.text_input("Ticket ID")
            dtls = st.text_area("Reason")
            if st.form_submit_button("Send"):
                st.success("Recorded")

    # إدارة الموظفين
    if is_admin:
        with t3:
            st.subheader("Employee Management")
            target = st.selectbox("Select Staff", st.session_state.u_df['username'].unique())
            if st.button("Reset to Default (123)"):
                st.session_state.u_df.loc[st.session_state.u_df['username'] == target, 'password'] = "123"
                st.session_state.u_df.loc[st.session_state.u_df['username'] == target, 'Force_Change'] = True
                st.session_state.u_df.to_csv(users_file, index=False)
                st.success(f"User {target} reset successfully.")

elif st.session_state.get("authentication_status") is False:
    st.error('Incorrect username or password')
elif st.session_state.get("authentication_status") is None:
    st.info('Please log in')
