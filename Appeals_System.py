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
    # توقيت بغداد الحقيقي
    now_baghdad = datetime.utcnow() + timedelta(hours=3)
    hour = now_baghdad.hour
    time_str = now_baghdad.strftime('%I:%M %p')
    date_str = now_baghdad.strftime('%Y-%m-%d')
    full_timestamp = now_baghdad.strftime('%Y-%m-%d %H:%M:%S')

    try:
        # محاولة جلب الحرارة برابط أكثر استقراراً
        cb = random.randint(1, 9999)
        res = requests.get(f"https://wttr.in/Baghdad?format=%t&m&_={cb}", timeout=5)
        temp = res.text.strip() if res.status_code == 200 and "+" in res.text else "Updating..."
    except:
        temp = "Check Connection"
    
    # اختيار الأجواء
    if 5 <= hour < 7:
        bg, icon, msg = "linear-gradient(to right, #4facfe, #00f2fe)", "🌅", "Good Early Morning"
    elif 7 <= hour < 12:
        bg, icon, msg = "linear-gradient(to right, #fceabb, #f8b500)", "🌞", "Good Morning"
    elif 12 <= hour < 17:
        bg, icon, msg = "linear-gradient(to right, #2980b9, #6dd5fa, #ffffff)", "☀️", "Good Afternoon"
    elif 17 <= hour < 20:
        bg, icon, msg = "linear-gradient(to right, #f83600, #f9d423)", "🌆", "Good Evening"
    else:
        bg, icon, msg = "linear-gradient(to bottom, #0f2027, #203a43, #2c5364)", "🌙", "Good Night"
        
    return temp, bg, icon, msg, time_str, date_str, full_timestamp

temp_val, bg_style, sky_icon, welcome_msg, b_time, b_date, b_full_now = get_baghdad_ui()

# تصميم الواجهة
st.markdown(f"""
    <style>
    .stApp {{ background: {bg_style}; background-attachment: fixed; }}
    .header-box {{
        background-color: rgba(0, 0, 0, 0.5);
        padding: 25px; border-radius: 20px; text-align: center;
        backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 25px; color: white;
    }}
    .main-title {{ font-size:40px !important; font-weight: bold; text-shadow: 2px 2px 10px #000; }}
    </style>
    <div class="header-box">
        <div class="main-title">{sky_icon} NMC OBJECTIONS SYSTEM</div>
        <div style="font-size:18px;">📅 {b_date} | 🕒 {b_time} | 🌡️ Temp: {temp_val}</div>
        <div style="font-weight:bold; margin-top:10px; font-size:22px; color: #FFD700;">{welcome_msg}</div>
    </div>
""", unsafe_allow_html=True)

# --- 2. البيانات ---
users_file = "users_list.csv"
appeals_file = "database_appeals.csv"

if not os.path.exists(users_file):
    data = [{"username": "jsafaa", "password": "admin123", "name": "J. SAFAA", "role": "Quality Engineer"}]
    pd.DataFrame(data).to_csv(users_file, index=False)

users_df = pd.read_csv(users_file)
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][row['username']] = {'name': f"{row['name']} ({row['role']})", 'password': str(row['password'])}

authenticator = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30)

try:
    authenticator.login('main')
except:
    try: authenticator.login()
    except: st.error("Login Error")

if st.session_state.get("authentication_status"):
    username = st.session_state.get("username")
    authenticator.logout('Logout', 'sidebar')
    
    # تحديث أعمدة قاعدة البيانات لتشمل التاريخ الأوتوماتيكي
    if not os.path.exists(appeals_file):
        pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Creation Date"]).to_csv(appeals_file, index=False)
    
    df_appeals = pd.read_csv(appeals_file)
    # التأكد من وجود العمود في حال كان الملف قديماً
    if "Objection Creation Date" not in df_appeals.columns:
        df_appeals["Objection Creation Date"] = "N/A"

    if username == 'jsafaa':
        main_tab, staff_tab = st.tabs(["📊 Operations Portal", "👥 Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        if username in ['jsafaa', 'ahatim']:
            st.subheader("🛠 Control Panel")
            st.dataframe(df_appeals, use_container_width=True)
            with st.expander("Update Decisions"):
                if not df_appeals.empty:
                    row_idx = st.number_input("Select Row", 0, len(df_appeals)-1, 0)
                    c1, c2 = st.columns(2)
                    with c1: q_in = st.text_area("Quality Decision", value=df_appeals.loc[row_idx, "Quality Decision"], disabled=(username == 'ahatim'))
                    with c2: m_in = st.text_area("Manager Decision", value=df_appeals.loc[row_idx, "Direct Manager"], disabled=(username == 'jsafaa'))
                    if st.button("Save Changes"):
                        df_appeals.loc[row_idx, "Quality Decision"] = q_in
                        df_appeals.loc[row_idx, "Direct Manager"] = m_in
                        df_appeals.to_csv(appeals_file, index=False); st.success("Updated!"); st.rerun()
        else:
            t1, t2 = st.tabs(["📤 Submit Objection", "📜 History"])
            with t1:
                with st.form("ob_form"):
                    fd = st.date_input("Incident Date")
                    ft = st.text_input("Ticket #")
                    ftb = st.selectbox("Tab", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Alwatani-Services", "BRIDGES", "Wireless", "IRQNBN", "ITPC", "MERTO", "NAS's", "Server Room", "Power", "AL-Watani Power"])
                    fdt = st.text_area("Details")
                    if st.form_submit_button("Submit"):
                        now_b = datetime.utcnow() + timedelta(hours=3)
                        if now_b.day >= 18 and fd.day <= 15:
                            st.error("❌ Submission period closed for 1st half.")
                        elif not ft or not fdt: st.error("❌ Fill all fields.")
                        else:
                            new_r = {
                                "Employee": st.session_state.get("name"), 
                                "Date": str(fd), 
                                "Ticket Number": ft, 
                                "Tab": ftb, 
                                "Details": fdt, 
                                "Quality Decision": "Pending Review", 
                                "Direct Manager": "Pending Review",
                                "Objection Creation Date": b_full_now # التقاط الوقت الحالي أوتوماتيكياً
                            }
                            df_appeals = pd.concat([df_appeals, pd.DataFrame([new_r])], ignore_index=True)
                            df_appeals.to_csv(appeals_file, index=False); st.success("Submitted!"); st.balloons()
            with t2: st.table(df_appeals[df_appeals['Employee'] == st.session_state.get("name")])

    if username == 'jsafaa':
        with staff_tab:
            st.subheader("👥 User Management")
            # أزرار الإضافة والمسح وتغيير الباسورد تبقى كما هي لضمان عملها
            with st.expander("Add New Employee"):
                nu = st.text_input("Username").lower().strip()
                nn = st.text_input("Full Name")
                if st.button("Add"):
                    if nu and nu not in users_df['username'].values:
                        users_df = pd.concat([users_df, pd.DataFrame([{"username": nu, "password": "123", "name": nn, "role": "Employee"}])], ignore_index=True)
                        users_df.to_csv(users_file, index=False); st.success("Added!")

elif st.session_state.get("authentication_status") == False: st.error("Wrong Info")
else: st.info("Welcome to NMC Portal.")