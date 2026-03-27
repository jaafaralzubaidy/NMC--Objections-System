import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 🚀 Configuration ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- Custom CSS (تنبيهات جاسم الصفراء) ---
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
        }
    </style>
""", unsafe_allow_html=True)

# --- File Management ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

def get_all_data():
    if 'main_df' not in st.session_state:
        if not os.path.exists(appeals_file):
            pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date"]).to_csv(appeals_file, index=False)
        st.session_state.main_df = pd.read_csv(appeals_file)
    return st.session_state.main_df

def get_users_df():
    if 'u_df' not in st.session_state:
        if not os.path.exists(users_file):
            initial_users = ["ahatim", "jsafaa", "mkhalid", "hfalah", "hmuayyad", "alimad", "rriyad", "hjabbar", "hmuhammada", "arubayi", "aadil", "ayasin", "fahmad", "hakali", "musadiq", "itsattar", "amusadaq", "aanbari", "afahad", "rthair", "omsubhi", "rwahab", "mlayth", "yasadi", "yriyad", "abfaysal", "hasanhadi", "hamuhsin", "aybasheer", "marmahmud", "abisameer", "jsafaa", "muhahamid", "murqasim", "moayad", "dadnan", "abiabbas", "qriyad", "tmustafa", "sbahnan", "admuhammad", "amohammad", "shzuhayr"]
            user_data = []
            for u in initial_users:
                p = 'admin123' if u == 'jsafaa' else ('manager123' if u == 'ahatim' else '123')
                role = 'Head Of Section' if u == 'ahatim' else ('Quality Engineer' if u == 'jsafaa' else 'Employee')
                user_data.append({"username": u, "password": p, "name": u.upper(), "role": role})
            pd.DataFrame(user_data).to_csv(users_file, index=False)
        st.session_state.u_df = pd.read_csv(users_file)
    return st.session_state.u_df

df_appeals = get_all_data()
users_df = get_users_df()

# --- Auth ---
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][row['username']] = {'name': f"{row['name']} ({row['role']})", 'password': str(row['password'])}

authenticator = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30)

st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

authenticator.login('main')

if st.session_state["authentication_status"]:
    username = st.session_state["username"]
    st.sidebar.write(f"Welcome **{username}**")
    authenticator.logout('Logout', 'sidebar')

    # --- 🔔 رجوع التنبيهات (Notification System) ---
    if username in ['jsafaa', 'ahatim']:
        pending_obs = df_appeals[(df_appeals['Quality Decision'] == 'Pending') | (df_appeals['Direct Manager'] == 'Pending')]
        if not pending_obs.empty:
            names = ", ".join(pending_obs['Employee'].unique())
            st.markdown(f'<div class="notification-banner">🔔 ALERT: Pending objections waiting for review from: {names}</div>', unsafe_allow_html=True)

        # --- 📊 الستاتستك (لك ولحاتم فقط) ---
        st.subheader("📊 Performance Statistics")
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="stat-box"><b>Total Objections</b><br><h2>{len(df_appeals)}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-box"><b>Pending Reviews</b><br><h2>{len(pending_obs)}</h2></div>', unsafe_allow_html=True)
        with c3: 
            accepted = len(df_appeals[df_appeals['Quality Decision'] == 'Accepted'])
            st.markdown(f'<div class="stat-box"><b>Accepted</b><br><h2>{accepted}</h2></div>', unsafe_allow_html=True)
        st.divider()

    # --- System Tabs ---
    if username == 'jsafaa':
        tab_sys, tab_users = st.tabs(["📊 Objections Management", "👥 Staff Management"])
    else:
        tab_sys = st.container()

    with tab_sys:
        if username in ['jsafaa', 'ahatim']:
            st.dataframe(df_appeals, use_container_width=True)
            with st.expander("Update Decisions"):
                row_idx = st.number_input("Row ID", 0, len(df_appeals)-1, 0)
                q_dec = st.text_input("Quality Decision", df_appeals.loc[row_idx, "Quality Decision"], disabled=(username == 'ahatim'))
                m_dec = st.text_input("Head Of Section Decision", df_appeals.loc[row_idx, "Direct Manager"], disabled=(username == 'jsafaa'))
                if st.button("Save Changes"):
                    df_appeals.at[row_idx, "Quality Decision"] = q_dec
                    df_appeals.at[row_idx, "Direct Manager"] = m_dec
                    df_appeals.to_csv(appeals_file, index=False)
                    st.success("Updated!"); st.rerun()
        else:
            # Employee Form
            with st.form("my_form"):
                f_date = st.date_input("Incident Date")
                f_ticket = st.text_input("Ticket Number")
                f_details = st.text_area("Details")
                if st.form_submit_button("Submit"):
                    # (اضافة السطر الجديد للـ CSV مثل الكود القديم تماماً)
                    st.success("Submitted!")

    # (تكملة كود ادارة الموظفين لجاسم تبقى كما هي)
