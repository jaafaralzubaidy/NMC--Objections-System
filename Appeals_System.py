import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime

# --- Page Configuration & Professional Styling ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# CSS for a professional "Dark Blue/Silver" IT look
st.markdown("""
    <style>
    .main-title { font-size:48px !important; color: #1E3A8A; text-align: center; font-weight: bold; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .sub-title { font-size:22px !important; color: #4B5563; text-align: center; margin-bottom: 20px; font-style: italic; }
    .stButton>button { background-color: #1E3A8A; color: white; border-radius: 8px; width: 100%; }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea { border: 1px solid #1E3A8A; }
    </style>
    <div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div>
    <p class="sub-title">Network Monitoring Center - Quality & Operations Management</p>
    <hr style="border: 1px solid #1E3A8A;">
""", unsafe_allow_html=True)

# --- User Credentials Configuration ---
config = {
    'credentials': {
        'usernames': {
            'admin': {'name': 'Quality Engineer', 'password': 'admin123'},
            'manager': {'name': 'Direct Manager', 'password': 'manager123'},
            'ahmed': {'name': 'Ahmed Ali', 'password': '123'},
            'zaid': {'name': 'Zaid Hassan', 'password': '123'}
        }
    },
    'cookie': {'expiry_days': 30, 'key': 'nmc_auth_key', 'name': 'nmc_cookie'}
}

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
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
    st.sidebar.success(f"Loged in as: {name}")

    # --- Database Initialization ---
    file_name = "database_appeals.csv"
    columns = ["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager"]
    if not os.path.exists(file_name):
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_name, index=False, encoding='utf-8-sig')
    
    df = pd.read_csv(file_name)

    # --- ADMIN & MANAGER INTERFACE ---
    if username in ['admin', 'manager']:
        st.subheader("🛠 MANAGEMENT CONTROL PANEL")
        st.write("Current Pending & Reviewed Objections:")
        st.dataframe(df, use_container_width=True)

        with st.expander("Update Decisions (Reply to Objection)"):
            if not df.empty:
                row_idx = st.number_input("Select Row ID to update", 0, len(df)-1, 0)
                col1, col2 = st.columns(2)
                with col1:
                    q_dec = st.text_area("Quality Decision", value=df.loc[row_idx, "Quality Decision"])
                with col2:
                    m_dec = st.text_area("Direct Manager Decision", value=df.loc[row_idx, "Direct Manager"])
                
                if st.button("Save & Submit Decisions"):
                    df.loc[row_idx, "Quality Decision"] = q_dec
                    df.loc[row_idx, "Direct Manager"] = m_dec
                    df.to_csv(file_name, index=False, encoding='utf-8-sig')
                    st.success("Decisions saved and sent to employee.")
                    st.rerun()
            else:
                st.info("No objections found in database.")

    # --- EMPLOYEE INTERFACE ---
    else:
        tab_submit, tab_history = st.tabs(["📤 Submit New Objection", "📜 My History"])
        
        with tab_submit:
            st.subheader("New Objection Entry Form")
            st.write("Please fill all required fields below:")
            
            with st.form("objection_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    f_date = st.date_input("Date (Mandatory)", datetime.now())
                    f_ticket = st.text_input("Ticket Number (Mandatory)")
                with col_b:
                    f_tab = st.selectbox("Select Tab (Mandatory)", ["Morning", "Evening", "Night", "Fajr"])
                    
                f_details = st.text_area("Problem Details (Mandatory)")
                
                # Hidden/ReadOnly for Employee
                st.info("Quality Decision & Manager Decision will be updated by the administration.")
                
                submit_btn = st.form_submit_button("Submit Objection")
                
                if submit_btn:
                    # Logic Check: All 4 fields must be filled
                    if not f_ticket or not f_details or not f_tab or not f_date:
                        st.error("❌ ERROR: All 4 fields (Ticket Number, Date, Tab, and Details) are required!")
                    else:
                        new_entry = {
                            "Employee": name, 
                            "Date": str(f_date), 
                            "Ticket Number": f_ticket, 
                            "Tab": f_tab, 
                            "Details": f_details, 
                            "Quality Decision": "Pending Review", 
                            "Direct Manager": "Pending Review"
                        }
                        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
                        df.to_csv(file_name, index=False, encoding='utf-8-sig')
                        st.success("✅ Success: Your objection has been recorded.")
                        st.balloons()

        with tab_history:
            st.subheader("Status of Your Previous Objections")
            my_data = df[df['Employee'] == name]
            if my_data.empty:
                st.write("You haven't submitted any objections yet.")
            else:
                st.dataframe(my_data, use_container_width=True)