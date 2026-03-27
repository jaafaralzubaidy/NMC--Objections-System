import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 🚀 Page Configuration ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- Custom CSS (تنسيق التنبيهات والإحصائيات) ---
st.markdown("""
    <style>
        .main-title { font-size:38px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        .notification-banner {
            padding: 20px;
            background-color: #ffeeb2;
            border-left: 8px solid #ffcc00;
            border-radius: 5px;
            color: #856404;
            font-weight: bold;
            margin-bottom: 25px;
            font-size: 19px;
        }
        .stat-box {
            background-color: #f1f3f6;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #d1d5db;
            color: #1E3A8A;
        }
    </style>
""", unsafe_allow_html=True)

# --- File Management ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

def get_all_data():
    if 'main_df' not in st.session_state:
        # فحص إذا الملف موجود أو فارغ تماماً
        if not os.path.exists(appeals_file) or os.stat(appeals_file).st_size == 0:
            pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date"]).to_csv(appeals_file, index=False)
        
        try:
            st.session_state.main_df = pd.read_csv(appeals_file)
        except Exception: # في حال فشل القراءة لأي سبب
            st.session_state.main_df = pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date"])
            
    return st.session_state.main_df

def get_users_df():
    if 'u_df' not in st.session_state:
        if not os.path.exists(users_file) or os.stat(users_file).st_size == 0:
            initial_users = ["ahatim", "jsafaa", "mkhalid", "hfalah", "hmuayyad", "alimad", "rriyad", "hjabbar", "hmuhammada", "arubayi", "aadil", "ayasin", "fahmad", "hakali", "musadiq", "itsattar", "amusadaq", "aanbari", "afahad", "rthair", "omsubhi", "rwahab", "mlayth", "yasadi", "yriyad", "abfaysal", "hasanhadi", "hamuhsin", "aybasheer", "marmahmud", "abisameer", "muhahamid", "murqasim", "moayad", "dadnan", "abiabbas", "qriyad", "tmustafa", "sbahnan", "admuhammad", "amohammad", "shzuhayr"]
            user_data = []
            for u in initial_users:
                p = 'admin123' if u == 'jsafaa' else ('manager123' if u == 'ahatim' else '123')
                role = 'Head Of Section' if u == 'ahatim' else ('Quality Engineer' if u == 'jsafaa' else 'Employee')
                user_data.append({"username": u.lower(), "password": p, "name": u.upper(), "role": role})
            pd.DataFrame(user_data).to_csv(users_file, index=False)
        st.session_state.u_df = pd.read_csv(users_file)
    return st.session_state.u_df

# Load Data
df_appeals = get_all_data()
users_df = get_users_df()

# --- Authenticator ---
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][row['username']] = {'name': f"{row['name']} ({row['role']})", 'password': str(row['password'])}

if 'auth_obj' not in st.session_state:
    st.session_state.auth_obj = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30)

authenticator = st.session_state.auth_obj

# --- App UI ---
st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

try:
    authenticator.login()
except:
    st.info("Please login")

if st.session_state.get("authentication_status"):
    username = st.session_state.get("username").lower()
    st.sidebar.markdown(f"👤 Welcome: **{username}**")
    authenticator.logout('Logout', 'sidebar')

    # --- 🔔 Notification & Stats (For Jassim & Hatim Only) ---
    if username in ['jsafaa', 'ahatim']:
        pending_obs = df_appeals[(df_appeals['Quality Decision'] == 'Pending') | (df_appeals['Direct Manager'] == 'Pending')]
        if not pending_obs.empty:
            names = ", ".join(pending_obs['Employee'].unique())
            st.markdown(f'<div class="notification-banner">🔔 ALERT: Pending objections waiting for review from: {names}</div>', unsafe_allow_html=True)

        st.subheader("📊 Performance Statistics")
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="stat-box"><b>Total Objections</b><br><h2>{len(df_appeals)}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-box"><b>Pending Reviews</b><br><h2>{len(pending_obs)}</h2></div>', unsafe_allow_html=True)
        with c3: 
            accepted = len(df_appeals[df_appeals['Quality Decision'].str.lower() == 'accepted'])
            st.markdown(f'<div class="stat-box"><b>Accepted</b><br><h2>{accepted}</h2></div>', unsafe_allow_html=True)
        st.divider()

    # --- System View ---
    if username == 'jsafaa':
        tab_sys, tab_users = st.tabs(["📊 Objections Management", "👥 Staff Management"])
    else:
        tab_sys = st.container()

    with tab_sys:
        if username in ['jsafaa', 'ahatim']:
            st.dataframe(df_appeals, use_container_width=True)
            with st.expander("Update Decisions"):
                if not df_appeals.empty:
                    row_idx = st.number_input("Select Row ID", 0, len(df_appeals)-1, 0)
                    q_dec = st.selectbox("Quality Decision", ["Pending", "Accepted", "Rejected"], index=["Pending", "Accepted", "Rejected"].index(df_appeals.loc[row_idx, "Quality Decision"]), disabled=(username == 'ahatim'))
                    m_dec = st.selectbox("Head Of Section Decision", ["Pending", "Accepted", "Rejected"], index=["Pending", "Accepted", "Rejected"].index(df_appeals.loc[row_idx, "Direct Manager"]), disabled=(username == 'jsafaa'))
                    if st.button("Save Changes"):
                        df_appeals.at[row_idx, "Quality Decision"] = q_dec
                        df_appeals.at[row_idx, "Direct Manager"] = m_dec
                        df_appeals.to_csv(appeals_file, index=False)
                        st.session_state.main_df = df_appeals
                        st.success("Decision updated successfully!")
                        st.rerun()
        else:
            # Employee View
            t_sub, t_hist = st.tabs(["📤 Submit Objection", "📜 History"])
            with t_sub:
                with st.form("obj_form", clear_on_submit=True):
                    f_date = st.date_input("Incident Date", datetime.now())
                    f_ticket = st.text_input("Ticket Number")
                    f_tab = st.selectbox("Tab", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Wireless", "Power"])
                    f_details = st.text_area("Objection Details")
                    if st.form_submit_button("Submit"):
                        baghdad_now = datetime.utcnow() + timedelta(hours=3)
                        new_row = {"Employee": username, "Date": str(f_date), "Ticket Number": f_ticket, "Tab": f_tab, "Details": f_details, "Quality Decision": "Pending", "Direct Manager": "Pending", "Objection Issue Date": baghdad_now.strftime("%Y-%m-%d %H:%M:%S")}
                        updated_df = pd.concat([df_appeals, pd.DataFrame([new_row])], ignore_index=True)
                        updated_df.to_csv(appeals_file, index=False)
                        st.session_state.main_df = updated_df
                        st.success("Submitted!"); st.balloons()
            with t_hist:
                st.dataframe(df_appeals[df_appeals['Employee'] == username], use_container_width=True)

    # Management Tab (Jasim Only)
    if username == 'jsafaa':
        with tab_users:
            st.subheader("👥 Employee Management")
            # (نفس كود إضافة اليوزرات المعتاد)
            with st.expander("➕ Add New Employee"):
                new_u = st.text_input("Username").lower().strip()
                new_n = st.text_input("Full Name")
                if st.button("Register"):
                    if new_u and new_u not in users_df['username'].values:
                        new_user = pd.DataFrame([{"username": new_u, "password": "123", "name": new_n, "role": "Employee"}])
                        users_df = pd.concat([users_df, new_user], ignore_index=True)
                        users_df.to_csv(users_file, index=False)
                        st.success(f"Registered {new_u}!"); st.rerun()

elif st.session_state.get("authentication_status") == False:
    st.error("Wrong Username or Password")
