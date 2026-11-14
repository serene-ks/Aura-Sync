import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Copy, ExternalLink, MapPin, Sparkles, Wallet } from "lucide-react";
import { useStore } from "../store";
import { useJobs } from "../lib/useJobs";
import { buildApplyKit } from "../lib/applyKit";
import { prettyDate } from "../lib/match";
import MatchRing from "../components/MatchRing";

function CopyButton({ text }) {
  const [done, setDone] = useState(false);
  async function copy() {
    try { await navigator.clipboard.writeText(text); setDone(true); setTimeout(() => setDone(false), 1500); } catch { /* clipboard blocked */ }
  }
  return <button className="btn-line !px-3 !py-1 !text-xs" onClick={copy}><Copy size={12} /> {done ? "Copied" : "Copy"}</button>;
}

export default function JobDetail() {
  const { id } = useParams();
  const { profile, tracker, track, setStatus } = useStore();
   const { jobs, loading, error } = useJobs();
   const job = jobs.find((j) => String(j.id) === String(id));
  const [kit, setKit] = useState(null);
  const [asking,setAsking]=useState(false);
   if (loading) {
     return <div className="p-10 text-center">Loading job details...</div>;
   }

   if (error) {
     return <div className="p-10 text-center">{error}</div>;
   }

  if (!job) return <div className="mx-auto max-w-2xl px-4 py-20 text-center"><h1 className="text-3xl font-extrabold">Job not found</h1><Link to="/jobs" className="btn-ink mt-6">Back to jobs</Link></div>;

  const item = tracker.find(
    (t) => String(t.job_id ?? t.job?.id ?? t.id) === String(job.id)
  );

  function apply() {
    window.open(job.apply_url, "_blank", "noopener");
    if (!item) track(job, "saved");
    setAsking(true); // when the student comes back we ask "Did you apply?"
  }
  function confirmApplied() {
    if (!item) track(job, "applied"); else setStatus(item.id, "applied");
    setAsking(false);
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-12">
      <Link to="/jobs" className="inline-flex items-center gap-1 text-sm text-ink/60 hover:text-ink"><ArrowLeft size={14} /> All jobs</Link>

      <header className="reveal mt-4 flex flex-wrap items-start justify-between gap-6">
        <div>
          <div className="flex gap-2">
            {job.remote && <span className="chip bg-teal/10 text-teal">Remote</span>}
            <span className="chip border border-line">{job.type}</span>
          </div>
          <h1 className="mt-3 text-4xl font-extrabold tracking-tight">{job.title}</h1>
          <p className="mt-1 text-lg text-ink/70">{job.company}</p>
          <p className="mt-3 flex flex-wrap gap-x-5 text-sm text-ink/60">
            <span className="inline-flex items-center gap-1"><MapPin size={14} />{job.location}</span>
            <span className="inline-flex items-center gap-1"><Wallet size={14} />{job.salary}</span>
            <span>Posted {prettyDate(job.posted_at)}</span>
          </p>
        </div>
        <MatchRing score={job.match.score} size={96} />
      </header>

      <div className="mt-8 flex flex-wrap items-center gap-3">
        <button className="btn-coral !px-6 !py-3" onClick={apply}>Open application page <ExternalLink size={16} /></button>
        <button className="btn-ink !py-3" onClick={() => setKit(buildApplyKit(job, profile, job.match))}><Sparkles size={16} /> Get my Apply Kit</button>
        {item && <span className="chip bg-ink/10">Tracker: {item.status}</span>}
      </div>

      {asking && (
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl2 bg-mustard p-4">
          <p className="font-medium">Did you apply to {job.company}?</p>
          <div className="flex gap-2">
            <button className="btn-ink !py-1.5" onClick={confirmApplied}>Yes, I applied</button>
            <button className="btn-line !py-1.5" onClick={() => setAsking(false)}>Not yet</button>
          </div>
        </div>
      )}

      <div className="mt-10 grid gap-4 md:grid-cols-2">
        <section className="card">
          <h2 className="text-xl font-bold">Why you match</h2>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {job.match.matched.length ? job.match.matched.map((s) => <span key={s} className="chip bg-teal text-white">{s}</span>) : <p className="text-sm text-ink/60">No overlap yet.</p>}
          </div>
          {job.match.missing.length > 0 && (
            <>
              <h3 className="mt-5 text-sm font-bold uppercase tracking-wider text-ink/60">Skills to learn</h3>
              <ul className="mt-2 space-y-1.5 text-sm">
                {job.match.missing.map((s) => (
                  <li key={s} className="flex items-center justify-between">
                    <span>{s}</span>
                    <a className="inline-flex items-center gap-1 font-semibold underline" target="_blank" rel="noreferrer"
                      href={`https://www.youtube.com/results?search_query=${encodeURIComponent("learn " + s + " for beginners")}`}>Learn <ExternalLink size={12} /></a>
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
        <section className="card">
          <h2 className="text-xl font-bold">About the role</h2>
          <p className="mt-3 text-ink/70">{job.description}</p>
          <p className="mt-3 text-sm text-ink/60">Experience: {job.experience}</p>
        </section>
      </div>

      {kit && (
        <section className="card reveal mt-4 space-y-5">
          <h2 className="text-2xl font-extrabold">Your Apply Kit</h2>
          <div>
            <div className="mb-2 flex items-center justify-between"><h3 className="font-bold">Cover note</h3><CopyButton text={kit.note} /></div>
            <pre className="whitespace-pre-wrap rounded-xl bg-cream p-4 font-sans text-sm">{kit.note}</pre>
          </div>
          <div>
            <h3 className="mb-2 font-bold">Skills to highlight</h3>
            <div className="flex flex-wrap gap-1.5">{kit.highlight.map((s) => <span key={s} className="chip bg-teal text-white">{s}</span>)}</div>
          </div>
          <div>
            <h3 className="mb-2 font-bold">Ready answers</h3>
            <div className="space-y-3">
              {kit.answers.map((a) => (
                <div key={a.q} className="rounded-xl bg-cream p-4">
                  <div className="flex items-center justify-between"><p className="text-sm font-semibold">{a.q}</p><CopyButton text={a.a} /></div>
                  <p className="mt-1 text-sm text-ink/70">{a.a}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
