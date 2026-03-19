import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. Page Configuration ---
st.set_page_config(page_title="NMC Portal", layout="wide")

def get_baghdad_time():
    return (datetime.utcnow() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')

# Professional Header
st.markdown("""
    <style>
    .stApp { background-color: #1a1a1a; color: white; }
    .header-box {
        background-color: #262626; padding: 20px; border-radius: 10px;
        text-align: center; border-bottom: 3px solid #007bff; margin-bottom: 20px;
    }
    </style>
    <div class="header-box">
        <h2 style='margin:0; color:white;'>🚀 NMC OBJECTIONS SYSTEM</h2>
        <p style='color:#888;'>Full English Mode - Optimized Stability</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. Data Persistence & Auto-Repair ---
u_file, a_file = "users_list.csv", "database_appeals.csv"
# The exact columns you requested
target_cols = ["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager Decision", "Objection Creation Date"]

# 1. FORCE CLEAN: If the file exists but has Arabic headers, DELETE it.
if os.path.exists(a_file):
    try:
        check_df = pd.read_csv(a_file)
        if "الموظف" in check_df.columns or "التاريخ" in check_df.columns:
            os.remove(a_file) # Removing old Arabic database
    except:
        os.remove(a_file)

if os.path.exists(u_file):
    try:
        check_u = pd.read_csv(u_file)
        if "username" not in check_u.columns:
            os.remove(u_file) # Removing old user list if corrupted
    except:
        os.remove(u_file)

# 2. Re-create Clean English Files
if not os.path.exists(u_file):
    pd.DataFrame([{"username":"jsafaa","password":"123","name":"Jassim Safaa"}]).to_csv(u_file, index=False)

if not os.path.exists(a_file):
    pd.DataFrame(columns=target_cols).to_csv(a_file, index=False)

u_df = pd.read_csv(u_file)
a_df = pd.read_csv(a_file)

# --- 3. Secure Login System ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("🔑 Secure Access")
    u_in = st.text_input("Username").lower().strip()
    p_in = st.text_input("Password", type="password")
    if st.button("Sign In"):
        auth = u_df[(u_df['username'] == u_in) & (u_df['password'].astype(str) == p_in)]
        if not auth.empty:
            st.session_state.logged_in = True
            st.session_state.username = u_in
            st.session_state.name = auth.iloc[0]['name']
            st.rerun()
        else:
            st.error("Access Denied: Incorrect credentials.")
else:
    # --- 4. Main Dashboard ---
    st.sidebar.title(f"👤 Welcome, {st.session_state.name}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    if st.session_state.username == 'jsafaa':
        tab1, tab2 = st.tabs(["📊 Operations Portal", "👥 Staff Management"])
    else:
        tab1 = st.container()

    with tab1:
        st.subheader("📋 Objections Records")
        st.dataframe(a_df, use_container_width=True) # Will show English headers now
        
        # Admin Decision Panel
        if st.session_state.username in ['jsafaa', 'ahatim']:
            if not a_df.empty:
                with st.expander("Update Decisions"):
                    row = st.number_input("Select Row Index", 0, len(a_df)-1, 0)
                    c1, c2 = st.columns(2)
                    with c1:
                        q = st.text_area("Quality Decision", a_df.loc[row, "Quality Decision"], 
                                         disabled=(st.session_state.username == 'ahatim'))
                    with c2:
                        m = st.text_area("Direct Manager Decision", a_df.loc[row, "Direct Manager Decision"], 
                                         disabled=(st.session_state.username == 'jsafaa'))
                    if st.button("Confirm Update"):
                        a_df.loc[row, "Quality Decision"] = q
                        a_df.loc[row, "Direct Manager Decision"] = m
                        a_df.to_csv(a_file, index=False)
                        st.success("Record updated successfully!")
                        st.rerun()
            else:
                st.info("System is currently empty.")
        
        # Submission Form (Visible for regular users)
        if st.session_state.username != 'jsafaa' and st.session_state.username != 'ahatim':
            with st.form("ob_submission", clear_on_submit=True):
                st.subheader("📤 Submit Objection")
                d1, d2 = st.date_input("Incident Date"), st.text_input("Ticket Number")
                d3 = st.selectbox("Tab", ["SWITCH STATE", "MPLS", "Wireless", "Power", "AL-Watani"])
                d4 = st.text_area("Submission Details")
                if st.form_submit_button("Submit"):
                    new_entry = {
                        "Employee": st.session_state.name, "Date": str(d1), "Ticket Number": d2, 
                        "Tab": d3, "Details": d4, "Quality Decision": "Pending", 
                        "Direct Manager Decision": "Pending", "Objection Creation Date": get_baghdad_time()
                    }
                    a_df = pd.concat([a_df, pd.DataFrame([new_entry])], ignore_index=True)
                    a_df.to_csv(a_file, index=False)
                    st.success("Submitted!")
                    st.rerun()

    # Staff Management (Admin Only)
    if st.session_state.username == 'jsafaa':
        with tab2:
            st.subheader("👥 User Controls")
            ca, cb, cc = st.columns(3)
            with ca:
                with st.expander("Add Staff"):
                    un, nm = st.text_input("New Username").lower().strip(), st.text_input("Full Name")
                    if st.button("Register"):
                        u_df = pd.concat([u_df, pd.DataFrame([{"username":un,"password":"123","name":nm}])], ignore_index=True)
                        u_df.to_csv(u_file, index=False); st.success("User Added"); st.rerun()
            with cb:
                with st.expander("Reset Password"):
                    target = st.selectbox("Select User", u_df['username'].values)
                    new_pass = st.text_input("New Password", type="password")
                    if st.button("Update"):
                        u_df.loc[u_df['username'] == target, 'password'] = new_pass
                        u_df.to_csv(u_file, index=False); st.success("Password Updated")
            with cc:
                with st.expander("Remove Staff"):
                    rem_u = st.selectbox("Select to Delete", [u for u in u_df['username'].values if u != 'jsafaa'])
                    if st.button("Delete"):
                        u_df = u_df[u_df['username'] != rem_u]
                        u_df.to_csv(u_file, index=False); st.rerun()
