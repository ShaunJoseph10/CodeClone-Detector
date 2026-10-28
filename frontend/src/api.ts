// Typed client for the FastAPI backend (/api). Base URL: VITE_API_BASE (empty = same origin).
export const API_BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/$/, '')

export type Signals = { dice: number; containment: number; lcs: number; winnow: number }
export type SubRef = { id: number; student_name: string; filename: string }
export type Submission = SubRef & {
  assignment_id: number; lines: number; uploaded_at: string; parse_error: string | null; source?: string
}
export type Assignment = {
  id: number; title: string; course: string; language: string; created_at: string; submission_count: number
  last_analysis: { id: number; status: Status; max_score: number | null } | null
}
export type Status = 'queued' | 'running' | 'done' | 'failed'
export type Summary = {
  files: number; total_pairs: number; pairs_scored: number; pairs_skipped: number; ignored_fingerprints: number
  flagged: number; clusters: number; max_score: number; engine_errors: Record<string, string>
  timing: Record<string, number>
}
export type Analysis = {
  id: number; assignment_id: number; status: Status; error: string | null; duration_ms: number | null
  config: { threshold: number; min_mass: number; weights: Partial<Signals> | null }
  summary: Partial<Summary>; created_at: string; started_at: string | null; finished_at: string | null
}
export type Pair = { id: number; score: number; signals: Signals; a: SubRef; b: SubRef; match_count: number }
export type Match = { a_start: number; a_end: number; b_start: number; b_end: number; size: number }
export type PairDetail = Omit<Pair, 'a' | 'b'> & { a: Submission & { source: string }; b: Submission & { source: string }; matches: Match[] }
export type Page<T> = { items: T[]; total: number; page: number; page_size: number }
export type Cluster = { id: number; max_score: number; members: SubRef[] }
export type Graph = {
  min_score: number
  nodes: { id: number; label: string; filename: string; degree: number }[]
  edges: { id: number; source: number; target: number; score: number }[]
}
export type AstNode = { label: string; value: string | null; start_line: number; end_line: number; children: AstNode[] }
export type UploadResult = { created: Submission[]; errors: { filename: string; error: string }[] }

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(API_BASE + path, {
    ...init,
    headers: init?.body && !(init.body instanceof FormData) ? { 'Content-Type': 'application/json' } : undefined,
  })
  if (!res.ok) throw new ApiError(res.status, await errorMessage(res))
  return res.status === 204 ? (undefined as T) : res.json()
}

async function errorMessage(res: Response) {
  try {
    const body = await res.json()
    return body?.error?.message ?? res.statusText
  } catch {
    return res.statusText || 'Request failed'
  }
}

export const api = {
  assignments: () => request<Assignment[]>('/api/assignments'),
  assignment: (id: number) => request<Assignment>(`/api/assignments/${id}`),
  createAssignment: (body: { title: string; course: string }) =>
    request<Assignment>('/api/assignments', { method: 'POST', body: JSON.stringify(body) }),
  deleteAssignment: (id: number) => request<void>(`/api/assignments/${id}`, { method: 'DELETE' }),
  submissions: (id: number) => request<Submission[]>(`/api/assignments/${id}/submissions`),
  submission: (id: number) => request<Submission & { source: string }>(`/api/submissions/${id}`),
  ast: (id: number, normalized: boolean) =>
    request<{ tree: AstNode }>(`/api/submissions/${id}/ast?normalized=${normalized}`),
  analyses: (id: number) => request<Analysis[]>(`/api/assignments/${id}/analyses`),
  analysis: (id: number) => request<Analysis>(`/api/analyses/${id}`),
  startAnalysis: (id: number, body: { threshold: number; min_mass: number; weights: Signals | null }) =>
    request<Analysis>(`/api/assignments/${id}/analyses`, { method: 'POST', body: JSON.stringify(body) }),
  pairs: (id: number, q: { min_score: number; student: string; sort: string; page: number; page_size: number }) =>
    request<Page<Pair>>(`/api/analyses/${id}/pairs?` + new URLSearchParams(Object.entries(q).map(([k, v]) => [k, String(v)]))),
  pair: (analysisId: number, pairId: number) => request<PairDetail>(`/api/analyses/${analysisId}/pairs/${pairId}`),
  clusters: (id: number) => request<Cluster[]>(`/api/analyses/${id}/clusters`),
  graph: (id: number) => request<Graph>(`/api/analyses/${id}/graph`),
  exportUrl: (id: number, format: 'csv' | 'json') => `${API_BASE}/api/analyses/${id}/export?format=${format}`,
}

/** Upload with progress (fetch has no upload progress, so XHR). */
export function uploadFiles(assignmentId: number, files: File[], onProgress: (pct: number) => void) {
  return new Promise<UploadResult>((resolve, reject) => {
    const form = new FormData()
    files.forEach((f) => form.append('files', f))
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API_BASE}/api/assignments/${assignmentId}/submissions`)
    xhr.upload.onprogress = (e) => e.lengthComputable && onProgress(Math.round((e.loaded / e.total) * 100))
    xhr.onload = () => {
      let body: { error?: { message?: string } } & UploadResult | null = null
      try { body = JSON.parse(xhr.responseText) } catch { /* not JSON */ }
      if (xhr.status >= 200 && xhr.status < 300 && body) resolve(body)
      else reject(new ApiError(xhr.status, body?.error?.message ?? 'Upload failed'))
    }
    xhr.onerror = () => reject(new ApiError(0, 'Network error during upload'))
    xhr.send(form)
  })
}
