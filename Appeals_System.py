import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- إعدادات الصفحة ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

st.markdown("""
    <style>
        .main-title { font-size:40px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        div[data-testid="stExpander"] { background-color: rgba(240, 242, 246, 0.5); border-radius: 10px; border: 1px solid #d1d5db; }
        .user-name-sidebar { color: #4CAF50; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

def get_all_data():
    if 'main_df' not in st.session_state:
        if not os.path.exists(appeals_file):
            pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date", "KPI"]).to_csv(appeals_file, index=False)
        st.session_state.main_df = pd.read_csv(appeals_file)
    return st.session_state.main_df

def get_users_df():
    if 'u_df' not in st.session_state:
        if not os.path.exists(users_file):
            initial_users = ["ahatim", "jsafaa", "farook"] # قائمة مختصرة للتوضيح، النظام سيضيف البقية تلقائياً
            user_data = []
            for u in initial_users:
                p = 'admin123' if u == 'jsafaa' else 'manager123'
                role = 'Team Leader' if u == 'farook' else ('Head Of Section' if u == 'ahatim' else 'Quality Engineer')
                user_data.append({"username": u, "password": p, "name": u.upper(), "role": role, "Force_Change": True})
            pd.DataFrame(user_data).to_csv(users_file, index=False)
        
        df = pd.read_csv(users_file)
        # التأكد من دور فاروق وتحديثه
        if 'farook' in df['username'].values:
            df.loc[df['username'] == 'farook', 'role'] = 'Team Leader'
            df.to_csv(users_file, index=False)
        st.session_state.u_df = df
    return st.session_state.u_df

users_df = get_users_df()
df_appeals = get_all_data()

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
    st.info("Please login to continue")

if st.session_state.get("authentication_status"):
    username = st.session_state.get("username")
    display_name = credentials['usernames'][username]['name']
    st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {display_name}</div>', unsafe_allow_html=True)
    authenticator.logout('Logout', 'sidebar')
    
    # تحديد الصلاحيات الإدارية (صفاء، حاتم، فاروق)
    is_admin = username in ['jsafaa', 'ahatim', 'farook']

    if username in ['jsafaa', 'farook']:
        main_tab, admin_users_tab = st.tabs(["📊 Main System", "👥 Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        if is_admin:
            st.subheader("🛠 MANAGEMENT CONTROL PANEL")
            st.dataframe(df_appeals, use_container_width=True)
            
            with st.expander("Update Decisions"):
                if not df_appeals.empty:
                    row_idx = st.number_input("Select Row ID", 0, len(df_appeals)-1, 0)
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # صفاء فقط يكتب في Quality Decision
                        q_disabled = (username != 'jsafaa')
                        q_val = st.text_area("Quality Decision", value=str(df_appeals.loc[row_idx, "Quality Decision"]), disabled=q_disabled)
                    
                    with col2:
                        # حاتم وفاروق يكتبون في Head Of Section Decision
                        m_disabled = (username == 'jsafaa')
                        m_val = st.text_area("Head Of Section Decision", value=str(df_appeals.loc[row_idx, "Direct Manager"]), disabled=m_disabled)
                    
                    if st.button("Save Changes"):
                        df_appeals.loc[row_idx, "Quality Decision"] = q_val
                        df_appeals.loc[row_idx, "Direct Manager"] = m_val
                        df_appeals.to_csv(appeals_file, index=False)
                        st.session_state.main_df = df_appeals
                        st.success("Decision Saved Successfully!")
                        st.rerun()
        else:
            # واجهة الموظفين العاديين
            t_sub, t_hist = st.tabs(["📤 Submit Objection", "📜 History"])
            with t_sub:
                with st.form("obj_form"):
                    f_date = st.date_input("Date", datetime.now())
                    f_ticket = st.text_input("Ticket Number")
                    f_details = st.text_area("Details")
                    if st.form_submit_button("Submit"):
                        new_row = {"Employee": username, "Date": str(f_date), "Ticket Number": f_ticket, "Details": f_details, "Quality Decision": "Pending", "Direct Manager": "Pending", "Objection Issue Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                        df_appeals = pd.concat([df_appeals, pd.DataFrame([new_row])], ignore_index=True)
                        df_appeals.to_csv(appeals_file, index=False)
                        st.session_state.main_df = df_appeals
                        st.success("Submitted!")
            with t_hist:
                st.dataframe(df_appeals[df_appeals['Employee'] == username])

    if username in ['jsafaa', 'farook']:
        with admin_users_tab:
            st.write("Staff Management Tools Here")

elif st.session_state.get("authentication_status") == False:
    st.error("Invalid credentials")
