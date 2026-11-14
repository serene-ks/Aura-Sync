import { Link } from "react-router-dom";
import { Trash2 } from "lucide-react";
import { useStore } from "../store";
import { daysSince, prettyDate } from "../lib/match";
import { followUpMessage } from "../lib/applyKit";

const COLUMNS = [
  { key: "saved", label: "Saved", bg: "bg-paper" },
  { key: "applied", label: "Applied", bg: "bg-teal/10" },
  { key: "interview", label: "Interview", bg: "bg-mustard/20" },
  { key: "offer", label: "Offer", bg: "bg-coral/10" },
  { key: "closed", label: "Closed", bg: "bg-ink/5" },
];

const STATUS_LABEL = {
  saved: "Saved",
  applied: "Applied",
  interview: "Interview",
  offer: "Offer",
  rejected: "Rejected",
  no_reply: "No reply",
};

const colOf = (s) => {
  const status = String(s || "saved").toLowerCase();

  return status === "rejected" || status === "no_reply"
    ? "closed"
    : status;
};

export default function Tracker() {
  const { tracker, profile, setStatus, setNotes, untrack } = useStore();

  if (tracker.length === 0) {
    return (
      <div className="mx-auto max-w-xl px-4 py-24 text-center">
        <span className="font-display text-8xl font-extrabold text-coral">
          00
        </span>

        <h1 className="mt-4 text-3xl font-extrabold">
          Nothing tracked yet
        </h1>

        <p className="mt-2 text-ink/60">
          Save a job to start your board.
        </p>

        <Link to="/jobs" className="btn-ink mt-6">
          Browse jobs
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1400px] px-4 py-12">
      <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
        Your tracker
      </h1>

      <p className="mt-2 text-ink/60">
        Use the dropdown on a card to move it. Applications with no reply after
        7 days get a follow-up nudge.
      </p>

      <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {COLUMNS.map((col) => {
          const items = tracker.filter(
            (t) => colOf(t.status) === col.key
          );

          return (
            <section
              key={col.key}
              className={`rounded-xl2 border border-line p-3 ${col.bg}`}
            >
              <h2 className="mb-3 flex items-center justify-between px-1 text-sm font-bold uppercase tracking-wider">
                {col.label}
                <span className="font-display text-lg">
                  {items.length}
                </span>
              </h2>

              <div className="space-y-3">
                {items.map((t, index) => {
                  const job = t.job || t;
                  const jobId = t.job_id ?? job.id;
                  const trackerId = t.id;

                  const status = String(
                    t.status || "saved"
                  ).toLowerCase();

                  const waiting =
                    status === "applied" && t.applied_at
                      ? daysSince(t.applied_at)
                      : 0;

                  return (
                    <article
                      key={trackerId || `tracker-${jobId || "unknown"}-${index}`}
                      className="rounded-xl bg-white p-4 shadow-sm"
                    >
                      <Link
                        to={`/jobs/${jobId}`}
                        className="font-display font-bold leading-tight hover:underline"
                      >
                        {job.title || "Job title unavailable"}
                      </Link>

                      <p className="text-sm text-ink/60">
                        {job.company || "Company unavailable"}
                      </p>

                      {t.applied_at && (
                        <p className="mt-1 text-xs text-ink/50">
                          Applied {prettyDate(t.applied_at)}
                        </p>
                      )}

                      {waiting >= 7 && (
                        <div className="mt-3 rounded-lg bg-coral/10 p-3 text-xs">
                          <p className="font-semibold text-coral">
                            No reply in {waiting} days. Follow up?
                          </p>

                          <button
                            className="mt-1 underline"
                            onClick={() =>
                              navigator.clipboard?.writeText(
                                followUpMessage(job, profile)
                              )
                            }
                          >
                            Copy follow-up message
                          </button>
                        </div>
                      )}

                      <select
                        className="input mt-3 !py-1.5 !text-xs"
                        value={status}
                        onChange={(e) =>
                          trackerId && setStatus(trackerId, e.target.value)
                        }
                        disabled={!trackerId}
                        aria-label="Move to"
                      >
                        {Object.entries(STATUS_LABEL).map(([k, v]) => (
                          <option key={k} value={k}>
                            {v}
                          </option>
                        ))}
                      </select>

                      <textarea
                        className="input mt-2 !py-1.5 !text-xs"
                        rows={2}
                        placeholder="Notes (recruiter, interview date...)"
                        value={t.notes || ""}
                        onChange={(e) =>
                          trackerId && setNotes(trackerId, e.target.value)
                        }
                        disabled={!trackerId}
                      />

                      <button
                        className="mt-2 inline-flex items-center gap-1 text-xs text-ink/50 hover:text-coral disabled:opacity-40"
                        onClick={() => trackerId && untrack(trackerId)}
                        disabled={!trackerId}
                      >
                        <Trash2 size={12} /> Remove
                      </button>
                    </article>
                  );
                })}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}