import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta
import requests

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="NMC Portal", layout="wide")

# دالة ذكية لجلب الطقس مع تخزين مؤقت (Cache) لمدة ساعة لتقليل الثقل
@st.cache_data(ttl=3600)
def get_cached_temp():
    try:
        res = requests.get("https://wttr.in/Baghdad?format=%t", timeout=2)
        return res.text.strip() if res.status_code == 200 else "N/A"
    except:
        return "N/A"

def get_baghdad_ui():
    now_baghdad = datetime.utcnow() + timedelta(hours=3)
    hour = now_baghdad.hour
    time_str = now_baghdad.strftime('%I:%M %p')
    date_str = now_baghdad.strftime('%Y-%m-%d')
    full_ts = now_baghdad.strftime('%Y-%m-%d %H:%M:%S')
    
    # جلب الحرارة المخزنة (سريعة جداً)
    temp = get_cached_temp()
    
    if 5 <= hour < 7:
        bg, icon, msg = "#4facfe", "🌅", "Good Early Morning"
    elif 7 <= hour < 12:
        bg, icon, msg = "#f8b500", "🌞", "Good Morning"
    elif 12 <= hour < 17:
        bg, icon, msg = "#2980b9", "☀️", "Good Afternoon"
    elif 17 <= hour < 20:
        bg, icon, msg = "#f83600", "🌆", "Good Evening"
    else:
        bg, icon, msg = "#2c3e50", "🌙", "Good Night"
        
    return temp, bg, icon, msg, time_str, date_str, full_ts

temp_val, bg_color, sky_icon, welcome_msg, b_time, b_date, b_full_now = get_baghdad_ui()

# تصميم الواجهة (تم تبسيطه لزيادة السرعة)
st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; }}
    .header-box {{
        background-color: rgba(0, 0, 0, 0.6);
        padding: 20px; border-radius: 15px; text-align: center;
        color: white; margin-bottom: 20px;
        border: 1px solid rgba(255,255,255,0.1);
    }}
    </style>
    <div class="header-box">
        <h1 style='margin:0;'>{sky_icon} NMC OBJECTIONS</h1>
        <p style='margin:5px;'>📅 {b_date} | 🕒 {b_time} | 🌡️ Temp: {temp_val}</p>
        <div style='color:#FFD700; font-weight:bold;'>{welcome_msg}</div>
    </div>
""", unsafe_allow_html=True)

# --- 2. إدارة البيانات ---
u_file, a_file = "users_list.csv", "database_appeals.csv"

# تحميل اليوزرات
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

    # --- 3. الواجهات ---
    if user == 'jsafaa':
        t_main, t_staff = st.tabs(["📊 Portal", "👥 Management"])
    else:
        t_main = st.container()

    with t_main:
        if user in ['jsafaa', 'ahatim']:
            st.dataframe(df, use_container_width=True)
            with st.expander("Update Decisions"):
                if not df.empty:
                    idx = st.number_input("Row ID", 0, len(df)-1, 0)
                    c1, c2 = st.columns(2)
                    with c1: q = st.text_area("Quality", df.loc[idx,"Quality Decision"], disabled=(user=='ahatim'))
                    with c2: m = st.text_area("Manager", df.loc[idx,"Direct Manager"], disabled=(user=='jsafaa'))
                    if st.button("Save"):
                        df.loc[idx,"Quality Decision"], df.loc[idx,"Direct Manager"] = q, m
                        df.to_csv(a_file, index=False); st.success("Saved!"); st.rerun()
        else:
            with st.form("ob_f"):
                f_d = st.date_input("Date"); f_t = st.text_input("Ticket#")
                f_tb = st.selectbox("Tab", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Alwatani-Services", "BRIDGES", "Wireless", "IRQNBN", "ITPC", "MERTO", "NAS's", "Server Room", "Power", "AL-Watani Power"])
                f_dt = st.text_area("Details")
                if st.form_submit_button("Submit"):
                    new_r = {"Employee":st.session_state.get("name"), "Date":str(f_d), "Ticket Number":f_t, "Tab":f_tb, "Details":f_dt, "Quality Decision":"Pending", "Direct Manager":"Pending", "Objection Creation Date":b_full_now}
                    df = pd.concat([df, pd.DataFrame([new_r])], ignore_index=True)
                    df.to_csv(a_file, index=False); st.success("Sent!"); st.balloons()
            st.subheader("My History")
            st.table(df[df['Employee'] == st.session_state.get("name")])

    if user == 'jsafaa':
        with t_staff:
            with st.expander("Add Staff"):
                nu, nn = st.text_input("User"), st.text_input("Full Name")
                if st.button("Add"):
                    u_df = pd.concat([u_df, pd.DataFrame([{"username":nu,"password":"123","name":nn,"role":"Employee"}])], ignore_index=True)
                    u_df.to_csv(u_file, index=False); st.success("Added")

elif st.session_state.get("authentication_status") == False: st.error("Wrong info")
else: st.info("Login please")