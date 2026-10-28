import { useEffect, useState } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import ClusterGraph from '../components/ClusterGraph'
import { Card, EmptyState, PageHeader, Skeleton, SkeletonRows, ScoreBar, Stat, StatusBadge, inputClass } from '../components/ui'
import NotFound from './NotFound'
import { SIGNALS, SIGNAL_LABEL, pct } from '../lib/format'

const PAGE_SIZE = 25

function useDebounced<T>(value: T, ms = 300) {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return v
}

function SortHeader({ field, label, sort, setSort }: { field: string; label: string; sort: string; setSort: (s: string) => void }) {
  const activeField = sort.replace('-', '') === field
  const desc = sort.startsWith('-')
  return (
    <th className="px-4 py-2 font-medium" aria-sort={activeField ? (desc ? 'descending' : 'ascending') : 'none'}>
      <button className={`inline-flex items-center gap-1 uppercase tracking-wide hover:text-ink ${activeField ? 'text-ink' : ''}`}
        onClick={() => setSort(activeField && desc ? field : '-' + field)}>
        {label}{activeField && <span aria-hidden>{desc ? '↓' : '↑'}</span>}
      </button>
    </th>
  )
}

function PairsTable({ analysisId, threshold }: { analysisId: number; threshold: number }) {
  const [minScore, setMinScore] = useState(threshold)
  const [student, setStudent] = useState('')
  const [sort, setSort] = useState('-score')
  const [page, setPage] = useState(1)
  const q = { min_score: useDebounced(minScore), student: useDebounced(student.trim()), sort, page, page_size: PAGE_SIZE }
  useEffect(() => setPage(1), [q.min_score, q.student, sort])
  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['pairs', analysisId, q], queryFn: () => api.pairs(analysisId, q), placeholderData: keepPreviousData,
  })
  const pages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1

  return (
    <Card className="p-0">
      <div className="flex flex-wrap items-end gap-4 px-5 pt-5">
        <h2 className="mr-auto font-semibold">Ranked pairs {data && <span className="font-normal text-muted">({data.total})</span>}</h2>
        <label className="text-sm">
          <span className="mb-1 block text-xs text-muted">Min score: <b className="text-ink">{pct(minScore)}</b></span>
          <input type="range" min={0} max={1} step={0.05} value={minScore} onChange={(e) => setMinScore(+e.target.value)}
            className="w-40 accent-[var(--color-accent)]" />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-xs text-muted">Search student</span>
          <input type="search" className={`${inputClass} w-48`} placeholder="name…" value={student} onChange={(e) => setStudent(e.target.value)} />
        </label>
      </div>
      <div className={`mt-4 overflow-x-auto transition-opacity ${isFetching ? 'opacity-70' : ''}`}>
        {isLoading ? <div className="p-5"><SkeletonRows /></div> : !data?.items.length ? (
          <div className="p-5"><EmptyState title="No pairs match" body="Lower the minimum score or clear the search." /></div>
        ) : (
          <table className="w-full text-sm">
            <thead className="border-y border-line text-left text-xs text-muted">
              <tr>
                <th className="px-4 py-2 font-medium uppercase tracking-wide">Students</th>
                <SortHeader field="score" label="Score" sort={sort} setSort={setSort} />
                {SIGNALS.map((k) => <SortHeader key={k} field={k} label={SIGNAL_LABEL[k]} sort={sort} setSort={setSort} />)}
                <th className="px-4 py-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.items.map((p) => (
                <tr key={p.id} className="hover:bg-raised/60">
                  <td className="px-4 py-2">
                    <div className="font-medium">{p.a.student_name} <span className="text-muted">↔</span> {p.b.student_name}</div>
                    <div className="font-mono text-xs text-muted">{p.a.filename} · {p.b.filename}</div>
                  </td>
                  <td className="px-4 py-2"><ScoreBar value={p.score} /></td>
                  {SIGNALS.map((k) => <td key={k} className="px-4 py-2 tabular-nums text-muted">{pct(p.signals[k])}</td>)}
                  <td className="px-4 py-2 text-right">
                    <Link to={`/analyses/${analysisId}/pairs/${p.id}`} className="font-medium text-accent hover:underline">Compare</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {data && data.total > PAGE_SIZE && (
        <div className="flex items-center justify-between border-t border-line px-5 py-3 text-sm">
          <span className="text-muted">Page {page} of {pages}</span>
          <div className="flex gap-2">
            <button className="rounded-lg border border-line px-3 py-1 disabled:opacity-40" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
            <button className="rounded-lg border border-line px-3 py-1 disabled:opacity-40" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</button>
          </div>
        </div>
      )}
    </Card>
  )
}

export default function ResultsPage() {
  const id = Number(useParams().id)
  const navigate = useNavigate()
  const [hideIsolated, setHideIsolated] = useState(true)
  const analysis = useQuery({
    queryKey: ['analysis', id], queryFn: () => api.analysis(id),
    refetchInterval: (q) => (['queued', 'running'].includes(q.state.data?.status ?? '') ? 1000 : false),
  })
  const done = analysis.data?.status === 'done'
  const graph = useQuery({ queryKey: ['graph', id], queryFn: () => api.graph(id), enabled: done })
  const clusters = useQuery({ queryKey: ['clusters', id], queryFn: () => api.clusters(id), enabled: done })
  const assignment = useQuery({
    queryKey: ['assignment', analysis.data?.assignment_id], queryFn: () => api.assignment(analysis.data!.assignment_id),
    enabled: !!analysis.data,
  })

  if ((analysis.error as { status?: number })?.status === 404) return <NotFound />
  if (analysis.isLoading || !analysis.data) {
    return <div className="space-y-4"><Skeleton className="h-10 w-80" /><div className="grid grid-cols-2 gap-4 md:grid-cols-6">{Array.from({ length: 6 }, (_, i) => <Skeleton key={i} className="h-24" />)}</div></div>
  }
  const a = analysis.data
  const s = a.summary

  return (
    <>
      <nav className="mb-2 text-sm text-muted">
        <Link to="/" className="hover:text-ink">Assignments</Link> /{' '}
        <Link to={`/assignments/${a.assignment_id}`} className="hover:text-ink">{assignment.data?.title ?? '…'}</Link> /
      </nav>
      <PageHeader title={<>Analysis #{a.id} <StatusBadge status={a.status} /></>}
        subtitle={`Threshold ${pct(a.config.threshold)} · min clone size ${a.config.min_mass} nodes`}
        actions={done && <>
          <a className="rounded-lg border border-line bg-surface px-3.5 py-2 text-sm font-medium hover:bg-raised" href={api.exportUrl(id, 'csv')} download>Export CSV</a>
          <a className="rounded-lg border border-line bg-surface px-3.5 py-2 text-sm font-medium hover:bg-raised" href={api.exportUrl(id, 'json')} download>Export JSON</a>
        </>} />

      {a.status === 'failed' && <EmptyState title="This analysis failed" body={a.error ?? 'Unknown error'} />}
      {!done && a.status !== 'failed' && <EmptyState title="Analysis in progress…" body="This page updates automatically." />}

      {done && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
            <Stat label="Files" value={s.files} />
            <Stat label="Pairs checked" value={s.pairs_scored} hint={`of ${s.total_pairs} possible`} />
            <Stat label="Skipped by index" value={s.pairs_skipped} hint="shared no fingerprints" />
            <Stat label="Flagged pairs" value={s.flagged} hint={`≥ ${pct(a.config.threshold)}`} />
            <Stat label="Clusters" value={s.clusters} />
            <Stat label="Duration" value={`${a.duration_ms} ms`} />
          </div>

          <PairsTable analysisId={id} threshold={a.config.threshold} />

          <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
            <Card>
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-semibold">Similarity graph</h2>
                <label className="flex items-center gap-2 text-sm text-muted">
                  <input type="checkbox" checked={hideIsolated} onChange={(e) => setHideIsolated(e.target.checked)} className="accent-[var(--color-accent)]" />
                  Hide students with no flagged pair
                </label>
              </div>
              {graph.data ? (graph.data.edges.length ? (
                <ClusterGraph graph={graph.data} hideIsolated={hideIsolated} onEdge={(pid) => navigate(`/analyses/${id}/pairs/${pid}`)} />
              ) : <EmptyState title="No flagged pairs" body="Nothing reached the threshold." />) : <Skeleton className="h-[28rem]" />}
              <p className="mt-2 text-xs text-muted">Thicker line = higher similarity. Click a line to compare the two files.</p>
            </Card>
            <Card>
              <h2 className="mb-3 font-semibold">Clusters</h2>
              {clusters.isLoading ? <SkeletonRows rows={3} /> : !clusters.data?.length ? (
                <p className="text-sm text-muted">No groups of similar submissions.</p>
              ) : (
                <ol className="space-y-3 text-sm">
                  {clusters.data.map((c, i) => (
                    <li key={c.id} className="rounded-lg border border-line p-3">
                      <div className="mb-1 flex justify-between text-xs text-muted"><span>Cluster {i + 1} · {c.members.length} students</span><span>max {pct(c.max_score)}</span></div>
                      <p>{c.members.map((m) => m.student_name).join(', ')}</p>
                    </li>
                  ))}
                </ol>
              )}
            </Card>
          </div>
        </div>
      )}
    </>
  )
}
