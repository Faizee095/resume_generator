from resume_layouts import generate_alternative_pdf


TEMPLATE_ID = "compact"
TEMPLATE_LABEL = "Compact"
TEMPLATE_ORDER = 30


def render_pdf(profile, education, resume, variant_id, output_path):
    generate_alternative_pdf(profile, education, resume, variant_id, TEMPLATE_ID, output_path)
