import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 🚀 Page Configuration ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- 🎨 Custom CSS ---
st.markdown("""
    <style>
        .main-title { font-size:40px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        div[data-testid="stExpander"] { background-color: rgba(240, 242, 246, 0.5); border-radius: 10px; border: 1px solid #d1d5db; }
        .user-name-sidebar { color: #4CAF50; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
        .stat-card { padding: 20px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 10px; border-left: 6px solid; }
        .stat-label { font-size: 16px; font-weight: bold; margin-bottom: 5px; }
        .stat-value { font-size: 32px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- ⚡ Data & Session Persistence ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

if 'df_appeals' not in st.session_state:
    if not os.path.exists(appeals_file):
        pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "KPI", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date", "Admin Notes"]).to_csv(appeals_file, index=False)
    st.session_state.df_appeals = pd.read_csv(appeals_file)

if 'users_df' not in st.session_state:
    if not os.path.exists(users_file):
        initial_users = ["ahatim", "mkhalid", "hfalah", "hmuayyad", "alimad", "rriyad", "hjabbar", "hmuhammada", "arubayi", "aadil", "ayasin", "fahmad", "hakali", "musadiq", "itsattar", "amusadaq", "aanbari", "afahad", "rthair", "omsubhi", "rwahab", "mlayth", "yasadi", "yriyad", "abfaysal", "hasanhadi", "hamuhsin", "aybasheer", "marmahmud", "abisameer", "jsafaa", "muhahamid", "murqasim", "moayad", "dadnan", "abiabbas", "qriyad", "tmustafa", "sbahnan", "admuhammad", "amohammad", "shzuhayr"]
        user_data = [{"username": u, "password": ('admin123' if u == 'jsafaa' else ('manager123' if u == 'ahatim' else '123')), "name": u.upper(), "role": ('Head Of Section' if u == 'ahatim' else ('
