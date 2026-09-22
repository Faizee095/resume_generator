from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, KeepTogether
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

today = datetime.now()
day_suffix = "th" if 10 < today.day % 100 < 14 else {1: "st", 2: "nd", 3: "rd"}.get(today.day % 10, "th")
date_label = f"{today.day}{day_suffix}{today.strftime('%B%Y')}"
OUTPUT = f"E:\\Personal\\Projects\\resume_generator\\Faiyazuddin_FrontEnd Developer_{date_label}.pdf"

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
S_HEADLINE = style("Headline", fontSize=9.2, fontName="Helvetica-Bold", textColor=GRAY, alignment=TA_CENTER, leading=12, spaceAfter=2)
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
    "Frontend Engineer  |  React  |  TypeScript  |  Next.js  |  Frontend Architecture",
    S_HEADLINE
))
story.append(Paragraph(
    'Muzaffarpur, India  |  faiyazsiddique9@gmail.com  |  +91-8709442967  '
    '|  <link href="https://faiyazuddin.netlify.app/" color="#2563eb">Portfolio</link>  '
    '|  <link href="https://www.linkedin.com/in/md-faiyazuddin-siddique-244a73192/" color="#2563eb">LinkedIn</link>  '
    '|  <link href="https://github.com/Faizee095" color="#2563eb">GitHub</link>',
    S_CONTACT
))
story.append(HRFlowable(width="100%", thickness=1, color=BLACK, spaceBefore=6, spaceAfter=0))

# Summary
story.append(section_header("SUMMARY"))
story.append(Paragraph(
    "Frontend Engineer with 5+ years of experience building and leading production React and TypeScript applications. "
    "Strong in frontend architecture, reusable component systems, performance optimization, and large-scale migrations "
    "from legacy platforms. Experienced in mentoring junior developers and collaborating with design and backend teams "
    "to deliver scalable, maintainable user experiences.",
    S_SUMMARY
))

# Skills
story.append(divider())
story.append(section_header("SKILLS"))

skills = [
    ("Core",       "React.js, TypeScript, Next.js, Redux, TanStack Query, Frontend Architecture"),
    ("UI",         "Tailwind CSS, Material-UI (MUI), HTML, CSS, Responsive Design, Accessibility (a11y)"),
    ("Engineering", "Reusable Component Systems, Performance Optimization, Code Splitting, Testing (Jest)"),
    ("Data & APIs", "REST, GraphQL, Charting Libraries, Table Libraries"),
    ("Auth & Tools", "Authentication, Authorization, Session Management, Git, Jira, Figma, Auth0"),
    ("Additional", "JavaScript, Firebase, Supabase, MongoDB, MySQL, ElasticSearch"),
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
    ("Software Engineer",           "SourceFuse",             "Feb 2025 – Jun 2026",
    ['Led frontend architecture for AI-driven applications using React + TypeScript, enabling scalable production systems',
        'Designed and implemented reusable component systems that improved consistency and speed of feature development',
          'Led frontend modernization from legacy systems to React-based architecture across multiple projects',
                'Optimized authentication and session management to reduce redundant API calls and improve user experience',
                    'Established frontend best practices, architectural guidelines, and collaboration patterns for production-scale delivery']),
    ("Career Break",               "Personal / Family Responsibilities", "Oct 2024 – Jan 2025",
     ["Took a planned career break to manage family responsibilities before returning to software engineering"]),
    ("Software Engineer",           "Kfaqs Infotech Pvt Ltd", "Feb 2022 – Sep 2024",
      [ 'Built and maintained 5+ production web applications using React and Redux',
          'Integrated REST and GraphQL APIs across multiple production applications',
          'Improved application performance through lazy loading, code splitting, and frontend optimization techniques',
          'Strengthened application stability through proactive debugging and issue resolution',]),
    ("Associate Software Engineer", "TCS",                    "Jan 2021 – Feb 2022",
     ["Built XML/XSL-based validation systems for banking workflows handling high-volume transactions",
            "Automated scripts and APIs to simplify recurring banking workflow tasks",
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
    ("AI Chat Platform",       "Rakuten  ·  Frontend Lead (1 junior developer)  ·  React.js, TypeScript, Tailwind CSS, TanStack Query, Charting and Table Libraries, Python",
     "Led frontend development with one junior developer for an AI-powered reporting platform that helps users generate insights faster than manually reviewing large sets of reports.",
     ["Designed a response-driven React component architecture that renders tables, charts, SQL results, and PDF newsletters based on backend responses",
      "Built authentication, authorization, and session management with frontend token handling for secure user workflows",
      "Implemented a real-time session sidebar supporting session creation, renaming, deletion, and switching across concurrent users",
    "Developed the interface using React, TypeScript, Tailwind CSS, TanStack Query for API data fetching, and charting and table libraries"]),
        ("Topia Web App",          "Frontend Lead (team of 3, incl. 2 junior developers)  ·  React.js, TypeScript, Redux, Tailwind CSS, TanStack Query",
         "Led the frontend migration of a complex enterprise application from .NET to React while preserving the existing user experience and coordinating with full-stack developers migrating backend services to Java.",
         ["Led a frontend team of three developers, including two junior developers, and coordinated implementation across interconnected application modules",
            "Decomposed the legacy application into independently deliverable React components and defined an incremental migration architecture",
            "Recreated existing workflows and designs in React using Redux, Tailwind CSS, and TanStack Query for API data fetching",
            "Integrated third-party authentication and authorization while coordinating frontend changes with backend API migration"]),
        ("Nuvama Web App",         "Frontend Lead  ·  React, TypeScript, Material-UI, Redux, GraphQL",
         "Led the migration of a complex .NET web application to React by analyzing the legacy architecture, mapping interconnected components, and defining an incremental frontend delivery plan.",
         ["Worked with one junior developer, providing technical guidance and training throughout the migration",
            "Owned frontend migration planning, ticket breakdown, and sprint execution across the identified component areas",
            "Rebuilt legacy workflows with React, Material-UI, Redux, and GraphQL while maintaining consistent user experiences",
            "Established reusable component patterns and frontend implementation standards for the migrated application"]),
    ("Carbon Emission Tracker","React, GraphQL, TypeScript  ·  Enterprise emissions dashboard",
         "Built a carbon accounting platform for enterprise customers to calculate emissions from vehicles, machines, factories, and other operational inputs against regulatory thresholds.",
         ["Developed a dashboard with interactive charts, data visualizations, and tables for reviewing categorized emission data",
            "Implemented Excel upload and categorization workflows for industry data such as food production, vehicles, and manufacturing",
            "Supported long-running report generation for large datasets with a real-time progress timer powered by GraphQL subscriptions",
            "Added Jest component tests and accessibility improvements as part of the frontend quality and delivery standards"]),
]

for i, (title, sub, desc, blist) in enumerate(projects):
    project_content = [
        Paragraph(title, S_JOBTITLE),
        Paragraph(sub, S_COMPANY),
        Paragraph(desc, S_PROJDESC),
        *bullets(blist),
    ]
    story.append(KeepTogether(project_content))
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

doc.build(story)
print("Done:", OUTPUT)
