import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
import os
from datetime import datetime

# --- إعدادات الواجهة واللوغو ---
st.set_page_config(page_title="NMC Objections System", layout="wide")

# تصميم الواجهة بالألوان واللوغو
st.markdown("""
    <style>
    .main-title { font-size:45px !important; color: #1E3A8A; text-align: center; font-weight: bold; }
    .sub-title { font-size:22px !important; color: #10B981; text-align: center; margin-bottom: 30px; }
    </style>
    <div class="main-title">🌐 NMC Objections System</div>
    <p class="sub-title">Network Monitoring Center - Quality & Management Portal</p>
    <hr>
""", unsafe_allow_html=True)

# --- نظام المستخدمين (أضف أسماء موظفيك هنا) ---
# ملاحظة: الباسوردات الافتراضية '123'
names = ['Admin Quality', 'Direct Manager', 'Ahmed Ali', 'Zaid Hassan']
usernames = ['admin', 'manager', 'ahmed', 'zaid']
passwords = ['admin123', 'manager123', '123', '123']

hashed_passwords = stauth.Hasher(passwords).generate()

authenticator = stauth.Authenticate(
    {'usernames': {u: {'name': n, 'password': p} for u, n, p in zip(usernames, names, hashed_passwords)}},
    'nmc_cookie', 'auth_key', cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status == False:
    st.error('الاسم أو الرمز السري غير صحيح')
elif authentication_status == None:
    st.info('يرجى تسجيل الدخول للوصول إلى نظام الاعتراضات')
elif authentication_status:
    
    authenticator.logout('تسجيل الخروج', 'sidebar')
    st.sidebar.success(f"أهلاً بك: {name}")

    # --- إدارة قاعدة البيانات ---
    file_name = "database_appeals.csv"
    if not os.path.exists(file_name):
        df = pd.DataFrame(columns=["Employee", "Date", "Ticket Number", "Tab", "Details", "Quality Decision", "Direct Manager"])
        df.to_csv(file_name, index=False, encoding='utf-8-sig')
    
    df = pd.read_csv(file_name)

    # --- واجهة الأدمن والمدير (Admin & Manager) ---
    if username in ['admin', 'manager']:
        st.subheader("🛠 لوحة التحكم - الإدارة والكوالتي")
        st.write("جدول الاعتراضات الحالي:")
        st.dataframe(df)

        with st.expander("تحديث القرارات (الرد على الاعتراض)"):
            row_to_update = st.number_input("أدخل رقم السطر المراد تعديله (يبدأ من 0)", min_value=0, max_value=len(df)-1 if len(df)>0 else 0, step=1)
            col_dec, col_mgr = st.columns(2)
            
            with col_dec:
                q_desc = st.text_area("قرار الكوالتي (Quality Decision)")
            with col_mgr:
                m_desc = st.text_area("قرار المدير المباشر (Direct Manager)")
            
            if st.button("حفظ وإرسال الرد"):
                df.loc[row_to_update, "Quality Decision"] = q_desc
                df.loc[row_to_update, "Direct Manager"] = m_desc
                df.to_csv(file_name, index=False, encoding='utf-8-sig')
                st.success("تم تحديث القرار بنجاح!")
                st.rerun()

    # --- واجهة الموظف (Employee Page) ---
    else:
        tab1, tab2 = st.tabs(["تقديم اعتراض جديد", "سجل اعتراضاتي"])
        
        with tab1:
            st.subheader("إضافة اعتراض")
            with st.form("employee_form"):
                f_date = st.date_input("Date (التاريخ)", datetime.now())
                f_ticket = st.text_input("Ticket Number (رقم التكت)")
                f_tab = st.selectbox("Tab / Shift", ["Morning", "Evening", "Night"])
                f_details = st.text_area("Details (شرح المشكلة)")
                
                submit_btn = st.form_submit_button("إرسال الاعتراض (Submit)")
                
                if submit_btn:
                    if not f_ticket or not f_details or not f_tab:
                        st.error("❌ جميع الحقول المطلوبة (رقم التكت، التاريخ، الشفت، التفاصيل) إلزامية!")
                    else:
                        new_row = {"Employee": name, "Date": str(f_date), "Ticket Number": f_ticket, 
                                   "Tab": f_tab, "Details": f_details, "Quality Decision": "قيد المراجعة", "Direct Manager": "قيد المراجعة"}
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        df.to_csv(file_name, index=False, encoding='utf-8-sig')
                        st.success("✅ تم إرسال اعتراضك بنجاح!")

        with tab2:
            st.subheader("حالة اعتراضاتي السابقة")
            user_data = df[df['Employee'] == name]
            if user_data.empty:
                st.info("لا يوجد لديك اعتراضات مسجلة بعد.")
            else:
                st.table(user_data)