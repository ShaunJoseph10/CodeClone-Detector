import { useRef, useState, type DragEvent } from 'react'
import { uploadFiles, type UploadResult } from '../api'

type Props = { assignmentId: number; onDone: (r: UploadResult) => void; onError: (msg: string) => void }

export function acceptable(f: File) {
  return /\.(py|zip)$/i.test(f.name)
}

export default function UploadZone({ assignmentId, onDone, onError }: Props) {
  const input = useRef<HTMLInputElement>(null)
  const [over, setOver] = useState(false)
  const [progress, setProgress] = useState<number | null>(null)
  const [rejected, setRejected] = useState<string[]>([])

  const send = async (list: FileList | null) => {
    if (!list?.length) return
    const files = Array.from(list)
    const ok = files.filter(acceptable)
    setRejected(files.filter((f) => !acceptable(f)).map((f) => f.name))
    if (!ok.length) return
    setProgress(0)
    try {
      onDone(await uploadFiles(assignmentId, ok, setProgress))
    } catch (e) {
      onError((e as Error).message)
    } finally {
      setProgress(null)
      if (input.current) input.current.value = ''
    }
  }

  const drop = (e: DragEvent) => {
    e.preventDefault()
    setOver(false)
    send(e.dataTransfer.files)
  }

  return (
    <div>
      <div
        role="button" tabIndex={0} aria-label="Upload .py files or a .zip"
        onClick={() => input.current?.click()}
        onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && input.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setOver(true) }}
        onDragLeave={() => setOver(false)}
        onDrop={drop}
        className={`cursor-pointer rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors ${over ? 'border-accent bg-accent-soft' : 'border-line hover:border-accent/60'}`}
      >
        <p className="font-medium">Drop .py files or a .zip here</p>
        <p className="mt-1 text-sm text-muted">or click to choose. In a zip, each top folder is one student.</p>
        <input ref={input} type="file" multiple accept=".py,.zip" className="hidden" data-testid="file-input"
          onChange={(e) => send(e.target.files)} />
      </div>
      {progress !== null && (
        <div className="mt-3" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100} aria-label="Upload progress">
          <div className="h-1.5 overflow-hidden rounded-full bg-raised">
            <div className="h-full bg-accent transition-all" style={{ width: `${progress}%` }} />
          </div>
          <p className="mt-1 text-xs text-muted">Uploading… {progress}%</p>
        </div>
      )}
      {rejected.length > 0 && (
        <p className="mt-2 text-sm text-danger">Skipped (only .py and .zip): {rejected.join(', ')}</p>
      )}
    </div>
  )
}
