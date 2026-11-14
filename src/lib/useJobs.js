import { useEffect, useMemo, useState } from "react";
import { matchJob } from "./match";
import { useStore } from "../store";

export function useJobs() {
  const { profile, apiFetch, user } = useStore();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadJobs() {
      if (!user) {
        setJobs([]);
        setLoading(false);
        return;
      }

      setLoading(true);
      setError("");

      try {
        const data = await apiFetch("/jobs/");
        if (active) {
          setJobs(Array.isArray(data) ? data : []);
          setError("");
        }
      } catch (err) {
        if (active) {
          console.error("Jobs fetch error:", err);
          setError("Failed to load jobs from backend. Please ensure you are logged in and the server is running.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadJobs();

    return () => {
      active = false;
    };
  }, [apiFetch, user]);

  const matchedJobs = useMemo(() => {
    const names = (profile?.skills || []).map((s) => (typeof s === "string" ? s : s.name));

    return jobs
      .map((job) => {
        const compatibleJob = {
          ...job,
          skills: job.skills || job.required_skills || [],
        };

        return {
          ...compatibleJob,
          match: matchJob(compatibleJob, names),
        };
      })
      .sort((a, b) => (b.match.score ?? -1) - (a.match.score ?? -1));
  }, [jobs, profile]);

  return { jobs: matchedJobs, loading, error };
}
