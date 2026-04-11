import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- CSS لتحسين الواجهة ---
st.markdown("""
    <style>
        .main-title { font-size:35px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        .user-name-sidebar { color: #4CAF50; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

# --- 2. دالة إدارة المستخدمين (المحدثة لضمان ظهور الجميع) ---
def get_users_df():
    # قائمة الموظفين الكاملة التي تريدها
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
        # فحص إذا كان هناك موظفين في القائمة أعلاه غير موجودين في الملف الحالي
        existing_users = df['username'].tolist()
        new_entries = []
        for u in initial_users:
            if u not in existing_users:
                p = 'admin123' if u == 'jsafaa' else ('manager123' if u in ['ahatim', 'farook'] else '123')
                role = 'Head Of Section' if u == 'ahatim' else ('Team Leader' if u == 'farook' else ('Quality Engineer' if u == 'jsafaa' else 'Employee'))
                new_entries.append({"username": u, "password": p, "name": u.upper(), "role": role, "Force_Change": True})
        
        if new_entries:
            df = pd.concat([df, pd.DataFrame(new_entries)], ignore_index=True)
            df.to_csv(users_file, index=False)
    else:
        # إنشاء الملف لأول مرة بالكامل
        user_data = []
        for u in initial_users:
            p = 'admin123' if u == 'jsafaa' else ('manager123' if u in ['ahatim', 'farook'] else '123')
            role = 'Head Of Section' if u == 'ahatim' else ('Team Leader' if u == 'farook' else ('Quality Engineer' if u == 'jsafaa' else 'Employee'))
            user_data.append({"username": u, "password": p, "name": u.upper(), "role": role, "Force_Change": True})
        df = pd.DataFrame(user_data)
        df.to_csv(users_file, index=False)
    
    return df

# تحميل البيانات في الذاكرة
if 'u_df' not in st.session_state:
    st.session_state.u_df = get_users_df()

if 'main_df' not in st.session_state:
    if os.path.exists(appeals_file):
        st.session_state.main_df = pd.read_csv(appeals_file)
    else:
        st.session_state.main_df = pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "KPI", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date"])

# --- 3. إعداد نظام الدخول ---
users_df = st.session_state.u_df
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][str(row['username'])] = {
        'name': f"{row['name']} ({row['role']})",
        'password': str(row['password'])
    }

# حفظ كائن Authenticator في الذاكرة لمنع أخطاء إعادة التحميل
if 'auth_obj' not in st.session_state:
    st.session_state.auth_obj = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30)

authenticator = st.session_state.auth_obj

# --- 4. واجهة التطبيق ---
st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

# محاولة تسجيل الدخول
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    # جلب بيانات المستخدم الحالي من الذاكرة
    user_row = st.session_state.u_df[st.session_state.u_df['username'] == username].iloc[0]
    
    # ميزة إجبار تغيير الباسوورد
    if str(user_row['Force_Change']).lower() == 'true':
        st.warning("⚠️ Security Alert: You must update your password to proceed.")
        with st.form("force_pass_change"):
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("Update Password"):
                if new_pw and new_pw == confirm_pw and new_pw != str(user_row['password']):
                    st.session_state.u_df.loc[st.session_state.u_df['username'] == username, 'password'] = new_pw
                    st.session_state.u_df.loc[st.session_state.u_df['username'] == username, 'Force_Change'] = False
                    st.session_state.u_df.to_csv(users_file, index=False)
                    st.success("✅ Password updated! Please refresh.")
                    st.rerun()
                else:
                    st.error("❌ Password error (empty, weak, or mismatch)")
        st.stop()

    # القائمة الجانبية
    st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {name}</div>', unsafe_allow_html=True)
    authenticator.logout('Logout', 'sidebar')

    # الصلاحيات
    is_admin = username in ['jsafaa', 'farook']
    is_mgmt = username in ['jsafaa', 'ahatim', 'farook']

    # التبويبات
    if is_admin:
        tabs = st.tabs(["📊 Main System", "👥 Manage Staff"])
    else:
        tabs = [st.container()] # لغير الأدمن يظهر النظام مباشرة

    # --- تبويب النظام الأساسي ---
    current_tab = tabs[0]
    with current_tab:
        if is_mgmt:
            st.subheader("🛠 MANAGEMENT CONTROL PANEL")
            st.dataframe(st.session_state.main_df, use_container_width=True)
            # كود التعديل السريع للمدراء هنا...
        else:
            # واجهة الموظف لتقديم الاعتراضات هنا...
            st.info("Employee Section Loaded")

    # --- تبويب إدارة الموظفين (لـ Quality Engineer فقط) ---
    if is_admin:
        with tabs[1]:
            st.subheader("👥 Employee Directory Management")
            
            # عرض عدد الموظفين للتأكد
            st.write(f"Total Staff Registered: {len(st.session_state.u_df)}")

            with st.expander("🔑 Change/Reset Employee Password"):
                # القائمة المنسدلة الآن تقرأ من كل اليوزرات الموجودة في الذاكرة
                target_user = st.selectbox("Select User", st.session_state.u_df['username'].unique())
                new_pass = st.text_input("New Password", type="password", key="admin_pwd")
                if st.button("Update and Force Change"):
                    st.session_state.u_df.loc[st.session_state.u_df['username'] == target_user, 'password'] = new_pass
                    st.session_state.u_df.loc[st.session_state.u_df['username'] == target_user, 'Force_Change'] = True
                    st.session_state.u_df.to_csv(users_file, index=False)
                    st.success(f"Password for {target_user} updated!")
                    st.rerun()

elif authentication_status == False:
    st.error("Username/password is incorrect")
