# Resume Generator

The project generates three PDF resumes from the editable defaults in `resume_data.json`:

- Frontend: `resume_frontend.py`
- Full Stack: `resume_fullstack.py`
- Full Stack (Frontend Lead): `resume_fullstack_light_backend.py`

## Setup

Install the PDF dependency:

```powershell
python -m pip install reportlab
```

## Generate PDFs

Run the generator for the version you need:

```powershell
python resume_frontend.py
python resume_fullstack.py
python resume_fullstack_light_backend.py
```

Each script writes a dated PDF into this project directory. The scripts can also be run independently; they all read `resume_data.json` through `resume_data.py`.

## Edit Default Resume Data

Edit `resume_data.json` to update the defaults used by the generators:

- `profile` contains name and contact information shared by all variants.
- `education` contains shared education entries.
- `variants.frontend`, `variants.fullstack`, and `variants.fullstack_frontend_lead` each contain a headline, summary, skill groups, experience, and projects.
- Experience and project bullets are arrays. Project organization, role, team, technologies, description, and bullets are separate fields.
- `output_name` controls the generated PDF filename prefix for a variant.

The current generators use these defaults directly. A browser-based editor and customized-data workflow have not been added yet.
