import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowRight, Plus, Upload, X } from "lucide-react";
import { useStore } from "../store";
import { SKILLS } from "../data/skills";

const YEARS = ["1st year", "2nd year", "3rd year", "Final year", "Graduated"];
const TYPES = ["Internship", "Full-time", "Part-time", "Contract"];
const STEPS = ["About you", "Skills", "Projects & links", "Preferences"];
const blank = {
  name: "", college: "", course: "", year: "", graduation_year: "",
  skills: [], projects: [{ title: "", description: "", link: "" }],
  links: { linkedin: "", github: "", portfolio: "" }, cv_name: "",
  preferences: { types: ["Internship"], remote: false, locations: "" },
};

export default function Onboarding({ editing = false }) {
  const { user, profile, saveProfile } = useStore();
  const nav = useNavigate();
  const [step, setStep] = useState(0);
  // The backend returns null / {} / [] for empty fields, so merge onto safe defaults
  // (otherwise f.preferences.types is undefined and the page crashes at the last step).
  const [f, setF] = useState(() => {
    const p = profile || {};
    const str = (v) => (typeof v === "string" ? v : "");
    return {
      ...blank,
      ...p,
      name: str(p.name) || user?.name || "",
      college: str(p.college),
      course: str(p.course),
      year: str(p.year),
      graduation_year: str(p.graduation_year),
      cv_name: str(p.cv_name),
      skills: Array.isArray(p.skills) ? p.skills : [],
      projects: Array.isArray(p.projects) && p.projects.length > 0
        ? p.projects.map((x) => ({ title: x.title || "", description: x.description || "", link: x.link || "" }))
        : [{ title: "", description: "", link: "" }],
      links: { ...blank.links, ...(p.links || {}) },
      preferences: {
        ...blank.preferences,
        ...(p.preferences || {}),
        types: Array.isArray(p.preferences?.types) ? p.preferences.types : blank.preferences.types,
        locations: typeof p.preferences?.locations === "string" ? p.preferences.locations : "",
      },
      email: user?.email || "",
    };
  });
  const [q, setQ] = useState("");
  const [detected, setDetected] = useState([]);
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));

  const has = (name) => f.skills.some((s) => s.name === name);
  // Functional update so adding several skills in a row (CV upload) keeps all of them.
  const addSkill = (name) =>
    setF((p) => (p.skills.some((s) => s.name === name) ? p : { ...p, skills: [...p.skills, { name, level: "Beginner" }] }));
  const removeSkill = (name) => set("skills", f.skills.filter((s) => s.name !== name));
  const toggleLevel = (name) =>
    set("skills", f.skills.map((s) => (s.name === name ? { ...s, level: s.level === "Beginner" ? "Intermediate" : "Beginner" } : s)));

  // DEMO parser: the real one is Python (POST /me/cv). Here we just pretend to detect a few skills.
  function onCv(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    set("cv_name", file.name);
    const found = ["Python", "SQL", "Git"];
    setDetected(found);
    found.forEach(addSkill);
  }

  const canNext = [f.name.trim() && f.year, f.skills.length > 0, true, true][step];
  const matches = SKILLS.filter((s) => !has(s) && s.toLowerCase().includes(q.toLowerCase())).slice(0, 12);


   async function finish() {
     try {
       const updatedProfile = {
         name: f.name.trim(),
         email: f.email,
         college: f.college,
         course: f.course,
         year: f.year,
         graduation_year: f.graduation_year,
         cv_name: f.cv_name,
         skills: f.skills,
         projects: f.projects,
         links: f.links,
         preferences: f.preferences,
         completed: true,
         recruitment_visible: typeof f.recruitment_visible === "boolean" ? f.recruitment_visible : true,
       };

       await saveProfile(updatedProfile);
       nav(editing ? "/dashboard" : "/dashboard", { replace: true });
     } catch (error) {
       console.error("Backend error:", error);
       alert(error.message || "Profile save failed. Please check your connection and try again.");
     }
   }



  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <div className="mb-8 flex items-end justify-between">
        <span className="font-display text-7xl font-extrabold leading-none text-coral">0{step + 1}</span>
        <p className="text-sm font-medium text-ink/60">{STEPS[step]} · step {step + 1} of {STEPS.length}</p>
      </div>
      <div className="mb-8 h-1.5 overflow-hidden rounded-full bg-line"><div className="h-full bg-ink transition-all" style={{ width: `${((step + 1) / STEPS.length) * 100}%` }} /></div>

      <div className="card space-y-4">
        {step === 0 && (
          <>
            <h2 className="text-2xl font-extrabold">About you</h2>
            <input className="input" placeholder="Full name *" value={f.name} onChange={(e) => set("name", e.target.value)} />
            <input className="input" placeholder="College" value={f.college} onChange={(e) => set("college", e.target.value)} />
            <input className="input" placeholder="Course / branch (e.g. B.Tech AI & ML)" value={f.course} onChange={(e) => set("course", e.target.value)} />
            <div>
              <p className="mb-2 text-sm font-medium">Which year are you in? *</p>
              <div className="flex flex-wrap gap-2">
                {YEARS.map((y) => (
                  <button key={y} type="button" onClick={() => set("year", y)}
                    className={`chip !px-4 !py-2 ${f.year === y ? "bg-ink text-cream" : "border border-line"}`}>{y}</button>
                ))}
              </div>
            </div>
            <input className="input" placeholder="Graduation year (e.g. 2027)" value={f.graduation_year} onChange={(e) => set("graduation_year", e.target.value)} />
          </>
        )}

        {step === 1 && (
          <>
            <h2 className="text-2xl font-extrabold">Your skills</h2>
            <label className="flex cursor-pointer items-center gap-3 rounded-xl border-2 border-dashed border-line p-4 hover:bg-cream">
              <Upload className="text-coral" />
              <span className="text-sm"><b>{f.cv_name || "Upload your CV (PDF)"}</b><br /><span className="text-ink/60">We'll detect your skills. (Demo: the real parser comes with the backend.)</span></span>
              <input type="file" accept=".pdf,.doc,.docx" className="hidden" onChange={onCv} />
            </label>
            {detected.length > 0 && <p className="text-sm text-teal">Detected: {detected.join(", ")}. Edit below if needed.</p>}

            <input className="input" placeholder="Search skills to add..." value={q} onChange={(e) => setQ(e.target.value)} />
            <div className="flex flex-wrap gap-2">
              {matches.map((s) => (
                <button key={s} type="button" onClick={() => addSkill(s)} className="chip border border-line hover:bg-ink hover:text-cream"><Plus size={12} className="mr-1" />{s}</button>
              ))}
            </div>
            <div>
              <p className="mb-2 text-sm font-medium">Selected ({f.skills.length}). Click a level to switch it.</p>
              <div className="flex flex-wrap gap-2">
                {f.skills.map((s) => (
                  <span key={s.name} className="chip gap-2 bg-teal text-white">
                    {s.name}
                    <button type="button" onClick={() => toggleLevel(s.name)} className="rounded-full bg-white/20 px-2">{s.level}</button>
                    <button type="button" aria-label={`Remove ${s.name}`} onClick={() => removeSkill(s.name)}><X size={12} /></button>
                  </span>
                ))}
                {f.skills.length === 0 && <span className="text-sm text-ink/50">Add at least one skill to continue.</span>}
              </div>
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <h2 className="text-2xl font-extrabold">Projects & links</h2>
            {f.projects.map((p, i) => (
              <div key={i} className="space-y-2 rounded-xl bg-cream p-4">
                <input className="input" placeholder="Project title" value={p.title} onChange={(e) => set("projects", f.projects.map((x, j) => (j === i ? { ...x, title: e.target.value } : x)))} />
                <textarea className="input" rows={2} placeholder="One-line description" value={p.description} onChange={(e) => set("projects", f.projects.map((x, j) => (j === i ? { ...x, description: e.target.value } : x)))} />
                <input className="input" placeholder="Link (GitHub / demo)" value={p.link} onChange={(e) => set("projects", f.projects.map((x, j) => (j === i ? { ...x, link: e.target.value } : x)))} />
              </div>
            ))}
            <button type="button" className="btn-line" onClick={() => set("projects", [...f.projects, { title: "", description: "", link: "" }])}><Plus size={14} /> Add another project</button>
            {["linkedin", "github", "portfolio"].map((k) => (
              <input key={k} className="input" placeholder={`${k[0].toUpperCase() + k.slice(1)} URL`} value={f.links[k]} onChange={(e) => set("links", { ...f.links, [k]: e.target.value })} />
            ))}
          </>
        )}

        {step === 3 && (
          <>
            <h2 className="text-2xl font-extrabold">What are you looking for?</h2>
            <div className="flex flex-wrap gap-2">
              {TYPES.map((t) => {
                const on = f.preferences.types.includes(t);
                return (
                  <button key={t} type="button"
                    onClick={() => set("preferences", { ...f.preferences, types: on ? f.preferences.types.filter((x) => x !== t) : [...f.preferences.types, t] })}
                    className={`chip !px-4 !py-2 ${on ? "bg-ink text-cream" : "border border-line"}`}>{t}</button>
                );
              })}
            </div>
            <label className="flex items-center gap-2 text-sm font-medium">
              <input type="checkbox" checked={f.preferences.remote} onChange={(e) => set("preferences", { ...f.preferences, remote: e.target.checked })} /> Remote only
            </label>
            <input className="input" placeholder="Preferred cities (e.g. Bengaluru, Pune)" value={f.preferences.locations} onChange={(e) => set("preferences", { ...f.preferences, locations: e.target.value })} />
          </>
        )}
      </div>

      <div className="mt-6 flex justify-between">
        <button className="btn-line" onClick={() => setStep(step - 1)} disabled={step === 0}><ArrowLeft size={16} /> Back</button>
        {step < STEPS.length - 1 ? (
          <button className="btn-ink" onClick={() => setStep(step + 1)} disabled={!canNext}>Next <ArrowRight size={16} /></button>
        ) : (
          <button className="btn-coral" onClick={finish}>{editing ? "Save profile" : "Finish & see my matches"} <ArrowRight size={16} /></button>
        )}
      </div>
    </div>
  );
}