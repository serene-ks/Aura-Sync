import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Check, Mail, X } from "lucide-react";
import { useStore } from "../../store";
import candidates from "../../data/candidates.json";
import { matchJob } from "../../lib/match";
import MatchRing from "../../components/MatchRing";

const LABEL = {
  shortlisted: "Shortlisted",
  contacted: "Contacted",
  rejected: "Rejected",
};

export default function Candidates() {
  const { id } = useParams();
  const { decisions, decide, loadDecisions, apiFetch } = useStore();

  const [job, setJob] = useState(null);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [minMatch, setMinMatch] = useState(0);
  const [onlyShortlisted, setOnlyShortlisted] = useState(false);

  useEffect(() => {
    let active = true;

    async function fetchData() {
      setLoading(true);
      setError("");

      try {
        // Fetch job details
        const jobData = await apiFetch(`/jobs/${id}`);

        // Fetch registered visible students for this recruiter
        const studentData = await apiFetch("/students/");

        if (active) {
          setJob({
            ...jobData,
            skills: jobData.skills || jobData.required_skills || [],
          });

          setStudents(Array.isArray(studentData) ? studentData : []);
        }

        await loadDecisions(id);
      } catch (err) {
        console.error("Candidates fetch error:", err);

        if (active) {
          setError(err.message || "Unable to load job or candidate details.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      active = false;
    };
  }, [id, apiFetch, loadDecisions]);

  // Combine dummy candidates and registered students
  const ranked = useMemo(() => {
    if (!job) return [];

    const dummyCandidates = candidates.map((c) => ({
      ...c,
      candidateType: "Sample",
    }));

    const registeredCandidates = students.map((s, index) => ({
      ...s,

      id:
        s.id ||
        (s.email
          ? `registered-${s.email}`
          : `registered-${index}`),

      name: s.name || "Student",

      college:
        s.college ||
        s.university ||
        s.institution ||
        "College not provided",

      course: s.course || "Course not provided",

      year: s.year || "Year not provided",

      skills: Array.isArray(s.skills)
        ? s.skills.map((skill) =>
            typeof skill === "object"
              ? skill.name || skill.skill || ""
              : skill
          ).filter(Boolean)
        : [],

      project: s.project || "Not provided",
      github: s.github || "GitHub not provided",

      candidateType: "Registered",
    }));

    const allCandidates = [
      ...dummyCandidates,
      ...registeredCandidates,
    ];

    return allCandidates
      .map((c) => ({
        ...c,
        match: matchJob(job, c.skills || []),
      }))
      .sort(
        (a, b) =>
          (b.match.score ?? -1) - (a.match.score ?? -1)
      );
  }, [job, students]);

  if (loading) {
    return (
      <div className="p-10 text-center">
        Loading job details...
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-20 text-center">
        <h1 className="text-3xl font-extrabold">
          {error || "Job not found"}
        </h1>

        <Link to="/recruiter" className="btn-ink mt-6">
          Back to dashboard
        </Link>
      </div>
    );
  }

  const status = (c) => decisions[job.id + ":" + c.id];

  const shown = ranked.filter(
    (c) =>
      (c.match.score ?? 0) >= minMatch &&
      (!onlyShortlisted || status(c) === "shortlisted")
  );

  const toggle = (c, s) => {
    decide(job.id, c.id, status(c) === s ? null : s);
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-12">
      <Link
        to="/recruiter"
        className="inline-flex items-center gap-1 text-sm text-ink/60 hover:text-ink"
      >
        <ArrowLeft size={14} /> Dashboard
      </Link>

      <h1 className="mt-3 text-4xl font-extrabold tracking-tight">
        {job.title}
      </h1>

      <p className="mt-1 text-ink/60">
        {job.company} · Candidates ranked by skill match.
      </p>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {job.skills.map((s) => (
          <span key={s} className="chip bg-teal text-white">
            {s}
          </span>
        ))}
      </div>

      <div className="card mt-6 flex flex-wrap items-center gap-3 !p-4">
        <select
          className="input !w-auto"
          value={minMatch}
          onChange={(e) => setMinMatch(Number(e.target.value))}
          aria-label="Minimum match"
        >
          <option value={0}>Any match</option>
          <option value={40}>40%+ match</option>
          <option value={70}>70%+ match</option>
        </select>

        <label className="flex items-center gap-2 text-sm font-medium">
          <input
            type="checkbox"
            checked={onlyShortlisted}
            onChange={(e) => setOnlyShortlisted(e.target.checked)}
          />
          Shortlisted only
        </label>

        <span className="ml-auto text-sm text-ink/60">
          {shown.length} of {ranked.length} candidates
        </span>
      </div>

      <div className="mt-4 grid gap-4">
        {shown.length === 0 && (
          <p className="card border-dashed text-center text-ink/60">
            No candidates match these filters.
          </p>
        )}

        {shown.map((c) => (
          <article key={c.id} className="card flex gap-5">
            <MatchRing score={c.match.score} />

            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h2 className="font-display text-lg font-bold leading-tight">
                    {c.name}
                  </h2>

                  <p className="text-sm text-ink/60">
                    {c.course} · {c.college} · {c.year}
                  </p>

                  <span className="mt-1 inline-block rounded-full bg-teal/10 px-2 py-1 text-xs font-semibold text-teal">
                    {c.candidateType}
                  </span>
                </div>

                {status(c) && (
                  <span className="chip bg-ink text-cream">
                    {LABEL[status(c)]}
                  </span>
                )}
              </div>

              <p className="mt-2 text-sm text-ink/70">
                Project: {c.project} · {c.github}
              </p>

              <div className="mt-3 flex flex-wrap gap-1.5">
                {c.match.matched.map((s) => (
                  <span key={s} className="chip bg-teal text-white">
                    {s}
                  </span>
                ))}

                {c.match.missing.map((s) => (
                  <span
                    key={s}
                    className="chip border border-dashed border-ink/30 text-ink/60"
                  >
                    {s}
                  </span>
                ))}
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  className="btn-ink !py-1.5"
                  onClick={() => toggle(c, "shortlisted")}
                >
                  <Check size={14} />
                  {status(c) === "shortlisted" ? "Shortlisted" : "Shortlist"}
                </button>

                <button
                  className="btn-line !py-1.5"
                  onClick={() => toggle(c, "contacted")}
                >
                  <Mail size={14} />
                  {status(c) === "contacted" ? "Contacted" : "Contact"}
                </button>

                <button
                  className="btn-line !py-1.5"
                  onClick={() => toggle(c, "rejected")}
                >
                  <X size={14} />
                  {status(c) === "rejected" ? "Rejected" : "Reject"}
                </button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}