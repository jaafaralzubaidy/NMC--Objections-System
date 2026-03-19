import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة والوقت ---
st.set_page_config(page_title="NMC Portal", layout="wide")

def get_baghdad_time():
    # توقيت بغداد UTC+3
    return (datetime.utcnow() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')

# تصميم الواجهة الاحترافية (Dark Theme)
st.markdown("""
    <style>
    .stApp { background-color: #1a1a1a; color: white; }
    .header-box {
        background-color: #262626; padding: 20px; border-radius: 12px;
        text-align: center; border-bottom: 4px solid #007bff; margin-bottom: 25px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #333; border-radius: 5px; padding: 10px 20px; color: white;
    }
    </style>
    <div class="header-box">
        <h1 style='margin:0; color:white;'>🚀 NMC OBJECTIONS SYSTEM</h1>
        <p style='color:#007bff; font-weight:bold;'>Full Features & High Performance</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. إدارة البيانات (CSV) ---
u_file, a_file = "users_list.csv", "database_appeals.csv"

# إنشاء الملفات إذا كانت مفقودة
if not os.path.exists(u_file):
    pd.DataFrame([{"username":"jsafaa","password":"123","name":"J. SAFAA","role":"Admin"}]).to_csv(u_file, index=False)
if not os.path.exists(a_file):
    cols = ["Employee","Date","Ticket Number","Tab","Details","Quality Decision","Direct Manager","Objection Creation Date"]
    pd.DataFrame(columns=cols).to_csv(a_file, index=False)

u_df = pd.read_csv(u_file)
a_df = pd.read_csv(a_file)

# التأكد من وجود عمود تاريخ الإنشاء
if "Objection Creation Date" not in a_df.columns:
    a_df["Objection Creation Date"] = "N/A"

# --- 3. نظام "تذكر تسجيل الدخول" ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.container():
        st.subheader("🔑 Login")
        u_input = st.text_input("Username").lower().strip()
        p_input = st.text_input("Password", type="password")
        if st.button("Sign In"):
            user_match = u_df[(u_df['username'] == u_input) & (u_df['password'].astype(str) == p_input)]
            if not user_match.empty:
                st.session_state.logged_in = True
                st.session_state.username = u_input
                st.session_state.name = user_match.iloc[0]['name']
                st.rerun()
            else:
                st.error("Wrong Username or Password")
else:
    # القائمة الجانبية (Sidebar)
    st.sidebar.title(f"👤 {st.session_state.name}")
    if st.sidebar.button("🔓 Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # التبويبات حسب الصلاحية
    if st.session_state.username == 'jsafaa':
        tab1, tab2 = st.tabs(["📊 Operations Portal", "👥 Admin: Manage Staff"])
    else:
        tab1 = st.container()

    # --- 4. واجهة الاعتراضات ---
    with tab1:
        if st.session_state.username in ['jsafaa', 'ahatim']:
            st.subheader("🛠 Control Panel")
            st.dataframe(a_df, use_container_width=True)
            with st.expander("Update Decisions (Quality/Manager)"):
                if not a_df.empty:
                    idx = st.number_input("Select Row Index", 0, len(a_df)-1, 0)
                    c1, c2 = st.columns(2)
                    with c1: q_val = st.text_area("Quality Decision", a_df.loc[idx, "Quality Decision"], disabled=(st.session_state.username == 'ahatim'))
                    with c2: m_val = st.text_area("Manager Decision", a_df.loc[idx, "Direct Manager"], disabled=(st.session_state.username == 'jsafaa'))
                    if st.button("Save Decisions"):
                        a_df.loc[idx, "Quality Decision"], a_df.loc[idx, "Direct Manager"] = q_val, m_val
                        a_df.to_csv(a_file, index=False); st.success("Updated!"); st.rerun()
        else:
            with st.form("ob_form", clear_on_submit=True):
                st.subheader("📤 New Objection Submission")
                f1 = st.date_input("Incident Date")
                f2 = st.text_input("Ticket Number")
                f3 = st.selectbox("Department", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Wireless", "Power"])
                f4 = st.text_area("Reason / Details")
                if st.form_submit_button("Submit"):
                    if not f2 or not f4:
                        st.error("❌ Fill all fields.")
                    else:
                        new_r = {
                            "Employee": st.session_state.name, "Date": str(f1), "Ticket Number": f2, "Tab": f3, "Details": f4,
                            "Quality Decision": "Pending Review", "Direct Manager": "Pending Review",
                            "Objection Creation Date": get_baghdad_time() # التسجيل الأوتوماتيكي
                        }
                        a_df = pd.concat([a_df, pd.DataFrame([new_r])], ignore_index=True)
                        a_df.to_csv(a_file, index=False); st.success("Submitted!"); st.balloons()
            
            st.divider()
            st.subheader("📜 My Records History")
            st.table(a_df[a_df['Employee'] == st.session_state.name])

    # --- 5. واجهة الآدمن (إضافة، مسح، تغيير باسوورد) ---
    if st.session_state.username == 'jsafaa':
        with tab2:
            st.subheader("👥 User Management Control")
            col_add, col_pass, col_del = st.columns(3)
            
            with col_add:
                with st.expander("➕ Add New User", expanded=True):
                    nu = st.text_input("New User ID").lower().strip()
                    nn = st.text_input("User Display Name")
                    if st.button("Add User"):
                        if nu and nu not in u_df['username'].values:
                            new_u = pd.DataFrame([{"username":nu,"password":"123","name":nn,"role":"Employee"}])
                            u_df = pd.concat([u_df, new_u], ignore_index=True)
                            u_df.to_csv(u_file, index=False); st.success("Added!"); st.rerun()

            with col_pass:
                with st.expander("🔑 Reset/Change Password", expanded=True):
                    target = st.selectbox("Select Staff", u_df['username'].values)
                    new_p = st.text_input("New Password", type="password")
                    if st.button("Update Password"):
                        u_df.loc[u_df['username'] == target, 'password'] = new_p
                        u_df.to_csv(u_file, index=False); st.success("Pass Updated!")

            with col_del:
                with st.expander("🗑️ Delete User Profile", expanded=True):
                    rem = st.selectbox("User to Remove", [u for u in u_df['username'].values if u != 'jsafaa'])
                    if st.button("Confirm Deletion"):
                        u_df = u_df[u_df['username'] != rem]
                        u_df.to_csv(u_file, index=False); st.warning(f"User {rem} Removed."); st.rerun()