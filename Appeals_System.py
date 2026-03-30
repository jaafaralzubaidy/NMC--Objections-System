# --- ⚡ التحسين: تشفير كلمات المرور قبل تمريرها للمصادقة ---
if 'authenticator' not in st.session_state:
    credentials = {'usernames': {}}
    
    # تحضير قائمة كلمات المرور للتشفير
    passwords_to_hash = [str(row.password) for row in users_df.itertuples(index=False)]
    hashed_passwords = stauth.Hasher(passwords_to_hash).generate()
    
    # بناء القاموس باستخدام النسخ المشفرة
    for i, row in enumerate(users_df.itertuples(index=False)):
        credentials['usernames'][str(row.username)] = {
            'name': str(row.name),
            'password': hashed_passwords[i], # نستخدم كلمة المرور المشفرة هنا
            'role': str(row.role)
        }
    
    st.session_state.authenticator = stauth.Authenticate(
        credentials, 
        'nmc_objections_cookie', 
        'auth_key_123', 
        cookie_expiry_days=30
    )
