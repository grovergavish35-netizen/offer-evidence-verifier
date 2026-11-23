
import json
from html import escape

import streamlit as st

from core.pipeline import verify_offer
from core.pdf_extractor import extract_pdf_text
from core.pdf_report import generate_evidence_pdf
from core.privacy import mask_sensitive_data
from core.schemas import FindingType


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Offer Evidence Verifier | Trust Console",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================================================
# DESIGN SYSTEM
# ==================================================

st.markdown(
    """
<style>
:root {
    --background: #F8F7F4;
    --surface: #FFFFFF;
    --navy: #172B4D;
    --teal: #0F766E;
    --text: #334155;
    --muted: #64748B;
    --border: #DFE5EC;
}

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: var(--background);
    color: var(--text);
}

.block-container {
    max-width: 1280px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

.stApp h1,
.stApp h2,
.stApp h3 {
    color: var(--navy);
    letter-spacing: -0.5px;
}

.stApp p,
.stApp label,
.stApp li {
    color: var(--text);
}

/* Sidebar */

[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--navy);
}

[data-testid="stSidebar"] p,
[data-testid="stSidebar"] li {
    color: var(--text);
}

/* Inputs */

.stTextArea textarea,
.stTextInput input {
    background: #FFFFFF !important;
    color: #172B4D !important;
    -webkit-text-fill-color: #172B4D !important;
    border: 1px solid #A9B8C9 !important;
    border-radius: 10px !important;
    caret-color: #0F766E !important;
}

.stTextArea textarea::placeholder,
.stTextInput input::placeholder {
    color: #64748B !important;
    -webkit-text-fill-color: #64748B !important;
    opacity: 1 !important;
}

.stTextArea textarea:focus,
.stTextInput input:focus {
    border-color: #0F766E !important;
}

/* Radio / Checkbox */

[data-testid="stRadio"] label p,
[data-testid="stCheckbox"] label p {
    color: #172B4D !important;
}

/* Buttons */

div.stButton > button[kind="primary"] {
    background: #0F766E !important;
    border: 1px solid #0F766E !important;
    color: #FFFFFF !important;
    border-radius: 10px !important;
    min-height: 48px;
    font-weight: 700;
}

div.stButton > button[kind="primary"] *,
div.stButton > button[kind="primary"] p {
    color: #FFFFFF !important;
}

div.stButton > button[kind="primary"]:hover {
    background: #115E59 !important;
    border-color: #115E59 !important;
}

div.stButton > button[kind="secondary"],
div.stDownloadButton > button {
    background: #FFFFFF !important;
    color: #172B4D !important;
    border: 1px solid #C5D0DC !important;
    border-radius: 10px !important;
    min-height: 44px;
}

div.stButton > button[kind="secondary"] *,
div.stDownloadButton > button * {
    color: #172B4D !important;
}

div.stDownloadButton > button:hover,
div.stButton > button[kind="secondary"]:hover {
    background: #EFF8F6 !important;
    border-color: #0F766E !important;
}

/* Header */

.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 20px;
}

.brand-title {
    color: #172B4D;
    font-size: 25px;
    font-weight: 800;
    letter-spacing: -0.8px;
}

.brand-subtitle {
    color: #64748B;
    font-size: 13px;
    margin-top: 3px;
}

.topbar-badge {
    color: #0F766E;
    background: #E8F6F2;
    border: 1px solid #BCE6D9;
    padding: 8px 12px;
    border-radius: 30px;
    font-size: 12px;
    font-weight: 700;
}

/* Hero */

.hero {
    background: linear-gradient(
        115deg,
        #172B4D 0%,
        #234765 65%,
        #176C74 100%
    );
    padding: 30px 34px;
    border-radius: 18px;
    margin-bottom: 24px;
    box-shadow: 0 8px 24px rgba(23,43,77,0.10);
}

.hero-eyebrow {
    color: #99F6E4;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.5px;
    margin-bottom: 12px;
}

.hero-title {
    color: #FFFFFF;
    font-size: clamp(26px, 3.4vw, 35px);
    font-weight: 800;
    line-height: 1.25;
    margin-bottom: 10px;
}

.hero-description {
    color: #E2E8F0;
    font-size: 14px;
    line-height: 1.75;
    max-width: 760px;
}

/* Sections */

.section-eyebrow {
    color: #0F766E;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    margin: 22px 0 7px;
}

.section-title {
    color: #172B4D;
    font-size: 23px;
    font-weight: 750;
    margin-bottom: 14px;
}

/* Workflow */

.workflow {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 20px;
}

.workflow-step {
    background: #FFFFFF;
    border: 1px solid #DFE5EC;
    border-radius: 10px;
    padding: 10px 13px;
    color: #52647B;
    font-size: 12px;
    font-weight: 600;
}

.workflow-step.active {
    background: #E8F6F2;
    border-color: #9AD6C6;
    color: #0F766E;
}

/* Metric cards */

.metric-card {
    background: #FFFFFF;
    border: 1px solid #DFE5EC;
    border-radius: 15px;
    padding: 18px;
    min-height: 132px;
    box-shadow: 0 3px 10px rgba(23,43,77,0.03);
}

.metric-label {
    color: #52647B;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 10px;
}

.metric-value {
    font-size: 32px;
    font-weight: 800;
    line-height: 1.1;
}

.metric-caption {
    color: #64748B;
    font-size: 11px;
    margin-top: 9px;
}

/* Evidence cards */

.evidence-card {
    background: #FFFFFF;
    border: 1px solid #DFE5EC;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 14px;
    box-shadow: 0 3px 10px rgba(23,43,77,0.03);
}

.evidence-heading {
    color: #172B4D;
    font-size: 16px;
    font-weight: 750;
    margin-bottom: 10px;
}

.evidence-badge {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 7px;
    font-size: 11px;
    font-weight: 700;
    margin-bottom: 12px;
}

.evidence-body {
    color: #334155;
    font-size: 13px;
    line-height: 1.75;
    overflow-wrap: anywhere;
}

.evidence-meta {
    color: #64748B;
    font-size: 12px;
    line-height: 1.7;
    margin-top: 12px;
    overflow-wrap: anywhere;
}

/* Sidebar info */

.sidebar-card {
    background: #EAF1F8;
    border: 1px solid #CBDDED;
    border-left: 4px solid #0F766E;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 12px;
}

.sidebar-card-title {
    color: #172B4D;
    font-size: 13px;
    font-weight: 750;
    margin-bottom: 6px;
}

.sidebar-card-body {
    color: #334155;
    font-size: 12px;
    line-height: 1.7;
}

/* Export */

.export-panel {
    background: #FFFFFF;
    border: 1px solid #DFE5EC;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 16px;
}

.footer-note {
    text-align: center;
    color: #64748B;
    font-size: 12px;
    margin-top: 38px;
    line-height: 1.8;
}

@media (max-width: 768px) {
    .topbar {
        flex-direction: column;
        align-items: flex-start;
    }

    .hero {
        padding: 23px;
    }

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


# ==================================================
# HELPERS
# ==================================================

def html_safe(value):
    """
    Mask recognized sensitive-number patterns
    and escape HTML characters.
    """
    if value is None:
        return "Not available"

    return escape(
        mask_sensitive_data(str(value))
    ).replace("\n", "<br>")


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


def section(eyebrow, title):
    st.markdown(
        (
            '<div class="section-eyebrow">'
            + html_safe(eyebrow)
            + '</div>'
            '<div class="section-title">'
            + html_safe(title)
            + '</div>'
        ),
        unsafe_allow_html=True,
    )


def render_metric(label, value, caption, color):
    st.markdown(
        (
            '<div class="metric-card">'
            '<div class="metric-label">'
            + html_safe(label)
            + '</div>'
            '<div class="metric-value" style="color:'
            + color
            + '">'
            + html_safe(value)
            + '</div>'
            '<div class="metric-caption">'
            + html_safe(caption)
            + '</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


def render_evidence_card(result):
    kind = get_finding_type(result)

    styles = {
        "risk_signal": {
            "label": "Risk signal",
            "bg": "#FFF7E8",
            "fg": "#92400E",
            "icon": "⚠️",
        },
        "contradiction": {
            "label": "Contradiction",
            "bg": "#FEECEC",
            "fg": "#B91C1C",
            "icon": "❌",
        },
        "supporting_evidence": {
            "label": "Supporting check",
            "bg": "#E8F6F2",
            "fg": "#0F766E",
            "icon": "✅",
        },
        "unknown": {
            "label": "Unverified",
            "bg": "#EFF3F7",
            "fg": "#475569",
            "icon": "🔎",
        },
    }

    style = styles.get(
        kind,
        styles["unknown"],
    )

    check_name = result.check_name.replace(
        "_", " "
    ).title()

    claim_type = (
        result.claim.claim_type
        if result.claim
        else "Not available"
    )

    # HTML is kept on one physical line to prevent
    # Markdown from displaying tags as code.
    card_html = (
        '<div class="evidence-card">'
        '<div class="evidence-heading">'
        + style["icon"] + " " + html_safe(check_name)
        + '</div>'
        '<span class="evidence-badge" style="background:'
        + style["bg"]
        + ';color:'
        + style["fg"]
        + '">'
        + style["label"]
        + '</span>'
        '<div class="evidence-body"><strong>Finding:</strong> '
        + html_safe(result.finding)
        + '</div>'
        '<div class="evidence-meta">'
        '<strong>Verdict:</strong> '
        + html_safe(result.verdict.value)
        + '<br><strong>Evidence source:</strong> '
        + html_safe(result.source)
        + '<br><strong>Claim type:</strong> '
        + html_safe(claim_type)
        + '<br><strong>Confidence / limitations:</strong> '
        + html_safe(result.confidence_note)
        + '</div>'
        '</div>'
    )

    st.markdown(
        card_html,
        unsafe_allow_html=True,
    )


# ==================================================
# SESSION STATE
# ==================================================

if "verification_report" not in st.session_state:
    st.session_state.verification_report = None

if "pdf_report_bytes" not in st.session_state:
    st.session_state.pdf_report_bytes = None


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:
    st.title("🛡️ Trust Console")
    st.caption("Offer Evidence Verifier")

    st.divider()

    st.markdown("### Workspace")

    st.write("📄 Offer analysis")
    st.write("🔎 Evidence checks")
    st.write("🛡️ Risk signals")
    st.write("📊 Evidence summary")
    st.write("📥 Report export")

    st.divider()

    st.markdown(
        (
            '<div class="sidebar-card">'
            '<div class="sidebar-card-title">'
            'Evidence-first verification'
            '</div>'
            '<div class="sidebar-card-body">'
            'A risk signal does not prove fraud. '
            'A supporting check does not certify authenticity.'
            '</div></div>'
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            '<div class="sidebar-card">'
            '<div class="sidebar-card-title">'
            'Privacy-aware workflow'
            '</div>'
            '<div class="sidebar-card-body">'
            'Common sensitive-number patterns are masked. '
            'Other personal information may remain.'
            '</div></div>'
        ),
        unsafe_allow_html=True,
    )

    if st.button(
        "Clear previous report",
        use_container_width=True,
    ):
        st.session_state.verification_report = None
        st.session_state.pdf_report_bytes = None
        st.rerun()


# ==================================================
# HEADER
# ==================================================

st.markdown(
    (
        '<div class="topbar">'
        '<div>'
        '<div class="brand-title">'
        '🛡️ Offer Evidence Verifier'
        '</div>'
        '<div class="brand-subtitle">'
        'Trust Intelligence Workspace'
        '</div>'
        '</div>'
        '<div class="topbar-badge">'
        'Evidence-first analysis'
        '</div>'
        '</div>'
    ),
    unsafe_allow_html=True,
)


# ==================================================
# HERO
# ==================================================

st.markdown(
    (
        '<div class="hero">'
        '<div class="hero-eyebrow">'
        'RECRUITMENT EVIDENCE INTELLIGENCE'
        '</div>'
        '<div class="hero-title">'
        'Know what you can verify.'
        '</div>'
        '<div class="hero-description">'
        'Analyze recruitment claims, identify caution '
        'signals and review structured evidence. '
        'Understand what is supported, what conflicts, '
        'and what still needs independent verification.'
        '</div>'
        '</div>'
    ),
    unsafe_allow_html=True,
)


# ==================================================
# WORKFLOW
# ==================================================

workflow_steps = [
    "01 · Submit offer",
    "02 · Configure checks",
    "03 · Analyze evidence",
    "04 · Review findings",
    "05 · Export report",
]

workflow_html = '<div class="workflow">'

for index, step in enumerate(workflow_steps):
    active_class = (
        "workflow-step active"
        if index == 0
        else "workflow-step"
    )

    workflow_html += (
        '<div class="'
        + active_class
        + '">'
        + html_safe(step)
        + '</div>'
    )

workflow_html += '</div>'

st.markdown(
    workflow_html,
    unsafe_allow_html=True,
)


# ==================================================
# OFFER INPUT
# ==================================================

section(
    "01 / Input",
    "Submit an offer",
)

input_mode = st.radio(
    "Input method",
    ["Paste Text", "Upload PDF"],
    horizontal=True,
)

offer_text = ""

if input_mode == "Paste Text":
    offer_text = st.text_area(
        "Offer content",
        height=230,
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
            "Text-based PDFs only. "
            "Scanned PDFs are not supported."
        ),
    )

    if uploaded_file is not None:
        try:
            offer_text = extract_pdf_text(
                uploaded_file.getvalue()
            )

            st.success(
                "PDF text extracted successfully."
            )

            with st.expander(
                "Preview extracted text"
            ):
                st.text(
                    mask_sensitive_data(offer_text)[:5000]
                )

        except Exception as exc:
            st.error(
                f"Could not process PDF: {exc}"
            )


# ==================================================
# VERIFICATION SETTINGS
# ==================================================

section(
    "02 / Configuration",
    "Verification settings",
)

left, right = st.columns(2)

with left:
    official_domain = st.text_input(
        "Independently confirmed employer domain",
        placeholder="example.com",
        help=(
            "Optional. Confirm the official domain "
            "outside the submitted offer."
        ),
    )

with right:
    enable_domain_intelligence = st.checkbox(
        "Enable RDAP and DNS intelligence",
        value=False,
        help=(
            "Optional network checks. "
            "Domain age does not prove authenticity."
        ),
    )


# ==================================================
# ANALYSIS
# ==================================================

section(
    "03 / Analysis",
    "Run evidence verification",
)

st.caption(
    "The system uses rule-based checks and optional "
    "domain intelligence. It does not make a final "
    "fraud determination."
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
            "Please provide offer text or a readable PDF."
        )

    else:
        with st.spinner(
            "Extracting claims and evaluating evidence..."
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


# ==================================================
# RESULTS
# ==================================================

report = st.session_state.verification_report

if report is not None:
    st.divider()

    section(
        "04 / Results",
        "Evidence overview",
    )

    st.success(
        "Analysis completed. Review the evidence below."
    )

    st.caption(
        "Report ID: "
        + mask_sensitive_data(str(report.report_id))
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

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric(
            "Risk signals",
            len(groups["risk_signal"]),
            "Caution indicators",
            "#B45309",
        )

    with col2:
        render_metric(
            "Contradictions",
            len(groups["contradiction"]),
            "Conflicting evidence",
            "#B91C1C",
        )

    with col3:
        render_metric(
            "Supporting checks",
            len(groups["supporting_evidence"]),
            "Limited supporting evidence",
            "#0F766E",
        )

    with col4:
        render_metric(
            "Unverified",
            len(groups["unknown"]),
            "Requires further checks",
            "#475569",
        )

    st.caption(
        "These counts represent findings, not "
        "a fraud probability or authenticity score."
    )

    section(
        "05 / Findings",
        "Evidence breakdown",
    )

    categories = [
        (
            "⚠️ Risk signals",
            groups["risk_signal"],
        ),
        (
            "❌ Contradictions",
            groups["contradiction"],
        ),
        (
            "✅ Supporting checks",
            groups["supporting_evidence"],
        ),
        (
            "🔎 Unknown / unverified",
            groups["unknown"],
        ),
    ]

    for heading, findings in categories:
        st.subheader(heading)

        if not findings:
            st.caption(
                "No findings in this category."
            )
        else:
            for finding in findings:
                render_evidence_card(finding)

    section(
        "06 / Guidance",
        "Recommended next steps",
    )

    if report.safe_steps:
        for index, step in enumerate(
            report.safe_steps,
            start=1,
        ):
            st.write(
                f"**{index}.** "
                + mask_sensitive_data(str(step))
            )
    else:
        st.info(
            "No specific recommendations were generated."
        )

    st.info(
        mask_sensitive_data(str(report.disclaimer))
    )

    section(
        "07 / Export",
        "Download evidence report",
    )

    st.markdown(
        (
            '<div class="export-panel">'
            '<strong>Report ready</strong><br>'
            'Download the evidence summary, individual '
            'findings, sources, limitations and '
            'recommended actions.'
            '</div>'
        ),
        unsafe_allow_html=True,
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
        export_data = safe_report_dict(report)

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

    st.caption(
        "Review exported reports before sharing. "
        "Masking does not remove every form of "
        "personal information."
    )


# ==================================================
# FOOTER
# ==================================================

st.markdown(
    (
        '<div class="footer-note">'
        'Offer Evidence Verifier · Trust Intelligence Workspace'
        '<br>'
        'Evidence-based decision support. '
        'No automated finding is a final determination '
        'of authenticity or fraud.'
        '</div>'
    ),
    unsafe_allow_html=True,
)











