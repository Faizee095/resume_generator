alter table public.saved_resumes
    drop constraint if exists saved_resumes_variant_id_check;

alter table public.saved_resumes
    add constraint saved_resumes_variant_id_check
    check (variant_id in ('frontend', 'fullstack', 'fullstack_frontend_lead', 'customer_relations'));

alter table public.resume_pdf_downloads
    drop constraint if exists resume_pdf_downloads_variant_id_check;

alter table public.resume_pdf_downloads
    add constraint resume_pdf_downloads_variant_id_check
    check (variant_id in ('frontend', 'fullstack', 'fullstack_frontend_lead', 'customer_relations'));
