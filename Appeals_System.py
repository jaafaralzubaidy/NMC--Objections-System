import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 🚀 تحسين استجابة الصفحة وتثبيت التنسيق ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- CSS لمعالجة مشكلة اللون الأبيض وضمان وضوح الكتابة ---
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
    </style>
""", unsafe_allow_html=True)

# --- File Names ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

# --- 🛠️ دوال قراءة البيانات الذكية ---
def get_all_data():
    if 'main_df' not in st.session_state:
        if not os.path.exists(appeals_file):
            pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date", "KPI"]).to_csv(appeals_file, index=False)
        st.session_state.main_df = pd.read_csv(appeals_file)
    return st.session_state.main_df

def get_users_df():
    if 'u_df' not in st.session_state:
        if not os.path.exists(users_file):
            initial_users = ["ahatim", "mkhalid", "hfalah", "hmuayyad", "alimad", "rriyad", "hjabbar", "hmuhammada", "arubayi", "aadil", "ayasin", "fahmad", "hakali", "musadiq", "itsattar", "amusadaq", "aanbari", "afahad", "rthair", "omsubhi", "rwahab", "mlayth", "yasadi", "yriyad", "abfaysal", "hasanhadi", "hamuhsin", "aybasheer", "marmahmud", "abisameer", "jsafaa", "muhahamid", "murqasim", "moayad", "dadnan", "abiabbas", "qriyad", "tmustafa", "sbahnan", "admuhammad", "amohammad", "shzuhayr", "farook"]
            user_data = []
            for u in initial_users:
                p = 'admin123' if u == 'jsafaa' else ('manager123' if u in ['ahatim', 'farook'] else '123')
                if u == 'farook':
                    role = 'Team Leader'
                elif u == 'ahatim':
                    role = 'Head Of Section'
                elif u == 'jsafaa':
                    role = 'Quality Engineer'
                else:
                    role = 'Employee'
                user_data.append({"username": u, "password": p, "name": u.upper(), "role": role, "Force_Change": True})
            pd.DataFrame(user_data).to_csv(users_file, index=False)
        
        df = pd.read_csv(users_file)
        
        if 'farook' in df['username'].values:
            df.loc[df['username'] == 'farook', 'role'] = 'Team Leader'
        
        if "Force_Change" not in df.columns:
            df["Force_Change"] = df["password"].astype(str).isin(['123', 'admin123', 'manager123'])
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
    user_row = users_df[users_df['username'] == username].iloc[0]
    # ميزة جبر الموظف على التغيير (موجودة هنا)
    needs_change = str(user_row.get('Force_Change', 'False')).lower() == 'true'
    
    if needs_change:
        st.warning("⚠️ Security Alert: You must update your password to proceed.")
        with st.form("force_pass_change"):
            new_pw = st.text_input("Enter New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("Update Password"):
                if not new_pw:
                    st.error("❌ Password cannot be empty.")
                elif new_pw == str(user_row['password']):
                    st.error("❌ Use a password different from the current one.")
                elif new_pw != confirm_pw:
                    st.error("❌ Passwords do not match.")
                else:
                    users_df.loc[users_df['username'] == username, 'password'] = new_pw
                    users_df.loc[users_df['username'] == username, 'Force_Change'] = False
                    users_df.to_csv(users_file, index=False)
                    st.session_state.pop('u_df')
                    st.success("✅ Password updated! Please wait for reload.")
                    st.rerun()
        authenticator.logout('Logout', 'sidebar')
        st.stop()

    if username in credentials['usernames']:
        display_name = credentials['usernames'][username]['name']
        st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {display_name}</div>', unsafe_allow_html=True)
    
    authenticator.logout('Logout', 'sidebar')
    
    if username in ['jsafaa', 'farook']:
        main_tab, admin_users_tab = st.tabs(["📊 Main System", "👥 Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        if username in ['jsafaa', 'ahatim', 'farook']:
            st.subheader("🛠 MANAGEMENT CONTROL PANEL")
            st.dataframe(df_appeals, use_container_width=True)
            with st.expander("Update Decisions"):
                if not df_appeals.empty:
                    row_idx = st.number_input("Select Row ID", 0, len(df_appeals)-1, 0)
                    col1, col2 = st.columns(2)
                    with col1:
                        q_dec = st.text_area("Quality Decision", value=df_appeals.loc[row_idx, "Quality Decision"], disabled=(username in ['ahatim', 'farook']))
                    with col2:
                        m_dec = st.text_area("Head Of Section Decision", value=df_appeals.loc[row_idx, "Direct Manager"], disabled=(username == 'jsafaa'))
                    if st.button("Save Changes"):
                        df_appeals.loc[row_idx, "Quality Decision"] = q_dec
                        df_appeals.loc[row_idx, "Direct Manager"] = m_dec
                        df_appeals.to_csv(appeals_file, index=False)
                        st.session_state.pop('main_df')
                        st.success("Updated!")
                        st.rerun()
        else:
            t_sub, t_hist = st.tabs(["📤 Submit Objection", "📜 History"])
            with t_sub:
                with st.form("obj_form", clear_on_submit=True):
                    f_date = st.date_input("Date", datetime.now())
                    f_ticket = st.text_input("Ticket Number")
                    f_tab = st.selectbox("Tab", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Alwatani-Services", "BRIDGES", "Wireless", "IRQNBN", "ITPC", "MERTO", "NAS's", "Server Room", "Power", "AL-Watani Power"])
                    f_kpi = st.selectbox("KPI", ["High MTTD", "Shift Delay", "Done Delay", "Done Delay Response", "Delay High Impact", "Closing Issue", "Reduce Number Of Incident", "Ticket Not Add", "Wrong Action", "Delay In Q Limit", "High ASR Utilization", "Zabbix Not Match", "Wrong Forward", "Wrong Action In Q Manager", "FMS", "Delay FMS", "Number Of Delay FMS", "No Task"])
                    f_details = st.text_area("Details")
                    if st.form_submit_button("Submit"):
                        baghdad_now = datetime.utcnow() + timedelta(hours=3)
                        if baghdad_now.day >= 18 and f_date.day <= 15:
                            st.error("❌ Error: Exceeded objection period for 1st half.")
                        elif not f_ticket or not f_details:
                            st.error("❌ Please fill all fields!")
                        else:
                            submission_time = baghdad_now.strftime("%Y-%m-%d %H:%M:%S")
                            new_row = {
                                "Employee": st.session_state.get("name"), 
                                "Date": str(f_date), 
                                "Ticket Number": f_ticket, 
                                "Tab": f_tab, 
                                "KPI": f_kpi, 
                                "Details": f_details, 
                                "Quality Decision": "Pending", 
                                "Direct Manager": "Pending", 
                                "Objection Issue Date": submission_time
                            }
                            updated_df = pd.concat([df_appeals, pd.DataFrame([new_row])], ignore_index=True)
                            updated_df.to_csv(appeals_file, index=False)
                            st.session_state.main_df = updated_df
                            st.success(f"Submitted successfully at {submission_time}!")
                            st.balloons()
            with t_hist: 
                st.dataframe(df_appeals[df_appeals['Employee'] == st.session_state.get("name")], use_container_width=True)

    if username in ['jsafaa', 'farook']:
        with admin_users_tab:
            st.subheader("👥 Staff Directory & Password Control")
            
            # 1. إضافة موظف
            with st.expander("➕ Add New Employee"):
                new_u = st.text_input("New Username").lower().strip()
                new_n = st.text_input("Full Name (Display)")
                if st.button("Add to System"):
                    if new_u and new_u not in users_df['username'].values:
                        new_user_row = {"username": new_u, "password": "123", "name": new_n, "role": "Employee", "Force_Change": True}
                        users_df = pd.concat([users_df, pd.DataFrame([new_user_row])], ignore_index=True)
                        users_df.to_csv(users_file, index=False)
                        st.session_state.pop('u_df')
                        st.success(f"User {new_u} added with default password '123'")
                        st.rerun()

            # 2. ميزة الريسيت باسوورد (تمت الإضافة هنا)
            with st.expander("🔄 Reset Employee Password"):
                st.info("Resets password to '123' and forces the user to change it on next login.")
                reset_user = st.selectbox("Select User to Reset", users_df['username'].values)
                if st.button("Confirm Password Reset"):
                    users_df.loc[users_df['username'] == reset_user, 'password'] = "123"
                    users_df.loc[users_df['username'] == reset_user, 'Force_Change'] = True
                    users_df.to_csv(users_file, index=False)
                    st.session_state.pop('u_df')
                    st.success(f"✅ Password for '{reset_user}' has been reset to '123'")

            # 3. مسح موظف
            with st.expander("🗑️ Remove Employee
