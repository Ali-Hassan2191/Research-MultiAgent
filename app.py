import streamlit as st


from crew import run_research


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="ResearchOS",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS ONLY
# ============================================================

st.markdown(
    """
<style>

html,
body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"] {
    background: #070b14 !important;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(
            circle at 10% 0%,
            rgba(79, 70, 229, 0.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 95% 5%,
            rgba(14, 165, 233, 0.12),
            transparent 25%
        ),
        #070b14 !important;
}

.block-container {
    max-width: 1180px !important;
    padding-top: 2rem !important;
    padding-bottom: 5rem !important;
}


/* Sidebar */

[data-testid="stSidebar"] {
    background: #080d18 !important;
    border-right: 1px solid rgba(148,163,184,.12) !important;
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label {
    color: #cbd5e1 !important;
}


/* Headings */

h1,
h2,
h3,
h4 {
    color: #f8fafc !important;
}


/* Normal text */

p,
li {
    color: #cbd5e1;
}


/* Text area */

textarea {
    background: #f8fafc !important;
    color: #0f172a !important;
    border-radius: 15px !important;
    border: 1px solid #334155 !important;
}

textarea::placeholder {
    color: #64748b !important;
}


/* Buttons */

.stButton > button {
    border-radius: 13px !important;
    min-height: 46px !important;

    background: #111827 !important;

    border: 1px solid rgba(148,163,184,.18) !important;

    color: #e2e8f0 !important;

    font-weight: 600 !important;
}

.stButton > button:hover {
    background: #1e293b !important;

    border-color: #818cf8 !important;

    color: #ffffff !important;
}


/* Primary button */

.stButton > button[kind="primary"] {
    background:
        linear-gradient(
            135deg,
            #6366f1,
            #4f46e5
        ) !important;

    color: #ffffff !important;

    border: none !important;

    min-height: 52px !important;

    font-size: 16px !important;

    font-weight: 750 !important;
}


/* Status */

[data-testid="stStatusWidget"] {
    background: #101a2d !important;

    border: 1px solid rgba(148,163,184,.15) !important;

    border-radius: 15px !important;
}

[data-testid="stStatusWidget"] * {
    color: #e2e8f0 !important;
}


/* Progress */

[data-testid="stProgressBar"] > div {
    background: #1e293b !important;
}

[data-testid="stProgressBar"] > div > div {
    background:
        linear-gradient(
            90deg,
            #6366f1,
            #38bdf8
        ) !important;
}


/* Download */

[data-testid="stDownloadButton"] button {
    border-radius: 13px !important;

    background: #111827 !important;

    color: #e2e8f0 !important;

    border: 1px solid rgba(148,163,184,.20) !important;
}


/* Cards */

[data-testid="stMetric"] {
    background: #101a2d !important;

    border: 1px solid rgba(148,163,184,.14) !important;

    border-radius: 18px !important;

    padding: 15px !important;
}

[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
}

[data-testid="stMetricValue"] {
    color: #ffffff !important;
}


/* Expanders */

[data-testid="stExpander"] {
    background: #101a2d !important;

    border: 1px solid rgba(148,163,184,.14) !important;

    border-radius: 15px !important;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("◈ ResearchOS")

    st.caption(
        "Multi-agent research powered by CrewAI + Groq."
    )

    st.divider()

    st.subheader("Research Pipeline")

    st.markdown(
        """
        **01** — Research Manager

        **02** — Web Research

        **03** — Academic Research

        **04** — Industry / Market

        **05** — Synthesizer
        """
    )

    st.divider()

    st.subheader("Model")

    st.code(
        "openai/gpt-oss-120b",
        language="text",
    )

    st.caption(
        "Groq-hosted GPT-OSS 120B"
    )

    st.divider()

    st.caption(
        "Research outputs should be verified before being "
        "used for high-stakes decisions."
    )


# ============================================================
# HERO
# ============================================================

st.title(
    "Research anything."
)

st.header(
    "From multiple perspectives."
)

st.write(
    """
    ResearchOS coordinates five specialized AI agents:
    a research manager, web researcher, academic researcher,
    industry researcher, and final synthesizer.
    """
)


# ============================================================
# METRICS
# ============================================================

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "AI Agents",
        "5",
    )

with c2:
    st.metric(
        "Research Streams",
        "3",
    )

with c3:
    st.metric(
        "Research Questions",
        "∞",
    )

with c4:
    st.metric(
        "Final Report",
        "1",
    )


# ============================================================
# QUESTION
# ============================================================

st.subheader(
    "What do you want to research?"
)


if "question" not in st.session_state:

    st.session_state.question = ""


question = st.text_area(
    "Research question",

    value=st.session_state.question,

    placeholder=(
        "Example: What are the major applications of "
        "generative AI in healthcare in 2026?"
    ),

    height=130,

    label_visibility="collapsed",
)


st.session_state.question = question


# ============================================================
# EXAMPLES
# ============================================================

st.caption("Try an example")

example_1, example_2, example_3 = st.columns(3)


with example_1:

    if st.button(
        "AI in software development",
        use_container_width=True,
    ):

        st.session_state.question = (
            "How is AI changing software development in 2026?"
        )

        st.rerun()


with example_2:

    if st.button(
        "Humanoid robotics",
        use_container_width=True,
    ):

        st.session_state.question = (
            "What are the business opportunities "
            "in humanoid robotics?"
        )

        st.rerun()


with example_3:

    if st.button(
        "AI tutoring research",
        use_container_width=True,
    ):

        st.session_state.question = (
            "What does academic research say "
            "about AI tutoring?"
        )

        st.rerun()


# ============================================================
# START
# ============================================================

st.write("")

start = st.button(
    "🚀 Start Research",
    type="primary",
    use_container_width=True,
)


# ============================================================
# RUN PIPELINE
# ============================================================

if start:

    research_question = (
        st.session_state.question.strip()
    )


    if not research_question:

        st.warning(
            "Please enter a research question first."
        )

        st.stop()


    st.subheader(
        "Research Pipeline"
    )


    progress = st.progress(0)


    # ========================================================
    # AGENT STATUS
    # ========================================================

    manager_status = st.status(
        "🧭 Research Manager — waiting",
        expanded=False,
    )


    web_col, academic_col, industry_col = st.columns(3)


    with web_col:

        web_status = st.status(
            "🌐 Web Research — waiting",
            expanded=False,
        )


    with academic_col:

        academic_status = st.status(
            "🎓 Academic Research — waiting",
            expanded=False,
        )


    with industry_col:

        industry_status = st.status(
            "📊 Industry Research — waiting",
            expanded=False,
        )


    synthesizer_status = st.status(
        "✍️ Synthesizer — waiting",
        expanded=False,
    )


    statuses = {
        "manager": manager_status,
        "web": web_status,
        "academic": academic_status,
        "industry": industry_status,
        "synthesizer": synthesizer_status,
    }


    # ========================================================
    # CALLBACK
    # ========================================================

    def update_status(
        stage,
        state,
        label,
    ):

        status = statuses.get(stage)


        if status:

            status.update(
                label=label,
                state=state,
                expanded=(
                    state == "running"
                ),
            )


        if state == "running":

            if stage == "manager":

                progress.progress(15)

            elif stage in {
                "web",
                "academic",
                "industry",
            }:

                progress.progress(40)

            elif stage == "synthesizer":

                progress.progress(80)


        elif state == "complete":

            if stage == "manager":

                progress.progress(30)

            elif stage in {
                "web",
                "academic",
                "industry",
            }:

                progress.progress(70)

            elif stage == "synthesizer":

                progress.progress(100)


    # ========================================================
    # EXECUTE
    # ========================================================

    try:

        result = run_research(
            research_question,
            status_callback=update_status,
        )


        progress.progress(100)


        st.success(
            "Research completed successfully."
        )


        # ====================================================
        # REPORT
        # ====================================================

        st.subheader(
            "Final Research Report"
        )


        st.markdown(
            result["report"]
        )


        # ====================================================
        # DOWNLOAD
        # ====================================================

        st.download_button(
            "⬇️ Download Research Report",

            data=result["report"],

            file_name="research_report.md",

            mime="text/markdown",

            use_container_width=True,
        )


        # ====================================================
        # PLAN
        # ====================================================

        with st.expander(
            "🧭 View Research Manager Plan"
        ):

            st.markdown(
                result["research_plan"]
            )


    except Exception as error:

        st.error(
            "The research pipeline encountered an error."
        )

        with st.expander(
            "Technical error details"
        ):

            st.exception(error)
