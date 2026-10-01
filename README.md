# Resume Generator

The project generates three PDF resumes from the editable defaults in `resume_data.json`:

- Frontend: `resume_frontend.py`
- Full Stack: `resume_fullstack.py`
- Full Stack (Frontend Lead): `resume_fullstack_light_backend.py`

## Setup

Create and activate the project environment, then install the app and PDF dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Open the Local Editor

Start the local web app:

```powershell
streamlit run app.py
```

The editor opens at `http://localhost:8501` by default.

Choose a resume version, then select **Default data** to generate its default PDF or **Customize** to edit a custom draft and generate a customized PDF. Use **Save draft** to keep edits in the local, Git-ignored `resume_custom.json` across app restarts. The editor never changes `resume_data.json`; **Reset custom draft** removes the saved custom copy and reloads the defaults after confirmation.

The custom draft is stored as a local JSON file without encryption. Keep the editor on your own computer until authentication and deployment protections are added.

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

The command-line generators use these defaults directly. The local editor provides the same defaults and customized PDF generation through the browser.
