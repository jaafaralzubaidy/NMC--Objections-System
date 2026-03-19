import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. Page Configuration ---
st.set_page_config(page_title="NMC Portal", layout="wide")

# Baghdad Time Function
def get_baghdad_time():
    return (datetime.utcnow() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')

# Professional Dark UI
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
        <p style='color:#888;'>Stable English Mode - Optimized for Quality Engineering</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. Data Persistence ---
u_file, a_file = "users_list.csv", "database_appeals.csv"

if not os.path.exists(u_file):
    pd.DataFrame([{"username":"jsafaa","password":"123","name":"J. SAFAA"}]).to_csv(u_file, index=False)

# Exact Columns as Requested
cols = ["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager Decision", "Objection Creation Date"]

if not os.path.exists(a_file):
    pd.DataFrame(columns=cols).to_csv(a_file, index=False)

u_df = pd.read_csv(u_file)
a_df = pd.read_csv(a_file)

# Ensure no crashes if file is empty
if "Objection Creation Date" not in a_df.columns:
    a_df["Objection Creation Date"] = "N/A"

# --- 3. Login System ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("🔑 Login to Portal")
    u_in = st.text_input("Username").lower().strip()
    p_in = st.text_input("Password", type="password")
    if st.button("Sign In"):
        user_auth = u_df[(u_df['username'] == u_in) & (u_df['password'].astype(str) == p_in)]
        if not user_auth.empty:
            st.session_state.logged_in = True
            st.session_state.username = u_in
            st.session_state.name = user_auth.iloc[0]['name']
            st.rerun()
        else:
            st.error("Invalid credentials.")
else:
    # --- 4. Main Application Interface ---
    st.sidebar.title(f"👤 {st.session_state.name}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # Tabs for Admin
    if st.session_state.username == 'jsafaa':
        tab1, tab2 = st.tabs(["📊 Operations", "👥 Staff Management"])
    else:
        tab1 = st.container()

    with tab1:
        st.subheader("📋 Objections Records")
        st.dataframe(a_df, use_container_width=True)
        
        # Admin/Manager Decision Panel
        if st.session_state.username in ['jsafaa', 'ahatim']:
            if not a_df.empty:
                with st.expander("Update Decisions"):
                    row_idx = st.number_input("Row Index", 0, len(a_df)-1, 0)
                    c1, c2 = st.columns(2)
                    with c1:
                        q_val = st.text_area("Quality Decision", a_df.loc[row_idx, "Quality Decision"], 
                                            disabled=(st.session_state.username == 'ahatim'))
                    with c2:
                        m_val = st.text_area("Direct Manager Decision", a_df.loc[row_idx, "Direct Manager Decision"], 
                                            disabled=(st.session_state.username == 'jsafaa'))
                    
                    if st.button("Update Now"):
                        a_df.loc[row_idx, "Quality Decision"] = q_val
                        a_df.loc[row_idx, "Direct Manager Decision"] = m_val
                        a_df.to_csv(a_file, index=False)
                        st.success("Updated successfully!")
                        st.rerun()
            else:
                st.info("No records available to update.")
        
        # User Submission Form
        else:
            with st.form("objection_form", clear_on_submit=True):
                st.subheader("📤 Submit New Objection")
                f_date = st.date_input("Date")
                f_ticket = st.text_input("Ticket Number")
                f_tab = st.selectbox("Tab", ["SWITCH STATE", "MPLS", "Wireless", "Power", "AL-Watani"])
                f_details = st.text_area("Details")
                
                if st.form_submit_button("Submit"):
                    if f_ticket and f_details:
                        new_entry = {
                            "Employee": st.session_state.name, "Date": str(f_date), 
                            "Ticket Number": f_ticket, "Tab": f_tab, "Details": f_details,
                            "Quality Decision": "Pending", "Direct Manager Decision": "Pending",
                            "Objection Creation Date": get_baghdad_time()
                        }
                        a_df = pd.concat([a_df, pd.DataFrame([new_entry])], ignore_index=True)
                        a_df.to_csv(a_file, index=False)
                        st.success("Submitted successfully!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Please fill all fields.")

    # Staff Management (Admin Only)
    if st.session_state.username == 'jsafaa':
        with tab2:
            st.subheader("👤 User Management")
            ca, cb, cc = st.columns(3)
            with ca:
                with st.expander("Add User"):
                    new_u = st.text_input("Username").lower().strip()
                    new_n = st.text_input("Full Name")
                    if st.button("Add"):
                        if new_u and new_u not in u_df['username'].values:
                            u_df = pd.concat([u_df, pd.DataFrame([{"username":new_u,"password":"123","name":new_n}])], ignore_index=True)
                            u_df.to_csv(u_file, index=False); st.success("Added"); st.rerun()
            with cb:
                with st.expander("Reset Password"):
                    tgt = st.selectbox("User", u_df['username'].values)
                    pwd = st.text_input("New Password", type="password")
                    if st.button("Reset"):
                        u_df.loc[u_df['username'] == tgt, 'password'] = pwd
                        u_df.to_csv(u_file, index=False); st.success("Reset Done")
            with cc:
                with st.expander("Delete User"):
                    del_u = st.selectbox("Select User", [u for u in u_df['username'].values if u != 'jsafaa'])
                    if st.button("Delete"):
                        u_df = u_df[u_df['username'] != del_u]
                        u_df.to_csv(u_file, index=False); st.warning("Deleted"); st.rerun()
