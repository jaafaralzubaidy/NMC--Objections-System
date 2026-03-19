import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 🚀 إعدادات الصفحة ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- تحسين المظهر ---
st.markdown("""
    <style>
        .main-title { font-size:40px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        div[data-testid="stExpander"] { background-color: rgba(240, 242, 246, 0.1); border-radius: 10px; }
        /* تنسيق اسم المستخدم في القائمة الجانبية */
        .user-profile { font-size: 20px; color: #4CAF50; font-weight: bold; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- الملفات ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

# --- 🛠️ إدارة البيانات ---
def get_users_df():
    if 'u_df' not in st.session_state:
        if not os.path.exists(users_file):
            initial_users = ["ahatim", "jsafaa", "mkhalid", "hfalah"] # قائمة مختصرة للمثال
            user_data = []
            for u in initial_users:
                p = 'admin123' if u == 'jsafaa' else ('manager123' if u == 'ahatim' else '123')
                role = 'Head Of Section' if u == 'ahatim' else ('Quality Engineer' if u == 'jsafaa' else 'Employee')
                user_data.append({"username": u, "password": p, "name": u.upper(), "role": role})
            pd.DataFrame(user_data).to_csv(users_file, index=False)
        st.session_state.u_df = pd.read_csv(users_file)
    return st.session_state.u_df

def get_all_data():
    if 'main_df' not in st.session_state:
        if not os.path.exists(appeals_file):
            pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date"]).to_csv(appeals_file, index=False)
        st.session_state.main_df = pd.read_csv(appeals_file)
    return st.session_state.main_df

users_df = get_users_df()
df_appeals = get_all_data()

# --- إعداد نظام الدخول ---
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][row['username']] = {
        'name': f"{row['name']} ({row['role']})",
        'password': str(row['password'])
    }

authenticator = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30)

# --- واجهة تسجيل الدخول ---
try:
    authenticator.login()
except:
    authenticator.login('main')

if st.session_state.get("authentication_status"):
    # 💡 الحل: سحب الاسم والدور بشكل مباشر وصحيح
    username = st.session_state["username"]
    full_display_name = credentials['usernames'][username]['name']
    
    # عرض الاسم في القائمة الجانبية (مثل الصورة image_3382b7)
    st.sidebar.markdown(f'<div class="user-profile">👤 {full_display_name}</div>', unsafe_allow_html=True)
    authenticator.logout('Logout', 'sidebar')

    st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

    if username == 'jsafaa':
        main_tab, admin_users_tab = st.tabs(["📊 Main System", "👥 Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        if username in ['jsafaa', 'ahatim']:
            st.subheader("🛠 MANAGEMENT CONTROL PANEL")
            st.dataframe(df_appeals, use_container_width=True)
            
            with st.expander("Update Decisions"):
                if not df_appeals.empty:
                    # 💡 إصلاح خطأ الـ MaxValue: نستخدم len-1 فقط إذا كان أكبر من 0
                    max_idx = len(df_appeals) - 1
                    row_idx = st.number_input("Select Row ID", 0, max_idx, 0)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        q_dec = st.text_area("Quality Decision", value=df_appeals.loc[row_idx, "Quality Decision"], disabled=(username == 'ahatim'))
                    with col2:
                        m_dec = st.text_area("Head Of Section Decision", value=df_appeals.loc[row_idx, "Direct Manager"], disabled=(username == 'jsafaa'))
                    
                    if st.button("Save Changes"):
                        df_appeals.loc[row_idx, "Quality Decision"] = q_dec
                        df_appeals.loc[row_idx, "Direct Manager"] = m_dec
                        df_appeals.to_csv(appeals_file, index=False)
                        st.session_state.pop('main_df')
                        st.success("Updated!")
                        st.rerun()
                else:
                    st.info("No records available to update.") # تظهر كما في الصورة image_3382b7

        else:
            # واجهة الموظف العادي
            t_sub, t_hist = st.tabs(["📤 Submit", "📜 History"])
            with t_sub:
                with st.form("obj_form", clear_on_submit=True):
                    f_date = st.date_input("Date", datetime.now())
                    f_ticket = st.text_input("Ticket Number")
                    f_tab = st.selectbox("Tab", ["SWITCH STATE", "MPLS", "Wireless", "Power"])
                    f_details = st.text_area("Details")
                    
                    if st.form_submit_button("Submit"):
                        submission_time = (datetime.utcnow() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
                        new_row = {
                            "Employee": full_display_name, # حفظ الاسم الكامل
                            "Date": str(f_date),
                            "Ticket Number": f_ticket,
                            "Tab": f_tab,
                            "Details": f_details,
                            "Quality Decision": "Pending",
                            "Direct Manager": "Pending",
                            "Objection Issue Date": submission_time
                        }
                        updated_df = pd.concat([df_appeals, pd.DataFrame([new_row])], ignore_index=True)
                        updated_df.to_csv(appeals_file, index=False)
                        st.session_state.main_df = updated_df
                        st.success("Submitted!")

            with t_hist:
                st.dataframe(df_appeals[df_appeals['Employee'] == full_display_name], use_container_width=True)

    # تبويب إدارة الموظفين لـ jsafaa
    if username == 'jsafaa' and 'admin_users_tab' in locals():
        with admin_users_tab:
            st.subheader("👥 Staff Management")
            # وضعنا خيارات الحذف وغيرها هنا.. مع التأكد من وجود موظفين للحذف (إصلاح الصورة image_337ad8)
            other_users = [u for u in users_df['username'].values if u != 'jsafaa']
            if other_users:
                del_user = st.selectbox("Select to Delete", other_users)
                if st.button("Delete"):
                    users_df = users_df[users_df['username'] != del_user]
                    users_df.to_csv(users_file, index=False)
                    st.session_state.pop('u_df')
                    st.rerun()
            else:
                st.write("No options to select")

elif st.session_state.get("authentication_status") == False:
    st.error("Username/password is incorrect")
