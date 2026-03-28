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

# 1. تأكد من وجود ملف الاعتراضات
if not os.path.exists(appeals_file):
    cols = ["Employee", "Incident Date", "Ticket Number", "KPI", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date", "Admin Comment"]
    pd.DataFrame(columns=cols).to_csv(appeals_file, index=False)

# 2. تأكد من وجود ملف المستخدمين (لا تمسحه إذا كان موجوداً)
if not os.path.exists(users_file):
    initial_users = [
        {"username": "jsafaa", "password": "123", "name": "JASFAA", "role": "Quality Engineer", "first_login": True},
        {"username": "ahatim", "password": "123", "name": "AHATIM", "role": "Head Of Section", "first_login": True}
    ]
    pd.DataFrame(initial_users).to_csv(users_file, index=False)

# 3. قراءة البيانات الحالية
df_appeals = pd.read_csv(appeals_file)
users_df = pd.read_csv(users_file)

# --- 🔐 Authenticator Setup ---
# تحضير اليوزرات لعملية اللوكن
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][str(row['username'])] = {
        'name': str(row['name']),
        'password': str(row['password'])
    }

authenticator = stauth.Authenticate(credentials, 'nmc_cookie', 'auth_key', cookie_expiry_days=30)

# واجهة تسجيل الدخول
authenticator.login('main')

if st.session_state["authentication_status"]:
    username = st.session_state["username"]
    full_name = st.session_state["name"]
    
    # جلب بيانات المستخدم بدقة من الملف
    user_info = users_df[users_df['username'] == username].iloc[0]

    # --- 🔒 إجبار تغيير الباسورد ---
    if user_info['first_login']:
        st.warning("🔒 Security: Change your password from '123' to continue.")
        with st.form("pwd_change"):
            new_p = st.text_input("New Password", type="password")
            conf_p = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Update Password"):
                if new_p == conf_p and len(new_p) >= 3:
                    users_df.loc[users_df['username'] == username, ['password', 'first_login']] = [new_p, False]
                    users_df.to_csv(users_file, index=False)
                    st.success("Success! Please log in again with your new password.")
                    st.session_state["authentication_status"] = None
                    st.rerun()
                else: st.error("Passwords mismatch or too short!")
        st.stop()

    st.sidebar.markdown(f"### 👤 {full_name}")
    authenticator.logout('Logout', 'sidebar')

    # --- 📊 الإحصائيات للإدارة ---
    if username in ['jsafaa', 'ahatim']:
        pending = len(df_appeals[(df_appeals['Quality Decision'] == 'Pending') | (df_appeals['Direct Manager'] == 'Pending')])
        decided = len(df_appeals[
            ((df_appeals['Quality Decision'] == 'Approved') & (df_appeals['Direct Manager'] == 'Approved')) | 
            ((df_appeals['Quality Decision'] == 'Rejected') & (df_appeals['Direct Manager'] == 'Rejected'))
        ])
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="stat-card" style="background-color:#e3f2fd;"><div class="stat-label">Total Objections</div><div class="stat-value">{len(df_appeals)}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="background-color:#fff3e0;"><div class="stat-label">Pending Review</div><div class="stat-value">{pending}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card" style="background-color:#e8f5e9;"><div class="stat-label">Fully Decided</div><div class="stat-value">{decided}</div></div>', unsafe_allow_html=True)

    # --- التبويبات ---
    if username == 'jsafaa':
        main_tab, admin_tab = st.tabs(["📊 Main System", "👥 Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        if username in ['jsafaa', 'ahatim']:
            st.subheader("🛠 Management Control Panel")
            st.dataframe(df_appeals, use_container_width=True)
            with st.expander("Update Decisions"):
                if not df_appeals.empty:
                    idx = st.number_input("Select Row Index", 0, len(df_appeals)-1, 0)
                    col1, col2, col3 = st.columns(3)
                    opts = ["Pending", "Approved", "Rejected"]
                    with col1: nq = st.selectbox("Quality", opts, index=opts.index(df_appeals.loc[idx, "Quality Decision"]), disabled=(username=='ahatim'))
                    with col2: nm = st.selectbox("Manager", opts, index=opts.index(df_appeals.loc[idx, "Direct Manager"]), disabled=(username=='jsafaa'))
                    with col3: note = st.text_area("Admin Note", value=str(df_appeals.loc[idx, "Admin Comment"]))
                    if st.button("Save Changes"):
                        df_appeals.loc[idx, ["Quality Decision", "Direct Manager", "Admin Comment"]] = [nq, nm, note]
                        df_appeals.to_csv(appeals_file, index=False)
                        st.success("Saved!"); st.rerun()
        else:
            t1, t2 = st.tabs(["📤 Submit Objection", "📜 History"])
            with t1:
                with st.form("obj_form", clear_on_submit=True):
                    f_date = st.date_input("Incident Date")
                    f_ticket = st.text_input("Ticket Number")
                    f_kpi = st.selectbox("KPI Type", ["Done Delay", "Done Delay Response", "High MTTD", "Shift Delay", "Delay High Impact", "Closing Issue", "Reduce Number Of Incident", "FMS", "Delay FMS", "Number Of Delay FMS", "No Task"])
                    f_tab = st.selectbox("Department", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Wireless", "Power", "ITPC", "Server Room"])
                    f_details = st.text_area("Details")
                    if st.form_submit_button("Submit"):
                        new_row = {"Employee": full_name, "Incident Date": str(f_date), "Ticket Number": f_ticket, "KPI": f_kpi, "Tab": f_tab, "Details": f_details, "Quality Decision": "Pending", "Direct Manager": "Pending", "Objection Issue Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Admin Comment": ""}
                        df_appeals = pd.concat([df_appeals, pd.DataFrame([new_row])], ignore_index=True)
                        df_appeals.to_csv(appeals_file, index=False)
                        st.success("Submitted!"); st.rerun()
            with t2:
                # عرض هستوري الموظف فقط
                st.dataframe(df_appeals[df_appeals['Employee'] == full_name], use_container_width=True)

    # --- إدارة الموظفين (فقط لجاسم) ---
    if username == 'jsafaa':
        with admin_tab:
            st.subheader("👥 Staff Management")
            # 1. إضافة موظف
            with st.expander("➕ Add New Employee"):
                nu = st.text_input("Username (Login Name)").lower().strip()
                nn = st.text_input("Full Display Name")
                if st.button("Add Account"):
                    if nu and nu not in users_df['username'].values:
                        new_entry = pd.DataFrame([{"username": nu, "password": "123", "name": nn.upper(), "role": "Employee", "first_login": True}])
                        users_df = pd.concat([users_df, new_entry], ignore_index=True)
                        users_df.to_csv(users_file, index=False)
                        st.success(f"User {nu} added successfully!"); st.rerun()
                    else: st.error("Username already exists or empty!")

            # 2. تصفير أو حذف
            with st.expander("🔑 Reset / 🗑️ Delete Account"):
                all_users = users_df['username'].tolist()
                target = st.selectbox("Select Account", all_users)
                if st.button("Reset Password to 123"):
                    users_df.loc[users_df['username'] == target, ['password', 'first_login']] = ["123", True]
                    users_df.to_csv(users_file, index=False)
                    st.success(f"Password for {target} is now 123. They will be forced to change it.")
                
                if st.button("Confirm Delete Account", type="primary"):
                    if target not in ['jsafaa', 'ahatim']:
                        users_df = users_df[users_df['username'] != target]
                        users_df.to_csv(users_file, index=False)
                        st.warning(f"Account {target} deleted!"); st.rerun()
                    else: st.error("Cannot delete admin accounts!")

elif st.session_state["authentication_status"] is False:
    st.error("Username/password is incorrect")
elif st.session_state["authentication_status"] is None:
    st.info("Please enter your username and password")
