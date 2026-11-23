
import html
import json

import streamlit as st

from core.pipeline import verify_offer
from core.pdf_extractor import extract_pdf_text
from core.privacy import mask_sensitive_data
from core.schemas import Verdict


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Offer Evidence Verifier",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ==========================================
# PROFESSIONAL DARK THEME
# ==========================================

st.markdown(
    """
    <style>
    .stApp {
        background: #0b1220;
        color: #e2e8f0;
    }

    .block-container {
        max-width: 1150px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #f1f5f9 !important;
        letter-spacing: -0.5px;
    }

    [data-testid="stMetric"] {
        background: #142237;
        border: 1px solid #26394f;
        border-radius: 14px;
        padding: 18px;
    }

    [data-testid="stMetricValue"] {
        color: #f8fafc;
    }

    [data-testid="stMetricLabel"] {
        color: #94a3b8;
    }

    div.stButton > button[kind="primary"] {
        background: #0d9488;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        min-height: 48px;
    }

    div.stButton > button[kind="primary"]:hover {
        background: #0f766e;
        color: white;
    }

    [data-testid="stExpander"] {
        background: #142237;
        border: 1px solid #26394f;
        border-radius: 12px;
        margin-bottom: 12px;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    .section-label {
        color: #5dd6c0;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }

    .evidence-label {
        color: #94a3b8;
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 10px;
    }

    .evidence-value {
        color: #e2e8f0;
        font-size: 0.95rem;
        overflow-wrap: anywhere;
        white-space: pre-wrap;
    }

    .status-warning {
        color: #fbbf24;
        font-weight: 600;
    }

    .status-unknown {
        color: #94a3b8;
        font-weight: 600;
    }

    .status-verified {
        color: #5dd6c0;
        font-weight: 600;
    }

    .footer-note {
        color: #94a3b8;
        font-size: 0.8rem;
    }

    textarea {
        border-radius: 12px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def safe(value):
    """Escape values before HTML rendering."""
    return html.escape(str(value), quote=True)


def evidence_field(label, value):
    st.markdown(
        f'<div class="evidence-label">{safe(label)}</div>'
        f'<div class="evidence-value">{safe(value)}</div>',
        unsafe_allow_html=True,
    )


def privacy_safe_report(report):
    """
    Create a redacted copy of report data.

    Does not modify the original Pydantic report.
    """
    data = report.model_dump(mode="json")

    def redact(value):
        if isinstance(value, str):
            return mask_sensitive_data(value)

        if isinstance(value, list):
            return [redact(item) for item in value]

        if isinstance(value, dict):
            return {
                key: redact(item)
                for key, item in value.items()
            }

        return value

    return redact(data)


# ==========================================
# HEADER
# ==========================================

st.markdown(
    '<div class="section-label">'
    'EVIDENCE-FIRST VERIFICATION'
    '</div>',
    unsafe_allow_html=True,
)

st.title("🛡️ Offer Evidence Verifier")

st.markdown(
    '<div class="hero-subtitle">'
    'Verify claims. Review evidence. Decide safely.'
    '</div>',
    unsafe_allow_html=True,
)

st.info(
    "This tool highlights potential inconsistencies "
    "and unverified claims. It cannot guarantee whether "
    "an offer is genuine or fraudulent."
)


# ==========================================
# INPUT SECTION
# ==========================================

st.subheader("Analyze an internship or job offer")

input_method = st.radio(
    "Choose input method",
    ["Paste Text", "Upload PDF"],
    horizontal=True,
)

offer_text = ""
input_error = None

if input_method == "Paste Text":

    offer_text = st.text_area(
        "Paste your offer letter or recruitment message",
        height=240,
        placeholder=(
            "Company: ABC Technologies\n"
            "Role: Software Developer Intern\n"
            "Email: hr@gmail.com\n"
            "Registration fee: Rs 1499\n"
            "Pay within 24 hours."
        ),
    )

else:

    uploaded_file = st.file_uploader(
        "Upload your offer letter",
        type=["pdf"],
        help="Text-based PDFs only. Maximum size: 5 MB.",
    )

    if uploaded_file is not None:
        try:
            offer_text = extract_pdf_text(
                uploaded_file.getvalue()
            )

            st.success("PDF text extracted successfully.")

            with st.expander("Privacy-safe text preview"):
                preview = mask_sensitive_data(offer_text)
                st.text(preview[:3000])

        except ValueError as exc:
            input_error = str(exc)
            st.error(input_error)


# ==========================================
# ANALYZE BUTTON
# ==========================================

analyze = st.button(
    "🔍 Analyze Offer",
    type="primary",
    use_container_width=True,
)


# ==========================================
# VERIFICATION REPORT
# ==========================================

if analyze:

    if input_error:
        st.error("Please upload a supported PDF.")

    elif not offer_text.strip():
        st.warning(
            "Please paste an offer or upload a PDF first."
        )

    elif len(offer_text) > 20000:
        st.warning(
            "Please limit the offer text to 20,000 characters."
        )

    else:

        # Redact identifiers before analysis.
        # Email addresses remain available for domain checks.
        protected_text = mask_sensitive_data(offer_text)

        with st.spinner("Analyzing offer evidence..."):
            report = verify_offer(protected_text)

        warnings = [
            item for item in report.checks
            if item.verdict == Verdict.INCONSISTENT
        ]

        unknown = [
            item for item in report.checks
            if item.verdict == Verdict.COULD_NOT_VERIFY
        ]

        verified = [
            item for item in report.checks
            if item.verdict == Verdict.VERIFIED
        ]

        st.divider()

        st.markdown(
            '<div class="section-label">'
            'ANALYSIS RESULTS'
            '</div>',
            unsafe_allow_html=True,
        )

        st.subheader("Verification summary")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Claims extracted", len(report.claims))
        c2.metric("Checks performed", len(report.checks))
        c3.metric("Warnings", len(warnings))
        c4.metric("Couldn't verify", len(unknown))

        if warnings:
            st.warning(
                f"{len(warnings)} check(s) identified "
                "potential inconsistencies or warning signals. "
                "Review the evidence below."
            )
        else:
            st.info(
                "No configured warning signals were detected. "
                "This does not authenticate the offer."
            )

        st.subheader("Evidence findings")

        for index, result in enumerate(
            report.checks, start=1
        ):

            if result.verdict == Verdict.INCONSISTENT:
                icon = "⚠️"
                status_class = "status-warning"

            elif result.verdict == Verdict.VERIFIED:
                icon = "✅"
                status_class = "status-verified"

            else:
                icon = "❔"
                status_class = "status-unknown"

            check_title = (
                result.check_name
                .replace("_", " ")
                .title()
            )

            with st.expander(
                f"{icon} {index}. {check_title}",
                expanded=True,
            ):

                st.markdown(
                    f'<span class="{status_class}">'
                    f'{safe(result.verdict.value)}'
                    '</span>',
                    unsafe_allow_html=True,
                )

                evidence_field(
                    "Claim examined",
                    mask_sensitive_data(result.claim.value),
                )

                evidence_field(
                    "Finding",
                    mask_sensitive_data(result.finding),
                )

                evidence_field(
                    "Evidence source",
                    mask_sensitive_data(
                        result.source or "Not available"
                    ),
                )

                evidence_field(
                    "Confidence and limitations",
                    mask_sensitive_data(
                        result.confidence_note
                    ),
                )

        # ==========================================
        # SAFETY RECOMMENDATIONS
        # ==========================================

        st.subheader("Recommended next steps")

        for step in report.safe_steps:
            st.write("•", mask_sensitive_data(step))

        st.caption(report.disclaimer)

        # ==========================================
        # DOWNLOAD REDACTED REPORT
        # ==========================================

        safe_report = privacy_safe_report(report)

        st.download_button(
            label="⬇️ Download Evidence Report (JSON)",
            data=json.dumps(
                safe_report,
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

st.divider()

st.markdown(
    '<div class="footer-note">'
    'Privacy: Common personal identifiers are masked '
    'before analysis and in exported reports. '
    'This is an experimental protection layer, '
    'not a guarantee of complete anonymization. '
    'Avoid uploading sensitive real documents.'
    '</div>',
    unsafe_allow_html=True,
)



