import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Trash2, Users } from "lucide-react";
import { useStore } from "../../store";
import candidates from "../../data/candidates.json";
import { matchJob, prettyDate } from "../../lib/match";

export default function RecruiterDashboard() {
  const { company, user, postedJobs, decisions, removeJob, apiFetch } = useStore();

  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Fetch recruiter jobs from Flask
  useEffect(() => {
    let active = true;

    async function loadJobs() {
      try {
        setLoading(true);
        const data = await apiFetch("/jobs/");
        if (active) {
          const recruiterJobs = (Array.isArray(data) ? data : []).filter(
            (job) => job.source === "recruiter"
          );
          setJobs(recruiterJobs);
          setError("");
        }
      } catch (err) {
        if (active) {
          console.error("Recruiter jobs fetch error:", err);
          setError("Failed to load recruiter jobs.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadJobs();

    return () => {
      active = false;
    };
  }, [postedJobs, apiFetch]);

  // Count candidate decisions
  const count = (status) =>
    Object.values(decisions).filter((d) => d === status).length;

  const tiles = [
    { label: "Active jobs", n: jobs.length, bg: "bg-paper" },
    { label: "Shortlisted", n: count("shortlisted"), bg: "bg-teal text-white" },
    { label: "Contacted", n: count("contacted"), bg: "bg-mustard" },
    { label: "Rejected", n: count("rejected"), bg: "bg-coral text-white" },
  ];

  // Calculate matching candidates
  const strongMatches = (job) =>
    candidates.filter(
      (c) => (matchJob(job, c.skills).score ?? 0) >= 50
    ).length;

  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <h1 className="reveal text-4xl font-extrabold tracking-tight sm:text-5xl">
        Hi {user?.name?.split(" ")[0] || "Recruiter"}, hiring for{" "}
        {company?.name || "your company"}.
      </h1>

      {/* Dashboard statistics */}
      <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-4">
        {tiles.map((t, i) => (
          <div
            key={t.label}
            className={`reveal rounded-xl2 border border-line p-5 ${t.bg}`}
            style={{ animationDelay: `${i * 70}ms` }}
          >
            <p className="font-display text-5xl font-extrabold">
              {t.n}
            </p>
            <p className="mt-1 text-sm font-medium opacity-80">
              {t.label}
            </p>
          </div>
        ))}
      </div>

      {/* Jobs section */}
      <div className="mb-4 mt-12 flex items-end justify-between">
        <h2 className="text-2xl font-extrabold">Your jobs</h2>
        <Link to="/recruiter/post" className="btn-coral">
          <Plus size={16} /> Post a job
        </Link>
      </div>

      {loading ? (
        <div className="card text-center">
          Loading jobs...
        </div>
      ) : error ? (
        <div className="card text-center text-coral">
          {error}
        </div>
      ) : jobs.length === 0 ? (
        <div className="card border-dashed text-center">
          <span className="font-display text-6xl font-extrabold text-mustard">
            00
          </span>
          <p className="mt-2 font-semibold">
            No jobs posted yet
          </p>
          <p className="text-sm text-ink/60">
            Post your first role and see which students match.
          </p>
          <Link to="/recruiter/post" className="btn-ink mt-4">
            Post a job
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {jobs.map((j) => (
            <article
              key={j.id}
              className="card flex flex-wrap items-center justify-between gap-4"
            >
              <div>
                <Link
                  to={`/recruiter/jobs/${j.id}`}
                  className="font-display text-lg font-bold hover:underline"
                >
                  {j.title}
                </Link>
                <p className="text-sm text-ink/60">
                  {j.type} · {j.location} · Posted{" "}
                  {prettyDate(j.posted_at)}
                </p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {(j.skills || []).map((s) => (
                    <span
                      key={s}
                      className="chip bg-teal text-white"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Link
                  to={`/recruiter/jobs/${j.id}`}
                  className="btn-ink !py-2"
                >
                  <Users size={14} /> {strongMatches(j)} strong matches
                </Link>

                <button
                  className="btn-line !py-2"
                  aria-label={`Remove ${j.title}`}
                  onClick={async () => {
                    try {
                      await removeJob(j.id);
                      setJobs((prev) =>
                        prev.filter((job) => job.id !== j.id)
                      );
                    } catch (err) {
                      alert("Could not delete job.");
                    }
                  }}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
