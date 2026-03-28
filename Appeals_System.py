import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 🚀 Page Configuration ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- Custom CSS (Darker text for better visibility) ---
st.markdown("""
    <style>
        .main-title { font-size:40px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        div[data-testid="stExpander"] { 
            background-color: rgba(240, 242, 246, 0.5); 
            border-radius: 10px; border: 1px solid #d1d5db;
        }
        .user-name-sidebar { color: #4CAF50; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
        
        /* Stats Cards Styling - Dark text to avoid visibility issues */
        .stat-card {
            padding: 20px; border-radius: 12px; text-align: center;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 10px;
        }
        .stat-label { font-size: 18px; font-weight: bold; margin-bottom: 5px; color: #1A1A1A !important; }
        .stat-value { font-size: 36px; font-weight: bold; color: #000000 !important; }
        
        .notification-banner {
            padding: 15px; background-color: #ffeeb2; border-left: 6px solid #ffcc00;
            border-radius: 5px; color: #856404; font-weight: bold; margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# --- File Names ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

# --- 🛠️ Data Loading Functions ---
def get_all_data():
    if 'main_df' not in st.session_state:
        if not os.path.exists(appeals_file):
            pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date", "Admin Comment"]).to_csv(appeals_file, index=False)
        df = pd.read_csv(appeals_file)
        if "Admin Comment" not in df.columns: 
            df["Admin Comment"] = ""
            df.to_csv(appeals_file, index=False)
        st.session_state.main_df = df
    return st.session_state.main_df

def get_users_df():
    if 'u_df' not in st.session_state:
        if not os.path.exists(users_file):
            initial_users = ["ahatim", "jsafaa"]
            user_data = []
            for u in initial_users:
                p = 'admin123' if u == 'jsafaa' else 'manager123'
                role = 'Quality Engineer' if u == 'jsafaa' else 'Head Of Section'
                user_data.append({"username": u, "password": p, "name": u.upper(), "role": role, "first_login": True})
            pd.DataFrame(user_data).to_csv(users_file, index=False)
        df = pd.read_csv(users_file)
        if "first_login" not in df.columns: 
            df["first_login"] = True
            df.to_csv(users_file, index=False)
        st.session_state.u_df = df
    return st.session_state.u_df

users_df = get_users_df()
df_appeals = get_all_data()

# --- Authenticator Setup ---
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][row['username']] = {'name': f"{row['name']} ({row['role']})", 'password': str(row['password'])}

if 'auth_obj' not in st.session_state:
    st.session_state.auth_obj = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30)

authenticator = st.session_state.auth_obj

# --- Main App ---
st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

try:
    authenticator.login()
except:
    try: authenticator.login('main')
    except: authenticator.login('Login', 'main')

if st.session_state.get("authentication_status"):
    username = st.session_state.get("username")
    user_row = users_df[users_df['username'] == username].iloc[0]

    # --- Forced Password Change ---
    if user_row['first_login']:
        st.warning("⚠️ SECURITY: Please change your password for the first time.")
        with st.form("first_pwd_change"):
            new_p = st.text_input("New Password", type="password")
            conf_p = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Update Password"):
                if new_p == conf_p and len(new_p) > 2:
                    users_df.loc[users_df['username'] == username, 'password'] = new_p
                    users_df.loc[users_df['username'] == username, 'first_login'] = False
                    users_df.to_csv(users_file, index=False)
                    st.success("Success! Please refresh."); st.rerun()
                else: st.error("Passwords do not match or too short.")
        st.stop()

    # --- Sidebar ---
    display_full_name = st.session_state.get('name', username.upper())
    st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {display_full_name}</div>', unsafe_allow_html=True)
    authenticator.logout('Logout', 'sidebar')

    # --- 📊 Stats Overview (Updated Logic) ---
    if username in ['jsafaa', 'ahatim']:
        # Pending: Either Quality OR Manager is "Pending"
        pending_count = len(df_appeals[(df_appeals['Quality Decision'] == 'Pending') | (df_appeals['Direct Manager'] == 'Pending')])
        # Fully Decided: (Both Approved) OR (Both Rejected)
        fully_decided = len(df_appeals[
            ((df_appeals['Quality Decision'] == 'Approved') & (df_appeals['Direct Manager'] == 'Approved')) |
            ((df_appeals['Quality Decision'] == 'Rejected') & (df_appeals['Direct Manager'] == 'Rejected'))
        ])

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="stat-card" style="background-color: #e3f2fd;"><div class="stat-label">Total Objections</div><div class="stat-value">{len(df_appeals)}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="stat-card" style="background-color: #fff3e0;"><div class="stat-label">Pending Review</div><div class="stat-value">{pending_count}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="stat-card" style="background-color: #e8f5e9;"><div class="stat-label">Fully Decided</div><div class="stat-value">{fully_decided}</div></div>', unsafe_allow_html=True)
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
            
            with st.expander("Update Decisions & Notes"):
                if not df_appeals.empty:
                    row_idx = st.number_input("Select Row ID (Index)", 0, len(df_appeals)-1, 0)
                    col1, col2, col3 = st.columns(3)
                    opts = ["Pending", "Approved", "Rejected"]
                    
                    with col1:
                        curr_q = df_appeals.loc[row_idx, "Quality Decision"]
                        q_idx = opts.index(curr_q) if curr_q in opts else 0
                        new_q = st.selectbox("Quality Decision", opts, index=q_idx, disabled=(username == 'ahatim'))
                    with col2:
                        curr_m = df_appeals.loc[row_idx, "Direct Manager"]
                        m_idx = opts.index(curr_m) if curr_m in opts else 0
                        new_m = st.selectbox("Head Of Section Decision", opts, index=m_idx, disabled=(username == 'jsafaa'))
                    with col3:
                        new_note = st.text_area("Admin Notes/Comment", value=str(df_appeals.loc[row_idx, "Admin Comment"]))
                    
                    if st.button("Save Updates"):
                        df_appeals.loc[row_idx, "Quality Decision"] = new_q
                        df_appeals.loc[row_idx, "Direct Manager"] = new_m
                        df_appeals.loc[row_idx, "Admin Comment"] = new_note
                        df_appeals.to_csv(appeals_file, index=False)
                        st.success("Saved!"); st.rerun()
        else:
            # Employee View
            t_sub, t_hist = st.tabs(["📤 Submit Objection", "📜 History"])
            with t_sub:
                with st.form("obj_form", clear_on_submit=True):
                    f_date = st.date_input("Incident Date", datetime.now())
                    f_ticket = st.text_input("Ticket Number")
                    f_tab = st.selectbox("Department", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Alwatani-Services", "BRIDGES", "Wireless", "IRQNBN", "ITPC", "MERTO", "NAS's", "Server Room", "Power", "AL-Watani Power"])
                    f_details = st.text_area("Objection Details")
                    if st.form_submit_button("Submit"):
                        baghdad_now = datetime.utcnow() + timedelta(hours=3)
                        # Fix: Use session_state directly to avoid KeyErrors
                        new_row = {
                            "Employee": st.session_state.get('name', username.upper()), "Date": str(f_date), 
                            "Ticket Number": f_ticket, "Tab": f_tab, "Details": f_details, 
                            "Quality Decision": "Pending", "Direct Manager": "Pending", 
                            "Objection Issue Date": baghdad_now.strftime("%Y-%m-%d %H:%M:%S"),
                            "Admin Comment": ""
                        }
                        updated_df = pd.concat([df_appeals, pd.DataFrame([new_row])], ignore_index=True)
                        updated_df.to_csv(appeals_file, index=False)
                        st.session_state.main_df = updated_df
                        st.success("Submitted!"); st.balloons()
            with t_hist: 
                user_hist = df_appeals[df_appeals['Employee'].str.contains(st.session_state.get('name', username.upper()), na=False)]
                st.dataframe(user_hist, use_container_width=True)

    # --- 👥 ADMIN: Manage Staff (Restored and Corrected) ---
    if username == 'jsafaa':
        with admin_users_tab:
            st.subheader("👥 Staff Management")
            
            # 1. Add User
            with st.expander("➕ Add New Employee"):
                new_u = st.text_input("Username").lower().strip()
                new_n = st.text_input("Full Display Name")
                if st.button("Add Account"):
                    if new_u and new_u not in users_df['username'].values:
                        new_row = {"username": new_u, "password": "123", "name": new_n.upper(), "role": "Employee", "first_login": True}
                        users_df = pd.concat([users_df, pd.DataFrame([new_row])], ignore_index=True)
                        users_df.to_csv(users_file, index=False)
                        st.success("User Added!"); st.rerun()

            # 2. Reset Password
            with st.expander("🔑 Reset Password"):
                sel_user = st.selectbox("Account to Reset", users_df['username'].values)
                if st.button("Reset to 123"):
                    users_df.loc[users_df['username'] == sel_user, 'password'] = "123"
                    users_df.loc[users_df['username'] == sel_user, 'first_login'] = True
                    users_df.to_csv(users_file, index=False)
                    st.success(f"Password for {sel_user} reset to '123'")

            # 3. Delete Account
            with st.expander("🗑️ Delete Account"):
                rem_user = st.selectbox("Select User to Delete", [u for u in users_df['username'].values if u not in ['jsafaa', 'ahatim']])
                if st.button("Confirm Delete"):
                    users_df = users_df[users_df['username'] != rem_user]
                    users_df.to_csv(users_file, index=False)
                    st.warning("Deleted!"); st.rerun()

elif st.session_state.get("authentication_status") == False: st.error("Wrong Login")
else: st.info("Please Login.")
