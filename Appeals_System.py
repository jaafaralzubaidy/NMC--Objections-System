import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime

# --- إعدادات الواجهة ---
st.set_page_config(page_title="NMC Objections System", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size:40px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
    .sub-title { font-size:20px !important; color: #10B981; text-align: center; margin-bottom: 20px; }
    </style>
    <div class="main-title">🌐 NMC Objections System</div>
    <p class="sub-title">Network Monitoring Center - Quality & Management Portal</p>
    <hr>
""", unsafe_allow_html=True)

# --- بيانات المستخدمين ---
config = {
    'credentials': {
        'usernames': {
            'admin': {'name': 'Admin Quality', 'password': 'admin123'},
            'manager': {'name': 'Direct Manager', 'password': 'manager123'},
            'ahmed': {'name': 'Ahmed Ali', 'password': '123'},
            'zaid': {'name': 'Zaid Hassan', 'password': '123'}
        }
    },
    'cookie': {'expiry_days': 30, 'key': 'nmc_auth_key', 'name': 'nmc_cookie'}
}

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- حل مشكلة سطر 43 (تعديل جذري) ---
# نستخدم محاولة تجربة الطرق المختلفة لتسجيل الدخول حسب إصدار المكتبة
try:
    # الطريقة الحديثة (بدون باراميترات)
    authenticator.login()
except:
    try:
        # طريقة الإصدارات الوسطى
        authenticator.login('main')
    except:
        # الطريقة القديمة
        authenticator.login('Login', 'main')

# التأكد من حالة تسجيل الدخول من الـ session_state مباشرة
if st.session_state.get("authentication_status") == False:
    st.error('الاسم أو الرمز السري غير صحيح')
elif st.session_state.get("authentication_status") == None:
    st.info('يرجى تسجيل الدخول للوصول إلى نظام الاعتراضات')
elif st.session_state.get("authentication_status"):
    
    name = st.session_state.get("name")
    username = st.session_state.get("username")
    
    authenticator.logout('Logout', 'sidebar')
    st.sidebar.success(f"أهلاً بك: {name}")

    # --- قاعدة البيانات ---
    file_name = "database_appeals.csv"
    if not os.path.exists(file_name):
        df = pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager"])
        df.to_csv(file_name, index=False, encoding='utf-8-sig')
    
    df = pd.read_csv(file_name)

    # --- واجهة الإدارة ---
    if username in ['admin', 'manager']:
        st.subheader("🛠 لوحة التحكم")
        st.dataframe(df)
        with st.expander("تعديل القرارات"):
            if not df.empty:
                row_idx = st.number_input("رقم السطر", 0, len(df)-1, 0)
                q_dec = st.text_area("قرار الكوالتي")
                m_dec = st.text_area("قرار المدير")
                if st.button("حفظ"):
                    df.loc[row_idx, "Quality Decision"] = q_dec
                    df.loc[row_idx, "Direct Manager"] = m_dec
                    df.to_csv(file_name, index=False, encoding='utf-8-sig')
                    st.success("تم الحفظ!")
                    st.rerun()
    # --- واجهة الموظف ---
    else:
        t1, t2 = st.tabs(["إضافة اعتراض", "اعتراضاتي"])
        with t1:
            with st.form("f1"):
                t_num = st.text_input("رقم التكت")
                t_det = st.text_area("التفاصيل")
                if st.form_submit_button("إرسال"):
                    new_data = {"Employee": name, "Date": str(datetime.now().date()), "Ticket Number": t_num, 
                                "Tab": "N/A", "Details": t_det, "Quality Decision": "Pending", "Direct Manager": "Pending"}
                    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                    df.to_csv(file_name, index=False, encoding='utf-8-sig')
                    st.success("تم الإرسال!")
        with t2:
            st.table(df[df['Employee'] == name])