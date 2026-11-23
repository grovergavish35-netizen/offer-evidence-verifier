
import json

import streamlit as st

from core.pipeline import verify_offer
from core.pdf_extractor import extract_pdf_text
from core.pdf_report import generate_evidence_pdf
from core.privacy import mask_sensitive_data
from core.schemas import FindingType


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Offer Evidence Verifier",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================
# DESIGN SYSTEM
# ==========================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: #080f1d;
        color: #e5e7eb;
    }

    .block-container {
        max-width: 1320px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        color: #f8fafc !important;
    }

    h1 {
        font-weight: 800 !important;
        letter-spacing: -1px;
    }

    div[data-testid="stMetric"] {
        background: #121e31;
        border: 1px solid #26364f;
        border-radius: 14px;
        padding: 18px;
        min-height: 115px;
    }

    div[data-testid="stMetricLabel"] {
        color: #94a3b8;
    }

    div[data-testid="stMetricValue"] {
        color: #f8fafc;
    }

    div[data-testid="stExpander"] {
        background: #111c2e;
        border: 1px solid #26364f;
        border-radius: 12px;
        margin-bottom: 10px;
    }

    .hero {
        background: linear-gradient(
            120deg,
            #102344 0%,
            #0d1a30 65%,
            #101c31 100%
        );
        border: 1px solid #28436b;
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 25px;
    }

    .hero-title {
        font-size: 34px;
        font-weight: 800;
        color: #f8fafc;
        letter-spacing: -1px;
        margin-bottom: 8px;
    }

    .hero-subtitle {
        color: #a7b8d0;
        font-size: 15px;
        line-height: 1.7;
    }

    .eyebrow {
        color: #60a5fa;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1.6px;
        text-transform: uppercase;
        margin-bottom: 12px;
    }

    .info-panel {
        background: #111c2e;
        border: 1px solid #26364f;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 18px;
    }

    .info-title {
        font-size: 14px;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 8px;
    }

    .info-text {
        font-size: 13px;
        color: #94a3b8;
        line-height: 1.7;
    }

    .section-label {
        color: #60a5fa;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 12px;
    }

    .footer-note {
        color: #64748b;
        font-size: 12px;
        text-align: center;
        margin-top: 35px;
    }

    div.stButton > button[kind="primary"] {
        background: #2563eb;
        border-radius: 10px;
        border: none;
        font-weight: 700;
        min-height: 48px;
    }

    div.stButton > button[kind="primary"]:hover {
        background: #1d4ed8;
    }

    div[data-testid="stFileUploader"] {
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_finding_type(result):
    kind = getattr(
        result,
        "finding_type",
        FindingType.UNKNOWN,
    )

    if isinstance(kind, FindingType):
        return kind.value

    return str(kind)


def safe_report_dict(report):
    data = report.model_dump(mode="json")

    def sanitize(value):
        if isinstance(value, str):
            return mask_sensitive_data(value)

        if isinstance(value, dict):
            return {
                key: sanitize(item)
                for key, item in value.items()
            }

        if isinstance(value, list):
            return [
                sanitize(item)
                for item in value
            ]

        return value

    return sanitize(data)


def show_evidence(result):
    kind = get_finding_type(result)

    icons = {
        "risk_signal": "⚠️",
        "contradiction": "❌",
        "supporting_evidence": "✅",
        "unknown": "🔎",
    }

    label = result.check_name.replace(
        "_", " "
    ).title()

    with st.expander(
        f"{icons.get(kind, '🔎')} {label}"
    ):
        st.markdown("**Finding**")
        st.write(result.finding)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Classification**")
            st.write(
                kind.replace("_", " ").title()
            )

        with col2:
            st.markdown("**Check verdict**")
            st.write(result.verdict.value)

        st.markdown("**Evidence source**")
        st.write(
            result.source or "Not available"
        )

        st.markdown("**Confidence and limitations**")
        st.write(result.confidence_note)

        if result.claim:
            st.caption(
                f"Claim type: {result.claim.claim_type}"
            )


# ==========================================
# SESSION STATE
# ==========================================

if "verification_report" not in st.session_state:
    st.session_state.verification_report = None

if "pdf_report_bytes" not in st.session_state:
    st.session_state.pdf_report_bytes = None


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:
    st.title("🛡️ Trust Console")

    st.caption(
        "Offer Evidence Verifier"
    )

    st.divider()

    st.markdown("### Verification workflow")

    st.write("1. Submit offer text or PDF")
    st.write("2. Configure optional checks")
    st.write("3. Analyze evidence")
    st.write("4. Review findings")
    st.write("5. Download PDF or JSON")

    st.divider()

    st.markdown("### Evidence policy")

    st.info(
        "Risk indicators are not proof of fraud. "
        "Supporting checks do not certify authenticity."
    )

    st.markdown("### Privacy")

    st.caption(
        "Common sensitive-number patterns are "
        "masked before analysis. Names, emails "
        "and other personal information may remain."
    )

    st.divider()

    if st.button(
        "Clear previous report",
        use_container_width=True,
    ):
        st.session_state.verification_report = None
        st.session_state.pdf_report_bytes = None
        st.rerun()


# ==========================================
# HERO
# ==========================================

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">
            Evidence-first verification platform
        </div>
        <div class="hero-title">
            Offer Evidence Verifier
        </div>
        <div class="hero-subtitle">
            Analyze internship and job offers using
            explainable checks, structured evidence,
            and transparent limitations.
            <br>
            Make informed decisions before trusting
            unfamiliar recruitment communications.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# INPUT SECTION
# ==========================================

st.markdown(
    '<div class="section-label">01 / Input</div>',
    unsafe_allow_html=True,
)

st.subheader("Submit an offer")

input_mode = st.radio(
    "Input method",
    ["Paste Text", "Upload PDF"],
    horizontal=True,
)

offer_text = ""

if input_mode == "Paste Text":
    offer_text = st.text_area(
        "Offer content",
        height=240,
        placeholder=(
            "Company: Example Technologies\n"
            "Role: Software Developer Intern\n"
            "Recruiter: hr@example.com\n"
            "No registration fee required."
        ),
    )

else:
    uploaded_file = st.file_uploader(
        "Upload a text-based PDF",
        type=["pdf"],
        help=(
            "Maximum 5 MB and 15 pages. "
            "Scanned image PDFs are not supported."
        ),
    )

    if uploaded_file is not None:
        try:
            offer_text = extract_pdf_text(
                uploaded_file.getvalue()
            )

            st.success(
                "Document text extracted."
            )

            with st.expander(
                "Preview extracted content"
            ):
                st.text(
                    mask_sensitive_data(
                        offer_text
                    )[:5000]
                )

        except Exception as exc:
            st.error(
                f"Could not read PDF: {exc}"
            )


# ==========================================
# CONFIGURATION
# ==========================================

st.markdown(
    '<div class="section-label">02 / Configuration</div>',
    unsafe_allow_html=True,
)

st.subheader("Verification settings")

left, right = st.columns(2)

with left:
    official_domain = st.text_input(
        "Official employer domain",
        placeholder="example.com",
        help=(
            "Optional. Enter only a domain confirmed "
            "independently of the submitted offer."
        ),
    )

with right:
    enable_domain_intelligence = st.checkbox(
        "Enable domain intelligence",
        value=False,
        help=(
            "Perform optional RDAP and DNS lookups. "
            "These can take several seconds."
        ),
    )


# ==========================================
# ANALYSIS
# ==========================================

st.markdown(
    '<div class="section-label">03 / Analysis</div>',
    unsafe_allow_html=True,
)

if st.button(
    "Analyze Offer",
    type="primary",
    use_container_width=True,
):
    st.session_state.verification_report = None
    st.session_state.pdf_report_bytes = None

    if not offer_text.strip():
        st.warning(
            "Please submit offer text or a readable PDF."
        )

    else:
        with st.spinner(
            "Extracting claims and analyzing evidence..."
        ):
            try:
                masked_text = mask_sensitive_data(
                    offer_text
                )

                report = verify_offer(
                    masked_text,
                    official_domain=(
                        official_domain.strip() or None
                    ),
                    enable_domain_intelligence=(
                        enable_domain_intelligence
                    ),
                )

                pdf_bytes = generate_evidence_pdf(
                    report
                )

                st.session_state.verification_report = report
                st.session_state.pdf_report_bytes = pdf_bytes

            except Exception as exc:
                st.error(
                    f"Analysis failed: {exc}"
                )
                st.stop()


# ==========================================
# RESULTS
# ==========================================

report = st.session_state.verification_report

if report is not None:
    st.divider()

    st.markdown(
        '<div class="section-label">04 / Results</div>',
        unsafe_allow_html=True,
    )

    st.subheader("Evidence overview")

    st.success(
        "Analysis completed successfully."
    )

    groups = {
        "risk_signal": [],
        "contradiction": [],
        "supporting_evidence": [],
        "unknown": [],
    }

    for result in report.checks:
        kind = get_finding_type(result)
        groups.setdefault(kind, []).append(result)

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric(
        "Risk signals",
        len(groups["risk_signal"]),
    )

    metric2.metric(
        "Contradictions",
        len(groups["contradiction"]),
    )

    metric3.metric(
        "Supporting checks",
        len(groups["supporting_evidence"]),
    )

    metric4.metric(
        "Unverified",
        len(groups["unknown"]),
    )

    st.caption(
        "Counts describe individual findings. "
        "They are not an authenticity score."
    )

    st.markdown(
        '<div class="section-label">05 / Evidence</div>',
        unsafe_allow_html=True,
    )

    sections = [
        (
            "⚠️ Risk signals",
            groups["risk_signal"],
        ),
        (
            "❌ Contradictions",
            groups["contradiction"],
        ),
        (
            "✅ Supporting evidence",
            groups["supporting_evidence"],
        ),
        (
            "🔎 Unknown / unverified",
            groups["unknown"],
        ),
    ]

    for title, findings in sections:
        st.subheader(title)

        if not findings:
            st.info(
                "No findings in this category."
            )
        else:
            for finding in findings:
                show_evidence(finding)

    st.markdown(
        '<div class="section-label">06 / Next Steps</div>',
        unsafe_allow_html=True,
    )

    st.subheader("Recommended actions")

    for index, step in enumerate(
        report.safe_steps,
        start=1,
    ):
        st.write(
            f"**{index}.** {step}"
        )

    st.info(report.disclaimer)

    st.markdown(
        '<div class="section-label">07 / Export</div>',
        unsafe_allow_html=True,
    )

    st.subheader("Download evidence report")

    st.write(
        "Export the findings as a professional PDF "
        "or machine-readable JSON file."
    )

    pdf_col, json_col = st.columns(2)

    with pdf_col:
        st.download_button(
            "📄 Download PDF Report",
            data=st.session_state.pdf_report_bytes,
            file_name="offer_evidence_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with json_col:
        export_data = safe_report_dict(
            report
        )

        st.download_button(
            "📋 Download JSON Report",
            data=json.dumps(
                export_data,
                indent=2,
                ensure_ascii=False,
            ),
            file_name="offer_evidence_report.json",
            mime="application/json",
            use_container_width=True,
        )


# ==========================================
# FOOTER
# ==========================================

st.markdown(
    """
    <div class="footer-note">
        Offer Evidence Verifier · Evidence-based decision support
        <br>
        No automated finding is a final determination
        of authenticity or fraud.
    </div>
    """,
    unsafe_allow_html=True,
)







