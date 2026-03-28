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
        div[data-testid="stExpander"] { background-color: rgba(240, 242, 246, 0.5); border-radius: 10px; border: 1px solid #d1d5db; }
        .stat-card { padding: 20px; border-radius: 12px; text-align: center; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); margin-bottom: 10px; }
        .stat-label { font-size: 18px; font-weight: bold; margin-bottom: 5px; color: #1A1A1A !important; }
        .stat-value { font-size: 36px; font-weight: bold; color: #000000 !important; }
    </style>
""", unsafe_allow_html=True)

# --- File Names ---
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

# --- 🛠️ Data Loading Functions ---
def load_files():
    if not os.path.exists(appeals_file):
        pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager", "Objection Issue Date", "Admin Comment"]).to_csv(appeals_file, index=False)
    if not os.path.exists(users_file):
        initial_users = [
            {"username": "jsafaa", "password": "123", "name": "JASFAA", "role": "Quality Engineer", "first_login": True},
            {"username": "ahatim", "password": "123", "name": "AHATIM", "role": "Head Of Section", "first_login": True}
        ]
        pd.DataFrame(initial_users).to_csv(users_file, index=False)
    return pd.read_csv(appeals_file), pd.read_csv(users_file)

df_appeals, users_df = load_files()

# --- 🔐 Authenticator (Fixed for new version) ---
credentials = {'usernames': {}}
for _, row in users_df.iterrows():
    credentials['usernames'][row['username']] = {'name': row['name'], 'password': str(row['password'])}

authenticator = stauth.Authenticate(credentials, 'nmc_cookie', 'auth_key', cookie_expiry_days=30)

# --- Login Logic ---
# التحديث الجديد يطلب استدعاء login بدون متغيرات توزيع مباشرة أحياناً
authenticator.login('main')

if st.session_state["authentication_status"]:
    username = st.session_state["username"]
    full_name = st.session_state["name"]
    
    user_row = users_df[users_df['username'] == username].iloc[0]

    # --- Forced Password Change ---
    if user_row['first_login']:
        st.warning("🔒 First Login: Change your password.")
        with st.form("pwd_change"):
            new_p = st.text_input("New Password", type="password")
            if st.form_submit_button("Update"):
                users_df.loc[users_df['username'] == username, ['password', 'first_login']] = [new_p, False]
                users_df.to_csv(users_file, index=False)
                st.success("Updated! Refreshing..."); st.rerun()
        st.stop()

    st.sidebar.markdown(f"### Welcome {full_name}")
    authenticator.logout('Logout', 'sidebar')

    # --- 📊 Stats Overview ---
    if username in ['jsafaa', 'ahatim']:
        pending = len(df_appeals[(df_appeals['Quality Decision'] == 'Pending') | (df_appeals['Direct Manager'] == 'Pending')])
        # Fully Decided = (Approved/Approved) OR (Rejected/Rejected)
        decided = len(df_appeals[
            ((df_appeals['Quality Decision'] == 'Approved') & (df_appeals['Direct Manager'] == 'Approved')) | 
            ((df_appeals['Quality Decision'] == 'Rejected') & (df_appeals['Direct Manager'] == 'Rejected'))
        ])
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="stat-card" style="background-color:#e3f2fd;"><div class="stat-label">Total Objections</div><div class="stat-value">{len(df_appeals)}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="background-color:#fff3e0;"><div class="stat-label">Pending Review</div><div class="stat-value">{pending}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card" style="background-color:#e8f5e9;"><div class="stat-label">Fully Decided</div><div class="stat-value">{decided}</div></div>', unsafe_allow_html=True)

    # --- Tabs Layout ---
    if username == 'jsafaa':
        main_tab, admin_tab = st.tabs(["📊 Main System", "👥 Manage Staff"])
    else:
        main_tab = st.container()

    with main_tab:
        if username in ['jsafaa', 'ahatim']:
            st.subheader("🛠 Management Control Panel")
            st.dataframe(df_appeals, use_container_width=True)
            with st.expander("Update Decisions & Notes"):
                if not df_appeals.empty:
                    row_idx = st.number_input("Row Index", 0, len(df_appeals)-1, 0)
                    col1, col2, col3 = st.columns(3)
                    opts = ["Pending", "Approved", "Rejected"]
                    with col1:
                        q_val = df_appeals.loc[row_idx, "Quality Decision"]
                        new_q = st.selectbox("Quality", opts, index=opts.index(q_val) if q_val in opts else 0, disabled=(username=='ahatim'))
                    with col2:
                        m_val = df_appeals.loc[row_idx, "Direct Manager"]
                        new_m = st.selectbox("Manager", opts, index=opts.index(m_val) if m_val in opts else 0, disabled=(username=='jsafaa'))
                    with col3:
                        new_note = st.text_area("Notes", value=str(df_appeals.loc[row_idx, "Admin Comment"]))
                    
                    if st.button("Save Changes"):
                        df_appeals.loc[row_idx, ["Quality Decision", "Direct Manager", "Admin Comment"]] = [new_q, new_m, new_note]
                        df_appeals.to_csv(appeals_file, index=False)
                        st.success("Updated!"); st.rerun()
        else:
            t1, t2 = st.tabs(["📤 Submit Objection", "📜 History"])
            with t1:
                with st.form("sub_form", clear_on_submit=True):
                    t_num = st.text_input("Ticket Number")
                    t_tab = st.selectbox("Dept", ["SWITCH STATE", "MPLS", "Wireless", "Power", "ITPC"])
                    t_det = st.text_area("Details")
                    if st.form_submit_button("Submit"):
                        # خزن الاسم بالضبط كما هو في الـ session لضمان ظهوره بالهستوري
                        new_row = {"Employee": full_name, "Date": str(datetime.now().date()), "Ticket Number": t_num, "Tab": t_tab, "Details": t_det, "Quality Decision": "Pending", "Direct Manager": "Pending", "Objection Issue Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Admin Comment": ""}
                        df_temp = pd.concat([df_appeals, pd.DataFrame([new_row])], ignore_index=True)
                        df_temp.to_csv(appeals_file, index=False)
                        st.success("Submitted!"); st.rerun()
            with t2:
                # الفلترة الآن تعتمد على full_name المأخوذ من الـ session
                user_history = df_appeals[df_appeals['Employee'] == full_name]
                st.write(f"Showing records for: **{full_name}**")
                st.dataframe(user_history, use_container_width=True)

    if username == 'jsafaa':
        with admin_tab:
            st.subheader("👥 Staff Management")
            with st.expander("Add Employee"):
                nu = st.text_input("New Username").lower().strip()
                nn = st.text_input("New Full Name")
                if st.button("Create Account"):
                    if nu and nu not in users_df['username'].values:
                        new_u = {"username": nu, "password": "123", "name": nn, "role": "Employee", "first_login": True}
                        pd.concat([users_df, pd.DataFrame([new_u])], ignore_index=True).to_csv(users_file, index=False)
                        st.success("User Added!"); st.rerun()
            with st.expander("Delete/Reset User"):
                target = st.selectbox("Select User", users_df['username'].values)
                if st.button("Reset Password to 123"):
                    users_df.loc[users_df['username'] == target, ['password', 'first_login']] = ["123", True]
                    users_df.to_csv(users_file, index=False)
                    st.success("Reset Done!")
                if st.button("Delete Account", type="primary"):
                    users_df[users_df['username'] != target].to_csv(users_file, index=False)
                    st.warning("Deleted!"); st.rerun()

elif st.session_state["authentication_status"] is False: st.error("Wrong Username/Password")
else: st.info("Please Login")
