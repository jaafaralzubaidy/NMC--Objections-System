import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# إعدادات لضمان التحديث
st.set_page_config(page_title="NMC System V3", layout="wide")

def get_time():
    return (datetime.utcnow() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 نظام الاعتراضات الإداري")

# ملفات البيانات
u_file = "users_list.csv"
a_file = "database_appeals.csv"

# إنشاء مستخدم افتراضي إذا اختفى الملف
if not os.path.exists(u_file):
    pd.DataFrame([{"username":"jsafaa","password":"123","name":"جاسم صفاء"}]).to_csv(u_file, index=False)

# الأعمدة الجديدة (إجبارية)
cols = ["الموظف", "التاريخ", "رقم_التكت", "القسم", "التفاصيل", "قرار_الجودة", "قرار_المدير", "وقت_إنشاء_الطلب"]

if not os.path.exists(a_file):
    pd.DataFrame(columns=cols).to_csv(a_file, index=False)

u_df = pd.read_csv(u_file)
a_df = pd.read_csv(a_file)

# --- نظام الدخول ---
if 'login' not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    u_in = st.text_input("Username").lower().strip()
    p_in = st.text_input("Password", type="password")
    if st.button("Login"):
        user = u_df[(u_df['username'] == u_in) & (u_df['password'].astype(str) == p_in)]
        if not user.empty:
            st.session_state.login = True
            st.session_state.user = u_in
            st.session_state.name = user.iloc[0]['name']
            st.rerun()
else:
    st.sidebar.write(f"👤 {st.session_state.name}")
    if st.sidebar.button("Logout"):
        st.session_state.login = False
        st.rerun()

    # التبويبات (تأكد أن اليوزر هو jsafaa لتظهر لك)
    if st.session_state.user == 'jsafaa':
        t1, t2 = st.tabs(["📊 العمليات", "👥 إدارة الموظفين"])
    else: t1 = st.container()

    with t1:
        st.subheader("جدول البيانات")
        st.dataframe(a_df, use_container_width=True) # هنا سيظهر عمود وقت_إنشاء_الطلب
        
        if st.session_state.user == 'jsafaa':
            with st.expander("تحديث القرارات"):
                idx = st.number_input("السطر", 0, len(a_df)-1, 0)
                q = st.text_area("الجودة", a_df.loc[idx, "قرار_الجودة"])
                m = st.text_area("المدير", a_df.loc[idx, "قرار_المدير"])
                if st.button("حفظ"):
                    a_df.loc[idx, "قرار_الجودة"], a_df.loc[idx, "قرار_المدير"] = q, m
                    a_df.to_csv(a_file, index=False); st.success("تم"); st.rerun()
        else:
            with st.form("ob_form"):
                f1, f2 = st.date_input("التاريخ"), st.text_input("التكت")
                f3 = st.selectbox("القسم", ["SWITCH", "MPLS", "Power"])
                f4 = st.text_area("التفاصيل")
                if st.form_submit_button("إرسال"):
                    new = {"الموظف": st.session_state.name, "التاريخ": str(f1), "رقم_التكت": f2, "القسم": f3, "التفاصيل": f4, "قرار_الجودة": "Pending", "قرار_المدير": "Pending", "وقت_إنشاء_الطلب": get_time()}
                    a_df = pd.concat([a_df, pd.DataFrame([new])], ignore_index=True)
                    a_df.to_csv(a_file, index=False); st.success("تم الإرسال"); st.rerun()

    if st.session_state.user == 'jsafaa':
        with t2:
            st.subheader("إدارة الحسابات")
            # هنا كود الحذف وتغيير الباسورد والإضافة
            c1, c2, c3 = st.columns(3)
            with c1:
                u_n, n_n = st.text_input("يوزر جديد"), st.text_input("اسم جديد")
                if st.button("إضافة"):
                    u_df = pd.concat([u_df, pd.DataFrame([{"username":u_n,"password":"123","name":n_n}])], ignore_index=True)
                    u_df.to_csv(u_file, index=False); st.success("تم")
            with c2:
                target = st.selectbox("تغيير باسورد", u_df['username'].values)
                p_n = st.text_input("باسورد جديد")
                if st.button("تحديث"):
                    u_df.loc[u_df['username'] == target, 'password'] = p_n
                    u_df.to_csv(u_file, index=False); st.success("تم")
            with c3:
                rem = st.selectbox("حذف موظف", [u for u in u_df['username'].values if u != 'jsafaa'])
                if st.button("حذف نهائي"):
                    u_df = u_df[u_df['username'] != rem]
                    u_df.to_csv(u_file, index=False); st.rerun()
