export default function Header() {
  return (
    <header className="w-full bg-[var(--color-pure-white)] border-b border-[var(--color-champagne-gold)]/30 shadow-sm h-16 flex items-center justify-between px-8">
      <div className="flex items-center">
        <span className="font-bold text-xl tracking-tight text-[var(--color-deep-slate)]">PLIE Engine</span>
      </div>
      <nav className="flex items-center gap-6 text-sm font-medium text-[var(--color-deep-slate)]/70">
        <a href="#" className="hover:text-[var(--color-deep-slate)] transition-colors">GitHub</a>
        <a href="#" className="hover:text-[var(--color-deep-slate)] transition-colors">Audit Log</a>
      </nav>
    </header>
  );
}
