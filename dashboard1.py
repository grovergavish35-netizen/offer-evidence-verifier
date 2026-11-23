
import json

import streamlit as st

from core.pipeline import verify_offer
from core.pdf_extractor import extract_pdf_text
from core.pdf_report import generate_evidence_pdf
from core.privacy import mask_sensitive_data
from core.schemas import FindingType


st.set_page_config(
    page_title="Offer Evidence Verifier",
    page_icon="🛡️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background: #0b1220;
        color: #e5e7eb;
    }

    h1, h2, h3 {
        color: #f8fafc;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
    }

    div[data-testid="stMetric"] {
        background: #172033;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
    }

    .subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }

    .notice {
        border: 1px solid #334155;
        background: #111c2d;
        padding: 14px;
        border-radius: 10px;
        color: #cbd5e1;
        margin-bottom: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def result_type(result):
    kind = getattr(
        result,
        "finding_type",
        FindingType.UNKNOWN,
    )

    if isinstance(kind, FindingType):
        return kind.value

    return str(kind)


def show_result(result):
    kind = result_type(result)

    icons = {
        "risk_signal": "⚠️",
        "contradiction": "❌",
        "supporting_evidence": "✅",
        "unknown": "🔎",
    }

    title = (
        f"{icons.get(kind, '🔎')} "
        f"{result.check_name.replace('_', ' ').title()}"
    )

    with st.expander(title):
        st.write("**Finding:**", result.finding)
        st.write(
            "**Finding type:**",
            kind.replace("_", " ").title(),
        )
        st.write(
            "**Check verdict:**",
            result.verdict.value,
        )
        st.write(
            "**Confidence note:**",
            result.confidence_note,
        )
        st.write(
            "**Evidence source:**",
            result.source or "Not available",
        )

        if result.claim:
            st.write(
                "**Claim type:**",
                result.claim.claim_type,
            )


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


if "verification_report" not in st.session_state:
    st.session_state.verification_report = None

if "pdf_report_bytes" not in st.session_state:
    st.session_state.pdf_report_bytes = None


st.title("🛡️ Offer Evidence Verifier")

st.markdown(
    '<div class="subtitle">'
    "Evidence-first internship and job offer screening"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="notice">'
    "This tool evaluates selected claims and warning "
    "patterns. It cannot certify that an offer is "
    "genuine or fraudulent."
    "</div>",
    unsafe_allow_html=True,
)


mode = st.radio(
    "Choose input method",
    ["Paste Text", "Upload PDF"],
    horizontal=True,
)

offer_text = ""

if mode == "Paste Text":
    offer_text = st.text_area(
        "Paste your internship or job offer",
        height=260,
        placeholder=(
            "Company: Example Technologies\n"
            "Role: Software Intern\n"
            "Recruiter: hr@example.com\n"
            "No registration fee required."
        ),
    )

else:
    uploaded_file = st.file_uploader(
        "Upload a text-based PDF",
        type=["pdf"],
    )

    if uploaded_file is not None:
        try:
            offer_text = extract_pdf_text(
                uploaded_file.getvalue()
            )

            st.success(
                "PDF text extracted successfully."
            )

            with st.expander("Preview extracted text"):
                st.text(
                    mask_sensitive_data(offer_text)[:5000]
                )

        except Exception as exc:
            st.error(
                f"PDF could not be processed: {exc}"
            )


st.subheader("Verification settings")

official_domain = st.text_input(
    "Independently confirmed official company domain",
    placeholder="example.com",
    help=(
        "Optional. Verify this domain outside the "
        "submitted offer before entering it."
    ),
)

enable_domain_intelligence = st.checkbox(
    "Enable RDAP and DNS domain intelligence",
    value=False,
    help=(
        "Optional network lookups. Domain age and "
        "MX records do not authenticate a recruiter."
    ),
)


if st.button(
    "Analyze Offer",
    type="primary",
    use_container_width=True,
):
    # Clear stale results before a new analysis.
    st.session_state.verification_report = None
    st.session_state.pdf_report_bytes = None

    if not offer_text.strip():
        st.warning(
            "Please paste offer text or upload a readable PDF."
        )

    else:
        with st.spinner(
            "Analyzing evidence and preparing report..."
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


report = st.session_state.verification_report

if report is not None:
    st.success("Evidence analysis completed.")

    groups = {
        "risk_signal": [],
        "contradiction": [],
        "supporting_evidence": [],
        "unknown": [],
    }

    for result in report.checks:
        kind = result_type(result)
        groups.setdefault(kind, []).append(result)

    st.subheader("Evidence summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Risk signals",
        len(groups["risk_signal"]),
    )

    col2.metric(
        "Contradictions",
        len(groups["contradiction"]),
    )

    col3.metric(
        "Supporting checks",
        len(groups["supporting_evidence"]),
    )

    col4.metric(
        "Unverified checks",
        len(groups["unknown"]),
    )

    st.caption(
        "These are counts of findings, not an "
        "authenticity score or fraud probability."
    )

    sections = [
        ("⚠️ Risk signals", groups["risk_signal"]),
        ("❌ Contradictions", groups["contradiction"]),
        (
            "✅ Supporting evidence",
            groups["supporting_evidence"],
        ),
        (
            "🔎 Unverified or unknown",
            groups["unknown"],
        ),
    ]

    for heading, items in sections:
        st.subheader(heading)

        if not items:
            st.info(
                "No findings in this category."
            )
        else:
            for result in items:
                show_result(result)

    st.subheader("Recommended next steps")

    for index, step in enumerate(
        report.safe_steps,
        start=1,
    ):
        st.write(f"{index}. {step}")

    st.info(report.disclaimer)

    st.subheader("Download Evidence Report")

    st.write(
        "Download the complete analysis as a "
        "professional PDF or structured JSON report."
    )

    pdf_col, json_col = st.columns(2)

    with pdf_col:
        st.download_button(
            label="📄 Download PDF Report",
            data=st.session_state.pdf_report_bytes,
            file_name="offer_evidence_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    with json_col:
        export_data = safe_report_dict(report)

        st.download_button(
            label="📋 Download JSON Report",
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
        "Common sensitive-number patterns are masked, "
        "but names, email addresses and other personal "
        "information may remain. Review before sharing."
    )






