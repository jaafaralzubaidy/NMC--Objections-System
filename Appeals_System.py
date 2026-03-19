import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="NMC Portal", layout="wide")

def get_baghdad_time():
    return (datetime.utcnow() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')

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
        <p style='color:#888;'>Official English Version - Full Staff Database Loaded</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. PRE-DEFINED STAFF LIST (41 Users) ---
# Setting jsafaa as Admin and ahatim as Head of Section
staff_list = [
    "jsafaa", "ahatim", "mkhalid", "hfalah", "hmuayyad", "alimad", "rriyad", "hjabbar", 
    "hmuhammada", "arubayi", "aadil", "ayasin", "fahmad", "hakali", "musadiq", "itsattar", 
    "amusadaq", "aanbari", "afahad", "rthair", "omsubhi", "rwahab", "mlayth", "yasadi", 
    "yriyad", "abfaysal", "hasanhadi", "hamuhsin", "aybasheer", "marmahmud", "abisameer", 
    "muhahamid", "murqasim", "moayad", "dadnan", "abiabbas", "qriyad", "tmustafa", 
    "sbahnan", "admuhammad", "amohammad", "shzuhayr"
]

u_file, a_file = "users_list.csv", "database_appeals.csv"
target_cols = ["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager Decision", "Objection Creation Date"]

# AUTO-REPAIR: If Arabic headers found or file missing, Rebuild!
if not os.path.exists(u_file) or "username" not in pd.read_csv(u_file).columns:
    users_data = []
    for u in staff_list:
        role = "Admin" if u == "jsafaa" else ("Manager" if u == "ahatim" else "Staff")
        users_data.append({"username": u, "password": "123", "name": u.upper(), "role": role})
    pd.DataFrame(users_data).to_csv(u_file, index=False)

if not os.path.exists(a_file) or "الموظف" in pd.read_csv(a_file).columns:
    pd.DataFrame(columns=target_cols).to_csv(a_file, index=False)

u_df = pd.read_csv(u_file)
a_df = pd.read_csv(a_file)

# --- 3. LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("🔑 Portal Sign-In")
    u_in = st.text_input("Username").lower().strip()
    p_in = st.text_input("Password", type="password")
    if st.button("Login"):
        auth = u_df[(u_df['username'] == u_in) & (u_df['password'].astype(str) == p_in)]
        if not auth.empty:
            st.session_state.logged_in = True
            st.session_state.username = u_in
            st.session_state.name = auth.iloc[0]['name']
            st.session_state.role = auth.iloc[0]['role']
            st.rerun()
        else: st.error("Access Denied.")
else:
    # --- 4. INTERFACE ---
    st.sidebar.title(f"👤 {st.session_state.name}")
    st.sidebar.write(f"Role: {st.session_state.role}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # Permissions Logic
    is_admin = (st.session_state.username == 'jsafaa')
    is_manager = (st.session_state.username == 'ahatim')
    
    if is_admin:
        tab1, tab2 = st.tabs(["📊 Operations Portal", "👥 Admin: Manage Staff"])
    else: tab1 = st.container()

    with tab1:
        st.subheader("📋 Objections Records")
        # Full view for Admin and Section Head (ahatim)
        view_df = a_df if (is_admin or is_manager) else a_df[a_df['Employee'] == st.session_state.name]
        st.dataframe(view_df, use_container_width=True)
        
        # Decision Management (Preventing Error Red Box)
        if (is_admin or is_manager) and not a_df.empty:
            with st.expander("📝 Update Decisions"):
                idx = st.number_input("Select Row Index", 0, len(a_df)-1, 0)
                c1, c2 = st.columns(2)
                with c1:
                    q_v = st.text_area("Quality Decision (jsafaa)", a_df.loc[idx, "Quality Decision"], disabled=not is_admin)
                with c2:
                    m_v = st.text_area("Manager Decision (ahatim)", a_df.loc[idx, "Direct Manager Decision"], disabled=not is_manager)
                if st.button("Save Updates"):
                    a_df.loc[idx, "Quality Decision"], a_df.loc[idx, "Direct Manager Decision"] = q_v, m_v
                    a_df.to_csv(a_file, index=False); st.success("Updated!"); st.rerun()
        
        # New Objection Submission
        if not (is_admin or is_manager):
            with st.form("ob_form", clear_on_submit=True):
                st.subheader("📤 Submit Objection")
                f1, f2 = st.date_input("Incident Date"), st.text_input("Ticket Number")
                f3 = st.selectbox("Tab", ["SWITCH STATE", "MPLS", "Wireless", "Power", "AL-Watani"])
                f4 = st.text_area("Details")
                if st.form_submit_button("Send"):
                    new_r = {
                        "Employee": st.session_state.name, "Date": str(f1), "Ticket Number": f2, "Tab": f3, "Details": f4,
                        "Quality Decision": "Pending", "Direct Manager Decision": "Pending", "Objection Creation Date": get_baghdad_time()
                    }
                    a_df = pd.concat([a_df, pd.DataFrame([new_r])], ignore_index=True)
                    a_df.to_csv(a_file, index=False); st.success("Submitted!"); st.rerun()

    # User Management (Admin only)
    if is_admin:
        with tab2:
            st.subheader("👥 Registered Staff")
            st.dataframe(u_df[['username', 'name', 'role']], use_container_width=True)
            with st.expander("⚠️ Danger Zone: Delete User"):
                rem = st.selectbox("Select User to Remove", [u for u in u_df['username'].values if u != 'jsafaa'])
                if st.button("Delete Permanently"):
                    u_df = u_df[u_df['username'] != rem]
                    u_df.to_csv(u_file, index=False); st.warning(f"User {rem} Deleted."); st.rerun()
