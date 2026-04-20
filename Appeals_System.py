import streamlit as st
import sqlite3
import hashlib
import os
import shutil
import logging
from datetime import datetime, date, timezone, timedelta

# ───────────────────────────────────────────────
# CONFIGURATION
# ───────────────────────────────────────────────
DB_FILE = "nmc_appeals.db"
BACKUP_DIR = "db_backups"
LOG_FILE = "system_audit.log"

QUALITY_MANAGER  = "jsafaa"
SUPERVISORS      = ["ahatim", "farook"]
GENERAL_MANAGER  = "rsamim"                          # المدير الكبير الجديد
ADMIN_ROLES      = [QUALITY_MANAGER] + SUPERVISORS   # محمية من الحذف
ALL_MGMT         = ADMIN_ROLES + [GENERAL_MANAGER]   # كل الإدارة

DEFAULT_PASSWORD = "123"

# Iraq timezone UTC+3
IRAQ_TZ = timezone(timedelta(hours=3))
def now_iraq():
    return datetime.now(IRAQ_TZ).strftime("%Y-%m-%d %H:%M:%S")

def today_iraq():
    return datetime.now(IRAQ_TZ).strftime("%Y-%m-%d")

KPI_LIST = [
    "Done Delay", "Done Delay Response", "High MTTD", "Shift Delay", "Ticket Not Add",
    "Wrong Action", "Delay In q", "High ASR Utlization", "Reduce Number Of Incident",
    "Delay High Impact", "Zabbix No Match", "Closing Issue", "Wrong Forward",
    "Wrong Action In Q Manager", "FMS", "Delay FMS", " Number Delay FMS", "No Task"
]

TAB_LIST = [
    "Bridges", "Earthlink Services", "IRQNBN", "Back Bone", "ITPC", "Metro",
    "Nas", "Power", "Baghdad Rings", "Server Room", "Switch State", "Wireless",
    "Al-watani Power", "Al-watani Services"
]

# ── منطق الحالة (Status) ──
# Pending                  → لم يُراجَع بعد
# Quality: Approved        → jsafaa وافقت، بانتظار السوبرفايزر
# Quality: Rejected        → jsafaa رفضت، بانتظار السوبرفايزر
# Approved                 → كلا الجانبين وافقا (أو المدير الكبير وافق)
# Rejected                 → كلا الجانبين رفضا (أو المدير الكبير رفض)
# Escalated to GM          → اختلاف في القرار، بانتظار rsamim

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
# AUTO DAILY BACKUP
# ───────────────────────────────────────────────
def auto_daily_backup():
    try:
        if not os.path.exists(DB_FILE):
            return
        os.makedirs(BACKUP_DIR, exist_ok=True)
        today = today_iraq()
        existing = os.listdir(BACKUP_DIR)
        already_backed_up = any(f.startswith(f"auto_{today}") for f in existing)
        if not already_backed_up:
            ts   = now_iraq().replace(":", "-").replace(" ", "_")
            dest = os.path.join(BACKUP_DIR, f"auto_{today}_{ts}.db")
            shutil.copy(DB_FILE, dest)
            audit_log("AUTO_BACKUP", "system", f"file={dest}")
            all_backups = sorted(
                [f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")], reverse=True
            )
            for old in all_backups[30:]:
                os.remove(os.path.join(BACKUP_DIR, old))
    except Exception as e:
        audit_log("AUTO_BACKUP_ERROR", "system", str(e))

def get_todays_backup_path():
    today = today_iraq()
    if not os.path.exists(BACKUP_DIR):
        return None, None
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if f.startswith(f"auto_{today}") and f.endswith(".db"):
            return os.path.join(BACKUP_DIR, f), f
    return None, None

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

    # ── أضف عمود quality_decision و manager_decision إذا ما موجودين ──
    # (للتوافق مع قواعد بيانات قديمة)
    for col, default in [
        ("quality_decision",  "''"),
        ("manager_decision",  "''"),
        ("gm_decision",       "''"),
        ("gm_response",       "''"),
    ]:
        try:
            c.execute(f"ALTER TABLE appeals ADD COLUMN {col} TEXT DEFAULT {default}")
        except Exception:
            pass  # العمود موجود مسبقاً

    c.execute("""
        CREATE TABLE IF NOT EXISTS appeals (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            employee          TEXT NOT NULL,
            problem_date      TEXT NOT NULL,
            ticket_number     TEXT NOT NULL,
            tab               TEXT NOT NULL,
            kpi               TEXT NOT NULL,
            description       TEXT NOT NULL,
            submission_date   TEXT NOT NULL,
            quality_response  TEXT DEFAULT '',
            quality_decision  TEXT DEFAULT '',
            manager_response  TEXT DEFAULT '',
            manager_decision  TEXT DEFAULT '',
            gm_response       TEXT DEFAULT '',
            gm_decision       TEXT DEFAULT '',
            status            TEXT DEFAULT 'Pending',
            created_at        TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (employee) REFERENCES users(username)
        )
    """)

    # ── Seed accounts ──
    default_accounts = [
        ("jsafaa",  "Safaa Al-Quality",   "quality_manager",  ""),
        ("ahatim",  "Hatim Manager",      "supervisor",       ""),
        ("farook",  "Farook Manager",     "supervisor",       ""),
        ("rsamim",  "Samim Al-General",   "general_manager",  ""),
    ]
    for uname, fname, role, sup in default_accounts:
        c.execute("""
            INSERT OR IGNORE INTO users (username, password_hash, full_name, role, supervisor, force_change)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (uname, hash_password(DEFAULT_PASSWORD), fname, role, sup))

    conn.commit()
    conn.close()

# ───────────────────────────────────────────────
# HELPER: حساب الـ status بناءً على القرارات
# ───────────────────────────────────────────────
def compute_status(quality_decision: str, manager_decision: str, gm_decision: str) -> str:
    """
    قواعد الحالة:
    - لو GM اتخذ قرار → قراره هو النهائي
    - لو كلا القرارين موجودين ومتطابقين → النتيجة النهائية
    - لو كلا القرارين موجودين ومختلفين → Escalated to GM
    - لو واحد بس موجود → نعرض من وين جاء
    - لو لا شيء → Pending
    """
    qd = (quality_decision or "").strip()
    md = (manager_decision or "").strip()
    gd = (gm_decision or "").strip()

    if gd in ("Approved", "Rejected"):
        return f"GM Decision: {gd}"

    if qd and md:
        if qd == md:
            return qd           # "Approved" أو "Rejected"
        else:
            return "Escalated to GM"

    if qd:
        return f"Quality: {qd}"
    if md:
        return f"Manager: {md}"

    return "Pending"

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
        conn.execute("UPDATE users SET password_hash=?, force_change=0 WHERE username=?",
                     (hash_password(new_password), username))
        conn.commit(); conn.close()
        audit_log("PASSWORD_CHANGE", username)
        return True
    except Exception as e:
        audit_log("PASSWORD_CHANGE_ERROR", username, str(e))
        return False

def reset_password(target_user: str, actor: str) -> bool:
    try:
        conn = get_conn()
        conn.execute("UPDATE users SET password_hash=?, force_change=1 WHERE username=?",
                     (hash_password(DEFAULT_PASSWORD), target_user))
        conn.commit(); conn.close()
        audit_log("PASSWORD_RESET", actor, f"target={target_user}")
        return True
    except Exception as e:
        audit_log("PASSWORD_RESET_ERROR", actor, str(e))
        return False

def get_all_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, username, full_name, role, supervisor, force_change, created_at FROM users ORDER BY created_at DESC")
    rows = c.fetchall(); conn.close()
    return rows

def add_user(username: str, full_name: str, role: str, supervisor: str, actor: str) -> bool:
    try:
        conn = get_conn()
        conn.execute("""
            INSERT INTO users (username, password_hash, full_name, role, supervisor, force_change)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (username.strip().lower(), hash_password(DEFAULT_PASSWORD), full_name.strip(), role, supervisor))
        conn.commit(); conn.close()
        audit_log("USER_ADDED", actor, f"new_user={username}")
        return True
    except sqlite3.IntegrityError:
        return False

def delete_user(username: str, actor: str) -> bool:
    if username in ALL_MGMT:
        return False
    try:
        conn = get_conn()
        conn.execute("DELETE FROM appeals WHERE employee=?", (username,))
        conn.execute("DELETE FROM users WHERE username=?", (username,))
        conn.commit(); conn.close()
        audit_log("USER_DELETED", actor, f"deleted={username}")
        return True
    except Exception as e:
        audit_log("USER_DELETE_ERROR", actor, str(e))
        return False

def get_employees_of_supervisor(supervisor: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE supervisor=?", (supervisor,))
    rows = c.fetchall(); conn.close()
    return [r[0] for r in rows]

# ───────────────────────────────────────────────
# APPEAL OPERATIONS
# ───────────────────────────────────────────────
def submit_appeal(employee, problem_date, ticket, tab, kpi, description) -> bool:
    try:
        conn = get_conn()
        conn.execute("""
            INSERT INTO appeals
              (employee, problem_date, ticket_number, tab, kpi, description, submission_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (employee, problem_date, ticket, tab, kpi, description, now_iraq()))
        conn.commit(); conn.close()
        audit_log("APPEAL_SUBMITTED", employee, f"ticket={ticket} kpi={kpi}")
        return True
    except Exception as e:
        audit_log("APPEAL_SUBMIT_ERROR", employee, str(e))
        return False

def _fetch_appeals(query, params=()):
    conn = get_conn()
    c = conn.cursor()
    c.execute(query, params)
    rows = c.fetchall(); conn.close()
    return rows

def get_my_appeals(username: str):
    return _fetch_appeals("""
        SELECT id, problem_date, ticket_number, tab, kpi, description,
               submission_date, quality_response, quality_decision,
               manager_response, manager_decision,
               gm_response, gm_decision, status
        FROM appeals WHERE employee=? ORDER BY id DESC
    """, (username,))

def get_all_appeals():
    return _fetch_appeals("""
        SELECT id, employee, problem_date, ticket_number, tab, kpi, description,
               submission_date, quality_response, quality_decision,
               manager_response, manager_decision,
               gm_response, gm_decision, status
        FROM appeals ORDER BY id DESC
    """)

def get_appeals_for_supervisor(supervisor: str):
    employees = get_employees_of_supervisor(supervisor)
    if not employees:
        return []
    ph = ",".join("?" * len(employees))
    return _fetch_appeals(f"""
        SELECT id, employee, problem_date, ticket_number, tab, kpi, description,
               submission_date, quality_response, quality_decision,
               manager_response, manager_decision,
               gm_response, gm_decision, status
        FROM appeals WHERE employee IN ({ph}) ORDER BY id DESC
    """, employees)

def get_escalated_appeals():
    """الاعتراضات المحالة للمدير الكبير (فيها خلاف)"""
    return _fetch_appeals("""
        SELECT id, employee, problem_date, ticket_number, tab, kpi, description,
               submission_date, quality_response, quality_decision,
               manager_response, manager_decision,
               gm_response, gm_decision, status
        FROM appeals WHERE status='Escalated to GM' ORDER BY id DESC
    """)

def save_quality_decision(appeal_id: int, response: str, decision: str, actor: str) -> bool:
    try:
        conn = get_conn()
        # احسب الـ status الجديد
        c = conn.cursor()
        c.execute("SELECT manager_decision, gm_decision FROM appeals WHERE id=?", (appeal_id,))
        row = c.fetchone()
        md = row[0] if row else ""
        gd = row[1] if row else ""
        new_status = compute_status(decision, md, gd)

        conn.execute("""
            UPDATE appeals
            SET quality_response=?, quality_decision=?, status=?
            WHERE id=?
        """, (response, decision, new_status, appeal_id))
        conn.commit(); conn.close()
        audit_log("QUALITY_DECISION", actor, f"appeal_id={appeal_id} decision={decision}")
        return True
    except Exception as e:
        audit_log("QUALITY_DECISION_ERROR", actor, str(e))
        return False

def save_manager_decision(appeal_id: int, response: str, decision: str, actor: str) -> bool:
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT quality_decision, gm_decision FROM appeals WHERE id=?", (appeal_id,))
        row = c.fetchone()
        qd = row[0] if row else ""
        gd = row[1] if row else ""
        new_status = compute_status(qd, decision, gd)

        conn.execute("""
            UPDATE appeals
            SET manager_response=?, manager_decision=?, status=?
            WHERE id=?
        """, (response, decision, new_status, appeal_id))
        conn.commit(); conn.close()
        audit_log("MANAGER_DECISION", actor, f"appeal_id={appeal_id} decision={decision}")
        return True
    except Exception as e:
        audit_log("MANAGER_DECISION_ERROR", actor, str(e))
        return False

def save_gm_decision(appeal_id: int, response: str, decision: str, actor: str) -> bool:
    try:
        conn = get_conn()
        new_status = compute_status("", "", decision)   # GM قرار نهائي
        conn.execute("""
            UPDATE appeals
            SET gm_response=?, gm_decision=?, status=?
            WHERE id=?
        """, (response, decision, new_status, appeal_id))
        conn.commit(); conn.close()
        audit_log("GM_DECISION", actor, f"appeal_id={appeal_id} decision={decision}")
        return True
    except Exception as e:
        audit_log("GM_DECISION_ERROR", actor, str(e))
        return False

# ───────────────────────────────────────────────
# DATABASE VIEWER (jsafaa only)
# ───────────────────────────────────────────────
def db_viewer_panel():
    st.markdown("---")
    st.subheader("Database Direct Access")

    tabs = st.tabs(["Users Table", "Appeals Table", "Run SQL Query", "Backup DB", "Restore DB"])

    with tabs[0]:
        st.caption("All registered users")
        conn = get_conn()
        import pandas as pd
        df = pd.read_sql_query(
            "SELECT id, username, full_name, role, supervisor, force_change, created_at FROM users", conn)
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
        st.info(
            "🔄 **Auto Backup Active:** Daily backup runs on every app start (Iraq time). "
            f"Last 30 backups kept. Today: {today_iraq()}"
        )
        today_path, today_fname = get_todays_backup_path()
        if today_path and os.path.exists(today_path):
            st.markdown("### ⬇️ Download Today's Backup")
            with open(today_path, "rb") as f:
                st.download_button(
                    label=f"📥 Download Today's Backup — {today_iraq()}",
                    data=f.read(), file_name=today_fname,
                    mime="application/octet-stream",
                    key="dl_today", type="primary", use_container_width=True,
                )
        else:
            st.warning("⚠️ Today's auto backup not found yet. Restart the app to generate it.")

        st.markdown("---")
        st.caption("Or create a manual backup anytime:")
        if st.button("Create Manual Backup Now"):
            os.makedirs(BACKUP_DIR, exist_ok=True)
            ts   = now_iraq().replace(":", "-").replace(" ", "_")
            dest = os.path.join(BACKUP_DIR, f"manual_{ts}.db")
            shutil.copy(DB_FILE, dest)
            audit_log("DB_BACKUP_MANUAL", QUALITY_MANAGER, f"file={dest}")
            st.success(f"Manual backup saved: {dest}")

        st.markdown("---")
        backup_files = sorted(os.listdir(BACKUP_DIR)) if os.path.exists(BACKUP_DIR) else []
        if backup_files:
            st.caption(f"All available backups ({len(backup_files)}) — 🟢 auto | 🔵 manual:")
            for f in backup_files[::-1]:
                fpath = os.path.join(BACKUP_DIR, f)
                col1, col2 = st.columns([3, 1])
                col1.text(("🟢 " if f.startswith("auto_") else "🔵 ") + f)
                with open(fpath, "rb") as fd:
                    col2.download_button("⬇ Download", fd.read(), file_name=f,
                                         mime="application/octet-stream", key=f"dl_{f}")
        else:
            st.info("No backups yet.")

    with tabs[4]:
        st.error(
            "⚠️ DANGER ZONE — Restoring will completely replace the current database. "
            "A safety backup is created automatically before any restore."
        )
        st.markdown("### 🗂️ Restore from a Saved Backup")
        backup_files = sorted(os.listdir(BACKUP_DIR)) if os.path.exists(BACKUP_DIR) else []
        if not backup_files:
            st.info("No backup files found.")
        else:
            sel = st.selectbox("Choose backup:",
                               options=backup_files[::-1],
                               format_func=lambda f: ("🟢 " if f.startswith("auto_") else "🔵 ") + f)
            confirm = st.text_input("", placeholder="Type CONFIRM here", key="restore_confirm")
            ready = confirm.strip().upper() == "CONFIRM"
            if st.button(f"🔄 Restore from: {sel}",
                         disabled=not ready,
                         type="primary" if ready else "secondary",
                         key="restore_btn"):
                try:
                    st_ts   = now_iraq().replace(":", "-").replace(" ", "_")
                    safety  = os.path.join(BACKUP_DIR, f"pre_restore_{st_ts}.db")
                    shutil.copy(DB_FILE, safety)
                    shutil.copy(os.path.join(BACKUP_DIR, sel), DB_FILE)
                    audit_log("DB_RESTORED", QUALITY_MANAGER, f"from={sel}")
                    st.success(f"✅ Restored from {sel}. Safety backup: {os.path.basename(safety)}")
                    st.warning("Press F5 to refresh the page.")
                except Exception as e:
                    st.error(f"❌ Restore failed: {e}")

        st.markdown("---")
        st.markdown("### 💻 Restore from an Uploaded File")
        up = st.file_uploader("Upload .db file", type=["db"], key="restore_upload")
        if up:
            confirm2 = st.text_input("", placeholder="Type CONFIRM here", key="restore_upload_confirm")
            ready2 = confirm2.strip().upper() == "CONFIRM"
            if st.button("🔄 Restore from Uploaded File",
                         disabled=not ready2,
                         type="primary" if ready2 else "secondary",
                         key="restore_upload_btn"):
                try:
                    st_ts  = now_iraq().replace(":", "-").replace(" ", "_")
                    safety = os.path.join(BACKUP_DIR, f"pre_restore_{st_ts}.db")
                    os.makedirs(BACKUP_DIR, exist_ok=True)
                    shutil.copy(DB_FILE, safety)
                    with open(DB_FILE, "wb") as out:
                        out.write(up.read())
                    audit_log("DB_RESTORED_FROM_UPLOAD", QUALITY_MANAGER, f"file={up.name}")
                    st.success(f"✅ Restored from {up.name}. Safety backup: {os.path.basename(safety)}")
                    st.warning("Press F5 to refresh the page.")
                except Exception as e:
                    st.error(f"❌ Restore failed: {e}")

# ───────────────────────────────────────────────
# UI HELPERS
# ───────────────────────────────────────────────
def status_badge(status: str) -> str:
    colors = {
        "Pending":            "#888888",
        "Escalated to GM":    "#9B59B6",
        "Approved":           "#27AE60",
        "Rejected":           "#E74C3C",
    }
    # قرارات جزئية أو GM
    for key in ["Quality:", "Manager:", "GM Decision:"]:
        if status.startswith(key):
            if "Approved" in status:
                color = "#2E86AB"
            else:
                color = "#E67E22"
            return f'<span style="background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:12px;">{status}</span>'

    color = colors.get(status, "#888888")
    return f'<span style="background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:12px;">{status}</span>'

def decision_badge(decision: str) -> str:
    if decision == "Approved":
        return "✅ Approved"
    elif decision == "Rejected":
        return "❌ Rejected"
    return "⏳ Pending"

# ── Appeal card للـ all_appeals / supervisor (15 أعمدة مع employee) ──
# cols: 0:id 1:employee 2:prob_date 3:ticket 4:tab 5:kpi 6:desc
#       7:sub_date 8:q_resp 9:q_dec 10:m_resp 11:m_dec
#       12:gm_resp 13:gm_dec 14:status
def appeal_card(row, is_admin=False, actor="", panel="quality"):
    status_text = row[14]
    with st.expander(f"Appeal #{row[0]} | {row[1]} | Ticket: {row[3]} | {row[2]} | {status_text}"):
        col1, col2 = st.columns(2)
        col1.markdown(f"**Employee:** {row[1]}")
        col1.markdown(f"**Problem Date:** {row[2]}")
        col1.markdown(f"**Ticket #:** {row[3]}")
        col2.markdown(f"**Tab:** {row[4]}")
        col2.markdown(f"**KPI:** {row[5]}")
        col2.markdown(f"**Submitted:** {row[7]}")
        st.markdown(f"**Description:**\n\n{row[6]}")
        st.markdown(f"**Status:** {status_badge(row[14])}", unsafe_allow_html=True)

        # عرض القرارات الموجودة
        if row[8] or row[9]:
            st.info(f"**Quality Response:** {row[8]}  |  Decision: {decision_badge(row[9])}")
        if row[10] or row[11]:
            st.info(f"**Manager Response:** {row[10]}  |  Decision: {decision_badge(row[11])}")
        if row[12] or row[13]:
            st.success(f"**GM Final Decision:** {decision_badge(row[13])}  |  Note: {row[12]}")

        if not is_admin:
            return

        st.markdown("---")

        # ── لوحة Quality Manager ──
        if panel == "quality":
            st.markdown("**Your Decision (Quality Manager):**")
            current_dec = row[9] or ""
            dec = st.radio(
                "Decision", ["Approved", "Rejected"],
                index=0 if current_dec != "Rejected" else 1,
                key=f"qdec_{row[0]}",
                horizontal=True
            )
            resp = st.text_area("Quality Notes (optional)",
                                value=row[8] or "", key=f"qresp_{row[0]}")
            if st.button(f"💾 Save Quality Decision #{row[0]}", key=f"qsave_{row[0]}"):
                if save_quality_decision(row[0], resp, dec, actor):
                    st.success(f"Saved: {dec}")
                    st.rerun()
                else:
                    st.error("Error saving.")

        # ── لوحة Supervisor ──
        elif panel == "manager":
            st.markdown("**Your Decision (Supervisor):**")
            current_dec = row[11] or ""
            dec = st.radio(
                "Decision", ["Approved", "Rejected"],
                index=0 if current_dec != "Rejected" else 1,
                key=f"mdec_{row[0]}",
                horizontal=True
            )
            resp = st.text_area("Manager Notes (optional)",
                                value=row[10] or "", key=f"mresp_{row[0]}")
            if st.button(f"💾 Save Manager Decision #{row[0]}", key=f"msave_{row[0]}"):
                if save_manager_decision(row[0], resp, dec, actor):
                    st.success(f"Saved: {dec}")
                    st.rerun()
                else:
                    st.error("Error saving.")

# ── Appeal card للـ GM (نفس الأعمدة) ──
def gm_appeal_card(row, actor=""):
    with st.expander(f"Appeal #{row[0]} | {row[1]} | Ticket: {row[3]} | {row[2]}"):
        col1, col2 = st.columns(2)
        col1.markdown(f"**Employee:** {row[1]}")
        col1.markdown(f"**Problem Date:** {row[2]}")
        col1.markdown(f"**Ticket #:** {row[3]}")
        col2.markdown(f"**Tab:** {row[4]}")
        col2.markdown(f"**KPI:** {row[5]}")
        col2.markdown(f"**Submitted:** {row[7]}")
        st.markdown(f"**Description:**\n\n{row[6]}")
        st.markdown(f"**Status:** {status_badge(row[14])}", unsafe_allow_html=True)

        st.info(f"**Quality Decision:** {decision_badge(row[9])}  |  Notes: {row[8] or '—'}")
        st.info(f"**Manager Decision:** {decision_badge(row[11])}  |  Notes: {row[10] or '—'}")

        if row[13]:
            st.success(f"**Your Previous Decision:** {decision_badge(row[13])}  |  {row[12]}")

        st.markdown("---")
        st.markdown("**⚖️ Your Final Decision (General Manager):**")
        current_gm = row[13] or ""
        dec = st.radio(
            "Final Decision", ["Approved", "Rejected"],
            index=0 if current_gm != "Rejected" else 1,
            key=f"gmdec_{row[0]}",
            horizontal=True
        )
        resp = st.text_area("GM Notes (optional)", value=row[12] or "", key=f"gmresp_{row[0]}")
        if st.button(f"💾 Save Final Decision #{row[0]}", key=f"gmsave_{row[0]}", type="primary"):
            if save_gm_decision(row[0], resp, dec, actor):
                st.success(f"Final decision saved: {dec}")
                st.rerun()
            else:
                st.error("Error saving.")

# ── Appeal card للموظف (13 عمود بدون employee) ──
# cols: 0:id 1:prob_date 2:ticket 3:tab 4:kpi 5:desc
#       6:sub_date 7:q_resp 8:q_dec 9:m_resp 10:m_dec
#       11:gm_resp 12:gm_dec 13:status
def my_appeal_card(row):
    with st.expander(f"Appeal #{row[0]} | Ticket: {row[2]} | {row[1]}"):
        col1, col2 = st.columns(2)
        col1.markdown(f"**Problem Date:** {row[1]}")
        col1.markdown(f"**Ticket #:** {row[2]}")
        col2.markdown(f"**Tab:** {row[3]}")
        col2.markdown(f"**KPI:** {row[4]}")
        col2.markdown(f"**Submitted:** {row[6]}")
        st.markdown(f"**Description:**\n\n{row[5]}")
        st.markdown(f"**Status:** {status_badge(row[13])}", unsafe_allow_html=True)
        if row[7] or row[8]:
            st.info(f"**Quality:** {decision_badge(row[8])}  |  {row[7] or '—'}")
        if row[9] or row[10]:
            st.info(f"**Manager:** {decision_badge(row[10])}  |  {row[9] or '—'}")
        if row[11] or row[12]:
            st.success(f"**GM Final:** {decision_badge(row[12])}  |  {row[11] or '—'}")

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
    new_pw  = st.text_input("New Password", type="password")
    new_pw2 = st.text_input("Confirm New Password", type="password")
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

    with tab1:
        st.subheader("Submit New Appeal")
        with st.form("appeal_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            problem_date  = col1.date_input("Problem Date", value=date.today(), max_value=date.today())
            ticket_number = col2.text_input("Ticket Number")
            tab_sel       = col1.selectbox("Tab", TAB_LIST)
            kpi_sel       = col2.selectbox("KPI", KPI_LIST)
            st.date_input("Submission Date", value=date.today(), max_value=date.today())
            description = st.text_area("Describe your problem in detail", height=150)
            submitted   = st.form_submit_button("Submit Appeal", type="primary")
        if submitted:
            if not ticket_number.strip():
                st.error("Please enter the ticket number.")
            elif not description.strip():
                st.error("Please write a description.")
            else:
                ok = submit_appeal(user["username"], str(problem_date),
                                   ticket_number.strip(), tab_sel, kpi_sel, description.strip())
                if ok:
                    st.success("Appeal submitted successfully.")
                else:
                    st.error("Error submitting appeal.")

    with tab2:
        st.subheader("My Appeals")
        appeals = get_my_appeals(user["username"])
        if not appeals:
            st.info("You have not submitted any appeals yet.")
        else:
            st.caption(f"Total: {len(appeals)} appeal(s)")
            for row in appeals:
                my_appeal_card(row)

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
# PAGE: GENERAL MANAGER DASHBOARD (rsamim)
# ───────────────────────────────────────────────
def page_general_manager():
    user = st.session_state["user"]
    st.title(f"General Manager Panel — {user['full_name'] or user['username']}")

    tab1, tab2 = st.tabs(["⚖️ Escalated Appeals", "Change My Password"])

    with tab1:
        escalated = get_escalated_appeals()
        if not escalated:
            st.success("✅ No conflicts at this time. All appeals have consistent decisions.")
        else:
            st.warning(f"⚠️ {len(escalated)} appeal(s) require your final decision (conflicting decisions).")
            for row in escalated:
                gm_appeal_card(row, actor=user["username"])

    with tab2:
        st.subheader("Change My Password")
        old_pw  = st.text_input("Current Password", type="password", key="gm_old")
        new_pw  = st.text_input("New Password",     type="password", key="gm_new")
        new_pw2 = st.text_input("Confirm Password", type="password", key="gm_new2")
        if st.button("Update Password", key="gm_upd"):
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
        "All Appeals", "User Management", "Database Access", "Change My Password"
    ])

    with tab1:
        st.subheader("All Employee Appeals")
        appeals = get_all_appeals()
        if not appeals:
            st.info("No appeals submitted yet.")
        else:
            col1, col2, col3 = st.columns(3)
            employees = list(set(r[1] for r in appeals))
            kpis      = list(set(r[5] for r in appeals))
            statuses  = list(set(r[14] for r in appeals))

            f_emp    = col1.selectbox("Filter by Employee", ["All"] + sorted(employees))
            f_kpi    = col2.selectbox("Filter by KPI",      ["All"] + sorted(kpis))
            f_status = col3.selectbox("Filter by Status",   ["All"] + sorted(statuses))

            filtered = appeals
            if f_emp    != "All": filtered = [r for r in filtered if r[1]  == f_emp]
            if f_kpi    != "All": filtered = [r for r in filtered if r[5]  == f_kpi]
            if f_status != "All": filtered = [r for r in filtered if r[14] == f_status]

            st.caption(f"Showing {len(filtered)} of {len(appeals)} appeal(s)")
            for row in filtered:
                appeal_card(row, is_admin=True, actor=user["username"], panel="quality")

    with tab2:
        st.subheader("User Management")
        st.markdown("### Add New Employee")
        with st.form("add_user_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            new_uname = c1.text_input("Username (login ID)")
            new_fname = c2.text_input("Full Name")
            new_role  = c1.selectbox("Role", ["employee", "supervisor", "quality_manager"])
            new_sup   = c2.selectbox("Assign to Supervisor", [""] + SUPERVISORS,
                                     help="Leave blank for supervisors/admins")
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
                    if col_a.button("Reset Password to 123", key=f"rst_{uid}"):
                        if uname == user["username"]:
                            col_a.warning("Cannot reset your own password here.")
                        elif reset_password(uname, user["username"]):
                            col_a.success(f"Password reset for {uname}")
                        else:
                            col_a.error("Error resetting password.")
                    if uname not in ALL_MGMT:
                        if col_b.button("Delete User", key=f"del_{uid}", type="secondary"):
                            if delete_user(uname, user["username"]):
                                col_b.success(f"User '{uname}' deleted.")
                                st.rerun()
                            else:
                                col_b.error("Error deleting user.")
                    else:
                        col_b.markdown("*(Protected Account)*")

    with tab3:
        db_viewer_panel()

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

    init_db()
    auto_daily_backup()

    if "user" in st.session_state:
        with st.sidebar:
            u = st.session_state["user"]
            st.markdown(f"**Logged in as:** {u['username']}")
            st.markdown(f"**Role:** {u['role']}")
            st.markdown("---")

            if u["role"] == "quality_manager":
                today_path, today_fname = get_todays_backup_path()
                if today_path and os.path.exists(today_path):
                    st.markdown("### 💾 Daily Backup")
                    st.caption(f"📅 {today_iraq()}")
                    with open(today_path, "rb") as f:
                        st.download_button(
                            "📥 Download Today's Backup",
                            data=f.read(), file_name=today_fname,
                            mime="application/octet-stream",
                            key="sidebar_dl_today",
                            use_container_width=True,
                        )
                    st.markdown("---")

            if st.button("Logout"):
                audit_log("LOGOUT", u["username"])
                st.session_state.clear()
                st.rerun()

    if "user" not in st.session_state:
        page_login()
        return

    user = st.session_state["user"]

    if user["force_change"]:
        page_force_change()
        return

    role = user["role"]
    if role == "quality_manager":
        page_quality_manager()
    elif role == "supervisor":
        page_supervisor()
    elif role == "general_manager":
        page_general_manager()
    else:
        page_employee()


if __name__ == "__main__":
    main()
