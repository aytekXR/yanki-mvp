import type { Analysis, CreateAnalysisResponse } from './contracts'

// Thin fetch wrapper. All paths are relative — Next rewrites proxy them to the
// backend (see next.config.ts), so there is no CORS and no base URL to configure.

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function readErrorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json()
    // FastAPI/Pydantic validation errors: { detail: [{ msg }] } or { detail: "…" }.
    if (typeof body?.detail === 'string') return body.detail
    if (Array.isArray(body?.detail) && typeof body.detail[0]?.msg === 'string') {
      return body.detail[0].msg
    }
  } catch {
    // No JSON body — fall through to a generic message.
  }
  return `Request failed (${res.status}).`
}

export async function createAnalysis(url: string): Promise<CreateAnalysisResponse> {
  const res = await fetch('/api/v1/analyses', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
  if (!res.ok) {
    const message =
      res.status === 422
        ? "That doesn't look like a valid URL. Use http:// or https://."
        : await readErrorMessage(res)
    throw new ApiError(message, res.status)
  }
  return (await res.json()) as CreateAnalysisResponse
}

export async function getAnalysis(id: string): Promise<Analysis> {
  const res = await fetch(`/api/v1/analyses/${encodeURIComponent(id)}`, {
    headers: { Accept: 'application/json' },
    cache: 'no-store',
  })
  if (!res.ok) {
    // 422 = the path id is not a valid UUID (malformed URL). Treat it like 404
    // so the user sees the friendly not-found copy, not a raw Pydantic string.
    const message =
      res.status === 404 || res.status === 422
        ? "We couldn't find that analysis."
        : await readErrorMessage(res)
    throw new ApiError(message, res.status)
  }
  return (await res.json()) as Analysis
}
