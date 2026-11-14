import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { useStore } from "../store";
import { useJobs } from "../lib/useJobs";
import { profileStrength } from "../lib/match";
import JobCard from "../components/JobCard";

export default function Dashboard() {
  const { profile, tracker } = useStore();
  const { jobs, loading, error } = useJobs();
  const strength = profileStrength(profile);
  const count = (s) => tracker.filter((t) => t.status === s).length;
  const first = (profile.name || "").split(" ")[0];
  const tiles = [
    { label: "Saved", n: count("saved"), bg: "bg-paper" },
    { label: "Applied", n: count("applied"), bg: "bg-teal text-white" },
    { label: "Interviews", n: count("interview"), bg: "bg-mustard" },
    { label: "Offers", n: count("offer"), bg: "bg-coral text-white" },
  ];

  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <h1 className="reveal text-4xl font-extrabold tracking-tight sm:text-5xl">Hi {first}, here's what fits you.</h1>

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        <div className="card reveal md:col-span-1" style={{ animationDelay: "80ms" }}>
          <p className="text-sm font-medium text-ink/60">Profile strength</p>
          <p className="font-display text-6xl font-extrabold">{strength}%</p>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-line"><div className="h-full bg-coral transition-all duration-700" style={{ width: `${strength}%` }} /></div>
          <p className="mt-3 text-sm text-ink/60">{strength < 100 ? "Add a project, links and your CV to improve your matches." : "Your profile is complete."}</p>
          <Link to="/profile" className="mt-4 inline-block text-sm font-semibold underline">Edit profile</Link>
        </div>
        <div className="grid grid-cols-2 gap-4 md:col-span-2 md:grid-cols-4">
          {tiles.map((t, i) => (
            <Link to="/tracker" key={t.label} className={`reveal rounded-xl2 border border-line p-5 transition hover:-translate-y-1 ${t.bg}`} style={{ animationDelay: `${120 + i * 70}ms` }}>
              <p className="font-display text-5xl font-extrabold">{t.n}</p>
              <p className="mt-1 text-sm font-medium opacity-80">{t.label}</p>
            </Link>
          ))}
        </div>
      </div>

      <div className="mb-4 mt-12 flex items-end justify-between">
        <h2 className="text-2xl font-extrabold">Top matches for you</h2>
        <Link to="/jobs" className="inline-flex items-center gap-1 text-sm font-semibold underline">See all jobs <ArrowRight size={14} /></Link>
      </div>

       <div className="grid gap-4">
         {loading && <p>Loading jobs...</p>}

         {!loading && error && (
           <p className="text-coral">{error}. Please check whether the backend is running.</p>
         )}

         {!loading && !error && jobs.length === 0 && (
           <p>No jobs available right now.</p>
         )}

         {!loading && !error && jobs.slice(0, 3).map((j, i) => (
           <JobCard key={j.id} job={j} delay={i * 100} />
         ))}
              </div>
            </div>
          );
        }


