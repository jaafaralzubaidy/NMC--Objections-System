import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="NMC Portal", layout="wide")

# دالة لجلب وقت بغداد فقط عند "الضغط على زر" لتسجيل وقت الاعتراض
def get_baghdad_now():
    return (datetime.utcnow() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')

# تصميم واجهة احترافية بسيطة جداً وغير ثقيلة
st.markdown("""
    <style>
    .stApp { background-color: #1E1E1E; }
    .header-box {
        background-color: #2D2D2D;
        padding: 20px; border-radius: 10px; text-align: center;
        color: white; margin-bottom: 20px;
        border-bottom: 4px solid #007BFF;
    }
    </style>
    <div class="header-box">
        <h1 style='margin:0;'>🚀 NMC OBJECTIONS SYSTEM</h1>
        <p style='margin:5px; color:#BBB;'>Performance Optimized Mode</p>
    </div>
""", unsafe_allow_html=True)

# --- 2. إدارة ملفات البيانات ---
u_file, a_file = "users_list.csv", "database_appeals.csv"

if not os.path.exists(u_file):
    pd.DataFrame([{"username":"jsafaa","password":"123","name":"J. SAFAA","role":"Quality Engineer"}]).to_csv(u_file, index=False)

u_df = pd.read_csv(u_file)
creds = {'usernames': {}}
for _, r in u_df.iterrows():
    creds['usernames'][r['username']] = {'name':f"{r['name']} ({r['role']})", 'password':str(r['password'])}

auth = stauth.Authenticate(creds, 'nmc_c', 'nmc_k', 30)

try: auth.login('main')
except: auth.login()

if st.session_state.get("authentication_status"):
    user = st.session_state.get("username")
    auth.logout('Logout', 'sidebar')
    
    if not os.path.exists(a_file):
        pd.DataFrame(columns=["Employee","Date","Ticket Number","Tab","Details","Quality Decision","Direct Manager","Objection Creation Date"]).to_csv(a_file, index=False)
    df = pd.read_csv(a_file)

    # --- 3. الواجهات الرئيسية ---
    if user == 'jsafaa':
        t_main, t_staff = st.tabs(["📊 Operations Portal", "👥 Manage Staff"])
    else:
        t_main = st.container()

    with t_main:
        if user in ['jsafaa', 'ahatim']:
            st.subheader("🛠 Control Panel")
            st.dataframe(df, use_container_width=True)
            with st.expander("Update Decisions"):
                if not df.empty:
                    idx = st.number_input("Select Row Index", 0, len(df)-1, 0)
                    c1, c2 = st.columns(2)
                    with c1: q = st.text_area("Quality Decision", df.loc[idx,"Quality Decision"], disabled=(user=='ahatim'))
                    with c2: m = st.text_area("Manager Decision", df.loc[idx,"Direct Manager"], disabled=(user=='jsafaa'))
                    if st.button("Save Changes"):
                        df.loc[idx,"Quality Decision"], df.loc[idx,"Direct Manager"] = q, m
                        df.to_csv(a_file, index=False); st.success("Saved Successfully!"); st.rerun()
        else:
            with st.form("ob_form"):
                st.subheader("📤 Submit New Objection")
                f_d = st.date_input("Incident Date")
                f_t = st.text_input("Ticket Number")
                f_tb = st.selectbox("Tab", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Alwatani-Services", "BRIDGES", "Wireless", "IRQNBN", "ITPC", "MERTO", "NAS's", "Server Room", "Power", "AL-Watani Power"])
                f_dt = st.text_area("Details")
                if st.form_submit_button("Submit Objection"):
                    if not f_t or not f_dt:
                        st.error("❌ Please fill all fields.")
                    else:
                        # يتم تسجيل التاريخ أوتوماتيكياً هنا فقط عند الضغط
                        new_r = {
                            "Employee": st.session_state.get("name"),
                            "Date": str(f_d),
                            "Ticket Number": f_t,
                            "Tab": f_tb,
                            "Details": f_dt,
                            "Quality Decision": "Pending",
                            "Direct Manager": "Pending",
                            "Objection Creation Date": get_baghdad_now()
                        }
                        df = pd.concat([df, pd.DataFrame([new_r])], ignore_index=True)
                        df.to_csv(a_file, index=False); st.success("Objection Sent!"); st.balloons()
            
            st.divider()
            st.subheader("📜 My Objections History")
            st.table(df[df['Employee'] == st.session_state.get("name")])

    if user == 'jsafaa':
        with t_staff:
            st.subheader("👥 User Management")
            with st.expander("Add New Employee"):
                nu = st.text_input("Username").lower().strip()
                nn = st.text_input("Full Name")
                if st.button("Add Employee"):
                    if nu and nu not in u_df['username'].values:
                        new_u = pd.DataFrame([{"username":nu,"password":"123","name":nn,"role":"Employee"}])
                        u_df = pd.concat([u_df, new_u], ignore_index=True)
                        u_df.to_csv(u_file, index=False); st.success(f"Added {nn} successfully!")

elif st.session_state.get("authentication_status") == False: st.error("Invalid Username or Password")
else: st.info("Welcome. Please log in to access the system.")