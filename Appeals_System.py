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
# ADMIN_ROLES يستخدم لمنع الحذف العرضي للحسابات الأساسية
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
            UPDATE users
