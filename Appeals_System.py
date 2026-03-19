import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime

# --- إعدادات الواجهة واللوغو ---
st.set_page_config(page_title="NMC Objections System", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size:45px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
    .sub-title { font-size:22px !important; color: #10B981; text-align: center; margin-bottom: 30px; }
    </style>
    <div class="main-title">🌐 NMC Objections System</div>
    <p class="sub-title">Network Monitoring Center - Quality & Management Portal</p>
    <hr>
""", unsafe_allow_html=True)

# --- نظام المستخدمين (التعديل الجديد والمبسط) ---
# هنا وضعنا اليوزرات والباسوردات مباشرة لتجنب الخطأ السابق
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

# تشغيل نظام تسجيل الدخول
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# عرض خانة تسجيل الدخول
name, authentication_status, username = authenticator.login(location='main')

if authentication_status == False:
    st.error('الاسم أو الرمز السري غير صحيح')
elif authentication_status == None:
    st.info('يرجى تسجيل الدخول للوصول إلى نظام الاعتراضات')
elif authentication_status:
    
    # زر تسجيل الخروج
    authenticator.logout('Logout', 'sidebar')
    st.sidebar.success(f"أهلاً بك: {name}")

    # --- إدارة قاعدة البيانات ---
    file_name = "database_appeals.csv"
    if not os.path.exists(file_name):
        df = pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager"])
        df.to_csv(file_name, index=False, encoding='utf-8-sig')
    
    df = pd.read_csv(file_name)

    # --- واجهة الأدمن والمدير ---
    if username in ['admin', 'manager']:
        st.subheader("🛠 لوحة التحكم - الإدارة والكوالتي")
        st.dataframe(df)

        with st.expander("تحديث القرارات (الرد على الاعتراض)"):
            if len(df) > 0:
                row_to_update = st.number_input("أدخل رقم السطر المراد تعديله (يبدأ من 0)", min_value=0, max_value=len(df)-1, step=1)
                col_dec, col_mgr = st.columns(2)
                
                with col_dec:
                    q_desc = st.text_area("قرار الكوالتي (Quality Decision)")
                with col_mgr:
                    m_desc = st.text_area("قرار المدير المباشر (Direct Manager)")
                
                if st.button("حفظ وإرسال الرد"):
                    df.loc[row_to_update, "Quality Decision"] = q_desc
                    df.loc[row_to_update, "Direct Manager"] = m_desc
                    df.to_csv(file_name, index=False, encoding='utf-8-sig')
                    st.success("تم تحديث القرار!")
                    st.rerun()
            else:
                st.write("لا توجد اعتراضات حالياً.")

    # --- واجهة الموظف ---
    else:
        tab1, tab2 = st.tabs(["تقديم اعتراض جديد", "سجل اعتراضاتي"])
        
        with tab1:
            with st.form("employee_form"):
                f_date = st.date_input("Date", datetime.now())
                f_ticket = st.text_input("Ticket Number")
                f_tab = st.selectbox("Tab / Shift", ["Morning", "Evening", "Night"])
                f_details = st.text_area("Details")
                
                submit_btn = st.form_submit_button("Submit")
                
                if submit_btn:
                    if not f_ticket or not f_details or not f_tab:
                        st.error("❌ جميع الحقول مطلوبة!")
                    else:
                        new_row = {"Employee": name, "Date": str(f_date), "Ticket Number": f_ticket, 
                                   "Tab": f_tab, "Details": f_details, "Quality Decision": "Pending", "Direct Manager": "Pending"}
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        df.to_csv(file_name, index=False, encoding='utf-8-sig')
                        st.success("✅ تم إرسال اعتراضك!")

        with tab2:
            user_data = df[df['Employee'] == name]
            st.table(user_data)