// A circular percentage. Uses an SVG circle; strokeDashoffset hides the part not filled.
export default function MatchRing({ score, size = 64 }) {
  if (score == null) return <span className="chip bg-ink/10">No data</span>;
  const r = 26, c = 2 * Math.PI * r;
  const color = score >= 70 ? "#2D6A8A" : score >= 40 ? "#EBA52B" : "#F26440";
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }} aria-label={`${score}% match`}>
      <svg viewBox="0 0 64 64" className="-rotate-90">
        <circle cx="32" cy="32" r={r} fill="none" stroke="#E0D9CB" strokeWidth="6" />
        <circle cx="32" cy="32" r={r} fill="none" stroke={color} strokeWidth="6" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - score / 100)} style={{ transition: "stroke-dashoffset .8s ease" }} />
      </svg>
      <span className="absolute inset-0 grid place-items-center font-display text-sm font-bold">{score}%</span>
    </div>
  );
}
