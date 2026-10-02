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

/* ==========================================================
   GLOBAL
   ========================================================== */

html,
body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
    background: #070b14 !important;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(
            circle at 15% 5%,
            rgba(79, 70, 229, 0.18),
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(14, 165, 233, 0.14),
            transparent 25%
        ),
        #070b14 !important;
}

.block-container {
    max-width: 1220px !important;
    padding-top: 2.2rem !important;
    padding-bottom: 5rem !important;
}


/* ==========================================================
   SIDEBAR
   ========================================================== */

[data-testid="stSidebar"] {
    background: #080d18 !important;
    border-right: 1px solid rgba(148, 163, 184, 0.12) !important;
}

[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}

[data-testid="stSidebar"] p {
    color: #94a3b8 !important;
}

[data-testid="stSidebar"] .stCaption {
    color: #64748b !important;
}


/* ==========================================================
   HERO
   ========================================================== */

.hero {
    position: relative;
    overflow: hidden;

    padding: 48px 48px 44px 48px;

    border-radius: 28px;

    background:
        linear-gradient(
            135deg,
            rgba(30, 41, 59, 0.98),
            rgba(15, 23, 42, 0.96)
        );

    border: 1px solid rgba(148, 163, 184, 0.18);

    box-shadow:
        0 30px 80px rgba(0, 0, 0, 0.40);

    margin-bottom: 26px;
}

.hero::after {
    content: "";

    position: absolute;

    width: 300px;
    height: 300px;

    right: -120px;
    top: -150px;

    border-radius: 50%;

    background:
        radial-gradient(
            circle,
            rgba(99, 102, 241, 0.25),
            transparent 70%
        );
}

.eyebrow {
    position: relative;
    z-index: 2;

    display: inline-block;

    padding: 8px 13px;

    border-radius: 999px;

    background: rgba(99, 102, 241, 0.15);

    border: 1px solid rgba(129, 140, 248, 0.30);

    color: #a5b4fc !important;

    font-size: 12px;
    font-weight: 800;

    letter-spacing: 0.08em;

    text-transform: uppercase;
}

.hero h1 {
    position: relative;
    z-index: 2;

    color: #f8fafc !important;

    font-size: 48px !important;

    line-height: 1.08 !important;

    margin-top: 20px !important;
    margin-bottom: 16px !important;

    font-weight: 800 !important;

    letter-spacing: -0.045em !important;
}

.hero p {
    position: relative;
    z-index: 2;

    color: #cbd5e1 !important;

    font-size: 17px;

    max-width: 820px;

    line-height: 1.75;

    margin-bottom: 0;
}


/* ==========================================================
   METRIC CARDS
   ========================================================== */

.metric-card {
    min-height: 105px;

    padding: 21px 22px;

    border-radius: 20px;

    background:
        linear-gradient(
            145deg,
            rgba(15, 23, 42, 0.95),
            rgba(15, 23, 42, 0.75)
        );

    border: 1px solid rgba(148, 163, 184, 0.14);

    box-shadow:
        0 15px 40px rgba(0, 0, 0, 0.18);
}

.metric-number {
    color: #f8fafc !important;

    font-size: 30px;

    line-height: 1;

    font-weight: 800;

    margin-bottom: 10px;
}

.metric-label {
    color: #94a3b8 !important;

    font-size: 13px;

    font-weight: 500;
}


/* ==========================================================
   SECTION TITLES
   ========================================================== */

.section-title {
    color: #f8fafc !important;

    font-size: 23px;

    font-weight: 750;

    margin-top: 32px;
    margin-bottom: 13px;
}

.small-muted {
    color: #94a3b8 !important;

    font-size: 13px;
}


/* ==========================================================
   TEXT AREA
   ========================================================== */

[data-testid="stTextArea"] label {
    color: #f8fafc !important;

    font-weight: 600 !important;
}

[data-testid="stTextArea"] textarea {
    background: #f8fafc !important;

    color: #0f172a !important;

    border: 1px solid #334155 !important;

    border-radius: 16px !important;

    font-size: 15px !important;

    line-height: 1.6 !important;
}

[data-testid="stTextArea"] textarea::placeholder {
    color: #64748b !important;

    opacity: 1 !important;
}

[data-testid="stTextArea"] textarea:focus {
    border: 2px solid #818cf8 !important;

    box-shadow:
        0 0 0 3px rgba(99, 102, 241, 0.16) !important;
}


/* ==========================================================
   BUTTONS
   ========================================================== */

.stButton > button {
    min-height: 46px;

    border-radius: 13px !important;

    border: 1px solid rgba(148, 163, 184, 0.18) !important;

    background: #111827 !important;

    color: #e2e8f0 !important;

    font-weight: 600 !important;

    transition:
        transform 0.15s ease,
        border-color 0.15s ease,
        background 0.15s ease;
}

.stButton > button:hover {
    transform: translateY(-1px);

    border-color: rgba(129, 140, 248, 0.65) !important;

    background: #172033 !important;

    color: #ffffff !important;
}


/* Primary button */

.stButton > button[kind="primary"] {
    min-height: 54px !important;

    border: none !important;

    border-radius: 15px !important;

    background:
        linear-gradient(
            135deg,
            #6366f1,
            #4f46e5
        ) !important;

    color: #ffffff !important;

    font-size: 16px !important;

    font-weight: 750 !important;

    box-shadow:
        0 12px 30px rgba(79, 70, 229, 0.28);
}

.stButton > button[kind="primary"]:hover {
    background:
        linear-gradient(
            135deg,
            #818cf8,
            #6366f1
        ) !important;

    color: #ffffff !important;

    transform: translateY(-1px);
}


/* ==========================================================
   STATUS COMPONENTS
   ========================================================== */

[data-testid="stStatusWidget"] {
    background: rgba(15, 23, 42, 0.85) !important;

    border: 1px solid rgba(148, 163, 184, 0.14) !important;

    border-radius: 16px !important;

    color: #e2e8f0 !important;
}

[data-testid="stStatusWidget"] * {
    color: #e2e8f0 !important;
}


/* ==========================================================
   PROGRESS BAR
   ========================================================== */

[data-testid="stProgressBar"] {
    margin-bottom: 20px;
}

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


/* ==========================================================
   REPORT
   ========================================================== */

.report-box {
    padding: 32px;

    border-radius: 22px;

    background:
        linear-gradient(
            145deg,
            rgba(15, 23, 42, 0.95),
            rgba(15, 23, 42, 0.78)
        );

    border: 1px solid rgba(148, 163, 184, 0.14);

    box-shadow:
        0 20px 60px rgba(0, 0, 0, 0.22);
}

.report-box h1,
.report-box h2,
.report-box h3 {
    color: #f8fafc !important;
}

.report-box p,
.report-box li {
    color: #cbd5e1 !important;

    line-height: 1.75;
}

.report-box strong {
    color: #f1f5f9 !important;
}

.report-box a {
    color: #93c5fd !important;
}


/* ==========================================================
   EXPANDER
   ========================================================== */

[data-testid="stExpander"] {
    background: rgba(15, 23, 42, 0.70) !important;

    border: 1px solid rgba(148, 163, 184, 0.14) !important;

    border-radius: 16px !important;
}

[data-testid="stExpander"] summary {
    color: #e2e8f0 !important;

    font-weight: 600 !important;
}


/* ==========================================================
   ALERTS
   ========================================================== */

[data-testid="stAlert"] {
    border-radius: 14px !important;
}


/* ==========================================================
   DOWNLOAD BUTTON
   ========================================================== */

[data-testid="stDownloadButton"] button {
    min-height: 48px;

    border-radius: 13px !important;

    background: #111827 !important;

    color: #e2e8f0 !important;

    border: 1px solid rgba(148, 163, 184, 0.20) !important;

    font-weight: 650 !important;
}

[data-testid="stDownloadButton"] button:hover {
    border-color: #818cf8 !important;

    color: #ffffff !important;
}


/* ==========================================================
   MOBILE
   ========================================================== */

@media (max-width: 768px) {

    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    .hero {
        padding: 30px 25px;
    }

    .hero h1 {
        font-size: 34px !important;
    }

    .hero p {
        font-size: 15px;
    }

}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            font-size: 22px;
            font-weight: 800;
            color: #f8fafc;
            margin-bottom: 8px;
        ">
            ◈ ResearchOS
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="
            color: #94a3b8;
            font-size: 13px;
            line-height: 1.6;
            margin-bottom: 20px;
        ">
            Multi-agent research powered by CrewAI + Groq.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown(
        """
        <div style="
            color: #f8fafc;
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 14px;
        ">
            Research Pipeline
        </div>
        """,
        unsafe_allow_html=True,
    )

    pipeline_items = [
        ("01", "Research Manager"),
        ("02", "Web Research"),
        ("03", "Academic Research"),
        ("04", "Industry / Market"),
        ("05", "Synthesizer"),
    ]

    for number, name in pipeline_items:

        st.markdown(
            f"""
            <div style="
                display:flex;
                align-items:center;
                gap:10px;
                padding:7px 0;
                color:#cbd5e1;
                font-size:13px;
            ">
                <span style="
                    color:#818cf8;
                    font-weight:700;
                    width:24px;
                ">
                    {number}
                </span>

                <span>{name}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    st.markdown(
        """
        <div style="
            color: #f8fafc;
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 12px;
        ">
            Model
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.code(
        "openai/gpt-oss-120b",
        language="text",
    )

    st.markdown(
        """
        <div style="
            color:#64748b;
            font-size:12px;
            margin-top:-5px;
        ">
            Groq-hosted GPT-OSS 120B
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown(
        """
        <div style="
            color:#64748b;
            font-size:11px;
            line-height:1.6;
        ">
            Research results should be verified before being
            used for high-stakes decisions.
        </div>
        """,
        unsafe_allow_html=True,
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
            academic researcher, industry analyst, and final
            synthesizer to turn one question into a structured,
            evidence-based research report.
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
# RESEARCH QUESTION
# ============================================================

st.markdown(
    """
    <div class="section-title">
        What do you want to research?
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# EXAMPLE QUESTION STATE
# ============================================================

if "question" not in st.session_state:
    st.session_state.question = ""


question = st.text_area(
    "Research question",
    value=st.session_state.question,
    placeholder=(
        "Example: What are the major applications of "
        "generative AI in healthcare in 2026?"
    ),
    height=125,
    label_visibility="collapsed",
)


# Keep typed question
st.session_state.question = question


# ============================================================
# EXAMPLES
# ============================================================

st.markdown(
    """
    <div class="small-muted" style="margin-top:10px;">
        Try an example
    </div>
    """,
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

            st.session_state.question = example

            st.rerun()


# ============================================================
# START BUTTON
# ============================================================

st.markdown(
    "<div style='height:8px'></div>",
    unsafe_allow_html=True,
)

start = st.button(
    "🚀  Start Research",
    type="primary",
    use_container_width=True,
)


# ============================================================
# RUN RESEARCH
# ============================================================

if start:

    research_question = st.session_state.question.strip()

    if not research_question:

        st.warning(
            "Please enter a research question first."
        )

        st.stop()

    st.markdown(
        """
        <div class="section-title">
            Research Pipeline
        </div>
        """,
        unsafe_allow_html=True,
    )

    progress = st.progress(0)

    # ========================================================
    # AGENT STATUS
    # ========================================================

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


    # ========================================================
    # STATUS CALLBACK
    # ========================================================

    def update_status(stage, state, label):

        status = statuses.get(stage)

        if status:

            status.update(
                label=label,
                state=state,
                expanded=(state == "running"),
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
                progress.progress(82)

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
        # FINAL REPORT
        # ====================================================

        st.markdown(
            """
            <div class="section-title">
                Final Research Report
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="report-box">',
            unsafe_allow_html=True,
        )

        st.markdown(
            result["report"]
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True,
        )


        # ====================================================
        # DOWNLOAD
        # ====================================================

        st.markdown(
            "<div style='height:12px'></div>",
            unsafe_allow_html=True,
        )

        st.download_button(
            label="⬇️  Download Research Report",
            data=result["report"],
            file_name="research_report.md",
            mime="text/markdown",
            use_container_width=True,
        )


        # ====================================================
        # RESEARCH PLAN
        # ====================================================

        with st.expander(
            "🧭 View Research Manager Plan"
        ):

            st.markdown(
                result["research_plan"]
            )


    except Exception as e:

        progress.empty()

        st.error(
            "The research pipeline encountered an error."
        )

        with st.expander(
            "Technical error details"
        ):

            st.exception(e)
