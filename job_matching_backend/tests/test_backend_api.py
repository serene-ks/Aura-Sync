import unittest
import uuid
from types import SimpleNamespace

from postgrest.exceptions import APIError
from supabase_auth.errors import AuthApiError

from app import create_app


IDS = {
    "student_profile": "11111111-1111-4111-8111-111111111111",
    "other_student_profile": "22222222-2222-4222-8222-222222222222",
    "recruiter_profile": "33333333-3333-4333-8333-333333333333",
    "other_recruiter_profile": "44444444-4444-4444-8444-444444444444",
    "company": "55555555-5555-4555-8555-555555555555",
    "other_company": "66666666-6666-4666-8666-666666666666",
    "demo_candidate": "77777777-7777-4777-8777-777777777777",
    "private_candidate": "88888888-8888-4888-8888-888888888888",
}


class FakeDatabase:
    def __init__(self):
        self.users = {
            "student-token": ("student-auth", "student@example.test"),
            "other-student-token": ("other-student-auth", "other@example.test"),
            "recruiter-token": ("recruiter-auth", "recruiter@example.test"),
            "other-recruiter-token": ("other-recruiter-auth", "other-recruiter@example.test"),
        }
        self.tables = {
            "profiles": [
                self._profile(IDS["student_profile"], "student-auth", "student", "Student", "student@example.test"),
                self._profile(IDS["other_student_profile"], "other-student-auth", "student", "Other Student", "other@example.test"),
                self._profile(IDS["recruiter_profile"], "recruiter-auth", "recruiter", "Recruiter", "recruiter@example.test"),
                self._profile(IDS["other_recruiter_profile"], "other-recruiter-auth", "recruiter", "Other Recruiter", "other-recruiter@example.test"),
                {
                    "id": IDS["demo_candidate"], "auth_user_id": None, "legacy_id": "c1",
                    "is_demo": True, "role": "student", "name": "Demo Candidate",
                    "email": None, "college": "Example College", "course": "CS",
                    "year": "Final year", "graduation_year": "2027", "cv_name": None,
                    "links": {"github": "github.com/demo"}, "preferences": {},
                    "completed": True, "recruitment_visible": True,
                },
                {
                    "id": IDS["private_candidate"], "auth_user_id": None, "legacy_id": "c2",
                    "is_demo": True, "role": "student", "name": "Private Candidate",
                    "email": None, "college": None, "course": None, "year": None,
                    "graduation_year": None, "cv_name": None, "links": {},
                    "preferences": {}, "completed": True, "recruitment_visible": False,
                },
            ],
            "companies": [
                {
                    "id": IDS["company"], "owner_profile_id": IDS["recruiter_profile"],
                    "name": "Recruiter Co", "website": "", "location": "",
                    "size": "", "about": "",
                },
                {
                    "id": IDS["other_company"], "owner_profile_id": IDS["other_recruiter_profile"],
                    "name": "Other Co", "website": "", "location": "",
                    "size": "", "about": "",
                },
            ],
            "jobs": [
                self._job("j11", IDS["company"], "Recruiter Co"),
                self._job("j12", IDS["other_company"], "Other Co"),
                self._job("j1", None, "Sample Co", source="sample"),
            ],
            "student_skills": [],
            "projects": [],
            "applications": [
                {
                    "id": "other-app", "student_profile_id": IDS["other_student_profile"],
                    "job_id": "j1", "status": "saved", "notes": "", "applied_at": None,
                },
            ],
            "candidate_decisions": [],
        }
        self.tables["profiles"][0]["recruitment_visible"] = True
        self.active_token = None

    @staticmethod
    def _profile(profile_id, auth_user_id, role, name, email):
        return {
            "id": profile_id, "auth_user_id": auth_user_id, "legacy_id": None,
            "is_demo": False, "role": role, "requested_role": None, "email": email,
            "name": name, "college": None, "course": None, "year": None,
            "graduation_year": None, "cv_name": None, "links": {},
            "preferences": {}, "completed": False, "recruitment_visible": False,
        }

    @staticmethod
    def _job(job_id, company_id, company_name, source="recruiter"):
        return {
            "id": job_id, "company_id": company_id, "company_name": company_name,
            "title": f"{job_id} role", "location": "Remote", "type": "Internship",
            "remote": True, "salary": "", "posted_at": "2026-11-01",
            "apply_url": "", "source": source, "description": "Test job",
            "skills": ["Python"], "experience": "",
        }

    @property
    def user(self):
        token_user = self.users.get(self.active_token)
        user_id = token_user[0] if token_user else None
        return next(
            (row for row in self.tables["profiles"] if row["auth_user_id"] == user_id),
            None,
        )

    def can_read(self, table, row):
        profile = self.user
        if not profile:
            return False
        if table == "profiles":
            return row.get("auth_user_id") == profile["auth_user_id"] and not row.get("is_demo")
        if table == "companies":
            return profile["role"] == "recruiter" and row["owner_profile_id"] == profile["id"]
        if table == "jobs":
            return True
        if table in {"student_skills", "projects", "applications"}:
            return profile["role"] == "student" and row.get(
                "profile_id", row.get("student_profile_id")
            ) == profile["id"]
        if table == "candidate_decisions":
            return (
                profile["role"] == "recruiter"
                and self.owns_job(row["job_id"])
                and self.candidate_is_visible(row["candidate_profile_id"])
            )
        return False

    def can_write(self, table, row, operation):
        profile = self.user
        if not profile:
            return False
        if table == "companies":
            return profile["role"] == "recruiter" and row.get("owner_profile_id") == profile["id"]
        if table == "jobs":
            if operation == "insert":
                return (
                    profile["role"] == "recruiter"
                    and row.get("source") == "recruiter"
                    and self.owns_company(row.get("company_id"))
                )
            return profile["role"] == "recruiter" and self.owns_job(row["id"])
        if table in {"student_skills", "projects"}:
            return profile["role"] == "student" and row.get("profile_id") == profile["id"]
        if table == "applications":
            return profile["role"] == "student" and row.get("student_profile_id") == profile["id"]
        if table == "candidate_decisions":
            return (
                profile["role"] == "recruiter"
                and self.owns_job(row["job_id"])
                and self.candidate_is_visible(row["candidate_profile_id"])
            )
        return False

    def owns_company(self, company_id):
        return any(
            row["id"] == company_id and row["owner_profile_id"] == (self.user or {}).get("id")
            for row in self.tables["companies"]
        )

    def owns_job(self, job_id):
        return any(
            row["id"] == job_id and self.owns_company(row.get("company_id"))
            for row in self.tables["jobs"]
        )

    def candidate_is_visible(self, profile_id):
        return any(
            row["id"] == profile_id and row["role"] == "student" and row["recruitment_visible"]
            for row in self.tables["profiles"]
        )


class FakeQuery:
    def __init__(self, client, table):
        self.client = client
        self.table_name = table
        self.operation = "select"
        self.payload = None
        self.filters = []
        self.single_result = False

    def select(self, columns="*"):
        self.columns = columns
        return self

    def insert(self, payload):
        self.operation, self.payload = "insert", payload
        return self

    def update(self, payload):
        self.operation, self.payload = "update", payload
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def order(self, field, desc=False):
        self.sort_field, self.sort_desc = field, desc
        return self

    def maybe_single(self):
        self.single_result = True
        return self

    def single(self):
        self.single_result = True
        return self

    def _matches(self, row):
        return all(row.get(field) == value for field, value in self.filters)

    def _with_relations(self, row):
        result = dict(row)
        if self.table_name == "applications" and "job:jobs(" in getattr(self, "columns", ""):
            result["job"] = next(
                (job for job in self.client.db.tables["jobs"] if job["id"] == row["job_id"]),
                None,
            )
        return result

    def execute(self):
        table = self.client.db.tables[self.table_name]
        if self.operation in {"insert", "upsert"}:
            payloads = self.payload if isinstance(self.payload, list) else [self.payload]
            inserted = []
            for original in payloads:
                row = dict(original)
                if self.table_name == "jobs" and not row.get("id"):
                    numbers = [
                        int(job["id"][1:])
                        for job in table
                        if job["id"].startswith("j") and job["id"][1:].isdigit()
                    ]
                    row["id"] = f"j{max(numbers, default=0) + 1}"
                elif self.table_name in {"companies", "projects", "applications"} and not row.get("id"):
                    row["id"] = str(uuid.uuid4())
                if not self.client.db.can_write(self.table_name, row, "insert"):
                    raise APIError({"message": "forbidden", "code": "42501"})
                table.append(row)
                inserted.append(self._with_relations(row))
            return SimpleNamespace(data=inserted[0] if self.single_result and inserted else inserted)

        selected = [
            row
            for row in table
            if self._matches(row) and self.client.db.can_read(self.table_name, row)
        ]
        if self.operation == "update":
            updated = []
            for row in selected:
                row.update(self.payload)
                updated.append(self._with_relations(row))
            selected = updated
        elif self.operation == "delete":
            for row in selected:
                if self.client.db.can_write(self.table_name, row, "delete"):
                    table.remove(row)
            selected = []
        if hasattr(self, "sort_field"):
            selected.sort(
                key=lambda row: row.get(self.sort_field) or "",
                reverse=self.sort_desc,
            )
        selected = [self._with_relations(row) for row in selected]
        if self.single_result:
            selected = selected[0] if selected else None
        return SimpleNamespace(data=selected)


class FakeClient:
    def __init__(self, db, token):
        self.db = db
        self.token = token
        self.db.active_token = token
        self.auth = self

    def get_user(self, token):
        if token not in self.db.users:
            raise AuthApiError("Invalid token", 401, None)
        user_id, email = self.db.users[token]
        return SimpleNamespace(user=SimpleNamespace(id=user_id, email=email))

    def table(self, name):
        return FakeQuery(self, name)

    def rpc(self, name, params):
        if name != "get_candidates_for_job":
            raise AssertionError(f"Unexpected RPC: {name}")
        job_id = params["p_job_id"]
        if not self.db.owns_job(job_id):
            raise APIError({"message": "forbidden", "code": "42501"})
        result = []
        for profile in self.db.tables["profiles"]:
            if profile["role"] != "student" or not profile["recruitment_visible"]:
                continue
            skills = [
                row for row in self.db.tables["student_skills"]
                if row["profile_id"] == profile["id"]
            ]
            projects = [
                row for row in self.db.tables["projects"]
                if row["profile_id"] == profile["id"]
            ]
            result.append({
                "id": profile.get("legacy_id") or profile["id"],
                "candidate_profile_id": profile["id"],
                "name": profile["name"],
                "college": profile.get("college"),
                "course": profile.get("course"),
                "year": profile.get("year"),
                "graduation_year": profile.get("graduation_year"),
                "skills": [row["skill_name"] for row in skills],
                "skill_details": skills,
                "project": projects[0]["title"] if projects else None,
                "github": (profile.get("links") or {}).get("github"),
                "projects": projects,
                "links": profile.get("links", {}),
                "candidateType": "Sample" if profile.get("is_demo") else "Registered",
                "is_demo": profile.get("is_demo", False),
            })
        return FakeQueryResult(result)


class FakeQueryResult:
    def __init__(self, data):
        self.data = data

    def execute(self):
        return self


class BackendApiTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDatabase()
        def fake_client_factory(url, key, token):
            self.assertEqual(url, "https://example.supabase.co")
            self.assertEqual(key, "test-publishable-key")
            return FakeClient(self.db, token)

        self.app = create_app({
            "TESTING": True,
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_KEY": "test-publishable-key",
            "SUPABASE_CLIENT_FACTORY": fake_client_factory,
        })
        self.client = self.app.test_client()

    def auth(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_startup_requires_supabase_configuration(self):
        with self.assertRaisesRegex(RuntimeError, "SUPABASE_URL, SUPABASE_KEY"):
            create_app({"SUPABASE_URL": "", "SUPABASE_KEY": ""})
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_authentication_failures_and_role_checks(self):
        self.assertEqual(self.client.get("/students/").status_code, 401)
        self.assertEqual(
            self.client.get("/students/", headers=self.auth("expired")).status_code,
            401,
        )
        self.assertEqual(
            self.client.post("/company/", headers=self.auth("student-token"), json={"name": "x"}).status_code,
            403,
        )

    def test_student_profile_skills_projects_create_read_and_update(self):
        payload = {
            "name": "Student One",
            "college": "Example University",
            "course": "B.Tech",
            "year": "Final year",
            "graduation_year": "2027",
            "completed": True,
            "recruitment_visible": True,
            "role": "recruiter",
            "auth_user_id": "other-student-auth",
            "skills": [
                {"name": "Python", "level": "Advanced"},
                {"name": "SQL", "level": "Intermediate"},
            ],
            "projects": [{"title": "Portfolio", "description": "Demo", "link": "https://example.test"}],
        }
        created = self.client.post("/students/", headers=self.auth("student-token"), json=payload)
        self.assertEqual(created.status_code, 201)
        student = created.get_json()["student"]
        self.assertEqual(student["email"], "student@example.test")
        self.assertEqual(student["role"], "student")
        self.assertEqual(student["id"], IDS["student_profile"])
        self.assertEqual(
            self.db.tables["profiles"][0]["auth_user_id"],
            "student-auth",
        )
        self.assertEqual(student["skills"][0], {"name": "Python", "level": "Advanced"})
        self.assertEqual(student["projects"][0]["title"], "Portfolio")

        retrieved = self.client.get("/students/", headers=self.auth("student-token"))
        self.assertEqual(retrieved.status_code, 200)
        self.assertEqual(len(retrieved.get_json()), 1)

        payload["skills"] = [{"name": "Rust", "level": "Beginner"}]
        payload["projects"] = []
        updated = self.client.put(
            "/students/student@example.test",
            headers=self.auth("student-token"),
            json=payload,
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["student"]["skills"], [{"name": "Rust", "level": "Beginner"}])
        self.assertEqual(updated.get_json()["student"]["projects"], [])

    def test_student_cannot_read_or_modify_another_students_profile_or_tracker(self):
        response = self.client.get("/students/", headers=self.auth("student-token"))
        self.assertNotIn("other@example.test", str(response.get_json()))
        forbidden = self.client.put(
            "/students/other@example.test",
            headers=self.auth("student-token"),
            json={"name": "Changed"},
        )
        self.assertEqual(forbidden.status_code, 403)
        hidden = self.client.put(
            "/tracker/other-app",
            headers=self.auth("student-token"),
            json={"notes": "unauthorized"},
        )
        self.assertEqual(hidden.status_code, 404)

    def test_company_and_job_operations_are_owned_by_recruiter(self):
        created_company = self.client.post(
            "/company/",
            headers=self.auth("recruiter-token"),
            json={"name": "New Company", "website": "https://company.test"},
        )
        self.assertEqual(created_company.status_code, 200)
        self.assertEqual(self.client.get("/company/", headers=self.auth("recruiter-token")).get_json()["name"], "New Company")
        recruiter_jobs = self.client.get("/jobs/", headers=self.auth("recruiter-token")).get_json()
        self.assertTrue(all(job.get("company_id") == IDS["company"] for job in recruiter_jobs))
        student_jobs = self.client.get("/jobs/", headers=self.auth("student-token")).get_json()
        self.assertTrue(any(job["id"] == "j12" for job in student_jobs))

        created = self.client.post(
            "/jobs/",
            headers=self.auth("recruiter-token"),
            json={
                "title": "New role", "type": "Internship", "skills": ["Python"],
                "remote": True, "location": "Remote",
            },
        )
        self.assertEqual(created.status_code, 201)
        job = created.get_json()["job"]
        self.assertEqual(job["company"], "New Company")
        self.assertEqual(job["source"], "recruiter")
        self.assertEqual(self.client.get(f"/jobs/{job['id']}", headers=self.auth("student-token")).status_code, 200)

        updated = self.client.put(
            f"/jobs/{job['id']}",
            headers=self.auth("recruiter-token"),
            json={"title": "Updated role", "skills": ["SQL"]},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["job"]["title"], "Updated role")
        self.assertEqual(
            self.client.put("/jobs/j12", headers=self.auth("recruiter-token"), json={"title": "Other"})
            .status_code,
            403,
        )
        self.assertEqual(
            self.client.delete(f"/jobs/{job['id']}", headers=self.auth("recruiter-token")).status_code,
            200,
        )
        self.assertEqual(self.client.get(f"/jobs/{job['id']}", headers=self.auth("student-token")).status_code, 404)

    def test_recruiter_can_create_company_profile(self):
        self.db.tables["companies"] = [
            row for row in self.db.tables["companies"]
            if row["owner_profile_id"] != IDS["recruiter_profile"]
        ]
        response = self.client.post(
            "/company/",
            headers=self.auth("recruiter-token"),
            json={"name": "First Company"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["company"]["name"], "First Company")

    def test_tracker_create_duplicate_update_delete(self):
        created = self.client.post(
            "/tracker/",
            headers=self.auth("student-token"),
            json={"job_id": "j1", "status": "saved", "notes": "private"},
        )
        self.assertEqual(created.status_code, 201)
        item = created.get_json()
        self.assertEqual(item["job"]["company"], "Sample Co")
        duplicate = self.client.post(
            "/tracker/", headers=self.auth("student-token"), json={"job_id": "j1"}
        )
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(duplicate.get_json()["id"], item["id"])
        self.assertEqual(self.client.get("/tracker/", headers=self.auth("student-token")).status_code, 200)
        updated = self.client.put(
            f"/tracker/{item['id']}",
            headers=self.auth("student-token"),
            json={"status": "applied", "notes": "updated"},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["status"], "applied")
        self.assertEqual(self.client.delete(f"/tracker/{item['id']}", headers=self.auth("student-token")).status_code, 200)
        self.assertEqual(self.client.delete(f"/tracker/{item['id']}", headers=self.auth("student-token")).status_code, 404)

    def test_recruiter_candidate_consent_and_decisions(self):
        visible = self.client.get("/students/", headers=self.auth("recruiter-token"))
        candidate_ids = {row["id"] for row in visible.get_json()}
        self.assertIn(IDS["student_profile"], candidate_ids)
        self.assertNotIn(IDS["private_candidate"], candidate_ids)
        self.assertNotIn("c1", candidate_ids)
        self.assertTrue(all("email" not in row for row in visible.get_json()))

        private_decision = self.client.post(
            "/jobs/j11/decisions/",
            headers=self.auth("recruiter-token"),
            json={"candidate_id": "c2", "status": "shortlisted"},
        )
        self.assertEqual(private_decision.status_code, 404)

        decided = self.client.post(
            "/jobs/j11/decisions/",
            headers=self.auth("recruiter-token"),
            json={"candidate_id": "c1", "status": "shortlisted"},
        )
        self.assertEqual(decided.status_code, 200)
        self.assertEqual(decided.get_json()["decisions"], {"j11:c1": "shortlisted"})
        self.assertEqual(
            self.client.get("/jobs/j11/decisions/", headers=self.auth("recruiter-token")).get_json(),
            {"j11:c1": "shortlisted"},
        )
        self.assertEqual(
            self.client.post(
                "/jobs/j12/decisions/",
                headers=self.auth("recruiter-token"),
                json={"candidate_id": "c1", "status": "rejected"},
            ).status_code,
            403,
        )

    def test_invalid_input_returns_client_error(self):
        response = self.client.post(
            "/students/",
            headers=self.auth("student-token"),
            json={"name": "Student", "skills": [{"name": "Python", "level": "Expert"}]},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("level", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
