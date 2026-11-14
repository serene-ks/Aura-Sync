import unittest
import uuid
from types import SimpleNamespace

from postgrest.exceptions import APIError
from supabase_auth.errors import AuthApiError

from app import create_app


class E2EIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.student_profile_id = str(uuid.uuid4())
        self.recruiter_profile_id = str(uuid.uuid4())
        self.unapproved_recruiter_profile_id = str(uuid.uuid4())
        self.company_id = str(uuid.uuid4())
        self.other_recruiter_profile_id = str(uuid.uuid4())
        self.other_company_id = str(uuid.uuid4())

        self.users = {
            "valid-student-jwt": ("student-auth-id", "student@example.edu", "student", self.student_profile_id),
            "valid-recruiter-jwt": ("recruiter-auth-id", "recruiter@company.com", "recruiter", self.recruiter_profile_id),
            "unapproved-recruiter-jwt": ("unapproved-auth-id", "applicant@pending.com", "student", self.unapproved_recruiter_profile_id),
            "other-recruiter-jwt": ("other-recruiter-auth-id", "other@otherco.com", "recruiter", self.other_recruiter_profile_id),
        }

        self.db = {
            "profiles": [
                {
                    "id": self.student_profile_id,
                    "auth_user_id": "student-auth-id",
                    "legacy_id": None,
                    "is_demo": False,
                    "role": "student",
                    "requested_role": None,
                    "email": "student@example.edu",
                    "name": "Jane Student",
                    "college": "State University",
                    "course": "B.Tech Computer Science",
                    "year": "Final year",
                    "graduation_year": "2027",
                    "cv_name": "jane_cv.pdf",
                    "links": {"github": "https://github.com/janestudent"},
                    "preferences": {"types": ["Internship"], "remote": True},
                    "completed": True,
                    "recruitment_visible": True,
                },
                {
                    "id": self.recruiter_profile_id,
                    "auth_user_id": "recruiter-auth-id",
                    "legacy_id": None,
                    "is_demo": False,
                    "role": "recruiter",
                    "requested_role": None,
                    "email": "recruiter@company.com",
                    "name": "Alice Recruiter",
                    "college": None,
                    "course": None,
                    "year": None,
                    "graduation_year": None,
                    "cv_name": None,
                    "links": {},
                    "preferences": {},
                    "completed": True,
                    "recruitment_visible": False,
                },
                {
                    "id": self.unapproved_recruiter_profile_id,
                    "auth_user_id": "unapproved-auth-id",
                    "legacy_id": None,
                    "is_demo": False,
                    "role": "student",
                    "requested_role": "recruiter",
                    "email": "applicant@pending.com",
                    "name": "Pending Recruiter",
                    "college": None,
                    "course": None,
                    "year": None,
                    "graduation_year": None,
                    "cv_name": None,
                    "links": {},
                    "preferences": {},
                    "completed": False,
                    "recruitment_visible": False,
                },
                {
                    "id": self.other_recruiter_profile_id,
                    "auth_user_id": "other-recruiter-auth-id",
                    "legacy_id": None,
                    "is_demo": False,
                    "role": "recruiter",
                    "requested_role": None,
                    "email": "other@otherco.com",
                    "name": "Bob Recruiter",
                    "college": None,
                    "course": None,
                    "year": None,
                    "graduation_year": None,
                    "cv_name": None,
                    "links": {},
                    "preferences": {},
                    "completed": True,
                    "recruitment_visible": False,
                },
                {
                    "id": str(uuid.uuid4()),
                    "auth_user_id": None,
                    "legacy_id": "c1",
                    "is_demo": True,
                    "role": "student",
                    "requested_role": None,
                    "email": None,
                    "name": "Demo Consenting Candidate",
                    "college": "Demo College",
                    "course": "CSE",
                    "year": "3rd year",
                    "graduation_year": "2028",
                    "cv_name": None,
                    "links": {"github": "https://github.com/demo"},
                    "preferences": {},
                    "completed": True,
                    "recruitment_visible": True,
                },
                {
                    "id": str(uuid.uuid4()),
                    "auth_user_id": None,
                    "legacy_id": "c2",
                    "is_demo": True,
                    "role": "student",
                    "requested_role": None,
                    "email": None,
                    "name": "Hidden Candidate",
                    "college": "Demo College",
                    "course": "CSE",
                    "year": "2nd year",
                    "graduation_year": "2029",
                    "cv_name": None,
                    "links": {},
                    "preferences": {},
                    "completed": True,
                    "recruitment_visible": False,
                },
            ],
            "companies": [
                {
                    "id": self.company_id,
                    "owner_profile_id": self.recruiter_profile_id,
                    "name": "Tech Corp",
                    "website": "https://techcorp.com",
                    "location": "Bengaluru",
                    "size": "51-200",
                    "about": "Building the future of software.",
                },
                {
                    "id": self.other_company_id,
                    "owner_profile_id": self.other_recruiter_profile_id,
                    "name": "Other Corp",
                    "website": "https://othercorp.com",
                    "location": "Pune",
                    "size": "11-50",
                    "about": "Innovating finance.",
                },
            ],
            "jobs": [
                {
                    "id": "j1",
                    "company_id": None,
                    "company_name": "Sample Co",
                    "title": "Software Intern",
                    "location": "Remote",
                    "type": "Internship",
                    "remote": True,
                    "salary": "₹25,000 / month",
                    "posted_at": "2026-11-01",
                    "apply_url": "https://sample.com/apply",
                    "source": "sample",
                    "description": "Great learning experience.",
                    "skills": ["Python", "SQL"],
                    "experience": "0-1 years",
                },
                {
                    "id": "j2",
                    "company_id": self.company_id,
                    "company_name": "Tech Corp",
                    "title": "Frontend Engineer",
                    "location": "Bengaluru",
                    "type": "Full-time",
                    "remote": False,
                    "salary": "₹8L / year",
                    "posted_at": "2026-11-02",
                    "apply_url": "https://techcorp.com/careers/j2",
                    "source": "recruiter",
                    "description": "React and TypeScript engineer.",
                    "skills": ["JavaScript", "React"],
                    "experience": "1-3 years",
                },
                {
                    "id": "j3",
                    "company_id": self.other_company_id,
                    "company_name": "Other Corp",
                    "title": "Backend Engineer",
                    "location": "Pune",
                    "type": "Full-time",
                    "remote": True,
                    "salary": "₹9L / year",
                    "posted_at": "2026-11-03",
                    "apply_url": "https://othercorp.com/careers/j3",
                    "source": "recruiter",
                    "description": "Go and Python microservices.",
                    "skills": ["Python", "Go"],
                    "experience": "1-3 years",
                },
            ],
            "student_skills": [
                {"profile_id": self.student_profile_id, "skill_name": "Python", "level": "Advanced"},
                {"profile_id": self.student_profile_id, "skill_name": "React", "level": "Intermediate"},
            ],
            "projects": [
                {
                    "id": str(uuid.uuid4()),
                    "profile_id": self.student_profile_id,
                    "title": "Skill Matcher",
                    "description": "AI-powered job matching system.",
                    "link": "https://github.com/janestudent/skill-matcher",
                }
            ],
            "applications": [],
            "candidate_decisions": [],
        }

        test_case = self
        class MockClient:
            def __init__(self, token):
                self.token = token
                self.auth = self

            def get_user(self, token):
                if token not in test_case.users:
                    raise AuthApiError("Invalid token", 401, None)
                auth_id, email, _, _ = test_case.users[token]
                return SimpleNamespace(user=SimpleNamespace(id=auth_id, email=email))

            def table(self, table_name):
                return MockQuery(self, table_name)

            def rpc(self, name, params):
                if name == "get_candidates_for_job":
                    job_id = params["p_job_id"]
                    job = next((j for j in test_case.db["jobs"] if j["id"] == job_id), None)
                    if not job:
                        raise APIError({"message": "Job not found", "code": "PGRST116"})

                    current_user_profile_id = test_case.users[self.token][3]
                    company = next((c for c in test_case.db["companies"] if c["id"] == job.get("company_id")), None)
                    if not company or company["owner_profile_id"] != current_user_profile_id:
                        raise APIError({"message": "forbidden", "code": "42501"})

                    result = []
                    for profile in test_case.db["profiles"]:
                        if profile["role"] != "student" or not profile["recruitment_visible"]:
                            continue
                        skills = [s["skill_name"] for s in test_case.db["student_skills"] if s["profile_id"] == profile["id"]]
                        skill_details = [s for s in test_case.db["student_skills"] if s["profile_id"] == profile["id"]]
                        projects = [p for p in test_case.db["projects"] if p["profile_id"] == profile["id"]]
                        result.append({
                            "id": profile.get("legacy_id") or profile["id"],
                            "candidate_profile_id": profile["id"],
                            "name": profile["name"],
                            "college": profile.get("college"),
                            "course": profile.get("course"),
                            "year": profile.get("year"),
                            "graduation_year": profile.get("graduation_year"),
                            "skills": skills,
                            "skill_details": skill_details,
                            "project": projects[0]["title"] if projects else None,
                            "github": (profile.get("links") or {}).get("github"),
                            "projects": projects,
                            "links": profile.get("links", {}),
                            "candidateType": "Sample" if profile.get("is_demo") else "Registered",
                            "is_demo": profile.get("is_demo", False),
                        })
                    return SimpleNamespace(data=result, execute=lambda: SimpleNamespace(data=result))
                raise NotImplementedError(name)

        class MockQuery:
            def __init__(self, client, table_name):
                self.client = client
                self.table_name = table_name
                self.op = "select"
                self.filters = []
                self.payload = None
                self.is_single = False
                self.order_field = None
                self.order_desc = False

            def select(self, cols="*"):
                self.cols = cols
                return self

            def eq(self, field, value):
                self.filters.append((field, value))
                return self

            def order(self, field, desc=False):
                self.order_field = field
                self.order_desc = desc
                return self

            def single(self):
                self.is_single = True
                return self

            def maybe_single(self):
                self.is_single = True
                return self

            def insert(self, payload):
                self.op = "insert"
                self.payload = payload
                return self

            def update(self, payload):
                self.op = "update"
                self.payload = payload
                return self

            def delete(self):
                self.op = "delete"
                return self

            def _filter_match(self, row):
                return all(row.get(f) == val for f, val in self.filters)

            def execute(self):
                table = test_case.db[self.table_name]
                if self.op == "insert":
                    items = self.payload if isinstance(self.payload, list) else [self.payload]
                    inserted = []
                    for it in items:
                        row = dict(it)
                        if self.table_name == "jobs" and "id" not in row:
                            existing_nums = [int(j["id"][1:]) for j in table if j["id"].startswith("j") and j["id"][1:].isdigit()]
                            row["id"] = f"j{max(existing_nums, default=0) + 1}"
                        elif self.table_name in ("companies", "projects", "applications") and "id" not in row:
                            row["id"] = str(uuid.uuid4())
                        table.append(row)
                        inserted.append(row)
                    res = inserted[0] if (self.is_single and inserted) else inserted
                    return SimpleNamespace(data=res)

                matches = [r for r in table if self._filter_match(r)]

                if self.op == "update":
                    for r in matches:
                        r.update(self.payload)
                    res = matches[0] if (self.is_single and matches) else matches
                    return SimpleNamespace(data=res)

                if self.op == "delete":
                    for r in matches:
                        table.remove(r)
                    return SimpleNamespace(data=None)

                if self.order_field:
                    matches.sort(key=lambda r: str(r.get(self.order_field) or ""), reverse=self.order_desc)

                if self.table_name == "applications" and hasattr(self, "cols") and "job:jobs(" in self.cols:
                    enriched = []
                    for app in matches:
                        copy = dict(app)
                        copy["job"] = next((j for j in test_case.db["jobs"] if j["id"] == app["job_id"]), None)
                        enriched.append(copy)
                    matches = enriched

                res = matches[0] if (self.is_single and matches) else (None if self.is_single else matches)
                return SimpleNamespace(data=res)

        self.app = create_app({
            "TESTING": True,
            "SUPABASE_URL": "https://rdqdvmdwbxwrxgpmwqbl.supabase.co",
            "SUPABASE_KEY": "sb_publishable_test",
            "SUPABASE_CLIENT_FACTORY": lambda u, k, t: MockClient(t),
        })
        self.client = self.app.test_client()

    def bearer(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_e2e_student_profile_skills_and_projects_flow(self):
        # 1. Read profile
        res = self.client.get("/students/", headers=self.bearer("valid-student-jwt"))
        self.assertEqual(res.status_code, 200)
        profile_list = res.get_json()
        self.assertEqual(len(profile_list), 1)
        self.assertEqual(profile_list[0]["name"], "Jane Student")
        self.assertEqual(len(profile_list[0]["skills"]), 2)

        # 2. Update profile with new skills & projects
        updated_payload = {
            "name": "Jane Doe Student",
            "college": "State University",
            "course": "B.Tech Computer Science",
            "year": "Graduated",
            "graduation_year": "2026",
            "completed": True,
            "recruitment_visible": True,
            "skills": [
                {"name": "Python", "level": "Advanced"},
                {"name": "FastAPI", "level": "Intermediate"},
            ],
            "projects": [
                {
                    "title": "Aura Sync",
                    "description": "Full stack integration platform",
                    "link": "https://github.com/janestudent/aura-sync",
                }
            ],
        }
        res_put = self.client.put(
            "/students/student@example.edu",
            headers=self.bearer("valid-student-jwt"),
            json=updated_payload,
        )
        self.assertEqual(res_put.status_code, 200)
        updated_data = res_put.get_json()["student"]
        self.assertEqual(updated_data["name"], "Jane Doe Student")
        self.assertEqual(len(updated_data["skills"]), 2)
        skill_names = [s["name"] for s in updated_data["skills"]]
        self.assertIn("FastAPI", skill_names)
        self.assertIn("Python", skill_names)

    def test_e2e_student_job_browsing_and_application_tracking(self):
        # 1. Browse jobs
        res = self.client.get("/jobs/", headers=self.bearer("valid-student-jwt"))
        self.assertEqual(res.status_code, 200)
        jobs = res.get_json()
        self.assertGreaterEqual(len(jobs), 3)

        # 2. Get specific job
        res_job = self.client.get("/jobs/j2", headers=self.bearer("valid-student-jwt"))
        self.assertEqual(res_job.status_code, 200)
        self.assertEqual(res_job.get_json()["title"], "Frontend Engineer")

        # 3. Track job (save)
        res_track = self.client.post(
            "/tracker/",
            headers=self.bearer("valid-student-jwt"),
            json={"job_id": "j2", "status": "saved", "notes": "Need to prepare React questions"},
        )
        self.assertEqual(res_track.status_code, 201)
        track_item = res_track.get_json()
        track_id = track_item["id"]
        self.assertEqual(track_item["status"], "saved")

        # 4. Update status to applied
        res_applied = self.client.put(
            f"/tracker/{track_id}",
            headers=self.bearer("valid-student-jwt"),
            json={"status": "applied", "applied_at": "2026-11-13"},
        )
        self.assertEqual(res_applied.status_code, 200)
        self.assertEqual(res_applied.get_json()["status"], "applied")

        # 5. Get tracker list
        res_list = self.client.get("/tracker/", headers=self.bearer("valid-student-jwt"))
        self.assertEqual(res_list.status_code, 200)
        self.assertEqual(len(res_list.get_json()), 1)

        # 6. Untrack job
        res_delete = self.client.delete(f"/tracker/{track_id}", headers=self.bearer("valid-student-jwt"))
        self.assertEqual(res_delete.status_code, 200)
        res_list_after = self.client.get("/tracker/", headers=self.bearer("valid-student-jwt"))
        self.assertEqual(len(res_list_after.get_json()), 0)

    def test_e2e_recruiter_company_job_management_and_candidate_discovery(self):
        # 1. Recruiter checks company profile
        res_company = self.client.get("/company/", headers=self.bearer("valid-recruiter-jwt"))
        self.assertEqual(res_company.status_code, 200)
        self.assertEqual(res_company.get_json()["name"], "Tech Corp")

        # 2. Recruiter posts a new job
        new_job_payload = {
            "title": "Cloud Architect",
            "location": "Bengaluru",
            "type": "Full-time",
            "remote": True,
            "salary": "₹15L / year",
            "experience": "2-4 years",
            "description": "Design secure cloud backends.",
            "skills": ["AWS", "Docker", "Python"],
            "posted_at": "2026-11-13",
        }
        res_post_job = self.client.post("/jobs/", headers=self.bearer("valid-recruiter-jwt"), json=new_job_payload)
        self.assertEqual(res_post_job.status_code, 201)
        created_job = res_post_job.get_json()["job"]
        self.assertEqual(created_job["title"], "Cloud Architect")
        self.assertEqual(created_job["source"], "recruiter")

        # 3. Recruiter views owned jobs (must see j2 and the new job, but NOT other recruiter's j3)
        res_jobs = self.client.get("/jobs/", headers=self.bearer("valid-recruiter-jwt"))
        self.assertEqual(res_jobs.status_code, 200)
        owned_jobs = res_jobs.get_json()
        owned_job_ids = {j["id"] for j in owned_jobs}
        self.assertIn("j2", owned_job_ids)
        self.assertIn(created_job["id"], owned_job_ids)
        self.assertNotIn("j3", owned_job_ids)

        # 4. Candidate discovery via get_candidates_for_job
        res_candidates = self.client.get("/students/", headers=self.bearer("valid-recruiter-jwt"))
        self.assertEqual(res_candidates.status_code, 200)
        candidate_ids = {c["id"] for c in res_candidates.get_json()}
        # Jane Student is recruitment_visible = True
        self.assertIn(self.student_profile_id, candidate_ids)
        # Demo candidate c1 is is_demo = True, so omitted from /students/ API response
        self.assertNotIn("c1", candidate_ids)
        # c2 has recruitment_visible = False, must NEVER appear
        self.assertNotIn("c2", candidate_ids)

        # 5. Shortlisting candidate for job j2
        res_decision = self.client.post(
            "/jobs/j2/decisions/",
            headers=self.bearer("valid-recruiter-jwt"),
            json={"candidate_id": self.student_profile_id, "status": "shortlisted"},
        )
        self.assertEqual(res_decision.status_code, 200)
        self.assertEqual(res_decision.get_json()["decisions"], {f"j2:{self.student_profile_id}": "shortlisted"})

    def test_e2e_role_based_access_control_and_approval_enforcement(self):
        # 1. Unapproved recruiter (role='student', requested_role='recruiter') cannot access recruiter routes
        res_pending = self.client.get("/company/", headers=self.bearer("unapproved-recruiter-jwt"))
        self.assertEqual(res_pending.status_code, 403)
        self.assertIn("cannot perform this operation", res_pending.get_json()["error"])

        res_post_pending = self.client.post(
            "/jobs/",
            headers=self.bearer("unapproved-recruiter-jwt"),
            json={"title": "Hacked Job", "skills": ["Python"]},
        )
        self.assertEqual(res_post_pending.status_code, 403)

        # 2. Student cannot access recruiter routes
        res_student_company = self.client.get("/company/", headers=self.bearer("valid-student-jwt"))
        self.assertEqual(res_student_company.status_code, 403)

        # 3. Recruiter cannot modify another recruiter's job
        res_modify_other = self.client.put(
            "/jobs/j3",
            headers=self.bearer("valid-recruiter-jwt"),
            json={"title": "Hijacked Title"},
        )
        self.assertEqual(res_modify_other.status_code, 403)

        # 4. Recruiter cannot access student private tracker
        res_recruiter_tracker = self.client.get("/tracker/", headers=self.bearer("valid-recruiter-jwt"))
        self.assertEqual(res_recruiter_tracker.status_code, 403)

        # 5. Unauthenticated request receives 401
        res_unauth = self.client.get("/jobs/")
        self.assertEqual(res_unauth.status_code, 401)


if __name__ == "__main__":
    unittest.main()
