import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 🚀 تحسين استجابة الصفحة ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- File Names ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

# --- 🛠️ دوال قراءة البيانات الذكية (تمنع الثقل) ---
def get_all_data():
    if 'main_df' not in st.session_state:
        if not os.path.exists(appeals_file):
            pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date"]).to_csv(appeals_file, index=False)
        st.session_state.main_df = pd.read_csv(appeals_file)
    return st.session_state.main_df

def get_users_df():
    if 'u_df' not in st.session_state:
        if not os.path.exists(users_file):
            initial_users = ["ahatim", "mkhalid", "hfalah", "hmuayyad", "alimad", "rriyad", "hjabbar", "hmuhammada", "arubayi", "aadil", "ayasin", "fahmad", "hakali", "musadiq", "itsattar", "amusadaq", "aanbari", "afahad", "rthair", "omsubhi", "rwahab", "mlayth", "yasadi", "yriyad", "abfaysal", "hasanhadi", "hamuhsin", "aybasheer", "marmahmud", "abisameer", "jsafaa", "muhahamid", "murqasim", "moayad", "dadnan", "abiabbas", "qriyad", "tmustafa", "sbahnan", "admuhammad", "amohammad", "shzuhayr"]
            user_data = []
            for u in initial_users:
                p = 'admin123' if u == 'jsafaa' else ('manager123' if u == 'ahatim' else '123')
                role = 'Head Of Section' if u == 'ahatim' else ('Quality Engineer' if u == 'jsafaa' else 'Employee')
                user_data.append({"username": u, "password": p, "name": u.upper(), "role": role})
            pd.DataFrame(user_data).to_csv(users_file, index=False)
        st.session_state.u_df = pd.read_csv(users_file)
    return st.session_state.u_df

# تحميل البيانات للعمل
users_df = get_users_df()
df_appeals = get_all_data()

# --- Authenticator Setup (Caching Optimized) ---
if 'auth_obj' not in st.session_state:
    credentials = {'usernames': {}}
    for _, row in users_df.iterrows():
        credentials['usernames'][row['username']] = {'name': f"{row['name']} ({row['role']})", 'password': str(row['password'])}
    st.session_state.auth_obj = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30)

authenticator = st.session_state.auth_obj

# --- App Interface ---
st.markdown("""<style>
    .main-title { font-size:40px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
    div[data-testid="stExpander"] { background-color: #f9f9f9; border-radius: 10px; }
</style>
<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>""", unsafe_allow_html=True)

try:
    authenticator.login()
except:
    try: authenticator.login('main')
    except: authenticator.login('Login', 'main')

if st.session_state.get("authentication_status"):
    username = st.session_state.get("username")
    authenticator.logout('Logout', 'sidebar')
    
    # التأكد من وجود الأعمدة
    if "Objection Issue Date" not in df_appeals.columns:
        df_appeals["Objection Issue Date"] = ""
        df_appeals.to_csv(appeals_file, index=False)

    if username == 'jsafaa':
        main_tab, admin_users_tab = st.tabs(["📊 Main System", "👥 Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        if username in ['jsafaa', 'ahatim']:
            st.subheader("🛠 MANAGEMENT CONTROL PANEL")
            st.dataframe(df_appeals, use_container_width=True)
            with st.expander("Update Decisions"):
                if not df_appeals.empty:
                    row_idx = st.number_input("Select Row ID", 0, len(df_appeals)-1, 0)
                    col1, col2 = st.columns(2)
                    with col1:
                        q_dec = st.text_area("Quality Decision", value=df_appeals.loc[row_idx, "Quality Decision"], disabled=(username == 'ahatim'))
                    with col2:
                        m_dec = st.text_area("Head Of Section Decision", value=df_appeals.loc[row_idx, "Direct Manager"], disabled=(username == 'jsafaa'))
                    if st.button("Save Changes"):
                        df_appeals.loc[row_idx, "Quality Decision"] = q_dec
                        df_appeals.loc[row_idx, "Direct Manager"] = m_dec
                        df_appeals.to_csv(appeals_file, index=False)
                        st.session_state.pop('main_df') # مسح الكاش لإعادة القراءة
                        st.success("Updated!")
                        st.rerun()
        
        else:
            t_sub, t_hist = st.tabs(["📤 Submit", "📜 History"])
            with t_sub:
                with st.form("obj_form", clear_on_submit=True):
                    f_date = st.date_input("Date", datetime.now()); f_ticket = st.text_input("Ticket Number")
                    f_tab = st.selectbox("Tab", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Alwatani-Services", "BRIDGES", "Wireless", "IRQNBN", "ITPC", "MERTO", "NAS's", "Server Room", "Power", "AL-Watani Power"])
                    f_details = st.text_area("Details")
                    if st.form_submit_button("Submit"):
                        baghdad_now = datetime.utcnow() + timedelta(hours=3)
                        if baghdad_now.day >= 18 and f_date.day <= 15:
                            st.error("❌ Error: Exceeded objection period for 1st half.")
                        elif not f_ticket or not f_details: st.error("❌ Fill all fields!")
                        else:
                            submission_time = baghdad_now.strftime("%Y-%m-%d %H:%M:%S")
                            new_row = {"Employee": st.session_state.get("name"), "Date": str(f_date), "Ticket Number": f_ticket, "Tab": f_tab, "Details": f_details, "Quality Decision": "Pending", "Direct Manager": "Pending", "Objection Issue Date": submission_time}
                            updated_df = pd.concat([df_appeals, pd.DataFrame([new_row])], ignore_index=True)
                            updated_df.to_csv(appeals_file, index=False)
                            st.session_state.main_df = updated_df # تحديث اللحظي
                            st.success(f"Submitted at {submission_time}!"); st.balloons()
            with t_hist: 
                st.dataframe(df_appeals[df_appeals['Employee'] == st.session_state.get("name")], use_container_width=True)

    if username == 'jsafaa':
        with admin_users_tab:
            st.subheader("👥 Employee Directory Management")
            with st.expander("➕ Add New Employee"):
                new_u = st.text_input("New Username").lower().strip()
                new_n = st.text_input("Full Name (Display)")
                if st.button("Add to System"):
                    if new_u and new_u not in users_df['username'].values:
                        new_user_row = {"username": new_u, "password": "123", "name": new_n, "role": "Employee"}
                        users_df = pd.concat([users_df, pd.DataFrame([new_user_row])], ignore_index=True)
                        users_df.to_csv(users_file, index=False)
                        st.session_state.pop('u_df')
                        st.success(f"User {new_u} added!")
                        st.rerun()

            with st.expander("🔑 Change Employee Password"):
                target_user = st.selectbox("Select User", users_df['username'].values)
                new_pass = st.text_input("New Password", type="password")
                if st.button("Update Password"):
                    users_df.loc[users_df['username'] == target_user, 'password'] = new_pass
                    users_df.to_csv(users_file, index=False)
                    st.session_state.pop('u_df')
                    st.success(f"Password for {target_user} updated!")

            with st.expander("🗑️ Remove Employee"):
                del_user = st.selectbox("Select User to Remove", [u for u in users_df['username'].values if u not in ['jsafaa', 'ahatim']])
                if st.button("Confirm Delete"):
                    users_df = users_df[users_df['username'] != del_user]
                    users_df.to_csv(users_file, index=False)
                    st.session_state.pop('u_df')
                    st.warning(f"User {del_user} removed.")
                    st.rerun()

elif st.session_state.get("authentication_status") == False: st.error("Wrong info")
else: st.info("Please Login")
