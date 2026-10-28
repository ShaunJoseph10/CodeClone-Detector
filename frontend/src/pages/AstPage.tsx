import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { api, type AstNode } from '../api'
import AstTree from '../components/AstTree'
import { Button, Card, EmptyState, PageHeader, Skeleton } from '../components/ui'
import NotFound from './NotFound'

function countNodes(n: AstNode): number {
  return 1 + n.children.reduce((s, c) => s + countNodes(c), 0)
}

export default function AstPage() {
  const id = Number(useParams().id)
  const [normalized, setNormalized] = useState(false)
  const [openDepth, setOpenDepth] = useState(3)
  const [treeKey, setTreeKey] = useState(0) // remount the tree to apply expand/collapse all
  const [hover, setHover] = useState<AstNode | null>(null)
  const sub = useQuery({ queryKey: ['submission', id], queryFn: () => api.submission(id) })
  const ast = useQuery({ queryKey: ['ast', id, normalized], queryFn: () => api.ast(id, normalized), enabled: !!sub.data && !sub.data.parse_error })

  if ((sub.error as { status?: number })?.status === 404) return <NotFound />
  const expand = (d: number) => { setOpenDepth(d); setTreeKey((k) => k + 1) }

  return (
    <>
      <nav className="mb-2 text-sm text-muted">
        {sub.data ? <Link to={`/assignments/${sub.data.assignment_id}`} className="hover:text-ink">← Assignment</Link> : '…'}
      </nav>
      <PageHeader title={sub.data ? `AST · ${sub.data.student_name}` : 'AST'}
        subtitle="The tree built by the project's own lexer and parser (teaching mode)." />

      {sub.data?.parse_error ? <EmptyState title="This file does not parse" body={sub.data.parse_error} /> : (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="min-w-0">
            <div className="mb-4 flex flex-wrap items-center gap-2">
              <div role="tablist" className="inline-flex rounded-lg border border-line p-0.5 text-sm">
                {[false, true].map((n) => (
                  <button key={String(n)} role="tab" aria-selected={normalized === n} onClick={() => setNormalized(n)}
                    className={`rounded-md px-3 py-1.5 ${normalized === n ? 'bg-accent text-white dark:text-slate-950' : 'text-muted hover:text-ink'}`}>
                    {n ? 'Normalized' : 'Raw'}
                  </button>
                ))}
              </div>
              <Button variant="ghost" onClick={() => expand(99)}>Expand all</Button>
              <Button variant="ghost" onClick={() => expand(1)}>Collapse</Button>
              {ast.data && <span className="ml-auto text-xs text-muted">{countNodes(ast.data.tree)} nodes</span>}
            </div>
            <p className="mb-3 text-xs text-muted">
              {normalized ? 'What the matcher sees: dead code removed, for-range loops rewritten as while, names → VAR / FUNC, literals → NUM / STR.'
                : 'Exactly as parsed. Hover a node to highlight its source lines.'}
            </p>
            {ast.data ? (
              <ul role="tree" aria-label="Abstract syntax tree" className="max-h-[70vh] overflow-auto font-mono text-[13px] leading-6" key={treeKey}>
                <AstTree node={ast.data.tree} openDepth={openDepth} onHover={setHover} />
              </ul>
            ) : <Skeleton className="h-96" />}
          </Card>
          <Card className="min-w-0 p-0">
            <div className="border-b border-line px-4 py-2 font-mono text-xs text-muted">{sub.data?.filename}</div>
            {sub.data ? (
              <div className="max-h-[75vh] overflow-auto py-2 font-mono text-[13px] leading-6">
                {sub.data.source.replace(/\n$/, '').split('\n').map((text, i) => {
                  const on = hover && i + 1 >= hover.start_line && i + 1 <= hover.end_line
                  return (
                    <div key={i} className={`flex pr-4 ${on ? 'bg-accent-soft' : ''}`}>
                      <span className="w-12 shrink-0 select-none pr-3 text-right text-muted">{i + 1}</span>
                      <pre className="whitespace-pre">{text || ' '}</pre>
                    </div>
                  )
                })}
              </div>
            ) : <Skeleton className="m-4 h-96" />}
          </Card>
        </div>
      )}
    </>
  )
}
