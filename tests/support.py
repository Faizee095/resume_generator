import copy


def sample_resume_data():
    experience = [
        {
            "title": "Software Engineer",
            "company": "Example Studio",
            "dates": "2022 - Present",
            "bullets": [
                "Built accessible features used by customer support teams.",
                "Improved page load time by 30 percent.",
            ],
        }
    ]
    projects = [
        {
            "title": "Project Atlas",
            "organization": "Example Studio",
            "role": "Developer",
            "team": "4 contributors",
            "technologies": ["Python", "TypeScript"],
            "context": "Internal platform",
            "description": "A workflow dashboard for coordinating service requests.",
            "bullets": ["Designed reusable components and automated checks."],
        }
    ]
    profile = {
        "name": "Sample Candidate",
        "location": "Example City",
        "email": "candidate@example.test",
        "phone": "555-0100",
        "links": [{"label": "Portfolio", "url": "https://example.test/portfolio"}],
    }

    variants = {}
    for variant_id, label, headline in (
        ("frontend", "Frontend Developer", "Frontend Engineer | React | TypeScript"),
        ("fullstack", "Full Stack Developer", "Full Stack Developer | Frontend | APIs"),
        (
            "fullstack_frontend_lead",
            "Full Stack Developer (Frontend Lead)",
            "Full Stack Developer | Frontend Lead",
        ),
    ):
        variants[variant_id] = {
            "label": label,
            "output_name": f"Sample_{variant_id}",
            "headline": headline,
            "summary": "Engineer focused on reliable, accessible web applications.",
            "skills": [
                {"label": "Languages", "items": ["Python", "TypeScript"]},
                {"label": "Tools", "items": ["React", "PostgreSQL"]},
            ],
            "experience": copy.deepcopy(experience),
            "projects": copy.deepcopy(projects),
        }

    variants["customer_relations"] = {
        "label": "Customer Relations",
        "output_name": "Sample_Customer_Relations",
        "headline": "Customer Relations Specialist",
        "objective": "Customer-focused professional experienced in service operations.",
        "skills": ["Customer service", "Issue resolution", "Communication"],
        "experience": [
            {
                "title": "Customer Relations Associate",
                "company": "Example Services",
                "dates": "2021 - Present",
                "bullets": [],
            }
        ],
        "projects": [],
        "achievements": ["Recognized for clear and timely customer support."],
    }

    return {
        "schema_version": 1,
        "profile": profile,
        "education": [
            {
                "school": "Example University",
                "degree": "Bachelor of Science",
                "year": "2021",
                "score": "Honors",
            }
        ],
        "variants": variants,
    }
