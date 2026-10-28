export const pct = (x: number | null | undefined, digits = 0) => (x == null ? '—' : `${(x * 100).toFixed(digits)}%`)

// The backend stores UTC timestamps without a zone suffix.
export const when = (iso: string | null) =>
  iso ? new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : iso + 'Z').toLocaleString() : '—'

export const SIGNALS = ['dice', 'containment', 'lcs', 'winnow'] as const
export const SIGNAL_LABEL: Record<(typeof SIGNALS)[number], string> = {
  dice: 'Dice', containment: 'Containment', lcs: 'LCS', winnow: 'Winnowing',
}

/** Score band used for colour: high >= 0.8, medium >= 0.5. */
export const band = (s: number) => (s >= 0.8 ? 'high' : s >= 0.5 ? 'medium' : 'low')
