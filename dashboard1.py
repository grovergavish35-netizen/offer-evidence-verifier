
import json
from html import escape
from textwrap import dedent

import streamlit as st

from core.pipeline import verify_offer
from core.pdf_extractor import extract_pdf_text
from core.pdf_report import generate_evidence_pdf
from core.privacy import mask_sensitive_data


# ============================================================
# 1. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Offer Evidence Verifier",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# 2. PREMIUM PROFESSIONAL CSS
# ============================================================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #F7F8FC;
    --white: #FFFFFF;
    --primary: #5046E5;
    --primary-dark: #4038C7;
    --primary-soft: #F0F1FF;
    --heading: #19243A;
    --body: #596781;
    --muted: #8491A7;
    --border: #E1E6EF;
    --green: #087F5B;
    --orange: #A86408;
    --red: #C0394B;
}

html,
body,
[class*="css"],
.stApp,
.stApp button,
.stApp input,
.stApp textarea {
    font-family: 'Inter', sans-serif !important;
}

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: var(--bg) !important;
    color: var(--heading) !important;
}

.block-container {
    max-width: 1440px !important;
    padding-top: 1.15rem !important;
    padding-bottom: 3rem !important;
}

[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

header[data-testid="stHeader"] {
    background: transparent !important;
}

.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4 {
    color: var(--heading) !important;
    letter-spacing: -0.035em;
}

.stApp p,
.stApp li,
.stApp label {
    color: var(--body);
}

[data-testid="stWidgetLabel"] p,
[data-testid="stRadio"] label p,
[data-testid="stCheckbox"] label p {
    color: #293751 !important;
    font-weight: 600 !important;
}

[data-testid="stCaptionContainer"] p {
    color: var(--muted) !important;
}

.stTextArea textarea,
.stTextInput input {
    background: #FFFFFF !important;
    color: #19243A !important;
    -webkit-text-fill-color: #19243A !important;
    border: 1px solid #D8DFEB !important;
    border-radius: 12px !important;
    font-size: 13px !important;
    line-height: 1.7 !important;
}

.stTextArea textarea::placeholder,
.stTextInput input::placeholder {
    color: #98A5B8 !important;
    -webkit-text-fill-color: #98A5B8 !important;
}

.stTextArea textarea:focus,
.stTextInput input:focus {
    border-color: #6258DD !important;
    box-shadow: 0 0 0 2px #6258DD22 !important;
}

div.stButton > button {
    min-height: 45px !important;
    border-radius: 11px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease;
}

div.stButton > button[kind="primary"] {
    background: #5046E5 !important;
    border: 1px solid #5046E5 !important;
    color: #FFFFFF !important;
    box-shadow: 0 5px 16px #5046E51A;
}

div.stButton > button[kind="primary"]:hover {
    background: #4038C7 !important;
    border-color: #4038C7 !important;
}

div.stButton > button[kind="primary"] p {
    color: #FFFFFF !important;
}

div.stButton > button[kind="secondary"] {
    background: #FFFFFF !important;
    border: 1px solid #DCE2ED !important;
    color: #293751 !important;
}

div.stButton > button[kind="secondary"] p {
    color: #293751 !important;
}

[data-testid="stFileUploader"] {
    background: #FAFBFF !important;
    border: 1px dashed #BCC7DD !important;
    border-radius: 15px !important;
    padding: 10px !important;
}

[data-testid="stFileUploader"] section {
    background: #FAFBFF !important;
}

[data-testid="stFileUploader"] button {
    background: #FFFFFF !important;
    color: #5046E5 !important;
    border: 1px solid #DCE2ED !important;
}

[data-testid="stExpander"] {
    background: #FFFFFF !important;
    border: 1px solid #E1E6EF !important;
    border-radius: 12px !important;
}

[data-testid="stExpander"] summary p {
    color: #293751 !important;
}

[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 1px solid #E1E6EF !important;
    border-radius: 15px !important;
    padding: 18px !important;
}

[data-testid="stMetricLabel"] p {
    color: #75839B !important;
    font-size: 12px !important;
}

[data-testid="stMetricValue"] {
    color: #19243A !important;
    font-weight: 800 !important;
}

[data-testid="stDownloadButton"] button {
    width: 100%;
    min-height: 49px !important;
    border-radius: 11px !important;
    background: #FFFFFF !important;
    border: 1px solid #DCE2ED !important;
}

[data-testid="stDownloadButton"] button p {
    color: #293751 !important;
}

hr {
    border-color: #E1E6EF !important;
}

/* TOP NAVIGATION */

.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 13px 0 22px;
    border-bottom: 1px solid #E1E6EF;
    margin-bottom: 28px;
}

.brand {
    display: flex;
    align-items: center;
    gap: 11px;
    font-size: 18px;
    font-weight: 750;
    letter-spacing: -0.7px;
    color: #19243A;
}

.brand-mark {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 39px;
    height: 39px;
    background: #5046E5;
    color: #FFFFFF;
    border-radius: 12px;
    font-size: 21px;
}

.nav-caption {
    color: #7B88A0;
    font-size: 12px;
    font-weight: 500;
}

/* PAGE TYPOGRAPHY */

.eyebrow {
    color: #5046E5;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.1em;
    margin-bottom: 11px;
}

.page-title {
    color: #19243A;
    font-size: clamp(30px, 3.2vw, 42px);
    font-weight: 750;
    letter-spacing: -1.5px;
    line-height: 1.2;
    margin-bottom: 14px;
}

.page-desc {
    color: #66758E;
    font-size: 14px;
    line-height: 1.85;
    max-width: 750px;
    margin-bottom: 24px;
}

.section-title {
    color: #19243A;
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.6px;
    margin: 27px 0 15px;
}

/* CONTENT PANELS */

.panel {
    background: #FFFFFF;
    border: 1px solid #E1E6EF;
    border-radius: 17px;
    padding: 23px;
    margin-bottom: 17px;
    box-shadow: 0 5px 20px #17243C06;
}

.panel-title {
    color: #19243A;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: -0.35px;
    margin-bottom: 9px;
}

.panel-text {
    color: #65738B;
    font-size: 13px;
    line-height: 1.85;
}

.panel-text p {
    margin: 8px 0;
    color: #65738B;
}

.panel-text strong {
    color: #293751;
}

/* SIDEBAR */

.side-label {
    font-size: 10px;
    color: #8B97AB;
    font-weight: 800;
    letter-spacing: 0.11em;
    margin: 12px 0;
}

.side-note {
    background: #F0F1FF;
    border: 1px solid #E0E1FF;
    border-radius: 14px;
    padding: 17px;
    font-size: 12px;
    line-height: 1.8;
    color: #5656A4;
    margin-top: 20px;
}

/* RESULTS PAGE */

.report-banner {
    background: linear-gradient(
        110deg,
        #FFFFFF,
        #F0F1FF
    );
    border: 1px solid #DFE1FB;
    border-radius: 22px;
    padding: 34px;
    margin: 17px 0 26px;
}

.report-banner h1 {
    font-size: clamp(30px, 4vw, 44px);
    font-weight: 750;
    letter-spacing: -1.5px;
    margin: 9px 0 12px;
    color: #19243A;
}

.report-banner p {
    color: #66758E;
    font-size: 14px;
    line-height: 1.8;
    max-width: 720px;
}

.status {
    display: inline-block;
    padding: 8px 14px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    margin-top: 13px;
}

.finding-card {
    background: #FFFFFF;
    border: 1px solid #E1E6EF;
    border-radius: 15px;
    padding: 22px;
    margin-bottom: 13px;
}

.finding-title {
    color: #19243A;
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 11px;
}

.finding-badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    margin-bottom: 12px;
}

.finding-body {
    color: #53627B;
    font-size: 13px;
    line-height: 1.85;
    overflow-wrap: anywhere;
}

.finding-meta {
    color: #8491A7;
    font-size: 12px;
    line-height: 1.9;
    margin-top: 12px;
    overflow-wrap: anywhere;
}

.guide-item {
    background: #FFFFFF;
    border: 1px solid #E1E6EF;
    border-radius: 14px;
    padding: 19px;
    margin-bottom: 13px;
}

.guide-item h3 {
    color: #19243A;
    font-size: 15px;
    font-weight: 700;
    margin: 0 0 8px;
}

.guide-item p {
    color: #68758D;
    font-size: 13px;
    line-height: 1.75;
    margin: 0;
}

/* FOOTER */

.footer {
    border-top: 1px solid #E1E6EF;
    margin-top: 48px;
    padding-top: 22px;
    text-align: center;
    color: #8B97AB;
    font-size: 12px;
    line-height: 1.8;
}

/* MOBILE */

@media(max-width:850px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    .brand {
        font-size: 15px;
    }

    .nav-caption {
        font-size: 10px;
    }

    .panel {
        padding: 17px;
    }

    .report-banner {
        padding: 23px;
    }

    .finding-card {
        padding: 17px;
    }

    .page-title {
        font-size: 30px;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 3. HTML AND DATA HELPERS
# ============================================================

def html(content):
    cleaned = dedent(content).strip()

    cleaned = " ".join(
        line.strip()
        for line in cleaned.splitlines()
        if line.strip()
    )

    st.markdown(
        cleaned,
        unsafe_allow_html=True,
    )


def safe(value):
    if value is None:
        return ""

    return escape(
        str(value),
        quote=True,
    )


def field(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(
        obj,
        name,
        default,
    )


def enum_text(value):
    return str(
        getattr(value, "value", value)
    )


def kind_of(check):
    value = enum_text(
        field(check, "finding_type", "unknown")
    )

    return (
        value.lower()
        .split(".")[-1]
        .replace(" ", "_")
        .replace("-", "_")
    )


def get_checks(report):
    """
    Your project's VerificationReport uses .checks.
    """
    for name in (
        "checks",
        "results",
        "check_results",
        "findings",
    ):
        value = field(report, name)

        if isinstance(value, (list, tuple)):
            return list(value)

    return []


def get_counts(checks):
    counts = {
        "risk_signal": 0,
        "contradiction": 0,
        "supporting_evidence": 0,
        "unknown": 0,
    }

    for check in checks:
        kind = kind_of(check)

        if kind not in counts:
            kind = "unknown"

        counts[kind] += 1

    return counts


def status_from_counts(counts):
    if counts["contradiction"] > 0:
        return (
            "Contradictions require review",
            "#FFF0F2",
            "#C0394B",
        )

    if counts["risk_signal"] > 0:
        return (
            "Warning signs identified",
            "#FFF5E5",
            "#A86408",
        )

    return (
        "Independent verification required",
        "#F0F1FF",
        "#5046E5",
    )


def report_json(report):
    if hasattr(report, "model_dump_json"):
        return report.model_dump_json(indent=2)

    if hasattr(report, "model_dump"):
        data = report.model_dump(mode="json")

    elif hasattr(report, "dict"):
        data = report.dict()

    else:
        data = report

    return json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
        default=str,
    )


# ============================================================
# 4. UI COMPONENTS
# ============================================================

def page_heading(eyebrow, title, description):
    html(
        f"""
        <div class="eyebrow">
            {safe(eyebrow)}
        </div>

        <div class="page-title">
            {safe(title)}
        </div>

        <div class="page-desc">
            {safe(description)}
        </div>
        """
    )


def guide(title, description):
    html(
        f"""
        <div class="guide-item">
            <h3>{safe(title)}</h3>
            <p>{safe(description)}</p>
        </div>
        """
    )


def finding_card(check):
    kind = kind_of(check)

    styles = {
        "risk_signal": (
            "Risk signal",
            "#FFF5E5",
            "#A86408",
            "⚠",
        ),
        "contradiction": (
            "Contradiction",
            "#FFF0F2",
            "#C0394B",
            "✕",
        ),
        "supporting_evidence": (
            "Supporting evidence",
            "#E9F8F0",
            "#087F5B",
            "✓",
        ),
        "unknown": (
            "Not verified",
            "#F0F1FF",
            "#5046E5",
            "◇",
        ),
    }

    label, bg, color, icon = styles.get(
        kind,
        styles["unknown"],
    )

    title = str(
        field(check, "check_name", "Evidence check")
    ).replace("_", " ").title()

    finding = field(
        check,
        "finding",
        "No finding available.",
    )

    source = field(
        check,
        "source",
        "Not available",
    )

    verdict = enum_text(
        field(check, "verdict", "Unknown")
    )

    confidence = field(
        check,
        "confidence_note",
        "",
    )

    claim = field(
        check,
        "claim",
    )

    claim_type = enum_text(
        field(
            claim,
            "claim_type",
            "Not available",
        )
    )

    html(
        f"""
        <div class="finding-card">
            <div class="finding-title">
                {safe(icon)}
                {safe(title)}
            </div>

            <span
                class="finding-badge"
                style="
                    background:{bg};
                    color:{color};
                "
            >
                {safe(label)}
            </span>

            <div class="finding-body">
                <strong>Finding</strong>
                <div>
                    {safe(finding)}
                </div>
            </div>

            <div class="finding-meta">
                <strong>Verdict:</strong>
                {safe(verdict)}
                <br>

                <strong>Source:</strong>
                {safe(source)}
                <br>

                <strong>Claim:</strong>
                {safe(claim_type)}
                <br>

                <strong>Limitations:</strong>
                {safe(confidence)}
            </div>
        </div>
        """
    )


# ============================================================
# 5. SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "overview"

if "report" not in st.session_state:
    st.session_state.report = None

if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None


def navigate(page):
    st.session_state.page = page
    st.rerun()


def reset():
    st.session_state.report = None
    st.session_state.pdf_bytes = None
    st.session_state.page = "verification"
    st.rerun()


# ============================================================
# 6. TOP NAVBAR
# ============================================================

html(
    """
    <div class="topbar">
        <div class="brand">
            <span class="brand-mark">✦</span>
            Offer Evidence Verifier
        </div>

        <div class="nav-caption">
            Trust through evidence
        </div>
    </div>
    """
)


# ============================================================
# 7. DEDICATED FULL-WIDTH RESULTS PAGE
# ============================================================

if st.session_state.page == "results":

    report = st.session_state.report

    if report is None:
        navigate("verification")

    top_left, top_right = st.columns([4, 1])

    with top_left:
        st.caption(
            "DASHBOARD / VERIFICATION / ANALYSIS RESULTS"
        )

    with top_right:
        if st.button(
            "← Back to Dashboard",
            use_container_width=True,
        ):
            navigate("overview")

    checks = get_checks(report)

    counts = get_counts(checks)

    status_label, status_bg, status_color = (
        status_from_counts(counts)
    )

    html(
        f"""
        <div class="report-banner">
            <div class="eyebrow">
                VERIFICATION REPORT
            </div>

            <h1>
                Your offer analysis is ready.
            </h1>

            <p>
                Explore evidence found in your
                offer letter. Review suspicious
                claims, contradictions and
                unresolved checks before making
                a decision.
            </p>

            <span
                class="status"
                style="
                    background:{status_bg};
                    color:{status_color};
                "
            >
                {safe(status_label)}
            </span>
        </div>
        """
    )

    html(
        '<div class="section-title">Evidence summary</div>'
    )

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric(
            "Risk signals",
            counts["risk_signal"],
        )

    with m2:
        st.metric(
            "Contradictions",
            counts["contradiction"],
        )

    with m3:
        st.metric(
            "Supporting evidence",
            counts["supporting_evidence"],
        )

    with m4:
        st.metric(
            "Unverified checks",
            counts["unknown"],
        )

    st.write("")

    detail_col, action_col = st.columns(
        [2.4, 1],
        gap="large",
    )

    with detail_col:

        html(
            '<div class="section-title">Detailed evidence</div>'
        )

        if not checks:
            st.info(
                "The verification engine returned "
                "no individual checks."
            )

        groups = [
            (
                "⚠ Risk signals",
                "risk_signal",
            ),
            (
                "✕ Contradictions",
                "contradiction",
            ),
            (
                "✓ Supporting evidence",
                "supporting_evidence",
            ),
            (
                "◇ Could not verify",
                "unknown",
            ),
        ]

        for heading, group_type in groups:

            items = []

            for check in checks:

                check_type = kind_of(check)

                if check_type not in {
                    "risk_signal",
                    "contradiction",
                    "supporting_evidence",
                }:
                    check_type = "unknown"

                if check_type == group_type:
                    items.append(check)

            if not items:
                continue

            st.markdown(
                f"### {heading}"
            )

            for item in items:
                finding_card(item)

    with action_col:

        html(
            '<div class="section-title">Recommended actions</div>'
        )

        guide(
            "01 · Verify the employer",
            (
                "Contact the company through "
                "independently confirmed official "
                "communication channels."
            ),
        )

        guide(
            "02 · Avoid unexpected fees",
            (
                "Do not pay registration or "
                "verification fees without "
                "independent confirmation."
            ),
        )

        guide(
            "03 · Protect personal data",
            (
                "Avoid sharing identity or "
                "banking details with an "
                "unverified recruiter."
            ),
        )

        guide(
            "04 · Verify the recruiter",
            (
                "Confirm the recruiter's "
                "identity through the "
                "employer's official HR team."
            ),
        )

        html(
            '<div class="section-title">Download report</div>'
        )

        pdf_data = (
            st.session_state.pdf_bytes
        )

        if pdf_data is not None:

            st.download_button(
                "↓ Download PDF",
                data=pdf_data,
                file_name="offer_evidence_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        else:

            st.caption(
                "PDF export unavailable "
                "for this analysis."
            )

        try:

            st.download_button(
                "↓ Download JSON",
                data=report_json(report),
                file_name="offer_evidence_report.json",
                mime="application/json",
                use_container_width=True,
            )

        except Exception as exc:

            st.warning(
                f"JSON export unavailable: {exc}"
            )

        st.write("")

        if st.button(
            "✦ Analyze Another Offer",
            type="primary",
            use_container_width=True,
        ):
            reset()

        st.caption(
            "Risk signals are not proof of fraud. "
            "Supporting evidence does not "
            "guarantee authenticity."
        )


# ============================================================
# 8. THREE-COLUMN DASHBOARD
# ============================================================

else:

    left, center, right = st.columns(
        [1.15, 3.2, 1.3],
        gap="medium",
    )

    # --------------------------------------------------------
    # LEFT NAVIGATION
    # --------------------------------------------------------

    with left:

        html(
            """
            <div class="panel">
                <div class="side-label">
                    NAVIGATION
                </div>

                <div class="panel-title">
                    Your dashboard
                </div>

                <div class="panel-text">
                    Access verification tools,
                    safety resources and
                    your latest report.
                </div>
            </div>
            """
        )

        menu = [
            (
                "overview",
                "▦ Overview",
            ),
            (
                "verification",
                "⌕ New Verification",
            ),
            (
                "risk",
                "⚠ Risk Indicators",
            ),
            (
                "guide",
                "☷ Safety Guide",
            ),
        ]

        for page_id, label in menu:

            active = (
                st.session_state.page
                == page_id
            )

            if st.button(
                ("● " if active else "") + label,
                key=f"menu_{page_id}",
                type=(
                    "primary"
                    if active
                    else "secondary"
                ),
                use_container_width=True,
            ):
                navigate(page_id)

        if st.session_state.report is not None:

            if st.button(
                "▤ Analysis Results",
                use_container_width=True,
            ):
                navigate("results")

        html(
            """
            <div class="side-note">
                <strong>
                    Privacy-aware verification
                </strong>
                <br>
                Common sensitive data patterns
                are masked before analysis.
                Review documents before uploading.
            </div>
            """
        )

    # --------------------------------------------------------
    # RIGHT INFORMATION PANEL
    # --------------------------------------------------------

    with right:

        html(
            """
            <div class="panel">
                <div class="panel-title">
                    ◇ What we check
                </div>

                <div class="panel-text">
                    ✓ Recruitment fee requests
                    <br>
                    ✓ Suspicious email domains
                    <br>
                    ✓ Urgency tactics
                    <br>
                    ✓ Unusual communication channels
                    <br>
                    ✓ Offer inconsistencies
                </div>
            </div>
            """
        )

        html(
            """
            <div class="panel">
                <div class="panel-title">
                    💡 Security tip
                </div>

                <div class="panel-text">
                    Never pay a recruitment fee
                    based only on an offer letter.
                    Verify the request using
                    independently confirmed
                    employer contact details.
                </div>
            </div>
            """
        )

        if st.session_state.report is not None:

            latest = get_checks(
                st.session_state.report
            )

            latest_counts = get_counts(
                latest
            )

            html(
                f"""
                <div class="panel">
                    <div class="panel-title">
                        ▤ Latest analysis
                    </div>

                    <div class="panel-text">
                        <strong>
                            {len(latest)}
                        </strong>
                        evidence checks
                        <br>

                        <strong>
                            {latest_counts["risk_signal"]}
                        </strong>
                        risk signals
                        <br>

                        <strong>
                            {latest_counts["contradiction"]}
                        </strong>
                        contradictions
                    </div>
                </div>
                """
            )

            if st.button(
                "View full report →",
                use_container_width=True,
                key="right_report",
            ):
                navigate("results")

        else:

            html(
                """
                <div class="panel">
                    <div class="panel-title">
                        ▤ Your report
                    </div>

                    <div class="panel-text">
                        Analyze an offer to see
                        evidence findings and
                        downloadable reports.
                    </div>
                </div>
                """
            )

        html(
            """
            <div class="panel">
                <div class="panel-title">
                    Important reminder
                </div>

                <div class="panel-text">
                    No automated check can
                    independently guarantee
                    that a job offer is genuine.
                </div>
            </div>
            """
        )

    # --------------------------------------------------------
    # CENTER CONTENT
    # --------------------------------------------------------

    with center:

        page = st.session_state.page

        # ====================================================
        # OVERVIEW PAGE
        # ====================================================

        if page == "overview":

            page_heading(
                "RECRUITMENT TRUST INTELLIGENCE",
                "Verify opportunities with confidence.",
                (
                    "Analyze job and internship offers, "
                    "identify suspicious claims and review "
                    "clear, evidence-based findings before "
                    "making your next career decision."
                ),
            )

            html(
                """
                <div class="panel">
                    <div class="eyebrow">
                        OFFER VERIFICATION
                    </div>

                    <div class="panel-title">
                        Have an offer letter?
                        Let's verify it.
                    </div>

                    <div class="panel-text">
                        Upload a PDF or paste your
                        offer letter to check for
                        recruitment fees, suspicious
                        communication, urgency tactics
                        and inconsistencies.
                    </div>
                </div>
                """
            )

            if st.button(
                "✦ Start New Verification",
                type="primary",
                use_container_width=True,
                key="overview_start",
            ):
                navigate("verification")

            html(
                """
                <div class="section-title">
                    How it works
                </div>
                """
            )

            html(
                """
                <div class="panel">
                    <div class="panel-text">

                        <strong>
                            01 — Submit your offer
                        </strong>

                        <p>
                            Upload a PDF or paste
                            the text of your job
                            or internship offer.
                        </p>

                        <hr style="
                            border:0;
                            border-top:1px solid #E1E6EF;
                        ">

                        <strong>
                            02 — Analyze evidence
                        </strong>

                        <p>
                            The verification engine
                            checks available claims
                            and warning signs.
                        </p>

                        <hr style="
                            border:0;
                            border-top:1px solid #E1E6EF;
                        ">

                        <strong>
                            03 — Review your report
                        </strong>

                        <p>
                            Examine findings,
                            limitations and
                            recommended verification
                            steps.
                        </p>

                    </div>
                </div>
                """
            )

            if st.session_state.report is not None:

                if st.button(
                    "View Latest Analysis →",
                    use_container_width=True,
                    key="overview_latest",
                ):
                    navigate("results")

        # ====================================================
        # NEW VERIFICATION PAGE
        # ====================================================

        elif page == "verification":

            page_heading(
                "NEW VERIFICATION",
                "Verify a job or internship offer.",
                (
                    "Upload a text-based PDF or paste "
                    "the complete offer letter. "
                    "Your analysis will open on "
                    "a dedicated results page."
                ),
            )

            html(
                """
                <div class="panel">
                    <div class="panel-title">
                        Start an investigation
                    </div>

                    <div class="panel-text">
                        Choose your input method.
                        The report will open
                        automatically after analysis.
                    </div>
                </div>
                """
            )

            mode = st.radio(
                "Input method",
                [
                    "Upload PDF",
                    "Paste Text",
                ],
                horizontal=True,
            )

            offer_text = ""

            if mode == "Upload PDF":

                uploaded = st.file_uploader(
                    "Upload offer letter",
                    type=["pdf"],
                    help=(
                        "Text-based PDFs supported. "
                        "Scanned PDFs need OCR."
                    ),
                )

                if uploaded is not None:

                    try:

                        offer_text = extract_pdf_text(
                            uploaded.getvalue()
                        )

                        if offer_text.strip():

                            st.success(
                                "PDF text extracted successfully."
                            )

                            with st.expander(
                                "Preview extracted text"
                            ):

                                st.text(
                                    mask_sensitive_data(
                                        offer_text
                                    )[:5000]
                                )

                        else:

                            st.warning(
                                "No readable text found. "
                                "Try Paste Text instead."
                            )

                    except Exception as exc:

                        st.error(
                            f"PDF extraction failed: {exc}"
                        )

            else:

                offer_text = st.text_area(
                    "Offer letter content",
                    height=300,
                    placeholder=(
                        "Paste your complete offer letter here...\n\n"
                        "Company: Example Technologies\n"
                        "Position: Software Development Intern\n"
                        "Recruiter: hr@example.com"
                    ),
                    key="offer_input",
                )

            with st.expander(
                "Advanced verification options"
            ):

                official_domain = st.text_input(
                    "Independently confirmed employer domain",
                    placeholder="example.com",
                )

                domain_intelligence = st.checkbox(
                    "Enable DNS and RDAP intelligence",
                    value=False,
                )

            st.write("")

            if st.button(
                "✦ Analyze Offer Letter",
                type="primary",
                use_container_width=True,
            ):

                if not offer_text.strip():

                    st.warning(
                        "Please provide readable offer text."
                    )

                else:

                    with st.spinner(
                        "Analyzing offer evidence..."
                    ):

                        try:

                            masked = mask_sensitive_data(
                                offer_text
                            )

                            report = verify_offer(
                                masked,
                                official_domain=(
                                    official_domain.strip()
                                    or None
                                ),
                                enable_domain_intelligence=(
                                    domain_intelligence
                                ),
                            )

                            st.session_state.report = report

                            try:

                                st.session_state.pdf_bytes = (
                                    generate_evidence_pdf(
                                        report
                                    )
                                )

                            except Exception:

                                st.session_state.pdf_bytes = (
                                    None
                                )

                            navigate("results")

                        except Exception as exc:

                            st.error(
                                f"Analysis failed: {exc}"
                            )

            st.caption(
                "The tool identifies warning signs "
                "and evidence. It does not certify "
                "authenticity."
            )

        # ====================================================
        # RISK INDICATORS PAGE
        # ====================================================

        elif page == "risk":

            page_heading(
                "RECRUITMENT RISK AWARENESS",
                "Recognize warning signs.",
                (
                    "Learn about common suspicious "
                    "recruitment patterns."
                ),
            )

            risks = [
                (
                    "Upfront recruitment fees",
                    (
                        "Unexpected registration, "
                        "verification or training "
                        "payments requested to "
                        "secure employment."
                    ),
                ),
                (
                    "Artificial urgency",
                    (
                        "Pressure to make a payment "
                        "or submit documents within "
                        "an unusually short deadline."
                    ),
                ),
                (
                    "Unverified email domains",
                    (
                        "Recruiter addresses that "
                        "cannot be connected to "
                        "independently confirmed "
                        "employer information."
                    ),
                ),
                (
                    "WhatsApp-only recruitment",
                    (
                        "Recruitment managed entirely "
                        "through informal messaging "
                        "without independent employer "
                        "confirmation."
                    ),
                ),
                (
                    "Guaranteed selection claims",
                    (
                        "Unusual promises of selection, "
                        "salary or placement without "
                        "a credible hiring process."
                    ),
                ),
                (
                    "Sensitive information requests",
                    (
                        "Requests for identity or "
                        "banking details before "
                        "verifying the recipient."
                    ),
                ),
            ]

            for title, description in risks:
                guide(title, description)

            st.info(
                "One warning sign alone does not "
                "establish fraud. Independently "
                "verify the offer."
            )

            if st.button(
                "Verify an Offer →",
                type="primary",
                use_container_width=True,
            ):
                navigate("verification")

        # ====================================================
        # SAFETY GUIDE PAGE
        # ====================================================

        elif page == "guide":

            page_heading(
                "CAREER SAFETY GUIDE",
                "Verify before you trust.",
                (
                    "Practical steps for checking "
                    "unfamiliar job and internship "
                    "opportunities."
                ),
            )

            steps = [
                (
                    "01 · Find the official employer website",
                    (
                        "Locate the company independently "
                        "rather than following only "
                        "the links in the offer."
                    ),
                ),
                (
                    "02 · Contact the official HR team",
                    (
                        "Use published official contact "
                        "details to confirm whether "
                        "the offer was issued."
                    ),
                ),
                (
                    "03 · Verify the recruiter",
                    (
                        "Confirm the recruiter's identity "
                        "and role through the employer."
                    ),
                ),
                (
                    "04 · Avoid unexpected payments",
                    (
                        "Treat registration and verification "
                        "fee requests as warning signs."
                    ),
                ),
                (
                    "05 · Protect your documents",
                    (
                        "Do not share identity or financial "
                        "details until the recipient "
                        "is verified."
                    ),
                ),
                (
                    "06 · Preserve suspicious evidence",
                    (
                        "Keep relevant messages and offer "
                        "documents if you suspect "
                        "recruitment fraud."
                    ),
                ),
            ]

            for title, description in steps:
                guide(title, description)

            if st.button(
                "Start Verification →",
                type="primary",
                use_container_width=True,
            ):
                navigate("verification")


# ============================================================
# 9. FOOTER
# ============================================================

html(
    """
    <div class="footer">
        © 2026 Offer Evidence Verifier
        <br>
        Evidence-first recruitment verification
        · Transparent findings · Safer decisions
    </div>
    """
)
