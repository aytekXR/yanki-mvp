import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { Analysis } from '@/lib/contracts'
import { axeCheck } from './a11y'

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ id: 'check-id' }),
  useSearchParams: () => new URLSearchParams('submission_id=sub-1'),
}))

vi.mock('@/lib/api', () => ({
  createCheckerAnalysis: vi.fn(),
  getAnalysis: vi.fn(),
  ApiError: class ApiError extends Error {
    status: number
    constructor(message: string, status: number) {
      super(message)
      this.name = 'ApiError'
      this.status = status
    }
  },
}))

import CheckerPage from '@/app/checker/page'
import CheckerResultsPage from '@/app/checker/[id]/page'
import { getAnalysis } from '@/lib/api'

const mockedGet = vi.mocked(getAnalysis)

function makeAnalysis(overrides: Partial<Analysis>): Analysis {
  return {
    id: 'check-id',
    url: 'checker:Notion',
    status: 'running',
    current_step: 'prompts',
    progress: 30,
    error: null,
    created_at: '2026-07-10T00:00:00Z',
    updated_at: '2026-07-10T00:00:00Z',
    result: {
      footprint_count: null,
      geo_score: null,
      kyc: null,
      prompts: [],
      responses: [],
      total_responses: null,
      engine_presence: null,
      competitors_appeared: null,
    },
    ...overrides,
  } as Analysis
}

describe('Checker screens accessibility', () => {
  beforeEach(() => {
    mockedGet.mockReset()
  })

  it('landing has no axe violations', async () => {
    const { container } = render(<CheckerPage />)
    // The form is present before the axe pass.
    expect(
      screen.getByRole('button', { name: /check my brand/i }),
    ).toBeInTheDocument()
    expect(await axeCheck(container)).toHaveNoViolations()
  })

  it('results screen has no axe violations while running', async () => {
    mockedGet.mockResolvedValue(
      makeAnalysis({ status: 'running', progress: 30, current_step: 'prompts' }),
    )
    const { container } = render(<CheckerResultsPage />)
    await screen.findByRole('progressbar')
    expect(await axeCheck(container)).toHaveNoViolations()
  })

  it('results screen has no axe violations on the done screen', async () => {
    mockedGet.mockResolvedValue(
      makeAnalysis({
        status: 'done',
        progress: 100,
        current_step: null,
        result: {
          footprint_count: 16,
          geo_score: 0.33,
          kyc: null,
          prompts: [{ id: 'p1', category: 'comparison', text: 'Best note app?' }],
          responses: [
            {
              id: 'r1',
              engine: 'openai',
              model: 'gpt-4o-mini',
              footprint: true,
              matched_snippet: 'Notion is a strong option.',
              prompt_id: 'p1',
              raw_text: 'Notion is a strong option and…',
              cost_usd: 0.0021,
            },
          ],
          total_responses: 48,
          engine_presence: [
            { engine: 'openai', mentioned: 4, total: 12 },
            { engine: 'anthropic', mentioned: 4, total: 12 },
          ],
          competitors_appeared: [
            { name: 'Acme', mentions: 48 },
            { name: 'Globex', mentions: 48 },
          ],
        },
      }),
    )
    const { container } = render(<CheckerResultsPage />)
    await screen.findByRole('img') // the ScoreGauge
    expect(await axeCheck(container)).toHaveNoViolations()
  })
})
