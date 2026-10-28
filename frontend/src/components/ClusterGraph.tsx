import { useEffect, useRef } from 'react'
import cytoscape from 'cytoscape'
import type { Graph } from '../api'

type Props = { graph: Graph; onEdge: (pairId: number) => void; hideIsolated: boolean }

const css = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim()

/** Node = student, edge thickness = similarity. Clicking an edge opens the compare view. */
export default function ClusterGraph({ graph, onEdge, hideIsolated }: Props) {
  const box = useRef<HTMLDivElement>(null)
  const onEdgeRef = useRef(onEdge)
  onEdgeRef.current = onEdge

  useEffect(() => {
    if (!box.current) return
    const nodes = graph.nodes.filter((n) => !hideIsolated || n.degree > 0)
    const cy = cytoscape({
      container: box.current,
      elements: [
        ...nodes.map((n) => ({ data: { id: `n${n.id}`, label: n.label } })),
        ...graph.edges.map((e) => ({ data: { id: `e${e.id}`, pair: e.id, source: `n${e.source}`, target: `n${e.target}`, score: e.score } })),
      ],
      style: [
        { selector: 'node', style: {
          'background-color': css('--color-accent'), label: 'data(label)', color: css('--color-ink'),
          'font-size': 10, 'text-valign': 'bottom', 'text-margin-y': 4, width: 16, height: 16,
          'text-background-color': css('--color-surface'), 'text-background-opacity': 0.8, 'text-background-padding': '1px' } },
        { selector: 'edge', style: {
          width: 'mapData(score, 0.5, 1, 1, 7)', 'line-color': css('--color-muted'), opacity: 0.55, 'curve-style': 'haystack' } },
        { selector: 'edge:active, edge:selected', style: { 'line-color': css('--color-accent'), opacity: 1 } },
      ],
      layout: { name: 'cose', animate: false, nodeRepulsion: () => 40000, idealEdgeLength: () => 140, padding: 20 },
      wheelSensitivity: 0.2,
      maxZoom: 1.2, // few nodes would otherwise zoom in until labels are huge
      minZoom: 0.2,
    })
    cy.on('tap', 'edge', (ev) => onEdgeRef.current(ev.target.data('pair')))
    cy.on('mouseover', 'edge', (ev) => { if (box.current) box.current.style.cursor = 'pointer'; ev.target.style('opacity', 1) })
    cy.on('mouseout', 'edge', (ev) => { if (box.current) box.current.style.cursor = ''; ev.target.removeStyle('opacity') })
    return () => cy.destroy()
  }, [graph, hideIsolated])

  return <div ref={box} className="h-[28rem] w-full rounded-lg bg-raised/40" aria-label="Similarity graph: students connected by similar code" role="img" />
}
