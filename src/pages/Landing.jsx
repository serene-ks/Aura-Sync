import { Link } from "react-router-dom";
import { ArrowRight, Upload, Target, Send, Sparkles, ListChecks, FileText } from "lucide-react";

// Big colored blocks + oversized numerals: the look from the reference.
const steps = [
  { n: "01", title: "Upload your CV", text: "We read it and pick out your skills. You just confirm.", bg: "bg-coral text-white", Icon: Upload },
  { n: "02", title: "See your match", text: "Every job shows a match score and the skills you're missing.", bg: "bg-teal text-white", Icon: Target },
  { n: "03", title: "Apply and track", text: "Get a ready Apply Kit, then follow every application on one board.", bg: "bg-mustard text-ink", Icon: Send },
];

const features = [
  { Icon: FileText, title: "Skill parser", text: "No long forms. Your CV becomes a skills profile in seconds." },
  { Icon: Target, title: "Match score", text: "See exactly why a job fits and what to learn to fit better." },
  { Icon: Sparkles, title: "Apply Kit", text: "A tailored cover note and ready answers, auto-filled from your profile." },
  { Icon: ListChecks, title: "Tracker", text: "Saved, Applied, Interview, Offer. With nudges when it's time to follow up." },
];

const audience = [
  { who: "2nd & 3rd year", what: "Find internships that match the skills you already have." },
  { who: "Final year", what: "Line up your first job before placement season ends." },
  { who: "Recent graduate", what: "Stop guessing titles. Search by what you can do." },
];

export default function Landing() {
  return (
    <>
      {/* HERO */}
      <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 pb-20 pt-16 md:grid-cols-2 md:pt-24">
        <div>
          <p className="reveal chip bg-ink text-cream">For students & freshers</p>
          <h1 className="reveal mt-5 text-5xl font-extrabold leading-[1.02] tracking-tight sm:text-6xl" style={{ animationDelay: "80ms" }}>
            Jobs that fit what you <span className="text-coral">already know.</span>
          </h1>
          <p className="reveal mt-6 max-w-md text-lg text-ink/70" style={{ animationDelay: "160ms" }}>
            Upload your CV, see how well you match every internship and job, apply faster, and never lose track of an application.
          </p>
          <div className="reveal mt-8 flex flex-wrap gap-3" style={{ animationDelay: "240ms" }}>
            <Link to="/login?mode=signup" className="btn-coral !px-6 !py-3 text-base">I'm a student <ArrowRight size={18} /></Link>
            <Link to="/login?role=recruiter&mode=signup" className="btn-line !px-6 !py-3 text-base">I'm hiring</Link>
          </div>
        </div>

        {/* Tilted tile collage built from plain divs */}
        <div className="relative mx-auto h-[380px] w-full max-w-md" aria-hidden="true">
          <div className="reveal absolute left-2 top-4 w-56 -rotate-6 rounded-xl2 bg-teal p-5 text-white shadow-xl" style={{ animationDelay: "200ms" }}>
            <p className="text-xs uppercase tracking-widest opacity-70">Match</p>
            <p className="font-display text-6xl font-extrabold">86%</p>
            <p className="mt-2 text-sm opacity-90">Data Analyst Intern</p>
          </div>
          <div className="reveal absolute right-0 top-24 w-52 rotate-3 rounded-xl2 bg-coral p-5 text-white shadow-xl" style={{ animationDelay: "320ms" }}>
            <p className="font-display text-7xl font-extrabold leading-none">02</p>
            <p className="mt-2 text-sm">Skills missing: Excel, Power BI</p>
          </div>
          <div className="reveal absolute bottom-2 left-10 w-60 -rotate-2 rounded-xl2 bg-mustard p-5 shadow-xl" style={{ animationDelay: "440ms" }}>
            <p className="text-xs uppercase tracking-widest opacity-60">Tracker</p>
            <div className="mt-2 flex gap-2 text-sm font-semibold"><span className="rounded-full bg-ink px-3 py-1 text-cream">Applied 3</span><span className="rounded-full bg-paper px-3 py-1">Interview 1</span></div>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="mx-auto max-w-6xl px-4 pb-20">
        <h2 className="mb-8 text-3xl font-extrabold tracking-tight sm:text-4xl">How it works</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {steps.map(({ n, title, text, bg, Icon }, i) => (
            <div key={n} className={`reveal rounded-xl2 p-7 ${bg} transition hover:-translate-y-1`} style={{ animationDelay: `${i * 120}ms` }}>
              <div className="flex items-start justify-between">
                <span className="font-display text-7xl font-extrabold leading-none">{n}</span>
                <Icon size={28} />
              </div>
              <h3 className="mt-8 text-2xl font-bold">{title}</h3>
              <p className="mt-2 opacity-90">{text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* DIFFERENTIATOR */}
      <section className="bg-ink py-20 text-cream">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="max-w-xl text-3xl font-extrabold tracking-tight sm:text-4xl">Built to make applying fast, not stressful.</h2>
          <div className="mt-10 grid gap-px overflow-hidden rounded-xl2 bg-cream/15 sm:grid-cols-2 lg:grid-cols-4">
            {features.map(({ Icon, title, text }) => (
              <div key={title} className="bg-ink p-6">
                <Icon className="text-mustard" />
                <h3 className="mt-4 text-lg font-bold">{title}</h3>
                <p className="mt-1 text-sm text-cream/70">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AUDIENCE */}
      <section className="mx-auto max-w-6xl px-4 py-20">
        <h2 className="mb-8 text-3xl font-extrabold tracking-tight sm:text-4xl">Made for where you are</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {audience.map((a) => (
            <div key={a.who} className="card">
              <p className="font-display text-xl font-bold">{a.who}</p>
              <p className="mt-2 text-ink/70">{a.what}</p>
            </div>
          ))}
        </div>
        <div className="mt-12 rounded-xl2 bg-coral p-10 text-center text-white">
          <h2 className="text-3xl font-extrabold sm:text-4xl">Find your first role.</h2>
          <Link to="/login?mode=signup" className="btn mt-6 bg-ink text-cream !px-6 !py-3 text-base">Create your profile <ArrowRight size={18} /></Link>
        </div>
      </section>
    </>
  );
}
