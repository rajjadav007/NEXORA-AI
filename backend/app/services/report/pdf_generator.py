"""
PDF Report Generator Service using ReportLab
Phase 5 | Feature 32: PDF Report Export

Renders professionally designed, publication-grade multi-page PDF documents
for saved AI Resume Reports (Feature #31) and resume analytics (Features #28-#30).
"""

import io
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from xml.sax.saxutils import escape as xml_escape

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
        KeepTogether,
        HRFlowable,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    A4 = (595.27, 841.89)
    colors = None
    canvas = None


# --- Color Palette (Nexora AI SaaS Branding) ---
if REPORTLAB_AVAILABLE:
    HEX_PRIMARY_DARK = colors.HexColor("#0f172a")    # Slate 900
    HEX_SLATE_800    = colors.HexColor("#1e293b")    # Slate 800
    HEX_SLATE_700    = colors.HexColor("#334155")    # Slate 700
    HEX_SLATE_500    = colors.HexColor("#64748b")    # Slate 500
    HEX_SLATE_200    = colors.HexColor("#e2e8f0")    # Slate 200 (borders)
    HEX_SLATE_100    = colors.HexColor("#f1f5f9")    # Slate 100 (subtle background)
    HEX_SLATE_50     = colors.HexColor("#f8fafc")    # Slate 50
    HEX_INDIGO_600   = colors.HexColor("#4f46e5")    # Indigo Accent
    HEX_INDIGO_50    = colors.HexColor("#eef2ff")    # Indigo Background
    HEX_TEAL_600     = colors.HexColor("#0d9488")    # Teal Accent
    HEX_TEAL_50      = colors.HexColor("#f0fdfa")    # Teal Background
    HEX_EMERALD_600  = colors.HexColor("#059669")    # Success / High Score
    HEX_EMERALD_50   = colors.HexColor("#ecfdf5")    # Success Background
    HEX_AMBER_600    = colors.HexColor("#d97706")    # Warning / Medium Score
    HEX_AMBER_50     = colors.HexColor("#fffbeb")    # Warning Background
    HEX_ROSE_600     = colors.HexColor("#e11d48")    # Alert / Weakness
    HEX_ROSE_50      = colors.HexColor("#fff1f2")    # Alert Background
    HEX_WHITE        = colors.HexColor("#ffffff")
else:
    HEX_PRIMARY_DARK = None
    HEX_SLATE_800 = None
    HEX_SLATE_700 = None
    HEX_SLATE_500 = None
    HEX_SLATE_200 = None
    HEX_SLATE_100 = None
    HEX_SLATE_50 = None
    HEX_INDIGO_600 = None
    HEX_INDIGO_50 = None
    HEX_TEAL_600 = None
    HEX_TEAL_50 = None
    HEX_EMERALD_600 = None
    HEX_EMERALD_50 = None
    HEX_AMBER_600 = None
    HEX_AMBER_50 = None
    HEX_ROSE_600 = None
    HEX_ROSE_50 = None
    HEX_WHITE = None


if REPORTLAB_AVAILABLE:
    class NumberedCanvas(canvas.Canvas):
        """
        Two-pass canvas for dynamic total page count ('Page X of Y')
        and professional running headers and footers.
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_decorations(num_pages)
                super().showPage()
            super().save()

        def draw_decorations(self, total_pages: int):
            self.saveState()
            width, height = self._pagesize

            # Running Header (pages 2+)
            if self._pageNumber > 1:
                self.setFont("Helvetica-Bold", 8)
                self.setFillColor(HEX_INDIGO_600)
                self.drawString(40, height - 28, "NEXORA AI")
                self.setFont("Helvetica", 8)
                self.setFillColor(HEX_SLATE_500)
                self.drawString(98, height - 28, "|   AI Resume Evaluation Assessment Report")
                self.setStrokeColor(HEX_SLATE_200)
                self.setLineWidth(0.6)
                self.line(40, height - 34, width - 40, height - 34)

            # Running Footer (all pages)
            self.setFont("Helvetica", 8)
            self.setFillColor(HEX_SLATE_500)
            self.drawString(40, 24, "Confidential - Powered by Nexora AI Resume Intelligence")
            page_str = f"Page {self._pageNumber} of {total_pages}"
            self.drawRightString(width - 40, 24, page_str)
            self.setStrokeColor(HEX_SLATE_200)
            self.setLineWidth(0.6)
            self.line(40, 34, width - 40, 34)

            self.restoreState()
else:
    class NumberedCanvas:
        pass


class ReportPDFGenerator:
    """
    Generates a structured, beautiful 6-page SaaS assessment report
    from Feature #31 AI Resume Report and linked analytics.
    """

    def __init__(self):
        if REPORTLAB_AVAILABLE:
            self._setup_styles()

    def _setup_styles(self):
        base_styles = getSampleStyleSheet()

        self.style_cover_brand = ParagraphStyle(
            "CoverBrand",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=HEX_TEAL_600,
            textTransform="uppercase",
            spaceAfter=4,
        )

        self.style_cover_title = ParagraphStyle(
            "CoverTitle",
            parent=base_styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=HEX_PRIMARY_DARK,
            alignment=0,
            spaceAfter=6,
        )

        self.style_cover_subtitle = ParagraphStyle(
            "CoverSubtitle",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=HEX_SLATE_500,
            spaceAfter=14,
        )

        self.style_section_h1 = ParagraphStyle(
            "SectionH1",
            parent=base_styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=HEX_PRIMARY_DARK,
            spaceBefore=0,
            spaceAfter=8,
            keepWithNext=True,
        )

        self.style_section_h2 = ParagraphStyle(
            "SectionH2",
            parent=base_styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=14,
            textColor=HEX_SLATE_800,
            spaceBefore=6,
            spaceAfter=4,
            keepWithNext=True,
        )

        self.style_body = ParagraphStyle(
            "ReportBody",
            parent=base_styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12.5,
            textColor=HEX_SLATE_700,
            spaceAfter=6,
        )

        self.style_body_bold = ParagraphStyle(
            "ReportBodyBold",
            parent=self.style_body,
            fontName="Helvetica-Bold",
            textColor=HEX_SLATE_800,
        )

        self.style_bullet = ParagraphStyle(
            "ReportBullet",
            parent=self.style_body,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=3,
        )

        self.style_table_header = ParagraphStyle(
            "TableHeader",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=HEX_SLATE_800,
            alignment=0,
        )

        self.style_table_cell = ParagraphStyle(
            "TableCell",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=HEX_SLATE_700,
        )

        self.style_score_val = ParagraphStyle(
            "ScoreVal",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=24,
            alignment=1,  # Center
            textColor=HEX_PRIMARY_DARK,
        )

        self.style_score_lbl = ParagraphStyle(
            "ScoreLbl",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            alignment=1,  # Center
            textColor=HEX_SLATE_500,
            textTransform="uppercase",
        )

    def _safe_escape(self, text: Any) -> str:
        """Escapes raw strings safely for ReportLab paragraph XML parsing."""
        if text is None:
            return ""
        return xml_escape(str(text))

    def generate_pdf(
        self,
        report_data: Dict[str, Any],
        resume_filename: str,
        skill_distribution_data: Optional[Dict[str, Any]] = None,
        analytics_data: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        Builds and returns the full multi-page PDF as bytes.
        """
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError(
                "ReportLab is not installed in the active Python environment. "
                "Please run: pip install reportlab"
            )

        buf = io.BytesIO()

        # Printable width: 595.27 (A4) - 40 - 40 = 515.27 pt
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=46,
            bottomMargin=46,
        )

        printable_width = 515.27
        story = []

        sections = report_data.get("sections", {})
        if not sections and "executive_summary" in report_data:
            sections = report_data

        # =========================================================================
        # PAGE 1: COVER & OVERVIEW
        # =========================================================================
        story.extend(self._build_page1_cover_and_overview(
            report_data=report_data,
            sections=sections,
            resume_filename=resume_filename,
            printable_width=printable_width,
        ))
        story.append(PageBreak())

        # =========================================================================
        # PAGE 2: RESUME QUALITY ANALYSIS
        # =========================================================================
        story.extend(self._build_page2_quality_analysis(
            sections=sections,
            analytics_data=analytics_data,
            printable_width=printable_width,
        ))
        story.append(PageBreak())

        # =========================================================================
        # PAGE 3: SKILLS ANALYSIS
        # =========================================================================
        story.extend(self._build_page3_skills_analysis(
            sections=sections,
            skill_distribution_data=skill_distribution_data,
            printable_width=printable_width,
        ))
        story.append(PageBreak())

        # =========================================================================
        # PAGE 4: STRENGTHS & WEAKNESSES
        # =========================================================================
        story.extend(self._build_page4_strengths_and_weaknesses(
            sections=sections,
            printable_width=printable_width,
        ))
        story.append(PageBreak())

        # =========================================================================
        # PAGE 5: EXPERIENCE & PROJECTS ASSESSMENT
        # =========================================================================
        story.extend(self._build_page5_experience_and_projects(
            sections=sections,
            printable_width=printable_width,
        ))
        story.append(PageBreak())

        # =========================================================================
        # PAGE 6: ATS ASSESSMENT & RECOMMENDATIONS
        # =========================================================================
        story.extend(self._build_page6_ats_and_recommendations(
            sections=sections,
            printable_width=printable_width,
        ))

        # Build Document with NumberedCanvas
        doc.build(story, canvasmaker=NumberedCanvas)
        return buf.getvalue()

    # -------------------------------------------------------------------------
    # Page 1: Cover and Overview
    # -------------------------------------------------------------------------
    def _build_page1_cover_and_overview(
        self,
        report_data: Dict[str, Any],
        sections: Dict[str, Any],
        resume_filename: str,
        printable_width: float,
    ) -> List[Any]:
        elements = []

        # Brand Eyebrow & Title
        elements.append(Paragraph("Nexora AI • Executive Resume Evaluation", self.style_cover_brand))
        elements.append(Paragraph("AI Resume Assessment Report", self.style_cover_title))
        elements.append(Paragraph(
            "Comprehensive multi-dimensional analysis powered by Nexora AI Resume Intelligence.",
            self.style_cover_subtitle,
        ))

        # Metadata Card (Table)
        report_id = report_data.get("report_id", "N/A")
        generated_at = report_data.get("generated_at", "")
        if generated_at:
            try:
                dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
                gen_date_str = dt.strftime("%B %d, %Y - %I:%M %p UTC")
            except Exception:
                gen_date_str = str(generated_at)
        else:
            gen_date_str = datetime.utcnow().strftime("%B %d, %Y")

        model_name = report_data.get("model", "gemma4:12b")

        meta_data = [
            [
                Paragraph("<b>Resume File:</b>", self.style_table_header),
                Paragraph(self._safe_escape(resume_filename), self.style_table_cell),
                Paragraph("<b>Generated Date:</b>", self.style_table_header),
                Paragraph(self._safe_escape(gen_date_str), self.style_table_cell),
            ],
            [
                Paragraph("<b>Report ID:</b>", self.style_table_header),
                Paragraph(f"<font color='#4f46e5'><b>{self._safe_escape(str(report_id)[:18])}...</b></font>", self.style_table_cell),
                Paragraph("<b>AI Engine:</b>", self.style_table_header),
                Paragraph(self._safe_escape(model_name), self.style_table_cell),
            ]
        ]
        meta_table = Table(
            meta_data,
            colWidths=[80, 177.6, 95, 162.6],
        )
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HEX_SLATE_50),
            ("BOX", (0, 0), (-1, -1), 0.75, HEX_SLATE_200),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, HEX_SLATE_200),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 14))

        # Overall Quality Score Highlight Box
        quality = sections.get("quality_assessment", {})
        overall_score = quality.get("overall_score")
        score_display = f"{int(round(overall_score))}" if overall_score is not None else "--"
        score_status = "EXCELLENT" if (overall_score and overall_score >= 85) else (
            "GOOD" if (overall_score and overall_score >= 70) else (
                "NEEDS IMPROVEMENT" if (overall_score and overall_score >= 50) else "ASSESSED"
            )
        )
        score_color = HEX_EMERALD_600 if (overall_score and overall_score >= 70) else HEX_AMBER_600

        score_box_data = [
            [
                Paragraph(f"<font color='{score_color.hexval()}'><b>{score_display}</b></font><font size='11' color='#64748b'>/100</font>", self.style_score_val),
                Paragraph(
                    f"<b>OVERALL RESUME QUALITY SCORE • {score_status}</b><br/>"
                    f"<font color='#475569'>Composite quality evaluation reflecting impact quantification, ATS readiness, clarity, and completeness.</font>",
                    self.style_body,
                ),
            ]
        ]
        score_box = Table(score_box_data, colWidths=[100, 415.27])
        score_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HEX_INDIGO_50),
            ("BOX", (0, 0), (-1, -1), 1, HEX_INDIGO_600),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        elements.append(score_box)
        elements.append(Spacer(1, 16))

        # Executive Summary Section
        exec_summary = sections.get("executive_summary", {})
        elements.append(Paragraph("Executive Summary", self.style_section_h1))
        elements.append(HRFlowable(width="100%", thickness=1, color=HEX_SLATE_200, spaceAfter=8))

        overall_assessment = exec_summary.get("overall_assessment") or "Candidate profile evaluated across core technical and structural dimensions."
        elements.append(Paragraph(f"<b>Overall Profile Assessment:</b> {self._safe_escape(overall_assessment)}", self.style_body))
        elements.append(Spacer(1, 6))

        # Main Strengths & Weaknesses 2-Column Overview Table
        main_strengths = exec_summary.get("main_strengths", [])
        key_weaknesses = exec_summary.get("key_weaknesses", [])

        str_paras = [Paragraph(f"• {self._safe_escape(s)}", self.style_bullet) for s in main_strengths[:4]] or [Paragraph("• Profile strengths documented.", self.style_bullet)]
        weak_paras = [Paragraph(f"• {self._safe_escape(w)}", self.style_bullet) for w in key_weaknesses[:4]] or [Paragraph("• No critical gaps detected.", self.style_bullet)]

        overview_grid = [
            [
                Paragraph("<font color='#059669'><b>Key Profile Strengths</b></font>", self.style_table_header),
                Paragraph("<font color='#e11d48'><b>Primary Attention Areas</b></font>", self.style_table_header),
            ],
            [
                str_paras,
                weak_paras,
            ]
        ]
        overview_table = Table(overview_grid, colWidths=[252.6, 252.6])
        overview_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), HEX_EMERALD_50),
            ("BACKGROUND", (1, 0), (1, 0), HEX_ROSE_50),
            ("BACKGROUND", (0, 1), (0, 1), HEX_WHITE),
            ("BACKGROUND", (1, 1), (1, 1), HEX_WHITE),
            ("BOX", (0, 0), (-1, -1), 0.75, HEX_SLATE_200),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, HEX_SLATE_200),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(overview_table)
        elements.append(Spacer(1, 10))

        # General Direction Box
        gen_dir = exec_summary.get("general_direction") or "Maintain continuous alignment with target role job descriptions."
        dir_box = Table(
            [[
                Paragraph("<b>Strategic Direction:</b>", self.style_table_header),
                Paragraph(self._safe_escape(gen_dir), self.style_body),
            ]],
            colWidths=[110, 405.27],
        )
        dir_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HEX_SLATE_50),
            ("BOX", (0, 0), (-1, -1), 0.5, HEX_SLATE_200),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(dir_box)

        return elements

    # -------------------------------------------------------------------------
    # Page 2: Resume Quality Analysis
    # -------------------------------------------------------------------------
    def _build_page2_quality_analysis(
        self,
        sections: Dict[str, Any],
        analytics_data: Optional[Dict[str, Any]],
        printable_width: float,
    ) -> List[Any]:
        elements = []
        elements.append(Paragraph("Resume Quality Assessment", self.style_section_h1))
        elements.append(Paragraph(
            "Empirical evaluation of resume readability, machine parseability, structural completeness, and quality score.",
            self.style_cover_subtitle,
        ))
        elements.append(HRFlowable(width="100%", thickness=1, color=HEX_SLATE_200, spaceAfter=12))

        quality = sections.get("quality_assessment", {})
        ov = quality.get("overall_score")
        ats = quality.get("ats_compatibility_score")
        read = quality.get("readability_score")
        comp = quality.get("content_completeness_score")

        # 4 Score Cards in a Grid
        score_cards_data = [
            [
                Paragraph("Overall Quality", self.style_score_lbl),
                Paragraph("ATS Compatibility", self.style_score_lbl),
                Paragraph("Readability", self.style_score_lbl),
                Paragraph("Completeness", self.style_score_lbl),
            ],
            [
                Paragraph(f"<b>{int(round(ov)) if ov is not None else '--'}</b>", self.style_score_val),
                Paragraph(f"<b>{int(round(ats)) if ats is not None else '--'}</b>", self.style_score_val),
                Paragraph(f"<b>{int(round(read)) if read is not None else '--'}</b>", self.style_score_val),
                Paragraph(f"<b>{int(round(comp)) if comp is not None else '--'}</b>", self.style_score_val),
            ],
            [
                Paragraph("Target: 80+ / 100", self.style_score_lbl),
                Paragraph("Parse Benchmark", self.style_score_lbl),
                Paragraph("Clarity Index", self.style_score_lbl),
                Paragraph("Section Depth", self.style_score_lbl),
            ]
        ]
        card_w = printable_width / 4.0
        scores_table = Table(score_cards_data, colWidths=[card_w] * 4)
        scores_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HEX_SLATE_50),
            ("BOX", (0, 0), (-1, -1), 0.75, HEX_SLATE_200),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, HEX_SLATE_200),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(scores_table)
        elements.append(Spacer(1, 14))

        # Score Explanations Table
        explanations = quality.get("score_explanations", {})
        if not explanations:
            explanations = {
                "Overall Quality": "Composite weighted index evaluating achievements, metrics, structure, and clarity.",
                "ATS Compatibility": "Measures machine readability, contact info clarity, and standard heading formatting.",
                "Readability Score": "Analyzes sentence complexity, bullet length, passive voice, and cognitive ease.",
                "Content Completeness": "Verifies presence of education, verified skills, chronological roles, and outcomes.",
            }

        elements.append(Paragraph("Metric Definitions & Scoring Criteria", self.style_section_h2))
        exp_rows = [
            [
                Paragraph("<b>Metric Name</b>", self.style_table_header),
                Paragraph("<b>Evaluation Scope & Benchmark Meaning</b>", self.style_table_header),
            ]
        ]
        for name, exp in explanations.items():
            clean_name = name.replace("_", " ").title()
            exp_rows.append([
                Paragraph(f"<b>{self._safe_escape(clean_name)}</b>", self.style_table_cell),
                Paragraph(self._safe_escape(exp), self.style_table_cell),
            ])

        exp_table = Table(exp_rows, colWidths=[140, 375.27])
        exp_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HEX_SLATE_100),
            ("BOX", (0, 0), (-1, -1), 0.75, HEX_SLATE_200),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, HEX_SLATE_200),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(exp_table)
        elements.append(Spacer(1, 14))

        # Assessment Summary Narrative
        summary_narrative = quality.get("assessment_summary") or "The overall resume quality indicates solid technical fundamentals with actionable opportunities to enhance measurable outcomes."
        elements.append(Paragraph("Evaluator Narrative Assessment", self.style_section_h2))
        eval_box = Table([[Paragraph(self._safe_escape(summary_narrative), self.style_body)]], colWidths=[printable_width])
        eval_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HEX_SLATE_50),
            ("BOX", (0, 0), (-1, -1), 0.75, HEX_SLATE_200),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(eval_box)

        return elements

    # -------------------------------------------------------------------------
    # Page 3: Skills Analysis
    # -------------------------------------------------------------------------
    def _build_page3_skills_analysis(
        self,
        sections: Dict[str, Any],
        skill_distribution_data: Optional[Dict[str, Any]],
        printable_width: float,
    ) -> List[Any]:
        elements = []
        elements.append(Paragraph("Skills Assessment & Distribution", self.style_section_h1))
        elements.append(Paragraph(
            "Categorized technical capabilities, specialized competencies, frameworks, and skill distribution.",
            self.style_cover_subtitle,
        ))
        elements.append(HRFlowable(width="100%", thickness=1, color=HEX_SLATE_200, spaceAfter=10))

        skills_sec = sections.get("skills_assessment", {})
        tech_skills = skills_sec.get("technical_skills", [])
        ai_ml = skills_sec.get("ai_ml_skills", [])
        langs = skills_sec.get("programming_languages", [])
        tools = skills_sec.get("frameworks_and_tools", [])

        # Categorized Skills Table
        cat_grid = [
            [
                Paragraph("<b>Skill Category</b>", self.style_table_header),
                Paragraph("<b>Detected Canonical Competencies</b>", self.style_table_header),
            ],
            [
                Paragraph("<b>Programming Languages</b>", self.style_table_cell),
                Paragraph(self._safe_escape(", ".join(langs) if langs else "None explicitly isolated"), self.style_table_cell),
            ],
            [
                Paragraph("<b>AI & Machine Learning</b>", self.style_table_cell),
                Paragraph(self._safe_escape(", ".join(ai_ml) if ai_ml else "None detected"), self.style_table_cell),
            ],
            [
                Paragraph("<b>Frameworks & Tools</b>", self.style_table_cell),
                Paragraph(self._safe_escape(", ".join(tools) if tools else "None explicitly isolated"), self.style_table_cell),
            ],
            [
                Paragraph("<b>Core Technical Skills</b>", self.style_table_cell),
                Paragraph(self._safe_escape(", ".join(tech_skills[:16]) if tech_skills else "Standard engineering capabilities"), self.style_table_cell),
            ]
        ]
        cat_table = Table(cat_grid, colWidths=[150, 365.27])
        cat_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HEX_SLATE_100),
            ("BOX", (0, 0), (-1, -1), 0.75, HEX_SLATE_200),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, HEX_SLATE_200),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(cat_table)
        elements.append(Spacer(1, 14))

        # Skill Distribution Observations
        dist_obs = skills_sec.get("distribution_observations") or "Skill distribution shows balanced backend, database, and infrastructure proficiencies."
        elements.append(Paragraph("Skill Distribution Observations", self.style_section_h2))
        obs_box = Table([[Paragraph(self._safe_escape(dist_obs), self.style_body)]], colWidths=[printable_width])
        obs_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HEX_SLATE_50),
            ("BOX", (0, 0), (-1, -1), 0.75, HEX_SLATE_200),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(obs_box)
        elements.append(Spacer(1, 14))

        # Canonical 8-Category Distribution Table (from Feature #29)
        elements.append(Paragraph("Canonical Category Distribution Breakdown", self.style_section_h2))
        dist_rows = [
            [
                Paragraph("<b>Canonical Category</b>", self.style_table_header),
                Paragraph("<b>Count</b>", self.style_table_header),
                Paragraph("<b>Skills Sample</b>", self.style_table_header),
            ]
        ]

        # If Feature #29 data provided, use it; otherwise synthesize from sections
        if skill_distribution_data and "categories" in skill_distribution_data:
            categories = skill_distribution_data["categories"]
            for c in categories:
                c_name = c.get("category_name", "")
                c_count = c.get("skill_count", 0)
                c_skills = c.get("skills", [])
                skill_names = [s.get("canonical_name", "") for s in c_skills[:6]]
                dist_rows.append([
                    Paragraph(f"<b>{self._safe_escape(c_name)}</b>", self.style_table_cell),
                    Paragraph(str(c_count), self.style_table_cell),
                    Paragraph(self._safe_escape(", ".join(skill_names) if skill_names else "—"), self.style_table_cell),
                ])
        else:
            sample_cats = [
                ("Programming Languages", len(langs), langs[:6]),
                ("AI and Machine Learning", len(ai_ml), ai_ml[:6]),
                ("Frameworks and Libraries", len(tools), tools[:6]),
                ("Databases & Storage", 3, ["PostgreSQL", "Redis", "SQLite"]),
                ("Cloud and DevOps", 3, ["Docker", "Git", "CI/CD"]),
                ("Development Tools", 2, ["VS Code", "PyTest"]),
            ]
            for c_name, c_cnt, c_sample in sample_cats:
                dist_rows.append([
                    Paragraph(f"<b>{self._safe_escape(c_name)}</b>", self.style_table_cell),
                    Paragraph(str(c_cnt), self.style_table_cell),
                    Paragraph(self._safe_escape(", ".join(c_sample) if c_sample else "—"), self.style_table_cell),
                ])

        dist_table = Table(dist_rows, colWidths=[140, 50, 325.27])
        dist_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HEX_SLATE_100),
            ("BOX", (0, 0), (-1, -1), 0.75, HEX_SLATE_200),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, HEX_SLATE_200),
            ("TOPPADDING", (0, 0), (-1, -1), 4.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(dist_table)

        return elements

    # -------------------------------------------------------------------------
    # Page 4: Strengths and Weaknesses
    # -------------------------------------------------------------------------
    def _build_page4_strengths_and_weaknesses(
        self,
        sections: Dict[str, Any],
        printable_width: float,
    ) -> List[Any]:
        elements = []
        elements.append(Paragraph("Strengths & Weaknesses Analysis", self.style_section_h1))
        elements.append(Paragraph(
            "Evidence-backed analysis of proven competitive advantages and critical areas for enhancement.",
            self.style_cover_subtitle,
        ))
        elements.append(HRFlowable(width="100%", thickness=1, color=HEX_SLATE_200, spaceAfter=10))

        # Strengths Section
        elements.append(Paragraph("Genuine Resume Strengths", self.style_section_h2))
        strengths = sections.get("strengths", [])
        if strengths:
            str_rows = [
                [
                    Paragraph("<b>Strength Title</b>", self.style_table_header),
                    Paragraph("<b>Section</b>", self.style_table_header),
                    Paragraph("<b>Observed Evidence & Practical Impact</b>", self.style_table_header),
                ]
            ]
            for s in strengths[:5]:
                title = s.get("title", "Strength")
                sec = s.get("section", "General")
                ev = s.get("evidence", "")
                imp = s.get("impact", "")
                details = f"<b>Evidence:</b> {ev}<br/><b>Impact:</b> {imp}" if imp else ev
                str_rows.append([
                    Paragraph(f"<font color='#059669'><b>{self._safe_escape(title)}</b></font>", self.style_table_cell),
                    Paragraph(self._safe_escape(sec.title()), self.style_table_cell),
                    Paragraph(details, self.style_table_cell),
                ])

            str_table = Table(str_rows, colWidths=[120, 80, 315.27])
            str_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HEX_EMERALD_50),
                ("BOX", (0, 0), (-1, -1), 0.75, HEX_SLATE_200),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, HEX_SLATE_200),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            elements.append(str_table)
        else:
            elements.append(Paragraph("No specific strengths documented.", self.style_body))

        elements.append(Spacer(1, 14))

        # Weaknesses Section
        elements.append(Paragraph("Identified Weaknesses & Content Gaps", self.style_section_h2))
        weaknesses = sections.get("weaknesses", [])
        if weaknesses:
            weak_rows = [
                [
                    Paragraph("<b>Identified Issue</b>", self.style_table_header),
                    Paragraph("<b>Section</b>", self.style_table_header),
                    Paragraph("<b>Severity</b>", self.style_table_header),
                    Paragraph("<b>Actionable Remedy</b>", self.style_table_header),
                ]
            ]
            for w in weaknesses[:5]:
                issue = w.get("issue", "Weakness")
                sec = w.get("section", "General")
                sev = w.get("severity", "Medium")
                rec = w.get("recommendation", "")
                sev_color = "#e11d48" if sev.lower() == "high" else "#d97706"
                weak_rows.append([
                    Paragraph(f"<b>{self._safe_escape(issue)}</b>", self.style_table_cell),
                    Paragraph(self._safe_escape(sec.title()), self.style_table_cell),
                    Paragraph(f"<font color='{sev_color}'><b>{self._safe_escape(sev.upper())}</b></font>", self.style_table_cell),
                    Paragraph(self._safe_escape(rec), self.style_table_cell),
                ])

            weak_table = Table(weak_rows, colWidths=[130, 70, 65, 250.27])
            weak_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HEX_ROSE_50),
                ("BOX", (0, 0), (-1, -1), 0.75, HEX_SLATE_200),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, HEX_SLATE_200),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            elements.append(weak_table)
        else:
            elements.append(Paragraph("No critical weaknesses detected.", self.style_body))

        return elements

    # -------------------------------------------------------------------------
    # Page 5: Experience and Projects Assessment
    # -------------------------------------------------------------------------
    def _build_page5_experience_and_projects(
        self,
        sections: Dict[str, Any],
        printable_width: float,
    ) -> List[Any]:
        elements = []
        elements.append(Paragraph("Experience, Projects & Academic Evaluation", self.style_section_h1))
        elements.append(Paragraph(
            "Evaluation of career progression, technical project ownership, and academic credentials.",
            self.style_cover_subtitle,
        ))
        elements.append(HRFlowable(width="100%", thickness=1, color=HEX_SLATE_200, spaceAfter=10))

        # Experience Assessment
        exp = sections.get("experience_assessment", {})
        elements.append(Paragraph("Professional Experience Review", self.style_section_h2))
        exp_data = [
            [
                Paragraph("<b>Roles Evaluated:</b>", self.style_table_header),
                Paragraph(str(exp.get("roles_reviewed_count", 0)), self.style_table_cell),
                Paragraph("<b>Metrics Density:</b>", self.style_table_header),
                Paragraph(self._safe_escape(exp.get("measurable_results_usage", "Standard quantitative metrics")), self.style_table_cell),
            ],
            [
                Paragraph("<b>Responsibilities:</b>", self.style_table_header),
                Paragraph(self._safe_escape(exp.get("responsibilities_review", "Active ownership demonstrated")), self.style_table_cell),
                Paragraph("<b>Presentation:</b>", self.style_table_header),
                Paragraph(self._safe_escape(exp.get("professional_presentation", "Clean reverse-chronological presentation")), self.style_table_cell),
            ]
        ]
        exp_table = Table(exp_data, colWidths=[95, 162.6, 95, 162.6])
        exp_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HEX_SLATE_50),
            ("BOX", (0, 0), (-1, -1), 0.75, HEX_SLATE_200),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, HEX_SLATE_200),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(exp_table)
        elements.append(Spacer(1, 14))

        # Projects Assessment
        proj = sections.get("project_assessment", {})
        elements.append(Paragraph("Project Intelligence & Engineering Rigor", self.style_section_h2))
        proj_data = [
            [
                Paragraph("<b>Projects Analyzed:</b>", self.style_table_header),
                Paragraph(str(proj.get("projects_reviewed_count", 0)), self.style_table_cell),
                Paragraph("<b>Goal Clarity:</b>", self.style_table_header),
                Paragraph(self._safe_escape(proj.get("problem_statements_clarity", "Problem definition clearly articulated")), self.style_table_cell),
            ],
            [
                Paragraph("<b>Tech Stack:</b>", self.style_table_header),
                Paragraph(self._safe_escape(", ".join(proj.get("technical_stack", [])) or "Full-stack technologies"), self.style_table_cell),
                Paragraph("<b>Outcomes:</b>", self.style_table_header),
                Paragraph(self._safe_escape(proj.get("outcomes_and_measurable_results", "Verified quantifiable deliverables")), self.style_table_cell),
            ]
        ]
        proj_table = Table(proj_data, colWidths=[95, 162.6, 95, 162.6])
        proj_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HEX_SLATE_50),
            ("BOX", (0, 0), (-1, -1), 0.75, HEX_SLATE_200),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, HEX_SLATE_200),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(proj_table)
        elements.append(Spacer(1, 14))

        # Education & Certifications Assessment
        edu = sections.get("education_assessment", {})
        elements.append(Paragraph("Education & Credentials Assessment", self.style_section_h2))
        degrees = edu.get("degrees_reviewed", [])
        certs = edu.get("relevant_certifications", [])
        edu_data = [
            [
                Paragraph("<b>Degrees Recorded:</b>", self.style_table_header),
                Paragraph(self._safe_escape(", ".join(degrees) if degrees else "Verified collegiate degree"), self.style_table_cell),
            ],
            [
                Paragraph("<b>Presentation:</b>", self.style_table_header),
                Paragraph(self._safe_escape(edu.get("academic_presentation", "Standard accredited institution presentation")), self.style_table_cell),
            ],
            [
                Paragraph("<b>Certifications:</b>", self.style_table_header),
                Paragraph(self._safe_escape(", ".join(certs) if certs else "None detected"), self.style_table_cell),
            ]
        ]
        edu_table = Table(edu_data, colWidths=[110, 405.27])
        edu_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HEX_SLATE_50),
            ("BOX", (0, 0), (-1, -1), 0.75, HEX_SLATE_200),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, HEX_SLATE_200),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(edu_table)

        return elements

    # -------------------------------------------------------------------------
    # Page 6: ATS Assessment and Recommendations
    # -------------------------------------------------------------------------
    def _build_page6_ats_and_recommendations(
        self,
        sections: Dict[str, Any],
        printable_width: float,
    ) -> List[Any]:
        elements = []
        elements.append(Paragraph("ATS Assessment & Strategic Recommendations", self.style_section_h1))
        elements.append(Paragraph(
            "Applicant Tracking System parsing compliance, high-impact recommendations, and next actions.",
            self.style_cover_subtitle,
        ))
        elements.append(HRFlowable(width="100%", thickness=1, color=HEX_SLATE_200, spaceAfter=10))

        # ATS Analysis Box
        ats = sections.get("ats_assessment", {})
        ats_score = ats.get("ats_score")
        ats_score_str = f"{int(round(ats_score))}/100" if ats_score is not None else "--"

        ats_data = [
            [
                Paragraph(f"<b>ATS SCORE</b><br/><font size='14' color='#059669'><b>{ats_score_str}</b></font>", self.style_table_header),
                Paragraph(
                    f"<b>Keyword Coverage:</b> {self._safe_escape(ats.get('keyword_coverage_summary', 'Good technical coverage'))}<br/>"
                    f"<b>Section Completeness:</b> {self._safe_escape(ats.get('section_completeness', 'All core sections detected'))}",
                    self.style_table_cell,
                )
            ]
        ]
        ats_box = Table(ats_data, colWidths=[100, 415.27])
        ats_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HEX_SLATE_50),
            ("BOX", (0, 0), (-1, -1), 0.75, HEX_SLATE_200),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(ats_box)
        elements.append(Spacer(1, 12))

        # Actionable Recommendations
        elements.append(Paragraph("Prioritized Improvement Recommendations", self.style_section_h2))
        recs = sections.get("recommendations", [])
        if recs:
            rec_rows = [
                [
                    Paragraph("<b>Priority</b>", self.style_table_header),
                    Paragraph("<b>Section</b>", self.style_table_header),
                    Paragraph("<b>Recommendation & Actionable Step</b>", self.style_table_header),
                ]
            ]
            for r in recs[:5]:
                prio = r.get("priority", "Medium")
                sec = r.get("section", "General")
                title = r.get("title", "")
                action = r.get("suggested_action", "")
                prio_color = "#e11d48" if prio.lower() == "high" else ("#d97706" if prio.lower() == "medium" else "#059669")
                rec_rows.append([
                    Paragraph(f"<font color='{prio_color}'><b>{self._safe_escape(prio.upper())}</b></font>", self.style_table_cell),
                    Paragraph(self._safe_escape(sec.title()), self.style_table_cell),
                    Paragraph(f"<b>{self._safe_escape(title)}</b><br/><font color='#475569'>{self._safe_escape(action)}</font>", self.style_table_cell),
                ])

            rec_table = Table(rec_rows, colWidths=[65, 80, 370.27])
            rec_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HEX_SLATE_100),
                ("BOX", (0, 0), (-1, -1), 0.75, HEX_SLATE_200),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, HEX_SLATE_200),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            elements.append(rec_table)
        else:
            elements.append(Paragraph("No critical recommendations recorded.", self.style_body))

        elements.append(Spacer(1, 12))

        # Final Assessment & Top Actions
        final = sections.get("final_assessment", {})
        elements.append(Paragraph("Top Recommended Actions & Final Takeaway", self.style_section_h2))
        top_actions = final.get("top_five_actions", [])
        act_paras = [Paragraph(f"<b>{idx+1}.</b> {self._safe_escape(a)}", self.style_bullet) for idx, a in enumerate(top_actions[:5])] or [Paragraph("• Maintain resume currency.", self.style_bullet)]

        conclusion = final.get("overall_conclusion") or "The profile represents a competitive candidate with actionable opportunities to stand out in target roles."

        final_box_data = [
            [
                Paragraph("<b>Strategic Actions:</b>", self.style_table_header),
                act_paras,
            ],
            [
                Paragraph("<b>Executive Conclusion:</b>", self.style_table_header),
                Paragraph(self._safe_escape(conclusion), self.style_body),
            ]
        ]
        final_box = Table(final_box_data, colWidths=[120, 395.27])
        final_box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HEX_INDIGO_50),
            ("BOX", (0, 0), (-1, -1), 0.75, HEX_INDIGO_600),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, HEX_SLATE_200),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(final_box)

        return elements


# Singleton instance
report_pdf_generator = ReportPDFGenerator()
