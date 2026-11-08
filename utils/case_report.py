
from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable
)

from core.cloudflare_llm import generate_response


def generate_case_summary(messages, uploaded_documents=None):
    conversation = []

    for message in messages:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        conversation.append(f"{role.upper()}: {content}")

    document_context = ""

    if uploaded_documents:
        for name, document in uploaded_documents.items():

            # Handle both dictionary and string formats
            if isinstance(document, dict):
                content = (
                    document.get("text")
                    or document.get("content")
                    or ""
                )
            else:
                content = str(document)

            document_context += (
                f"\nDocument: {name}\n{content[:5000]}\n"
            )

    prompt = f"""
Prepare a factual cybercrime incident case report based on
the following conversation and uploaded documents.

CONVERSATION:
{chr(10).join(conversation)}

UPLOADED DOCUMENTS:
{document_context[:12000]}

Include these sections:

1. Incident Overview
2. Complainant Details
3. Type of Cybercrime
4. Incident Description
5. Transaction Details
6. Chronology of Events
7. Evidence Available
8. Actions Already Taken
9. Requested Assistance
10. Missing Information

Important instructions:
- Do not invent facts, names, dates, amounts or transaction IDs.
- Mark unavailable details as "Not provided".
- Clearly distinguish reported facts from assumptions.
- Use formal, simple English.
- This is a supporting case summary, not an official FIR.
"""

    messages_for_llm = [
        {
            "role": "system",
            "content": "You are a factual cybercrime case documentation assistant."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    return generate_response(
        messages_for_llm,
        temperature=0.2,
        max_tokens=1200
    )


def create_case_report_pdf(report_text):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#17365D"),
        fontSize=18,
        spaceAfter=8
    )

    heading_style = ParagraphStyle(
        "ReportHeading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#17365D"),
        fontSize=11,
        spaceBefore=10,
        spaceAfter=5
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=14,
        spaceAfter=6
    )

    story = [
        Paragraph("CYBERCRIME INCIDENT CASE REPORT", title_style),
        Paragraph(
            f"Generated on: {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
            styles["Normal"]
        ),
        Spacer(1, 8),
        HRFlowable(width="100%", thickness=1, color=colors.grey),
        Spacer(1, 12)
    ]

    for line in report_text.splitlines():

        line = line.strip()

        if not line:
            story.append(Spacer(1, 5))
            continue

        safe_line = escape(line)

        if (
            line.isupper()
            or (
                len(line) < 90
                and line[:1].isdigit()
                and "." in line[:4]
            )
        ):
            story.append(Paragraph(safe_line, heading_style))
        else:
            story.append(Paragraph(safe_line, body_style))

    story.extend([
        Spacer(1, 15),
        HRFlowable(width="100%", thickness=0.5, color=colors.grey),
        Spacer(1, 6),
        Paragraph(
            "<b>Disclaimer:</b> This document is an AI-generated "
            "supporting summary based on information provided by "
            "the user. It is not an official FIR, legal notice, "
            "or substitute for professional legal advice.",
            styles["Italic"]
        )
    ])

    document.build(story)

    return buffer.getvalue()
