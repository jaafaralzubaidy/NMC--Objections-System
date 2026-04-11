import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="NMC System", layout="wide")

# أسماء الملفات التي تحتوي على بياناتك
u_file = "users_list.csv"
a_file = "database_appeals.csv"

# --- 2. جلب البيانات (قراءة مباشرة لضمان السرعة والبيانات) ---
def get_all_data():
    # تحميل المستخدمين
    if os.path.exists(u_file):
        u_df = pd.read_csv(u_file)
        # التأكد من رتبة فاروق
        if 'farook' in u_df['username'].values:
            u_df.loc[u_df['username'] == 'farook', 'role'] = 'Team Leader'
    else:
        st.error("Missing users_list.csv!")
        st.stop()
    
    # تحميل الاعتراضات
    if os.path.exists(a_file):
        a_df = pd.read_csv(a_file)
    else:
        a_df = pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Details", "Quality Decision", "Direct Manager"])
    
    return u_df, a_df

users_df, df_appeals = get_all_data()

# --- 3. إعداد الدخول ---
creds = {'usernames': {}}
for _, r in users_df.iterrows():
    creds['usernames'][str(r['username'])] = {
        'name': f"{r['name']} ({r['role']})",
        'password': str(r['password'])
    }

auth = stauth.Authenticate(creds, 'nmc_cookie', 'nmc_key', cookie_expiry_days=30)

st.markdown("<h2 style='text-align:center;'>🛰️ NMC OBJECTIONS SYSTEM</h2>", unsafe_allow_html=True)

try:
    auth.login()
except:
    pass

if st.session_state.get("authentication_status"):
    user = st.session_state.get("username")
    
    # حماية من خطأ KeyError الظاهر في الصورة
    if user not in creds['usernames']:
        st.error("User not found in database.")
        st.stop()

    st.sidebar.write(f"👤 {creds['usernames'][user]['name']}")
    auth.logout('Logout', 'sidebar')

    # الصلاحيات
    is_admin = user in ['jsafaa', 'farook']
    is_mgmt = user in ['jsafaa', 'ahatim', 'farook']

    # التبويبات (تم حذف "إضافة موظف" لسرعة البرنامج)
    t = st.tabs(["📊 System", "🔄 Reset Password"]) if is_admin else st.tabs(["📊 System"])

    with t[0]:
        if is_mgmt:
            st.subheader("Management Panel")
            st.dataframe(df_appeals, use_container_width=True)
            
            with st.expander("Update Decisions"):
                if not df_appeals.empty:
                    idx = st.number_input("Select ID", 0, len(df_appeals)-1, 0)
                    c1, c2 = st.columns(2)
                    with c1:
                        # جودة (صفاء) فقط
                        q_val = st.text_area("Quality", value=df_appeals.loc[idx, "Quality Decision"], disabled=(user != 'jsafaa'))
                    with c2:
                        # مدير (حاتم/فاروق) فقط
                        m_val = st.text_area("Manager", value=df_appeals.loc[idx, "Direct Manager"], disabled=(user == 'jsafaa'))
                    
                    if st.button("Save"):
                        df_appeals.loc[idx, "Quality Decision"] = q_val
                        df_appeals.loc[idx, "Direct Manager"] = m_val
                        df_appeals.to_csv(a_file, index=False)
                        st.success("Saved!")
                        st.rerun()
        else:
            # واجهة الموظف
            st.subheader("My Submissions")
            st.dataframe(df_appeals[df_appeals['Employee'] == user])
            with st.form("sub"):
                tkt = st.text_input("Ticket #")
                det = st.text_area("Details")
                if st.form_submit_button("Submit"):
                    new = {"Employee": user, "Date": str(datetime.now().date()), "Ticket Number": tkt, "Details": det, "Quality Decision": "Pending", "Direct Manager": "Pending"}
                    new_df = pd.concat([df_appeals, pd.DataFrame([new])], ignore_index=True)
                    new_df.to_csv(a_file, index=False)
                    st.success("Sent!")
                    st.rerun()

    if is_admin and len(t) > 1:
        with t[1]:
            st.subheader("Reset Staff Password")
            target = st.selectbox("Select User", users_df['username'].values)
            if st.button("Reset to 123"):
                users_df.loc[users_df['username'] == target, 'password'] = "123"
                users_df.to_csv(u_file, index=False)
                st.success(f"Password for {target} is now 123")

elif st.session_state.get("authentication_status") == False:
    st.error("Wrong Username/Password")
