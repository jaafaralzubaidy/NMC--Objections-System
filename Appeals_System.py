import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="NMC Portal", layout="wide")

# دالة الوقت (توقيت بغداد UTC+3)
def get_baghdad_time():
    return (datetime.utcnow() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')

# تصميم واجهة خفيفة واحترافية
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
        <p style='color:#888;'>Stable & Fast Mode - Full Features Enabled</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. إدارة البيانات ---
u_file, a_file = "users_list.csv", "database_appeals.csv"

if not os.path.exists(u_file):
    pd.DataFrame([{"username":"jsafaa","password":"123","name":"J. SAFAA","role":"Admin"}]).to_csv(u_file, index=False)
if not os.path.exists(a_file):
    cols = ["Employee","Date","Ticket Number","Tab","Details","Quality Decision","Direct Manager","Objection Creation Date"]
    pd.DataFrame(columns=cols).to_csv(a_file, index=False)

u_df = pd.read_csv(u_file)
a_df = pd.read_csv(a_file)

# ضمان وجود عمود التاريخ
if "Objection Creation Date" not in a_df.columns:
    a_df["Objection Creation Date"] = "N/A"

# --- 3. نظام "تذكر تسجيل الدخول" ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.container():
        st.subheader("🔑 Login to Portal")
        u_input = st.text_input("Username").lower().strip()
        p_input = st.text_input("Password", type="password")
        col_log, _ = st.columns([1, 4])
        if col_log.button("Login"):
            user_row = u_df[(u_df['username'] == u_input) & (u_df['password'].astype(str) == p_input)]
            if not user_row.empty:
                st.session_state.logged_in = True
                st.session_state.username = u_input
                st.session_state.name = user_row.iloc[0]['name']
                st.rerun()
            else:
                st.error("Invalid Username or Password")
else:
    # --- 4. واجهة البرنامج بعد الدخول ---
    st.sidebar.title(f"👤 {st.session_state.name}")
    st.sidebar.info("Status: Online")
    if st.sidebar.button("🔓 Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # التبويبات
    if st.session_state.username == 'jsafaa':
        tab1, tab2 = st.tabs(["📊 Operations Portal", "👥 Admin: Manage Staff"])
    else:
        tab1 = st.container()

    with tab1:
        if st.session_state.username in ['jsafaa', 'ahatim']:
            st.subheader("🛠 Control Panel (Admin View)")
            st.dataframe(a_df, use_container_width=True)
            with st.expander("Update Status & Decisions"):
                if not a_df.empty:
                    idx = st.number_input("Select Row Index", 0, len(a_df)-1, 0)
                    c1, c2 = st.columns(2)
                    with c1: q_v = st.text_area("Quality Decision", a_df.loc[idx, "Quality Decision"], disabled=(st.session_state.username == 'ahatim'))
                    with c2: m_v = st.text_area("Manager Decision", a_df.loc[idx, "Direct Manager"], disabled=(st.session_state.username == 'jsafaa'))
                    if st.button("Confirm Changes"):
                        a_df.loc[idx, "Quality Decision"], a_df.loc[idx, "Direct Manager"] = q_v, m_v
                        a_df.to_csv(a_file, index=False)
                        st.success("Record Updated Successfully!")
                        st.rerun()
        else:
            with st.form("ob_form", clear_on_submit=True):
                st.subheader("📤 New Objection Submission")
                f1 = st.date_input("Incident Date")
                f2 = st.text_input("Ticket Number")
                f3 = st.selectbox("Department/Tab", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Wireless", "Power", "AL-Watani Power"])
                f4 = st.text_area("Details & Reasons")
                if st.form_submit_button("Submit Objection"):
                    if not f2 or not f4:
                        st.error("❌ Please fill all fields.")
                    else:
                        new_r = {
                            "Employee": st.session_state.name, "Date": str(f1), "Ticket Number": f2, "Tab": f3, "Details": f4,
                            "Quality Decision": "Pending", "Direct Manager": "Pending",
                            "Objection Creation Date": get_baghdad_time()
                        }
                        a_df = pd.concat([a_df, pd.DataFrame([new_r])], ignore_index=True)
                        a_df.to_csv(a_file, index=False)
                        st.success("Objection Sent Successfully!")
                        st.balloons()
            
            st.divider()
            st.subheader("📜 My Records")
            st.table(a_df[a_df['Employee'] == st.session_state.name])

    # لوحة تحكم الآدمن (إضافة، مسح، تغيير باسوورد)
    if st.session_state.username == 'jsafaa':
        with tab2:
            st.subheader("👥 User Management System")
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                with st.expander("➕ Add New User", expanded=True):
                    nu = st.text_input("New Username").lower().strip()
                    nn = st.text_input("Full Name")
                    if st.button("Add Now"):
                        if nu and nu not in u_df['username'].values:
                            u_df = pd.concat([u_df, pd.DataFrame([{"username":nu,"password":"123","name":nn,"role":"Employee"}])], ignore_index=True)
                            u_df.to_csv(u_file, index=False); st.success(f"Added: {nn}"); st.rerun()

            with col_b:
                with st.expander("🔑 Reset Password", expanded=True):
                    target = st.selectbox("Select User", u_df['username'].values)
                    new_p = st.text_input("Set New Password", type="password")
                    if st.button("Update Password"):
                        u_df.loc[u_df['username'] == target, 'password'] = new_p
                        u_df.to_csv(u_file, index=False); st.success("Updated!")

            with col_c:
                with st.expander("🗑️ Delete User", expanded=True):
                    rem = st.selectbox("User to Remove", [u for u in u_df['username'].values if u != 'jsafaa'])
                    if st.button("Confirm Delete"):
                        u_df = u_df[u_df['username'] != rem]
                        u_df.to_csv(u_file, index=False); st.warning(f"User {rem} Deleted."); st.rerun()
