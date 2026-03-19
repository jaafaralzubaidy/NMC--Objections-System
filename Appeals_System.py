import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# 1. إعدادات المتصفح والخط العربي
st.set_page_config(page_title="نظام NMC", layout="wide")

# دالة الوقت - توقيت بغداد
def جلب_الوقت():
    return (datetime.utcnow() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')

st.markdown("<h1 style='text-align: center; color: #007bff;'>🚀 نظام الاعتراضات NMC - النسخة الإدارية الكاملة</h1>", unsafe_allow_html=True)

# 2. تعريف ملفات البيانات
ملف_المستخدمين = "users_list.csv"
ملف_البيانات = "database_appeals.csv"

# إنشاء الملفات إذا كانت مفقودة لأول مرة
if not os.path.exists(ملف_المستخدمين):
    pd.DataFrame([{"username":"jsafaa","password":"123","name":"جاسم صفاء"}]).to_csv(ملف_المستخدمين, index=False)

# تعريف الأعمدة (تم إضافة عمود وقت الإنشاء ليعمل بشكل صحيح)
أعمدة_النظام = ["الموظف", "التاريخ", "رقم_التكت", "القسم", "التفاصيل", "قرار_الجودة", "قرار_المدير", "وقت_إنشاء_الطلب"]

if not os.path.exists(ملف_البيانات):
    pd.DataFrame(columns=أعمدة_النظام).to_csv(ملف_البيانات, index=False)

# قراءة البيانات الحالية
df_users = pd.read_csv(ملف_المستخدمين)
df_main = pd.read_csv(ملف_البيانات)

# ضمان وجود عمود الوقت في حال تم مسحه بالخطأ
if "وقت_إنشاء_الطلب" not in df_main.columns:
    df_main["وقت_إنشاء_الطلب"] = "N/A"

# 3. نظام تسجيل الدخول (يبقى مسجلاً)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("🔑 تسجيل الدخول إلى النظام")
    يوزر_ادخال = st.text_input("اسم المستخدم").lower().strip()
    رمز_ادخال = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        فحص = df_users[(df_users['username'] == يوزر_ادخال) & (df_users['password'].astype(str) == رمز_ادخال)]
        if not فحص.empty:
            st.session_state.logged_in = True
            st.session_state.user = يوزر_ادخال
            st.session_state.name = فحص.iloc[0]['name']
            st.rerun()
        else:
            st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
else:
    # القائمة الجانبية
    st.sidebar.success(f"مرحباً بك: {st.session_state.name}")
    if st.sidebar.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.rerun()

    # التبويبات (تظهر فقط للمدير jsafaa)
    if st.session_state.user == 'jsafaa':
        تبويب1, تبويب2 = st.tabs(["📊 بوابة الاعتراضات", "👥 إدارة الموظفين"])
    else:
        تبويب1 = st.container()

    # --- تبويب العمليات ---
    with تبويب1:
        if st.session_state.user in ['jsafaa', 'ahatim']:
            st.subheader("🛠 لوحة التحكم والمراجعة")
            st.dataframe(df_main, use_container_width=True)
            with st.expander("تحديث القرارات الإدارية"):
                رقم_الطلب = st.number_input("رقم الطلب (Index)", 0, len(df_main)-1, 0)
                col_q, col_m = st.columns(2)
                with col_q:
                    قرار_ق = st.text_area("تعديل قرار الجودة", df_main.loc[رقم_الطلب, "قرار_الجودة"])
                with col_m:
                    قرار_م = st.text_area("تعديل قرار المدير", df_main.loc[رقم_الطلب, "قرار_المدير"])
                if st.button("حفظ التحديث"):
                    df_main.loc[رقم_الطلب, "قرار_الجودة"] = قرار_ق
                    df_main.loc[رقم_الطلب, "قرار_المدير"] = قرار_م
                    df_main.to_csv(ملف_البيانات, index=False)
                    st.success("تم تحديث البيانات بنجاح")
                    st.rerun()
        else:
            # واجهة الموظف العادي
            with st.form("ob_form", clear_on_submit=True):
                st.subheader("📤 تقديم اعتراض جديد")
                تاريخ_الحدث = st.date_input("تاريخ الحادثة")
                رقم_التكت = st.text_input("رقم التكت")
                القسم = st.selectbox("اختر القسم", ["SWITCH STATE", "MPLS", "Wireless", "Power", "AL-Watani"])
                التفاصيل = st.text_area("شرح الأسباب والتفاصيل")
                if st.form_submit_button("إرسال الاعتراض"):
                    جديد = {
                        "الموظف": st.session_state.name, "التاريخ": str(تاريخ_الحدث), 
                        "رقم_التكت": رقم_التكت, "القسم": القسم, "التفاصيل": التفاصيل, 
                        "قرار_الجودة": "Pending", "قرار_المدير": "Pending", 
                        "وقت_إنشاء_الطلب": جلب_الوقت() # تسجيل الوقت بدقة
                    }
                    df_main = pd.concat([df_main, pd.DataFrame([جديد])], ignore_index=True)
                    df_main.to_csv(ملف_البيانات, index=False)
                    st.success("تم إرسال اعتراضك بنجاح")
                    st.balloons()
            
            st.divider()
            st.subheader("📜 سجل اعتراضاتي السابقة")
            st.table(df_main[df_main['الموظف'] == st.session_state.name])

    # --- تبويب الإدارة (إضافة، مسح، باسورد) ---
    if st.session_state.user == 'jsafaa':
        with تبويب2:
            st.subheader("👤 التحكم في حسابات الموظفين")
            c1, c2, c3 = st.columns(3)
            
            with c1:
                with st.expander("➕ إضافة موظف جديد"):
                    يوزر_جديد = st.text_input("اسم المستخدم الجديد").lower().strip()
                    اسم_جديد = st.text_input("الاسم الكامل للموظف")
                    if st.button("تأكيد الإضافة"):
                        if يوزر_جديد and يوزر_جديد not in df_users['username'].values:
                            df_users = pd.concat([df_users, pd.DataFrame([{"username":يوزر_جديد,"password":"123","name":اسم_جديد}])], ignore_index=True)
                            df_users.to_csv(ملف_المستخدمين, index=False)
                            st.success(f"تمت إضافة {اسم_جديد} بنجاح")
                            st.rerun()

            with c2:
                with st.expander("🔑 تغيير كلمة مرور"):
                    الموظف_المستهدف = st.selectbox("اختر الموظف", df_users['username'].values)
                    الرمز_الجديد = st.text_input("كلمة المرور الجديدة")
                    if st.button("تحديث كلمة السر"):
                        df_users.loc[df_users['username'] == الموظف_المستهدف, 'password'] = الرمز_الجديد
                        df_users.to_csv(ملف_المستخدمين, index=False)
                        st.success("تم تغيير كلمة المرور بنجاح")

            with c3:
                with st.expander("🗑️ حذف حساب موظف"):
                    يوزر_للحذف = st.selectbox("اختر الحساب المراد حذفه", [u for u in df_users['username'].values if u != 'jsafaa'])
                    if st.button("حذف نهائي"):
                        df_users = df_users[df_users['username'] != يوزر_للحذف]
                        df_users.to_csv(ملف_المستخدمين, index=False)
                        st.warning(f"تم حذف الحساب {يوزر_للحذف}")
                        st.rerun()
