import streamlit as st
import sqlite3
import hashlib
import os
import shutil
import logging
from datetime import datetime, date, timezone, timedelta  # FIX 2: added timezone, timedelta

# ───────────────────────────────────────────────
# CONFIGURATION
# ───────────────────────────────────────────────
DB_FILE = "nmc_appeals.db"
BACKUP_DIR = "db_backups"
LOG_FILE = "system_audit.log"

QUALITY_MANAGER = "jsafaa"
SUPERVISORS = ["ahatim", "farook"]
ADMIN_ROLES = [QUALITY_MANAGER] + SUPERVISORS

DEFAULT_PASSWORD = "123"

# FIX 2: Iraq timezone UTC+3
IRAQ_TZ = timezone(timedelta(hours=3))
def now_iraq():
    return datetime.now(IRAQ_TZ).strftime("%Y-%m-%d %H:%M:%S")

KPI_LIST = [
    "Done Delay", "Done Delay Response", "High MTTD", "Shift Delay", "Ticket Not Add",
    "Wrong Action", "Delay In q", "High ASR Utlization", "Reduce Number Of Incident", "Delay High Impact", "Zabbix No Match", "Closing Issue", "Wrong Forward", "Wrong Action In Q Manager", "FMS", "Delay FMS", " Number Delay FMS", "No Task"
]

TAB_LIST = ["Bridges", "Earthlink Services", "IRQNBN", "Back Bone", "ITPC", "Metro", "Nas", "Power", "Baghdad Rings", "Server Room", "Switch State", "Wireless", "Al-watani Power", "Al-watani Services"]]

# ───────────────────────────────────────────────
# LOGGING SETUP
# ───────────────────────────────────────────────
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def audit_log(action: str, actor: str, details: str = ""):
    logging.info(f"ACTOR={actor} | ACTION={action} | {details}")

# ───────────────────────────────────────────────
# DATABASE INITIALIZATION
# ───────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            full_name     TEXT    DEFAULT '',
            role          TEXT    DEFAULT 'employee',
            supervisor    TEXT    DEFAULT '',
            force_change  INTEGER DEFAULT 1,
            created_at    TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS appeals (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            employee         TEXT NOT NULL,
            problem_date     TEXT NOT NULL,
            ticket_number    TEXT NOT NULL,
            tab              TEXT NOT NULL,
            kpi              TEXT NOT NULL,
            description      TEXT NOT NULL,
            submission_date  TEXT NOT NULL,
            quality_response TEXT DEFAULT '',
            manager_response TEXT DEFAULT '',
            status           TEXT DEFAULT 'Pending',
            created_at       TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (employee) REFERENCES users(username)
        )
    """)

    # ── Seed default admin & supervisor accounts ──
    default_accounts = [
        ("jsafaa",  "Safaa Al-Quality",  "quality_manager", ""),
        ("ahatim",  "Hatim Manager",     "supervisor",      ""),
        ("farook",  "Farook Manager",    "supervisor",      ""),
    ]
    for uname, fname, role, sup in default_accounts:
        c.execute("""
            INSERT OR IGNORE INTO users (username, password_hash, full_name, role, supervisor, force_change)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (uname, hash_password(DEFAULT_PASSWORD), fname, role, sup))

    conn.commit()
    conn.close()

# ───────────────────────────────────────────────
# USER OPERATIONS
# ───────────────────────────────────────────────
def authenticate(username: str, password: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[2] == hash_password(password):
        return {
            "id":           row[0],
            "username":     row[1],
            "full_name":    row[3],
            "role":         row[4],
            "supervisor":   row[5],
            "force_change": row[6],
        }
    return None

def update_password(username: str, new_password: str) -> bool:
    try:
        conn = get_conn()
        conn.execute("""
            UPDATE users SET password_hash = ?, force_change = 0
            WHERE username = ?
        """, (hash_password(new_password), username))
        conn.commit()
        conn.close()
        audit_log("PASSWORD_CHANGE", username)
        return True
    except Exception as e:
        audit_log("PASSWORD_CHANGE_ERROR", username, str(e))
        return False

def reset_password(target_user: str, actor: str) -> bool:
    try:
        conn = get_conn()
        conn.execute("""
            UPDATE users SET password_hash = ?, force_change = 1
            WHERE username = ?
        """, (hash_password(DEFAULT_PASSWORD), target_user))
        conn.commit()
        conn.close()
        audit_log("PASSWORD_RESET", actor, f"target={target_user}")
        return True
    except Exception as e:
        audit_log("PASSWORD_RESET_ERROR", actor, str(e))
        return False

def get_all_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, username, full_name, role, supervisor, force_change, created_at FROM users ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def add_user(username: str, full_name: str, role: str, supervisor: str, actor: str) -> bool:
    try:
        conn = get_conn()
        conn.execute("""
            INSERT INTO users (username, password_hash, full_name, role, supervisor, force_change)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (username.strip().lower(), hash_password(DEFAULT_PASSWORD), full_name.strip(), role, supervisor))
        conn.commit()
        conn.close()
        audit_log("USER_ADDED", actor, f"new_user={username}")
        return True
    except sqlite3.IntegrityError:
        return False

# FIX 1: delete_user — كان يرجع False لأي يوزر اسمه في ADMIN_ROLES
# السبب: الكود الأصلي صح منطقياً، لكن المشكلة في الـ UI —
# زر الحذف ما يظهر أصلاً إلا لو uname not in ADMIN_ROLES
# إذن المشكلة كانت أن الـ foreign key constraint يمنع الحذف
# لو في appeals مرتبطة بالـ user. الحل: نحذف appeals اليوزر أولاً.
def delete_user(username: str, actor: str) -> bool:
    if username in ADMIN_ROLES:
        return False
    try:
        conn = get_conn()
        conn.execute("DELETE FROM appeals WHERE employee = ?", (username,))
        conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        audit_log("USER_DELETED", actor, f"deleted={username}")
        return True
    except Exception as e:
        audit_log("USER_DELETE_ERROR", actor, str(e))
        return False

def get_employees_of_supervisor(supervisor: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT username, full_name FROM users WHERE supervisor = ?", (supervisor,))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

# ───────────────────────────────────────────────
# APPEAL OPERATIONS
# ───────────────────────────────────────────────
def submit_appeal(employee: str, problem_date: str, ticket: str,
                  tab: str, kpi: str, description: str) -> bool:
    try:
        conn = get_conn()
        conn.execute("""
            INSERT INTO appeals
              (employee, problem_date, ticket_number, tab, kpi, description, submission_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (employee, problem_date, ticket, tab, kpi, description,
              now_iraq()))  # FIX 2: توقيت العراق بدل توقيت السيرفر
        conn.commit()
        conn.close()
        audit_log("APPEAL_SUBMITTED", employee, f"ticket={ticket} kpi={kpi}")
        return True
    except Exception as e:
        audit_log("APPEAL_SUBMIT_ERROR", employee, str(e))
        return False

def get_my_appeals(username: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, problem_date, ticket_number, tab, kpi, description,
               submission_date, quality_response, manager_response, status
        FROM appeals WHERE employee = ? ORDER BY id DESC
    """, (username,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_appeals():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, employee, problem_date, ticket_number, tab, kpi, description,
               submission_date, quality_response, manager_response, status
        FROM appeals ORDER BY id DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def get_appeals_for_supervisor(supervisor: str):
    employees = get_employees_of_supervisor(supervisor)
    if not employees:
        return []
    conn = get_conn()
    c = conn.cursor()
    placeholders = ",".join("?" * len(employees))
    c.execute(f"""
        SELECT id, employee, problem_date, ticket_number, tab, kpi, description,
               submission_date, quality_response, manager_response, status
        FROM appeals WHERE employee IN ({placeholders}) ORDER BY id DESC
    """, employees)
    rows = c.fetchall()
    conn.close()
    return rows

def update_quality_response(appeal_id: int, response: str, actor: str) -> bool:
    try:
        conn = get_conn()
        conn.execute("""
            UPDATE appeals SET quality_response = ?, status = 'Reviewed by Quality'
            WHERE id = ?
        """, (response, appeal_id))
        conn.commit()
        conn.close()
        audit_log("QUALITY_RESPONSE", actor, f"appeal_id={appeal_id}")
        return True
    except Exception as e:
        audit_log("QUALITY_RESPONSE_ERROR", actor, str(e))
        return False

def update_manager_response(appeal_id: int, response: str, actor: str) -> bool:
    try:
        conn = get_conn()
        conn.execute("""
            UPDATE appeals SET manager_response = ?, status = 'Reviewed by Manager'
            WHERE id = ?
        """, (response, appeal_id))
        conn.commit()
        conn.close()
        audit_log("MANAGER_RESPONSE", actor, f"appeal_id={appeal_id}")
        return True
    except Exception as e:
        audit_log("MANAGER_RESPONSE_ERROR", actor, str(e))
        return False

# ───────────────────────────────────────────────
# DATABASE VIEWER (jsafaa only)
# ───────────────────────────────────────────────
def db_viewer_panel():
    st.markdown("---")
    st.subheader("Database Direct Access")

    tabs = st.tabs(["Users Table", "Appeals Table", "Run SQL Query", "Backup DB"])

    with tabs[0]:
        st.caption("All registered users")
        conn = get_conn()
        import pandas as pd
        df = pd.read_sql_query("SELECT id, username, full_name, role, supervisor, force_change, created_at FROM users", conn)
        conn.close()
        st.dataframe(df, use_container_width=True)

    with tabs[1]:
        st.caption("All appeals (never deleted)")
        conn = get_conn()
        import pandas as pd
        df2 = pd.read_sql_query("SELECT * FROM appeals ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(df2, use_container_width=True)
        csv = df2.to_csv(index=False).encode("utf-8")
        st.download_button("Download Appeals as CSV", csv, "appeals_export.csv", "text/csv")

    with tabs[2]:
        st.warning("Careful: only SELECT queries are recommended here.")
        raw_sql = st.text_area("SQL Query", value="SELECT * FROM appeals LIMIT 20;", height=120)
        if st.button("Execute Query"):
            try:
                conn = get_conn()
                import pandas as pd
                df3 = pd.read_sql_query(raw_sql, conn)
                conn.close()
                st.dataframe(df3, use_container_width=True)
            except Exception as e:
                st.error(f"SQL Error: {e}")

    with tabs[3]:
        st.caption("Create a backup copy of the database file")
        if st.button("Create Backup Now"):
            os.makedirs(BACKUP_DIR, exist_ok=True)
            ts = now_iraq().replace(":", "-").replace(" ", "_")  # FIX 2: توقيت العراق
            dest = os.path.join(BACKUP_DIR, f"nmc_appeals_{ts}.db")
            shutil.copy(DB_FILE, dest)
            audit_log("DB_BACKUP", QUALITY_MANAGER, f"file={dest}")
            st.success(f"Backup saved: {dest}")

        backup_files = sorted(os.listdir(BACKUP_DIR)) if os.path.exists(BACKUP_DIR) else []
        if backup_files:
            st.caption("Available backups:")
            for f in backup_files[::-1]:
                # FIX 3: زر تحميل لكل باك أب بدل st.text
                fpath = os.path.join(BACKUP_DIR, f)
                col1, col2 = st.columns([3, 1])
                col1.text(f)
                with open(fpath, "rb") as fdata:
                    col2.download_button(
                        label="⬇ Download",
                        data=fdata.read(),
                        file_name=f,
                        mime="application/octet-stream",
                        key=f"dl_{f}"
                    )

# ───────────────────────────────────────────────
# UI HELPERS
# ───────────────────────────────────────────────
def status_badge(status: str) -> str:
    colors = {
        "Pending":                 "#FFA500",
        "Reviewed by Quality":     "#1E90FF",
        "Reviewed by Manager":     "#32CD32",
    }
    color = colors.get(status, "#888888")
    return f'<span style="background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:12px;">{status}</span>'

def appeal_card(row, is_admin: bool = False, actor: str = "", panel: str = "quality"):
    """
    row columns (all appeals):
    0:id, 1:employee, 2:problem_date, 3:ticket, 4:tab, 5:kpi,
    6:description, 7:submission_date, 8:quality_response, 9:manager_response, 10:status
    """
    with st.expander(f"Appeal #{row[0]} | {row[1]} | Ticket: {row[3]} | {row[2]}"):
        col1, col2 = st.columns(2)
        col1.markdown(f"**Employee:** {row[1]}")
        col1.markdown(f"**Problem Date:** {row[2]}")
        col1.markdown(f"**Ticket #:** {row[3]}")
        col2.markdown(f"**Tab:** {row[4]}")
        col2.markdown(f"**KPI:** {row[5]}")
        col2.markdown(f"**Submitted:** {row[7]}")
        st.markdown(f"**Description:**\n\n{row[6]}")
        st.markdown(f"**Status:** {status_badge(row[10])}", unsafe_allow_html=True)

        if row[8]:
            st.info(f"**Quality Response:** {row[8]}")
        if row[9]:
            st.success(f"**Manager Response:** {row[9]}")

        if is_admin:
            st.markdown("---")
            if panel == "quality":
                resp = st.text_area(f"Quality Response for #{row[0]}", value=row[8] or "", key=f"qr_{row[0]}")
                if st.button(f"Save Quality Response #{row[0]}", key=f"qsave_{row[0]}"):
                    if update_quality_response(row[0], resp, actor):
                        st.success("Response saved.")
                    else:
                        st.error("Error saving response.")
            elif panel == "manager":
                resp = st.text_area(f"Manager Response for #{row[0]}", value=row[9] or "", key=f"mr_{row[0]}")
                if st.button(f"Save Manager Response #{row[0]}", key=f"msave_{row[0]}"):
                    if update_manager_response(row[0], resp, actor):
                        st.success("Response saved.")
                    else:
                        st.error("Error saving response.")

def my_appeal_card(row):
    """
    row columns (my appeals):
    0:id, 1:problem_date, 2:ticket, 3:tab, 4:kpi,
    5:description, 6:submission_date, 7:quality_response, 8:manager_response, 9:status
    """
    with st.expander(f"Appeal #{row[0]} | Ticket: {row[2]} | {row[1]}"):
        col1, col2 = st.columns(2)
        col1.markdown(f"**Problem Date:** {row[1]}")
        col1.markdown(f"**Ticket #:** {row[2]}")
        col2.markdown(f"**Tab:** {row[3]}")
        col2.markdown(f"**KPI:** {row[4]}")
        col2.markdown(f"**Submitted:** {row[6]}")
        st.markdown(f"**Description:**\n\n{row[5]}")
        st.markdown(f"**Status:** {status_badge(row[9])}", unsafe_allow_html=True)
        if row[7]:
            st.info(f"**Quality Response:** {row[7]}")
        if row[8]:
            st.success(f"**Manager Response:** {row[8]}")

# ───────────────────────────────────────────────
# PAGE: LOGIN
# ───────────────────────────────────────────────
def page_login():
    st.markdown("""
    <style>
        .login-box {max-width:420px; margin:auto; padding-top:80px;}
        h1 {text-align:center; color:#1a3c6e;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.markdown("## NMC Appeals System")
    st.markdown("Please log in to continue.")

    username = st.text_input("Username").strip().lower()
    password = st.text_input("Password", type="password")

    if st.button("Login", type="primary"):
        if not username or not password:
            st.error("Please fill in all fields.")
            return
        user = authenticate(username, password)
        if user:
            st.session_state["user"] = user
            audit_log("LOGIN", username)
        else:
            st.error("Invalid username or password.")
            audit_log("LOGIN_FAILED", username)
    st.markdown("</div>", unsafe_allow_html=True)

# ───────────────────────────────────────────────
# PAGE: FORCE CHANGE PASSWORD
# ───────────────────────────────────────────────
def page_force_change():
    user = st.session_state["user"]
    st.warning("You must change your password before continuing.")
    st.subheader("Set New Password")

    new_pw   = st.text_input("New Password", type="password")
    new_pw2  = st.text_input("Confirm New Password", type="password")

    if st.button("Change Password", type="primary"):
        if not new_pw or not new_pw2:
            st.error("Please fill both fields.")
        elif new_pw != new_pw2:
            st.error("Passwords do not match.")
        elif new_pw == DEFAULT_PASSWORD:
            st.error("New password cannot be the default password (123).")
        elif len(new_pw) < 4:
            st.error("Password must be at least 4 characters.")
        else:
            if update_password(user["username"], new_pw):
                st.session_state["user"]["force_change"] = 0
                st.success("Password changed successfully! Please continue.")
                st.rerun()
            else:
                st.error("Error saving new password. Please try again.")

# ───────────────────────────────────────────────
# PAGE: EMPLOYEE DASHBOARD
# ───────────────────────────────────────────────
def page_employee():
    user = st.session_state["user"]
    st.title(f"Welcome, {user['full_name'] or user['username']}")

    tab1, tab2, tab3 = st.tabs(["Submit Appeal", "My Appeals", "Change Password"])

    # ── TAB 1: Submit Appeal ──
    with tab1:
        st.subheader("Submit New Appeal")
        with st.form("appeal_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            problem_date = col1.date_input(
                "Problem Date",
                value=date.today(),
                max_value=date.today()
            )
            ticket_number = col2.text_input("Ticket Number")
            tab_sel  = col1.selectbox("Tab", TAB_LIST)
            kpi_sel  = col2.selectbox("KPI", KPI_LIST)
            sub_date = st.date_input(
                "Submission Date",
                value=date.today(),
                max_value=date.today()
            )
            description = st.text_area("Describe your problem in detail", height=150)
            submitted = st.form_submit_button("Submit Appeal", type="primary")

        if submitted:
            if not ticket_number.strip():
                st.error("Please enter the ticket number.")
            elif not description.strip():
                st.error("Please write a description.")
            else:
                ok = submit_appeal(
                    employee=user["username"],
                    problem_date=str(problem_date),
                    ticket=ticket_number.strip(),
                    tab=tab_sel,
                    kpi=kpi_sel,
                    description=description.strip()
                )
                if ok:
                    st.success("Appeal submitted successfully and saved permanently.")
                else:
                    st.error("Error submitting appeal. Please try again.")

    # ── TAB 2: My Appeals ──
    with tab2:
        st.subheader("My Appeals")
        appeals = get_my_appeals(user["username"])
        if not appeals:
            st.info("You have not submitted any appeals yet.")
        else:
            st.caption(f"Total: {len(appeals)} appeal(s)")
            for row in appeals:
                my_appeal_card(row)

    # ── TAB 3: Change Password ──
    with tab3:
        st.subheader("Change My Password")
        old_pw  = st.text_input("Current Password", type="password", key="emp_old")
        new_pw  = st.text_input("New Password",     type="password", key="emp_new")
        new_pw2 = st.text_input("Confirm Password", type="password", key="emp_new2")
        if st.button("Update Password", key="emp_upd"):
            if not authenticate(user["username"], old_pw):
                st.error("Current password is incorrect.")
            elif new_pw != new_pw2:
                st.error("New passwords do not match.")
            elif len(new_pw) < 4:
                st.error("Password must be at least 4 characters.")
            elif new_pw == DEFAULT_PASSWORD:
                st.error("Cannot use the default password.")
            else:
                if update_password(user["username"], new_pw):
                    st.success("Password updated successfully.")
                else:
                    st.error("Error updating password.")

# ───────────────────────────────────────────────
# PAGE: SUPERVISOR DASHBOARD
# ───────────────────────────────────────────────
def page_supervisor():
    user = st.session_state["user"]
    st.title(f"Supervisor Panel - {user['full_name'] or user['username']}")

    tab1, tab2 = st.tabs(["Team Appeals", "Change My Password"])

    with tab1:
        st.subheader("My Team's Appeals")
        appeals = get_appeals_for_supervisor(user["username"])
        if not appeals:
            st.info("No appeals found for your team yet.")
        else:
            st.caption(f"Total: {len(appeals)} appeal(s)")
            for row in appeals:
                appeal_card(row, is_admin=True, actor=user["username"], panel="manager")

    with tab2:
        st.subheader("Change My Password")
        old_pw  = st.text_input("Current Password", type="password", key="sup_old")
        new_pw  = st.text_input("New Password",     type="password", key="sup_new")
        new_pw2 = st.text_input("Confirm Password", type="password", key="sup_new2")
        if st.button("Update Password", key="sup_upd"):
            if not authenticate(user["username"], old_pw):
                st.error("Current password is incorrect.")
            elif new_pw != new_pw2:
                st.error("Passwords do not match.")
            elif len(new_pw) < 4:
                st.error("Password must be at least 4 characters.")
            else:
                if update_password(user["username"], new_pw):
                    st.success("Password updated successfully.")
                else:
                    st.error("Error updating password.")

# ───────────────────────────────────────────────
# PAGE: QUALITY MANAGER DASHBOARD (jsafaa)
# ───────────────────────────────────────────────
def page_quality_manager():
    user = st.session_state["user"]
    st.title(f"Quality Manager Panel - {user['full_name'] or user['username']}")

    tab1, tab2, tab3, tab4 = st.tabs([
        "All Appeals",
        "User Management",
        "Database Access",
        "Change My Password"
    ])

    # ── TAB 1: All Appeals ──
    with tab1:
        st.subheader("All Employee Appeals")
        appeals = get_all_appeals()
        if not appeals:
            st.info("No appeals submitted yet.")
        else:
            # Filter controls
            col1, col2, col3 = st.columns(3)
            employees   = list(set(r[1] for r in appeals))
            kpis        = list(set(r[5] for r in appeals))
            statuses    = list(set(r[10] for r in appeals))

            f_emp    = col1.selectbox("Filter by Employee", ["All"] + sorted(employees))
            f_kpi    = col2.selectbox("Filter by KPI",      ["All"] + sorted(kpis))
            f_status = col3.selectbox("Filter by Status",   ["All"] + sorted(statuses))

            filtered = appeals
            if f_emp    != "All": filtered = [r for r in filtered if r[1]  == f_emp]
            if f_kpi    != "All": filtered = [r for r in filtered if r[5]  == f_kpi]
            if f_status != "All": filtered = [r for r in filtered if r[10] == f_status]

            st.caption(f"Showing {len(filtered)} of {len(appeals)} appeal(s)")
            for row in filtered:
                appeal_card(row, is_admin=True, actor=user["username"], panel="quality")

    # ── TAB 2: User Management ──
    with tab2:
        st.subheader("User Management")

        st.markdown("### Add New Employee")
        with st.form("add_user_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            new_uname  = c1.text_input("Username (login ID)")
            new_fname  = c2.text_input("Full Name")
            new_role   = c1.selectbox("Role", ["employee", "supervisor", "quality_manager"])
            new_sup    = c2.selectbox(
                "Assign to Supervisor",
                [""] + SUPERVISORS,
                help="Leave blank for supervisors/admins"
            )
            add_submitted = st.form_submit_button("Add User", type="primary")

        if add_submitted:
            if not new_uname.strip():
                st.error("Username cannot be empty.")
            else:
                ok = add_user(new_uname, new_fname, new_role, new_sup, user["username"])
                if ok:
                    st.success(f"User '{new_uname}' added with default password: 123")
                else:
                    st.error(f"Username '{new_uname}' already exists.")

        st.markdown("---")
        st.markdown("### Manage Existing Users")
        all_users = get_all_users()
        if all_users:
            for u in all_users:
                uid, uname, fname, role, sup, fc, created = u
                with st.expander(f"{uname} | {fname} | Role: {role} | Supervisor: {sup or 'None'}"):
                    st.markdown(f"**Created:** {created}")
                    st.markdown(f"**Force Change Password:** {'Yes' if fc else 'No'}")

                    col_a, col_b = st.columns(2)
                    # Reset password
                    if col_a.button(f"Reset Password to 123", key=f"rst_{uid}"):
                        if uname == user["username"]:
                            col_a.warning("Cannot reset your own password here.")
                        elif reset_password(uname, user["username"]):
                            col_a.success(f"Password reset for {uname}")
                        else:
                            col_a.error("Error resetting password.")

                    # Delete user (protected accounts cannot be deleted)
                    if uname not in ADMIN_ROLES:
                        if col_b.button(f"Delete User", key=f"del_{uid}", type="secondary"):
                            if delete_user(uname, user["username"]):
                                col_b.success(f"User '{uname}' deleted.")
                                st.rerun()
                            else:
                                col_b.error("Error deleting user.")
                    else:
                        col_b.markdown("*(Protected Account)*")

    # ── TAB 3: Database Access ──
    with tab3:
        db_viewer_panel()

    # ── TAB 4: Change My Password ──
    with tab4:
        st.subheader("Change My Password")
        old_pw  = st.text_input("Current Password", type="password", key="qm_old")
        new_pw  = st.text_input("New Password",     type="password", key="qm_new")
        new_pw2 = st.text_input("Confirm Password", type="password", key="qm_new2")
        if st.button("Update Password", key="qm_upd"):
            if not authenticate(user["username"], old_pw):
                st.error("Current password is incorrect.")
            elif new_pw != new_pw2:
                st.error("Passwords do not match.")
            elif len(new_pw) < 4:
                st.error("Password must be at least 4 characters.")
            else:
                if update_password(user["username"], new_pw):
                    st.success("Password updated successfully.")
                else:
                    st.error("Error updating password.")

# ───────────────────────────────────────────────
# MAIN APP
# ───────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="NMC Appeals System",
        page_icon="favicon.ico",
        layout="wide"
    )

    # Initialize DB on every startup (safe, uses IF NOT EXISTS)
    init_db()

    # ── Sidebar: Logout ──
    if "user" in st.session_state:
        with st.sidebar:
            u = st.session_state["user"]
            st.markdown(f"**Logged in as:** {u['username']}")
            st.markdown(f"**Role:** {u['role']}")
            st.markdown("---")
            if st.button("Logout"):
                audit_log("LOGOUT", u["username"])
                st.session_state.clear()
                st.rerun()

    # ── Routing ──
    if "user" not in st.session_state:
        page_login()
        return

    user = st.session_state["user"]

    # Force password change on first login
    if user["force_change"]:
        page_force_change()
        return

    # Route by role
    role = user["role"]
    if role == "quality_manager":
        page_quality_manager()
    elif role == "supervisor":
        page_supervisor()
    else:
        page_employee()


if __name__ == "__main__":
    main()
