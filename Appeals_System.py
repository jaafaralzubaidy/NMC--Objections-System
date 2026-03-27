import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta
from io import BytesIO

# --- 🚀 Page Configuration ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide", page_icon="🛰️")

# --- Custom CSS for Professional Look ---
st.markdown("""
    <style>
        .main-title { font-size:35px !important; color: #1E3A8A; text-align: center; font-weight: bold; margin-bottom: 20px; }
        .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef; }
        .notification-banner {
            padding: 15px;
            background-color: #ffeeb2;
            border-left: 6px solid #ffcc00;
            border-radius: 5px;
            color: #856404;
            font-weight: bold;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# --- File Names ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

# --- 🛠️ Helper Functions ---
def to_excel(df):
    output = BytesIO()
    # نحتاج مكتبة XlsxWriter لتصدير الملف بشكل صحيح
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='NMC_Objections')
    return output.getvalue()

def get_all_data():
    if 'main_df' not in st.session_state:
        if not os.path.exists(appeals_file):
            pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date"]).to_csv(appeals_file, index=False)
        st.session_state.main_df = pd.read_csv(appeals_file)
    return st.session_state.main_df

def get_users_df():
    if 'u_df' not in st.session_state:
        if not os.path.exists(users_file):
            # قائمة اليوزرات الافتراضية
            initial_users = ["ahatim", "jsafaa", "mkhalid", "hfalah", "hmuayyad", "alimad", "rriyad", "hjabbar", "hmuhammada", "arubayi", "aadil", "ayasin", "fahmad", "hakali", "musadiq", "itsattar", "amusadaq", "aanbari", "afahad", "rthair", "omsubhi", "rwahab", "mlayth", "yasadi", "yriyad", "abfaysal", "hasanhadi", "hamuhsin", "aybasheer", "marmahmud", "abisameer", "muhahamid", "murqasim", "moayad", "dadnan", "abiabbas", "qriyad", "tmustafa", "sbahnan", "admuhammad", "amohammad", "shzuhayr"]
            user_data = []
            for u in initial_users:
                p = 'admin123' if u == 'jsafaa' else ('manager123' if u == 'ahatim' else '123')
                role = 'Head Of Section' if u == 'ahatim' else ('Quality Engineer' if u == 'jsafaa' else 'Employee')
                user_data.append({"username": u.lower(), "password": p, "name": u.upper(), "role": role})
            pd.DataFrame(user_data).to_csv(users_file, index=False)
        st.session_state.u_df = pd.read_csv(users_file)
    return st.session_state.u_df

# Load Initial Data
users_df = get_users_df()
df_appeals = get_all_data()

# --- Authenticator Setup ---
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][row['username']] = {'name': f"{row['name']} ({row['role']})", 'password': str(row['password'])}

if 'auth_obj' not in st.session_state:
    st.session_state.auth_obj = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30)

authenticator = st.session_state.auth_obj

# --- Main Interface ---
st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM PRO</div>', unsafe_allow_html=True)

try:
    authenticator.login()
except:
    st.info("Please login to proceed.")

if st.session_state.get("authentication_status"):
    username = st.session_state.get("username").lower() # توحيد اليوزر سمول لتر
    
    # Sidebar Profile
    display_name = credentials['usernames'][username]['name']
    st.sidebar.markdown(f"### 👤 {display_name}")
    authenticator.logout('Logout', 'sidebar')
    
    # --- 📊 Dashboard for Management (Jassim & Hatim) ---
    if username in ['jsafaa', 'ahatim']:
        st.subheader("📊 Management Overview")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total", len(df_appeals))
        m2.metric("Pending Quality", len(df_appeals[df_appeals['Quality Decision'] == 'Pending']))
        m3.metric("Pending Manager", len(df_appeals[df_appeals['Direct Manager'] == 'Pending']))
        
        # زر تصدير التقرير
        excel_data = to_excel(df_appeals)
