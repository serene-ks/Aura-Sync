import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useStore } from "../../store";
import SkillPicker from "../../components/SkillPicker";

const TYPES = ["Internship", "Full-time", "Part-time", "Contract"];

// Creates a job in the same shape as src/data/jobs.json, so students see it in /jobs.
// With the backend this becomes POST /employer/jobs.
export default function PostJob() {
  const { postJob } = useStore();
  const nav = useNavigate();
  const [f, setF] = useState({ title: "", type: "Internship", location: "", remote: false, salary: "", experience: "0-1 years", description: "", skills: [] });
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const valid = f.title.trim() && f.location.trim() && f.description.trim() && f.skills.length > 0;

  async function submit(e) {
    e.preventDefault();

    try {
      await postJob({
        ...f,
        salary: f.salary.trim() || "Not disclosed",
      });

      nav("/recruiter");
    } catch (err) {
      alert("Job post nahi hui. Please try again.");
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <span className="font-display text-7xl font-extrabold leading-none text-teal">02</span>
      <h1 className="mt-2 text-3xl font-extrabold tracking-tight">Post a job</h1>
      <p className="mt-1 text-ink/60">Required skills decide which students match, so pick them carefully.</p>

      <form onSubmit={submit} className="card mt-6 space-y-4">
        <label className="block text-sm font-medium">Job title *
          <input className="input mt-1" value={f.title} onChange={set("title")} placeholder="Frontend Developer Intern" />
        </label>
        <div>
          <p className="mb-2 text-sm font-medium">Type</p>
          <div className="flex flex-wrap gap-2">
            {TYPES.map((t) => (
              <button key={t} type="button" onClick={() => setF({ ...f, type: t })}
                className={`chip !px-4 !py-2 ${f.type === t ? "bg-ink text-cream" : "border border-line"}`}>{t}</button>
            ))}
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm font-medium">Location *
            <input className="input mt-1" value={f.location} onChange={set("location")} placeholder="Pune, India" />
          </label>
          <label className="block text-sm font-medium">Salary / stipend
            <input className="input mt-1" value={f.salary} onChange={set("salary")} placeholder="₹20,000 / month" />
          </label>
        </div>
        <label className="flex items-center gap-2 text-sm font-medium">
          <input type="checkbox" checked={f.remote} onChange={(e) => setF({ ...f, remote: e.target.checked })} /> Remote friendly
        </label>
        <label className="block text-sm font-medium">Experience
          <input className="input mt-1" value={f.experience} onChange={set("experience")} />
        </label>
        <label className="block text-sm font-medium">Description *
          <textarea className="input mt-1" rows={4} value={f.description} onChange={set("description")} placeholder="What will the student do?" />
        </label>
        <div>
          <p className="mb-2 text-sm font-medium">Required skills *</p>
          <SkillPicker value={f.skills} onChange={(skills) => setF({ ...f, skills })} />
        </div>
        <button className="btn-coral" disabled={!valid}>Publish job</button>
      </form>
    </div>
  );
}
