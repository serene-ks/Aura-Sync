import { useState } from "react";
import { Plus, X } from "lucide-react";
import { SKILLS } from "../data/skills";

// Simple multi-select of skill names. `value` is an array of strings; `onChange` gets the new array.
export default function SkillPicker({ value, onChange }) {
  const [q, setQ] = useState("");
  const options = SKILLS.filter((s) => !value.includes(s) && s.toLowerCase().includes(q.toLowerCase())).slice(0, 12);
  return (
    <div className="space-y-3">
      <input className="input" placeholder="Search skills to require..." value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search skills" />
      <div className="flex flex-wrap gap-2">
        {options.map((s) => (
          <button key={s} type="button" onClick={() => onChange([...value, s])} className="chip border border-line hover:bg-ink hover:text-cream">
            <Plus size={12} className="mr-1" />{s}
          </button>
        ))}
      </div>
      <div className="flex min-h-[2rem] flex-wrap gap-2">
        {value.map((s) => (
          <span key={s} className="chip gap-1.5 bg-teal text-white">
            {s}
            <button type="button" aria-label={`Remove ${s}`} onClick={() => onChange(value.filter((x) => x !== s))}><X size={12} /></button>
          </span>
        ))}
        {value.length === 0 && <span className="text-sm text-ink/50">Pick at least one required skill.</span>}
      </div>
    </div>
  );
}
