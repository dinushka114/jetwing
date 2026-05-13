import streamlit as st
import pandas as pd
from datetime import datetime
import uuid


st.set_page_config(
    page_title="Jetwing | Voucher Issue Resolution System",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)


EXECUTIVES = {
    "TR-9": "Kamal Perera",
    "TR-8": "Nimal Fernando",
    "TR-7": "Nadeesha Silva",
    "TR-6": "Kasun Jayawardena",
}
DEFAULT_EXECUTIVE = "Irosh Rupasinghe"

STATUS_FLOW = ["Open", "In Progress", "Resolved", "Closed", "Reopened"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]

STATUS_COLORS = {
    "Open": "🔵",
    "In Progress": "🟡",
    "Resolved": "🟢",
    "Closed": "⚫",
    "Reopened": "🔴",
}


def assign_executive(tour_number: str) -> str:
    """Rule-based assignment by tour-number prefix."""
    tour = (tour_number or "").upper().strip()
    for prefix, exec_name in EXECUTIVES.items():
        if tour.startswith(prefix):
            return exec_name
    return DEFAULT_EXECUTIVE



def init_state() -> None:
    if "tickets" in st.session_state:
        return

    now = datetime.now()
    seed = [
        {
            "id": "TKT-001",
            "tour": "TR-9921",
            "voucher": "V-5541",
            "executive": assign_executive("TR-9921"),
            "status": "Open",
            "priority": "High",
            "desc": "Incorrect hotel rate applied on the voucher.",
            "created": now,
            "updated": now,
            "comments": [],
        },
        {
            "id": "TKT-002",
            "tour": "TR-8840",
            "voucher": "V-1120",
            "executive": assign_executive("TR-8840"),
            "status": "In Progress",
            "priority": "Medium",
            "desc": "Duplicate payment issue — supplier paid twice.",
            "created": now,
            "updated": now,
            "comments": [
                {
                    "by": "Bimal Fernando",
                    "at": now,
                    "text": "Investigating with supplier accounts team.",
                }
            ],
        },
        {
            "id": "TKT-003",
            "tour": "TR-7705",
            "voucher": "V-9087",
            "executive": assign_executive("TR-7705"),
            "status": "Resolved",
            "priority": "Low",
            "desc": "Currency conversion rounding off by 0.5 USD.",
            "created": now,
            "updated": now,
            "comments": [
                {
                    "by": "Nadeesha Silva",
                    "at": now,
                    "text": "Adjusted rate in core system. Ready for finance verification.",
                }
            ],
        },
        {
            "id": "TKT-004",
            "tour": "TR-9120",
            "voucher": "V-3344",
            "executive": assign_executive("TR-9120"),
            "status": "Open",
            "priority": "Critical",
            "desc": "Voucher amount mismatch with PO — supplier on hold.",
            "created": now,
            "updated": now,
            "comments": [],
        },
    ]

    st.session_state.tickets = seed
    st.session_state.audit = [
        {"at": now, "actor": "System", "action": f"Seeded ticket {t['id']}"}
        for t in seed
    ]
    st.session_state.counter = len(seed) + 1


def log_audit(actor: str, action: str) -> None:
    st.session_state.audit.append(
        {"at": datetime.now(), "actor": actor, "action": action}
    )


def update_ticket(ticket_id: str, **changes) -> None:
    for t in st.session_state.tickets:
        if t["id"] == ticket_id:
            t.update(changes)
            t["updated"] = datetime.now()
            break


def add_comment(ticket_id: str, author: str, text: str) -> None:
    for t in st.session_state.tickets:
        if t["id"] == ticket_id:
            t["comments"].append(
                {"by": author, "at": datetime.now(), "text": text}
            )
            t["updated"] = datetime.now()
            break


def tickets_df() -> pd.DataFrame:
    rows = []
    for t in st.session_state.tickets:
        rows.append(
            {
                "Ticket ID": t["id"],
                "Tour": t["tour"],
                "Voucher": t["voucher"],
                "Executive": t["executive"],
                "Status": f"{STATUS_COLORS.get(t['status'],'')} {t['status']}",
                "Priority": t["priority"],
                "Description": t["desc"],
                "Created": t["created"].strftime("%Y-%m-%d %H:%M"),
                "Updated": t["updated"].strftime("%Y-%m-%d %H:%M"),
                "Comments": len(t["comments"]),
            }
        )
    return pd.DataFrame(rows)


def finance_logging_view() -> None:
    st.header("Issue Logging")
    # st.caption(
    #     "Log voucher discrepancies through this structured form instead of email. "
    #     "Smart Assignment routes tickets automatically based on tour number."
    # )

    with st.form("ticket_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tour = st.text_input("Tour Number", placeholder="e.g. TR-9921")
            priority = st.selectbox("Priority Level", PRIORITIES, index=1)
        with col2:
            voucher = st.text_input("Voucher Number", placeholder="e.g. V-5541")
            preview = (
                f"Will be assigned to **{assign_executive(tour)}**"
                if tour
                else "Enter a Tour Number to preview the assignee."
            )
            st.markdown(preview)

        desc = st.text_area(
            "Issue Description",
            placeholder="Describe the discrepancy clearly…",
            height=120,
        )

        submitted = st.form_submit_button("Create Ticket", type="primary")

        if submitted:
            if not tour or not voucher or not desc:
                st.error("Tour Number, Voucher Number and Description are required.")
            else:
                ticket_id = f"TKT-{st.session_state.counter:03d}"
                executive = assign_executive(tour)
                st.session_state.tickets.append(
                    {
                        "id": ticket_id,
                        "tour": tour.upper(),
                        "voucher": voucher.upper(),
                        "executive": executive,
                        "status": "Open",
                        "priority": priority,
                        "desc": desc,
                        "created": datetime.now(),
                        "updated": datetime.now(),
                        "comments": [],
                    }
                )
                st.session_state.counter += 1
                log_audit(
                    "Finance",
                    f"Created {ticket_id} ({tour.upper()} / {voucher.upper()}) → {executive}",
                )
                st.success(
                    f"Ticket **{ticket_id}** created and auto-assigned to **{executive}**."
                )

    st.divider()
    st.subheader("Verification & Closure")
    st.caption("Review resolved tickets and mark them as Closed or Reopen.")

    resolved = [t for t in st.session_state.tickets if t["status"] == "Resolved"]
    if not resolved:
        st.info("No resolved tickets awaiting verification.")
        return

    for t in resolved:
        with st.expander(f"{t['id']} · {t['tour']} · {t['voucher']} — {t['priority']}"):
            st.write(f"**Description:** {t['desc']}")
            st.write(f"**Resolved by:** {t['executive']}")
            if t["comments"]:
                st.write("**Comments:**")
                for c in t["comments"]:
                    st.markdown(
                        f"> *{c['at'].strftime('%Y-%m-%d %H:%M')} — {c['by']}:* {c['text']}"
                    )

            note = st.text_input(
                "Verification note", key=f"verify_note_{t['id']}", placeholder="Optional"
            )
            c1, c2, _ = st.columns([1, 1, 4])
            with c1:
                if st.button("Close", key=f"close_{t['id']}", type="primary"):
                    update_ticket(t["id"], status="Closed")
                    if note:
                        add_comment(t["id"], "Finance", f"[Closed] {note}")
                    log_audit("Finance", f"Closed {t['id']}")
                    st.rerun()
            with c2:
                if st.button("Reopen", key=f"reopen_{t['id']}"):
                    update_ticket(t["id"], status="Reopened")
                    reason = note or "Issue persists — please re-investigate."
                    add_comment(t["id"], "Finance", f"[Reopened] {reason}")
                    log_audit("Finance", f"Reopened {t['id']}")
                    st.rerun()


def executive_view() -> None:
    st.header("Tour Executive")
    # st.caption("Open → In Progress → Resolved. Add comments for transparency.")

    all_execs = sorted({t["executive"] for t in st.session_state.tickets})
    me = st.selectbox("Acting as", all_execs)

    actionable_statuses = ["Open", "In Progress", "Reopened"]
    mine = [
        t
        for t in st.session_state.tickets
        if t["executive"] == me and t["status"] in actionable_statuses
    ]

    if not mine:
        st.success("No pending tickets — you're all caught up.")
        return

    # Dashboard-style "notification" banner (Section 4.3)
    high_priority = [t for t in mine if t["priority"] in ("High", "Critical")]
    if high_priority:
        st.warning(
            f"You have **{len(high_priority)}** high-priority ticket(s) requiring attention."
        )

    st.write(f"### Assigned to {me} ({len(mine)} pending)")

    for t in mine:
        badge = STATUS_COLORS.get(t["status"], "")
        with st.expander(
            f"{badge} {t['id']} · {t['tour']} · {t['voucher']} — "
            f"**{t['priority']}** — _{t['status']}_"
        ):
            st.write(f"**Description:** {t['desc']}")
            st.write(f"**Created:** {t['created'].strftime('%Y-%m-%d %H:%M')}")

            if t["comments"]:
                st.write("**Comment thread:**")
                for c in t["comments"]:
                    st.markdown(
                        f"> *{c['at'].strftime('%Y-%m-%d %H:%M')} — {c['by']}:* {c['text']}"
                    )

            new_comment = st.text_input(
                "Add a comment", key=f"cmt_{t['id']}", placeholder="Status update…"
            )

            c1, c2, c3 = st.columns(3)
            with c1:
                if t["status"] in ("Open", "Reopened"):
                    if st.button("Start (In Progress)", key=f"prog_{t['id']}"):
                        update_ticket(t["id"], status="In Progress")
                        if new_comment:
                            add_comment(t["id"], me, new_comment)
                        log_audit(me, f"Moved {t['id']} to In Progress")
                        st.rerun()
            with c2:
                if st.button("Mark Resolved", key=f"res_{t['id']}", type="primary"):
                    update_ticket(t["id"], status="Resolved")
                    if new_comment:
                        add_comment(t["id"], me, new_comment)
                    else:
                        add_comment(t["id"], me, "Issue fixed in core system.")
                    log_audit(me, f"Resolved {t['id']}")
                    st.rerun()
            with c3:
                if st.button("Add comment only", key=f"cmtonly_{t['id']}"):
                    if new_comment:
                        add_comment(t["id"], me, new_comment)
                        log_audit(me, f"Commented on {t['id']}")
                        st.rerun()
                    else:
                        st.warning("Enter a comment first.")


def management_dashboard() -> None:
    st.header("Management Dashboard")
    # st.caption("Real-time visibility, search & filter, and full audit trail.")

    df_raw = pd.DataFrame(st.session_state.tickets)

    total = len(df_raw)
    open_n = (df_raw["status"] == "Open").sum() if total else 0
    progress_n = (df_raw["status"] == "In Progress").sum() if total else 0
    resolved_n = (df_raw["status"] == "Resolved").sum() if total else 0
    closed_n = (df_raw["status"] == "Closed").sum() if total else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Tickets", total)
    k2.metric("🔵 Open", int(open_n))
    k3.metric("🟡 In Progress", int(progress_n))
    k4.metric("🟢 Resolved", int(resolved_n))
    k5.metric("⚫ Closed", int(closed_n))

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Tickets by Status")
        st.bar_chart(df_raw["status"].value_counts())
    with c2:
        st.subheader("Tickets by Priority")
        st.bar_chart(df_raw["priority"].value_counts())

    st.divider()

    st.subheader("Search & Filter")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        tour_filter = st.text_input("Tour contains")
    with f2:
        exec_filter = st.multiselect(
            "Executive", sorted(df_raw["executive"].unique().tolist())
        )
    with f3:
        prio_filter = st.multiselect("Priority", PRIORITIES)
    with f4:
        status_filter = st.multiselect("Status", STATUS_FLOW)

    filtered = df_raw.copy()
    if tour_filter:
        filtered = filtered[
            filtered["tour"].str.contains(tour_filter.upper(), na=False)
        ]
    if exec_filter:
        filtered = filtered[filtered["executive"].isin(exec_filter)]
    if prio_filter:
        filtered = filtered[filtered["priority"].isin(prio_filter)]
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]

    st.subheader("Real-Time Ticket Table")
    display = filtered.assign(
        Status=filtered["status"].map(lambda s: f"{STATUS_COLORS.get(s,'')} {s}"),
        Created=filtered["created"].dt.strftime("%Y-%m-%d %H:%M"),
        Updated=filtered["updated"].dt.strftime("%Y-%m-%d %H:%M"),
        Comments=filtered["comments"].apply(len),
    )[
        [
            "id",
            "tour",
            "voucher",
            "executive",
            "Status",
            "priority",
            "desc",
            "Created",
            "Updated",
            "Comments",
        ]
    ].rename(
        columns={
            "id": "Ticket ID",
            "tour": "Tour",
            "voucher": "Voucher",
            "executive": "Executive",
            "priority": "Priority",
            "desc": "Description",
        }
    )
    st.dataframe(display, use_container_width=True, hide_index=True)

    csv = display.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Export filtered view (CSV)",
        csv,
        "voucher_tickets.csv",
        "text/csv",
    )

    st.divider()

    st.subheader("Full Audit Trail")
    audit_df = pd.DataFrame(st.session_state.audit)
    if not audit_df.empty:
        audit_df["at"] = audit_df["at"].dt.strftime("%Y-%m-%d %H:%M:%S")
        audit_df = audit_df.rename(
            columns={"at": "Timestamp", "actor": "Actor", "action": "Action"}
        )
        st.dataframe(
            audit_df.iloc[::-1], use_container_width=True, hide_index=True
        )
    else:
        st.info("No audit events yet.")



def sidebar() -> str:
    with st.sidebar:
        st.markdown("Voucher Issue Resolution")
        st.caption("Jetwing Air · POC by Purple Software")
        st.divider()

        role = st.radio(
            "Select Role",
            ["Finance / Operations", "Tour Executive", "Management"],
            help="Switch perspectives to walk through the full workflow.",
        )

        st.divider()
        st.markdown("### Smart Assignment Rules")
        for prefix, exec_name in EXECUTIVES.items():
            st.markdown(f"- `{prefix}xxx` → **{exec_name}**")
        st.markdown(f"- *(others)* → **{DEFAULT_EXECUTIVE}**")

        st.divider()
        if st.button("Reset demo data"):
            for k in ("tickets", "audit", "counter"):
                st.session_state.pop(k, None)
            st.rerun()

    return role


def main() -> None:
    init_state()
    role = sidebar()

    st.set_page_config(menu_items=None)

    hide_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stAppDeployButton {display: none !important;}

        /* Hide the "Hosted with Streamlit" floating badge (all known class hashes) */
        .viewerBadge_container__1QSob,
        .viewerBadge_link__1S137,
        .viewerBadge_text__1JaDK,
        .styles_viewerBadge__CvC9N,
        [class^="viewerBadge_"],
        [class*=" viewerBadge_"],
        [class*="_viewerBadge_"],
        div[class*="viewerBadge"],
        a[class*="viewerBadge"] {
            display: none !important;
            visibility: hidden !important;
        }

        /* Hide the GitHub profile avatar shown bottom-right on Streamlit Cloud */
        [class^="_profileContainer"],
        [class*=" _profileContainer"],
        [class*="profileContainer"],
        div[class*="profileContainer"],
        a[href*="streamlit.io/cloud"],
        a[href*="share.streamlit.io"],
        a[href*="github.com/"][target="_blank"][class*="profile"] {
            display: none !important;
            visibility: hidden !important;
        }

        /* Streamlit decoration / status widget */
        [data-testid="stStatusWidget"],
        [data-testid="stDecoration"] {
            display: none !important;
        }
        </style>

        <script>
        (function () {
            const hide = () => {
                document.querySelectorAll('a').forEach(a => {
                    const href = (a.getAttribute('href') || '').toLowerCase();
                    if (
                        href.includes('streamlit.io') ||
                        href.includes('share.streamlit.io') ||
                        (href.includes('github.com/') && a.querySelector('img'))
                    ) {
                        let el = a;
                        for (let i = 0; i < 4 && el && el.parentElement; i++) {
                            el = el.parentElement;
                        }
                        (el || a).style.display = 'none';
                    }
                });
                document.querySelectorAll('[class*="viewerBadge"], [class*="profileContainer"]').forEach(el => {
                    el.style.display = 'none';
                });
            };
            hide();
            const obs = new MutationObserver(hide);
            obs.observe(document.body, { childList: true, subtree: true });
        })();
        </script>
        """
    st.markdown(hide_style, unsafe_allow_html=True)
    st.components.v1.html(
        """
        <script>
        const root = window.parent.document;
        const hide = () => {
            root.querySelectorAll('a').forEach(a => {
                const href = (a.getAttribute('href') || '').toLowerCase();
                if (
                    href.includes('streamlit.io') ||
                    href.includes('share.streamlit.io') ||
                    (href.includes('github.com/') && a.querySelector('img'))
                ) {
                    let el = a;
                    for (let i = 0; i < 4 && el && el.parentElement; i++) {
                        el = el.parentElement;
                    }
                    (el || a).style.display = 'none';
                }
            });
            root.querySelectorAll('[class*="viewerBadge"], [class*="profileContainer"]').forEach(el => {
                el.style.display = 'none';
            });
        };
        hide();
        new MutationObserver(hide).observe(root.body, { childList: true, subtree: true });
        </script>
        """,
        height=0,
    )

    st.image("main-logo.png")
    st.title("Voucher Issue Resolution System")
    
    # st.markdown(
    #     "_AI-powered workflow automation to eliminate manual email-based issue "
    #     "handling — full visibility, tracking and accountability._"
    # )
    st.divider()
    

    if role == "Finance / Operations":
        finance_logging_view()
    elif role == "Tour Executive":
        executive_view()
    else:
        management_dashboard()


if __name__ == "__main__":
    main()
