import streamlit as st
import pandas as pd
from datetime import date, datetime

from agent import WaterIntakeAgent
from database import get_intake_history, log_intake


st.set_page_config(
    page_title="AI Water Intake Tracker",
    page_icon="💧",
    layout="wide",
)

if "tracker_started" not in st.session_state:
    st.session_state.tracker_started = False
if "user_id" not in st.session_state:
    st.session_state.user_id = "guest"
if "daily_goal" not in st.session_state:
    st.session_state.daily_goal = 3000
if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = ""
if "last_logged_ml" not in st.session_state:
    st.session_state.last_logged_ml = 0


def load_history(user_id: str) -> pd.DataFrame:
    records = get_intake_history(user_id)
    if not records:
        return pd.DataFrame(columns=["intake_ml", "date"])
    return pd.DataFrame(records, columns=["intake_ml", "date"])


def get_today_total(history: pd.DataFrame) -> int:
    if history.empty:
        return 0
    today = date.today().isoformat()
    today_rows = history[history["date"] == today]
    if today_rows.empty:
        return 0
    return int(today_rows["intake_ml"].sum())


st.markdown(
    """
    <style>
        .block-container { padding-top: 2rem; }
        .hero {
            padding: 2rem;
            border-radius: 24px;
            background: linear-gradient(135deg, rgba(26,115,232,0.14), rgba(0,184,212,0.12));
            border: 1px solid rgba(120,140,160,0.18);
        }
        .metric-card {
            padding: 1rem 1.2rem;
            border-radius: 18px;
            background: rgba(255,255,255,0.6);
            border: 1px solid rgba(120,140,160,0.18);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if not st.session_state.tracker_started:
    st.markdown(
        """
        <div class="hero">
            <h1>Welcome to the AI Water Intake Tracker</h1>
            <p>Track your daily hydration, review your history, and get AI guidance on whether you should drink more water.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    c1, c2, c3 = st.columns(3)
    c1.metric("Daily target", "3 L")
    c2.metric("AI analysis", "On demand")
    c3.metric("History", "Saved locally")

    if st.button("Start Tracking", type="primary"):
        st.session_state.tracker_started = True
        st.rerun()
else:
    st.title("AI Water Intake Dashboard")
    st.caption("Log your hydration, watch your progress, and get a quick AI-based suggestion.")

    with st.sidebar:
        st.header("Profile")
        st.session_state.user_id = st.text_input("User ID", value=st.session_state.user_id)
        st.session_state.daily_goal = st.number_input(
            "Daily goal (ml)", min_value=500, max_value=10000, value=st.session_state.daily_goal, step=250
        )
        if st.button("Reset session"):
            st.session_state.tracker_started = False
            st.session_state.last_analysis = ""
            st.session_state.last_logged_ml = 0
            st.rerun()

    history = load_history(st.session_state.user_id)
    today_total = get_today_total(history)
    remaining = max(st.session_state.daily_goal - today_total, 0)
    progress = min(today_total / st.session_state.daily_goal, 1.0) if st.session_state.daily_goal else 0

    top_left, top_mid, top_right = st.columns(3)
    top_left.metric("Today's total", f"{today_total} ml")
    top_mid.metric("Daily goal", f"{st.session_state.daily_goal} ml")
    top_right.metric("Remaining", f"{remaining} ml")

    st.progress(progress)

    form_col, insight_col = st.columns([1, 1])
    with form_col:
        st.subheader("Log water intake")
        with st.form("log_intake_form", clear_on_submit=False):
            intake_ml = st.number_input("Amount (ml)", min_value=1, max_value=5000, value=250, step=50)
            submitted = st.form_submit_button("Save intake")
        if submitted:
            log_intake(st.session_state.user_id, int(intake_ml))
            agent = WaterIntakeAgent()
            updated_total = today_total + int(intake_ml)
            st.session_state.last_logged_ml = int(intake_ml)
            st.session_state.last_analysis = agent.analyse_intake(updated_total)
            st.success(f"Saved {int(intake_ml)} ml for {st.session_state.user_id}.")
            st.rerun()

    with insight_col:
        st.subheader("AI insight")
        if st.session_state.last_analysis:
            st.write(st.session_state.last_analysis)
        else:
            st.info("Log water intake to get a hydration recommendation.")

        st.subheader("Quick summary")
        st.write(f"User: `{st.session_state.user_id}`")
        st.write(f"Last entry: `{st.session_state.last_logged_ml} ml`")
        st.write(f"Last updated: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")

    st.subheader("Intake history")
    if history.empty:
        st.info("No intake records yet.")
    else:
        st.dataframe(history.sort_values(["date"], ascending=False), use_container_width=True)
        daily_history = history.copy()
        daily_history["date"] = pd.to_datetime(daily_history["date"])
        daily_summary = daily_history.groupby(daily_history["date"].dt.date)["intake_ml"].sum().reset_index()
        daily_summary.columns = ["date", "intake_ml"]
        st.line_chart(daily_summary.set_index("date"))
