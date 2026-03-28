import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 🚀 Page Configuration ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- Custom CSS for English Layout & Notifications ---
st.markdown("""
    <style>
        .main-title { font-size:40px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        div[data-testid="stExpander"] { 
            background-color: rgba(240, 242, 246, 0.5); 
            border-radius: 10px; 
            border: 1px solid #d1d5db;
        }
        .stMarkdown h3 { color: #1E3A8A !important; }
        .user-name-sidebar { color: #4CAF50; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
        
        /* Notification Banner Design */
        .notification-banner {
            padding: 15px;
            background-color: #ffeeb2;
            border-left: 6px solid #ffcc00;
            border-radius: 5px;
            color: #856404;
            font-weight: bold;
            margin-bottom: 20px;
            font-size: 18px;
        }

        /* 🎨 Custom Stats Cards Styling */
        .stat-card {
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 10px;
        }
        .stat-label { font-size: 16px; font-weight: bold; margin-bottom: 5px; }
        .stat-value { font-size: 32px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- File Names ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

# --- 🛠️ Data Loading Functions ---
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
                # إضافة عمود first_login هنا
                user_data.append({"username": u, "password": p, "name": u.upper(), "role": role, "first_login": True})
            pd.DataFrame(user_data).to_csv(users_file, index=False)
        
        temp_df = pd.read_csv(users_file)
        # تأكد أن العمود موجود في الملف في حال كان الملف قديماً
        if "first_login" not in temp_df.columns:
            temp_df["first_login"] = True
            temp_df.to_csv(users_file, index=False)
        st.session_state.u_df = temp_df
    return st.session_state.u_df

users_df = get_users_df()
df_appeals = get_all_data()

# --- Authenticator Setup ---
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][row['username']] = {'name': f"{row['name']} ({row['role']})", 'password': str(row['password'])}

if 'auth_obj' not in st.session_state:
    st.session_state.auth_obj = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30)

authenticator = st.session_state.auth_obj

# --- App Interface (English) ---
st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

try:
    authenticator.login()
except:
    try: authenticator.login('main')
    except: authenticator.login('Login', 'main')

if st.session_state.get("authentication_status"):
    username = st.session_state.get("username")
    
    # جلب معلومات المستخدم الحالي للتحقق من أول دخول
    user_row = users_df[users_df['username'] == username].iloc[0]
    is_first_login = user_row['first_login']

    if is_first_login:
        # --- 🔒 إجبار المستخدم على تغيير كلمة المرور ---
        st.warning("⚠️ Security Alert: This is your first login. You must change your default password to continue.")
        with st.form("change_password_form"):
            new_pwd = st.text_input("New Password", type="password")
            conf_pwd = st.text_input("Confirm New Password", type="password")
            submit_change = st.form_submit_button("Update Password & Enter System")

            if submit_change:
                if len(new_pwd) < 3:
                    st.error("Password is too short!")
                elif new_pwd != conf_pwd:
                    st.error("Passwords do not match!")
                else:
                    # تحديث كلمة المرور وحالة أول دخول في الـ DataFrame والملف
                    users_df.loc[users_df['username'] == username, 'password'] = new_pwd
                    users_df.loc[users_df['username'] == username, 'first_login'] = False
                    users_df.to_csv(users_file, index=False)
                    
                    # تنظيف الـ session state لإعادة التحميل بالبيانات الجديدة
                    if 'u_df' in st.session_state: st.session_state.pop('u_df')
                    st.success("Password updated successfully! Redirecting...")
                    st.rerun()
        st.stop() # يمنع ظهور باقي الكود حتى يغير الباسورد

    # --- الكود الأصلي بعد تغيير الباسورد ---
    if username in credentials['usernames']:
        display_name = credentials['usernames'][username]['name']
        st.sidebar.markdown(f'<div class="user-name-sidebar">👤 {display_name}</div>', unsafe_allow_html=True)
    
    authenticator.logout('Logout', 'sidebar')
    
    if "Objection Issue Date" not in df_appeals.columns:
        df_appeals["Objection Issue Date"] = ""
        df_appeals.to_csv(appeals_file, index=False)

    # --- 📊 Statistics & Notifications (For Jassim & Hatim Only) ---
    if username in ['jsafaa', 'ahatim']:
        pending_obs = df_appeals[(df_appeals['Quality Decision'] == 'Pending') | (df_appeals['Direct Manager'] == 'Pending')]
        
        if not pending_obs.empty:
            names_str = ", ".join(pending_obs['Employee'].unique())
            st.markdown(f'<div class="notification-banner">🔔 ALERT: Pending objections from: {names_str}</div>', unsafe_allow_html=True)

        # 📈 Colored Statistics Overview
        st.subheader("📈 System Statistics Overview")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'''<div class="stat-card" style="background-color: #e3f2fd; border-left: 6px solid #1565c0;">
                <div class="stat-label" style="color: #1565c0;">Total Objections</div>
                <div class="stat-value" style="color: #0d47a1;">{len(df_appeals)}</div>
            </div>''', unsafe_allow_html=True)
        with c2:
            st.markdown(f'''<div class="stat-card" style="background-color: #fff3e0; border-left: 6px solid #ef6c00;">
                <div class="stat-label" style="color: #ef6c00;">Pending Review</div>
                <div class="stat-value" style="color: #e65100;">{len(pending_obs)}</div>
            </div>''', unsafe_allow_html=True)
        with c3:
            acc_count = len(df_appeals[(df_appeals['Quality Decision'] == 'Accepted') & (df_appeals['Direct Manager'] == 'Accepted')])
            st.markdown(f'''<div class="stat-card" style="background-color: #e8f5e9; border-left: 6px solid #2e7d32;">
                <div class="stat-label" style="color: #2e7d32;">Fully Accepted</div>
                <div class="stat-value" style="color: #1b5e20;">{acc_count}</div>
            </div>''', unsafe_allow_html=True)
        st.divider()

    # Tab System
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
                        if 'main_df' in st.session_state: st.session_state.pop('main_df')
                        st.success("Changes Saved Successfully!"); st.rerun()
        else:
            t_sub, t_hist = st.tabs(["📤 Submit Objection", "📜 History"])
            with t_sub:
                with st.form("obj_form", clear_on_submit=True):
                    f_date = st.date_input("Incident Date", datetime.now())
                    f_ticket = st.text_input("Ticket Number")
                    f_tab = st.selectbox("Department", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Alwatani-Services", "BRIDGES", "Wireless", "IRQNBN", "ITPC", "MERTO", "NAS's", "Server Room", "Power", "AL-Watani Power"])
                    f_details = st.text_area("Objection Details")
                    if st.form_submit_button("Submit"):
                        baghdad_now = datetime.utcnow() + timedelta(hours=3)
                        if baghdad_now.day >= 18 and f_date.day <= 15:
                            st.error("❌ Access Denied: Deadline passed.")
                        elif not f_ticket or not f_details: st.error("❌ Fill all fields!")
                        else:
                            submission_time = baghdad_now.strftime("%Y-%m-%d %H:%M:%S")
                            new_row = {"Employee": st.session_state.get("name"), "Date": str(f_date), "Ticket Number": f_ticket, "Tab": f_tab, "Details": f_details, "Quality Decision": "Pending", "Direct Manager": "Pending", "Objection Issue Date": submission_time}
                            updated_df = pd.concat([df_appeals, pd.DataFrame([new_row])], ignore_index=True)
                            updated_df.to_csv(appeals_file, index=False)
                            st.session_state.main_df = updated_df
                            st.success(f"Submitted at {submission_time}!"); st.balloons()
            with t_hist: 
                user_history = df_appeals[df_appeals['Employee'] == st.session_state.get("name")]
                st.dataframe(user_history, use_container_width=True)

    if username == 'jsafaa':
        with admin_users_tab:
            st.subheader("👥 Employee Directory Management")
            with st.expander("➕ Add New Employee"):
                new_u = st.text_input("New Username").lower().strip()
                new_n = st.text_input("Full Name (Display)")
                if st.button("Register User"):
                    if new_u and new_u not in users_df['username'].values:
                        # إضافة first_login هنا أيضاً للمستخدمين الجدد
                        new_user_row = {"username": new_u, "password": "123", "name": new_n, "role": "Employee", "first_login": True}
                        users_df = pd.concat([users_df, pd.DataFrame([new_user_row])], ignore_index=True)
                        users_df.to_csv(users_file, index=False)
                        st.session_state.pop('u_df'); st.success("User registered!"); st.rerun()

            with st.expander("🔑 Reset Password"):
                target_user = st.selectbox("Select User Account", users_df['username'].values)
                new_pass = st.text_input("New Password", type="password")
                if st.button("Confirm Reset"):
                    users_df.loc[users_df['username'] == target_user, 'password'] = new_pass
                    # عند تصفير الباسورد من الأدمن، هل تريد إجباره مرة أخرى؟ إذا نعم، اجعل السطر التالي True
                    users_df.loc[users_df['username'] == target_user, 'first_login'] = False 
                    users_df.to_csv(users_file, index=False)
                    st.session_state.pop('u_df'); st.success(f"Updated {target_user}!")

            with st.expander("🗑️ Delete Account"):
                del_user = st.selectbox("User to Remove", [u for u in users_df['username'].values if u not in ['jsafaa', 'ahatim']])
                if st.button("Final Delete"):
                    users_df = users_df[users_df['username'] != del_user]
                    users_df.to_csv(users_file, index=False)
                    st.session_state.pop('u_df'); st.warning(f"Deleted {del_user}!"); st.rerun()

elif st.session_state.get("authentication_status") == False: st.error("Incorrect Username or Password")
else: st.info("Authentication Required.")
