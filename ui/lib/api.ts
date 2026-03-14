import type {
  Execution,
  ExecutionListResponse,
  ExecutionListParams,
  CreateExecutionPayload,
  Agent,
  ApiKeySettings,
  ModelSettings,
  AgentSettings,
  HealthResponse,
} from './types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

// ── Core fetch wrapper ─────────────────────────────────────────────────────

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text()
    let message = text
    try { message = JSON.parse(text)?.detail ?? text } catch {}
    const err = new Error(message) as Error & { status: number }
    err.status = res.status
    throw err
  }
  return res.json()
}

// ── API client ─────────────────────────────────────────────────────────────

export const api = {

  // ── Health ────────────────────────────────────────────────────────────────
  health: () =>
    request<HealthResponse>('/health'),

  // ── Executions ────────────────────────────────────────────────────────────
  executions: {
    create: (payload: CreateExecutionPayload) =>
      request<Execution>('/api/v1/executions', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    list: (params?: ExecutionListParams) => {
      const qs = new URLSearchParams()
      if (params?.skip      !== undefined) qs.set('skip',       String(params.skip))
      if (params?.limit     !== undefined) qs.set('limit',      String(params.limit))
      if (params?.agent_name)              qs.set('agent_name', params.agent_name)
      if (params?.status)                  qs.set('status',     params.status)
      const query = qs.toString() ? `?${qs.toString()}` : ''
      return request<ExecutionListResponse>(`/api/v1/executions${query}`)
    },

    get: (id: number) =>
      request<Execution>(`/api/v1/executions/${id}`),

    // ── Artifact download ──────────────────────────────────────────────────
    // Cannot use request<T>() here because the response is binary (zip),
    // not JSON. We use fetch() directly and trigger a browser file download
    // via a temporary <a> element.
    downloadArtifacts: async (id: number): Promise<void> => {
      const res = await fetch(
        `${BASE_URL}/api/v1/executions/${id}/download`,
        { method: 'GET' }
      )

      if (!res.ok) {
        const text = await res.text()
        let message = text
        try { message = JSON.parse(text)?.detail ?? text } catch {}
        throw new Error(message)
      }

      // Convert response to a Blob — raw binary object in memory
      const blob = await res.blob()

      // Create a temporary blob:// URL pointing to the zip in memory
      const url = URL.createObjectURL(blob)

      // Extract filename from Content-Disposition header if present
      const disposition = res.headers.get('Content-Disposition') ?? ''
      const match = disposition.match(/filename=(.+)/)
      const filename = match ? match[1] : `execution_${id}_artifacts.zip`

      // Programmatically click a hidden <a> to trigger the download dialog
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()

      // Clean up — free the blob URL from memory
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    },
  },

  // ── Agents ────────────────────────────────────────────────────────────────
  agents: {
    list: () => request<Agent[]>('/api/v1/agents'),
  },

  // ── Settings (stubbed — backend not yet wired) ────────────────────────────
  settings: {
    getApiKeys: () =>
      request<ApiKeySettings>('/api/v1/settings/api-keys'),

    saveApiKeys: (payload: ApiKeySettings) =>
      request<void>('/api/v1/settings/api-keys', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    getModels: () =>
      request<ModelSettings>('/api/v1/settings/models'),

    saveModels: (payload: ModelSettings) =>
      request<void>('/api/v1/settings/models', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),

    getAgents: () =>
      request<AgentSettings[]>('/api/v1/settings/agents'),

    saveAgents: (payload: AgentSettings[]) =>
      request<void>('/api/v1/settings/agents', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },

  // ── SSE stream ────────────────────────────────────────────────────────────
  streamExecution: (id: number) =>
    new EventSource(`${BASE_URL}/api/v1/executions/${id}/stream`),
}
