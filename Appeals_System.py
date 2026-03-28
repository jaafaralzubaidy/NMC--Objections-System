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
        pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "KPI", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date", "Admin Notes/Comment"]).to_csv(appeals_file, index=False)
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
    credentials['usernames'][str(row['username'])] = {'name': f"{row['name']} ({row['role']})", 'password': str(row['password'])}

authenticator = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30)

# --- App Interface ---
st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

# تصحيح دالة الدخول لتعمل على كل النسخ
try:
    name, authentication_status, username = authenticator.login('main')
except:
    name, authentication_status, username = authenticator.login(location='main')

if authentication_status:
    # جلب حالة المستخدم الحالية بدقة
    user_status = users_df[users_df['username'] == username].iloc[0]

    # --- 🛡️ Forced Password Change Logic ---
    if user_status['first_login']:
        st.warning("⚠️ SECURITY: You must change your password to access the system.")
        with st.form("force_password_change"):
            new_p = st.text_input("New Password", type="password")
            conf_p = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Update Password"):
                if new_p == conf_p and len(new_p) >= 3:
                    users_df.loc[users_df['username'] == username, ['password', 'first_login']] = [new_p, False]
                    users_df.to_csv(users_file, index=False)
                    st.success("Updated! Please refresh the page.")
                    st.rerun()
                else: st.error("Mismatch or too short!")
        st.stop()

    st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {name}</div>', unsafe_allow_html=True)
    authenticator.logout('Logout', 'sidebar')
    
    # --- Statistics (Admin Only) ---
    if username in ['jsafaa', 'ahatim']:
        pending_obs = df_appeals[(df_appeals['Quality Decision'] == 'Pending') | (df_appeals['Direct Manager'] == 'Pending')]
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card" style="background-color: #e3f2fd;"><div class="stat-label">Total</div><div class="stat-value">{len(df_appeals)}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="background-color: #fff3e0;"><div class="stat-label">Pending</div><div class="stat-value">{len(pending_obs)}</div></div>', unsafe_allow_html=True)
        with c3:
            acc = len(df_appeals[(df_appeals['Quality Decision'].str.contains('Accept', na=False)) & (df_appeals['Direct Manager'].str.contains('approve', na=False, case=False))])
            st.markdown(f'<div class="stat-card" style="background-color: #e8f5e9;"><div class="stat-label">Accepted</div><div class="stat-value">{acc}</div></div>', unsafe_allow_html=True)
        with c4:
            rej = len(df_appeals[(df_appeals['Quality Decision'].str.contains('Reject', na=False))])
            st.markdown(f'<div class="stat-card" style="background-color: #ffebee;"><div class="stat-label">Rejected</div><div class="stat-value">{rej}</div></div>', unsafe_allow_html=True)

    # --- Tabs ---
    if username == 'jsafaa':
        main_tab, admin_users_tab = st.tabs(["📊 Main System", "👥 Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        if username in ['jsafaa', 'ahatim']:
            st.subheader("🛠 MANAGEMENT CONTROL PANEL")
            st.dataframe(df_appeals, use_container_width=True)
            with st.expander("Update Decisions & Notes"):
                if not df_appeals.empty:
                    row_idx = st.number_input("Select Row ID", 0, len(df_appeals)-1, 0)
                    col1, col2 = st.columns(2)
                    with col1: q_dec = st.selectbox("Quality Decision", ["Pending", "Accepted", "Rejected"], index=0, disabled=(username == 'ahatim'))
                    with col2: m_dec = st.selectbox("Head Of Section Decision", ["Pending", "approved", "rejected"], index=0, disabled=(username == 'jsafaa'))
                    note = st.text_area("Admin Notes/Comment", value=str(df_appeals.loc[row_idx, "Admin Notes/Comment"]) if "Admin Notes/Comment" in df_appeals.columns else "")
                    if st.button("Save Updates"):
                        df_appeals.loc[row_idx, ["Quality Decision", "Direct Manager", "Admin Notes/Comment"]] = [q_dec, m_dec, note]
                        df_appeals.to_csv(appeals_file, index=False)
                        st.success("Saved!"); st.rerun()
        else:
            t_sub, t_hist = st.tabs(["📤 Submit Objection", "📜 History"])
            with t_sub:
                with st.form("obj_form", clear_on_submit=True):
                    f_date = st.date_input("Incident Date", datetime.now())
                    f_ticket = st.text_input("Ticket Number")
                    f_kpi = st.selectbox("KPI Type", ["Done Delay", "Done Delay Response", "High MTTD", "Shift Delay", "Delay High Impact", "Closing Issue", "Reduce Number Of Incident", "FMS", "Delay FMS", "Number Of Delay FMS", "No Task"])
                    f_tab = st.selectbox("Department", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Alwatani-Services", "BRIDGES", "Wireless", "IRQNBN", "ITPC", "MERTO", "NAS's", "Server Room", "Power", "AL-Watani Power"])
                    f_details = st.text_area("Objection Details")
                    if st.form_submit_button("Submit"):
                        baghdad_now = datetime.utcnow() + timedelta(hours=3)
                        if baghdad_now.day >= 18 and f_date.day <= 15:
                            st.error("❌ Deadline passed.")
                        elif not f_ticket or not f_details: st.error("❌ Fill all fields!")
                        else:
                            submission_time = baghdad_now.strftime("%Y-%m-%d %H:%M:%S")
                            new_row = {"Employee": name.split(' (')[0], "Date": str(f_date), "Ticket Number": f_ticket, "KPI": f_kpi, "Tab": f_tab, "Details": f_details, "Quality Decision": "Pending", "Direct Manager": "Pending", "Objection Issue Date": submission_time, "Admin Notes/Comment": ""}
                            df_appeals = pd.concat([df_appeals, pd.DataFrame([new_row])], ignore_index=True)
                            df_appeals.to_csv(appeals_file, index=False)
                            st.success("Submitted!"); st.rerun()
            with t_hist:
                st.dataframe(df_appeals[df_appeals['Employee'] == name.split(' (')[0]], use_container_width=True)

    if username == 'jsafaa':
        with admin_users_tab:
            st.subheader("👥 Staff Management")
            with st.expander("➕ Add New"):
                nu = st.text_input("New Username").lower().strip()
                nn = st.text_input("Full Name")
                if st.button("Register"):
                    if nu and nu not in users_df['username'].values:
                        new_u = {"username": nu, "password": "123", "name": nn.upper(), "role": "Employee", "first_login": True}
                        users_df = pd.concat([users_df, pd.DataFrame([new_u])], ignore_index=True)
                        users_df.to_csv(users_file, index=False)
                        st.success("Registered!"); st.rerun()

            with st.expander("🔑 Force Reset Password"):
                target = st.selectbox("Select User", users_df['username'].values)
                if st.button("Reset to 123"):
                    users_df.loc[users_df['username'] == target, ['password', 'first_login']] = ["123", True]
                    users_df.to_csv(users_file, index=False)
                    st.success("Password reset to 123. They must change it on login."); st.rerun()

elif authentication_status is False: st.error("Wrong Login")
else: st.info("Please Login")
