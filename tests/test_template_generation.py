import json
import os
import subprocess
import sys
from pathlib import Path

import fitz
import pytest

from resume_templates import generate_template, template_options
from tests.support import sample_resume_data


PROJECT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_BY_VARIANT = {
    "frontend": "resume_frontend.py",
    "fullstack": "resume_fullstack.py",
    "fullstack_frontend_lead": "resume_fullstack_light_backend.py",
    "customer_relations": "resume_customer_relations.py",
}


@pytest.mark.parametrize(
    ("variant_id", "script_name"),
    SCRIPT_BY_VARIANT.items(),
)
@pytest.mark.parametrize("layout_id", template_options().values())
def test_every_resume_variant_and_layout_generates_a_readable_pdf(
    tmp_path, variant_id, script_name, layout_id
):
    data = sample_resume_data()
    data_path = tmp_path / "sample_resume.json"
    data_path.write_text(json.dumps(data), encoding="utf-8")
    output_dir = tmp_path / variant_id / layout_id
    output_dir.mkdir(parents=True)

    environment = os.environ.copy()
    environment["RESUME_DATA_PATH"] = str(data_path)
    environment["RESUME_OUTPUT_DIR"] = str(output_dir)
    environment["RESUME_TEMPLATE_ID"] = layout_id
    result = subprocess.run(
        [sys.executable, str(PROJECT_DIR / script_name)],
        cwd=PROJECT_DIR,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    generated_pdfs = list(output_dir.glob("*.pdf"))
    assert len(generated_pdfs) == 1
    with fitz.open(generated_pdfs[0]) as document:
        assert len(document) >= 1
        text = "\n".join(page.get_text() for page in document)
    assert "Sample Candidate" in text
    expected_content = (
        data["variants"][variant_id]["objective"]
        if variant_id == "customer_relations"
        else data["variants"][variant_id]["headline"].split("|")[0].strip()
    )
    assert expected_content in text


def test_template_registry_dispatches_known_layouts_and_rejects_unknown():
    options = template_options()
    assert options["Classic (current)"] == "classic"
    assert options["ATS-Friendly"] == "ats"
    assert len(options) == len(set(options))

    with pytest.raises(ValueError, match="Unknown resume template"):
        generate_template("not-a-template", {}, [], {}, "frontend", Path("unused.pdf"))
