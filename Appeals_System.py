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
        div[data-testid="stExpander"] { 
            background-color: rgba(240, 242, 246, 0.5); 
            border-radius: 10px; 
            border: 1px solid #d1d5db;
        }
        .stMarkdown h3 { color: #1E3A8A !important; }
        .user-name-sidebar { color: #4CAF50; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
        .notification-banner {
            padding: 15px; background-color: #ffeeb2; border-left: 6px solid #ffcc00;
            border-radius: 5px; color: #856404; font-weight: bold; margin-bottom: 20px; font-size: 18px;
        }
        .stat-card {
            padding: 20px; border-radius: 12px; text-align: center;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 10px;
        }
        .stat-label { font-size: 16px; font-weight: bold; margin-bottom: 5px; }
        .stat-value { font-size: 32px; font-weight: bold; }
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
            initial_users = ["ahatim", "mkhalid", "hfalah", "hmuayyad", "alimad", "rriyad", "hjabbar", "hmuhammada", "arubayi", "aadil", "ayasin", "fahmad", "hakali", "musadiq", "itsattar", "amusadaq", "aanbari", "afahad", "rthair", "omsubhi", "rwahab", "mlayth", "yasadi", "yriyad", "abfaysal", "hasanhadi", "hamuhsin", "aybasheer", "marmahmud", "abisameer", "jsafaa", "muhahamid", "murqasim", "moayad", "dadnan", "abiabbas", "qriyad", "tmustafa", "sbahnan", "admuhammad", "amohammad", "shzuhayr"]
            user_data = []
            for u in initial_users:
                p = 'admin123' if u == 'jsafaa' else ('manager123' if u == 'ahatim' else '123')
                role = 'Head Of Section' if u == 'ahatim' else ('Quality Engineer' if u == 'jsafaa' else 'Employee')
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

# --- App Interface ---
st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

try:
    authenticator.login()
except:
    try: authenticator.login('main')
    except: authenticator.login('Login', 'main')

if st.session_state.get("authentication_status"):
    username = st.session_state.get("username")
    
    # التحقق من أول تسجيل دخول
    user_row = users_df[users_df['username'] == username].iloc[0]
    if user_row['first_login']:
        st.warning("🔒 Security: Please change your password for the first time.")
        with st.form("pwd_change"):
            new_p = st.text_input("New Password", type="password")
            conf_p = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Update & Login"):
                if new_p == conf_p and len(new_p) > 2:
                    users_df.loc[users_df['username'] == username, 'password'] = new_p
                    users_df.loc[users_df['username'] == username, 'first_login'] = False
                    users_df.to_csv(users_file, index=False)
                    st.success("Updated! Please refresh."); st.rerun()
                else: st.error("Passwords don't match or too short!")
        st.stop()

    if username in credentials['usernames']:
        display_name = credentials['usernames'][username]['name']
        st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {display_name}</div>', unsafe_allow_html=True)
    
    authenticator.logout('Logout', 'sidebar')

    # --- 📊 Statistics ---
    if username in ['jsafaa', 'ahatim']:
        pending_obs = df_appeals[(df_appeals['Quality Decision'] == 'Pending') | (df_appeals['Direct Manager'] == 'Pending')]
        if not pending_obs.empty:
            st.markdown(f'<div class="notification-banner">🔔 ALERT: {len(pending_obs)} Pending Review(s)</div>', unsafe_allow_html=True)

        st.subheader("📈 Statistics Overview")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="stat-card" style="background-color: #e3f2fd;"><div class="stat-label">Total</div><div class="stat-value">{len(df_appeals)}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="stat-card" style="background-color: #fff3e0;"><div class="stat-label">Pending</div><div class="stat-value">{len(pending_obs)}</div></div>', unsafe_allow_html=True)
        with c3:
            acc = len(df_appeals[(df_appeals['Quality Decision'] == 'Accepted') & (df_appeals['Direct Manager'] == 'Accepted')])
            st.markdown(f'<div class="stat-card" style="background-color: #e8f5e9;"><div class="stat-label">Fully Accepted</div><div class="stat-value">{acc}</div></div>', unsafe_allow_html=True)
        with c4:
            rej = len(df_appeals[(df_appeals['Quality Decision'] == 'Rejected') & (df_appeals['Direct Manager'] == 'Rejected')])
            st.markdown(f'<div class="stat-card" style="background-color: #ffebee;"><div class="stat-label">Fully Rejected</div><div class="stat-value">{rej}</div></div>', unsafe_allow_html=True)

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
                    col1, col2, col3 = st.columns(3)
                    opts = ["Pending", "Accepted", "Rejected"]
                    
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
                        st.success("Updated Successfully!"); st.rerun()
        else:
            t_sub, t_hist = st.tabs(["📤 Submit Objection", "📜 History"])
            with t_sub:
                with st.form("obj_form", clear_on_submit=True):
                    f_date = st.date_input("Incident Date", datetime.now())
                    f_ticket = st.text_input("Ticket Number")
                    f_tab = st.selectbox("Department", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Alwatani-Services", "BRIDGES", "Wireless", "IRQNBN", "ITPC", "MERTO", "NAS's", "Server Room", "Power", "AL-Watani Power"])
                    f_details = st.text_area("Objection Details")
                    if st.form_submit_button("Submit"):
                        baghdad_now = datetime.utcnow() + timedelta(hours=3)
                        if baghdad_now.day >= 18 and f_date.day <= 15: st.error("❌ Deadline passed.")
                        elif not f_ticket or not f_details: st.error("❌ Fill all fields!")
                        else:
                            new_row = {"Employee": st.session_state.get("name"), "Date": str(f_date), "Ticket Number": f_ticket, "Tab": f_tab, "Details": f_details, "Quality Decision": "Pending", "Direct Manager": "Pending", "Objection Issue Date": baghdad_now.strftime("%Y-%m-%d %H:%M:%S"), "Admin Comment": ""}
                            updated_df = pd.concat([df_appeals, pd.DataFrame([new_row])], ignore_index=True)
                            updated_df.to_csv(appeals_file, index=False)
                            st.session_state.main_df = updated_df
                            st.success("Submitted!"); st.balloons()
            with t_hist: 
                user_history = df_appeals[df_appeals['Employee'] == st.session_state.get("name")]
                st.dataframe(user_history, use_container_width=True)

    if username == 'jsafaa':
        with admin_users_tab:
            st.subheader("👥 Employee Directory")
            with st.expander("➕ Add New Employee"):
                new_u = st.text_input("New Username").lower().strip()
                new_n = st.text_input("Full Name")
                if st.button("Register"):
                    if new_u and new_u not in users_df['username'].values:
                        new_user = {"username": new_u, "password": "123", "name": new_n, "role": "Employee", "first_login": True}
                        users_df = pd.concat([users_df, pd.DataFrame([new_user])], ignore_index=True)
                        users_df.to_csv(users_file, index=False)
                        st.success("User added!"); st.rerun()

            with st.expander("🗑️ Delete Account"):
                del_user = st.selectbox("User to Remove", [u for u in users_df['username'].values if u not in ['jsafaa', 'ahatim']])
                if st.button("Final Delete"):
                    users_df = users_df[users_df['username'] != del_user]
                    users_df.to_csv(users_file, index=False)
                    st.warning(f"Deleted {del_user}!"); st.rerun()

elif st.session_state.get("authentication_status") == False: st.error("Wrong credentials")
else: st.info("Please Login.")
