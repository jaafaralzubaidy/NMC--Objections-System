import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime
import requests

# --- 1. إعدادات الصفحة والواجهة ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# دالة لجلب الطقس والوقت وتغيير الألوان تلقائياً
def get_dynamic_ui():
    try:
        # جلب درجة حرارة بغداد
        res = requests.get("https://wttr.in/Baghdad?format=%t", timeout=5)
        temp = res.text if res.status_code == 200 else "N/A"
    except:
        temp = "N/A"
    
    hour = datetime.now().hour
    
    # اختيار الثيم حسب الوقت (صباح، ظهر، عصر، ليل)
    if 5 <= hour < 12:
        bg, icon, msg = "linear-gradient(to right, #FFDEE9, #B5FFFC)", "🌅", "Good Morning"
    elif 12 <= hour < 17:
        bg, icon, msg = "linear-gradient(to right, #00B4DB, #0083B0)", "☀️", "Good Afternoon"
    elif 17 <= hour < 20:
        bg, icon, msg = "linear-gradient(to right, #da1b60, #ff8a00)", "🌇", "Good Evening"
    else:
        bg, icon, msg = "linear-gradient(to bottom, #0f2027, #203a43, #2c5364)", "🌙", "Good Night"
        
    return temp, bg, icon, msg

temp_val, bg_style, sky_icon, welcome_msg = get_dynamic_ui()

# تطبيق التصميم الجمالي CSS
st.markdown(f"""
    <style>
    .stApp {{ background: {bg_style}; background-attachment: fixed; }}
    .header-box {{
        background-color: rgba(255, 255, 255, 0.2);
        padding: 25px; border-radius: 15px; text-align: center;
        backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.3);
        margin-bottom: 25px; color: white;
    }}
    .main-title {{ font-size:42px !important; font-weight: bold; text-shadow: 2px 2px 8px #000; }}
    </style>
    <div class="header-box">
        <div class="main-title">{sky_icon} NMC OBJECTIONS SYSTEM</div>
        <div style="font-size:18px; text-shadow: 1px 1px 3px #000;">
            📅 {datetime.now().strftime('%Y-%m-%d')} | 🕒 {datetime.now().strftime('%H:%M')} | 🌡️ Baghdad: {temp_val}
        </div>
        <div style="font-weight:bold; margin-top:10px; font-size:20px;">{welcome_msg}</div>
    </div>
""", unsafe_allow_html=True)

# --- 2. إدارة ملفات البيانات ---
users_file = "users_list.csv"
appeals_file = "database_appeals.csv"

# إنشاء قائمة الموظفين الأولية إذا كان الملف غير موجود
if not os.path.exists(users_file):
    initial_list = [
        "ahatim", "mkhalid", "hfalah", "hmuayyad", "alimad", "rriyad", "hjabbar", 
        "hmuhammada", "arubayi", "aadil", "ayasin", "fahmad", "hakali", "musadiq", 
        "itsattar", "amusadaq", "aanbari", "afahad", "rthair", "omsubhi", "rwahab", 
        "mlayth", "yasadi", "yriyad", "abfaysal", "hasanhadi", "hamuhsin", "aybasheer", 
        "marmahmud", "abisameer", "jsafaa", "muhahamid", "murqasim", "moayad", 
        "dadnan", "abiabbas", "qriyad", "tmustafa", "sbahnan", "admuhammad", 
        "amohammad", "shzuhayr"
    ]
    data = []
    for u in initial_list:
        p = 'admin123' if u == 'jsafaa' else ('manager123' if u == 'ahatim' else '123')
        r = 'Quality Engineer' if u == 'jsafaa' else ('Head Of Section' if u == 'ahatim' else 'Employee')
        data.append({"username": u, "password": p, "name": u.upper(), "role": r})
    pd.DataFrame(data).to_csv(users_file, index=False)

users_df = pd.read_csv(users_file)

# --- 3. نظام تسجيل الدخول ---
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][row['username']] = {
        'name': f"{row['name']} ({row['role']})",
        'password': str(row['password'])
    }

authenticator = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30)

try:
    authenticator.login()
except:
    try: authenticator.login('main')
    except: authenticator.login('Login', 'main')

if st.session_state.get("authentication_status"):
    username = st.session_state.get("username")
    authenticator.logout('Logout', 'sidebar')
    
    if not os.path.exists(appeals_file):
        pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager"]).to_csv(appeals_file, index=False)
    df_appeals = pd.read_csv(appeals_file)

    # --- 4. واجهة المستخدم حسب الصلاحية ---
    if username == 'jsafaa':
        main_tab, staff_tab = st.tabs(["📊 Operations Portal", "👥 Admin: Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        # واجهة الكوالتي والمدير
        if username in ['jsafaa', 'ahatim']:
            st.subheader("🛠 Control Panel")
            st.dataframe(df_appeals, use_container_width=True)
            with st.expander("Update Status/Decisions"):
                if not df_appeals.empty:
                    row_idx = st.number_input("Row ID", 0, len(df_appeals)-1, 0)
                    c1, c2 = st.columns(2)
                    with c1:
                        q_txt = st.text_area("Quality Decision", value=df_appeals.loc[row_idx, "Quality Decision"], disabled=(username == 'ahatim'))
                    with c2:
                        m_txt = st.text_area("Head Of Section Decision", value=df_appeals.loc[row_idx, "Direct Manager"], disabled=(username == 'jsafaa'))
                    if st.button("Save Changes"):
                        df_appeals.loc[row_idx, "Quality Decision"] = q_txt
                        df_appeals.loc[row_idx, "Direct Manager"] = m_txt
                        df_appeals.to_csv(appeals_file, index=False); st.success("Updated!"); st.rerun()
        
        # واجهة الموظف
        else:
            t1, t2 = st.tabs(["📤 New Objection", "📜 My Record"])
            with t1:
                with st.form("ob_form"):
                    fd = st.date_input("Date"); ft = st.text_input("Ticket #")
                    ftb = st.selectbox("Tab", ["SWITCH STATE", "Baghdad Rings", "MPLS", "EARTHLINK SERVICES", "Alwatani-Services", "BRIDGES", "Wireless", "IRQNBN", "ITPC", "MERTO", "NAS's", "Server Room", "Power", "AL-Watani Power"])
                    fdt = st.text_area("Details")
                    if st.form_submit_button("Submit"):
                        if datetime.now().day >= 18 and fd.day <= 15:
                            st.error("❌ Time-Lock: Objection period for 1st half is closed.")
                        elif not ft or not fdt: st.error("❌ Fill all fields.")
                        else:
                            new_r = {"Employee": st.session_state.get("name"), "Date": str(fd), "Ticket Number": ft, "Tab": ftb, "Details": fdt, "Quality Decision": "Pending", "Direct Manager": "Pending"}
                            df_appeals = pd.concat([df_appeals, pd.DataFrame([new_r])], ignore_index=True)
                            df_appeals.to_csv(appeals_file, index=False); st.success("Done!"); st.balloons()
            with t2: st.table(df_appeals[df_appeals['Employee'] == st.session_state.get("name")])

    # --- 5. لوحة تحكم الموظفين (للآدمن فقط) ---
    if username == 'jsafaa':
        with staff_tab:
            st.subheader("👥 User Management")
            with st.expander("Add New Employee"):
                nu = st.text_input("New Username").lower().strip()
                nn = st.text_input("Name")
                if st.button("Add"):
                    if nu and nu not in users_df['username'].values:
                        users_df = pd.concat([users_df, pd.DataFrame([{"username": nu, "password": "123", "name": nn, "role": "Employee"}])], ignore_index=True)
                        users_df.to_csv(users_file, index=False); st.success("Added! Refresh to apply.")
            with st.expander("Change Password"):
                target = st.selectbox("Select User", users_df['username'].values)
                new_p = st.text_input("New Pass", type="password")
                if st.button("Update"):
                    users_df.loc[users_df['username'] == target, 'password'] = new_p
                    users_df.to_csv(users_file, index=False); st.success("Updated!")
            with st.expander("Remove User"):
                du = st.selectbox("User to delete", [u for u in users_df['username'].values if u not in ['jsafaa', 'ahatim']])
                if st.button("Confirm Delete"):
                    users_df = users_df[users_df['username'] != du]
                    users_df.to_csv(users_file, index=False); st.warning("Deleted."); st.rerun()

elif st.session_state.get("authentication_status") == False: st.error("Login Error")
else: st.info("Please login with your NMC credentials.")