import { describe, expect, it, vi, afterEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ScoreBar, StatusBadge } from '../components/ui'
import AstTree from '../components/AstTree'
import UploadZone from '../components/UploadZone'
import Dashboard from '../pages/Dashboard'
import NotFound from '../pages/NotFound'
import { ToastProvider } from '../components/Toast'
import { lineMatches } from '../lib/highlight'
import * as api from '../api'

afterEach(() => vi.restoreAllMocks())

function wrap(ui: React.ReactNode, path = '/') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}><ToastProvider>
      <MemoryRouter initialEntries={[path]}><Routes><Route path="*" element={ui} /></Routes></MemoryRouter>
    </ToastProvider></QueryClientProvider>,
  )
}

describe('ScoreBar', () => {
  it('shows the percentage and an accessible meter', () => {
    render(<ScoreBar value={0.873} />)
    expect(screen.getByText('87.3%')).toBeInTheDocument()
    expect(screen.getByRole('meter')).toHaveAttribute('aria-valuenow', '87')
  })
})

describe('StatusBadge', () => {
  it('renders the status text', () => {
    render(<StatusBadge status="failed" />)
    expect(screen.getByText('failed')).toBeInTheDocument()
  })
})

describe('lineMatches', () => {
  it('maps lines to the first covering match per side', () => {
    const m = lineMatches([
      { a_start: 1, a_end: 3, b_start: 10, b_end: 12, size: 9 },
      { a_start: 3, a_end: 4, b_start: 2, b_end: 3, size: 6 },
    ], 'a')
    expect([...m.entries()]).toEqual([[1, 0], [2, 0], [3, 0], [4, 1]])
  })
})

describe('AstTree', () => {
  const tree = {
    label: 'Module', value: null, start_line: 1, end_line: 2, children: [
      { label: 'Assign', value: null, start_line: 1, end_line: 1, children: [
        { label: 'Name', value: 'x', start_line: 1, end_line: 1, children: [] }] },
    ],
  }
  it('collapses and expands nodes', async () => {
    render(<ul role="tree"><AstTree node={tree} openDepth={1} /></ul>)
    expect(screen.queryByText('(x)')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Expand Assign' }))
    expect(screen.getByText('(x)')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Collapse Module' }))
    expect(screen.queryByText('Assign')).not.toBeInTheDocument()
  })
})

describe('UploadZone', () => {
  it('uploads .py/.zip files and reports the rest', async () => {
    const spy = vi.spyOn(api, 'uploadFiles').mockResolvedValue({ created: [], errors: [] })
    const onDone = vi.fn()
    render(<UploadZone assignmentId={7} onDone={onDone} onError={vi.fn()} />)
    const files = [new File(['x=1'], 'a.py'), new File(['PK'], 'b.zip'), new File(['hi'], 'notes.txt')]
    await userEvent.upload(screen.getByTestId('file-input'), files, { applyAccept: false })
    expect(spy).toHaveBeenCalledOnce()
    expect(spy.mock.calls[0][0]).toBe(7)
    expect(spy.mock.calls[0][1].map((f: File) => f.name)).toEqual(['a.py', 'b.zip'])
    expect(onDone).toHaveBeenCalled()
    expect(screen.getByText(/notes\.txt/)).toBeInTheDocument()
  })
})

describe('Dashboard', () => {
  it('shows the empty state', async () => {
    vi.spyOn(api.api, 'assignments').mockResolvedValue([])
    wrap(<Dashboard />)
    expect(await screen.findByText('No assignments yet')).toBeInTheDocument()
  })

  it('lists assignments with their last analysis', async () => {
    vi.spyOn(api.api, 'assignments').mockResolvedValue([{
      id: 1, title: 'HW1', course: 'DSA', language: 'python-subset', created_at: '2026-10-28T10:00:00',
      submission_count: 51, last_analysis: { id: 3, status: 'done', max_score: 0.95 },
    }])
    wrap(<Dashboard />)
    const row = (await screen.findByText('HW1')).closest('tr')!
    expect(within(row).getByText('51')).toBeInTheDocument()
    expect(within(row).getByText('95.0%')).toBeInTheDocument()
    expect(within(row).getByText('done')).toBeInTheDocument()
  })
})

describe('NotFound', () => {
  it('links home', () => {
    wrap(<NotFound />, '/nope')
    expect(screen.getByRole('link', { name: 'Back to assignments' })).toHaveAttribute('href', '/')
  })
})
