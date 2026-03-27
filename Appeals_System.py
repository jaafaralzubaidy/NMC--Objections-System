import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 🚀 Page Configuration ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- Custom CSS (التنبيهات والإحصائيات) ---
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
        if not os.path.exists(appeals_file) or os.stat(appeals_file).st_size == 0:
            pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date"]).to_csv(appeals_file, index=False)
        st.session_state.main_df = pd.read_csv(appeals_file)
    return st.session_state.main_df

def get_users_df():
    if 'u_df' not in st.session_state:
        if not os.path.exists(users_file) or os.stat(users_file).st_size == 0:
            # القائمة الأساسية
            initial_users = ["ahatim", "jsafaa"]
            user_data = []
            for u in initial_users:
                p = 'admin123' if u == 'jsafaa' else 'manager123'
                role = 'Head Of Section' if u == 'ahatim' else 'Quality Engineer'
                user_data.append({"username": u, "password": p, "name": u.upper(), "role": role})
            pd.DataFrame(user_data).to_csv(users_file, index=False)
        st.session_state.u_df = pd.read_csv(users_file)
    return st.session_state.u_df

df_appeals = get_all_data()
users_df = get_users_df()

# --- Authenticator ---
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][row['username']] = {'name': f"{row['name']} ({row['role']})", 'password': str(row['password'])}

if 'auth_obj' not in st.session_state:
    st.session_state.auth_obj = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30)

authenticator = st.session_state.auth_obj

st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

try:
    authenticator.login()
except:
    st.info("Please login")

if st.session_state.get("authentication_status"):
    username = st.session_state.get("username").lower()
    st.sidebar.markdown(f"👤 Welcome: **{username}**")
    authenticator.logout('Logout', 'sidebar')

    # --- 🔔 Notifications & Stats (Jassim & Hatim) ---
    if username in ['jsafaa', 'ahatim']:
        pending_obs = df_appeals[(df_appeals['Quality Decision'] == 'Pending') | (df_appeals['Direct Manager'] == 'Pending')]
        if not pending_obs.empty:
            names = ", ".join(pending_obs['Employee'].unique())
            st.markdown(f'<div class="notification-banner">🔔 ALERT: Pending objections from: {names}</div>', unsafe_allow_html=True)

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
            # (نفس كود تحديث القرارات المعتاد)
        else:
            # (نفس كود تقديم الاعتراض للموظفين)
            pass

    # --- 👥 Staff Management (إرجاع التحكم الكامل) ---
    if username == 'jsafaa':
        with tab_users:
            st.subheader("👥 User Management Control")
            st.dataframe(users_df, use_container_width=True)
            
            col_add, col_edit, col_del = st.columns(3)
            
            with col_add:
                with st.expander("➕ Add New"):
                    u_new = st.text_input("Username").lower().strip()
                    n_new = st.text_input("Name")
                    p_new = st.text_input("Password", "123")
                    if st.button("Register User"):
                        if u_new and u_new not in users_df['username'].values:
                            new_row = pd.DataFrame([{"username": u_new, "password": p_new, "name": n_new, "role": "Employee"}])
                            users_df = pd.concat([users_df, new_row], ignore_index=True)
                            users_df.to_csv(users_file, index=False)
                            st.success(f"Added {u_new}!"); st.rerun()

            with col_edit:
                with st.expander("🔑 Reset Password"):
                    u_edit = st.selectbox("Select User", users_df['username'].values)
                    new_pass = st.text_input("New Password")
                    if st.button("Update Password"):
                        users_df.loc[users_df['username'] == u_edit, 'password'] = new_pass
                        users_df.to_csv(users_file, index=False)
                        st.success("Password updated!"); st.rerun()

            with col_del:
                with st.expander("🗑️ Delete User"):
                    u_del = st.selectbox("Delete User", users_df['username'].values, key="del_box")
                    if st.button("Confirm Delete"):
                        users_df = users_df[users_df['username'] != u_del]
                        users_df.to_csv(users_file, index=False)
                        st.success(f"Deleted {u_del}!"); st.rerun()

elif st.session_state.get("authentication_status") == False:
    st.error("Login Failed")
