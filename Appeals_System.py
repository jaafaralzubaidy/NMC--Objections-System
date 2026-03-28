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

# --- 🛠️ Data Loading Functions ---
def get_all_data():
    if not os.path.exists(appeals_file):
        pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "KPI", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date"]).to_csv(appeals_file, index=False)
    return pd.read_csv(appeals_file)

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

# --- Authenticator Setup ---
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][row['username']] = {'name': f"{row['name']} ({row['role']})", 'password': str(row['password'])}

authenticator = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30)

# --- App Interface ---
st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    # جلب حالة المستخدم الحالية
    user_status = users_df[users_df['username'] == username].iloc[0]

    # --- 🛡️ Forced Password Change Logic ---
    if user_status['first_login']:
        st.warning("⚠️ SECURITY ALERT: You must change your password to access the system.")
        with st.form("pwd_change_form"):
            new_p = st.text_input("Enter New Password", type="password")
            confirm_p = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("Update Password & Login"):
                if new_p == confirm_p and len(new_p) >= 3:
                    users_df.loc[users_df['username'] == username, ['password', 'first_login']] = [new_p, False]
                    users_df.to_csv(users_file, index=False)
                    st.success("Password Updated! Please refresh the page."); st.rerun()
                else: st.error("Passwords mismatch or too short!")
        st.stop() # يمنع ظهور باقي الصفحة حتى يغير الباسورد

    st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {name}</div>', unsafe_allow_html=True)
    authenticator.logout('Logout', 'sidebar')
    
    # --- Statistics (For Jassim & Hatim) ---
    if username in ['jsafaa', 'ahatim']:
        pending_obs = df_appeals[(df_appeals['Quality Decision'] == 'Pending') | (df_appeals['Direct Manager'] == 'Pending')]
        if not pending_obs.empty:
            st.markdown(f'<div class="notification-banner">🔔 ALERT: Pending objections from: {", ".join(pending_obs["Employee"].unique())}</div>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="stat-card" style="background-color: #e3f2fd; border-left: 6px solid #1565c0;"><div class="stat-label">Total</div><div class="stat-value">{len(df_appeals)}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="background-color: #fff3e0; border-left: 6px solid #ef6c00;"><div class="stat-label">Pending</div><div class="stat-value">{len(pending_obs)}</div></div>', unsafe_allow_html=True)
        with c3:
            acc_count = len(df_appeals[(df_appeals['Quality Decision'] == 'Accepted') & (df_appeals['Direct Manager'] == 'Accepted')])
            st.markdown(f'<div class="stat-card" style="background-color: #e8f5e9; border-left: 6px solid #2e7d32;"><div class="stat-label">Fully Accepted</div><div class="stat-value">{acc_count}</div></div>', unsafe_allow_html=True)
        st.divider()

    # --- Tabs ---
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
                    row_idx = st.number_input("Select Row ID", 0, len(df_appeals)-1, 0)
                    col1, col2 = st.columns(2)
                    with col1: q_dec = st.text_area("Quality Decision", value=df_appeals.loc[row_idx, "Quality Decision"], disabled=(username == 'ahatim'))
                    with col2: m_dec = st.text_area("Head Of Section Decision", value=df_appeals.loc[row_idx, "Direct Manager"], disabled=(username == 'jsafaa'))
                    if st.button("Save Changes"):
                        df_appeals.loc[row_idx, ["Quality Decision", "Direct Manager"]] = [q_dec, m_dec]
                        df_appeals.to_csv(appeals_file, index=False)
                        st.success("Changes Saved!"); st.rerun()
        else:
            t_sub, t_hist = st.tabs(["📤 Submit Objection", "📜 History"])
            with t_sub:
                with st.form("obj_form", clear_on_submit=True):
                    f_date = st.date_input("Incident Date", datetime.now())
                    f_ticket = st.text_input("Ticket Number")
                    # --- KPI الحقل الجديد ---
                    f_kpi = st.selectbox("KPI Type", ["Done Delay", "Done Delay Response", "High MTTD", "Shift Delay", "Delay High Impact", "Closing Issue", "Reduce Number Of Incident", "FMS", "Delay FMS", "Number Of Delay FMS", "No Task"])
                    f_tab = st.selectbox("Department", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Alwatani-Services", "BRIDGES", "Wireless", "IRQNBN", "ITPC", "MERTO", "NAS's", "Server Room", "Power", "AL-Watani Power"])
                    f_details = st.text_area("Objection Details")
                    
                    if st.form_submit_button("Submit"):
                        baghdad_now = datetime.utcnow() + timedelta(hours=3)
                        if baghdad_now.day >= 18 and f_date.day <= 15:
                            st.error("❌ Access Denied: Deadline passed.")
                        elif not f_ticket or not f_details: st.error("❌ Fill all fields!")
                        else:
                            submission_time = baghdad_now.strftime("%Y-%m-%d %H:%M:%S")
                            # أضفت الـ name الحقيقي للموظف لضمان ظهوره في الهستوري
                            new_row = {"Employee": name.split(' (')[0], "Date": str(f_date), "Ticket Number": f_ticket, "KPI": f_kpi, "Tab": f_tab, "Details": f_details, "Quality Decision": "Pending", "Direct Manager": "Pending", "Objection Issue Date": submission_time}
                            df_appeals = pd.concat([df_appeals, pd.DataFrame([new_row])], ignore_index=True)
                            df_appeals.to_csv(appeals_file, index=False)
                            st.success(f"Submitted at {submission_time}!"); st.balloons(); st.rerun()
            with t_hist:
                # فلترة دقيقة باستخدام الاسم المسجل
                user_only = df_appeals[df_appeals['Employee'] == name.split(' (')[0]]
                st.dataframe(user_only, use_container_width=True)

    if username == 'jsafaa':
        with admin_users_tab:
            st.subheader("👥 Employee Directory Management")
            with st.expander("➕ Add New Employee"):
                new_u = st.text_input("New Username").lower().strip()
                new_n = st.text_input("Full Name (Display)")
                if st.button("Register User"):
                    if new_u and new_u not in users_df['username'].values:
                        new_user_row = {"username": new_u, "password": "123", "name": new_n, "role": "Employee", "first_login": True}
                        users_df = pd.concat([users_df, pd.DataFrame([new_user_row])], ignore_index=True)
                        users_df.to_csv(users_file, index=False)
                        st.success("User registered! They must change password on login."); st.rerun()

            with st.expander("🔑 Reset Password (Force Change)"):
                target_user = st.selectbox("Select User Account", users_df['username'].values)
                if st.button("Reset to 123 & Force Change"):
                    # عند تصفير الباسورد، نرجع first_login إلى True ليجبره النظام على التغيير
                    users_df.loc[users_df['username'] == target_user, ['password', 'first_login']] = ["123", True]
                    users_df.to_csv(users_file, index=False)
                    st.success(f"Updated {target_user}! Password is '123' and they must change it.")

            with st.expander("🗑️ Delete Account"):
                del_user = st.selectbox("User to Remove", [u for u in users_df['username'].values if u not in ['jsafaa', 'ahatim']])
                if st.button("Final Delete"):
                    users_df = users_df[users_df['username'] != del_user]
                    users_df.to_csv(users_file, index=False)
                    st.warning(f"Deleted {del_user}!"); st.rerun()

elif authentication_status == False: st.error("Incorrect Username or Password")
else: st.info("Authentication Required.")
