import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { Button, Card, EmptyState, PageHeader, SkeletonRows, StatusBadge, inputClass } from '../components/ui'
import { useToast } from '../components/Toast'
import { pct, when } from '../lib/format'

function NewAssignment({ onClose }: { onClose: () => void }) {
  const [title, setTitle] = useState('')
  const [course, setCourse] = useState('')
  const toast = useToast()
  const qc = useQueryClient()
  const navigate = useNavigate()
  const create = useMutation({
    mutationFn: api.createAssignment,
    onSuccess: (a) => {
      qc.invalidateQueries({ queryKey: ['assignments'] })
      navigate(`/assignments/${a.id}`)
    },
    onError: (e: Error) => toast('error', e.message),
  })
  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (title.trim()) create.mutate({ title, course })
  }
  return (
    <Card className="mb-6">
      <form onSubmit={submit} className="grid gap-3 sm:grid-cols-[2fr_1fr_auto] sm:items-end">
        <label className="text-sm">
          <span className="mb-1 block font-medium">Title</span>
          <input autoFocus required maxLength={200} className={inputClass} value={title}
            onChange={(e) => setTitle(e.target.value)} placeholder="Week 3: sorting" />
        </label>
        <label className="text-sm">
          <span className="mb-1 block font-medium">Course</span>
          <input maxLength={100} className={inputClass} value={course} onChange={(e) => setCourse(e.target.value)} placeholder="CS201" />
        </label>
        <div className="flex gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="primary" disabled={!title.trim() || create.isPending}>Create</Button>
        </div>
      </form>
    </Card>
  )
}

export default function Dashboard() {
  const [creating, setCreating] = useState(false)
  const { data, isLoading, error } = useQuery({ queryKey: ['assignments'], queryFn: api.assignments })

  return (
    <>
      <PageHeader title="Assignments" subtitle="Upload submissions, run an analysis, and review similar pairs."
        actions={<Button variant="primary" onClick={() => setCreating(true)}>+ New assignment</Button>} />
      {creating && <NewAssignment onClose={() => setCreating(false)} />}
      {isLoading ? <SkeletonRows rows={4} /> : error ? (
        <EmptyState title="Could not load assignments" body={(error as Error).message} />
      ) : !data?.length ? (
        <EmptyState title="No assignments yet" body="Create one, then drop in the students' .py files or a .zip."
          action={!creating && <Button variant="primary" onClick={() => setCreating(true)}>Create an assignment</Button>} />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-line bg-surface">
          <table className="w-full text-sm">
            <thead className="border-b border-line text-left text-xs uppercase tracking-wide text-muted">
              <tr>
                <th className="px-4 py-3 font-medium">Assignment</th>
                <th className="px-4 py-3 font-medium">Submissions</th>
                <th className="px-4 py-3 font-medium">Last analysis</th>
                <th className="px-4 py-3 font-medium">Highest similarity</th>
                <th className="px-4 py-3 font-medium">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {data.map((a) => (
                <tr key={a.id} className="hover:bg-raised/60">
                  <td className="px-4 py-3">
                    <Link to={`/assignments/${a.id}`} className="font-medium text-accent hover:underline">{a.title}</Link>
                    {a.course && <span className="ml-2 text-muted">{a.course}</span>}
                  </td>
                  <td className="px-4 py-3 tabular-nums">{a.submission_count}</td>
                  <td className="px-4 py-3">
                    {a.last_analysis ? (
                      <Link to={`/analyses/${a.last_analysis.id}`}><StatusBadge status={a.last_analysis.status} /></Link>
                    ) : <span className="text-muted">never run</span>}
                  </td>
                  <td className="px-4 py-3 tabular-nums">{pct(a.last_analysis?.max_score, 1)}</td>
                  <td className="px-4 py-3 text-muted">{when(a.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
