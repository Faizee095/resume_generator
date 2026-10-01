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

The editor opens at `http://localhost:8501` by default. Local mode needs no Supabase account and stores its single custom draft in the ignored `resume_custom.json` file.

Choose a resume version, then select **Default data** to generate its default PDF or **Customize** to edit a custom draft and generate a customized PDF. Use **Save draft** to keep edits in the local, Git-ignored `resume_custom.json` across app restarts. The editor never changes `resume_data.json`; **Reset custom draft** removes the saved custom copy and reloads the defaults after confirmation.

Local custom drafts are stored as JSON without encryption. Keep local mode on your own computer.

## Supabase and Render

Hosted mode uses Supabase Auth and private Postgres JSONB records for named saved resumes. The **Saved drafts** workspace lets the user open, update, save as a new copy, generate a PDF, or delete a draft. Legacy single-draft data is imported by the migration. If a local draft file exists and the account has no cloud draft yet, the editor offers a confirmed import and keeps the local file as a backup.

PDFs are uploaded to the private `resume-pdfs` Storage bucket when the user clicks a PDF download button. The **PDF downloads** workspace lists those requests and lets the user retrieve the archived PDF again. The app can record the download request, but cannot confirm that the browser completed saving the file. Deleting a saved resume does not delete its PDF history.

1. For the existing Supabase project, run `supabase/migrations/20261001000000_saved_resumes_and_pdf_history.sql` in its SQL Editor. For a new Supabase project, run `supabase/schema.sql` instead.
2. In Supabase Auth, disable public sign-ups and create/invite the account you will use. The app also checks the account against `ALLOWED_EMAILS`.
3. Create a Render web service from this repository using `render.yaml`.
4. In the Render service environment, set `SUPABASE_URL`, `SUPABASE_KEY`, and `ALLOWED_EMAILS`. Use the Supabase publishable key or legacy anon key for `SUPABASE_KEY`; never use the `service_role` key.
5. Deploy the service and open its Render URL. Only allowlisted accounts can sign in; row-level security restricts draft access to the authenticated user's own row.

Render's blueprint marks these values as secrets and prompts for them during setup. Do not put real credentials in `.env.example`, source code, or Git. The app detects Render and forces Supabase mode even if `PERSISTENCE_MODE` is missing or accidentally set to `local`; it shows a configuration error rather than exposing resume data when Supabase settings are missing. Outside Render, it defaults to local mode unless `PERSISTENCE_MODE=supabase` is set.

Keep the Git repository private because `resume_data.json` contains personal resume details. Render's URL is internet-reachable, but the app requires an allowlisted Supabase login before showing resume data.

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
