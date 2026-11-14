import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { supabase } from "./lib/supabase";
import { today } from "./lib/match";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

const initialStore = {
  user: null,
  profile: null,
  tracker: [],
  company: null,
  postedJobs: [],
  decisions: {},
  loading: true,
  error: null,
};

const Ctx = createContext(null);

export function StoreProvider({ children }) {
  const [state, setState] = useState(initialStore);

  // Helper for authenticated backend API requests
  const apiFetch = useCallback(async (path, options = {}) => {
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;

    if (!token) {
      throw new Error("No active authentication session. Please log in.");
    }

    const headers = {
      ...(options.headers || {}),
      Authorization: `Bearer ${token}`,
    };

    if (options.body && typeof options.body === "string" && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const url = path.startsWith("http") ? path : `${API}${path.startsWith("/") ? "" : "/"}${path}`;
    const res = await fetch(url, { ...options, headers });

    if (res.status === 401) {
      // Try token refresh once
      const { data: refreshed, error: refreshErr } = await supabase.auth.refreshSession();
      if (!refreshErr && refreshed?.session?.access_token) {
        headers.Authorization = `Bearer ${refreshed.session.access_token}`;
        const retryRes = await fetch(url, { ...options, headers });
        if (!retryRes.ok) {
          const errData = await retryRes.json().catch(() => ({}));
          throw new Error(errData.error || `Request failed with status ${retryRes.status}`);
        }
        return retryRes.json().catch(() => ({}));
      }
    }

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error || `Request failed with status ${res.status}`);
    }

    return res.json().catch(() => ({}));
  }, []);

  // Load user data based on role
  const loadUserData = useCallback(async (authUser) => {
    try {
      // Query profiles table for role and profile info
      const { data: profileRow, error: pErr } = await supabase
        .from("profiles")
        .select("id, role, requested_role, name, email, completed")
        .eq("auth_user_id", authUser.id)
        .maybeSingle();

      if (pErr) {
        console.error("Profile fetch error:", pErr);
      }

      const role = profileRow?.role || "student";
      const requestedRole = profileRow?.requested_role || null;
      const userObj = {
        id: authUser.id,
        email: authUser.email,
        name: profileRow?.name || authUser.user_metadata?.name || authUser.email?.split("@")[0] || "",
        role,
        requested_role: requestedRole,
      };

      if (role === "student") {
        // Fetch student profile and tracker from Flask API
        let studentProfile = null;
        let trackerItems = [];

        try {
          const students = await apiFetch("/students/");
          if (Array.isArray(students) && students.length > 0) {
            studentProfile = students[0];
          }
        } catch (e) {
          console.warn("Could not fetch student profile from API:", e.message);
        }

        try {
          const trackerRes = await apiFetch("/tracker/");
          if (Array.isArray(trackerRes)) {
            trackerItems = trackerRes;
          }
        } catch (e) {
          console.warn("Could not fetch tracker items from API:", e.message);
        }

        const finalProfile = studentProfile || {
          name: userObj.name,
          email: userObj.email,
          role: "student",
          completed: profileRow?.completed || false,
          skills: [],
          projects: [],
        };

        if (profileRow?.completed && !finalProfile.completed) {
          finalProfile.completed = true;
        }

        setState((s) => ({
          ...s,
          user: userObj,
          profile: finalProfile,
          tracker: trackerItems,
          company: null,
          postedJobs: [],
          loading: false,
        }));

        return { user: userObj, profile: finalProfile, company: null };
      } else if (role === "recruiter") {
        // Fetch company and posted jobs from Flask API
        let companyData = null;
        let jobsData = [];

        try {
          const cRes = await apiFetch("/company/");
          if (cRes && Object.keys(cRes).length > 0) {
            companyData = cRes;
          }
        } catch (e) {
          console.warn("Could not fetch company profile from API:", e.message);
        }

        try {
          const jRes = await apiFetch("/jobs/");
          if (Array.isArray(jRes)) {
            jobsData = jRes;
          }
        } catch (e) {
          console.warn("Could not fetch recruiter jobs from API:", e.message);
        }

        setState((s) => ({
          ...s,
          user: userObj,
          profile: null,
          tracker: [],
          company: companyData,
          postedJobs: jobsData,
          loading: false,
        }));

        return { user: userObj, profile: null, company: companyData, postedJobs: jobsData };
      }
    } catch (err) {
      console.error("Error loading user data:", err);
      const fallbackUser = {
        id: authUser.id,
        email: authUser.email,
        name: authUser.user_metadata?.name || authUser.email?.split("@")[0] || "",
        role: "student",
        requested_role: null,
      };
      const fallbackProfile = {
        name: fallbackUser.name,
        email: fallbackUser.email,
        role: "student",
        completed: false,
        skills: [],
        projects: [],
      };
      setState((s) => ({
        ...s,
        user: fallbackUser,
        profile: fallbackProfile,
        loading: false,
        error: err.message,
      }));
      return { user: fallbackUser, profile: fallbackProfile, company: null };
    }
  }, [apiFetch]);

  // Listen to Supabase auth state changes
  useEffect(() => {
    let mounted = true;

    async function initAuth() {
      try {
        const { data: { session }, error } = await supabase.auth.getSession();
        if (error) {
          console.error("Auth session error:", error);
          if (mounted) setState((s) => ({ ...s, loading: false }));
          return;
        }

        if (session?.user && mounted) {
          await loadUserData(session.user);
        } else if (mounted) {
          setState((s) => ({ ...s, user: null, profile: null, loading: false }));
        }
      } catch (err) {
        console.error("Auth initialization error:", err);
        if (mounted) setState((s) => ({ ...s, loading: false }));
      }
    }

    initAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (!mounted) return;
        if (event === "INITIAL_SESSION") return; // handled by initAuth
        if ((event === "SIGNED_IN" || event === "TOKEN_REFRESHED") && session?.user) {
          // Defer: awaiting Supabase calls inside this callback deadlocks the auth lock
          setTimeout(() => { if (mounted) loadUserData(session.user); }, 0);
        } else if (event === "SIGNED_OUT") {
          setState({
            ...initialStore,
            loading: false,
          });
        }
      }
    );

    return () => {
      mounted = false;
      subscription?.unsubscribe();
    };
  }, [loadUserData]);

  const api = {
    ...state,
    apiFetch,

    // Supabase Sign Up
    async signup({ email, password, name, role = "student" }) {
      setState((s) => ({ ...s, loading: true, error: null }));
      try {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: {
              name,
              role,
              requested_role: role === "recruiter" ? "recruiter" : undefined,
            },
          },
        });

        if (error) throw error;

        // If session was established directly (auto-confirm enabled)
        if (data.session && data.user) {
          const loaded = await loadUserData(data.user);
          return {
            user: loaded?.user || data.user,
            session: data.session,
            profile: loaded?.profile || null,
            company: loaded?.company || null,
            needsConfirmation: false,
          };
        }

        // Email confirmation is required
        setState((s) => ({ ...s, loading: false }));
        return {
          user: data.user,
          session: null,
          needsConfirmation: true,
          message: "Account created! Please check your email to confirm your account before logging in.",
        };
      } catch (err) {
        setState((s) => ({ ...s, loading: false, error: err.message }));
        throw err;
      }
    },

    // Supabase Sign In
    async login({ email, password }) {
      setState((s) => ({ ...s, loading: true, error: null }));
      try {
        const { data, error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });

        if (error) throw error;

        let loaded = null;
        if (data.user) {
          loaded = await loadUserData(data.user);
        }
        return {
          user: loaded?.user || data.user,
          session: data.session,
          profile: loaded?.profile || null,
          company: loaded?.company || null,
        };
      } catch (err) {
        setState((s) => ({ ...s, loading: false, error: err.message }));
        throw err;
      }
    },

    // Sign Out
    async logout() {
      try {
        await supabase.auth.signOut();
      } catch (err) {
        console.error("SignOut error:", err);
      } finally {
        setState({
          ...initialStore,
          loading: false,
        });
      }
    },

    // Save Student Profile via Flask API
    async saveProfile(profileData) {
      try {
        const email = profileData.email || state.user?.email;
        const res = await apiFetch(`/students/${encodeURIComponent(email)}`, {
          method: "PUT",
          body: JSON.stringify(profileData),
        });

        const saved = res.student || profileData;
        const completeSaved = { ...saved, completed: true };
        setState((s) => ({
          ...s,
          profile: completeSaved,
        }));
        return completeSaved;
      } catch (err) {
        // Fallback to POST /students/ if PUT returned 404 or profile not found yet
        try {
          const postRes = await apiFetch("/students/", {
            method: "POST",
            body: JSON.stringify(profileData),
          });
          const saved = postRes.student || profileData;
          const completeSaved = { ...saved, completed: true };
          setState((s) => ({
            ...s,
            profile: completeSaved,
          }));
          return completeSaved;
        } catch (postErr) {
          console.error("Profile save error:", postErr);
          throw postErr;
        }
      }
    },

    // Add job to tracker
    async track(job, status = "saved") {
      const jobId = String(job.id);
      const exists = state.tracker.some(
        (item) => String(item.job_id ?? item.job?.id ?? item.id) === jobId
      );
      if (exists) return;

      const payload = {
        job_id: jobId,
        status: String(status).toLowerCase(),
        notes: "",
        applied_at: status === "applied" ? today() : null,
      };

      try {
        const data = await apiFetch("/tracker/", {
          method: "POST",
          body: JSON.stringify(payload),
        });

        setState((s) => ({
          ...s,
          tracker: s.tracker.some((t) => String(t.job_id) === String(data.job_id))
            ? s.tracker
            : [...s.tracker, data],
        }));
        return data;
      } catch (err) {
        console.error("Tracker track error:", err);
        throw err;
      }
    },

    // Update tracker status
    async setStatus(id, status) {
      try {
        const payload = {
          status,
          ...(status === "applied" ? { applied_at: today() } : {}),
        };
        const updated = await apiFetch(`/tracker/${encodeURIComponent(id)}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });

        setState((s) => ({
          ...s,
          tracker: s.tracker.map((item) =>
            String(item.id) === String(id) ? { ...item, ...updated, status } : item
          ),
        }));
        return updated;
      } catch (err) {
        console.error("Status update error:", err);
        throw err;
      }
    },

    // Update tracker notes
    async setNotes(id, notes) {
      try {
        const updated = await apiFetch(`/tracker/${encodeURIComponent(id)}`, {
          method: "PUT",
          body: JSON.stringify({ notes }),
        });

        setState((s) => ({
          ...s,
          tracker: s.tracker.map((item) =>
            String(item.id) === String(id) ? { ...item, ...updated, notes } : item
          ),
        }));
        return updated;
      } catch (err) {
        console.error("Notes update error:", err);
        throw err;
      }
    },

    // Untrack application
    async untrack(id) {
      try {
        await apiFetch(`/tracker/${encodeURIComponent(id)}`, {
          method: "DELETE",
        });

        setState((s) => ({
          ...s,
          tracker: s.tracker.filter((item) => String(item.id) !== String(id)),
        }));
      } catch (err) {
        console.error("Tracker delete error:", err);
        throw err;
      }
    },

    // Recruiter: Save company
    async saveCompany(patch) {
      const companyPayload = {
        name: patch.name || state.company?.name || "",
        website: patch.website !== undefined ? patch.website : state.company?.website || "",
        location: patch.location !== undefined ? patch.location : state.company?.location || "",
        size: patch.size !== undefined ? patch.size : state.company?.size || "",
        about: patch.about !== undefined ? patch.about : state.company?.about || "",
      };

      try {
        const res = await apiFetch("/company/", {
          method: "POST",
          body: JSON.stringify(companyPayload),
        });

        const savedCompany = res.company || companyPayload;
        setState((s) => ({
          ...s,
          company: savedCompany,
        }));
        return savedCompany;
      } catch (err) {
        console.error("Company save error:", err);
        throw err;
      }
    },

    // Recruiter: Post job
    async postJob(job) {
      const jobPayload = {
        title: job.title,
        location: job.location || "Not specified",
        type: job.type || "Full-time",
        remote: Boolean(job.remote),
        salary: job.salary || "Not disclosed",
        experience: job.experience || "0-1 years",
        description: job.description || "",
        skills: job.skills || [],
        apply_url: job.apply_url || state.company?.website || "",
        posted_at: today(),
      };

      try {
        const res = await apiFetch("/jobs/", {
          method: "POST",
          body: JSON.stringify(jobPayload),
        });

        const newJob = res.job || res;
        setState((s) => ({
          ...s,
          postedJobs: [...s.postedJobs, newJob],
        }));
        return newJob;
      } catch (err) {
        console.error("Job posting error:", err);
        throw err;
      }
    },

    // Recruiter: Remove job
    async removeJob(id) {
      try {
        await apiFetch(`/jobs/${encodeURIComponent(id)}`, {
          method: "DELETE",
        });

        setState((s) => {
          const updatedDecisions = { ...s.decisions };
          Object.keys(updatedDecisions).forEach((key) => {
            if (key.startsWith(`${id}:`)) {
              delete updatedDecisions[key];
            }
          });

          return {
            ...s,
            postedJobs: s.postedJobs.filter((job) => String(job.id) !== String(id)),
            decisions: updatedDecisions,
          };
        });
      } catch (err) {
        console.error("Job deletion error:", err);
        throw err;
      }
    },

    // Recruiter: Load candidate decisions
    async loadDecisions(jobId) {
      try {
        const data = await apiFetch(`/jobs/${encodeURIComponent(jobId)}/decisions/`);
        setState((s) => ({
          ...s,
          decisions: {
            ...s.decisions,
            ...(data || {}),
          },
        }));
        return data;
      } catch (err) {
        console.error("Decision fetch error:", err);
      }
    },

    // Recruiter: Update candidate decision
    async decide(jobId, candId, status) {
      const key = `${jobId}:${candId}`;
      try {
        const res = await apiFetch(`/jobs/${encodeURIComponent(jobId)}/decisions/`, {
          method: "POST",
          body: JSON.stringify({
            candidate_id: candId,
            status,
          }),
        });

        setState((s) => {
          const updatedDecisions = { ...s.decisions };
          if (status === null) {
            delete updatedDecisions[key];
          } else {
            updatedDecisions[key] = status;
          }
          return {
            ...s,
            decisions: res.decisions || updatedDecisions,
          };
        });
      } catch (err) {
        console.error("Decision error:", err);
        throw err;
      }
    },
  };

  return <Ctx.Provider value={api}>{children}</Ctx.Provider>;
}

export function useStore() {
  return useContext(Ctx);
}