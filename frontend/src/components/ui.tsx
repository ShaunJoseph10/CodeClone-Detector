import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { band, pct } from '../lib/format'
import type { Status } from '../api'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
const VARIANTS: Record<Variant, string> = {
  primary: 'bg-accent text-white hover:bg-accent-hover dark:text-slate-950',
  secondary: 'border border-line bg-surface hover:bg-raised',
  ghost: 'hover:bg-raised',
  danger: 'border border-line bg-surface text-danger hover:bg-raised',
}

export function Button({ variant = 'secondary', className = '', ...rest }:
  ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${VARIANTS[variant]} ${className}`}
      {...rest}
    />
  )
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-xl border border-line bg-surface p-5 ${className}`}>{children}</section>
}

export function PageHeader({ title, subtitle, actions }: { title: ReactNode; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0">
        <h1 className="truncate text-2xl font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  )
}

export function Skeleton({ className = '' }: { className?: string }) {
  return <div aria-hidden className={`animate-pulse rounded-md bg-raised ${className}`} />
}

export function SkeletonRows({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2" role="status" aria-label="Loading">
      {Array.from({ length: rows }, (_, i) => <Skeleton key={i} className="h-9 w-full" />)}
    </div>
  )
}

export function EmptyState({ title, body, action }: { title: string; body?: ReactNode; action?: ReactNode }) {
  return (
    <div className="rounded-xl border border-dashed border-line px-6 py-12 text-center">
      <p className="font-medium">{title}</p>
      {body && <p className="mx-auto mt-1 max-w-md text-sm text-muted">{body}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

const BAND_BG = { high: 'bg-danger', medium: 'bg-warn', low: 'bg-ok' }

export function ScoreBar({ value, label }: { value: number; label?: string }) {
  const b = band(value)
  return (
    <div className="flex items-center gap-2" title={label}>
      <div className="h-2 w-24 overflow-hidden rounded-full bg-raised" role="meter" aria-valuemin={0}
        aria-valuemax={100} aria-valuenow={Math.round(value * 100)} aria-label={label ?? 'Similarity'}>
        <div className={`h-full rounded-full ${BAND_BG[b]}`} style={{ width: `${Math.min(100, value * 100)}%` }} />
      </div>
      <span className="w-12 text-right text-sm font-medium tabular-nums">{pct(value, 1)}</span>
    </div>
  )
}

const STATUS_STYLE: Record<Status, string> = {
  queued: 'bg-raised text-muted',
  running: 'bg-accent-soft text-accent',
  done: 'bg-ok/15 text-ok',
  failed: 'bg-danger/15 text-danger',
}

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLE[status]}`}>
      {(status === 'running' || status === 'queued') && <span className="size-1.5 animate-pulse rounded-full bg-current" />}
      {status}
    </span>
  )
}

export function Stat({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
      {hint && <p className="mt-0.5 text-xs text-muted">{hint}</p>}
    </div>
  )
}

export const inputClass =
  'w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm placeholder:text-muted focus:border-accent focus:outline-none'
