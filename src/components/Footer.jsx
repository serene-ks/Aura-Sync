import { BRAND } from "../brand";

export default function Footer() {
  return (
    <footer className="border-t border-line py-8 text-center text-sm text-ink/60">
      © {new Date().getFullYear()} {BRAND} · Frontend prototype with sample data
    </footer>
  );
}
