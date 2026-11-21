"""
FORMGUARD AI - PDF Report Generator
Professional PDF report generation using ReportLab.
"""

import io
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))


class ReportGenerator:
    """Generate professional PDF verification reports using ReportLab."""

    # Color palette
    COLORS = {
        "primary": (27, 42, 74),       # #1B2A4A
        "secondary": (46, 80, 144),    # #2E5090
        "accent": (16, 185, 129),      # #10B981
        "warning": (245, 158, 11),     # #F59E0B
        "error": (239, 68, 68),        # #EF4444
        "text": (30, 41, 59),          # #1E293B
        "text_light": (100, 116, 139), # #64748B
        "bg_light": (248, 250, 252),   # #F8FAFC
        "white": (255, 255, 255),
        "border": (226, 232, 240),     # #E2E8F0
    }

    DISCLAIMER = (
        "This report provides AI-assisted document consistency and scheme-requirement checks. "
        "It is not an official government verification, eligibility decision, or guarantee of "
        "application approval. Always verify with official government portals and authorities."
    )

    def generate_report(
        self,
        verification_id: str,
        verification_result: Dict,
        extractions: Dict,
        language: str = "en",
    ) -> Optional[bytes]:
        """
        Generate a complete PDF verification report.
        Returns PDF as bytes, or None on failure.
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm, cm
            from reportlab.lib.colors import HexColor, Color
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                PageBreak, HRFlowable, KeepTogether,
            )
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        except ImportError:
            print("[Report] ReportLab not installed. Install with: pip install reportlab")
            return None

        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            title="FORMGUARD AI - Verification Report",
            author="FORMGUARD AI",
        )

        # Styles
        styles = getSampleStyleSheet()

        style_title = ParagraphStyle(
            'ReportTitle',
            parent=styles['Title'],
            fontSize=20,
            textColor=HexColor('#1B2A4A'),
            spaceAfter=6,
            alignment=TA_CENTER,
        )

        style_subtitle = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=HexColor('#64748B'),
            alignment=TA_CENTER,
            spaceAfter=12,
        )

        style_heading = ParagraphStyle(
            'ReportHeading',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=HexColor('#1B2A4A'),
            spaceBefore=16,
            spaceAfter=8,
            borderWidth=0,
            borderPadding=0,
        )

        style_body = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontSize=9,
            textColor=HexColor('#1E293B'),
            leading=14,
        )

        style_small = ParagraphStyle(
            'ReportSmall',
            parent=styles['Normal'],
            fontSize=7.5,
            textColor=HexColor('#64748B'),
            leading=10,
        )

        style_disclaimer = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=7,
            textColor=HexColor('#64748B'),
            leading=10,
            alignment=TA_CENTER,
            spaceBefore=20,
        )

        # Build content
        elements = []

        # ── Header ──
        elements.append(Paragraph("🛡️ FORMGUARD AI", style_title))
        elements.append(Paragraph("Intelligent Government Application Preflight Verification Report", style_subtitle))
        elements.append(Spacer(1, 4))

        # Report info
        report_info = [
            ["Report ID:", verification_id],
            ["Generated:", datetime.now().strftime('%d %B %Y, %I:%M %p')],
            ["Scheme:", verification_result.get("scheme_name", "N/A")],
            ["Academic Year:", verification_result.get("academic_year", "N/A")],
            ["Category:", verification_result.get("applicant_category", "N/A")],
            ["Documents Processed:", str(verification_result.get("documents_processed", 0))],
        ]

        info_table = Table(report_info, colWidths=[120, 350])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#64748B')),
            ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#1E293B')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(info_table)

        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#E2E8F0')))

        # ── Summary ──
        elements.append(Paragraph("Verification Summary", style_heading))

        pass_count = verification_result.get("pass_count", 0)
        warning_count = verification_result.get("warning_count", 0)
        critical_count = verification_result.get("critical_count", 0)
        review_count = verification_result.get("manual_review_count", 0)
        readiness = verification_result.get("overall_readiness", 0)

        summary_data = [
            ["Check Type", "Count", "Status"],
            ["✅ Passed", str(pass_count), "No issues"],
            ["⚠️ Warnings", str(warning_count), "Needs attention" if warning_count > 0 else "None"],
            ["❌ Critical", str(critical_count), "Must fix" if critical_count > 0 else "None"],
            ["🔍 Manual Review", str(review_count), "Verify manually" if review_count > 0 else "None"],
            ["Overall Readiness", f"{readiness:.0f}%",
             "Ready" if readiness >= 80 else "Needs work" if readiness >= 50 else "Significant issues"],
        ]

        summary_table = Table(summary_data, colWidths=[160, 80, 230])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1B2A4A')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F8FAFC')]),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ]))
        elements.append(summary_table)

        # ── Detailed Findings ──
        elements.append(Paragraph("Detailed Findings", style_heading))

        checks = verification_result.get("checks", [])
        severity_order = {"CRITICAL": 0, "WARNING": 1, "MANUAL_REVIEW": 2, "PASS": 3}
        sorted_checks = sorted(checks, key=lambda c: severity_order.get(c.get("severity", "PASS"), 4))

        for i, check in enumerate(sorted_checks, 1):
            severity = check.get("severity", "PASS")
            icon = {"CRITICAL": "❌", "WARNING": "⚠️", "MANUAL_REVIEW": "🔍", "PASS": "✅"}.get(severity, "⚪")

            finding_text = (
                f"<b>{i}. {icon} [{severity}] {check.get('check_name', 'Check')}</b><br/>"
                f"<b>Field:</b> {check.get('field_checked', 'N/A')}<br/>"
                f"<b>Reason:</b> {check.get('reason', 'N/A')}<br/>"
            )

            if check.get("extracted_values"):
                values_str = ", ".join(f"{k}: {v}" for k, v in check["extracted_values"].items())
                finding_text += f"<b>Values:</b> {values_str}<br/>"

            if check.get("recommended_action"):
                finding_text += f"<b>Action:</b> {check['recommended_action']}<br/>"

            elements.append(Paragraph(finding_text, style_body))
            elements.append(Spacer(1, 6))

        # ── Extracted Fields Summary ──
        if extractions:
            elements.append(PageBreak())
            elements.append(Paragraph("Extracted Document Information", style_heading))

            from config import DOCUMENT_TYPES

            for doc_type, extraction in extractions.items():
                doc_name = DOCUMENT_TYPES.get(doc_type, {}).get("display_name", doc_type)
                elements.append(Paragraph(f"<b>📄 {doc_name}</b>", style_body))

                fields = extraction.get("extracted_fields", {})
                if fields:
                    field_data = [["Field", "Value", "Confidence"]]
                    for fname, fdata in fields.items():
                        if isinstance(fdata, dict):
                            value = fdata.get("value", "N/A")
                            conf = f"{fdata.get('confidence', 0):.0%}"
                        else:
                            value = str(fdata)
                            conf = "N/A"
                        field_data.append([fname.replace("_", " ").title(), value[:60], conf])

                    field_table = Table(field_data, colWidths=[140, 250, 80])
                    field_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2E5090')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#E2E8F0')),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F8FAFC')]),
                    ]))
                    elements.append(field_table)
                else:
                    elements.append(Paragraph("No fields extracted.", style_small))

                elements.append(Spacer(1, 10))

        # ── Checklist ──
        elements.append(Paragraph("Application Readiness Checklist", style_heading))

        for check in sorted_checks:
            severity = check.get("severity", "PASS")
            icon = {"CRITICAL": "☐", "WARNING": "☐", "MANUAL_REVIEW": "☐", "PASS": "☑"}.get(severity, "☐")
            status = {"CRITICAL": "[CRITICAL]", "WARNING": "[WARNING]", "MANUAL_REVIEW": "[REVIEW]", "PASS": "[OK]"}.get(severity, "")

            elements.append(Paragraph(
                f"{icon} {status} {check.get('check_name', 'Check')}",
                style_body,
            ))

        # ── Disclaimer ──
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#E2E8F0')))
        elements.append(Paragraph(f"⚠️ DISCLAIMER: {self.DISCLAIMER}", style_disclaimer))
        elements.append(Paragraph(
            "Generated by FORMGUARD AI | IDEA//FORGE Hackathon | Track 1: Civic Pulse",
            style_disclaimer,
        ))

        # Build PDF
        try:
            doc.build(elements)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            return pdf_bytes
        except Exception as e:
            print(f"[Report] PDF generation error: {e}")
            buffer.close()
            return None
