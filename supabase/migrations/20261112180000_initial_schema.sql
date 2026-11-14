-- Skill Bridge initial Supabase schema.
-- Run once in the Supabase SQL Editor only after reviewing this file.
-- This migration creates schema objects only; it does not import JSON data.
-- It contains no DROP, TRUNCATE, or data-deletion statements. The DDL is wrapped
-- in one transaction. If it fails before COMMIT, verify that it rolled back
-- before rerunning the complete migration. If COMMIT succeeded, do not rerun it.
-- Back up the existing JSON files before a later data import, and retain them
-- until migrated rows and relationships have been verified.
-- Import jobs with their original text IDs, then run the sequence-sync function
-- below (SELECT public.sync_job_id_seq()) before allowing the application to
-- create jobs.
-- Sample candidates use profiles.legacy_id (for example c1), separate from
-- authenticated users. Set recruitment_visible only for demo profiles or users
-- who have explicitly consented to recruiter discovery.
-- Before importing JSON, make separate backups of jobs.json, decisions.json,
-- company.json, candidates.json, and any student/tracker data still available.
-- This file does not import JSON. Do not retry a partially completed import
-- with blind INSERTs; reconcile the rows against the backups first.
-- Map candidate JSON id/name/project/github to legacy_id/name/projects/links,
-- and map each skills string to student_skills with its level if known (otherwise
-- Beginner). Map existing decision keys to the corresponding profile UUID and
-- preserve each job's original text ID.
-- The current student and tracker APIs keep records only in Python memory;
-- records lost when that process stopped cannot be recovered from this schema.
-- Existing jobs/company files do not reliably identify an authenticated owner.
-- Assign company_id only after independently verifying the recruiter ownership.
-- All profile/job history foreign keys use RESTRICT: account, company, job, or
-- candidate deletion is blocked while it has dependent history. The current
-- recruiter UI has no submitted-applications inbox; applications below are the
-- student's private tracker, so there is deliberately no recruiter read policy.
-- Signup may include raw_user_meta_data.requested_role = 'recruiter'. This is
-- recorded only as a request; it never grants recruiter permissions. The
-- existing role selector may also send raw_user_meta_data.role = 'recruiter';
-- that value is treated only as the same untrusted request. After independently
-- verifying the person, a trusted project admin can approve:
-- UPDATE public.profiles
-- SET role = 'recruiter', requested_role = NULL
-- WHERE auth_user_id = '<verified auth.users UUID>'
--   AND role = 'student' AND requested_role = 'recruiter' AND NOT is_demo;

BEGIN;

CREATE SCHEMA IF NOT EXISTS private;
REVOKE ALL ON SCHEMA private FROM PUBLIC, anon, authenticated;
GRANT USAGE ON SCHEMA private TO authenticated;
GRANT USAGE ON SCHEMA public TO authenticated;

CREATE SEQUENCE public.job_id_seq AS bigint START WITH 1 INCREMENT BY 1;
REVOKE ALL ON SEQUENCE public.job_id_seq FROM PUBLIC, anon, authenticated;

CREATE TABLE public.profiles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id uuid UNIQUE REFERENCES auth.users (id) ON DELETE RESTRICT,
    legacy_id text UNIQUE,
    is_demo boolean NOT NULL DEFAULT false,
    role text NOT NULL CHECK (role IN ('student', 'recruiter')),
    requested_role text CHECK (
        requested_role IS NULL OR requested_role = 'recruiter'
    ),
    email text,
    name text NOT NULL DEFAULT '',
    college text,
    course text,
    year text,
    graduation_year text,
    cv_name text,
    links jsonb NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(links) = 'object'),
    preferences jsonb NOT NULL DEFAULT '{}'::jsonb
        CHECK (jsonb_typeof(preferences) = 'object'),
    completed boolean NOT NULL DEFAULT false,
    recruitment_visible boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT profiles_auth_or_demo_check CHECK (
        (is_demo AND auth_user_id IS NULL AND role = 'student' AND legacy_id IS NOT NULL)
        OR
        (NOT is_demo AND auth_user_id IS NOT NULL AND legacy_id IS NULL)
    )
);

CREATE UNIQUE INDEX profiles_email_lower_uidx
    ON public.profiles (lower(email))
    WHERE email IS NOT NULL;

CREATE TABLE public.companies (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_profile_id uuid NOT NULL UNIQUE
        REFERENCES public.profiles (id) ON DELETE RESTRICT,
    name text NOT NULL CHECK (length(btrim(name)) > 0),
    website text NOT NULL DEFAULT '',
    location text NOT NULL DEFAULT '',
    size text NOT NULL DEFAULT '',
    about text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.jobs (
    id text PRIMARY KEY DEFAULT ('j' || nextval('public.job_id_seq'::regclass)::text),
    company_id uuid REFERENCES public.companies (id) ON DELETE RESTRICT,
    company_name text NOT NULL DEFAULT '',
    title text NOT NULL CHECK (length(btrim(title)) > 0),
    location text NOT NULL DEFAULT 'Not specified',
    type text NOT NULL DEFAULT 'Full-time'
        CHECK (type IN ('Internship', 'Full-time', 'Part-time', 'Contract')),
    remote boolean NOT NULL DEFAULT false,
    salary text NOT NULL DEFAULT '',
    posted_at date NOT NULL DEFAULT current_date,
    apply_url text NOT NULL DEFAULT '',
    source text NOT NULL DEFAULT 'recruiter'
        CHECK (source IN ('sample', 'recruiter')),
    description text NOT NULL DEFAULT '',
    skills text[] NOT NULL DEFAULT '{}'::text[],
    experience text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT jobs_skills_check CHECK (
        array_position(skills, NULL) IS NULL
        AND array_position(skills, '') IS NULL
    )
);

CREATE TABLE public.student_skills (
    profile_id uuid NOT NULL
        REFERENCES public.profiles (id) ON DELETE RESTRICT,
    skill_name text NOT NULL CHECK (length(btrim(skill_name)) > 0),
    level text NOT NULL DEFAULT 'Beginner'
        CHECK (level IN ('Beginner', 'Intermediate', 'Advanced')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (profile_id, skill_name)
);

CREATE TABLE public.projects (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id uuid NOT NULL
        REFERENCES public.profiles (id) ON DELETE RESTRICT,
    title text NOT NULL CHECK (length(btrim(title)) > 0),
    description text NOT NULL DEFAULT '',
    link text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE public.applications (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_profile_id uuid NOT NULL
        REFERENCES public.profiles (id) ON DELETE RESTRICT,
    job_id text NOT NULL
        REFERENCES public.jobs (id) ON DELETE RESTRICT,
    status text NOT NULL DEFAULT 'saved'
        CHECK (status IN ('saved', 'applied', 'interview', 'offer', 'closed', 'rejected', 'no_reply')),
    notes text NOT NULL DEFAULT '',
    applied_at date,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT applications_one_per_student_job UNIQUE (student_profile_id, job_id)
);

CREATE TABLE public.candidate_decisions (
    job_id text NOT NULL
        REFERENCES public.jobs (id) ON DELETE RESTRICT,
    candidate_profile_id uuid NOT NULL
        REFERENCES public.profiles (id) ON DELETE RESTRICT,
    status text NOT NULL
        CHECK (status IN ('shortlisted', 'contacted', 'rejected')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (job_id, candidate_profile_id)
);

CREATE INDEX jobs_company_id_idx ON public.jobs (company_id);
CREATE INDEX jobs_source_posted_at_idx ON public.jobs (source, posted_at DESC);
CREATE INDEX jobs_skills_gin_idx ON public.jobs USING gin (skills);
CREATE INDEX student_skills_name_idx ON public.student_skills (lower(skill_name));
CREATE UNIQUE INDEX student_skills_profile_skill_lower_uidx
    ON public.student_skills (profile_id, lower(skill_name));
CREATE INDEX projects_profile_id_idx ON public.projects (profile_id);
CREATE INDEX applications_profile_status_idx
    ON public.applications (student_profile_id, status);
CREATE INDEX applications_job_id_idx ON public.applications (job_id);
CREATE INDEX candidate_decisions_candidate_id_idx
    ON public.candidate_decisions (candidate_profile_id);

-- Run this after importing all jobs with their preserved IDs. It advances the
-- generated jN IDs past the greatest numeric jN already present without
-- renumbering or replacing any imported job.
CREATE FUNCTION public.sync_job_id_seq()
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    highest_job_number bigint;
BEGIN
    LOCK TABLE public.jobs IN ACCESS EXCLUSIVE MODE;

    SELECT coalesce(max(substring(j.id FROM 2)::bigint), 0)
    INTO highest_job_number
    FROM public.jobs AS j
    WHERE j.id ~ '^j[0-9]+$';

    IF highest_job_number = 0 THEN
        PERFORM setval('public.job_id_seq'::regclass, 1, false);
    ELSE
        PERFORM setval(
            'public.job_id_seq'::regclass,
            highest_job_number,
            true
        );
    END IF;

    RETURN highest_job_number;
END;
$$;
REVOKE ALL ON FUNCTION public.sync_job_id_seq() FROM PUBLIC, anon, authenticated;

CREATE FUNCTION private.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER profiles_set_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION private.set_updated_at();
CREATE TRIGGER companies_set_updated_at
    BEFORE UPDATE ON public.companies
    FOR EACH ROW EXECUTE FUNCTION private.set_updated_at();
CREATE TRIGGER jobs_set_updated_at
    BEFORE UPDATE ON public.jobs
    FOR EACH ROW EXECUTE FUNCTION private.set_updated_at();
CREATE TRIGGER student_skills_set_updated_at
    BEFORE UPDATE ON public.student_skills
    FOR EACH ROW EXECUTE FUNCTION private.set_updated_at();
CREATE TRIGGER projects_set_updated_at
    BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION private.set_updated_at();
CREATE TRIGGER applications_set_updated_at
    BEFORE UPDATE ON public.applications
    FOR EACH ROW EXECUTE FUNCTION private.set_updated_at();
CREATE TRIGGER candidate_decisions_set_updated_at
    BEFORE UPDATE ON public.candidate_decisions
    FOR EACH ROW EXECUTE FUNCTION private.set_updated_at();

CREATE FUNCTION private.create_profile_for_auth_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    INSERT INTO public.profiles (
        auth_user_id, role, requested_role, email, name
    )
    VALUES (
        NEW.id,
        'student',
        CASE
            WHEN NEW.raw_user_meta_data ->> 'requested_role' = 'recruiter'
              OR NEW.raw_user_meta_data ->> 'role' = 'recruiter'
                THEN 'recruiter'
            ELSE NULL
        END,
        lower(NEW.email),
        coalesce(NEW.raw_user_meta_data ->> 'name', '')
    );
    RETURN NEW;
END;
$$;

REVOKE ALL ON FUNCTION private.create_profile_for_auth_user() FROM PUBLIC, anon, authenticated;

CREATE TRIGGER skill_bridge_create_profile
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION private.create_profile_for_auth_user();

CREATE FUNCTION private.sync_profile_email()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    UPDATE public.profiles
    SET email = lower(NEW.email)
    WHERE auth_user_id = NEW.id;
    RETURN NEW;
END;
$$;

REVOKE ALL ON FUNCTION private.sync_profile_email() FROM PUBLIC, anon, authenticated;

CREATE TRIGGER skill_bridge_sync_profile_email
    AFTER UPDATE OF email ON auth.users
    FOR EACH ROW
    WHEN (OLD.email IS DISTINCT FROM NEW.email)
    EXECUTE FUNCTION private.sync_profile_email();

CREATE FUNCTION private.current_profile_id()
RETURNS uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT p.id
    FROM public.profiles AS p
    WHERE p.auth_user_id = (SELECT auth.uid())
      AND NOT p.is_demo
    LIMIT 1
$$;

CREATE FUNCTION private.current_profile_role()
RETURNS text
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT p.role
    FROM public.profiles AS p
    WHERE p.auth_user_id = (SELECT auth.uid())
      AND NOT p.is_demo
    LIMIT 1
$$;

CREATE FUNCTION private.owns_company(target_company_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT coalesce(
        private.current_profile_role() = 'recruiter'
        AND EXISTS (
            SELECT 1
            FROM public.companies AS c
            WHERE c.id = target_company_id
              AND c.owner_profile_id = private.current_profile_id()
        ),
        false
    )
$$;

CREATE FUNCTION private.owns_job(target_job_id text)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT coalesce(
        private.current_profile_role() = 'recruiter'
        AND EXISTS (
            SELECT 1
            FROM public.jobs AS j
            JOIN public.companies AS c ON c.id = j.company_id
            WHERE j.id = target_job_id
              AND c.owner_profile_id = private.current_profile_id()
        ),
        false
    )
$$;

CREATE FUNCTION private.is_student_profile(target_profile_id uuid)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.profiles AS p
        WHERE p.id = target_profile_id
          AND p.role = 'student'
          AND p.recruitment_visible
    )
$$;

REVOKE ALL ON FUNCTION private.set_updated_at() FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION private.current_profile_id() FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION private.current_profile_role() FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION private.owns_company(uuid) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION private.owns_job(text) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION private.is_student_profile(uuid) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION private.current_profile_id() TO authenticated;
GRANT EXECUTE ON FUNCTION private.current_profile_role() TO authenticated;
GRANT EXECUTE ON FUNCTION private.owns_company(uuid) TO authenticated;
GRANT EXECUTE ON FUNCTION private.owns_job(text) TO authenticated;
GRANT EXECUTE ON FUNCTION private.is_student_profile(uuid) TO authenticated;

CREATE FUNCTION public.get_candidates_for_job(p_job_id text)
RETURNS TABLE (
    id text,
    candidate_profile_id uuid,
    name text,
    college text,
    course text,
    year text,
    graduation_year text,
    skills jsonb,
    skill_details jsonb,
    project text,
    github text,
    projects jsonb,
    links jsonb,
    "candidateType" text,
    is_demo boolean
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    IF NOT private.owns_job(p_job_id) THEN
        RAISE EXCEPTION 'Not authorized to view candidates for this job'
            USING ERRCODE = 'insufficient_privilege';
    END IF;

    RETURN QUERY
    SELECT
        coalesce(p.legacy_id, p.id::text),
        p.id,
        p.name,
        p.college,
        p.course,
        p.year,
        p.graduation_year,
        coalesce(
            (
                SELECT jsonb_agg(
                    to_jsonb(s.skill_name)
                    ORDER BY s.skill_name
                )
                FROM public.student_skills AS s
                WHERE s.profile_id = p.id
            ),
            '[]'::jsonb
        ),
        coalesce(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'name', s.skill_name,
                        'level', s.level
                    )
                    ORDER BY s.skill_name
                )
                FROM public.student_skills AS s
                WHERE s.profile_id = p.id
            ),
            '[]'::jsonb
        ),
        (
            SELECT pr.title
            FROM public.projects AS pr
            WHERE pr.profile_id = p.id
            ORDER BY pr.created_at, pr.id
            LIMIT 1
        ),
        p.links ->> 'github',
        coalesce(
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'title', pr.title,
                        'description', pr.description,
                        'link', pr.link
                    )
                    ORDER BY pr.created_at, pr.id
                )
                FROM public.projects AS pr
                WHERE pr.profile_id = p.id
            ),
            '[]'::jsonb
        ),
        jsonb_strip_nulls(
            jsonb_build_object(
                'linkedin', nullif(p.links ->> 'linkedin', ''),
                'github', nullif(p.links ->> 'github', ''),
                'portfolio', nullif(p.links ->> 'portfolio', '')
            )
        ),
        CASE WHEN p.is_demo THEN 'Sample' ELSE 'Registered' END,
        p.is_demo
    FROM public.profiles AS p
    WHERE p.role = 'student'
      AND p.recruitment_visible
    ORDER BY p.is_demo DESC, p.name;
END;
$$;

REVOKE ALL ON FUNCTION public.get_candidates_for_job(text) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.get_candidates_for_job(text) TO authenticated;

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.candidate_decisions ENABLE ROW LEVEL SECURITY;

CREATE POLICY profiles_select_own
    ON public.profiles FOR SELECT TO authenticated
    USING (auth_user_id = (SELECT auth.uid()) AND NOT is_demo);
CREATE POLICY profiles_update_own
    ON public.profiles FOR UPDATE TO authenticated
    USING (auth_user_id = (SELECT auth.uid()) AND NOT is_demo)
    WITH CHECK (auth_user_id = (SELECT auth.uid()) AND NOT is_demo);

CREATE POLICY companies_select_own
    ON public.companies FOR SELECT TO authenticated
    USING (owner_profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'recruiter');
CREATE POLICY companies_insert_own
    ON public.companies FOR INSERT TO authenticated
    WITH CHECK (owner_profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'recruiter');
CREATE POLICY companies_update_own
    ON public.companies FOR UPDATE TO authenticated
    USING (owner_profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'recruiter')
    WITH CHECK (owner_profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'recruiter');

CREATE POLICY jobs_select_authenticated
    ON public.jobs FOR SELECT TO authenticated
    USING (true);
CREATE POLICY jobs_insert_for_owned_company
    ON public.jobs FOR INSERT TO authenticated
    WITH CHECK (
        source = 'recruiter'
        AND company_id IS NOT NULL
        AND (SELECT private.owns_company(company_id))
    );
CREATE POLICY jobs_update_owned
    ON public.jobs FOR UPDATE TO authenticated
    USING ((SELECT private.owns_job(id)))
    WITH CHECK ((SELECT private.owns_job(id)) AND source = 'recruiter');
CREATE POLICY jobs_delete_owned
    ON public.jobs FOR DELETE TO authenticated
    USING ((SELECT private.owns_job(id)));

CREATE POLICY student_skills_select_own
    ON public.student_skills FOR SELECT TO authenticated
    USING (
        profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'student'
    );
CREATE POLICY student_skills_insert_own
    ON public.student_skills FOR INSERT TO authenticated
    WITH CHECK (
        profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'student'
    );
CREATE POLICY student_skills_update_own
    ON public.student_skills FOR UPDATE TO authenticated
    USING (
        profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'student'
    )
    WITH CHECK (
        profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'student'
    );
CREATE POLICY student_skills_delete_own
    ON public.student_skills FOR DELETE TO authenticated
    USING (
        profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'student'
    );

CREATE POLICY projects_select_own
    ON public.projects FOR SELECT TO authenticated
    USING (
        profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'student'
    );
CREATE POLICY projects_insert_own
    ON public.projects FOR INSERT TO authenticated
    WITH CHECK (
        profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'student'
    );
CREATE POLICY projects_update_own
    ON public.projects FOR UPDATE TO authenticated
    USING (
        profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'student'
    )
    WITH CHECK (
        profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'student'
    );
CREATE POLICY projects_delete_own
    ON public.projects FOR DELETE TO authenticated
    USING (
        profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'student'
    );

CREATE POLICY applications_select_own
    ON public.applications FOR SELECT TO authenticated
    USING (
        student_profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'student'
    );
CREATE POLICY applications_insert_own
    ON public.applications FOR INSERT TO authenticated
    WITH CHECK (
        student_profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'student'
    );
CREATE POLICY applications_update_own
    ON public.applications FOR UPDATE TO authenticated
    USING (
        student_profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'student'
    )
    WITH CHECK (
        student_profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'student'
    );
CREATE POLICY applications_delete_own
    ON public.applications FOR DELETE TO authenticated
    USING (
        student_profile_id = (SELECT private.current_profile_id())
        AND (SELECT private.current_profile_role()) = 'student'
    );

CREATE POLICY candidate_decisions_select_owned_jobs
    ON public.candidate_decisions FOR SELECT TO authenticated
    USING (
        (SELECT private.owns_job(job_id))
        AND (SELECT private.is_student_profile(candidate_profile_id))
    );
CREATE POLICY candidate_decisions_insert_owned_jobs
    ON public.candidate_decisions FOR INSERT TO authenticated
    WITH CHECK (
        (SELECT private.owns_job(job_id))
        AND (SELECT private.is_student_profile(candidate_profile_id))
    );
CREATE POLICY candidate_decisions_update_owned_jobs
    ON public.candidate_decisions FOR UPDATE TO authenticated
    USING (
        (SELECT private.owns_job(job_id))
        AND (SELECT private.is_student_profile(candidate_profile_id))
    )
    WITH CHECK (
        (SELECT private.owns_job(job_id))
        AND (SELECT private.is_student_profile(candidate_profile_id))
    );
CREATE POLICY candidate_decisions_delete_owned_jobs
    ON public.candidate_decisions FOR DELETE TO authenticated
    USING (
        (SELECT private.owns_job(job_id))
        AND (SELECT private.is_student_profile(candidate_profile_id))
    );
REVOKE ALL ON TABLE
    public.profiles,
    public.companies,
    public.jobs,
    public.student_skills,
    public.projects,
    public.applications,
    public.candidate_decisions
FROM PUBLIC, anon, authenticated;

GRANT SELECT ON public.profiles TO authenticated;
GRANT UPDATE (
    name, college, course, year, graduation_year, cv_name,
    links, preferences, completed, recruitment_visible
) ON public.profiles TO authenticated;

GRANT SELECT, INSERT, UPDATE, DELETE
    ON public.student_skills, public.projects TO authenticated;
GRANT SELECT, INSERT
    ON public.companies TO authenticated;
GRANT UPDATE (name, website, location, size, about)
    ON public.companies TO authenticated;
GRANT SELECT, DELETE
    ON public.jobs TO authenticated;
GRANT INSERT (
    company_id, company_name, title, location, type, remote, salary,
    posted_at, apply_url, description, skills, experience
) ON public.jobs TO authenticated;
GRANT UPDATE (
    company_name, title, location, type, remote, salary, posted_at,
    apply_url, description, skills, experience
) ON public.jobs TO authenticated;
GRANT SELECT, INSERT, DELETE
    ON public.applications TO authenticated;
GRANT UPDATE (status, notes, applied_at)
    ON public.applications TO authenticated;
GRANT SELECT, INSERT, DELETE
    ON public.candidate_decisions TO authenticated;
GRANT UPDATE (status) ON public.candidate_decisions TO authenticated;
GRANT USAGE ON SEQUENCE public.job_id_seq TO authenticated;

COMMIT;

-- Verification queries: run these after applying the schema in Supabase.
-- Expected: seven public tables, each with RLS enabled; policies and indexes
-- should be listed for the corresponding tables.

WITH expected_tables (table_name) AS (
    VALUES
        ('profiles'),
        ('student_skills'),
        ('projects'),
        ('companies'),
        ('jobs'),
        ('applications'),
        ('candidate_decisions')
)
SELECT
    e.table_name,
    c.oid IS NOT NULL AS table_exists,
    coalesce(c.relrowsecurity, false) AS rls_enabled
FROM expected_tables AS e
LEFT JOIN pg_namespace AS n ON n.nspname = 'public'
LEFT JOIN pg_class AS c
    ON c.relnamespace = n.oid
   AND c.relname = e.table_name
   AND c.relkind = 'r'
ORDER BY e.table_name;

SELECT
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type
FROM information_schema.table_constraints AS tc
WHERE tc.table_schema = 'public'
  AND tc.table_name IN (
      'profiles', 'student_skills', 'projects', 'companies',
      'jobs', 'applications', 'candidate_decisions'
  )
ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name;

SELECT
    child.relname AS table_name,
    con.conname AS constraint_name,
    child_column.attname AS column_name,
    parent.relname AS referenced_table,
    parent_schema.nspname AS referenced_schema,
    parent_column.attname AS referenced_column,
    CASE con.confdeltype
        WHEN 'a' THEN 'NO ACTION'
        WHEN 'r' THEN 'RESTRICT'
        WHEN 'c' THEN 'CASCADE'
        WHEN 'n' THEN 'SET NULL'
        WHEN 'd' THEN 'SET DEFAULT'
    END AS on_delete
FROM pg_constraint AS con
JOIN pg_class AS child ON child.oid = con.conrelid
JOIN pg_namespace AS child_schema ON child_schema.oid = child.relnamespace
JOIN pg_class AS parent ON parent.oid = con.confrelid
JOIN pg_namespace AS parent_schema ON parent_schema.oid = parent.relnamespace
JOIN LATERAL unnest(con.conkey) WITH ORDINALITY AS child_key(attnum, ord)
    ON true
JOIN LATERAL unnest(con.confkey) WITH ORDINALITY AS parent_key(attnum, ord)
    ON parent_key.ord = child_key.ord
JOIN pg_attribute AS child_column
    ON child_column.attrelid = child.oid
   AND child_column.attnum = child_key.attnum
JOIN pg_attribute AS parent_column
    ON parent_column.attrelid = parent.oid
   AND parent_column.attnum = parent_key.attnum
WHERE con.contype = 'f'
  AND child_schema.nspname = 'public'
  AND child.relname IN (
      'profiles', 'student_skills', 'projects', 'companies',
      'jobs', 'applications', 'candidate_decisions'
  )
ORDER BY child.relname, con.conname, child_key.ord;

SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN (
      'profiles', 'student_skills', 'projects', 'companies',
      'jobs', 'applications', 'candidate_decisions'
  )
ORDER BY tablename, indexname;

SELECT schemaname, tablename, policyname, roles, cmd, qual, with_check
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN (
      'profiles', 'student_skills', 'projects', 'companies',
      'jobs', 'applications', 'candidate_decisions'
  )
ORDER BY tablename, policyname;

SELECT
    t.tgname AS trigger_name,
    n.nspname AS table_schema,
    c.relname AS table_name,
    pg_get_triggerdef(t.oid) AS trigger_definition,
    p.proname AS function_name,
    pg_get_functiondef(p.oid) AS function_definition
FROM pg_trigger AS t
JOIN pg_class AS c ON c.oid = t.tgrelid
JOIN pg_namespace AS n ON n.oid = c.relnamespace
JOIN pg_proc AS p ON p.oid = t.tgfoid
WHERE NOT t.tgisinternal
  AND n.nspname = 'auth'
  AND c.relname = 'users'
  AND t.tgname IN (
      'skill_bridge_create_profile',
      'skill_bridge_sync_profile_email'
  )
ORDER BY t.tgname;

SELECT
    t.tgname AS trigger_name,
    n.nspname AS table_schema,
    c.relname AS table_name,
    pg_get_triggerdef(t.oid) AS trigger_definition,
    p.proname AS function_name
FROM pg_trigger AS t
JOIN pg_class AS c ON c.oid = t.tgrelid
JOIN pg_namespace AS n ON n.oid = c.relnamespace
JOIN pg_proc AS p ON p.oid = t.tgfoid
WHERE NOT t.tgisinternal
  AND n.nspname = 'public'
  AND c.relname IN (
      'profiles', 'student_skills', 'projects', 'companies',
      'jobs', 'applications', 'candidate_decisions'
  )
ORDER BY c.relname, t.tgname;

SELECT
    p.oid::regprocedure AS sequence_sync_function,
    pg_get_functiondef(p.oid) AS function_definition
FROM pg_proc AS p
JOIN pg_namespace AS n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND p.proname = 'sync_job_id_seq';

SELECT
    n.nspname AS function_schema,
    p.proname AS function_name,
    p.prosecdef AS security_definer,
    p.proconfig AS function_settings,
    has_function_privilege('anon', p.oid, 'EXECUTE') AS anon_can_execute,
    has_function_privilege('authenticated', p.oid, 'EXECUTE')
        AS authenticated_can_execute
FROM pg_proc AS p
JOIN pg_namespace AS n ON n.oid = p.pronamespace
WHERE (n.nspname = 'public' AND p.proname IN (
          'get_candidates_for_job', 'sync_job_id_seq'
      ))
   OR (n.nspname = 'private' AND p.proname IN (
          'set_updated_at', 'create_profile_for_auth_user', 'sync_profile_email',
          'current_profile_id', 'current_profile_role',
          'owns_company', 'owns_job', 'is_student_profile'
      ))
ORDER BY n.nspname, p.proname;

SELECT
    grantee,
    table_name,
    privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 'public'
  AND grantee IN ('anon', 'authenticated')
  AND table_name IN (
      'profiles', 'student_skills', 'projects', 'companies',
      'jobs', 'applications', 'candidate_decisions'
  )
ORDER BY grantee, table_name, privilege_type;

SELECT
    grantee,
    table_name,
    column_name,
    privilege_type
FROM information_schema.column_privileges
WHERE table_schema = 'public'
  AND grantee IN ('anon', 'authenticated')
  AND table_name IN (
      'profiles', 'student_skills', 'projects', 'companies',
      'jobs', 'applications', 'candidate_decisions'
  )
ORDER BY grantee, table_name, column_name, privilege_type;

-- Manual, read-only RLS smoke tests. Replace each placeholder with real UUIDs
-- and job IDs from this project. Run each block separately in the SQL Editor.
-- The SQL Editor must permit SET ROLE; no rows should be modified by these tests.
--
-- Student: own profile should be visible; the other profile should return zero.
-- BEGIN;
-- SET LOCAL ROLE authenticated;
-- SELECT set_config('request.jwt.claim.sub', '<STUDENT_AUTH_UUID>', true);
-- SELECT count(*) AS own_profile_rows FROM public.profiles
--   WHERE auth_user_id = auth.uid();
-- SELECT count(*) AS other_profile_rows FROM public.profiles
--   WHERE id = '<OTHER_PROFILE_UUID>'::uuid;
-- SELECT count(*) AS own_applications FROM public.applications
--   WHERE student_profile_id = (
--     SELECT id FROM public.profiles WHERE auth_user_id = auth.uid()
--   );
-- ROLLBACK;
--
-- Recruiter: own company/jobs should be visible. Direct candidate/profile and
-- application tables do not grant other students' records or private notes.
-- BEGIN;
-- SET LOCAL ROLE authenticated;
-- SELECT set_config('request.jwt.claim.sub', '<RECRUITER_AUTH_UUID>', true);
-- SELECT count(*) AS own_companies FROM public.companies
--   WHERE owner_profile_id = (
--     SELECT id FROM public.profiles WHERE auth_user_id = auth.uid()
--   );
-- SELECT count(*) AS direct_candidate_profiles FROM public.profiles
--   WHERE role = 'student';
-- SELECT count(*) AS direct_applications FROM public.applications;
-- SELECT * FROM public.get_candidates_for_job('<OWNED_JOB_ID>');
-- SELECT count(*) AS nonconsenting_candidate_rows
--   FROM public.get_candidates_for_job('<OWNED_JOB_ID>')
--   WHERE candidate_profile_id = '<NONCONSENTING_PROFILE_UUID>'::uuid;
-- ROLLBACK;
--
-- Unauthorized recruiter: call get_candidates_for_job with a job owned by a
-- different recruiter in a separate transaction; it must raise insufficient
-- privilege. recruitment_visible=false candidates must not appear in the
-- owned-job RPC result. Do not treat SQL-editor superuser results as RLS tests.
--
-- Role escalation: as authenticated, an UPDATE of profiles.role or
-- profiles.requested_role must fail with insufficient privilege. A new account
-- with requested_role='recruiter' in user metadata must still have role='student'
-- and requested_role='recruiter' until trusted admin approval.
