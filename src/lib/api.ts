const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'APIError'
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `HTTP ${res.status}`
    try {
      const data = await res.json()
      message = data.detail || data.error || message
    } catch {}
    throw new APIError(res.status, message)
  }
  return res.json() as Promise<T>
}

export interface AnalysisResult {
  bpm: number
  key: string
  scale: string
  total_bars: number
  note_count: number
  detected_style: 'rawstyle' | 'euphoric'
  key_root: number
}

export interface TrendSummary {
  version: string
  last_updated: string
  bpm_range: { min: number; max: number; typical: number }
  top_patterns: Array<{ id: string; style: string; energy: string; composite_score: number }>
  available_styles: string[]
}

export const api = {
  async analyzeMidi(file: File): Promise<AnalysisResult> {
    const form = new FormData()
    form.append('file', file)

    const res = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      body: form,
    })
    return handleResponse<AnalysisResult>(res)
  },

  async generateMidi(
    file: File,
    options: {
      style: string
      energy: string
      bars: number
    }
  ): Promise<{ blob: Blob; sessionId: string }> {
    const form = new FormData()
    form.append('file', file)
    form.append('style', options.style)
    form.append('energy', options.energy)
    form.append('bars', String(options.bars))

    const res = await fetch(`${API_BASE}/generate`, {
      method: 'POST',
      body: form,
    })

    if (!res.ok) {
      let message = `HTTP ${res.status}`
      try {
        const data = await res.json()
        message = data.detail || data.error || message
      } catch {}
      throw new APIError(res.status, message)
    }

    const blob = await res.blob()
    const sessionId = res.headers.get('X-Session-ID') || 'UNKNOWN'
    return { blob, sessionId }
  },

  async getTrends(): Promise<TrendSummary> {
    const res = await fetch(`${API_BASE}/trends`)
    return handleResponse<TrendSummary>(res)
  },

  async checkHealth(): Promise<{ status: string; trend_engine_loaded: boolean }> {
    const res = await fetch(`${API_BASE}/health`)
    return handleResponse(res)
  },
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
