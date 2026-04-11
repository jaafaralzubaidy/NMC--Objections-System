import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime

# --- 1. إعدادات الصفحة الأساسية ---
st.set_page_config(page_title="NMC Portal", layout="wide")

# --- 2. إدارة البيانات في الذاكرة (للسرعة القصوى) ---
def init_data():
    # تحميل بيانات الموظفين
    if 'u_df' not in st.session_state:
        if not os.path.exists("users_list.csv"):
            # إعداد الحسابات الأساسية
            initial_data = [
                {"username": "jsafaa", "password": "admin123", "name": "SAFAA", "role": "Quality Engineer", "Force_Change": True},
                {"username": "ahatim", "password": "manager123", "name": "HATIM", "role": "Head Of Section", "Force_Change": True},
                {"username": "farook", "password": "manager123", "name": "FAROOK", "role": "Team Leader", "Force_Change": True}
            ]
            pd.DataFrame(initial_data).to_csv("users_list.csv", index=False)
        
        df = pd.read_csv("users_list.csv")
        # التأكد من دور فاروق كـ Team Leader
        if 'farook' in df['username'].values:
            df.loc[df['username'] == 'farook', 'role'] = 'Team Leader'
        st.session_state.u_df = df

    # تحميل بيانات الاعتراضات
    if 'main_df' not in st.session_state:
        if not os.path.exists("database_appeals.csv"):
            cols = ["Employee", "Date", "Ticket Number", "Details", "Quality Decision", "Direct Manager", "Time"]
            pd.DataFrame(columns=cols).to_csv("database_appeals.csv", index=False)
        st.session_state.main_df = pd.read_csv("database_appeals.csv")

init_data()

# --- 3. نظام الدخول السريع ---
users_df = st.session_state.u_df
creds = {'usernames': {}}
for _, r in users_df.iterrows():
    creds['usernames'][r['username']] = {
        'name': f"{r['name']} ({r['role']})",
        'password': str(r['password'])
    }

# حفظ كائن المصادقة في الذاكرة لمنع إعادة إنشائه
if 'authenticator' not in st.session_state:
    st.session_state.authenticator = stauth.Authenticate(creds, 'nmc_cookie', 'nmc_key', cookie_expiry_days=30)

auth = st.session_state.authenticator

# تسجيل الدخول
try:
    auth.login()
except:
    st.info("Login required")

if st.session_state.get("authentication_status"):
    user = st.session_state.get("username")
    u_info = users_df[users_df['username'] == user].iloc[0]
    
    # ميزة جبر التغيير عند أول دخول
    if str(u_info.get('Force_Change', 'False')).lower() == 'true':
        st.warning("Update password to continue.")
        with st.form("fast_pwd"):
            new_p = st.text_input("New Password", type="password")
            if st.form_submit_button("Update"):
                if new_p:
                    st.session_state.u_df.loc[st.session_state.u_df['username'] == user, 'password'] = new_p
                    st.session_state.u_df.loc[st.session_state.u_df['username'] == user, 'Force_Change'] = False
                    st.session_state.u_df.to_csv("users_list.csv", index=False)
                    st.success("Done!")
                    st.rerun()
        st.stop()

    st.sidebar.write(f"👤 {user}")
    auth.logout('Logout', 'sidebar')

    # الصلاحيات
    is_admin = user in ['jsafaa', 'farook']
    is_mgmt = user in ['jsafaa', 'ahatim', 'farook']

    # تم إلغاء خاصية إضافة موظف لزيادة السرعة بناءً على طلبك
    tabs = st.tabs(["📊 System", "🔄 Reset Pass"]) if is_admin else st.tabs(["📊 System"])

    with tabs[0]:
        if is_mgmt:
            st.dataframe(st.session_state.main_df, use_container_width=True)
            with st.expander("Fast Edit"):
                if not st.session_state.main_df.empty:
                    idx = st.number_input("Row ID", 0, len(st.session_state.main_df)-1, 0)
                    c1, c2 = st.columns(2)
                    with c1:
                        # صلاحية صفاء للقرار الفني
                        q_val = st.text_area("Quality", value=st.session_state.main_df.loc[idx, "Quality Decision"], disabled=(user != 'jsafaa'))
                    with c2:
                        # صلاحية المدير المباشر أو فاروق
                        m_val = st.text_area("Manager", value=st.session_state.main_df.loc[idx, "Direct Manager"], disabled=(user == 'jsafaa'))
                    
                    if st.button("Save"):
                        st.session_state.main_df.loc[idx, "Quality Decision"] = q_val
                        st.session_state.main_df.loc[idx, "Direct Manager"] = m_val
                        st.session_state.main_df.to_csv("database_appeals.csv", index=False)
                        st.success("Saved")
        else:
            with st.form("fast_sub"):
                tkt = st.text_input("Ticket #")
                det = st.text_area("Details")
                if st.form_submit_button("Submit"):
                    new_row = {
                        "Employee": user, "Date": str(datetime.now().date()), 
                        "Ticket Number": tkt, "Details": det, 
                        "Quality Decision": "Pending", "Direct Manager": "Pending",
                        "Time": datetime.now().strftime("%H:%M:%S")
                    }
                    st.session_state.main_df = pd.concat([st.session_state.main_df, pd.DataFrame([new_row])], ignore_index=True)
                    st.session_state.main_df.to_csv("database_appeals.csv", index=False)
                    st.rerun()

    if is_admin and len(tabs) > 1:
        with tabs[1]:
            st.subheader("Quick Reset")
            u_sel = st.selectbox("Select User", st.session_state.u_df['username'].values)
            if st.button("Reset to 123"):
                st.session_state.u_df.loc[st.session_state.u_df['username'] == u_sel, 'password'] = "123"
                st.session_state.u_df.loc[st.session_state.u_df['username'] == u_sel, 'Force_Change'] = True
                st.session_state.u_df.to_csv("users_list.csv", index=False)
                st.success(f"User {u_sel} Reset")

elif st.session_state.get("authentication_status") == False:
    st.error("Invalid Credentials")
