from resume_layouts import generate_alternative_pdf


TEMPLATE_ID = "elegant"
TEMPLATE_LABEL = "Elegant"
TEMPLATE_ORDER = 20


def render_pdf(profile, education, resume, variant_id, output_path):
    generate_alternative_pdf(profile, education, resume, variant_id, TEMPLATE_ID, output_path)
