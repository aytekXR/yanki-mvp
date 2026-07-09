import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import ResultsTable from '@/components/ResultsTable'
import type { AnalysisResponse, Prompt } from '@/lib/contracts'
import { axeCheck } from './a11y'

const prompts: Prompt[] = [
  { id: 'p1', category: 'comparison', text: 'Best CRM for small teams?' },
  { id: 'p2', category: 'recommendation', text: 'Which analytics tool should I pick?' },
]

const responses: AnalysisResponse[] = [
  {
    id: 'r1',
    engine: 'openai',
    model: 'gpt-4o-mini',
    footprint: true,
    matched_snippet: 'Acme is a strong option for small teams.',
    prompt_id: 'p1',
    raw_text: 'Acme is a strong option for small teams and offers…',
    cost_usd: 0.0021,
  },
  {
    id: 'r2',
    engine: 'anthropic',
    model: 'claude-3-5-haiku',
    footprint: false,
    matched_snippet: null,
    prompt_id: 'p2',
    raw_text: 'There are several analytics tools worth considering…',
    cost_usd: 0.0018,
  },
]

describe('ResultsTable accessibility', () => {
  it('has no axe violations across footprint yes/no and a null snippet', async () => {
    const { container } = render(
      <main>
        <ResultsTable responses={responses} prompts={prompts} />
      </main>,
    )
    expect(await axeCheck(container)).toHaveNoViolations()
  })
})
