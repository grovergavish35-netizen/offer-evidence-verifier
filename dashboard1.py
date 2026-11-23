
import json

import streamlit as st

from core.pipeline import verify_offer
from core.pdf_extractor import extract_pdf_text
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
    """Support new and older check result objects."""

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

    icon = icons.get(kind, "🔎")

    title = (
        f"{icon} {result.check_name.replace('_', ' ').title()}"
    )

    with st.expander(title):
        st.write("**Finding:**", result.finding)
        st.write("**Finding type:**", kind.replace("_", " ").title())
        st.write("**Check verdict:**", result.verdict.value)
        st.write("**Confidence note:**", result.confidence_note)
        st.write("**Source:**", result.source or "Not available")

        if result.claim:
            st.write(
                "**Claim type:**",
                result.claim.claim_type,
            )

def safe_report_dict(report):
    """Mask common sensitive patterns in exported text."""

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

st.title("🛡️ Offer Evidence Verifier")

st.markdown(
    '<div class="subtitle">'
    "Evidence-first internship and job offer screening"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="notice">'
    "This tool checks selected claims and warning patterns. "
    "It cannot certify that an offer is genuine or fraudulent."
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

            st.success("PDF text extracted successfully.")

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
    "Independently confirmed official company domain (optional)",
    placeholder="example.com",
    help=(
        "Enter a domain verified independently, "
        "not one copied only from the offer."
    ),
)

enable_domain_intelligence = st.checkbox(
    "Enable RDAP and DNS domain intelligence",
    value=False,
    help=(
        "Optional network lookups may take several seconds. "
        "They provide domain evidence, not employer verification."
    ),
)

if st.button(
    "Analyze Offer",
    type="primary",
    use_container_width=True,
):
    if not offer_text.strip():
        st.warning(
            "Please paste offer text or upload a readable PDF."
        )

    else:
        with st.spinner("Analyzing available evidence..."):
            masked_text = mask_sensitive_data(
                offer_text
            )

            try:
                report = verify_offer(
                    masked_text,
                    official_domain=(
                        official_domain.strip() or None
                    ),
                    enable_domain_intelligence=(
                        enable_domain_intelligence
                    ),
                )

            except Exception as exc:
                st.error(
                    f"Analysis failed: {exc}"
                )
                st.stop()

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
            "These are counts of check findings, "
            "not a fraud probability or authenticity score."
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

        st.subheader("Export evidence report")

        export_data = safe_report_dict(report)

        st.download_button(
            label="Download JSON Report",
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
            "Common phone, PAN, Aadhaar-like and labeled "
            "bank-account patterns are masked. Names, emails "
            "and other personal information may remain. "
            "Review the JSON before sharing."
        )





