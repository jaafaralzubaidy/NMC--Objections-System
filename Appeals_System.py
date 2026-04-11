import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="NMC Objections System", layout="wide")

# ملفات البيانات (المصدر الحقيقي لكل معلوماتك)
appeals_file = "database_appeals.csv"
users_file = "users_list.csv"

# --- 2. جلب البيانات (بدون إعادة ضبط أو تغيير) ---
def load_existing_data():
    # التأكد من وجود الملفات قبل القراءة
    if os.path.exists(users_file):
        u_df = pd.read_csv(users_file)
        # التأكد من بقاء منصب فاروق كما هو
        if 'farook' in u_df['username'].values:
            u_df.loc[u_df['username'] == 'farook', 'role'] = 'Team Leader'
    else:
        st.error("ملف المستخدمين غير موجود! تأكد من وجود users_list.csv في نفس المجلد.")
        st.stop()
        
    if os.path.exists(appeals_file):
        a_df = pd.read_csv(appeals_file)
    else:
        a_df = pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Details", "Quality Decision", "Direct Manager"])
        
    return u_df, a_df

users_df, df_appeals = load_existing_data()

# --- 3. نظام الدخول المستقر ---
creds = {'usernames': {}}
for _, row in users_df.iterrows():
    creds['usernames'][row['username']] = {
        'name': f"{row['name']} ({row['role']})",
        'password': str(row['password']) # نستخدم الباسورد المخزن في ملفك حصراً
    }

authenticator = stauth.Authenticate(creds, 'nmc_cookie', 'nmc_key', cookie_expiry_days=30)

st.markdown('<h2 style="text-align:center;">🛰️ NMC OBJECTIONS SYSTEM</h2>', unsafe_allow_html=True)

try:
    authenticator.login()
except Exception:
    pass

if st.session_state.get("authentication_status"):
    username = st.session_state.get("username")
    
    st.sidebar.markdown(f"👤 **{creds[username]['name']}**")
    authenticator.logout('Logout', 'sidebar')

    # تحديد الصلاحيات بناءً على الاسم
    is_admin = username in ['jsafaa', 'farook']
    is_mgmt = username in ['jsafaa', 'ahatim', 'farook']

    # تبويبات النظام
    tabs = st.tabs(["📊 System", "🔄 Password Management"]) if is_admin else st.tabs(["📊 System"])

    with tabs[0]:
        if is_mgmt:
            st.subheader("📋 Management Control Panel")
            # عرض كافة الاعتراضات السابقة
            st.dataframe(df_appeals, use_container_width=True)
            
            with st.expander("Update Decisions"):
                if not df_appeals.empty:
                    row_idx = st.number_input("Select Row ID", 0, len(df_appeals)-1, 0)
                    col1, col2 = st.columns(2)
                    with col1:
                        q_dec = st.text_area("Quality Decision", value=df_appeals.loc[row_idx, "Quality Decision"], disabled=(username != 'jsafaa'))
                    with col2:
                        m_dec = st.text_area("Head Of Section Decision", value=df_appeals.loc[row_idx, "Direct Manager"], disabled=(username == 'jsafaa'))
                    
                    if st.button("Save Changes"):
                        df_appeals.loc[row_idx, "Quality Decision"] = q_dec
                        df_appeals.loc[row_idx, "Direct Manager"] = m_dec
                        df_appeals.to_csv(appeals_file, index=False)
                        st.success("تم الحفظ بنجاح")
                        st.rerun()
        else:
            # واجهة الموظف
            st.subheader("📝 My Objections")
            my_data = df_appeals[df_appeals['Employee'] == username]
            st.dataframe(my_data, use_container_width=True)
            
            with st.form("new_objection"):
                t_num = st.text_input("Ticket Number")
                details = st.text_area("Objection Details")
                if st.form_submit_button("Submit Objection"):
                    new_entry = {
                        "Employee": username, "Date": str(datetime.now().date()), 
                        "Ticket Number": t_num, "Details": details,
                        "Quality Decision": "Pending", "Direct Manager": "Pending"
                    }
                    df_appeals = pd.concat([df_appeals, pd.DataFrame([new_entry])], ignore_index=True)
                    df_appeals.to_csv(appeals_file, index=False)
                    st.success("تم إرسال الاعتراض")
                    st.rerun()

    if is_admin and len(tabs) > 1:
        with tabs[1]:
            st.subheader("🔄 Staff Password Reset")
            target_user = st.selectbox("Select Staff Member", users_df['username'].values)
            if st.button("Reset to 123"):
                users_df.loc[users_df['username'] == target_user, 'password'] = "123"
                users_df.loc[users_df['username'] == target_user, 'Force_Change'] = True
                users_df.to_csv(users_file, index=False)
                st.success(f"تم إعادة تعيين رمز {target_user}")

elif st.session_state.get("authentication_status") == False:
    st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
