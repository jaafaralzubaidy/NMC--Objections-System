import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime

# --- Page Configuration & Styling ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size:40px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
    .sub-title { font-size:20px !important; color: #4B5563; text-align: center; margin-bottom: 20px; }
    .stButton>button { background-color: #1E3A8A; color: white; border-radius: 8px; width: 100%; }
    </style>
    <div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div>
    <p class="sub-title">Network Monitoring Center - Quality & Operations Management</p>
    <hr style="border: 1px solid #1E3A8A;">
""", unsafe_allow_html=True)

# --- User Credentials ---
users_list = [
    "ahatim", "mkhalid", "hfalah", "hmuayyad", "alimad", "rriyad", "hjabbar", 
    "hmuhammada", "arubayi", "aadil", "ayasin", "fahmad", "hakali", "musadiq", 
    "itsattar", "amusadaq", "aanbari", "afahad", "rthair", "omsubhi", "rwahab", 
    "mlayth", "yasadi", "yriyad", "abfaysal", "hasanhadi", "hamuhsin", "aybasheer", 
    "marmahmud", "abisameer", "jsafaa", "muhahamid", "murqasim", "moayad", 
    "dadnan", "abiabbas", "qriyad", "tmustafa", "sbahnan", "admuhammad", 
    "amohammad", "shzuhayr"
]

credentials = {'usernames': {}}
for user in users_list:
    pwd = '123'
    name = user.upper()
    if user == 'jsafaa':
        pwd = 'admin123'
        name = "J. SAFAA (Quality Engineer)"
    elif user == 'ahatim':
        pwd = 'manager123'
        name = "A. HATIM (Head Of Section)"
    credentials['usernames'][user] = {'name': name, 'password': pwd}

authenticator = stauth.Authenticate(
    credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30
)

# --- Login Logic ---
try:
    authenticator.login()
except:
    try:
        authenticator.login('main')
    except:
        authenticator.login('Login', 'main')

if st.session_state.get("authentication_status") == False:
    st.error('Username/password is incorrect')
elif st.session_state.get("authentication_status") == None:
    st.info('Please log in with your NMC credentials')
elif st.session_state.get("authentication_status"):
    
    name = st.session_state.get("name")
    username = st.session_state.get("username")
    authenticator.logout('Logout', 'sidebar')
    st.sidebar.success(f"Welcome: {name}")

    # --- Database ---
    file_name = "database_appeals.csv"
    if not os.path.exists(file_name):
        pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager"]).to_csv(file_name, index=False)
    
    df = pd.read_csv(file_name)

    # --- Tabs List ---
    tab_options = ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Alwatani-Services", "BRIDGES", "Wireless", "IRQNBN", "ITPC", "MERTO", "NAS's", "Server Room", "Power", "AL-Watani Power"]

    # --- ADMIN & MANAGER INTERFACE ---
    if username in ['jsafaa', 'ahatim']:
        st.subheader("🛠 MANAGEMENT CONTROL PANEL")
        st.dataframe(df, use_container_width=True)
        with st.expander("Update Decisions"):
            if not df.empty:
                row_idx = st.number_input("Select Row ID", 0, len(df)-1, 0)
                col1, col2 = st.columns(2)
                with col1:
                    is_quality_disabled = (username == 'ahatim')
                    q_dec = st.text_area("Quality Decision", value=df.loc[row_idx, "Quality Decision"], disabled=is_quality_disabled)
                with col2:
                    is_manager_disabled = (username == 'jsafaa')
                    m_dec = st.text_area("Head Of Section Decision", value=df.loc[row_idx, "Direct Manager"], disabled=is_manager_disabled)
                if st.button("Save Changes"):
                    df.loc[row_idx, "Quality Decision"] = q_dec
                    df.loc[row_idx, "Direct Manager"] = m_dec
                    df.to_csv(file_name, index=False)
                    st.success("Updated Successfully!")
                    st.rerun()

    # --- EMPLOYEE INTERFACE ---
    else:
        t_sub, t_hist = st.tabs(["📤 Submit New Objection", "📜 My History"])
        with t_sub:
            with st.form("objection_form"):
                col1, col2 = st.columns(2)
                with col1:
                    f_date = st.date_input("Date of Issue", datetime.now())
                    f_ticket = st.text_input("Ticket Number")
                with col2:
                    f_tab = st.selectbox("Select Tab", tab_options)
                f_details = st.text_area("Problem Details")
                
                if st.form_submit_button("Submit Objection"):
                    today = datetime.now()
                    # --- منطق التحقق من الوقت (Time Locking Logic) ---
                    # إذا كان اليوم الحالي هو 18 أو أكثر، وكان التاريخ المختار قبل يوم 16
                    if today.day >= 18 and f_date.day <= 15 and f_date.month == today.month:
                        st.error("❌ Error: You have exceeded the objection period for the first half of the month.")
                    elif not f_ticket or not f_details:
                        st.error("❌ Error: Please fill all fields!")
                    else:
                        new_entry = {
                            "Employee": name, "Date": str(f_date), "Ticket Number": f_ticket, 
                            "Tab": f_tab, "Details": f_details, 
                            "Quality Decision": "Pending Review", "Direct Manager": "Pending Review"
                        }
                        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
                        df.to_csv(file_name, index=False)
                        st.success("Submitted Successfully!")
                        st.balloons()
        with t_hist:
            st.dataframe(df[df['Employee'] == name], use_container_width=True)