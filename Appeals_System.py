import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime

# --- 🚀 Page Configuration ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- Custom CSS ---
st.markdown("""
    <style>
        .main-title { font-size:40px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        .stat-card { padding: 20px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 10px; }
        .stat-label { font-size: 18px; font-weight: bold; color: #1A1A1A !important; }
        .stat-value { font-size: 36px; font-weight: bold; color: #000000 !important; }
        div[data-testid="stExpander"] { background-color: rgba(240, 242, 246, 0.5); border-radius: 10px; border: 1px solid #d1d5db; }
    </style>
""", unsafe_allow_html=True)

# --- 📁 File Handling ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

def load_data():
    if not os.path.exists(appeals_file):
        pd.DataFrame(columns=["Employee", "Incident Date", "Ticket Number", "KPI", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date", "Admin Comment"]).to_csv(appeals_file, index=False)
    if not os.path.exists(users_file):
        # اليوزرات الافتراضية إذا انمسح الملف
        initial_users = [
            {"username": "jsafaa", "password": "123", "name": "JASFAA", "role": "Quality Engineer", "first_login": True},
            {"username": "ahatim", "password": "123", "name": "AHATIM", "role": "Head Of Section", "first_login": True}
        ]
        pd.DataFrame(initial_users).to_csv(users_file, index=False)
    return pd.read_csv(appeals_file), pd.read_csv(users_file)

df_appeals, users_df = load_data()

# --- 🔐 Authenticator ---
# نحول البيانات إلى القاموس المطلوب للمكتبة
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][str(row['username'])] = {
        'name': str(row['name']),
        'password': str(row['password'])
    }

authenticator = stauth.Authenticate(credentials, 'nmc_cookie', 'auth_key', cookie_expiry_days=30)

# محاولة تسجيل الدخول
try:
    authenticator.login('main')
except Exception as e:
    st.error("Login Component Error. Please refresh.")

if st.session_state["authentication_status"]:
    username = st.session_state["username"]
    full_name = st.session_state["name"]
    
    # جلب بيانات اليوزر الحالي من الملف مباشرة للتأكد من حالة first_login
    user_info = users_df[users_df['username'] == username].iloc[0]

    # --- 🛡️ Forced Password Change ---
    if user_info['first_login']:
        st.warning("🔒 Security: You must change your password from '123' to a new one.")
        with st.form("force_password_change"):
            new_pwd = st.text_input("New Password", type="password")
            conf_pwd = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("Update Password"):
                if new_pwd == conf_pwd and len(new_pwd) >= 3:
                    # تحديث الملف
                    users_df.loc[users_df['username'] == username, ['password', 'first_login']] = [new_pwd, False]
                    users_df.to_csv(users_file, index=False)
                    st.success("Password updated! Please log in again with your new password.")
                    st.session_state["authentication_status"] = None # تسجيل خروج للإجبار على الدخول بالجديد
                    st.rerun()
                else:
                    st.error("Passwords don't match or too short!")
        st.stop()

    # --- Sidebar ---
    st.sidebar.markdown(f"### 👤 {full_name}")
    authenticator.logout('Logout', 'sidebar')

    # --- 📊 Admin Stats ---
    if username in ['jsafaa', 'ahatim']:
        pending = len(df_appeals[(df_appeals['Quality Decision'] == 'Pending') | (df_appeals['Direct Manager'] == 'Pending')])
        decided = len(df_appeals[
            ((df_appeals['Quality Decision'] == 'Approved') & (df_appeals['Direct Manager'] == 'Approved')) | 
            ((df_appeals['Quality Decision'] == 'Rejected') & (df_appeals['Direct Manager'] == 'Rejected'))
        ])
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="stat-card" style="background-color:#e3f2fd;"><div class="stat-label">Total Objections</div><div class="stat-value">{len(df_appeals)}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="background-color:#fff3e0;"><div class="stat-label">Pending Review</div><div class="stat-value">{pending}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card" style="background-color:#e8f5e9;"><div class="stat-label">Fully Accepted/Rejected</div><div class="stat-value">{decided}</div></div>', unsafe_allow_html=True)
        st.divider()

    # --- Tabs ---
    if username == 'jsafaa':
        main_tab, admin_tab = st.tabs(["📊 Main System", "👥 Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        if username in ['jsafaa', 'ahatim']:
            st.subheader("🛠 Management Control Panel")
            st.dataframe(df_appeals, use_container_width=True)
            with st.expander("Update Decisions & Notes"):
                if not df_appeals.empty:
                    row_idx = st.number_input("Row Index", 0, len(df_appeals)-1, 0)
                    col1, col2, col3 = st.columns(3)
                    opts = ["Pending", "Approved", "Rejected"]
                    with col1:
                        new_q = st.selectbox("Quality", opts, index=opts.index(df_appeals.loc[row_idx, "Quality Decision"]), disabled=(username=='ahatim'))
                    with col2:
                        new_m = st.selectbox("Manager", opts, index=opts.index(df_appeals.loc[row_idx, "Direct Manager"]), disabled=(username=='jsafaa'))
                    with col3:
                        new_note = st.text_area("Admin Notes/Comment", value=str(df_appeals.loc[row_idx, "Admin Comment"]))
                    
                    if st.button("Save Changes"):
                        df_appeals.loc[row_idx, ["Quality Decision", "Direct Manager", "Admin Comment"]] = [new_q, new_m, new_note]
                        df_appeals.to_csv(appeals_file, index=False)
                        st.success("Saved!"); st.rerun()
        else:
            t1, t2 = st.tabs(["📤 Submit Objection", "📜 History"])
            with t1:
                with st.form("obj_form", clear_on_submit=True):
                    f_date = st.date_input("Incident Date")
                    f_ticket = st.text_input("Ticket Number")
                    f_kpi = st.selectbox("KPI Type", ["Done Delay", "Done Delay Response", "High MTTD", "Shift Delay", "Delay High Impact", "Closing Issue", "Reduce Number Of Incident", "FMS", "Delay FMS", "Number Of Delay FMS", "No Task"])
                    f_tab = st.selectbox("Department", ["SWITCH STATE
