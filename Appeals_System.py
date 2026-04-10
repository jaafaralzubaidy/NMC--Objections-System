import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="NMC Objections", layout="wide")

# --- 2. جلب البيانات بأسرع وسيلة (Caching) ---
@st.cache_data(ttl=300) # تخزين البيانات لمدة 5 دقائق لسرعة فائقة
def load_data(file, columns=None):
    if not os.path.exists(file) and columns:
        pd.DataFrame(columns=columns).to_csv(file, index=False)
    return pd.read_csv(file)

users_df = load_data("users_list.csv")
df_appeals = load_data("database_appeals.csv", ["Employee", "Date", "Ticket Number", "Details", "Quality Decision", "Direct Manager"])

# --- 3. إعداد الدخول ---
creds = {'usernames': {}}
for _, r in users_df.iterrows():
    creds['usernames'][r['username']] = {
        'name': f"{r['name']} ({r['role']})",
        'password': str(r['password'])
    }

auth = stauth.Authenticate(creds, 'nmc_c', 'nmc_k', cookie_expiry_days=30)

st.markdown('<h2 style="text-align:center;">🛰️ NMC SYSTEM - FAST MODE</h2>', unsafe_allow_html=True)

try:
    auth.login()
except:
    st.info("Please Login")

if st.session_state.get("authentication_status"):
    user = st.session_state.get("username")
    st.sidebar.markdown(f"👤 {creds['usernames'][user]['name']}")
    auth.logout('Logout', 'sidebar')

    # الصلاحيات
    is_admin = user in ['jsafaa', 'farook']
    is_mgmt = user in ['jsafaa', 'ahatim', 'farook']

    # تم حذف خاصية الإضافة وبقي فقط المنج ستاف للريسيت
    t_list = ["📊 System", "🔄 Staff Control"] if is_admin else ["📊 System"]
    main_tabs = st.tabs(t_list)

    with main_tabs[0]:
        if is_mgmt:
            st.dataframe(df_appeals, use_container_width=True)
            with st.expander("Update"):
                if not df_appeals.empty:
                    idx = st.number_input("ID", 0, len(df_appeals)-1, 0)
                    c1, c2 = st.columns(2)
                    with c1:
                        q_val = st.text_area("Quality", value=df_appeals.loc[idx, "Quality Decision"], disabled=(user != 'jsafaa'))
                    with c2:
                        m_val = st.text_area("Manager", value=df_appeals.loc[idx, "Direct Manager"], disabled=(user == 'jsafaa'))
                    if st.button("Save"):
                        df_appeals.loc[idx, "Quality Decision"] = q_val
                        df_appeals.loc[idx, "Direct Manager"] = m_val
                        df_appeals.to_csv("database_appeals.csv", index=False)
                        st.cache_data.clear() # تحديث فوري
                        st.success("Saved")
                        st.rerun()
        else:
            with st.form("sub"):
                tkt = st.text_input("Ticket")
                det = st.text_area("Details")
                if st.form_submit_button("Send"):
                    new = {"Employee": user, "Date": str(datetime.now().date()), "Ticket Number": tkt, "Details": det, "Quality Decision": "Pending", "Direct Manager": "Pending"}
                    pd.concat([df_appeals, pd.DataFrame([new])]).to_csv("database_appeals.csv", index=False)
                    st.cache_data.clear()
                    st.rerun()

    if is_admin:
        with main_tabs[1]:
            st.subheader("Password Reset Only")
            u_sel = st.selectbox("Select User", users_df['username'].values)
            if st.button("Reset to 123"):
                users_df.loc[users_df['username'] == u_sel, 'password'] = "123"
                users_df.loc[users_df['username'] == u_sel, 'Force_Change'] = True
                users_df.to_csv("users_list.csv", index=False)
                st.cache_data.clear()
                st.success(f"Done for {u_sel}")

elif st.session_state.get("authentication_status") == False:
    st.error("Error")
