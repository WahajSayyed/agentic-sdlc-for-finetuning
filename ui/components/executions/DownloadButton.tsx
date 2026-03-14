'use client'

import { useState } from 'react'
import { Download, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { ExecutionStatus } from '@/lib/types'

interface DownloadButtonProps {
  executionId: number
  status: ExecutionStatus
  // variant: "icon" for the executions list table row
  //          "button" for the execution detail page
  variant?: 'icon' | 'button'
}

export function DownloadButton({
  executionId,
  status,
  variant = 'button',
}: DownloadButtonProps) {
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState<string | null>(null)

  // Only completed and failed executions have artifacts to download.
  // Pending/running executions haven't produced output yet.
  const isAvailable = status === 'completed' || status === 'failed'

  const handleDownload = async () => {
    if (!isAvailable || loading) return
    setLoading(true)
    setError(null)
    try {
      await api.executions.downloadArtifacts(executionId)
    } catch (err: any) {
      setError(err.message ?? 'Download failed')
    } finally {
      setLoading(false)
    }
  }

  // ── Icon variant — compact, used in table rows ─────────────────────────
  if (variant === 'icon') {
    return (
      <button
        onClick={handleDownload}
        disabled={!isAvailable || loading}
        title={
          !isAvailable
            ? 'Artifacts not available yet'
            : loading
            ? 'Downloading…'
            : `Download artifacts for execution ${executionId}`
        }
        className={cn(
          'p-1.5 rounded transition-all duration-150',
          isAvailable && !loading
            ? 'text-muted-fg hover:text-accent hover:bg-accent-dim cursor-pointer'
            : 'text-muted-fg/30 cursor-not-allowed'
        )}
      >
        {loading
          ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
          : <Download className="w-3.5 h-3.5" />
        }
      </button>
    )
  }

  // ── Button variant — prominent, used on detail page ────────────────────
  return (
    <div className="flex flex-col items-end gap-1">
      <button
        onClick={handleDownload}
        disabled={!isAvailable || loading}
        className={cn(
          'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-mono transition-all duration-150 border',
          isAvailable && !loading
            ? 'bg-accent text-background border-accent hover:opacity-90 cursor-pointer'
            : 'bg-muted text-muted-fg border-border cursor-not-allowed opacity-50'
        )}
      >
        {loading
          ? <Loader2 className="w-4 h-4 animate-spin" />
          : <Download className="w-4 h-4" />
        }
        {loading ? 'Downloading…' : 'Download Artifacts'}
      </button>

      {/* Inline error message — shown below the button */}
      {error && (
        <p className="text-xs font-mono text-danger">{error}</p>
      )}

      {/* Availability hint when execution hasn't finished */}
      {!isAvailable && (
        <p className="text-[11px] font-mono text-muted-fg">
          Available once execution completes
        </p>
      )}
    </div>
  )
}
