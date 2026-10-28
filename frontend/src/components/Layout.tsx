import { useState } from 'react'
import { Link, Outlet } from 'react-router-dom'

function ThemeToggle() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains('dark'))
  const toggle = () => {
    const next = !dark
    setDark(next)
    document.documentElement.classList.toggle('dark', next)
    try { localStorage.setItem('theme', next ? 'dark' : 'light') } catch { /* storage blocked */ }
  }
  return (
    <button onClick={toggle} className="rounded-lg p-2 text-muted hover:bg-raised hover:text-ink"
      aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'} title="Toggle theme">
      {dark ? (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>
      ) : (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" /></svg>
      )}
    </button>
  )
}

export default function Layout() {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-line bg-surface/85 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6">
          <Link to="/" className="flex items-center gap-2 font-semibold">
            <img src="/favicon.svg" alt="" className="size-6" />
            CodeClone
            <span className="rounded bg-accent-soft px-1.5 py-0.5 text-[10px] font-semibold text-accent">v2</span>
          </Link>
          <nav className="flex items-center gap-1 text-sm">
            <Link to="/" className="rounded-lg px-3 py-2 text-muted hover:bg-raised hover:text-ink">Assignments</Link>
            <a href="/docs" className="rounded-lg px-3 py-2 text-muted hover:bg-raised hover:text-ink">API docs</a>
            <ThemeToggle />
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <Outlet />
      </main>
    </div>
  )
}
