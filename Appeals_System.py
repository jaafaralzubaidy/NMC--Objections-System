import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime, timedelta

# --- 🚀 Page Configuration ---
st.set_page_config(page_title="NMC Objections Portal", layout="wide")

# --- Custom CSS ---
st.markdown("""
    <style>
        .main-title { font-size:40px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
        div[data-testid="stExpander"] { 
            background-color: rgba(240, 242, 246, 0.5); 
            border-radius: 10px; border: 1px solid #d1d5db;
        }
        .stat-card {
            padding: 20px; border-radius: 12px; text-align: center;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 10px;
        }
        .stat-label { font-size: 18px; font-weight: bold; margin-bottom: 5px; color: #1A1A1A !important; }
        .stat-value { font-size: 36px; font-weight: bold; color: #000000 !important; }
    </style>
""", unsafe_allow_html=True)

# --- File Names ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

# --- 🛠️ Data Loading ---
def get_all_data():
    if not os.path.exists(appeals_file):
        pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date", "Admin Comment"]).to_csv(appeals_file, index=False)
    df = pd.read_csv(appeals_file)
    if "Admin Comment" not in df.columns: 
        df["Admin Comment"] = ""
        df.to_csv(appeals_file, index=False)
    return df

def get_users_df():
    if not os.path.exists(users_file):
        initial_users = [{"username": "jsafaa", "password": "123", "name": "JASFAA", "role": "Quality Engineer", "first_login": True},
                        {"username": "ahatim", "password": "123", "name": "AHATIM", "role": "Head Of Section", "first_login": True}]
        pd.DataFrame(initial_users).to_csv(users_file, index=False)
    return pd.read_csv(users_file)

users_df = get_users_df()
df_appeals = get_all_data()

# --- Authenticator ---
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][row['username']] = {'name': row['name'], 'password': str(row['password'])}

authenticator = stauth.Authenticate(credentials, 'nmc_cookie', 'nmc_auth_key', cookie_expiry_days=30)

# --- App ---
st.markdown('<div class="main-title">🛰️ NMC OBJECTIONS SYSTEM</div><hr>', unsafe_allow_html=True)

name, authentication_status, username = authenticator.login('main')

if authentication_status:
    user_row = users_df[users_df['username'] == username].iloc[0]

    # --- Forced Password Change ---
    if user_row['first_login']:
        st.warning("⚠️ SECURITY: Change your password first.")
        with st.form("pwd_change"):
            new_p = st.text_input("New Password", type="password")
            if st.form_submit_button("Update"):
                users_df.loc[users_df['username'] == username, ['password', 'first_login']] = [new_p, False]
                users_df.to_csv(users_file, index=False)
                st.success("Updated! Please refresh."); st.rerun()
        st.stop()

    st.sidebar.write(f"Welcome {name}")
    authenticator.logout('Logout', 'sidebar')

    # --- Admin/Manager Stats ---
    if username in ['jsafaa', 'ahatim']:
        pending = len(df_appeals[(df_appeals['Quality Decision'] == 'Pending') | (df_appeals['Direct Manager'] == 'Pending')])
        decided = len(df_appeals[((df_appeals['Quality Decision'] == 'Approved') & (df_appeals['Direct Manager'] == 'Approved')) | 
                                 ((df_appeals['Quality Decision'] == 'Rejected') & (df_appeals['Direct Manager'] == 'Rejected'))])
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="stat-card" style="background-color:#e3f2fd;"><div class="stat-label">Total</div><div class="stat-value">{len(df_appeals)}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="background-color:#fff3e0;"><div class="stat-label">Pending</div><div class="stat-value">{pending}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card" style="background-color:#e8f5e9;"><div class="stat-label">Fully Decided</div><div class="stat-value">{decided}</div></div>', unsafe_allow_html=True)

    # --- Tabs ---
    if username == 'jsafaa':
        main_tab, admin_tab = st.tabs(["📊 Main System", "👥 Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        if username in ['jsafaa', 'ahatim']:
            st.dataframe(df_appeals, use_container_width=True)
            with st.expander("Update Decision"):
                idx = st.number_input("Row ID", 0, len(df_appeals)-1 if not df_appeals.empty else 0, 0)
                q_dec = st.selectbox("Quality", ["Pending", "Approved", "Rejected"], index=["Pending", "Approved", "Rejected"].index(df_appeals.loc[idx, "Quality Decision"]) if not df_appeals.empty else 0, disabled=(username=='ahatim'))
                m_dec = st.selectbox("Manager", ["Pending", "Approved", "Rejected"], index=["Pending", "Approved", "Rejected"].index(df_appeals.loc[idx, "Direct Manager"]) if not df_appeals.empty else 0, disabled=(username=='jsafaa'))
                note = st.text_area("Note", value=str(df_appeals.loc[idx, "Admin Comment"]) if not df_appeals.empty else "")
                if st.button("Save"):
                    df_appeals.loc[idx, ["Quality Decision", "Direct Manager", "Admin Comment"]] = [q_dec, m_dec, note]
                    df_appeals.to_csv(appeals_file, index=False)
                    st.success("Saved!"); st.rerun()
        else:
            t1, t2 = st.tabs(["📤 Submit", "📜 History"])
            with t1:
                with st.form("submit_form", clear_on_submit=True):
                    ticket = st.text_input("Ticket #")
                    details = st.text_area("Details")
                    if st.form_submit_button("Send"):
                        new_data = {"Employee": name, "Date": str(datetime.now().date()), "Ticket Number": ticket, "Tab": "N/A", "Details": details, "Quality Decision": "Pending", "Direct Manager": "Pending", "Objection Issue Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Admin Comment": ""}
                        df_appeals = pd.concat([df_appeals, pd.DataFrame([new_data])], ignore_index=True)
                        df_appeals.to_csv(appeals_file, index=False)
                        st.success("Submitted!"); st.rerun()
            with t2:
                # 🔥 الحل هنا: الفلترة باستخدام الاسم المسجل في الـ Session
                user_history = df_appeals[df_appeals['Employee'] == name]
                st.write(f"Found {len(user_history)} records for {name}") # للتأكد من القيمة
                st.dataframe(user_history, use_container_width=True)

    if username == 'jsafaa':
        with admin_tab:
            st.subheader("Manage Staff")
            # --- إضافة موظف ---
            with st.expander("Add User"):
                u = st.text_input("Username").lower()
                n = st.text_input("Full Name")
                if st.button("Add"):
                    new_u = pd.DataFrame([{"username": u, "password": "123", "name": n, "role": "Employee", "first_login": True}])
                    pd.concat([users_df, new_u], ignore_index=True).to_csv(users_file, index=False)
                    st.success("Added!"); st.rerun()
            # --- حذف موظف ---
            with st.expander("Delete User"):
                target = st.selectbox("Select User", users_df['username'].values)
                if st.button("Delete"):
                    users_df[users_df['username'] != target].to_csv(users_file, index=False)
                    st.success("Deleted!"); st.rerun()

elif authentication_status == False: st.error("Wrong Login")
