import os
from xml.sax.saxutils import escape

from resume_data import contact_line, load_resume, output_path, project_subtitle

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

PROFILE, EDUCATION, RESUME = load_resume("fullstack")
OUTPUT = str(output_path(RESUME))
TEMPLATE_ID = os.environ.get("RESUME_TEMPLATE_ID", "classic")
if TEMPLATE_ID != "classic":
    from resume_templates import generate_template

    generate_template(TEMPLATE_ID, PROFILE, EDUCATION, RESUME, "fullstack", OUTPUT)
    print("Done:", OUTPUT)
    raise SystemExit(0)

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=letter,
    leftMargin=0.60 * inch,
    rightMargin=0.60 * inch,
    topMargin=0.45 * inch,
    bottomMargin=0.45 * inch,
)

PAGE_W = letter[0] - 1.20 * inch
BLACK = colors.HexColor("#1a1a1a")
GRAY = colors.HexColor("#444444")
LIGHT_GRAY = colors.HexColor("#888888")
DIVIDER = colors.HexColor("#cccccc")


def style(name, **kwargs):
    defaults = dict(fontName="Helvetica", fontSize=9, textColor=BLACK,
                    leading=13, spaceBefore=0, spaceAfter=0)
    defaults.update(kwargs)
    return ParagraphStyle(name, **defaults)


S_NAME = style("Name", fontSize=16, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=20, spaceAfter=2)
S_CONTACT = style("Contact", fontSize=8.0, textColor=GRAY, alignment=TA_CENTER)
S_HEADLINE = style("Headline", fontSize=9.2, fontName="Helvetica-Bold", textColor=GRAY, alignment=TA_CENTER, leading=12, spaceAfter=2)
S_SECTION = style("Section", fontSize=8.8, fontName="Helvetica-Bold")
S_JOBTITLE = style("JobTitle", fontSize=9.2, fontName="Helvetica-Bold")
S_COMPANY = style("Company", fontSize=8.8, textColor=GRAY, spaceAfter=1)
S_DATE = style("Date", fontSize=8.2, textColor=LIGHT_GRAY, alignment=TA_RIGHT)
S_BULLET = style("Bullet", fontSize=8.5, leftIndent=12, leading=11.5)
S_SUMMARY = style("Summary", fontSize=8.5, leading=12)
S_SKILL_L = style("SkillL", fontSize=8.5, fontName="Helvetica-Bold")
S_SKILL_V = style("SkillV", fontSize=8.5, textColor=GRAY)
S_PROJDESC = style("ProjDesc", fontSize=8.5, leading=11.5, spaceAfter=1)


def divider(before=3, after=2):
    return HRFlowable(width="100%", thickness=0.5, color=DIVIDER,
                      spaceBefore=before, spaceAfter=after)


def section_header(text):
    table = Table([[Paragraph(text, S_SECTION)]], colWidths=[PAGE_W], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return table


def job_header(title, company, duration):
    table = Table(
        [[Paragraph(escape(title), S_JOBTITLE), Paragraph(escape(duration), S_DATE)]],
        colWidths=[PAGE_W * 0.68, PAGE_W * 0.32],
        hAlign="LEFT",
    )
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return [table, Paragraph(escape(company), S_COMPANY)]


def bullets(items):
    return [Paragraph(f"• {escape(item)}", S_BULLET) for item in items]


story = []

# Header
story.append(Paragraph(escape(PROFILE["name"]), S_NAME))
story.append(Paragraph(escape(RESUME["headline"].replace(" | ", "  |  ")), S_HEADLINE))
story.append(Paragraph(contact_line(PROFILE), S_CONTACT))
story.append(HRFlowable(width="100%", thickness=1, color=BLACK, spaceBefore=6, spaceAfter=0))

# Summary
story.append(section_header("SUMMARY"))
story.append(Paragraph(escape(RESUME["summary"]), S_SUMMARY))

# Skills
story.append(divider())
story.append(section_header("SKILLS"))
skills = [(item["label"], ", ".join(item["items"])) for item in RESUME["skills"]]
for label, value in skills:
    row = Table(
        [[Paragraph(escape(label) + ":", S_SKILL_L), Paragraph(escape(value), S_SKILL_V)]],
        colWidths=[1.05 * inch, PAGE_W - 1.05 * inch],
        hAlign="LEFT",
    )
    row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(row)

# Experience
story.append(divider())
story.append(section_header("EXPERIENCE"))
jobs = [(job["title"], job["company"], job["dates"], job["bullets"]) for job in RESUME["experience"]]
for index, (title, company, duration, job_bullets) in enumerate(jobs):
    story.extend(job_header(title, company, duration))
    story.extend(bullets(job_bullets))
    if index < len(jobs) - 1:
        story.append(Spacer(1, 3))

# Projects
projects = [
    (project["title"], project_subtitle(project), project["description"], project["bullets"])
    for project in RESUME["projects"]
]
for index, (title, subtitle, description, project_bullets) in enumerate(projects):
    project_header = [
        Paragraph(escape(title), S_JOBTITLE),
        Paragraph(escape(subtitle), S_COMPANY),
        Paragraph(escape(description), S_PROJDESC),
    ]
    project_bullet_flowables = bullets(project_bullets)
    if index == 0:
        project_header = [divider(), section_header("PROJECTS"), *project_header]
    story.append(KeepTogether(project_header + project_bullet_flowables[:1]))
    story.extend(project_bullet_flowables[1:])
    if index < len(projects) - 1:
        story.append(Spacer(1, 3))

# Education
story.append(divider())
story.append(section_header("EDUCATION"))
education = Table(
    [[Paragraph(escape(item["degree"]), S_JOBTITLE), Paragraph(escape(item["year"]), S_DATE)] for item in EDUCATION],
    colWidths=[PAGE_W * 0.68, PAGE_W * 0.32],
    hAlign="LEFT",
)
education.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ("TOPPADDING", (0, 0), (-1, -1), 0),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
]))
story.append(education)

doc.build(story)
print("Done:", OUTPUT)
