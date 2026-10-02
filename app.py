import streamlit as st

from crew import run_research


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ResearchOS",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

@import url(
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
);

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(
            circle at 10% 10%,
            rgba(99, 102, 241, 0.16),
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(14, 165, 233, 0.12),
            transparent 25%
        ),
        #070b14;
}

.block-container {
    max-width: 1200px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

.hero {
    padding: 42px;
    border-radius: 28px;
    background:
        linear-gradient(
            135deg,
            rgba(30, 41, 59, 0.96),
            rgba(15, 23, 42, 0.92)
        );
    border: 1px solid rgba(148, 163, 184, 0.16);
    box-shadow:
        0 30px 80px rgba(0, 0, 0, 0.30);
    margin-bottom: 24px;
}

.eyebrow {
    display: inline-block;
    padding: 7px 12px;
    border-radius: 999px;
    background: rgba(99, 102, 241, 0.14);
    border: 1px solid rgba(129, 140, 248, 0.22);
    color: #a5b4fc;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.hero h1 {
    font-size: 48px;
    line-height: 1.05;
    margin: 18px 0 12px 0;
    font-weight: 800;
    letter-spacing: -0.04em;
}

.hero p {
    color: #94a3b8;
    font-size: 17px;
    max-width: 780px;
    line-height: 1.7;
}

.metric-card {
    padding: 22px;
    border-radius: 20px;
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.13);
}

.metric-number {
    font-size: 28px;
    font-weight: 800;
}

.metric-label {
    color: #94a3b8;
    font-size: 13px;
    margin-top: 5px;
}

.section-title {
    font-size: 22px;
    font-weight: 750;
    margin: 30px 0 12px 0;
}

.agent-card {
    padding: 18px;
    border-radius: 18px;
    background: rgba(15, 23, 42, 0.70);
    border: 1px solid rgba(148, 163, 184, 0.12);
}

.small-muted {
    color: #64748b;
    font-size: 13px;
}

textarea {
    border-radius: 16px !important;
}

button[kind="primary"] {
    border-radius: 14px !important;
    font-weight: 700 !important;
}

[data-testid="stSidebar"] {
    background: #090e19;
    border-right: 1px solid rgba(148, 163, 184, 0.10);
}

.report-box {
    padding: 30px;
    border-radius: 22px;
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.12);
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## ◈ ResearchOS")

    st.markdown(
        """
        <div class="small-muted">
        Multi-agent research powered by CrewAI + Groq.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### Pipeline")

    st.markdown(
        """
        **01** Research Manager  
        **02** Web Research  
        **03** Academic Research  
        **04** Industry / Market Research  
        **05** Synthesizer
        """
    )

    st.divider()

    st.markdown("### Model")

    st.code(
        "openai/gpt-oss-120b",
        language="text"
    )

    st.caption(
        "Groq-hosted GPT-OSS 120B"
    )

    st.divider()

    st.caption(
        "Research results should be verified before being used "
        "for high-stakes decisions."
    )


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
<div class="hero">

<div class="eyebrow">
MULTI-AGENT RESEARCH
</div>

<h1>
Research anything.<br>
From multiple perspectives.
</h1>

<p>
ResearchOS coordinates a research manager, web researcher,
academic researcher, industry analyst, and final synthesizer
to turn one question into a structured evidence-based report.
</p>

</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# METRICS
# ============================================================

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-number">5</div>
            <div class="metric-label">AI Agents</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:

    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-number">3</div>
            <div class="metric-label">Parallel Research Streams</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:

    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-number">∞</div>
            <div class="metric-label">Research Questions</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:

    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-number">1</div>
            <div class="metric-label">Final Report</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# INPUT
# ============================================================

st.markdown(
    '<div class="section-title">What do you want to research?</div>',
    unsafe_allow_html=True,
)

question = st.text_area(
    "Research question",
    placeholder=(
        "Example: What are the major applications of "
        "generative AI in healthcare in 2026?"
    ),
    height=130,
    label_visibility="collapsed",
)


# ============================================================
# EXAMPLES
# ============================================================

st.markdown(
    '<div class="small-muted">Try an example</div>',
    unsafe_allow_html=True,
)

example_cols = st.columns(3)

examples = [
    "How is AI changing software development in 2026?",
    "What are the business opportunities in humanoid robotics?",
    "What does academic research say about AI tutoring?",
]

for col, example in zip(example_cols, examples):

    with col:

        if st.button(
            example,
            use_container_width=True,
        ):

            st.session_state["question"] = example

            st.rerun()


if "question" in st.session_state and not question:

    question = st.session_state["question"]


# ============================================================
# START BUTTON
# ============================================================

start = st.button(
    "🚀 Start Research",
    type="primary",
    use_container_width=True,
)


# ============================================================
# RESEARCH PIPELINE
# ============================================================

if start:

    if not question.strip():

        st.warning(
            "Please enter a research question first."
        )

        st.stop()

    st.markdown(
        '<div class="section-title">Research Pipeline</div>',
        unsafe_allow_html=True,
    )

    progress = st.progress(0)

    # --------------------------------------------------------
    # STATUS CONTAINERS
    # --------------------------------------------------------

    manager_status = st.status(
        "🧭 Research Manager — waiting",
        expanded=False,
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        web_status = st.status(
            "🌐 Web Research — waiting",
            expanded=False,
        )

    with col2:

        academic_status = st.status(
            "🎓 Academic Research — waiting",
            expanded=False,
        )

    with col3:

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

    # --------------------------------------------------------
    # CALLBACK
    # --------------------------------------------------------

    def update_status(stage, state, label):

        status = statuses.get(stage)

        if status:

            status.update(
                label=label,
                state=state,
                expanded=(state == "running"),
            )

        # Approximate visual progress
        progress_values = {
            "manager": 20,
            "web": 45,
            "academic": 45,
            "industry": 45,
            "synthesizer": 85,
        }

        if state == "running":

            progress.progress(
                progress_values.get(stage, 20)
            )

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

    # --------------------------------------------------------
    # RUN
    # --------------------------------------------------------

    try:

        result = run_research(
            question,
            status_callback=update_status,
        )

        progress.progress(100)

        st.success(
            "Research completed successfully."
        )

        # ----------------------------------------------------
        # REPORT
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">Final Research Report</div>',
            unsafe_allow_html=True,
        )

        with st.container():

            st.markdown(
                '<div class="report-box">',
                unsafe_allow_html=True,
            )

            st.markdown(
                result["report"]
            )

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        st.download_button(
            label="⬇️ Download Research Report",
            data=result["report"],
            file_name="research_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

        # ----------------------------------------------------
        # RESEARCH PLAN
        # ----------------------------------------------------

        with st.expander(
            "View Research Manager Plan"
        ):

            st.markdown(
                result["research_plan"]
            )

    except Exception as e:

        progress.empty()

        st.error(
            f"Research pipeline failed: {str(e)}"
        )

        with st.expander(
            "Technical error"
        ):

            st.exception(e)
