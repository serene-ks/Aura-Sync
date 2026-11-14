import { Routes, Route, Navigate, Outlet, useLocation, Link } from "react-router-dom";
import { useEffect } from "react";
import { useStore } from "./store";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import Landing from "./pages/Landing";
import Auth from "./pages/Auth";
import Onboarding from "./pages/Onboarding";
import Dashboard from "./pages/Dashboard";
import Jobs from "./pages/Jobs";
import JobDetail from "./pages/JobDetail";
import Tracker from "./pages/Tracker";
import RecruiterSetup from "./pages/recruiter/RecruiterSetup";
import RecruiterDashboard from "./pages/recruiter/RecruiterDashboard";
import PostJob from "./pages/recruiter/PostJob";
import Candidates from "./pages/recruiter/Candidates";

function Layout() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1"><Outlet /></main>
      <Footer />
    </div>
  );
}

// Page guards: not logged in -> /login; profile not finished -> /onboarding
// Student pages. A logged-in recruiter is sent to the recruiter area instead.
function RequireLogin({ children }) {
  const { user, loading } = useStore();
  if (loading) return <div className="p-10 text-center text-ink/60">Loading session...</div>;
  if (!user) return <Navigate to="/login?mode=login" replace />;
  if (user.role === "recruiter") return <Navigate to="/recruiter" replace />;
  return children;
}

function RequireProfile({ children }) {
  const { user, profile, loading } = useStore();
  if (loading) return <div className="p-10 text-center text-ink/60">Loading session...</div>;
  if (!user) return <Navigate to="/login?mode=login" replace />;
  if (user.role === "recruiter") return <Navigate to="/recruiter" replace />;
  if (!profile?.completed) return <Navigate to="/onboarding" replace />;
  return children;
}

// Recruiter pages. withCompany: also require the company profile to be filled in.
function RequireRecruiter({ children, withCompany = true }) {
  const { user, company, loading } = useStore();
  if (loading) return <div className="p-10 text-center text-ink/60">Loading session...</div>;
  if (!user) return <Navigate to="/login?role=recruiter&mode=login" replace />;
  if (user.requested_role === "recruiter" && user.role !== "recruiter") {
    return (
      <div className="mx-auto max-w-lg p-10 text-center">
        <div className="card space-y-4">
          <h2 className="text-2xl font-extrabold text-ink">Account Pending Approval</h2>
          <p className="text-sm text-ink/70">
            Your recruiter account has been registered and is pending administrator verification.
            Once approved, you will have access to post jobs and discover candidates.
          </p>
          <div className="pt-2">
            <Link to="/" className="btn-coral">Return to Home</Link>
          </div>
        </div>
      </div>
    );
  }
  if (user.role !== "recruiter") return <Navigate to="/dashboard" replace />;
  if (withCompany && !company?.name) return <Navigate to="/recruiter/setup" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Auth />} />
        <Route path="/employer" element={<Navigate to="/login?role=recruiter&mode=login" replace />} />
        <Route path="/recruiter/setup" element={<RequireRecruiter withCompany={false}><RecruiterSetup /></RequireRecruiter>} />
        <Route path="/recruiter" element={<RequireRecruiter><RecruiterDashboard /></RequireRecruiter>} />
        <Route path="/recruiter/post" element={<RequireRecruiter><PostJob /></RequireRecruiter>} />
        <Route path="/recruiter/jobs/:id" element={<RequireRecruiter><Candidates /></RequireRecruiter>} />
        <Route path="/onboarding" element={<RequireLogin><Onboarding /></RequireLogin>} />
        <Route path="/profile" element={<RequireLogin><Onboarding editing /></RequireLogin>} />
        <Route path="/dashboard" element={<RequireProfile><Dashboard /></RequireProfile>} />
        <Route path="/jobs" element={<RequireProfile><Jobs /></RequireProfile>} />
        <Route path="/jobs/:id" element={<RequireProfile><JobDetail /></RequireProfile>} />
        <Route path="/tracker" element={<RequireProfile><Tracker /></RequireProfile>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
