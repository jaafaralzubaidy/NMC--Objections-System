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

appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

# --- 2. إدارة البيانات ---
def get_users_df():
    # القائمة الكاملة للموظفين
    initial_users = [
        "ahatim", "mkhalid", "hfalah", "hmuayyad", "alimad", "rriyad", "hjabbar", 
        "hmuhammada", "arubayi", "aadil", "ayasin", "fahmad", "hakali", "musadiq", 
        "itsattar", "amusadaq", "aanbari", "afahad", "rthair", "omsubhi", "rwahab", 
        "mlayth", "yasadi", "yriyad", "abfaysal", "hasanhadi", "hamuhsin", "aybasheer", 
        "marmahmud", "abisameer", "jsafaa", "muhahamid", "murqasim", "moayad", 
        "dadnan", "abiabbas", "qriyad", "tmustafa", "sbahnan", "admuhammad", 
        "amohammad", "shzuhayr", "farook"
    ]

    if os.path.exists(users_file):
        df = pd.read_csv(users_file)
        # دمج أي موظف ناقص من القائمة
        existing = df['username'].tolist()
        new_users = []
        for u in initial_users:
            if u not in existing:
                p = 'admin123' if u == 'jsafaa' else ('manager123' if u in ['ahatim', 'farook'] else '123')
                role = 'Head Of Section' if u == 'ahatim' else ('Team Leader' if u == 'farook' else ('Quality Engineer' if u == 'jsafaa' else 'Employee'))
                new_users.append({"username": u, "password": p, "name": u.upper(), "role": role, "Force_Change": True})
        if new_users:
            df = pd.concat([df, pd.DataFrame(new_users)], ignore_index=True)
            df.to_csv(users_file, index=False)
        return df
    else:
        user_data = []
        for u in initial_users:
            p = 'admin123' if u == 'jsafaa' else ('manager123' if u in ['ahatim', 'farook'] else '123')
            role = 'Head Of Section' if u == 'ahatim' else ('Team Leader' if u == 'farook' else ('Quality Engineer' if u == 'jsafaa' else 'Employee'))
            user_data.append({"username": u, "password": p, "name": u.upper(), "role": role, "Force_Change": True})
        df = pd.DataFrame(user_data)
        df.to_csv(users_file, index=False)
        return df

if 'u_df' not in st.session_state:
    st.session_state.u_df = get_users_df()

if 'main_df' not in st.session_state:
    if os.path.exists(appeals_file):
        st.session_state.main_df = pd.read_csv(appeals_file)
    else:
        st.session_state.main_df = pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "KPI", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date"])

# --- 3. نظام المصادقة ---
credentials = {'usernames': {}}
for _, row in st.session_state.u_df.iterrows():
    credentials['usernames'][str(row['username'])] = {
        'name': str(row['name']),
        'password': str(row['password'])
    }

# إنشاء كائن المصادقة
authenticator = stauth.Authenticate(credentials, 'nmc_portal', 'auth_key', cookie_expiry_days=30)

# --- 4. واجهة الدخول (تم إصلاح الخطأ هنا) ---
