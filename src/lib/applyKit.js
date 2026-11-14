// Template-based Apply Kit. The backend can swap this for an AI-written version later.
export function buildApplyKit(job, profile, match) {
  const first = (profile.name || "there").split(" ")[0];
  const top = match.matched.slice(0, 3).join(", ") || "my core skills";
  const project = (profile.projects || []).find((p) => p.title);
  const note =
    `Hi ${job.company} team,\n\n` +
    `I'm ${profile.name || first}, a ${profile.year || "student"} at ${profile.college || "my college"} studying ${profile.course || "my course"}. ` +
    `I'm excited about the ${job.title} role because it uses ${top}, which I've been building skills in.\n\n` +
    (project ? `Recently I worked on "${project.title}"${project.description ? `: ${project.description}` : ""}. ` : "") +
    (match.missing.length ? `I'm actively learning ${match.missing.slice(0, 2).join(" and ")} and pick up new tools quickly.\n\n` : "\n\n") +
    `Thank you for your time. I'd love to talk.\n\n${profile.name || ""}`;
  const answers = [
    { q: "Why do you want this role?", a: `It matches my skills in ${top} and gives me hands-on experience at ${job.company}.` },
    { q: "Tell us about yourself.", a: `I'm a ${profile.year || "student"} at ${profile.college || "college"} (${profile.course || "course"}) with skills in ${(profile.skills || []).slice(0, 4).map((s) => s.name).join(", ")}.` },
    { q: "Describe a project you're proud of.", a: project ? `${project.title}. ${project.description || ""}` : "Add a project to your profile to auto-fill this answer." },
  ];
  return { note, highlight: match.matched, answers };
}

export const followUpMessage = (job, profile) =>
  `Hi ${job.company} team,\n\nI applied for the ${job.title} role and wanted to follow up. I'm still very interested and happy to share anything else that helps.\n\nThank you,\n${profile?.name || ""}`;
