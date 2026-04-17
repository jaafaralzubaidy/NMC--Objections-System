import streamlit as st
import sqlite3
import hashlib
import os
import shutil
import logging
from datetime import datetime, date

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

KPI_LIST = [
    "AHT", "ACW", "CSAT", "FCR", "Adherence",
    "Quality Score", "Attendance", "SLA", "Other"
]

TAB_LIST = ["Calls", "Chats", "Emails", "Callbacks", "Other"]

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

def delete_user(username: str, actor: str) -> bool:
    if username in ADMIN_ROLES:
        return False
    try:
        conn = get_conn()
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
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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
        FROM appeals WHERE employee = ?
        ORDER BY id DESC
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
# DATABASE VIEWER
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
                df3 = pd.read_sql_query(raw_sql, conn)
                conn.close()
                st.dataframe(df3, use_container_width=True)
            except Exception as e:
                st.error(f"SQL Error: {e}")

    with tabs[3]:
        st.caption("Create a backup copy of the database file")
        if st.button("Create Backup Now"):
            os.makedirs(BACKUP_DIR, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = os.path.join(BACKUP_DIR, f"nmc_appeals_{ts}.db")
            shutil.copy(DB_FILE, dest)
            audit_log("DB_BACKUP", QUALITY_MANAGER, f"file={dest}")
            st.success(f"Backup saved: {dest}")

        backup_files = sorted(os.listdir(BACKUP_DIR)) if os.path.exists(BACKUP_DIR) else []
        if backup_files:
            st.caption("Available
