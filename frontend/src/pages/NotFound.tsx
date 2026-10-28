import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="py-24 text-center">
      <p className="text-sm font-semibold text-accent">404</p>
      <h1 className="mt-2 text-2xl font-semibold">Page not found</h1>
      <p className="mt-2 text-muted">This page, or the item it points to, does not exist.</p>
      <Link to="/" className="mt-6 inline-block rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white dark:text-slate-950">Back to assignments</Link>
    </div>
  )
}
