import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, type Analysis, type Signals, type UploadResult } from '../api'
import { Button, Card, EmptyState, PageHeader, Skeleton, SkeletonRows, StatusBadge, inputClass } from '../components/ui'
import { useToast } from '../components/Toast'
import UploadZone from '../components/UploadZone'
import NotFound from './NotFound'
import { SIGNALS, SIGNAL_LABEL, pct, when } from '../lib/format'

const DEFAULT_WEIGHTS: Signals = { dice: 0.3, containment: 0.2, lcs: 0.3, winnow: 0.2 }
const active = (a?: Analysis) => a?.status === 'queued' || a?.status === 'running'

function RunPanel({ assignmentId, disabled }: { assignmentId: number; disabled: boolean }) {
  const [threshold, setThreshold] = useState(0.6)
  const [minMass, setMinMass] = useState(6)
  const [weights, setWeights] = useState<Signals>(DEFAULT_WEIGHTS)
  const [custom, setCustom] = useState(false)
  const toast = useToast()
  const qc = useQueryClient()
  const run = useMutation({
    mutationFn: () => api.startAnalysis(assignmentId, { threshold, min_mass: minMass, weights: custom ? weights : null }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['analyses', assignmentId] }),
    onError: (e: Error) => toast('error', e.message),
  })
  const weightSum = SIGNALS.reduce((s, k) => s + weights[k], 0)

  return (
    <Card>
      <h2 className="font-semibold">Run analysis</h2>
      <div className="mt-4 space-y-4 text-sm">
        <label className="block">
          <span className="flex justify-between font-medium">Threshold <span className="tabular-nums text-accent">{pct(threshold)}</span></span>
          <input type="range" min={0.3} max={0.95} step={0.05} value={threshold}
            onChange={(e) => setThreshold(+e.target.value)} className="mt-2 w-full accent-[var(--color-accent)]" />
          <span className="text-xs text-muted">Pairs at or above this score are flagged.</span>
        </label>
        <label className="block">
          <span className="font-medium">Minimum clone size (nodes)</span>
          <input type="number" min={1} max={200} value={minMass} onChange={(e) => setMinMass(Math.max(1, +e.target.value || 1))}
            className={`${inputClass} mt-1`} />
        </label>
        <details onToggle={(e) => setCustom((e.target as HTMLDetailsElement).open)}>
          <summary className="cursor-pointer font-medium text-muted hover:text-ink">Advanced: signal weights</summary>
          <div className="mt-3 grid grid-cols-2 gap-3">
            {SIGNALS.map((k) => (
              <label key={k} className="block">
                <span className="text-xs text-muted">{SIGNAL_LABEL[k]}</span>
                <input type="number" min={0} max={1} step={0.05} value={weights[k]}
                  onChange={(e) => setWeights({ ...weights, [k]: Math.max(0, +e.target.value || 0) })}
                  className={`${inputClass} mt-1`} />
              </label>
            ))}
          </div>
          {weightSum <= 0 && <p className="mt-2 text-xs text-danger">At least one weight must be above zero.</p>}
        </details>
        <Button variant="primary" className="w-full" disabled={disabled || run.isPending || (custom && weightSum <= 0)}
          onClick={() => run.mutate()}>
          {run.isPending ? 'Starting…' : 'Run analysis'}
        </Button>
        {disabled && <p className="text-xs text-muted">Upload at least two files that parse to run an analysis.</p>}
      </div>
    </Card>
  )
}

function AnalysisList({ assignmentId }: { assignmentId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ['analyses', assignmentId],
    queryFn: () => api.analyses(assignmentId),
    refetchInterval: (q) => (q.state.data?.some(active) ? 1000 : false), // live status while running
  })
  if (isLoading) return <SkeletonRows rows={2} />
  if (!data?.length) return <p className="text-sm text-muted">No analyses yet.</p>
  return (
    <ul className="divide-y divide-line">
      {data.map((a) => (
        <li key={a.id} className="flex flex-wrap items-center justify-between gap-2 py-3 text-sm">
          <div className="flex items-center gap-3">
            <StatusBadge status={a.status} />
            <span className="text-muted">#{a.id} · threshold {pct(a.config.threshold)} · {when(a.created_at)}</span>
          </div>
          {a.status === 'done' && (
            <Link to={`/analyses/${a.id}`} className="font-medium text-accent hover:underline">
              {a.summary.flagged} flagged · view results →
            </Link>
          )}
          {a.status === 'failed' && <span className="text-danger">{a.error}</span>}
        </li>
      ))}
    </ul>
  )
}

export default function AssignmentPage() {
  const id = Number(useParams().id)
  const qc = useQueryClient()
  const toast = useToast()
  const navigate = useNavigate()
  const [lastUpload, setLastUpload] = useState<UploadResult | null>(null)
  const assignment = useQuery({ queryKey: ['assignment', id], queryFn: () => api.assignment(id) })
  const subs = useQuery({ queryKey: ['submissions', id], queryFn: () => api.submissions(id) })
  const remove = useMutation({
    mutationFn: () => api.deleteAssignment(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assignments'] })
      toast('success', 'Assignment deleted')
      navigate('/')
    },
    onError: (e: Error) => toast('error', e.message),
  })

  if ((assignment.error as { status?: number })?.status === 404) return <NotFound />
  const parsed = subs.data?.filter((s) => !s.parse_error).length ?? 0

  return (
    <>
      <nav className="mb-2 text-sm text-muted"><Link to="/" className="hover:text-ink">Assignments</Link> /</nav>
      {assignment.data ? (
        <PageHeader title={assignment.data.title}
          subtitle={`${assignment.data.course || 'No course'} · ${assignment.data.submission_count} submissions`}
          actions={<Button variant="danger" onClick={() => confirm('Delete this assignment and all its results?') && remove.mutate()}>Delete</Button>} />
      ) : <Skeleton className="mb-6 h-12 w-72" />}

      <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
        <div className="min-w-0 space-y-6">
          <Card>
            <h2 className="mb-4 font-semibold">Upload submissions</h2>
            <UploadZone assignmentId={id}
              onDone={(r) => {
                setLastUpload(r)
                qc.invalidateQueries({ queryKey: ['submissions', id] })
                qc.invalidateQueries({ queryKey: ['assignment', id] })
                toast('success', `${r.created.length} file(s) added`)
              }}
              onError={(m) => toast('error', m)} />
            {lastUpload && lastUpload.errors.length > 0 && (
              <div className="mt-3 rounded-lg border border-danger/30 bg-danger/5 p-3 text-sm">
                <p className="font-medium text-danger">{lastUpload.errors.length} file(s) not added</p>
                <ul className="mt-1 space-y-0.5 text-muted">
                  {lastUpload.errors.map((e) => <li key={e.filename}><code>{e.filename}</code>: {e.error}</li>)}
                </ul>
              </div>
            )}
          </Card>

          <Card className="p-0">
            <h2 className="px-5 pt-5 font-semibold">Submissions</h2>
            <div className="mt-3 overflow-x-auto">
              {subs.isLoading ? <div className="p-5"><SkeletonRows /></div> : !subs.data?.length ? (
                <div className="p-5"><EmptyState title="No submissions yet" body="Upload files above to get started." /></div>
              ) : (
                <table className="w-full text-sm">
                  <thead className="border-y border-line text-left text-xs uppercase tracking-wide text-muted">
                    <tr><th className="px-5 py-2 font-medium">Student</th><th className="px-5 py-2 font-medium">File</th>
                      <th className="px-5 py-2 font-medium">Lines</th><th className="px-5 py-2 font-medium">Parse status</th></tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {subs.data.map((s) => (
                      <tr key={s.id}>
                        <td className="px-5 py-2 font-medium">{s.student_name}</td>
                        <td className="px-5 py-2 font-mono text-xs">{s.filename}</td>
                        <td className="px-5 py-2 tabular-nums">{s.lines}</td>
                        <td className="px-5 py-2">
                          {s.parse_error ? <span className="text-danger" title={s.parse_error}>✕ {s.parse_error}</span> : (
                            <Link to={`/submissions/${s.id}/ast`} className="text-ok hover:underline">✓ parsed · AST</Link>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <RunPanel assignmentId={id} disabled={parsed < 2} />
          <Card>
            <h2 className="mb-2 font-semibold">Analyses</h2>
            <AnalysisList assignmentId={id} />
          </Card>
        </div>
      </div>
    </>
  )
}
