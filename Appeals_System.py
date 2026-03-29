import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 🚀 Page Configuration ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- ⚡ التحسين الأول: تخزين البيانات في الذاكرة الدائمة للجلسة ---
if 'df_appeals' not in st.session_state:
    appeals_file = "database_appeals.csv"
    if not os.path.exists(appeals_file):
        pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "KPI", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date", "Admin Notes"]).to_csv(appeals_file, index=False)
    st.session_state.df_appeals = pd.read_csv(appeals_file)

if 'users_df' not in st.session_state:
    users_file = "users_list.csv"
    if not os.path.exists(users_file):
        initial_users = ["ahatim", "mkhalid", "hfalah", "hmuayyad", "alimad", "rriyad", "hjabbar", "hmuhammada", "arubayi", "aadil", "ayasin", "fahmad", "hakali", "musadiq", "itsattar", "amusadaq", "aanbari", "afahad", "rthair", "omsubhi", "rwahab", "mlayth", "yasadi", "yriyad", "abfaysal", "hasanhadi", "hamuhsin", "aybasheer", "marmahmud", "abisameer", "jsafaa", "muhahamid", "murqasim", "moayad", "dadnan", "abiabbas", "qriyad", "tmustafa", "sbahnan", "admuhammad", "amohammad", "shzuhayr"]
        user_data = [{"username": u, "password": ('admin123' if u == 'jsafaa' else ('manager123' if u == 'ahatim' else '123')), "name": u.upper(), "role": ('Head Of Section' if u == 'ahatim' else ('Quality Engineer' if u == 'jsafaa' else 'Employee')), "first_login": True} for u in initial_users]
        pd.DataFrame(user_data).to_csv(users_file, index=False)
    st.session_state.users_df = pd.read_csv(users_file)

# --- ⚡ التحسين الثاني: تشغيل نظام المصادقة مرة واحدة فقط (The Core Speed Fix) ---
if 'authenticator' not in st.session_state:
    users_df = st.session_state.users_df
    credentials = {'usernames': {}}
    for row in users_df.itertuples(index=False):
        credentials['usernames'][str(row.username)] = {
            'name': str(row.name), 
            'password': str(row.password), 
            'role': str(row.role)
        }
    # تخزين الكائن بالكامل لتجنب إعادة معالجة الكوكيز في كل Run
    st.session_state.authenticator = stauth.Authenticate(
        credentials, 'nmc_objections_cookie', 'auth_key_123', cookie_expiry_days=30
    )

authenticator = st.session_state.authenticator

# --- Custom CSS ---
st.markdown("""
    <style>
        .main-title { font-size:40px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        div[data-testid="stExpander"] { background-color: rgba(240, 242, 246, 0.5); border-radius: 10px; border: 1px solid #d1d5db; }
        .user-name-sidebar { color: #4CAF50; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
        .stat-card { padding: 20px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 10px; }
        .stat-label { font-size: 16px; font-weight: bold; margin-bottom: 5px; }
        .stat-value { font-size: 32px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

# تسجيل الدخول
res = authenticator.login('main')

if st.session_state["authentication_status"]:
    username = st.session_state["username"]
    full_name = st.session_state.users_df.loc[st.session_state.users_df['username'] == username, 'name'].values[0]
    user_info = st.session_state.users_df[st.session_state.users_df['username'] == username].iloc[0]

    # --- Forced Password Change Logic (Simplified for speed) ---
    if user_info['first_login']:
        st.warning("⚠️ Security: Change your password.")
        with st.form("pwd_form"):
            new_p = st.text_input("New Password", type="password")
            if st.form_submit_button("Update"):
                st.session_state.users_df.loc[st.session_state.users_df['username'] == username, ['password', 'first_login']] = [new_p, False]
                st.session_state.users_df.to_csv("users_list.csv", index=False)
                st.success("Updated! Please logout and login again.")
        st.stop()

    st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {full_name}</div>', unsafe_allow_html=True)
    authenticator.logout('Logout', 'sidebar')

    # --- Admin Dashboard ---
    if username in ['jsafaa', 'ahatim']:
        df_appeals = st.session_state.df_appeals
        pending_obs = df_appeals[(df_appeals['Quality Decision'] == 'Pending') | (df_appeals['Direct Manager'] == 'Pending')]
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="stat-card" style="background-color:#E1BEE7;"><div class="stat-label">Total</div><div class="stat-value">{len(df_appeals)}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="background-color:#FFCC80;"><div class="stat-label">Pending</div><div class="stat-value">{len(pending_obs)}</div></div>', unsafe_allow_html=True)
        with c3:
            acc = len(df_appeals[(df_appeals['Quality Decision'] == 'Accepted') & (df_appeals['Direct Manager'] == 'Accepted')])
            st.markdown(f'<div class="stat-card" style="background-color:#C8E6C9;"><div class="stat-label">Fully Accepted</div><div class="stat-value">{acc}</div></div>', unsafe_allow_html=True)

    # --- Tabs ---
    if username == 'jsafaa':
        main_tab, admin_users_tab = st.tabs(["📊 Main System", "👥 Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        if username in ['jsafaa', 'ahatim']:
            st.subheader("🛠 MANAGEMENT CONTROL PANEL")
            df_display = st.session_state.df_appeals.copy()
            df_display['Final Status'] = df_display.apply(lambda r: "✅ Fully Accepted" if r['Quality Decision'] == 'Accepted' and r['Direct Manager'] == 'Accepted' else ("❌ Fully Rejected" if r['Quality Decision'] == 'Rejected' and r['Direct Manager'] == 'Rejected' else "⏳ Processing"), axis=1)
            st.dataframe(df_display, use_container_width=True)

            with st.expander("Update Decisions"):
                if not st.session_state.df_appeals.empty:
                    idx = st.number_input("Select Row Index", 0, len(st.session_state.df_appeals)-1, 0)
                    col1, col2 = st.columns(2)
                    options = ["Pending", "Accepted", "Rejected"]
                    with col1:
                        q_dec = st.selectbox("Quality Decision", options, index=options.index(st.session_state.df_appeals.loc[idx, "Quality Decision"]), disabled=(username == 'ahatim'))
                    with col2:
                        m_dec = st.selectbox("Head Of Section Decision", options, index=options.index(st.session_state.df_appeals.loc[idx, "Direct Manager"]), disabled=(username == 'jsafaa'))
                    
                    if st.button("Save Changes"):
                        if username == 'jsafaa': st.session_state.df_appeals.loc[idx, "Quality Decision"] = q_dec
                        if username == 'ahatim': st.session_state.df_appeals.loc[idx, "Direct Manager"] = m_dec
                        st.session_state.df_appeals.to_csv("database_appeals.csv", index=False)
                        st.success("Saved!"); st.rerun()
        else:
            t1, t2 = st.tabs(["📤 Submit Objection", "📜 History"])
            with t1:
                with st.form("obj_form", clear_on_submit=True):
                    f_date = st.date_input("Incident Date", datetime.now())
                    f_ticket = st.text_input("Ticket Number")
                    f_kpi = st.selectbox("KPI Type", ["Done Delay", "Done Delay Response", "High MTTD", "Shift Delay", "Delay High Impact", "Closing Issue", "Reduce Number Of Incident", "FMS", "Delay FMS", "Number Of Delay FMS", "No Task"])
                    f_tab = st.selectbox("Department", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Alwatani-Services", "BRIDGES", "Wireless", "IRQNBN", "ITPC", "MERTO", "NAS's", "Server Room", "Power", "AL-Watani Power"])
                    f_details = st.text_area("Details")
                    if st.form_submit_button("Submit"):
                        baghdad_now = datetime.utcnow() + timedelta(hours=3)
                        new_row = {"Employee": full_name, "Date": str(f_date), "Ticket Number": f_ticket, "KPI": f_kpi, "Tab": f_tab, "Details": f_details, "Quality Decision": "Pending", "Direct Manager": "Pending", "Objection Issue Date": baghdad_now.strftime("%Y-%m-%d %
