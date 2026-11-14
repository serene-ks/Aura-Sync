import argparse
from datetime import date, datetime
import json
from pathlib import Path
import shutil
import sys
import uuid

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
SOURCE_FILES = {
    "jobs": BACKEND_DIR / "data" / "jobs.json",
    "decisions": BACKEND_DIR / "data" / "decisions.json",
    "company": BACKEND_DIR / "data" / "company.json",
    "candidates": PROJECT_DIR / "src" / "data" / "candidates.json",
    "frontend_jobs_reference": PROJECT_DIR / "src" / "data" / "jobs.json",
}
VALID_JOB_TYPES = {"Internship", "Full-time", "Part-time", "Contract"}
VALID_DECISIONS = {"shortlisted", "contacted", "rejected"}


def _read_json(path, expected_type):
    with path.open("r", encoding="utf-8") as file:
        value = json.load(file)
    if not isinstance(value, expected_type):
        raise ValueError(f"{path.name} must contain {expected_type.__name__}.")
    return value


def _record(report, source, record_id, status, reason=""):
    report.append({
        "source": source,
        "record_id": str(record_id),
        "status": status,
        "reason": reason,
    })


def _optional_text(row, field, default=None):
    value = row.get(field, default)
    if value is None:
        return default
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{field} must be text.")
    return value


def build_plan(data, company_owner_profile_id=None):
    report = []
    job_rows = []
    candidate_rows = []
    decision_rows = []
    jobs = data["jobs"]
    candidates = data["candidates"]
    decisions = data["decisions"]
    company = data["company"]

    seen_jobs = set()
    for index, row in enumerate(jobs):
        if not isinstance(row, dict):
            _record(report, "jobs", f"row-{index + 1}", "failed", "Job record must be an object.")
            continue
        record_id = row.get("id", f"row-{index + 1}")
        if not isinstance(record_id, str) or not record_id.strip():
            _record(report, "jobs", record_id, "failed", "Job ID is missing or invalid.")
            continue
        if record_id in seen_jobs:
            _record(report, "jobs", record_id, "skipped", "Duplicate ID in source file.")
            continue
        seen_jobs.add(record_id)
        if not isinstance(row.get("title"), str) or not row["title"].strip():
            _record(report, "jobs", record_id, "failed", "Job title is required.")
            continue
        if (
            not isinstance(row.get("type", "Full-time"), str)
            or row.get("type", "Full-time") not in VALID_JOB_TYPES
        ):
            _record(report, "jobs", record_id, "failed", "Unsupported job type.")
            continue
        if (
            not isinstance(row.get("source", "recruiter"), str)
            or row.get("source", "recruiter") not in {"sample", "recruiter"}
        ):
            _record(report, "jobs", record_id, "failed", "Unsupported job source.")
            continue
        skills = row.get("skills", [])
        if not isinstance(skills, list) or any(
            not isinstance(skill, str) or not skill.strip() for skill in skills
        ):
            _record(report, "jobs", record_id, "failed", "Job skills must be non-empty text values.")
            continue
        if not isinstance(row.get("remote", False), bool):
            _record(report, "jobs", record_id, "failed", "Remote must be a boolean.")
            continue
        try:
            text_fields = {
                field: _optional_text(row, field, default)
                for field, default in (
                    ("company", ""),
                    ("location", "Not specified"),
                    ("salary", ""),
                    ("posted_at", None),
                    ("apply_url", ""),
                    ("description", ""),
                    ("experience", ""),
                )
            }
            if text_fields["posted_at"]:
                date.fromisoformat(text_fields["posted_at"])
        except (TypeError, ValueError):
            _record(report, "jobs", record_id, "failed", "A job text field or posted_at date is invalid.")
            continue
        job_rows.append({
            "id": record_id,
            "title": row["title"],
            "company_name": text_fields["company"],
            "location": text_fields["location"],
            "type": row.get("type", "Full-time"),
            "remote": row.get("remote", False),
            "salary": text_fields["salary"],
            "posted_at": text_fields["posted_at"] or None,
            "apply_url": text_fields["apply_url"],
            "source": row.get("source", "recruiter"),
            "description": text_fields["description"],
            "skills": skills,
            "experience": text_fields["experience"],
        })
        _record(report, "jobs", record_id, "planned")

    candidate_ids = set()
    seen_candidate_ids = set()
    for index, row in enumerate(candidates):
        if not isinstance(row, dict):
            _record(report, "candidates", f"row-{index + 1}", "failed", "Candidate record must be an object.")
            continue
        candidate_id = row.get("id", f"row-{index + 1}")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            _record(report, "candidates", candidate_id, "failed", "Candidate ID is missing or invalid.")
            continue
        if candidate_id in seen_candidate_ids:
            _record(report, "candidates", candidate_id, "skipped", "Duplicate ID in source file.")
            continue
        seen_candidate_ids.add(candidate_id)
        if not isinstance(row.get("name"), str) or not row["name"].strip():
            _record(report, "candidates", candidate_id, "failed", "Candidate name is required.")
            continue
        try:
            candidate_text = {
                field: _optional_text(row, field)
                for field in ("college", "course", "year", "project", "github")
            }
        except ValueError as error:
            _record(report, "candidates", candidate_id, "failed", str(error))
            continue
        skills = row.get("skills", [])
        if not isinstance(skills, list) or any(
            not isinstance(skill, str) or not skill.strip() for skill in skills
        ):
            _record(report, "candidates", candidate_id, "failed", "Candidate skills must be non-empty text values.")
            continue
        candidate_rows.append({
            "id": candidate_id,
            "name": row["name"],
            "college": candidate_text["college"],
            "course": candidate_text["course"],
            "year": candidate_text["year"],
            "skills": skills,
            "project": candidate_text["project"],
            "github": candidate_text["github"],
        })
        candidate_ids.add(candidate_id)
        _record(report, "candidates", candidate_id, "planned")

    planned_job_ids = {row["id"] for row in job_rows}
    seen_decisions = set()
    for key, status in decisions.items():
        job_id, separator, candidate_ref = str(key).partition(":")
        pair = (job_id, candidate_ref)
        if not separator or not job_id or not candidate_ref:
            _record(report, "decisions", key, "failed", "Decision key must be job_id:candidate_id.")
            continue
        if pair in seen_decisions:
            _record(report, "decisions", key, "skipped", "Duplicate decision in source file.")
            continue
        seen_decisions.add(pair)
        if job_id not in planned_job_ids:
            _record(report, "decisions", key, "skipped", "Referenced job is not in the jobs import.")
            continue
        if not isinstance(status, str) or status not in VALID_DECISIONS:
            _record(report, "decisions", key, "failed", "Unsupported recruiter decision status.")
            continue
        if candidate_ref not in candidate_ids and not candidate_ref.startswith("registered-"):
            _record(report, "decisions", key, "skipped", "Candidate has no matching importable profile reference.")
            continue
        decision = {
            "job_id": job_id,
            "candidate_legacy_id": None,
            "candidate_email": None,
            "status": status,
        }
        if candidate_ref in candidate_ids:
            decision["candidate_legacy_id"] = candidate_ref
        else:
            email = candidate_ref[len("registered-"):].strip().lower()
            if "@" not in email:
                _record(report, "decisions", key, "failed", "Registered candidate reference is not an email.")
                continue
            decision["candidate_email"] = email
        decision_rows.append(decision)
        _record(report, "decisions", key, "planned")

    valid_owner_id = None
    if company_owner_profile_id:
        try:
            valid_owner_id = str(uuid.UUID(company_owner_profile_id))
        except (ValueError, TypeError, AttributeError):
            _record(report, "company", "company.json", "failed", "Company owner profile ID must be a UUID.")

    company_row = None
    company_name = company.get("name") if isinstance(company, dict) else None
    if not isinstance(company_name, str) or not company_name.strip() or company_name.strip() == ".":
        _record(report, "company", "company.json", "skipped", "Source contains no usable company profile.")
    elif not valid_owner_id:
        _record(report, "company", "company.json", "skipped", "No independently verified recruiter profile was supplied.")
    else:
        try:
            company_row = {
                "owner_profile_id": valid_owner_id,
                "name": company_name.strip(),
                "website": _optional_text(company, "website", ""),
                "location": _optional_text(company, "location", ""),
                "size": _optional_text(company, "size", ""),
                "about": _optional_text(company, "about", ""),
            }
        except ValueError as error:
            _record(report, "company", "company.json", "failed", str(error))
        else:
            _record(report, "company", "company.json", "planned")

    return {
        "jobs": job_rows,
        "candidates": candidate_rows,
        "decisions": decision_rows,
        "company": company_row,
        "report": report,
    }


def _sql_json(value):
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return "'" + encoded.replace("'", "''") + "'::jsonb"


def _sql_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def render_sql(plan):
    lines = [
        "-- Generated from the existing JSON data; inspect before running.",
        "-- Execute once in the Supabase SQL Editor as a trusted database owner.",
        "-- This transaction inserts missing rows only and never updates/deletes existing rows.",
        "-- Jobs are not assigned to a recruiter company because source ownership is unverified.",
        "BEGIN;",
        "CREATE TEMP TABLE _sb_import_report (source text, record_id text, status text, reason text) ON COMMIT DROP;",
    ]

    failed_or_skipped = [
        row for row in plan["report"]
        if row["status"] in {"failed", "skipped"}
    ]
    for row in failed_or_skipped:
        lines.append(
            "INSERT INTO _sb_import_report VALUES "
            f"({_sql_literal(row['source'])}, {_sql_literal(row['record_id'])}, "
            f"{_sql_literal(row['status'])}, {_sql_literal(row['reason'])});"
        )

    jobs_json = _sql_json(plan["jobs"])
    lines.extend([
        "CREATE TEMP TABLE _sb_jobs_input AS",
        "SELECT * FROM jsonb_to_recordset(" + jobs_json + ") AS j(",
        "    id text, title text, company_name text, location text, type text,",
        "    remote boolean, salary text, posted_at date, apply_url text,",
        "    source text, description text, skills text[], experience text",
        ");",
        "WITH inserted AS (",
        "    INSERT INTO public.jobs (",
        "        id, company_name, title, location, type, remote, salary, posted_at,",
        "        apply_url, source, description, skills, experience",
        "    )",
        "    SELECT id, company_name, title, location, type, remote, salary,",
        "        coalesce(posted_at, current_date), apply_url, source, description,",
        "        skills, experience",
        "    FROM _sb_jobs_input",
        "    ON CONFLICT (id) DO NOTHING",
        "    RETURNING id",
        ")",
        "INSERT INTO _sb_import_report",
        "SELECT 'jobs', input.id,",
        "    CASE WHEN inserted.id IS NULL THEN 'skipped' ELSE 'imported' END,",
        "    CASE WHEN inserted.id IS NULL THEN 'Job ID already exists.' ELSE '' END",
        "FROM _sb_jobs_input AS input",
        "LEFT JOIN inserted USING (id);",
        "SELECT public.sync_job_id_seq();",
    ])

    candidates_json = _sql_json(plan["candidates"])
    lines.extend([
        "CREATE TEMP TABLE _sb_candidates_input AS",
        "SELECT * FROM jsonb_to_recordset(" + candidates_json + ") AS c(",
        "    id text, name text, college text, course text, year text,",
        "    skills jsonb, project text, github text",
        ");",
        "WITH inserted AS (",
        "    INSERT INTO public.profiles (",
        "        legacy_id, is_demo, role, name, college, course, year, links,",
        "        recruitment_visible",
        "    )",
        "    SELECT id, true, 'student', name, college, course, year,",
        "        jsonb_build_object('github', github), true",
        "    FROM _sb_candidates_input",
        "    ON CONFLICT (legacy_id) DO NOTHING",
        "    RETURNING legacy_id",
        ")",
        "INSERT INTO _sb_import_report",
        "SELECT 'candidates', input.id,",
        "    CASE WHEN inserted.legacy_id IS NULL THEN 'skipped' ELSE 'imported' END,",
        "    CASE WHEN inserted.legacy_id IS NULL THEN 'Candidate ID already exists.' ELSE '' END",
        "FROM _sb_candidates_input AS input",
        "LEFT JOIN inserted ON inserted.legacy_id = input.id;",
        "WITH requested AS (",
        "    SELECT input.id AS candidate_id, profile.id AS profile_id,",
        "        btrim(skill.value) AS skill_name",
        "    FROM _sb_candidates_input AS input",
        "    JOIN public.profiles AS profile ON profile.legacy_id = input.id",
        "    CROSS JOIN LATERAL jsonb_array_elements_text(input.skills) AS skill(value)",
        "), inserted AS (",
        "    INSERT INTO public.student_skills (profile_id, skill_name, level)",
        "    SELECT profile_id, skill_name, 'Beginner'",
        "    FROM requested WHERE skill_name <> ''",
        "    ON CONFLICT DO NOTHING",
        "    RETURNING profile_id, skill_name",
        ")",
        "INSERT INTO _sb_import_report",
        "SELECT 'student_skills', requested.candidate_id || ':' || requested.skill_name,",
        "    CASE WHEN inserted.profile_id IS NULL THEN 'skipped' ELSE 'imported' END,",
        "    CASE WHEN inserted.profile_id IS NULL THEN 'Skill already exists.' ELSE '' END",
        "FROM requested",
        "LEFT JOIN inserted USING (profile_id, skill_name);",
        "WITH requested AS (",
        "    SELECT input.id AS candidate_id, profile.id AS profile_id,",
        "        btrim(input.project) AS title",
        "    FROM _sb_candidates_input AS input",
        "    JOIN public.profiles AS profile ON profile.legacy_id = input.id",
        "    WHERE nullif(btrim(input.project), '') IS NOT NULL",
        "), inserted AS (",
        "    INSERT INTO public.projects (profile_id, title, description, link)",
        "    SELECT requested.profile_id, requested.title, '', ''",
        "    FROM requested",
        "    WHERE NOT EXISTS (",
        "        SELECT 1 FROM public.projects AS existing",
        "        WHERE existing.profile_id = requested.profile_id",
        "          AND existing.title = requested.title",
        "          AND existing.description = '' AND existing.link = ''",
        "    )",
        "    RETURNING profile_id, title",
        ")",
        "INSERT INTO _sb_import_report",
        "SELECT 'projects', requested.candidate_id || ':' || requested.title,",
        "    CASE WHEN inserted.profile_id IS NULL THEN 'skipped' ELSE 'imported' END,",
        "    CASE WHEN inserted.profile_id IS NULL THEN 'Project already exists.' ELSE '' END",
        "FROM requested",
        "LEFT JOIN inserted USING (profile_id, title);",
    ])

    if plan["company"]:
        company_json = _sql_json([plan["company"]])
        lines.extend([
            "WITH input AS (",
            "    SELECT * FROM jsonb_to_recordset(" + company_json + ") AS c(",
            "        owner_profile_id uuid, name text, website text, location text,",
            "        size text, about text",
            "    )",
            "), eligible AS (",
            "    SELECT input.* FROM input",
            "    JOIN public.profiles AS owner ON owner.id = input.owner_profile_id",
            "    WHERE owner.role = 'recruiter' AND NOT owner.is_demo",
            "), inserted AS (",
            "    INSERT INTO public.companies",
            "        (owner_profile_id, name, website, location, size, about)",
            "    SELECT owner_profile_id, name, website, location, size, about FROM eligible",
            "    ON CONFLICT (owner_profile_id) DO NOTHING",
            "    RETURNING owner_profile_id",
            ")",
            "INSERT INTO _sb_import_report",
            "SELECT 'company', 'company.json',",
            "    CASE",
            "        WHEN eligible.owner_profile_id IS NULL THEN 'skipped'",
            "        WHEN inserted.owner_profile_id IS NULL THEN 'skipped'",
            "        ELSE 'imported'",
            "    END,",
            "    CASE",
            "        WHEN eligible.owner_profile_id IS NULL THEN 'Owner profile is missing or is not an approved recruiter.'",
            "        WHEN inserted.owner_profile_id IS NULL THEN 'A company already exists for this owner.'",
            "        ELSE ''",
            "    END",
            "FROM input",
            "LEFT JOIN eligible USING (owner_profile_id)",
            "LEFT JOIN inserted USING (owner_profile_id);",
        ])

    decisions_json = _sql_json(plan["decisions"])
    lines.extend([
        "CREATE TEMP TABLE _sb_decisions_input AS",
        "SELECT * FROM jsonb_to_recordset(" + decisions_json + ") AS d(",
        "    job_id text, candidate_legacy_id text, candidate_email text, status text",
        ");",
        "WITH resolved AS (",
        "    SELECT input.job_id, profile.id AS candidate_profile_id, input.status,",
        "        input.candidate_legacy_id, input.candidate_email",
        "    FROM _sb_decisions_input AS input",
        "    JOIN public.jobs AS job ON job.id = input.job_id",
        "    JOIN public.profiles AS profile ON",
        "        (input.candidate_legacy_id IS NOT NULL AND profile.legacy_id = input.candidate_legacy_id)",
        "        OR (input.candidate_email IS NOT NULL AND lower(profile.email) = lower(input.candidate_email))",
        "), inserted AS (",
        "    INSERT INTO public.candidate_decisions (job_id, candidate_profile_id, status)",
        "    SELECT job_id, candidate_profile_id, status FROM resolved",
        "    ON CONFLICT DO NOTHING",
        "    RETURNING job_id, candidate_profile_id",
        ")",
        "INSERT INTO _sb_import_report",
        "SELECT 'decisions', input.job_id || ':' ||",
        "    coalesce(input.candidate_legacy_id, 'registered-' || input.candidate_email),",
        "    CASE",
        "        WHEN resolved.candidate_profile_id IS NULL THEN 'skipped'",
        "        WHEN inserted.job_id IS NULL THEN 'skipped'",
        "        ELSE 'imported'",
        "    END,",
        "    CASE",
        "        WHEN resolved.candidate_profile_id IS NULL THEN 'Referenced job or candidate profile was not found.'",
        "        WHEN inserted.job_id IS NULL THEN 'Decision already exists.'",
        "        ELSE ''",
        "    END",
        "FROM _sb_decisions_input AS input",
        "LEFT JOIN resolved ON resolved.job_id = input.job_id",
        "    AND resolved.status = input.status",
        "    AND resolved.candidate_legacy_id IS NOT DISTINCT FROM input.candidate_legacy_id",
        "    AND resolved.candidate_email IS NOT DISTINCT FROM input.candidate_email",
        "LEFT JOIN inserted ON inserted.job_id = resolved.job_id",
        "    AND inserted.candidate_profile_id = resolved.candidate_profile_id;",
        "SELECT status, source, count(*) AS records",
        "FROM _sb_import_report GROUP BY status, source ORDER BY source, status;",
        "SELECT source, record_id, status, reason",
        "FROM _sb_import_report WHERE status <> 'imported'",
        "ORDER BY source, record_id;",
        "COMMIT;",
    ])
    return "\n".join(lines) + "\n"


def load_sources():
    return {
        "jobs": _read_json(SOURCE_FILES["jobs"], list),
        "decisions": _read_json(SOURCE_FILES["decisions"], dict),
        "company": _read_json(SOURCE_FILES["company"], dict),
        "candidates": _read_json(SOURCE_FILES["candidates"], list),
    }


def backup_sources():
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = BACKEND_DIR / "data_backups"
    backup_dir = backup_root / f"supabase-migration-{timestamp}"
    suffix = 1
    while backup_dir.exists():
        backup_dir = backup_root / f"supabase-migration-{timestamp}-{suffix}"
        suffix += 1
    backup_dir.mkdir(parents=True)
    for source_name, source_path in SOURCE_FILES.items():
        if source_path.is_file():
            shutil.copy2(source_path, backup_dir / f"{source_name}.json")
    return backup_dir


def _print_report(report):
    counts = {}
    for row in report:
        status = row["status"]
        if status == "planned":
            status = "planned_for_import"
        counts[status] = counts.get(status, 0) + 1
    print("Source data report:")
    print(f"  planned for import: {counts.get('planned_for_import', 0)}")
    print(f"  skipped: {counts.get('skipped', 0)}")
    print(f"  failed validation: {counts.get('failed', 0)}")
    for row in report:
        if row["status"] in {"failed", "skipped"}:
            print(
                f"  {row['status']}: {row['source']} {row['record_id']}"
                + (f" — {row['reason']}" if row["reason"] else "")
            )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Plan a JSON import and generate idempotent SQL for the Supabase SQL Editor. "
            "This script never connects to or writes to Supabase."
        )
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--output", type=Path, help="Generate SQL at this new file path.")
    parser.add_argument(
        "--company-owner-profile-id",
        help="UUID of a recruiter whose ownership was independently verified.",
    )
    args = parser.parse_args(argv)

    try:
        plan = build_plan(load_sources(), args.company_owner_profile_id)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Could not prepare JSON migration: {error}")
        return 2

    _print_report(plan["report"])
    if args.dry_run:
        print("Dry run only: no backup, SQL file, database connection, or data writes.")
        return 1 if any(row["status"] == "failed" for row in plan["report"]) else 0

    output_path = args.output.resolve()
    source_paths = {path.resolve() for path in SOURCE_FILES.values()}
    if output_path in source_paths:
        print("Output path cannot overwrite an existing JSON source file.")
        return 2
    if output_path.exists():
        print("Output file already exists; choose a new path to avoid overwriting it.")
        return 2

    try:
        backup_dir = backup_sources()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("x", encoding="utf-8", newline="\n") as file:
            file.write(render_sql(plan))
    except OSError as error:
        print(f"Could not create the backup or SQL file ({type(error).__name__}).")
        return 2

    print(f"JSON backups created at: {backup_dir}")
    print(f"Generated import SQL at: {output_path}")
    print("Review the SQL and execute it manually in the Supabase SQL Editor.")
    return 1 if any(row["status"] == "failed" for row in plan["report"]) else 0


if __name__ == "__main__":
    sys.exit(main())
