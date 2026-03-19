import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. إعدادات سريعة جداً ---
st.set_page_config(page_title="NMC Portal", layout="wide")

# دالة الوقت (تعمل فقط عند الحفظ)
def get_now():
    return (datetime.utcnow() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')

# تصميم بسيط جداً (بدون صور أو تعقيد)
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    <h2 style='text-align: center; color: #1f77b4;'>🚀 NMC OBJECTIONS SYSTEM - Fast Mode</h2>
    <hr>
""", unsafe_allow_html=True)

# --- 2. إدارة البيانات (Simple CSV) ---
u_file, a_file = "users_list.csv", "database_appeals.csv"

if not os.path.exists(u_file):
    pd.DataFrame([{"username":"jsafaa","password":"123","name":"J. SAFAA","role":"Quality"}]).to_csv(u_file, index=False)
if not os.path.exists(a_file):
    pd.DataFrame(columns=["Employee","Date","Ticket Number","Tab","Details","Quality Decision","Direct Manager","Objection Creation Date"]).to_csv(a_file, index=False)

u_df = pd.read_csv(u_file)
a_df = pd.read_csv(a_file)

# --- 3. نظام دخول مبسط جداً (أسرع من المكتبات الخارجية) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.form("login_form"):
        st.subheader("Login")
        user_input = st.text_input("Username").lower().strip()
        pass_input = st.text_input("Password", type="password")
        if st.form_submit_button("Sign In"):
            user_row = u_df[(u_df['username'] == user_input) & (u_df['password'].astype(str) == pass_input)]
            if not user_row.empty:
                st.session_state.logged_in = True
                st.session_state.username = user_input
                st.session_state.name = user_row.iloc[0]['name']
                st.session_state.role = user_row.iloc[0]['role']
                st.rerun()
            else:
                st.error("Wrong username or password")
else:
    # --- 4. واجهة البرنامج بعد الدخول ---
    st.sidebar.write(f"Welcome, **{st.session_state.name}**")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # تبويبات بسيطة
    if st.session_state.username == 'jsafaa':
        tab1, tab2 = st.tabs(["📊 View Objections", "👥 Add Users"])
    else:
        tab1 = st.container()

    with tab1:
        if st.session_state.username in ['jsafaa', 'ahatim']:
            st.dataframe(a_df, use_container_width=True)
            with st.expander("Update Decisions"):
                if not a_df.empty:
                    idx = st.number_input("Row Index", 0, len(a_df)-1, 0)
                    q_val = st.text_input("Quality", a_df.loc[idx, "Quality Decision"])
                    m_val = st.text_input("Manager", a_df.loc[idx, "Direct Manager"])
                    if st.button("Update Now"):
                        a_df.loc[idx, "Quality Decision"] = q_val
                        a_df.loc[idx, "Direct Manager"] = m_val
                        a_df.to_csv(a_file, index=False)
                        st.success("Updated!")
                        st.rerun()
        else:
            with st.form("objection_form"):
                st.subheader("New Objection")
                d1 = st.date_input("Incident Date")
                d2 = st.text_input("Ticket Number")
                d3 = st.selectbox("Tab", ["SWITCH STATE", "MPLS", "Wireless", "Power", "Other"])
                d4 = st.text_area("Details")
                if st.form_submit_button("Submit"):
                    new_data = {
                        "Employee": st.session_state.name, "Date": str(d1),
                        "Ticket Number": d2, "Tab": d3, "Details": d4,
                        "Quality Decision": "Pending", "Direct Manager": "Pending",
                        "Objection Creation Date": get_now()
                    }
                    a_df = pd.concat([a_df, pd.DataFrame([new_data])], ignore_index=True)
                    a_df.to_csv(a_file, index=False)
                    st.success("Submitted!")
                    st.rerun()
            
            st.subheader("My Records")
            st.table(a_df[a_df['Employee'] == st.session_state.name])

    if st.session_state.username == 'jsafaa':
        with tab2:
            with st.form("add_user"):
                new_u = st.text_input("New Username")
                new_n = st.text_input("Full Name")
                if st.form_submit_button("Add User"):
                    new_row = {"username": new_u.lower().strip(), "password": "123", "name": new_n, "role": "Employee"}
                    u_df = pd.concat([u_df, pd.DataFrame([new_row])], ignore_index=True)
                    u_df.to_csv(u_file, index=False)
                    st.success("User Added!")