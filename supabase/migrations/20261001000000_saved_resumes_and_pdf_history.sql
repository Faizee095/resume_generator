create table if not exists public.saved_resumes (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id) on delete cascade,
    name text not null check (char_length(trim(name)) between 1 and 120),
    variant_id text not null check (variant_id in ('frontend', 'fullstack', 'fullstack_frontend_lead')),
    data jsonb not null check (jsonb_typeof(data) = 'object'),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists saved_resumes_user_updated_idx
    on public.saved_resumes (user_id, updated_at desc);

alter table public.saved_resumes enable row level security;
revoke all on table public.saved_resumes from anon;
grant select, insert, update, delete on table public.saved_resumes to authenticated;

drop policy if exists saved_resumes_owner_all on public.saved_resumes;
create policy saved_resumes_owner_all
    on public.saved_resumes
    for all
    to authenticated
    using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);

insert into public.saved_resumes (user_id, name, variant_id, data, created_at, updated_at)
select legacy.user_id, 'Imported custom draft', 'frontend', legacy.data, legacy.updated_at, legacy.updated_at
from public.resume_drafts as legacy
where not exists (
    select 1
    from public.saved_resumes as saved
    where saved.user_id = legacy.user_id
      and saved.data = legacy.data
);

create table if not exists public.resume_pdf_downloads (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id) on delete cascade,
    saved_resume_id uuid references public.saved_resumes (id) on delete set null,
    resume_name text not null,
    variant_id text not null check (variant_id in ('frontend', 'fullstack', 'fullstack_frontend_lead')),
    filename text not null,
    storage_path text not null unique,
    download_requested_at timestamptz not null default now()
);

create index if not exists resume_pdf_downloads_user_date_idx
    on public.resume_pdf_downloads (user_id, download_requested_at desc);

alter table public.resume_pdf_downloads enable row level security;
revoke all on table public.resume_pdf_downloads from anon;
grant select, insert, delete on table public.resume_pdf_downloads to authenticated;

drop policy if exists resume_pdf_downloads_owner_all on public.resume_pdf_downloads;
create policy resume_pdf_downloads_owner_all
    on public.resume_pdf_downloads
    for all
    to authenticated
    using ((select auth.uid()) = user_id)
    with check ((select auth.uid()) = user_id);

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('resume-pdfs', 'resume-pdfs', false, 10485760, array['application/pdf'])
on conflict (id) do update
set public = false,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists resume_pdfs_owner_read on storage.objects;
create policy resume_pdfs_owner_read
    on storage.objects
    for select
    to authenticated
    using (
        bucket_id = 'resume-pdfs'
        and (storage.foldername(name))[1] = (select auth.uid())::text
    );

drop policy if exists resume_pdfs_owner_insert on storage.objects;
create policy resume_pdfs_owner_insert
    on storage.objects
    for insert
    to authenticated
    with check (
        bucket_id = 'resume-pdfs'
        and (storage.foldername(name))[1] = (select auth.uid())::text
    );

drop policy if exists resume_pdfs_owner_delete on storage.objects;
create policy resume_pdfs_owner_delete
    on storage.objects
    for delete
    to authenticated
    using (
        bucket_id = 'resume-pdfs'
        and (storage.foldername(name))[1] = (select auth.uid())::text
    );
