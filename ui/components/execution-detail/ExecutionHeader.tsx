'use client'

import { ArrowLeft } from 'lucide-react'
import type { Execution } from '@/lib/types'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { DownloadButton } from '@/components/executions/DownloadButton'
import { formatDateTime } from '@/lib/time'

interface Props {
  execution: Execution
  onBack: () => void
}

export function ExecutionHeader({ execution, onBack }: Props) {
  return (
    <div className="flex items-start justify-between gap-4">
      {/* Left — back button + title */}
      <div className="flex items-start gap-4">
        <button
          onClick={onBack}
          className="btn-ghost flex items-center gap-1.5 mt-0.5 text-xs"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back
        </button>

        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold font-sans text-foreground tracking-tight">
              Execution <span className="text-accent">#{execution.id}</span>
            </h2>
            <StatusBadge status={execution.status} />
          </div>
          <p className="text-xs font-mono text-muted-fg mt-1">
            Agent: <span className="text-foreground">{execution.agent_name}</span>
            {' · '}
            Started: <span className="text-foreground">{formatDateTime(execution.created_at)}</span>
          </p>
        </div>
      </div>

      {/* Right — download button */}
      <DownloadButton
        executionId={execution.id}
        status={execution.status}
        variant="button"
      />
    </div>
  )
}
