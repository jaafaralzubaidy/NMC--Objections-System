import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 🚀 Page Configuration ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- Custom CSS for English Layout & Notifications ---
st.markdown("""
    <style>
        .main-title { font-size:40px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        div[data-testid="stExpander"] { 
            background-color: rgba(240, 242, 246, 0.5); 
            border-radius: 10px; 
            border: 1px solid #d1d5db;
        }
        .stMarkdown h3 { color: #1E3A8A !important; }
        .user-name-sidebar { color: #4CAF50; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
        /* Notification Banner Design */
        .notification-banner {
            padding: 15px;
            background-color: #ffeeb2;
            border-left: 6px solid #ffcc00;
            border-radius: 5px;
            color: #856404;
            font-weight: bold;
            margin-bottom: 20px;
            font-size: 18px;
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
            pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date"]).to_csv(appeals_file, index=False)
        st.session_state.main_df = pd.read_csv(appeals_file)
    return st.session_state.main_df

def get_users_df():
    if 'u_df' not in st.session_state:
        if not os.path.exists(users_file):
            initial_users = ["ahatim", "mkhalid", "hfalah", "hmuayyad", "alimad", "rriyad", "hjabbar", "hmuhammada", "arubayi", "aadil", "ayasin", "fahmad", "hakali", "musadiq", "itsattar", "amusadaq", "aanbari", "afahad", "rthair", "omsubhi", "rwahab", "mlayth", "yasadi", "yriyad", "abfaysal", "hasanhadi", "hamuhsin", "aybasheer", "marmahmud", "abisameer", "jsafaa", "muhahamid", "murqasim", "moayad", "dadnan", "abiabbas", "qriyad", "tmustafa", "sbahnan", "admuhammad", "amohammad", "shzuhayr"]
            user_data = []
            for u in initial_users:
                p = 'admin123' if u == 'jsafaa' else ('manager123' if u == 'ahatim' else '123')
                role = 'Head Of Section' if u == 'ahatim' else ('Quality Engineer' if u == 'jsafaa' else 'Employee')
                user_data.append({"username": u, "password": p, "name": u.upper(), "role": role})
            pd.DataFrame(user_data).to_csv(users_file, index=False)
        st.session_state.u_df = pd.read_csv(users_file)
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

# --- App Interface (English) ---
st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

try:
    authenticator.login()
except:
    try: authenticator.login('main')
    except: authenticator.login('Login', 'main')

if st.session_state.get("authentication_status"):
    username = st.session_state.get("username")
    
    # Sidebar Profile Display
    if username in credentials['usernames']:
        display_name = credentials['usernames'][username]['name']
        st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {display_name}</div>', unsafe_allow_html=True)
    
    authenticator.logout('Logout', 'sidebar')
    
    # Ensure all columns exist
    if "Objection Issue Date" not in df_appeals.columns:
        df_appeals["Objection Issue Date"] = ""
        df_appeals.to_csv(appeals_file, index=False)

    # --- 🔔 Management Notification System ---
    if username in ['jsafaa', 'ahatim']:
        # Filter for entries that are "Pending" from either side
        pending_obs = df_appeals[(df_appeals['Quality Decision'] == 'Pending') | (df_appeals['Direct Manager'] == 'Pending')]
        
        if not pending_obs.empty:
            unique_employees = pending_obs['Employee'].unique()
            names_str = ", ".join(unique_employees)
            st.markdown(f"""
                <div class="notification-banner">
                    🔔 ALERT: Pending objections waiting for review from: {names_str}
                </div>
            """, unsafe_allow_html=True)

    # Tab System
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
                    with col1:
                        q_dec = st.text_area("Quality Decision", value=df_appeals.loc[row_idx, "Quality Decision"], disabled=(username == 'ahatim'))
                    with col2:
                        m_dec = st.text_area("Head Of Section Decision", value=df_appeals.loc[row_idx, "Direct Manager"], disabled=(username == 'jsafaa'))
                    
                    if st.button("Save Changes"):
                        df_appeals.loc[row_idx, "Quality Decision"] = q_dec
                        df_appeals.loc[row_idx, "Direct Manager"] = m_dec
                        df_appeals.to_csv(appeals_file, index=False)
                        st.session_state.pop('main_df')
                        st.success("Changes Saved Successfully!")
                        st.rerun()
        else:
            t_sub, t_hist = st.tabs(["📤 Submit Objection", "📜 History"])
            with t_sub:
                with st.form("obj_form", clear_on_submit=True):
                    f_date = st.date_input("Incident Date", datetime.now())
                    f_ticket = st.text_input("Ticket Number")
                    f_tab = st.selectbox("Department/Tab", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Alwatani-Services", "BRIDGES", "Wireless", "IRQNBN", "ITPC", "MERTO", "NAS's", "Server Room", "Power", "AL-Watani Power"])
                    f_details = st.text_area("Objection Details")
                    
                    if st.form_submit_button("Submit"):
                        baghdad_now = datetime.utcnow() + timedelta(hours=3)
                        # Your custom date restriction rule
                        if baghdad_now.day >= 18 and f_date.day <= 15:
                            st.error("❌ Access Denied: Deadline for 1st half of the month has passed.")
                        elif not f_ticket or not f_details: 
                            st.error("❌ Please fill in all required fields!")
                        else:
                            submission_time = baghdad_now.strftime("%Y-%m-%d %H:%M:%S")
                            new_row = {
                                "Employee": st.session_state.get("name"), 
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
                            st.success(f"Submitted Successfully at {submission_time}!"); st.balloons()
            
            with t_hist: 
                user_history = df_appeals[df_appeals['Employee'] == st.session_state.get("name")]
                st.dataframe(user_history, use_container_width=True)

    # Management Tab (Jasim Only)
    if username == 'jsafaa':
        with admin_users_tab:
            st.subheader("👥 Employee Directory Management")
            
            with st.expander("➕ Add New Employee"):
                new_u = st.text_input("New Username").lower().strip()
                new_n = st.text_input("Full Name (Display)")
                if st.button("Register User"):
                    if new_u and new_u not in users_df['username'].values:
                        new_user_row = {"username": new_u, "password": "123", "name": new_n, "role": "Employee"}
                        users_df = pd.concat([users_df, pd.DataFrame([new_user_row])], ignore_index=True)
                        users_df.to_csv(users_file, index=False)
                        st.session_state.pop('u_df')
                        st.success(f"User '{new_u}' registered successfully!")
                        st.rerun()

            with st.expander("🔑 Reset Password"):
                target_user = st.selectbox("Select User Account", users_df['username'].values)
                new_pass = st.text_input("New Password", type="password")
                if st.button("Confirm Reset"):
                    users_df.loc[users_df['username'] == target_user, 'password'] = new_pass
                    users_df.to_csv(users_file, index=False)
                    st.session_state.pop('u_df')
                    st.success(f"Password updated for {target_user}!")

            with st.expander("🗑️ Delete Account"):
                del_user = st.selectbox("User to Remove", [u for u in users_df['username'].values if u not in ['jsafaa', 'ahatim']])
                if st.button("Final Delete"):
                    users_df = users_df[users_df['username'] != del_user]
                    users_df.to_csv(users_file, index=False)
                    st.session_state.pop('u_df')
                    st.warning(f"User {del_user} has been deleted.")
                    st.rerun()

elif st.session_state.get("authentication_status") == False: 
    st.error("Incorrect Username or Password")
else: 
    st.info("Authentication Required: Please login to proceed.")
