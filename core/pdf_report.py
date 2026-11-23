
from io import BytesIO
from collections import Counter
from html import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)

from core.privacy import mask_sensitive_data
from core.schemas import VerificationReport


NAVY = colors.HexColor("#14233B")
BLUE = colors.HexColor("#2563EB")
GRAY = colors.HexColor("#64748B")
LIGHT = colors.HexColor("#F1F5F9")
BORDER = colors.HexColor("#CBD5E1")
RED = colors.HexColor("#B91C1C")
AMBER = colors.HexColor("#92400E")
GREEN = colors.HexColor("#166534")


def safe_text(value):
    """
    Mask recognized sensitive-number patterns and
    escape markup before inserting into the PDF.
    """
    if value is None:
        return "Not available"

    text = mask_sensitive_data(str(value))
    return escape(text).replace("\n", "<br/>")


def get_finding_type(check):
    kind = getattr(check, "finding_type", "unknown")
    return getattr(kind, "value", str(kind))


def get_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitleCustom",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=24,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportSubtitleCustom",
            parent=styles["Normal"],
            fontSize=9,
            leading=14,
            textColor=GRAY,
            alignment=TA_CENTER,
            spaceAfter=15,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportSectionCustom",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=NAVY,
            spaceBefore=15,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportBodyCustom",
            parent=styles["Normal"],
            fontSize=9,
            leading=14,
            textColor=NAVY,
            spaceAfter=6,
            wordWrap="CJK",
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportSmallCustom",
            parent=styles["Normal"],
            fontSize=8,
            leading=12,
            textColor=GRAY,
            spaceAfter=5,
            wordWrap="CJK",
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportFindingCustom",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=NAVY,
            spaceAfter=7,
        )
    )

    return styles


def add_page_number(canvas, doc):
    canvas.saveState()

    width, _ = A4

    canvas.setStrokeColor(BORDER)
    canvas.line(
        18 * mm,
        16 * mm,
        width - 18 * mm,
        16 * mm,
    )

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRAY)

    canvas.drawString(
        18 * mm,
        11 * mm,
        "Offer Evidence Verifier | Decision Support",
    )

    canvas.drawRightString(
        width - 18 * mm,
        11 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


def make_summary_table(report, styles):
    counts = Counter(
        get_finding_type(check)
        for check in report.checks
    )

    summary = [
        ("Risk signals", counts["risk_signal"]),
        ("Contradictions", counts["contradiction"]),
        (
            "Supporting checks",
            counts["supporting_evidence"],
        ),
        ("Unknown / unverified", counts["unknown"]),
    ]

    cells = [
        [
            Paragraph(
                safe_text(label),
                styles["ReportBodyCustom"],
            ),
            Paragraph(
                str(count),
                styles["ReportBodyCustom"],
            ),
        ]
        for label, count in summary
    ]

    table = Table(
        cells,
        colWidths=[125 * mm, 45 * mm],
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    return table


def finding_color(kind):
    return {
        "risk_signal": AMBER,
        "contradiction": RED,
        "supporting_evidence": GREEN,
        "unknown": GRAY,
    }.get(kind, GRAY)


def make_finding(check, index, styles):
    kind = get_finding_type(check)
    label = kind.replace("_", " ").title()

    content = []

    heading = (
        f"{index}. "
        f"{safe_text(check.check_name.replace('_', ' ').title())}"
    )

    content.append(
        Paragraph(
            heading,
            styles["ReportFindingCustom"],
        )
    )

    content.append(
        Paragraph(
            f"<b>Classification:</b> {safe_text(label)}",
            styles["ReportBodyCustom"],
        )
    )

    content.append(
        Paragraph(
            f"<b>Verdict:</b> {safe_text(check.verdict.value)}",
            styles["ReportBodyCustom"],
        )
    )

    content.append(
        Paragraph(
            f"<b>Finding:</b> {safe_text(check.finding)}",
            styles["ReportBodyCustom"],
        )
    )

    content.append(
        Paragraph(
            f"<b>Evidence source:</b> {safe_text(check.source)}",
            styles["ReportSmallCustom"],
        )
    )

    content.append(
        Paragraph(
            f"<b>Confidence note:</b> "
            f"{safe_text(check.confidence_note)}",
            styles["ReportSmallCustom"],
        )
    )

    if check.claim:
        content.append(
            Paragraph(
                f"<b>Claim type:</b> "
                f"{safe_text(check.claim.claim_type)}",
                styles["ReportSmallCustom"],
            )
        )

    # Use a separate line instead of a large unbreakable
    # table so long findings can flow across PDF pages.
    content.append(
        HRFlowable(
            width="100%",
            thickness=0.6,
            color=finding_color(kind),
            spaceBefore=6,
            spaceAfter=10,
        )
    )

    return content


def generate_evidence_pdf(
    report: VerificationReport,
) -> bytes:
    """
    Generate an in-memory PDF evidence report.

    No file is written to disk.
    This function does not perform verification.
    It formats existing check results.
    """

    if not isinstance(report, VerificationReport):
        raise TypeError(
            "report must be a VerificationReport instance"
        )

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=19 * mm,
        bottomMargin=22 * mm,
        title="Offer Evidence Verification Report",
        author="Offer Evidence Verifier",
    )

    styles = get_styles()
    story = []

    story.append(
        Paragraph(
            "OFFER EVIDENCE REPORT",
            styles["ReportTitleCustom"],
        )
    )

    story.append(
        Paragraph(
            "Evidence-based internship and job offer screening",
            styles["ReportSubtitleCustom"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Report ID:</b> {safe_text(report.report_id)}",
            styles["ReportBodyCustom"],
        )
    )

    created = report.created_at.strftime(
        "%d %B %Y, %H:%M UTC"
    )

    story.append(
        Paragraph(
            f"<b>Generated:</b> {safe_text(created)}",
            styles["ReportBodyCustom"],
        )
    )

    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "Evidence Summary",
            styles["ReportSectionCustom"],
        )
    )

    story.append(
        make_summary_table(report, styles)
    )

    story.append(
        Paragraph(
            "Counts represent individual check findings, "
            "not a fraud probability or authenticity score.",
            styles["ReportSmallCustom"],
        )
    )

    story.append(
        Paragraph(
            "Detailed Findings",
            styles["ReportSectionCustom"],
        )
    )

    if not report.checks:
        story.append(
            Paragraph(
                "No checks were available in this report.",
                styles["ReportBodyCustom"],
            )
        )

    for index, check in enumerate(
        report.checks,
        start=1,
    ):
        story.extend(
            make_finding(check, index, styles)
        )

    story.append(
        Paragraph(
            "Recommended Safe Steps",
            styles["ReportSectionCustom"],
        )
    )

    if report.safe_steps:
        for index, step in enumerate(
            report.safe_steps,
            start=1,
        ):
            story.append(
                Paragraph(
                    f"{index}. {safe_text(step)}",
                    styles["ReportBodyCustom"],
                )
            )
    else:
        story.append(
            Paragraph(
                "No specific recommendations available.",
                styles["ReportBodyCustom"],
            )
        )

    story.append(
        Paragraph(
            "Limitations and Disclaimer",
            styles["ReportSectionCustom"],
        )
    )

    story.append(
        Paragraph(
            safe_text(report.disclaimer),
            styles["ReportBodyCustom"],
        )
    )

    story.append(
        Paragraph(
            "A matching domain, an older domain, or an "
            "absence of warning patterns does not prove "
            "that an offer is authentic. A risk signal "
            "does not prove fraud. Source references "
            "identify where a check obtained or sought "
            "evidence; they do not necessarily constitute "
            "independent confirmation.",
            styles["ReportSmallCustom"],
        )
    )

    story.append(
        Paragraph(
            "Common sensitive-number patterns are masked "
            "in the PDF, but names, email addresses and "
            "other personal information may remain. "
            "Review the report before sharing.",
            styles["ReportSmallCustom"],
        )
    )

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
