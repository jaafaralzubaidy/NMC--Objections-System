import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

st.markdown("""
    <style>
        .main-title { font-size:35px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        .user-name-sidebar { color: #4CAF50; font-weight: bold; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# أسماء الملفات الثابتة
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

# --- 2. دوال إدارة البيانات (الذكية) ---
def load_users():
    # إذا كان الملف موجوداً، لا ننشئ قائمة جديدة بل نستخدم الموجودة لضمان بقاء باسووردات الموظفين
    if os.path.exists(users_file):
        df = pd.read_csv(users_file)
        # التأكد من وجود الأعمدة الأساسية
        if 'Force_Change' not in df.columns:
            df['Force_Change'] = False
        return df
    else:
        # قائمة الموظفين الكاملة (تُستخدم فقط في المرة الأولى)
        initial_users = [
            "ahatim", "mkhalid", "hfalah", "hmuayyad", "alimad", "rriyad", "hjabbar", 
            "hmuhammada", "arubayi", "aadil", "ayasin", "fahmad", "hakali", "musadiq", 
            "itsattar", "amusadaq", "aanbari", "afahad", "rthair", "omsubhi", "rwahab", 
            "mlayth", "yasadi", "yriyad", "abfaysal", "hasanhadi", "hamuhsin", "aybasheer", 
            "marmahmud", "abisameer", "jsafaa", "muhahamid", "murqasim", "moayad", 
            "dadnan", "abiabbas", "qriyad", "tmustafa", "sbahnan", "admuhammad", 
            "amohammad", "shzuhayr", "farook"
        ]
        user_data = []
        for u in initial_users:
            if u == 'jsafaa': p, role = 'admin123', 'Quality Engineer'
            elif u == 'ahatim': p, role = 'manager123', 'Head Of Section'
            elif u == 'farook': p, role = 'manager123', 'Team Leader'
            else: p, role = '123', 'Employee'
            
            user_data.append({"username": u, "password": p, "name": u.upper(), "role": role, "Force_Change": True})
        
        df = pd.DataFrame(user_data)
        df.to_csv(users_file, index=False)
        return df

# تحميل البيانات في الذاكرة
if 'u_df' not in st.session_state:
    st.session_state.u_df = load_users()

if 'main_df' not in st.session_state:
    if os.path.exists(appeals_file):
        st.session_state.main_df = pd.read_csv(appeals_file)
    else:
        cols = ["Employee", "Date", "Ticket Number", "Tab", "KPI", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date"]
        st.session_state.main_df = pd.DataFrame(columns=cols)

# --- 3. نظام المصادقة ---
# تحديث بيانات الدخول من الملف الحالي
users_df = st.session_state.u_df
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][str(row['username'])] = {
        'name': f"{row['name']} ({row['role']})",
        'password': str(row['password'])
    }

# حفظ كائن Authenticate لمنع إعادة التشغيل غير الضرورية
if 'auth_obj' not in st.session_state:
    st.session_state.auth_obj = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30)

authenticator = st.session_state.auth_obj

# --- 4. واجهة المستخدم ---
