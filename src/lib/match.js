// The matching logic. The Python backend will do this later; the result shape is the same:
// { score, matched, missing }  (see claude/backend-pipeline.md)
export function matchJob(job, skillNames) {
  const mine = new Set(skillNames.map((s) => s.toLowerCase()));
  const matched = job.skills.filter((s) => mine.has(s.toLowerCase()));
  const missing = job.skills.filter((s) => !mine.has(s.toLowerCase()));
  const score = job.skills.length ? Math.round((100 * matched.length) / job.skills.length) : null;
  return { score, matched, missing };
}

export function profileStrength(p) {
  if (!p) return 0;
  let pts = 0;
  if (p.name && p.college && p.course && p.year) pts += 25;
  if ((p.skills || []).length >= 3) pts += 25;
  if ((p.projects || []).some((x) => x.title)) pts += 20;
  if (p.links && (p.links.github || p.links.linkedin || p.links.portfolio)) pts += 15;
  if (p.cv_name) pts += 15;
  return pts;
}

export const today = () => new Date().toISOString().slice(0, 10);
export const daysSince = (iso) => (iso ? Math.floor((Date.now() - new Date(iso).getTime()) / 86400000) : 0);
export const prettyDate = (iso) =>
  new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
