import unittest

from scripts.migrate_json_to_supabase import build_plan, render_sql


class JsonMigrationPlanTests(unittest.TestCase):
    def sample_data(self):
        return {
            "jobs": [
                {
                    "id": "j14",
                    "title": "Python Developer",
                    "company": "Example Co",
                    "type": "Full-time",
                    "source": "sample",
                    "skills": ["Python", "SQL"],
                    "remote": False,
                    "posted_at": "2026-11-01",
                },
                {
                    "id": "j14",
                    "title": "Duplicate ID",
                    "type": "Full-time",
                    "skills": [],
                },
            ],
            "candidates": [
                {
                    "id": "c1",
                    "name": "Demo Candidate",
                    "skills": ["Python"],
                    "project": "Portfolio",
                    "github": "github.com/demo",
                },
            ],
            "decisions": {
                "j14:c1": "shortlisted",
                "missing:c1": "rejected",
            },
            "company": {
                "name": ".",
                "website": "",
                "location": "",
                "size": "",
                "about": "",
            },
        }

    def test_plan_preserves_ids_and_marks_duplicates_and_unresolved_rows(self):
        plan = build_plan(self.sample_data())
        self.assertEqual([row["id"] for row in plan["jobs"]], ["j14"])
        self.assertEqual(plan["candidates"][0]["id"], "c1")
        self.assertEqual(plan["decisions"][0]["candidate_legacy_id"], "c1")
        self.assertIsNone(plan["company"])
        statuses = [(row["source"], row["status"]) for row in plan["report"]]
        self.assertIn(("jobs", "skipped"), statuses)
        self.assertIn(("decisions", "skipped"), statuses)

    def test_rendered_sql_is_transactional_idempotent_and_non_destructive(self):
        plan = build_plan(self.sample_data())
        sql = render_sql(plan)
        self.assertIn("BEGIN;", sql)
        self.assertIn("COMMIT;", sql)
        self.assertIn("ON CONFLICT (id) DO NOTHING", sql)
        self.assertIn("ON CONFLICT (legacy_id) DO NOTHING", sql)
        self.assertIn("SELECT public.sync_job_id_seq();", sql)
        self.assertIn('"id":"j14"', sql)
        self.assertIn("recruitment_visible", sql)
        self.assertNotIn("TRUNCATE", sql.upper())
        self.assertNotIn("DROP TABLE", sql.upper())
        self.assertNotIn("DELETE FROM", sql.upper())

    def test_validation_reports_invalid_records_without_building_them(self):
        data = self.sample_data()
        data["jobs"].append({
            "id": "j15", "title": "Invalid", "type": "Unknown",
            "source": "sample", "skills": [], "remote": False,
        })
        plan = build_plan(data)
        self.assertNotIn("j15", {row["id"] for row in plan["jobs"]})
        self.assertTrue(
            any(row["record_id"] == "j15" and row["status"] == "failed" for row in plan["report"])
        )

    def test_verified_company_and_registered_candidate_are_mapped(self):
        data = self.sample_data()
        data["company"] = {
            "name": "Verified Co",
            "website": "https://example.test",
            "location": "Remote",
            "size": "1-10",
            "about": "Example",
        }
        data["decisions"]["j14:registered-student@example.test"] = "contacted"
        plan = build_plan(
            data,
            "99999999-9999-4999-8999-999999999999",
        )
        self.assertEqual(plan["company"]["name"], "Verified Co")
        self.assertEqual(
            plan["decisions"][-1]["candidate_email"],
            "student@example.test",
        )
        sql = render_sql(plan)
        self.assertIn("owner_profile_id uuid", sql)
        self.assertIn("lower(profile.email) = lower(input.candidate_email)", sql)


if __name__ == "__main__":
    unittest.main()
