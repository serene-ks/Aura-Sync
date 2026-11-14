import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useStore } from "../store";

export default function Auth() {
  const { user, loading, login, signup, profile, company } = useStore();
  const nav = useNavigate();
  const [params] = useSearchParams();
  const [role, setRole] = useState(params.get("role") === "recruiter" ? "recruiter" : "student");
  const [mode, setMode] = useState(params.get("mode") === "signup" ? "signup" : "login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [submitting, setSubmitting] = useState(false);
  const [authError, setAuthError] = useState("");
  const [infoMessage, setInfoMessage] = useState("");

  // Sync mode and role if URL query parameters change
  useEffect(() => {
    const m = params.get("mode");
    if (m === "login" || m === "signup") {
      setMode(m);
    }
  }, [params]);

  useEffect(() => {
    const r = params.get("role");
    if (r === "recruiter" || r === "student") {
      setRole(r);
    }
  }, [params]);

  // If already authenticated, redirect to appropriate destination
  useEffect(() => {
    if (!loading && user) {
      const isPendingRecruiter = user.requested_role === "recruiter" && user.role !== "recruiter";
      if (isPendingRecruiter) {
        setInfoMessage("Your recruiter account is pending administrator approval.");
      } else if (user.role === "recruiter") {
        nav(company?.name ? "/recruiter" : "/recruiter/setup", { replace: true });
      } else {
        nav(profile?.completed ? "/dashboard" : "/onboarding", { replace: true });
      }
    }
  }, [user, profile, company, loading, nav]);

  const set = (k) => (e) => {
    setAuthError("");
    setInfoMessage("");
    setForm({ ...form, [k]: e.target.value });
  };

  const valid = form.email.includes("@") && form.password.length >= 6 && (mode === "login" || form.name.trim());
  const recruiter = role === "recruiter";

  async function submit(e) {
    e.preventDefault();
    if (!valid || submitting) return;

    setSubmitting(true);
    setAuthError("");
    setInfoMessage("");

    try {
      if (mode === "signup") {
        const result = await signup({
          email: form.email.trim(),
          password: form.password,
          name: form.name.trim(),
          role,
        });

        if (result.needsConfirmation) {
          setInfoMessage(result.message || "Signup successful! Please check your email to confirm your account before logging in.");
          setMode("login");
        } else {
          // Direct session established
          const userObj = result.user;
          const actualRole = userObj?.role || role;
          const isPendingRecruiter = (userObj?.requested_role === "recruiter" || role === "recruiter") && actualRole !== "recruiter";

          if (isPendingRecruiter) {
            setInfoMessage("Your recruiter account has been registered and is pending administrator approval before you can access the recruiter portal.");
            return;
          }

          if (actualRole === "recruiter") {
            nav(result.company?.name ? "/recruiter" : "/recruiter/setup", { replace: true });
          } else {
            nav(result.profile?.completed ? "/dashboard" : "/onboarding", { replace: true });
          }
        }
      } else {
        const result = await login({
          email: form.email.trim(),
          password: form.password,
        });

        if (result?.user) {
          const userObj = result.user;
          const actualRole = userObj.role || "student";
          const isPendingRecruiter = userObj.requested_role === "recruiter" && actualRole !== "recruiter";

          if (isPendingRecruiter) {
            setInfoMessage("Your recruiter account is pending administrator approval. Once approved, you can access the recruiter dashboard.");
            return;
          }

          if (actualRole === "recruiter") {
            nav(result.company?.name ? "/recruiter" : "/recruiter/setup", { replace: true });
          } else {
            nav(result.profile?.completed ? "/dashboard" : "/onboarding", { replace: true });
          }
        }
      }
    } catch (err) {
      console.error("Auth error:", err);
      let msg = err.message || "An authentication error occurred.";
      if (msg.includes("Invalid login credentials")) {
        msg = "Invalid email or password. Please check your credentials.";
      } else if (msg.includes("Email not confirmed")) {
        msg = "Email address has not been confirmed yet. Please verify your email via the confirmation link.";
      } else if (msg.includes("already registered")) {
        msg = "This email is already registered. Please log in instead.";
      }
      setAuthError(msg);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto grid max-w-5xl gap-10 px-4 py-16 md:grid-cols-2">
      <div className={`hidden flex-col justify-between rounded-xl2 p-8 text-white md:flex ${recruiter ? "bg-coral" : "bg-teal"}`}>
        <span className="font-display text-8xl font-extrabold leading-none">{recruiter ? "02" : "01"}</span>
        <div>
          <h2 className="text-3xl font-extrabold">
            {recruiter ? "Post a role. We'll rank the students who fit." : "Tell us what you know. We'll find what fits."}
          </h2>
          <p className="mt-3 text-white/80">{recruiter ? "Set up your company in under a minute." : "It takes about 3 minutes to set up your profile."}</p>
        </div>
      </div>

      <form onSubmit={submit} className="card space-y-4 self-center">
        <div className="flex gap-2 rounded-full bg-cream p-1" role="tablist" aria-label="I am a">
          {[["student", "I'm a student"], ["recruiter", "I'm hiring"]].map(([r, label]) => (
            <button
              type="button"
              key={r}
              onClick={() => {
                setRole(r);
                setAuthError("");
                setInfoMessage("");
              }}
              className={`flex-1 rounded-full py-2 text-sm font-semibold transition ${role === r ? "bg-coral text-white" : ""}`}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="flex gap-2 rounded-full bg-cream p-1">
          {["signup", "login"].map((m) => (
            <button
              type="button"
              key={m}
              onClick={() => {
                setMode(m);
                setAuthError("");
                setInfoMessage("");
              }}
              className={`flex-1 rounded-full py-2 text-sm font-semibold transition ${mode === m ? "bg-ink text-cream" : ""}`}
            >
              {m === "signup" ? "Sign up" : "Log in"}
            </button>
          ))}
        </div>

        {authError && (
          <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 border border-red-200">
            {authError}
          </div>
        )}

        {infoMessage && (
          <div className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800 border border-emerald-200">
            {infoMessage}
          </div>
        )}

        {mode === "signup" && (
          <label className="block text-sm font-medium">{recruiter ? "Your name" : "Full name"}
            <input className="input mt-1" value={form.name} onChange={set("name")} placeholder={recruiter ? "Priya Menon" : "Aarav Sharma"} required />
          </label>
        )}
        <label className="block text-sm font-medium">{recruiter ? "Work email" : "Email"}
          <input type="email" className="input mt-1" value={form.email} onChange={set("email")} placeholder={recruiter ? "you@company.com" : "you@college.edu"} required />
        </label>
        <label className="block text-sm font-medium">Password
          <input type="password" className="input mt-1" value={form.password} onChange={set("password")} placeholder="At least 6 characters" minLength={6} required />
        </label>
        <button className="btn-coral w-full !py-3" disabled={!valid || submitting}>
          {submitting ? "Please wait..." : mode === "signup" ? "Create account" : "Log in"}
        </button>
        {recruiter && mode === "signup" && (
          <p className="text-center text-xs text-ink/60">
            Note: Recruiter accounts are subject to administrative approval before posting jobs.
          </p>
        )}
        <p className="text-center text-xs text-ink/50">
          Secured with Supabase Authentication. Your credentials are fully encrypted.
        </p>
      </form>
    </div>
  );
}
