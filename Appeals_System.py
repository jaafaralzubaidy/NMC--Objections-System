import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta
import requests
import random

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# دالة لضبط الوقت والطقس والأجواء حسب توقيت بغداد (UTC+3)
def get_baghdad_ui():
    # جلب الوقت العالمي وتحويله لتوقيت بغداد
    now_baghdad = datetime.utcnow() + timedelta(hours=3)
    hour = now_baghdad.hour
    time_str = now_baghdad.strftime('%I:%M %p') # نظام 12 ساعة
    date_str = now_baghdad.strftime('%Y-%m-%d')

    try:
        # جلب حرارة بغداد الحقيقية مع منع التخزين القديم (Cache Busting)
        cb = random.randint(1, 9999)
        res = requests.get(f"https://wttr.in/Baghdad?format=%t&_={cb}", timeout=5)
        temp = res.text.strip() if res.status_code == 200 else "N/A"
    except:
        temp = "N/A"
    
    # اختيار الأجواء والأيقونات بدقة حسب ساعة بغداد
    if 5 <= hour < 7: # وقت الفجر
        bg, icon, msg = "linear-gradient(to right, #4facfe, #00f2fe)", "🌅", "Good Early Morning"
    elif 7 <= hour < 12: # الصباح
        bg, icon, msg = "linear-gradient(to right, #fceabb, #f8b500)", "🌞", "Good Morning"
    elif 12 <= hour < 17: # الظهر
        bg, icon, msg = "linear-gradient(to right, #2980b9, #6dd5fa, #ffffff)", "☀️", "Good Afternoon"
    elif 17 <= hour < 20: # المساء/الغروب
        bg, icon, msg = "linear-gradient(to right, #f83600, #f9d423)", "🌆", "Good Evening"
    else: # الليل
        bg, icon, msg = "linear-gradient(to bottom, #0f2027, #203a43, #2c5364)", "🌙", "Good Night"
        
    return temp, bg, icon, msg, time_str, date_str

temp_val, bg_style, sky_icon, welcome_msg, b_time, b_date = get_baghdad_ui()

# تطبيق التصميم الجمالي CSS (Dark Glassmorphism)
st.markdown(f"""
    <style>
    .stApp {{ background: {bg_style}; background-attachment: fixed; }}
    .header-box {{
        background-color: rgba(0, 0, 0, 0.5);
        padding: 25px; border-radius: 20px; text-align: center;
        backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 25px; color: white;
    }}
    .main-title {{ font-size:45px !important; font-weight: bold; text-shadow: 2px 2px 10px #000; color: #FFFFFF; }}
    .info-bar {{ font-size:20px; margin-top:10px; color: #E0E0E0; }}
    .welcome-text {{ font-weight:bold; margin-top:15px; font-size:26px; color: #FFD700; text-shadow: 1px 1px 5px #000; }}
    </style>
    <div class="header-box">
        <div class="main-title">{sky_icon} NMC OBJECTIONS SYSTEM</div>
        <div class="info-bar">
            📅 {b_date} | 🕒 {b_time} (Baghdad Time) | 🌡️ Temp: {temp_val}
        </div>
        <div class="welcome-text">{welcome_msg}</div>
    </div>
""", unsafe_allow_html=True)

# --- 2. ملفات البيانات ---
users_file = "users_list.csv"
appeals_file = "database_appeals.csv"

# إنشاء ملفات البيانات إذا لم تكن موجودة
if not os.path.exists(users_file):
    data = [
        {"username": "jsafaa", "password": "admin123", "name": "J. SAFAA", "role": "Quality Engineer"},
        {"username": "ahatim", "password": "manager123", "name": "A. HATIM", "role": "Head Of Section"}
    ]
    pd.DataFrame(data).to_csv(users_file, index=False)

users_df = pd.read_csv(users_file)
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][row['username']] = {'name': f"{row['name']} ({row['role']})", 'password': str(row['password'])}

authenticator = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30)

# --- 3. تسجيل الدخول ---
try:
    authenticator.login('main')
except:
    try: authenticator.login()
    except: st.error("Login Module Error")

if st.session_state.get("authentication_status"):
    username = st.session_state.get("username")
    authenticator.logout('Logout', 'sidebar')
    
    if not os.path.exists(appeals_file):
        pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager"]).to_csv(appeals_file, index=False)
    df_appeals = pd.read_csv(appeals_file)

    # --- 4. التبويبات حسب الصلاحية ---
    if username == 'jsafaa':
        main_tab, staff_tab = st.tabs(["📊 Operations Portal", "👥 Admin: Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        # واجهة الكوالتي انجنير ورئيس القسم
        if username in ['jsafaa', 'ahatim']:
            st.subheader("🛠 Control Panel")
            st.dataframe(df_appeals, use_container_width=True)
            with st.expander("Update Decisions (Fixed Logic)"):
                if not df_appeals.empty:
                    row_idx = st.number_input("Select Row ID", 0, len(df_appeals)-1, 0)
                    c1, c2 = st.columns(2)
                    with c1:
                        q_input = st.text_area("Quality Decision", value=df_appeals.loc[row_idx, "Quality Decision"], disabled=(username == 'ahatim'))
                    with c2:
                        m_input = st.text_area("Head Of Section Decision", value=df_appeals.loc[row_idx, "Direct Manager"], disabled=(username == 'jsafaa'))
                    if st.button("Save Changes"):
                        df_appeals.loc[row_idx, "Quality Decision"] = q_input
                        df_appeals.loc[row_idx, "Direct Manager"] = m_input
                        df_appeals.to_csv(appeals_file, index=False); st.success("Updated!"); st.rerun()
        
        # واجهة الموظفين
        else:
            t1, t2 = st.tabs(["📤 Submit New Objection", "📜 My Records"])
            with t1:
                with st.form("ob_form"):
                    fd = st.date_input("Incident Date"); ft = st.text_input("Ticket Number")
                    ftb = st.selectbox("Department/Tab", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Alwatani-Services", "BRIDGES", "Wireless", "IRQNBN", "ITPC", "MERTO", "NAS's", "Server Room", "Power", "AL-Watani Power"])
                    fdt = st.text_area("Describe the issue")
                    if st.form_submit_button("Submit"):
                        # فحص قفل الوقت حسب توقيت بغداد
                        now_b = datetime.utcnow() + timedelta(hours=3)
                        if now_b.day >= 18 and fd.day <= 15:
                            st.error("❌ Time-Lock: Submission period for the first half is closed.")
                        elif not ft or not fdt: st.error("❌ Please fill all fields.")
                        else:
                            new_r = {"Employee": st.session_state.get("name"), "Date": str(fd), "Ticket Number": ft, "Tab": ftb, "Details": fdt, "Quality Decision": "Pending Review", "Direct Manager": "Pending Review"}
                            df_appeals = pd.concat([df_appeals, pd.DataFrame([new_r])], ignore_index=True)
                            df_appeals.to_csv(appeals_file, index=False); st.success("Submitted!"); st.balloons()
            with t2: st.table(df_appeals[df_appeals['Employee'] == st.session_state.get("name")])

    # --- 5. لوحة تحكم الآدمن (jsafaa فقط) ---
    if username == 'jsafaa':
        with staff_tab:
            st.subheader("👥 Directory Management")
            with st.expander("➕ Add New Staff Member"):
                nu = st.text_input("Username (lowercase)").lower().strip()
                nn = st.text_input("Full Display Name")
                if st.button("Add to System"):
                    if nu and nu not in users_df['username'].values:
                        users_df = pd.concat([users_df, pd.DataFrame([{"username": nu, "password": "123", "name": nn, "role": "Employee"}])], ignore_index=True)
                        users_df.to_csv(users_file, index=False); st.success("Added! Re-login to apply changes.")
            with st.expander("🔑 Reset Password"):
                target = st.selectbox("Select Staff Member", users_df['username'].values)
                new_p = st.text_input("New Password", type="password")
                if st.button("Update Pass"):
                    users_df.loc[users_df['username'] == target, 'password'] = new_p
                    users_df.to_csv(users_file, index=False); st.success("Password Updated!")
            with st.expander("🗑️ Delete User"):
                du = st.selectbox("Select User to Remove", [u for u in users_df['username'].values if u not in ['jsafaa', 'ahatim']])
                if st.button("Remove Permanently"):
                    users_df = users_df[users_df['username'] != du]
                    users_df.to_csv(users_file, index=False); st.warning(f"User {du} removed."); st.rerun()

elif st.session_state.get("authentication_status") == False: st.error("Wrong credentials")
else: st.info("Welcome to the NMC Objections Portal. Please log in.")