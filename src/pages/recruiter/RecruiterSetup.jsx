import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { useStore } from "../../store";

const SIZES = ["1-10", "11-50", "51-200", "201-1000", "1000+"];

// One short form: who is hiring. Also used to edit the company later.
export default function RecruiterSetup() {
  const { company, saveCompany } = useStore();
  const nav = useNavigate();
  const [f, setF] = useState({ name: "", website: "", location: "", size: "", about: "", ...(company || {}) });
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  function submit(e) {
    e.preventDefault();
    saveCompany(f);
    nav("/recruiter");
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <span className="font-display text-7xl font-extrabold leading-none text-coral">01</span>
      <h1 className="mt-2 text-3xl font-extrabold tracking-tight">Tell students who's hiring</h1>
      <form onSubmit={submit} className="card mt-6 space-y-4">
        <label className="block text-sm font-medium">Company name *
          <input className="input mt-1" value={f.name} onChange={set("name")} placeholder="Orbit Analytics" />
        </label>
        <label className="block text-sm font-medium">Website
          <input className="input mt-1" value={f.website} onChange={set("website")} placeholder="https://company.com/careers" />
        </label>
        <label className="block text-sm font-medium">Headquarters
          <input className="input mt-1" value={f.location} onChange={set("location")} placeholder="Bengaluru, India" />
        </label>
        <div>
          <p className="mb-2 text-sm font-medium">Company size</p>
          <div className="flex flex-wrap gap-2">
            {SIZES.map((s) => (
              <button key={s} type="button" onClick={() => setF({ ...f, size: s })}
                className={`chip !px-4 !py-2 ${f.size === s ? "bg-ink text-cream" : "border border-line"}`}>{s}</button>
            ))}
          </div>
        </div>
        <label className="block text-sm font-medium">About the company
          <textarea className="input mt-1" rows={3} value={f.about} onChange={set("about")} placeholder="Two lines students will read before applying." />
        </label>
        <button className="btn-coral" disabled={!f.name.trim()}>Save and continue <ArrowRight size={16} /></button>
      </form>
    </div>
  );
}
