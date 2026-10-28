import type { Match } from '../api'

// Match colours: translucent so they work on light and dark backgrounds.
export const MATCH_COLORS = [
  'rgba(99,102,241,0.22)', 'rgba(16,185,129,0.22)', 'rgba(245,158,11,0.25)',
  'rgba(236,72,153,0.20)', 'rgba(14,165,233,0.22)', 'rgba(168,85,247,0.22)',
]

/** line number -> index of the match that covers it on one side (the first match wins). */
export function lineMatches(matches: Match[], side: 'a' | 'b'): Map<number, number> {
  const out = new Map<number, number>()
  matches.forEach((m, i) => {
    const [lo, hi] = side === 'a' ? [m.a_start, m.a_end] : [m.b_start, m.b_end]
    for (let line = lo; line <= hi; line++) if (!out.has(line)) out.set(line, i)
  })
  return out
}
