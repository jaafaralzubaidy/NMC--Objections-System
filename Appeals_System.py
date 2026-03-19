import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة والوقت ---
st.set_page_config(page_title="NMC Portal", layout="wide")

def get_baghdad_time():
    # توقيت بغداد UTC+3
    return (datetime.utcnow() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')

# تصميم واجهة احترافية ثابتة (Dark Theme)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .header-box {
        background-color: #1a1c24; padding: 25px; border-radius: 15px;
        text-align: center; border-bottom: 5px solid #007bff; margin-bottom: 30px;
    }
    </style>
    <div class="header-box">
        <h1 style='margin:0; color:white;'>🚀 NMC OBJECTIONS SYSTEM</h1>
        <p style='color:#007bff; font-weight:bold; font-size:18px;'>Stable & High-Performance Version</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. إدارة ملفات البيانات ---
u_file, a_file = "users_list.csv", "database_appeals.csv"

# إنشاء الملفات إذا كانت مفقودة لضمان عدم حدوث Error
if not os.path.exists(u_file):
    pd.DataFrame([{"username":"jsafaa","password":"123","name":"J. SAFAA","role":"Admin"}]).to_csv(u_file, index=False)

if not os.path.exists(a_file):
    cols = ["Employee","Date","Ticket Number","Tab","Details","Quality Decision","Direct Manager","Objection Creation Date"]
    pd.DataFrame(columns=cols).to_csv(a_file, index=False)

u_df = pd.read_csv(u_file)
a_df = pd.read_csv(a_file)

# ضمان وجود عمود "تاريخ إنشاء الاعتراض" في الـ DataFrame
if "Objection Creation Date" not in a_df.columns:
    a_df["Objection Creation Date"] = "N/A"

# --- 3. نظام البقاء مسجلاً (Session State) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.container():
        st.subheader("🔑 Sign In to Portal")
        u_in = st.text_input("Username").lower().strip()
        p_in = st.text_input("Password", type="password")
        if st.button("Login"):
            user_row = u_df[(u_df['username'] == u_in) & (u_df['password'].astype(str) == p_in)]
            if not user_row.empty:
                st.session_state.logged_in = True
                st.session_state.username = u_in
                st.session_state.name = user_row.iloc[0]['name']
                st.rerun()
            else:
                st.error("❌ Invalid Username or Password")
else:
    # القائمة الجانبية للتسجيل الخروج
    st.sidebar.markdown(f"### 👤 {st.session_state.name}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # التبويبات حسب الصلاحية (حصراً لـ jsafaa)
    if st.session_state.username == 'jsafaa':
        tab1, tab2 = st.tabs(["📊 Operations Portal", "👥 Admin: Manage Staff"])
    else:
        tab1 = st.container()

    # --- 4. واجهة العمليات ---
    with tab1:
        if st.session_state.username in ['jsafaa', 'ahatim']:
            st.subheader("🛠 Control Panel")
            # عرض الجدول مع عمود Objection Creation Date
            st.dataframe(a_df, use_container_width=True)
            
            with st.expander("Update Decisions"):
                if not a_df.empty:
                    idx = st.number_input("Select Row Index", 0, len(a_df)-1, 0)
                    c1, c2 = st.columns(2)
                    with c1: q_v = st.text_area("Quality Decision", a_df.loc[idx, "Quality Decision"], disabled=(st.session_state.username == 'ahatim'))
                    with c2: m_v = st.text_area("Manager Decision", a_df.loc[idx, "Direct Manager"], disabled=(st.session_state.username == 'jsafaa'))
                    if st.button("Save Changes"):
                        a_df.loc[idx, "Quality Decision"], a_df.loc[idx, "Direct Manager"] = q_v, m_v
                        a_df.to_csv(a_file, index=False)
                        st.success("Updated Successfully!")
                        st.rerun()
        else:
            with st.form("ob_form", clear_on_submit=True):
                st.subheader("📤 Submit New Objection")
                f1 = st.date_input("Incident Date")
                f2 = st.text_input("Ticket Number")
                f3 = st.selectbox("Category", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Wireless", "Power"])
                f4 = st.text_area("Details")
                if st.form_submit_button("Submit"):
                    if not f2 or not f4:
                        st.error("❌ Please fill all fields.")
                    else:
                        new_r = {
                            "Employee": st.session_state.name, "Date": str(f1), "Ticket Number": f2, 
                            "Tab": f3, "Details": f4, "Quality Decision": "Pending", 
                            "Direct Manager": "Pending", 
                            "Objection Creation Date": get_baghdad_time() # هنا يتم التسجيل أوتوماتيكياً
                        }
                        a_df = pd.concat([a_df, pd.DataFrame([new_r])], ignore_index=True)
                        a_df.to_csv(a_file, index=False)
                        st.success("Objection Sent!")
                        st.balloons()
            
            st.divider()
            st.subheader("📜 Your Submission History")
            st.table(a_df[a_df['Employee'] == st.session_state.name])

    # --- 5. واجهة الآدمن (إضافة، تغيير باسورد، مسح) ---
    if st.session_state.username == 'jsafaa':
        with tab2:
            st.subheader("👥 User Management Control")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                with st.expander("➕ Add User"):
                    new_u = st.text_input("Username").lower().strip()
                    new_n = st.text_input("Full Name")
                    if st.button("Add Now"):
                        if new_u and new_u not in u_df['username'].values:
                            u_df = pd.concat([u_df, pd.DataFrame([{"username":new_u,"password":"123","name":new_n,"role":"User"}])], ignore_index=True)
                            u_df.to_csv(u_file, index=False); st.success(f"Added {new_n}!"); st.rerun()

            with col2:
                with st.expander("🔑 Change Password"):
                    target = st.selectbox("Select User", u_df['username'].values)
                    pass_val = st.text_input("New Password", type="password")
                    if st.button("Update Pass"):
                        u_df.loc[u_df['username'] == target, 'password'] = pass_val
                        u_df.to_csv(u_file, index=False); st.success("Updated!")

            with col3:
                with st.expander("🗑️ Delete User"):
                    del_u = st.selectbox("User to Delete", [u for u in u_df['username'].values if u != 'jsafaa'])
                    if st.button("Confirm Delete"):
                        u_df = u_df[u_df['username'] != del_u]
                        u_df.to_csv(u_file, index=False); st.warning("Deleted."); st.rerun()