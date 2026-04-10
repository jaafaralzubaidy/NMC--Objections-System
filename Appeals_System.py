import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="NMC Objections", layout="wide")

# --- 2. دوال البيانات السريعة (Cached) ---
@st.cache_data(ttl=60) # تحديث الذاكرة كل دقيقة لضمان السرعة
def load_all_data():
    if not os.path.exists("database_appeals.csv"):
        cols = ["Employee", "Date", "Ticket Number", "Tab", "Details", 
                "Quality Decision", "Direct Manager", "Objection Issue Date", "KPI"]
        pd.DataFrame(columns=cols).to_csv("database_appeals.csv", index=False)
    return pd.read_csv("database_appeals.csv")

@st.cache_data
def load_users_fast():
    if not os.path.exists("users_list.csv"):
        u_data = [
            {"username": "jsafaa", "password": "admin123", "name": "SAFAA", "role": "Quality Engineer", "Force_Change": True},
            {"username": "ahatim", "password": "manager123", "name": "HATIM", "role": "Head Of Section", "Force_Change": True},
            {"username": "farook", "password": "manager123", "name": "FAROOK", "role": "Team Leader", "Force_Change": True}
        ]
        pd.DataFrame(u_data).to_csv("users_list.csv", index=False)
    df = pd.read_csv("users_list.csv")
    if 'farook' in df['username'].values:
        df.loc[df['username'] == 'farook', 'role'] = 'Team Leader'
    return df

# استدعاء البيانات
users_df = load_users_fast()
df_appeals = load_all_data()

# --- 3. إعداد الدخول ---
creds = {'usernames': {}}
for _, r in users_df.iterrows():
    creds['usernames'][r['username']] = {
        'name': f"{r['name']} ({r['role']})",
        'password': str(r['password'])
    }

auth = stauth.Authenticate(creds, 'nmc_c', 'nmc_k', cookie_expiry_days=30)

st.markdown('<h1 style="text-align:center;">🛰️ NMC OBJECTIONS SYSTEM</h1>', unsafe_allow_html=True)

try:
    auth.login()
except:
    st.info("Please Login")

if st.session_state.get("authentication_status"):
    user = st.session_state.get("username")
    u_row = users_df[users_df['username'] == user].iloc[0]
    
    # ميزة جبر التغيير
    if str(u_row.get('Force_Change', 'False')).lower() == 'true':
        st.warning("⚠️ Security: Update your password.")
        with st.form("p_form"):
            new_p = st.text_input("New Password", type="password")
            if st.form_submit_button("Update"):
                if new_p and new_p != str(u_row['password']):
                    users_df.loc[users_df['username'] == user, 'password'] = new_p
                    users_df.loc[users_df['username'] == user, 'Force_Change'] = False
                    users_df.to_csv("users_list.csv", index=False)
                    st.cache_data.clear() # مسح الكاش لتحديث البيانات
                    st.success("✅ Done!")
                    st.rerun()
        st.stop()

    st.sidebar.markdown(f"👤 {creds['usernames'][user]['name']}")
    auth.logout('Logout', 'sidebar')

    # الصلاحيات
    is_admin = user in ['jsafaa', 'farook']
    is_mgmt = user in ['jsafaa', 'ahatim', 'farook']

    t_list = ["📊 System", "👥 Manage Staff"] if is_admin else ["📊 System"]
    main_tabs = st.tabs(t_list)

    with main_tabs[0]:
        if is_mgmt:
            st.subheader("🛠 CONTROL PANEL")
            st.dataframe(df_appeals, use_container_width=True)
            with st.expander("Update Decisions"):
                if not df_appeals.empty:
                    idx = st.number_input("Select ID", 0, len(df_appeals)-1, 0)
                    col1, col2 = st.columns(2)
                    with col1:
                        q_dis = (user != 'jsafaa')
                        q_txt = st.text_area("Quality Decision", value=df_appeals.loc[idx, "Quality Decision"], disabled=q_dis)
                    with col2:
                        m_dis = (user == 'jsafaa')
                        m_txt = st.text_area("Manager Decision", value=df_appeals.loc[idx, "Direct Manager"], disabled=m_dis)
                    if st.button("Save Changes"):
                        df_appeals.loc[idx, "Quality Decision"] = q_txt
                        df_appeals.loc[idx, "Direct Manager"] = m_txt
                        df_appeals.to_csv("database_appeals.csv", index=False)
                        st.cache_data.clear()
                        st.success("Saved!")
                        st.rerun()
        else:
            with st.form("sub_form"):
                f_tkt = st.text_input("Ticket Number")
                f_det = st.text_area("Details")
                if st.form_submit_button("Submit"):
                    new_obj = {
                        "Employee": user, "Date": str(datetime.now().date()), 
                        "Ticket Number": f_tkt, "Details": f_det,
                        "Quality Decision": "Pending", "Direct Manager": "Pending",
                        "Objection Issue Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    df_appeals = pd.concat([df_appeals, pd.DataFrame([new_obj])], ignore_index=True)
                    df_appeals.to_csv("database_appeals.csv", index=False)
                    st.cache_data.clear()
                    st.success("Success!")
                    st.rerun()

    if is_admin:
        with main_tabs[1]:
            st.subheader("👥 Management Tools")
            with st.expander("🔄 Reset Password"):
                u_sel = st.selectbox("User", users_df['username'].values)
                if st.button("Reset to 123"):
                    users_df.loc[users_df['username'] == u_sel, 'password'] = "123"
                    users_df.loc[users_df['username'] == u_sel, 'Force_Change'] = True
                    users_df.to_csv("users_list.csv", index=False)
                    st.cache_data.clear()
                    st.success(f"Reset {u_sel}")

            with st.expander("➕ Add User"):
                n_u = st.text_input("Username").lower()
                n_n = st.text_input("Name")
                if st.button("Add"):
                    if n_u and n_u not in users_df['username'].values:
                        new_u = {"username": n_u, "password": "123", "name": n_n, "role": "Employee", "Force_Change": True}
                        users_df = pd.concat([users_df, pd.DataFrame([new_u])], ignore_index=True)
                        users_df.to_csv("users_list.csv", index=False)
                        st.cache_data.clear()
                        st.rerun()

elif st.session_state.get("authentication_status") == False:
    st.error("Invalid Credentials")
