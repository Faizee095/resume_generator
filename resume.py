from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

OUTPUT = "E:\\Personal\\Projects\\resume_generator\\Faiyazuddin_Resume.pdf"

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=letter,
    leftMargin=0.60*inch,
    rightMargin=0.60*inch,
    topMargin=0.45*inch,
    bottomMargin=0.45*inch,
)

PAGE_W = letter[0] - 1.20*inch

BLACK      = colors.HexColor("#1a1a1a")
GRAY       = colors.HexColor("#444444")
LIGHT_GRAY = colors.HexColor("#888888")
DIVIDER    = colors.HexColor("#cccccc")

def style(name, **kw):
    defaults = dict(fontName="Helvetica", fontSize=9, textColor=BLACK,
                    leading=13, spaceBefore=0, spaceAfter=0)
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

S_NAME     = style("Name",    fontSize=16, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=20, spaceAfter=2)
S_CONTACT  = style("Contact", fontSize=8.0, textColor=GRAY, alignment=TA_CENTER, spaceAfter=0)
S_SECTION  = style("Section", fontSize=8.8,fontName="Helvetica-Bold", leftIndent=0)
S_JOBTITLE = style("JobTitle",fontSize=9.2,fontName="Helvetica-Bold", spaceAfter=0, leftIndent=0)
S_COMPANY  = style("Company", fontSize=8.8,textColor=GRAY, spaceAfter=1, leftIndent=0)
S_DATE     = style("Date",    fontSize=8.2,textColor=LIGHT_GRAY, alignment=TA_RIGHT)
S_BULLET   = style("Bullet",  fontSize=8.5,leftIndent=12, spaceAfter=0, leading=11.5)
S_SUMMARY  = style("Summary", fontSize=8.5,leading=12, spaceAfter=0, leftIndent=0)
S_SKILL_L  = style("SkillL",  fontSize=8.5,fontName="Helvetica-Bold", leftIndent=0)
S_SKILL_V  = style("SkillV",  fontSize=8.5,textColor=GRAY, leftIndent=0)
S_PROJDESC = style("ProjDesc",fontSize=8.5,leading=11.5, spaceAfter=1, leftIndent=0)

def divider(before=3, after=2):
    return HRFlowable(width="100%", thickness=0.5, color=DIVIDER,
                      spaceBefore=before, spaceAfter=after)

def section_header(text):
    tbl = Table([[Paragraph(text, S_SECTION)]], colWidths=[PAGE_W], hAlign='LEFT')
    tbl.setStyle(TableStyle([
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
    ]))
    return tbl

def job_header(title, company, duration):
    tbl = Table(
        [[Paragraph(title, S_JOBTITLE), Paragraph(duration, S_DATE)]],
        colWidths=[PAGE_W * 0.68, PAGE_W * 0.32],
        hAlign='LEFT'
    )
    tbl.setStyle(TableStyle([
        ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
        ("TOPPADDING",    (0,0),(-1,-1), 0),
        ("BOTTOMPADDING", (0,0),(-1,-1), 0),
    ]))
    return [tbl, Paragraph(company, S_COMPANY)]

def bullets(items):
    return [Paragraph(f"• {b}", S_BULLET) for b in items]

story = []

# Header
story.append(Paragraph("Md Faiyazuddin Siddique", S_NAME))
story.append(Paragraph(
    'Muzaffarpur, India  |  faiyazsiddique9@gmail.com  |  +91-8709442967  '
    '|  <link href="https://faiyazuddin.netlify.app/" color="#2563eb">Portfolio</link>  '
    '|  <link href="https://linkedin.com/in/md-faiyazuddin-siddique" color="#2563eb">LinkedIn</link>  '
    '|  <link href="https://github.com/Faizee095" color="#2563eb">GitHub</link>',
    S_CONTACT
))
story.append(HRFlowable(width="100%", thickness=1, color=BLACK, spaceBefore=6, spaceAfter=0))

# Summary
story.append(section_header("SUMMARY"))
story.append(Paragraph(
    "Frontend-focused Software Engineer with 5+ years of experience building scalable web applications "
    "using React, Next.js, and TypeScript. Proven track record of leading frontend initiatives, improving "
    "performance, and delivering high-quality user experiences at scale.",
    S_SUMMARY
))

# Skills
story.append(divider())
story.append(section_header("SKILLS"))

skills = [
    ("Languages",  "JavaScript, TypeScript"),
    ("Frontend",   "React.js, Next.js, Redux"),
    ("UI",         "Material-UI (MUI), Tailwind CSS, HTML, CSS"),
    ("APIs",       "REST, GraphQL"),
    ("Tools",      "Git, Jira, Figma, Firebase, Auth0, Supabase"),
    ("Databases",  "MongoDB, MySQL, ElasticSearch"),
]
for label, val in skills:
    row = Table(
        [[Paragraph(label + ":", S_SKILL_L), Paragraph(val, S_SKILL_V)]],
        colWidths=[1.05*inch, PAGE_W - 1.05*inch],
        hAlign='LEFT'
    )
    row.setStyle(TableStyle([
        ("VALIGN",        (0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
        ("TOPPADDING",    (0,0),(-1,-1), 1),
        ("BOTTOMPADDING", (0,0),(-1,-1), 1),
    ]))
    story.append(row)
story.append(divider())
story.append(section_header("EXPERIENCE"))

jobs = [
    ("Software Engineer",           "SourceFuse",             "Feb 2025 – Present",
     ["Led frontend architecture for AI-driven applications using React + TypeScript, improving scalability by ~40%",
      "Built reusable component systems, reducing feature development time by 30%+",
      "Implemented authentication and session management, reducing redundant API calls by 25%",
      "Collaborated with cross-functional teams to deliver production-ready features with 99%+ uptime"]),
    ("Software Engineer",           "Kfaqs Infotech Pvt Ltd", "Feb 2022 – Sep 2024",
     ["Developed and maintained 5+ production web applications using React and Redux",
      "Integrated REST & GraphQL APIs, reducing data-fetch latency by 20–30%",
      "Delivered pixel-perfect UI from Figma, improving user engagement and consistency",
      "Optimized performance via lazy loading & code splitting, improving page load speed by 35%",
      "Resolved critical bugs and reduced production issues by 40%"]),
    ("Associate Software Engineer", "TCS",                    "Jan 2021 – Feb 2022",
     ["Built XML/XSL-based validation systems for banking workflows handling high-volume transactions",
      "Automated scripts and APIs, reducing manual effort by 30%",
      "Contributed to frontend modules using React, improving UI responsiveness"]),
]

for i, (title, company, duration, blist) in enumerate(jobs):
    story.extend(job_header(title, company, duration))
    story.extend(bullets(blist))
    if i < len(jobs) - 1:
        story.append(Spacer(1, 3))

# Projects
story.append(divider())
story.append(section_header("PROJECTS"))

projects = [
    ("AI Chat Platform",       "Rakuten  ·  React.js, TypeScript, Material-UI, Python",
     "Built a production-grade AI chat system from scratch for real-time conversational workflows.",
     ["Designed modular frontend architecture, improving code reusability by 40%",
      "Replaced legacy APIs with session-based architecture, reducing API calls by 25%",
      "Migrated styling to MUI theme system, reducing UI inconsistencies"]),
    ("Topia Web App",          "Frontend Lead  ·  React.js, TypeScript, Material-UI, MonoUI",
     "Led frontend modernization, improving UI consistency across modules by 50%.",
     ["Developed reusable components, reducing duplication by 30%",
      "Mentored team members, improving delivery efficiency and reducing rework"]),
    ("Nuvama Web App",         "Frontend Lead  ·  React, TypeScript, Material-UI",
     "Led migration from legacy .NET WebForms to React, improving performance by ~40%.",
     ["Improved page responsiveness and user experience across key workflows",
      "Established frontend best practices, reducing technical debt significantly"]),
    ("Carbon Emission Tracker","React, GraphQL, TypeScript",
     "Scalable dashboard handling large datasets with GraphQL.",
     ["Optimized rendering and state management, improving performance by 30%+",
      "Implemented predictive insights improving usability and decision-making"]),
]

for i, (title, sub, desc, blist) in enumerate(projects):
    story.append(Paragraph(title, S_JOBTITLE))
    story.append(Paragraph(sub, S_COMPANY))
    story.append(Paragraph(desc, S_PROJDESC))
    story.extend(bullets(blist))
    if i < len(projects) - 1:
        story.append(Spacer(1, 3))

# Education
story.append(divider())
story.append(section_header("EDUCATION"))

edu = Table(
    [[Paragraph("B.Tech in Computer Science", S_JOBTITLE), Paragraph("2020", S_DATE)]],
    colWidths=[PAGE_W * 0.68, PAGE_W * 0.32],
    hAlign='LEFT'
)
edu.setStyle(TableStyle([
    ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
    ("LEFTPADDING",   (0,0),(-1,-1), 0),
    ("RIGHTPADDING",  (0,0),(-1,-1), 0),
    ("TOPPADDING",    (0,0),(-1,-1), 0),
    ("BOTTOMPADDING", (0,0),(-1,-1), 0),
]))
story.append(edu)

story.append(divider())
story.append(section_header("STRENGTHS"))
strengths = [
    "Strong ownership mindset (proven in Rakuten project leadership)",
    "Ability to lead frontend architecture and mentor developers",
    "Focus on clean code, scalability, and performance",
    "Excellent collaboration with design and backend teams",
]
story.extend(bullets(strengths))

doc.build(story)
print("Done:", OUTPUT)
