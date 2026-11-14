import { Link } from "react-router-dom";
import { Bookmark, Check, MapPin, Wallet } from "lucide-react";
import MatchRing from "./MatchRing";
import { useStore } from "../store";

export default function JobCard({ job, delay = 0 }) {
  const { tracker, track } = useStore();
  const saved = tracker.some(
    (t) => String(t.job_id ?? t.job?.id) === String(job.id)
  );
  return (
    <article className="card reveal flex gap-5 transition hover:-translate-y-0.5 hover:shadow-lg" style={{ animationDelay: `${delay}ms` }}>
      <MatchRing score={job.match.score} />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <Link to={`/jobs/${job.id}`} className="font-display text-lg font-bold leading-tight hover:underline">{job.title}</Link>
            <p className="text-sm text-ink/60">{job.company}</p>
          </div>
          <div className="flex gap-1.5">
            {job.remote && <span className="chip bg-teal/10 text-teal">Remote</span>}
            <span className="chip border border-line">{job.type}</span>
          </div>
        </div>
        <p className="mt-2 flex flex-wrap gap-x-4 text-sm text-ink/60">
          <span className="inline-flex items-center gap-1"><MapPin size={14} />{job.location}</span>
          <span className="inline-flex items-center gap-1"><Wallet size={14} />{job.salary}</span>
        </p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {job.match.matched.map((s) => <span key={s} className="chip bg-teal text-white">{s}</span>)}
          {job.match.missing.map((s) => <span key={s} className="chip border border-dashed border-ink/30 text-ink/60">{s}</span>)}
        </div>
        <div className="mt-4 flex gap-2">
          <Link to={`/jobs/${job.id}`} className="btn-ink !py-1.5">View</Link>
          <button className="btn-line !py-1.5" onClick={() => track(job)} disabled={saved}>
            {saved ? <><Check size={14} /> Saved</> : <><Bookmark size={14} /> Save</>}
          </button>
        </div>
      </div>
    </article>
  );
}
