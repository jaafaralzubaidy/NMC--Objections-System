import streamlit as st
import hashlib
import logging
from datetime import datetime, date, timezone, timedelta
from supabase import create_client

# ───────────────────────────────────────────────
# CONFIGURATION
# ───────────────────────────────────────────────
QUALITY_MANAGER = "jsafaa"
SUPERVISORS     = ["ahatim", "farook"]
GENERAL_MANAGER = "rsamim"
ADMIN_ROLES     = [QUALITY_MANAGER] + SUPERVISORS
ALL_MGMT        = ADMIN_ROLES + [GENERAL_MANAGER]
DEFAULT_PASSWORD = "123"

IRAQ_TZ = timezone(timedelta(hours=3))
def now_iraq():
    return datetime.now(IRAQ_TZ).strftime("%Y-%m-%d %H:%M:%S")

def today_iraq():
    return datetime.now(IRAQ_TZ).strftime("%Y-%m-%d")

KPI_LIST = [
    "Done Delay", "Done Delay Response", "High MTTD", "Shift Delay", "Ticket Not Add",
    "Wrong Action", "Delay In q", "High ASR Utlization", "Reduce Number Of Incident",
    "Delay High Impact", "Zabbix No Match", "Closing Issue", "Wrong Forward",
    "Wrong Action In Q Manager", "FMS", "Delay FMS", "Number Delay FMS", "No Task"
]

TAB_LIST = [
    "Bridges", "Earthlink Services", "IRQNBN", "Back Bone", "ITPC", "Metro",
    "Nas", "Power", "Baghdad Rings", "Server Room", "Switch State", "Wireless",
    "Al-watani Power", "Al-watani Services"
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
def audit_log(action, actor, details=""):
    logging.info(f"ACTOR={actor} | ACTION={action} | {details}")

# ───────────────────────────────────────────────
# SUPABASE CLIENT
# ───────────────────────────────────────────────
@st.cache_resource
def get_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def init_db():
    sb = get_client()
    for uname, fname, role, sup in [
        ("jsafaa", "Safaa Al-Quality",  "quality_manager", ""),
        ("ahatim", "Hatim Manager",     "supervisor",      ""),
        ("farook", "Farook Manager",    "supervisor",      ""),
        ("rsamim", "Samim Al-General",  "general_manager", ""),
    ]:
        existing = sb.table("users").select("id").eq("username", uname).execute()
        if not existing.data:
            sb.table("users").insert({
                "username": uname, "password_hash": hash_password(DEFAULT_PASSWORD),
                "full_name": fname, "role": role, "supervisor": sup,
                "force_change": 1, "created_at": now_iraq()
            }).execute()

# ───────────────────────────────────────────────
# STATUS LOGIC
# ───────────────────────────────────────────────
def compute_status(qd, md, gd):
    qd = (qd or "").strip()
    md = (md or "").strip()
    gd = (gd or "").strip()
    if gd in ("Approved", "Rejected"): return f"GM Decision: {gd}"
    if qd and md: return qd if qd == md else "Escalated to GM"
    if qd: return f"Quality: {qd}"
    if md: return f"Manager: {md}"
    return "Pending"

# ───────────────────────────────────────────────
# USER OPERATIONS
# ───────────────────────────────────────────────
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def authenticate(username, password):
    sb = get_client()
    res = sb.table("users").select("*").eq("username", username).execute()
    if res.data and res.data[0]["password_hash"] == hash_password(password):
        u = res.data[0]
        return {"id":u["id"],"username":u["username"],"full_name":u["full_name"],
                "role":u["role"],"supervisor":u["supervisor"],"force_change":u["force_change"]}
    return None

def update_password(username, new_password):
    try:
        get_client().table("users").update({"password_hash":hash_password(new_password),"force_change":0}).eq("username",username).execute()
        audit_log("PASSWORD_CHANGE", username); return True
    except Exception as e:
        audit_log("PASSWORD_CHANGE_ERROR", username, str(e)); return False

def reset_password(target_user, actor):
    try:
        get_client().table("users").update({"password_hash":hash_password(DEFAULT_PASSWORD),"force_change":1}).eq("username",target_user).execute()
        audit_log("PASSWORD_RESET", actor, f"target={target_user}"); return True
    except Exception as e:
        audit_log("PASSWORD_RESET_ERROR", actor, str(e)); return False

def get_all_users():
    res = get_client().table("users").select("id,username,full_name,role,supervisor,force_change,created_at").order("created_at", desc=True).execute()
    return [(r["id"],r["username"],r["full_name"],r["role"],r["supervisor"],r["force_change"],r["created_at"]) for r in res.data]

def add_user(username, full_name, role, supervisor, actor):
    try:
        sb = get_client()
        if sb.table("users").select("id").eq("username", username.strip().lower()).execute().data: return False
        sb.table("users").insert({
            "username":username.strip().lower(), "password_hash":hash_password(DEFAULT_PASSWORD),
            "full_name":full_name.strip(), "role":role, "supervisor":supervisor,
            "force_change":1, "created_at":now_iraq()
        }).execute()
        audit_log("USER_ADDED", actor, f"new_user={username}"); return True
    except Exception: return False

def delete_user(username, actor):
    if username in ALL_MGMT: return False
    try:
        sb = get_client()
        sb.table("appeals").delete().eq("employee", username).execute()
        sb.table("users").delete().eq("username", username).execute()
        audit_log("USER_DELETED", actor, f"deleted={username}"); return True
    except Exception as e:
        audit_log("USER_DELETE_ERROR", actor, str(e)); return False

def get_employees_of_supervisor(supervisor):
    res = get_client().table("users").select("username").eq("supervisor", supervisor).execute()
    return [r["username"] for r in res.data]

# ───────────────────────────────────────────────
# APPEAL OPERATIONS
# ───────────────────────────────────────────────
def submit_appeal(employee, problem_date, ticket, tab, kpi, description):
    try:
        get_client().table("appeals").insert({
            "employee":employee, "problem_date":problem_date, "ticket_number":ticket,
            "tab":tab, "kpi":kpi, "description":description,
            "submission_date":now_iraq(), "created_at":now_iraq(),
            "quality_response":"", "quality_decision":"",
            "manager_response":"", "manager_decision":"",
            "gm_response":"", "gm_decision":"", "status":"Pending"
        }).execute()
        audit_log("APPEAL_SUBMITTED", employee, f"ticket={ticket}"); return True
    except Exception as e:
        audit_log("APPEAL_SUBMIT_ERROR", employee, str(e)); return False

def _row(r, with_emp=True):
    if with_emp:
        return (r["id"],r["employee"],r["problem_date"],r["ticket_number"],r["tab"],r["kpi"],
                r["description"],r["submission_date"],r["quality_response"],r["quality_decision"],
                r["manager_response"],r["manager_decision"],r["gm_response"],r["gm_decision"],r["status"])
    return (r["id"],r["problem_date"],r["ticket_number"],r["tab"],r["kpi"],
            r["description"],r["submission_date"],r["quality_response"],r["quality_decision"],
            r["manager_response"],r["manager_decision"],r["gm_response"],r["gm_decision"],r["status"])

def get_my_appeals(username):
    res = get_client().table("appeals").select("*").eq("employee",username).order("id",desc=True).execute()
    return [_row(r, with_emp=False) for r in res.data]

def get_all_appeals():
    res = get_client().table("appeals").select("*").order("id",desc=True).execute()
    return [_row(r) for r in res.data]

def get_appeals_for_supervisor(supervisor):
    emps = get_employees_of_supervisor(supervisor)
    if not emps: return []
    res = get_client().table("appeals").select("*").in_("employee",emps).order("id",desc=True).execute()
    return [_row(r) for r in res.data]

def get_escalated_appeals():
    res = get_client().table("appeals").select("*").eq("status","Escalated to GM").order("id",desc=True).execute()
    return [_row(r) for r in res.data]

def save_quality_decision(appeal_id, response, decision, actor):
    try:
        sb = get_client()
        cur = sb.table("appeals").select("manager_decision,gm_decision").eq("id",appeal_id).execute()
        md = cur.data[0]["manager_decision"] if cur.data else ""
        gd = cur.data[0]["gm_decision"] if cur.data else ""
        sb.table("appeals").update({
            "quality_response":response, "quality_decision":decision,
            "status":compute_status(decision,md,gd)
        }).eq("id",appeal_id).execute()
        audit_log("QUALITY_DECISION", actor, f"id={appeal_id} dec={decision}"); return True
    except Exception as e:
        audit_log("QUALITY_DECISION_ERROR", actor, str(e)); return False

def save_manager_decision(appeal_id, response, decision, actor):
    try:
        sb = get_client()
        cur = sb.table("appeals").select("quality_decision,gm_decision").eq("id",appeal_id).execute()
        qd = cur.data[0]["quality_decision"] if cur.data else ""
        gd = cur.data[0]["gm_decision"] if cur.data else ""
        sb.table("appeals").update({
            "manager_response":response, "manager_decision":decision,
            "status":compute_status(qd,decision,gd)
        }).eq("id",appeal_id).execute()
        audit_log("MANAGER_DECISION", actor, f"id={appeal_id} dec={decision}"); return True
    except Exception as e:
        audit_log("MANAGER_DECISION_ERROR", actor, str(e)); return False

def save_gm_decision(appeal_id, response, decision, actor):
    try:
        get_client().table("appeals").update({
            "gm_response":response, "gm_decision":decision,
            "status":compute_status("","",decision)
        }).eq("id",appeal_id).execute()
        audit_log("GM_DECISION", actor, f"id={appeal_id} dec={decision}"); return True
    except Exception as e:
        audit_log("GM_DECISION_ERROR", actor, str(e)); return False

# ───────────────────────────────────────────────
# NOTIFICATIONS — إشعارات للموظف
# ───────────────────────────────────────────────
def show_employee_notifications(username):
    """
    يعرض إشعارات للموظف عن اعتراضاته التي تغير وضعها
    يعتمد على الـ session_state لتتبع الحالات السابقة
    """
    appeals = get_my_appeals(username)
    if not appeals:
        return

    # نحفظ الحالات السابقة في session_state
    prev_key = f"prev_statuses_{username}"
    if prev_key not in st.session_state:
        st.session_state[prev_key] = {}

    prev = st.session_state[prev_key]
    notifications = []

    for row in appeals:
        appeal_id  = row[0]
        cur_status = row[13]   # status بدون employee
        prev_status = prev.get(appeal_id)

        if prev_status is not None and prev_status != cur_status:
            # تغير الوضع — اصنع إشعار
            notifications.append((appeal_id, row[2], cur_status))

        # حدّث الحالة المحفوظة
        prev[appeal_id] = cur_status

    st.session_state[prev_key] = prev

    # عرض الإشعارات
    if notifications:
        st.markdown("---")
        st.markdown("### 🔔 Appeal Status Updates")
        for aid, ticket, status in notifications:
            if "Approved" in status:
                st.success(f"✅ Appeal #{aid} (Ticket: {ticket}) — Status changed to: **{status}**")
            elif "Rejected" in status:
                st.error(f"❌ Appeal #{aid} (Ticket: {ticket}) — Status changed to: **{status}**")
            elif "Escalated" in status:
                st.warning(f"⚖️ Appeal #{aid} (Ticket: {ticket}) — Escalated to General Manager")
            else:
                st.info(f"📋 Appeal #{aid} (Ticket: {ticket}) — Status changed to: **{status}**")
        st.markdown("---")

# ───────────────────────────────────────────────
# STATISTICS — إحصائيات
# ───────────────────────────────────────────────
def show_statistics(appeals, title="📊 Statistics"):
    """عرض إحصائيات الاعتراضات"""
    if not appeals:
        return

    st.markdown(f"### {title}")

    total     = len(appeals)
    pending   = sum(1 for r in appeals if r[-1] == "Pending")
    approved  = sum(1 for r in appeals if "Approved" in r[-1])
    rejected  = sum(1 for r in appeals if "Rejected" in r[-1])
    escalated = sum(1 for r in appeals if r[-1] == "Escalated to GM")
    in_review = total - pending - approved - rejected - escalated

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📋 Total",      total)
    c2.metric("⏳ Pending",    pending)
    c3.metric("✅ Approved",   approved)
    c4.metric("❌ Rejected",   rejected)
    c5.metric("⚖️ Escalated",  escalated)

    # نسب مئوية بشكل بسيط
    if total > 0:
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if approved + rejected > 0:
                approval_rate = round(approved / (approved + rejected) * 100)
                st.markdown(f"**Approval Rate:** {approval_rate}%")
                st.progress(approval_rate / 100)

        with col2:
            resolved = approved + rejected
            resolution_rate = round(resolved / total * 100)
            st.markdown(f"**Resolution Rate:** {resolution_rate}%")
            st.progress(resolution_rate / 100)

    st.markdown("---")

def show_supervisor_statistics(appeals, title="📊 Team Statistics"):
    """إحصائيات للسوبرفايزر"""
    show_statistics(appeals, title)

def show_quality_statistics(appeals):
    """إحصائيات مفصّلة للـ quality manager"""
    if not appeals:
        return

    st.markdown("### 📊 Overall Statistics")

    total     = len(appeals)
    pending   = sum(1 for r in appeals if r[-1] == "Pending")
    approved  = sum(1 for r in appeals if "Approved" in r[-1])
    rejected  = sum(1 for r in appeals if "Rejected" in r[-1])
    escalated = sum(1 for r in appeals if r[-1] == "Escalated to GM")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📋 Total",     total)
    c2.metric("⏳ Pending",   pending)
    c3.metric("✅ Approved",  approved)
    c4.metric("❌ Rejected",  rejected)
    c5.metric("⚖️ Escalated", escalated)

    if total > 0:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if approved + rejected > 0:
                rate = round(approved / (approved + rejected) * 100)
                st.markdown(f"**Approval Rate:** {rate}%")
                st.progress(rate / 100)
        with col2:
            res_rate = round((approved + rejected) / total * 100)
            st.markdown(f"**Resolution Rate:** {res_rate}%")
            st.progress(res_rate / 100)
        with col3:
            esc_rate = round(escalated / total * 100) if total > 0 else 0
            st.markdown(f"**Escalation Rate:** {esc_rate}%")
            st.progress(esc_rate / 100)

    # إحصائيات حسب KPI
    st.markdown("---")
    st.markdown("**Top KPIs by Appeal Count:**")
    kpi_counts = {}
    for r in appeals:
        kpi = r[5]
        kpi_counts[kpi] = kpi_counts.get(kpi, 0) + 1
    top_kpis = sorted(kpi_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    for kpi, count in top_kpis:
        st.markdown(f"- **{kpi}:** {count} appeal(s)")

    st.markdown("---")

# ───────────────────────────────────────────────
# UI HELPERS
# ───────────────────────────────────────────────
def status_badge(s):
    color = "#888888"
    if s == "Approved":          color = "#27AE60"
    elif s == "Rejected":        color = "#E74C3C"
    elif s == "Escalated to GM": color = "#9B59B6"
    elif "GM Decision" in s:     color = "#27AE60" if "Approved" in s else "#E74C3C"
    elif "Quality" in s:         color = "#2E86AB"
    elif "Manager" in s:         color = "#E67E22"
    return f'<span style="background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:12px;">{s}</span>'

def dbadge(d):
    if d == "Approved": return "✅ Approved"
    if d == "Rejected": return "❌ Rejected"
    return "⏳ Pending"

# cols مع employee: 0:id 1:emp 2:prob 3:ticket 4:tab 5:kpi 6:desc
#                   7:sub 8:q_resp 9:q_dec 10:m_resp 11:m_dec 12:gm_resp 13:gm_dec 14:status
def appeal_card(row, is_admin=False, actor="", panel="quality"):
    with st.expander(f"Appeal #{row[0]} | {row[1]} | Ticket: {row[3]} | {row[2]} | {row[14]}"):
        c1, c2 = st.columns(2)
        c1.markdown(f"**Employee:** {row[1]}")
        c1.markdown(f"**Problem Date:** {row[2]}")
        c1.markdown(f"**Ticket #:** {row[3]}")
        c2.markdown(f"**Tab:** {row[4]}")
        c2.markdown(f"**KPI:** {row[5]}")
        c2.markdown(f"**Submitted:** {row[7]}")
        st.markdown(f"**Description:**\n\n{row[6]}")
        st.markdown(f"**Status:** {status_badge(row[14])}", unsafe_allow_html=True)
        if row[8] or row[9]:   st.info(f"**Quality:** {dbadge(row[9])} | {row[8] or '—'}")
        if row[10] or row[11]: st.info(f"**Manager:** {dbadge(row[11])} | {row[10] or '—'}")
        if row[12] or row[13]: st.success(f"**GM Final:** {dbadge(row[13])} | {row[12] or '—'}")
        if not is_admin: return
        st.markdown("---")
        if panel == "quality":
            st.markdown("**Your Decision (Quality Manager):**")
            dec = st.radio("Decision", ["Approved","Rejected"],
                           index=0 if (row[9] or "") != "Rejected" else 1,
                           key=f"qdec_{row[0]}", horizontal=True)
            resp = st.text_area("Notes (optional)", value=row[8] or "", key=f"qresp_{row[0]}")
            if st.button(f"💾 Save #{row[0]}", key=f"qsave_{row[0]}"):
                if save_quality_decision(row[0], resp, dec, actor):
                    st.success(f"Saved: {dec}"); st.rerun()
                else: st.error("Error saving.")
        elif panel == "manager":
            st.markdown("**Your Decision (Supervisor):**")
            dec = st.radio("Decision", ["Approved","Rejected"],
                           index=0 if (row[11] or "") != "Rejected" else 1,
                           key=f"mdec_{row[0]}", horizontal=True)
            resp = st.text_area("Notes (optional)", value=row[10] or "", key=f"mresp_{row[0]}")
            if st.button(f"💾 Save #{row[0]}", key=f"msave_{row[0]}"):
                if save_manager_decision(row[0], resp, dec, actor):
                    st.success(f"Saved: {dec}"); st.rerun()
                else: st.error("Error saving.")

def gm_appeal_card(row, actor=""):
    with st.expander(f"Appeal #{row[0]} | {row[1]} | Ticket: {row[3]} | {row[2]}"):
        c1, c2 = st.columns(2)
        c1.markdown(f"**Employee:** {row[1]}")
        c1.markdown(f"**Problem Date:** {row[2]}")
        c1.markdown(f"**Ticket #:** {row[3]}")
        c2.markdown(f"**Tab:** {row[4]}")
        c2.markdown(f"**KPI:** {row[5]}")
        c2.markdown(f"**Submitted:** {row[7]}")
        st.markdown(f"**Description:**\n\n{row[6]}")
        st.info(f"**Quality Decision:** {dbadge(row[9])} | {row[8] or '—'}")
        st.info(f"**Manager Decision:** {dbadge(row[11])} | {row[10] or '—'}")
        if row[13]: st.success(f"**Your Previous Decision:** {dbadge(row[13])}")
        st.markdown("---")
        st.markdown("**⚖️ Your Final Decision:**")
        dec = st.radio("Final Decision", ["Approved","Rejected"],
                       index=0 if (row[13] or "") != "Rejected" else 1,
                       key=f"gmdec_{row[0]}", horizontal=True)
        resp = st.text_area("Notes (optional)", value=row[12] or "", key=f"gmresp_{row[0]}")
        if st.button(f"💾 Save Final Decision #{row[0]}", key=f"gmsave_{row[0]}", type="primary"):
            if save_gm_decision(row[0], resp, dec, actor):
                st.success(f"Saved: {dec}"); st.rerun()
            else: st.error("Error saving.")

# cols بدون employee: 0:id 1:prob 2:ticket 3:tab 4:kpi 5:desc
#                     6:sub 7:q_resp 8:q_dec 9:m_resp 10:m_dec 11:gm_resp 12:gm_dec 13:status
def my_appeal_card(row):
    with st.expander(f"Appeal #{row[0]} | Ticket: {row[2]} | {row[1]}"):
        c1, c2 = st.columns(2)
        c1.markdown(f"**Problem Date:** {row[1]}")
        c1.markdown(f"**Ticket #:** {row[2]}")
        c2.markdown(f"**Tab:** {row[3]}")
        c2.markdown(f"**KPI:** {row[4]}")
        c2.markdown(f"**Submitted:** {row[6]}")
        st.markdown(f"**Description:**\n\n{row[5]}")
        st.markdown(f"**Status:** {status_badge(row[13])}", unsafe_allow_html=True)
        if row[7] or row[8]:   st.info(f"**Quality:** {dbadge(row[8])} | {row[7] or '—'}")
        if row[9] or row[10]:  st.info(f"**Manager:** {dbadge(row[10])} | {row[9] or '—'}")
        if row[11] or row[12]: st.success(f"**GM Final:** {dbadge(row[12])} | {row[11] or '—'}")

# ───────────────────────────────────────────────
# DATABASE VIEWER
# ───────────────────────────────────────────────
def db_viewer_panel():
    st.markdown("---")
    st.subheader("Database Direct Access")
    tabs = st.tabs(["Users Table", "Appeals Table"])
    with tabs[0]:
        import pandas as pd
        res = get_client().table("users").select("id,username,full_name,role,supervisor,force_change,created_at").order("created_at",desc=True).execute()
        st.dataframe(pd.DataFrame(res.data), use_container_width=True)
    with tabs[1]:
        import pandas as pd
        res = get_client().table("appeals").select("*").order("id",desc=True).execute()
        df = pd.DataFrame(res.data)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.download_button("Download Appeals as CSV", df.to_csv(index=False).encode("utf-8"), "appeals_export.csv", "text/csv")

# ───────────────────────────────────────────────
# PAGES
# ───────────────────────────────────────────────
def page_login():
    st.markdown("<style>.block-container{max-width:450px;margin:auto;padding-top:80px}</style>", unsafe_allow_html=True)
    st.markdown("## 🏢 NMC Appeals System")
    st.markdown("Please log in to continue.")
    username = st.text_input("Username").strip().lower()
    password = st.text_input("Password", type="password")
    if st.button("Login", type="primary", use_container_width=True):
        if not username or not password:
            st.error("Please fill in all fields."); return
        user = authenticate(username, password)
        if user:
            st.session_state["user"] = user
            audit_log("LOGIN", username); st.rerun()
        else:
            st.error("Invalid username or password.")

def page_force_change():
    user = st.session_state["user"]
    st.warning("You must change your password before continuing.")
    st.subheader("Set New Password")
    new_pw  = st.text_input("New Password", type="password")
    new_pw2 = st.text_input("Confirm New Password", type="password")
    if st.button("Change Password", type="primary"):
        if not new_pw or not new_pw2:    st.error("Please fill both fields.")
        elif new_pw != new_pw2:           st.error("Passwords do not match.")
        elif new_pw == DEFAULT_PASSWORD:  st.error("Cannot use the default password.")
        elif len(new_pw) < 4:             st.error("Minimum 4 characters.")
        else:
            if update_password(user["username"], new_pw):
                st.session_state["user"]["force_change"] = 0
                st.success("Password changed!"); st.rerun()
            else: st.error("Error saving password.")

def _change_pw_section(key_prefix, username):
    st.subheader("Change My Password")
    old_pw  = st.text_input("Current Password", type="password", key=f"{key_prefix}_old")
    new_pw  = st.text_input("New Password",     type="password", key=f"{key_prefix}_new")
    new_pw2 = st.text_input("Confirm Password", type="password", key=f"{key_prefix}_new2")
    if st.button("Update Password", key=f"{key_prefix}_upd"):
        if not authenticate(username, old_pw):  st.error("Current password is incorrect.")
        elif new_pw != new_pw2:                  st.error("Passwords do not match.")
        elif len(new_pw) < 4:                    st.error("Minimum 4 characters.")
        elif new_pw == DEFAULT_PASSWORD:          st.error("Cannot use the default password.")
        else:
            if update_password(username, new_pw): st.success("Password updated successfully.")
            else: st.error("Error updating password.")

def page_employee():
    user = st.session_state["user"]
    st.title(f"Welcome, {user['full_name'] or user['username']}")

    # ── إشعارات الموظف ──
    show_employee_notifications(user["username"])

    tab1, tab2, tab3 = st.tabs(["Submit Appeal", "My Appeals", "Change Password"])

    with tab1:
        st.subheader("Submit New Appeal")
        with st.form("appeal_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            problem_date  = c1.date_input("Problem Date", value=date.today(), max_value=date.today())
            ticket_number = c2.text_input("Ticket Number")
            tab_sel = c1.selectbox("Tab", TAB_LIST)
            kpi_sel = c2.selectbox("KPI", KPI_LIST)
            st.date_input("Submission Date", value=date.today(), max_value=date.today())
            description = st.text_area("Describe your problem in detail", height=150)
            submitted = st.form_submit_button("Submit Appeal", type="primary")
        if submitted:
            if not ticket_number.strip(): st.error("Please enter the ticket number.")
            elif not description.strip():  st.error("Please write a description.")
            else:
                if submit_appeal(user["username"], str(problem_date), ticket_number.strip(), tab_sel, kpi_sel, description.strip()):
                    st.success("Appeal submitted successfully.")
                else: st.error("Error submitting appeal.")

    with tab2:
        st.subheader("My Appeals")
        appeals = get_my_appeals(user["username"])
        if not appeals: st.info("You have not submitted any appeals yet.")
        else:
            # ── إحصائيات الموظف ──
            show_statistics(appeals, "📊 My Appeals Summary")
            st.caption(f"Total: {len(appeals)} appeal(s)")
            for row in appeals: my_appeal_card(row)

    with tab3:
        _change_pw_section("emp", user["username"])

def page_supervisor():
    user = st.session_state["user"]
    st.title(f"Supervisor Panel — {user['full_name'] or user['username']}")
    tab1, tab2 = st.tabs(["Team Appeals", "Change My Password"])

    with tab1:
        appeals = get_appeals_for_supervisor(user["username"])
        if not appeals: st.info("No appeals found for your team yet.")
        else:
            # ── إحصائيات الفريق ──
            show_supervisor_statistics(appeals, "📊 Team Statistics")
            st.caption(f"Total: {len(appeals)} appeal(s)")
            for row in appeals: appeal_card(row, is_admin=True, actor=user["username"], panel="manager")

    with tab2:
        _change_pw_section("sup", user["username"])

def page_general_manager():
    user = st.session_state["user"]
    st.title(f"General Manager Panel — {user['full_name'] or user['username']}")
    tab1, tab2 = st.tabs(["⚖️ Escalated Appeals", "Change My Password"])

    with tab1:
        escalated = get_escalated_appeals()
        if not escalated: st.success("✅ No conflicts at this time.")
        else:
            st.warning(f"⚠️ {len(escalated)} appeal(s) require your final decision.")
            # ── إحصائيات المحالة ──
            show_statistics(escalated, "📊 Escalated Appeals Summary")
            for row in escalated: gm_appeal_card(row, actor=user["username"])

    with tab2:
        _change_pw_section("gm", user["username"])

def page_quality_manager():
    user = st.session_state["user"]
    st.title(f"Quality Manager Panel — {user['full_name'] or user['username']}")
    tab1, tab2, tab3, tab4 = st.tabs(["All Appeals","User Management","Database Access","Change My Password"])

    with tab1:
        appeals = get_all_appeals()
        if not appeals: st.info("No appeals submitted yet.")
        else:
            # ── إحصائيات شاملة ──
            show_quality_statistics(appeals)

            c1, c2, c3 = st.columns(3)
            f_emp    = c1.selectbox("Filter by Employee", ["All"] + sorted(set(r[1] for r in appeals)))
            f_kpi    = c2.selectbox("Filter by KPI",      ["All"] + sorted(set(r[5] for r in appeals)))
            f_status = c3.selectbox("Filter by Status",   ["All"] + sorted(set(r[14] for r in appeals)))
            filtered = [r for r in appeals
                        if (f_emp=="All" or r[1]==f_emp)
                        and (f_kpi=="All" or r[5]==f_kpi)
                        and (f_status=="All" or r[14]==f_status)]
            st.caption(f"Showing {len(filtered)} of {len(appeals)} appeal(s)")
            for row in filtered: appeal_card(row, is_admin=True, actor=user["username"], panel="quality")

    with tab2:
        st.subheader("User Management")
        st.markdown("### Add New Employee")
        with st.form("add_user_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            new_uname = c1.text_input("Username (login ID)")
            new_fname = c2.text_input("Full Name")
            new_role  = c1.selectbox("Role", ["employee","supervisor","quality_manager"])
            new_sup   = c2.selectbox("Assign to Supervisor", [""]+SUPERVISORS)
            add_submitted = st.form_submit_button("Add User", type="primary")
        if add_submitted:
            if not new_uname.strip(): st.error("Username cannot be empty.")
            else:
                if add_user(new_uname, new_fname, new_role, new_sup, user["username"]):
                    st.success(f"User '{new_uname}' added. Default password: 123")
                else: st.error(f"Username '{new_uname}' already exists.")
        st.markdown("---")
        st.markdown("### Manage Existing Users")
        for u in get_all_users():
            uid, uname, fname, role, sup, fc, created = u
            with st.expander(f"{uname} | {fname} | Role: {role} | Supervisor: {sup or 'None'}"):
                st.markdown(f"**Created:** {created}")
                st.markdown(f"**Force Change Password:** {'Yes' if fc else 'No'}")
                ca, cb = st.columns(2)
                if ca.button("Reset Password to 123", key=f"rst_{uid}"):
                    if uname == user["username"]: ca.warning("Cannot reset your own password here.")
                    elif reset_password(uname, user["username"]): ca.success(f"Password reset for {uname}")
                    else: ca.error("Error resetting password.")
                if uname not in ALL_MGMT:
                    if cb.button("Delete User", key=f"del_{uid}", type="secondary"):
                        if delete_user(uname, user["username"]):
                            cb.success(f"User '{uname}' deleted."); st.rerun()
                        else: cb.error("Error deleting user.")
                else:
                    cb.markdown("*(Protected Account)*")

    with tab3:
        db_viewer_panel()

    with tab4:
        _change_pw_section("qm", user["username"])

# ───────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────
def main():
    st.set_page_config(page_title="NMC Appeals System", page_icon="🏢", layout="wide")

    try:
        init_db()
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        st.info("Please check SUPABASE_URL and SUPABASE_KEY in Streamlit Secrets.")
        return

    if "user" in st.session_state:
        with st.sidebar:
            u = st.session_state["user"]
            st.markdown(f"**Logged in as:** {u['username']}")
            st.markdown(f"**Role:** {u['role']}")
            st.markdown("---")
            if st.button("Logout"):
                audit_log("LOGOUT", u["username"])
                st.session_state.clear(); st.rerun()

    if "user" not in st.session_state:
        page_login(); return

    user = st.session_state["user"]
    if user["force_change"]:
        page_force_change(); return

    role = user["role"]
    if   role == "quality_manager":  page_quality_manager()
    elif role == "supervisor":        page_supervisor()
    elif role == "general_manager":   page_general_manager()
    else:                             page_employee()

if __name__ == "__main__":
    main()
