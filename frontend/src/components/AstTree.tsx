import { useState } from 'react'
import type { AstNode } from '../api'

type Props = { node: AstNode; depth?: number; openDepth: number; onHover?: (n: AstNode | null) => void }

/** Collapsible n-ary tree. Nodes deeper than openDepth start collapsed. */
export default function AstTree({ node, depth = 0, openDepth, onHover }: Props) {
  const [open, setOpen] = useState(depth < openDepth)
  const leaf = node.children.length === 0
  return (
    <li role="treeitem" aria-expanded={leaf ? undefined : open} aria-level={depth + 1}>
      <div className="flex items-center gap-1 rounded px-1 hover:bg-raised"
        onMouseEnter={() => onHover?.(node)} onMouseLeave={() => onHover?.(null)}>
        {leaf ? <span className="w-5" /> : (
          <button className="w-5 text-muted hover:text-ink" onClick={() => setOpen(!open)}
            aria-label={`${open ? 'Collapse' : 'Expand'} ${node.label}`}>{open ? '▾' : '▸'}</button>
        )}
        <span className="font-medium text-accent">{node.label}</span>
        {node.value !== null && <span className="text-ink">({node.value})</span>}
        <span className="ml-2 text-xs text-muted">L{node.start_line}{node.end_line !== node.start_line && `–${node.end_line}`}</span>
        {!leaf && !open && <span className="ml-1 text-xs text-muted">· {node.children.length} children</span>}
      </div>
      {!leaf && open && (
        <ul role="group" className="ml-3 border-l border-line pl-2">
          {node.children.map((c, i) => <AstTree key={i} node={c} depth={depth + 1} openDepth={openDepth} onHover={onHover} />)}
        </ul>
      )}
    </li>
  )
}
