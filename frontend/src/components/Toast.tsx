import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'

type Toast = { id: number; kind: 'error' | 'success'; text: string }
const ToastContext = createContext<(kind: Toast['kind'], text: string) => void>(() => {})

export const useToast = () => useContext(ToastContext)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const push = useCallback((kind: Toast['kind'], text: string) => {
    const id = Date.now() + Math.random()
    setToasts((t) => [...t, { id, kind, text }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 5000)
  }, [])
  return (
    <ToastContext.Provider value={push}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex w-[min(24rem,calc(100vw-2rem))] flex-col gap-2" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} role={t.kind === 'error' ? 'alert' : 'status'}
            className={`flex items-start justify-between gap-3 rounded-lg border bg-surface px-4 py-3 text-sm shadow-lg ${t.kind === 'error' ? 'border-danger/40' : 'border-ok/40'}`}>
            <span><b className={t.kind === 'error' ? 'text-danger' : 'text-ok'}>{t.kind === 'error' ? 'Error' : 'Done'}:</b> {t.text}</span>
            <button className="text-muted hover:text-ink" aria-label="Dismiss" onClick={() => setToasts((x) => x.filter((y) => y.id !== t.id))}>×</button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
