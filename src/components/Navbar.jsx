import { Link, NavLink, useNavigate } from "react-router-dom";
import { useStore } from "../store";
import { BRAND } from "../brand";

export function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2 font-display text-xl font-extrabold tracking-tight">
      <span className="grid h-8 w-8 place-items-center rounded-full bg-coral text-white">{BRAND[0]}</span>
      {BRAND}
    </Link>
  );
}

export default function Navbar() {
  const { user, profile, logout } = useStore();
  const nav = useNavigate();
  const link = ({ isActive }) => `rounded-full px-3 py-1.5 text-sm font-medium ${isActive ? "bg-ink text-cream" : "hover:bg-ink/5"}`;
  const isRecruiter = user?.role === "recruiter";
  const ready = user && !isRecruiter && profile?.completed;
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-cream/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        <Logo />
        <nav className="flex items-center gap-1">
          {ready && (
            <>
              <NavLink to="/dashboard" className={link}>Dashboard</NavLink>
              <NavLink to="/jobs" className={link}>Jobs</NavLink>
              <NavLink to="/tracker" className={link}>Tracker</NavLink>
              <NavLink to="/profile" className={link}>Profile</NavLink>
            </>
          )}
          {isRecruiter && (
            <>
              <NavLink to="/recruiter" end className={link}>Dashboard</NavLink>
              <NavLink to="/recruiter/post" className={link}>Post a job</NavLink>
              <NavLink to="/recruiter/setup" className={link}>Company</NavLink>
            </>
          )}
          {user && !isRecruiter && !profile?.completed && (
            <NavLink to="/onboarding" className={link}>Complete Profile</NavLink>
          )}
          {user ? (
            <button className="btn-line ml-2" onClick={async () => { await logout(); nav("/"); }}>Log out</button>
          ) : (
            <>
              <Link to="/login?role=recruiter&mode=login" className="hidden rounded-full px-3 py-1.5 text-sm font-medium hover:bg-ink/5 sm:block">For employers</Link>
              <Link to="/login?mode=signup" className="btn-ink ml-2">Get started</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
