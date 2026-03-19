import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- 1. الإعدادات والوقت ---
st.set_page_config(page_title="NMC Portal", layout="wide")

def get_baghdad_time():
    return (datetime.utcnow() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')

# --- 2. إدارة البيانات ---
u_file, a_file = "users_list.csv", "database_appeals.csv"

if not os.path.exists(u_file):
    pd.DataFrame([{"username":"jsafaa","password":"123","name":"J. SAFAA","role":"Admin"}]).to_csv(u_file, index=False)
if not os.path.exists(a_file):
    cols = ["Employee","Date","Ticket Number","Tab","Details","Quality Decision","Direct Manager","Objection Creation Date"]
    pd.DataFrame(columns=cols).to_csv(a_file, index=False)

u_df = pd.read_csv(u_file)
a_df = pd.read_csv(a_file)

# تأكيد وجود العمود المطلوب
if "Objection Creation Date" not in a_df.columns:
    a_df["Objection Creation Date"] = "N/A"

# --- 3. نظام الدخول وتذكر المستخدم ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.form("login_form"):
        st.subheader("🔑 Login")
        u_in = st.text_input("Username").lower().strip()
        p_in = st.text_input("Password", type="password")
        if st.form_submit_button("Sign In"):
            user_row = u_df[(u_df['username'] == u_in) & (u_df['password'].astype(str) == p_in)]
            if not user_row.empty:
                st.session_state.logged_in, st.session_state.username = True, u_in
                st.session_state.name = user_row.iloc[0]['name']
                st.rerun()
            else: st.error("خطأ في البيانات")
else:
    st.sidebar.write(f"👤 {st.session_state.name}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # --- 4. التبويبات ---
    if st.session_state.username == 'jsafaa':
        tab1, tab2 = st.tabs(["📊 Operations", "👥 Admin: Manage Staff"])
    else: tab1 = st.container()

    with tab1:
        if st.session_state.username in ['jsafaa', 'ahatim']:
            st.subheader("🛠 Control Panel")
            st.dataframe(a_df, use_container_width=True) # عرض الجدول مع عمود التاريخ
            with st.expander("Update Decisions"):
                if not a_df.empty:
                    idx = st.number_input("Index", 0, len(a_df)-1, 0)
                    c1, c2 = st.columns(2)
                    with c1: q = st.text_area("Quality", a_df.loc[idx, "Quality Decision"], disabled=(st.session_state.username == 'ahatim'))
                    with c2: m = st.text_area("Manager", a_df.loc[idx, "Direct Manager"], disabled=(st.session_state.username == 'jsafaa'))
                    if st.button("Save"):
                        a_df.loc[idx, "Quality Decision"], a_df.loc[idx, "Direct Manager"] = q, m
                        a_df.to_csv(a_file, index=False); st.success("Done"); st.rerun()
        else:
            with st.form("ob_form"):
                st.subheader("📤 Submit Objection")
                f1, f2 = st.date_input("Date"), st.text_input("Ticket#")
                f3 = st.selectbox("Tab", ["SWITCH STATE", "MPLS", "Wireless", "Power"])
                f4 = st.text_area("Details")
                if st.form_submit_button("Submit"):
                    new_r = {
                        "Employee": st.session_state.name, "Date": str(f1), "Ticket Number": f2, "Tab": f3, "Details": f4,
                        "Quality Decision": "Pending", "Direct Manager": "Pending",
                        "Objection Creation Date": get_baghdad_time() # التسجيل التلقائي
                    }
                    a_df = pd.concat([a_df, pd.DataFrame([new_r])], ignore_index=True)
                    a_df.to_csv(a_file, index=False); st.success("Sent"); st.rerun()
            st.table(a_df[a_df['Employee'] == st.session_state.name])

    # --- 5. لوحة التحكم (الإضافة، الحذف، الباسورد) ---
    if st.session_state.username == 'jsafaa':
        with tab2:
            st.subheader("👥 Manage Staff")
            c_add, c_pass, c_del = st.columns(3)
            with c_add:
                with st.expander("➕ Add"):
                    nu, nn = st.text_input("User ID"), st.text_input("Full Name")
                    if st.button("Add Now"):
                        u_df = pd.concat([u_df, pd.DataFrame([{"username":nu.lower(),"password":"123","name":nn,"role":"User"}])], ignore_index=True)
                        u_df.to_csv(u_file, index=False); st.success("Added"); st.rerun()
            with c_pass:
                with st.expander("🔑 Password"):
                    target = st.selectbox("Select User", u_df['username'].values)
                    np = st.text_input("New Password")
                    if st.button("Update Pass"):
                        u_df.loc[u_df['username'] == target, 'password'] = np
                        u_df.to_csv(u_file, index=False); st.success("Updated")
            with c_del:
                with st.expander("🗑️ Delete"):
                    rem = st.selectbox("Delete", [u for u in u_df['username'].values if u != 'jsafaa'])
                    if st.button("Confirm Delete"):
                        u_df = u_df[u_df['username'] != rem]
                        u_df.to_csv(u_file, index=False); st.warning("Deleted"); st.rerun()