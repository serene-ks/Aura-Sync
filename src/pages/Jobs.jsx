import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { useJobs } from "../lib/useJobs";
import JobCard from "../components/JobCard";

const TYPES = ["Internship", "Full-time", "Part-time", "Contract"];

export default function Jobs() {
 const { jobs, loading, error } = useJobs(); // already sorted by match score
  const [q, setQ] = useState("");
  const [type, setType] = useState("");
  const [remote, setRemote] = useState(false);
  const [minMatch, setMinMatch] = useState(0);

  const results = useMemo(() => {
    const text = q.trim().toLowerCase();
    return jobs.filter((j) => {
      if (type && j.type !== type) return false;
      if (remote && !j.remote) return false;
      if ((j.match.score ?? 0) < minMatch) return false;
      if (!text) return true;
      return [j.title, j.company, j.location, ...j.skills].join(" ").toLowerCase().includes(text);
    });
  }, [jobs, q, type, remote, minMatch]);

  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">Jobs & internships</h1>
      <p className="mt-2 text-ink/60">Sorted by how well they match your skills.</p>

      <div className="card mt-6 flex flex-wrap items-center gap-3 !p-4">
        <div className="relative min-w-[220px] flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink/40" />
          <input className="input !pl-9" placeholder="Title, company, skill or city" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search jobs" />
        </div>
        <select className="input !w-auto" value={type} onChange={(e) => setType(e.target.value)} aria-label="Job type">
          <option value="">All types</option>
          {TYPES.map((t) => <option key={t}>{t}</option>)}
        </select>
        <select className="input !w-auto" value={minMatch} onChange={(e) => setMinMatch(Number(e.target.value))} aria-label="Minimum match">
          <option value={0}>Any match</option>
          <option value={40}>40%+ match</option>
          <option value={70}>70%+ match</option>
        </select>
        <label className="flex items-center gap-2 text-sm font-medium"><input type="checkbox" checked={remote} onChange={(e) => setRemote(e.target.checked)} /> Remote only</label>
      </div>

      <p className="mb-4 mt-6 text-sm text-ink/60">{results.length} {results.length === 1 ? "job" : "jobs"} found</p>
      {results.length === 0 ? (
        <p className="card border-dashed text-center text-ink/60">No jobs match. Try fewer filters.</p>
      ) : (
        <div className="grid gap-4">{results.map((j, i) => <JobCard key={j.id} job={j} delay={Math.min(i, 6) * 60} />)}</div>
      )}
    </div>
  );
}
