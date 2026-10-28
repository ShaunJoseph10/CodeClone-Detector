import { useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { api, type Match, type PairDetail } from '../api'
import { Card, ScoreBar, Skeleton } from '../components/ui'
import NotFound from './NotFound'
import { MATCH_COLORS, lineMatches } from '../lib/highlight'
import { SIGNALS, SIGNAL_LABEL, pct } from '../lib/format'

type Side = 'a' | 'b'

function CodePane({ side, sub, matches, onPick, paneRef }: {
  side: Side; sub: PairDetail['a']; matches: Match[]; onPick: (i: number, from: Side) => void
  paneRef: React.RefObject<HTMLDivElement>
}) {
  const byLine = lineMatches(matches, side)
  const lines = sub.source.replace(/\n$/, '').split('\n')
  return (
    <div className="min-w-0 overflow-hidden rounded-xl border border-line bg-surface">
      <div className="flex items-center justify-between border-b border-line px-4 py-2 text-sm">
        <span className="font-medium">{sub.student_name}</span>
        <Link to={`/submissions/${sub.id}/ast`} className="font-mono text-xs text-muted hover:text-accent">{sub.filename} · AST</Link>
      </div>
      <div ref={paneRef} className="max-h-[70vh] overflow-auto py-2 font-mono text-[13px] leading-6">
        {lines.map((text, i) => {
          const no = i + 1
          const m = byLine.get(no)
          const props = m === undefined ? {} : {
            role: 'button', tabIndex: 0, 'aria-label': `Line ${no}, match ${m + 1}: jump to the other file`,
            onClick: () => onPick(m, side),
            onKeyDown: (e: React.KeyboardEvent) => (e.key === 'Enter' || e.key === ' ') && onPick(m, side),
          }
          return (
            <div key={no} data-line={no} {...props}
              className={`flex pr-4 ${m === undefined ? '' : 'cursor-pointer hover:brightness-95'} transition-[outline]`}
              style={m === undefined ? undefined : { background: MATCH_COLORS[m % MATCH_COLORS.length] }}>
              <span className="w-12 shrink-0 select-none pr-3 text-right text-muted">{no}</span>
              <pre className="whitespace-pre">{text || ' '}</pre>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function ComparePage() {
  const analysisId = Number(useParams().analysisId)
  const pairId = Number(useParams().pairId)
  const { data, isLoading, error } = useQuery({ queryKey: ['pair', analysisId, pairId], queryFn: () => api.pair(analysisId, pairId) })
  const panes = { a: useRef<HTMLDivElement>(null), b: useRef<HTMLDivElement>(null) }

  const jump = (i: number, from: Side) => {
    if (!data) return
    const m = data.matches[i]
    const to: Side = from === 'a' ? 'b' : 'a'
    for (const side of [from, to]) {
      const line = side === 'a' ? m.a_start : m.b_start
      const el = panes[side].current?.querySelector<HTMLElement>(`[data-line="${line}"]`)
      if (!el) continue
      if (side === to) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      el.animate([{ outline: '2px solid var(--color-accent)' }, { outline: '2px solid transparent' }], { duration: 1200 })
    }
  }

  if ((error as { status?: number })?.status === 404) return <NotFound />
  if (isLoading || !data) return <div className="space-y-4"><Skeleton className="h-28" /><div className="grid gap-4 lg:grid-cols-2"><Skeleton className="h-96" /><Skeleton className="h-96" /></div></div>

  return (
    <>
      <nav className="mb-2 text-sm text-muted">
        <Link to={`/analyses/${analysisId}`} className="hover:text-ink">← Analysis #{analysisId}</Link>
      </nav>
      <Card className="mb-4">
        <div className="flex flex-wrap items-center gap-x-8 gap-y-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-muted">Pair</p>
            <h1 className="text-xl font-semibold">{data.a.student_name} <span className="text-muted">↔</span> {data.b.student_name}</h1>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-muted">Score</p>
            <ScoreBar value={data.score} />
          </div>
          {SIGNALS.map((k) => (
            <div key={k}>
              <p className="text-xs uppercase tracking-wide text-muted">{SIGNAL_LABEL[k]}</p>
              <p className="font-semibold tabular-nums">{pct(data.signals[k], 1)}</p>
            </div>
          ))}
        </div>
        {data.matches.length > 0 ? (
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            {data.matches.map((m, i) => (
              <button key={i} onClick={() => jump(i, 'a')} className="rounded-md border border-line px-2 py-1 font-mono hover:border-accent"
                style={{ background: MATCH_COLORS[i % MATCH_COLORS.length] }}>
                A {m.a_start}–{m.a_end} = B {m.b_start}–{m.b_end} · {m.size} nodes
              </button>
            ))}
          </div>
        ) : <p className="mt-4 text-sm text-muted">No identical subtrees; the score comes from the LCS and winnowing signals.</p>}
        <p className="mt-2 text-xs text-muted">Click a highlighted region to jump to its match in the other file.</p>
      </Card>
      <div className="grid gap-4 lg:grid-cols-2">
        <CodePane side="a" sub={data.a} matches={data.matches} onPick={jump} paneRef={panes.a} />
        <CodePane side="b" sub={data.b} matches={data.matches} onPick={jump} paneRef={panes.b} />
      </div>
    </>
  )
}
